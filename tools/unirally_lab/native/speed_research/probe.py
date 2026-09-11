"""Compare speed arithmetic using original call arguments; no native runtime."""
import argparse
import hashlib
import subprocess
import tempfile
import json
from pathlib import Path
from collections import Counter
from .contract import SpeedState, SpeedContext, update_speed
from ...access.derive import validate_document
from ..probe_sampling import validate_primary_access

STRIDE = 0x1600


def ordered_events(access, frame):
    return sorted((row[0], kind, row) for frames in access['watch_addresses'].values()
                  for kind, rows in frames.get(str(frame), {}).items() for row in rows)


def snapshot(series, frame, events, stop):
    memory = list(series[(frame - 1) * STRIDE:frame * STRIDE])
    for sequence, kind, row in events:
        if sequence >= stop:
            break
        _, _, _, address, width, value = row
        if address >= STRIDE:
            continue
        if kind == 'w':
            memory[address:address + width] = ([None] * width if value is None
                                              else list(value.to_bytes(width, 'little')))
        elif value is not None and None in memory[address:address + width]:
            memory[address:address + width] = list(value.to_bytes(width, 'little'))
    return memory


def read_word(memory, address, events=(), start=0, end=0):
    pair = memory[address:address + 2]
    if None in pair:
        for sequence, kind, row in events:
            if not start <= sequence < end or row[3] != address:
                continue
            if kind == 'w':
                break
            if row[4] == 2 and row[5] is not None:
                return row[5]
        raise ValueError(f'unresolved incoming word {address:04x}')
    return int.from_bytes(pair, 'little')


def cartridge_mode(events, start, end):
    reads = [row for sequence, kind, row in events
             if start <= sequence < end and kind == 'r' and row[1] == 0x82a81a]
    if len(reads) != 1:
        raise ValueError("speed call must contain exactly one cartridge-mode read")
    row = reads[0]
    if row[3] != 0x77074a or row[4] != 2 or type(row[5]) is not int or not 0 <= row[5] <= 65535:
        raise ValueError("cartridge-mode read must identify a known word at $77:074A")
    return row[5] & 255


def validate_domain(access, series):
    expected = {"start": 1534, "end": 2999, "count": 1466}
    if access.get("frames") != expected or any(type(value) is not int for value in access["frames"].values()):
        raise ValueError("expected complete primary speed domain1534–2999")
    metadata = access["wram_series"]
    if any(type(metadata.get(key)) is not int or metadata[key] != value for key, value in
           [("start", 0), ("length", STRIDE), ("every", 1), ("bytes", 3000 * STRIDE)]):
        raise ValueError("unexpected series dimensions")
    if metadata.get("frames") != list(range(3000)) or any(type(frame) is not int for frame in metadata["frames"]):
        raise ValueError("series must cover all3000 frames in order")
    if len(series) != 3000 * STRIDE:
        raise ValueError("truncated series")


def compare(access, series, rom, native_probe=None):
    validate_document(access)
    validate_primary_access(access)
    validate_domain(access, series)
    if hashlib.sha256(series).hexdigest() != access['wram_series']['sha256']:
        raise ValueError('series hash differs')
    if hashlib.sha256(rom).hexdigest() != access['rom']['sha256']:
        raise ValueError('ROM hash differs')
    masks = rom[0x51b:0x524]
    decay = [int.from_bytes(rom[0x524 + i * 2:0x526 + i * 2], 'little') for i in range(9)]
    counts = Counter()
    mismatches = []
    contexts = {}
    native_inputs, native_expected = [], []
    for frame in range(1534, 3000):
        events = ordered_events(access, frame)
        counter_rows = access['watch_addresses'][str(0x127f)][str(frame)]
        old = [row[5] for row in counter_rows['r'] if row[1] == 0x83ccde]
        new = [row[5] for row in counter_rows['w'] if row[1] == 0x83cce4]
        used = [row[5] for row in counter_rows['r'] if row[1] == 0x82a88f]
        if len(old) != 1 or len(new) != 1 or new[0] != (old[0] + 1) & 255 or used != [new[0], new[0]]:
            raise ValueError(f'counter recurrence/order mismatch at{frame}')
        counts['counter_recurrences'] += 1
        starts = [seq for seq, kind, row in events if kind == 'r' and row[1] == 0x82a6fa]
        if len(starts) != 2:
            raise ValueError(f'expected two speed calls at {frame}')
        for start in starts:
            end = min(seq for seq, kind, row in events if seq > start and kind == 'r' and row[1] == 0x82a627)
            before = snapshot(series, frame, events, start)
            after = snapshot(series, frame, events, end)
            def get(address):
                return read_word(before, address, events, start, end)
            selector = get(0xff9)
            if selector not in (0, 2):
                raise ValueError('invalid rider selector')
            if get(0x547 + selector) != 0:
                raise ValueError("the primary capture contract excludes skipped speed calls")
            mode = cartridge_mode(events, start, end)
            state = SpeedState(get(0xfa9), get(0xfab), get(0x11d7), get(0x11dd), get(0x343 + selector))
            context = SpeedContext(selector // 2, get(0x547 + selector), get(0x1225 + selector),
                                   get(0x1513 if selector == 0 else 0x150b) & 255,
                                   get(0x11f1), get(0xc6d), get(0xfcd), get(0xfcf), get(0x1283),
                                   get(0x1281), get(0x11d3), get(0x127f), get(0xf21), mode)
            actual = update_speed(state, context, masks, decay)
            expected = SpeedState(*(read_word(after, a) for a in
                                    [0xfa9, 0xfab, 0x11d7, 0x11dd, 0x343 + selector]))
            native_inputs.append(" ".join(str(value) for value in [*vars(state).values(), *vars(context).values()]))
            native_expected.append(list(vars(expected).values()))
            counts['calls'] += 1
            counts['values'] += 5
            counts['start_override_calls'] += bool(context.start_override)
            counts['drag_calls'] += bool(context.drag)
            counts['skipped_calls'] += bool(context.skip)
            for key, value in vars(context).items():
                contexts.setdefault(key, set()).add(value)
            if actual != expected:
                mismatches.append({'frame': frame, 'rider': selector // 2,
                                   'actual': vars(actual), 'expected': vars(expected),
                                   'input': vars(state), 'context': vars(context)})
    native_result = {"status": "not run"}
    if native_probe is not None:
        with tempfile.TemporaryDirectory() as directory:
            mask_path, decay_path = Path(directory) / 'masks.bin', Path(directory) / 'decrements.bin'
            mask_path.write_bytes(masks)
            decay_path.write_bytes(rom[0x524:0x536])
            process = subprocess.run([str(native_probe.resolve()), str(mask_path), str(decay_path)],
                                     input="\n".join(native_inputs) + "\n", text=True,
                                     capture_output=True, timeout=30)
        if process.returncode:
            raise RuntimeError(f'native speed probe failed: {process.stderr}')
        try:
            native_rows = [[int(value) for value in line.split()] for line in process.stdout.splitlines()]
        except ValueError as error:
            raise RuntimeError('malformed native speed output') from error
        if native_rows != native_expected:
            raise RuntimeError('native speed output differs from captured contract')
        native_result = {"status": "passed", "values": len(native_expected) * 5,
                         "stdout_sha256": hashlib.sha256(process.stdout.encode()).hexdigest()}
    return {'kind': 'isolated_speed_research', 'native': native_result, 'counts': counts, 'mismatches': mismatches,
            'status': 'passed' if not mismatches else 'failed',
            'context_domains': {key: sorted(values) for key, values in contexts.items()},
            'autonomous_movement': 'not tested'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-probe', type=Path)
    parser.add_argument('--report', type=Path, default=Path('artifacts/speed/comparison.json'))
    args = parser.parse_args()
    capture = Path('artifacts/speed/primary')
    access_path = capture / 'access.json'
    access = json.loads(access_path.read_text())
    series = (capture / 'wram-series.bin').read_bytes()
    rom = Path(Path('local/rom-location.txt').read_text().strip()).read_bytes()
    result = compare(access, series, rom, args.native_probe)
    result['access_sha256'] = hashlib.sha256(access_path.read_bytes()).hexdigest()
    result['series_sha256'] = hashlib.sha256(series).hexdigest()
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(result['native'])
    print(result['status'], result['counts'], result['mismatches'][:3])
    print({key: (min(values), max(values)) for key, values in result['context_domains'].items()})
    raise SystemExit(bool(result['mismatches']))
