"""M4-14 reference laboratory for sustained traversal; no native state repair."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile
from . import zoom_zoo_trial as trial
from .zoom_zoo_trial_reference import ROOT, ROM_SHA, CORE_SHA, PRIMARY_SHA, sha, digest, project, guards


def capture(out, library, horizon=3299):
    """Retain full WRAM for future-state inventory and targeted writer audits."""
    from ..reference.bsnes import BsnesCore
    from ..reference.worker import inputs_for_frame
    from ..replay.manifest import derive_script
    if out.exists() or out.with_suffix('.wram').exists():
        raise ValueError('refusing to overwrite reference')
    if not 3299 <= horizon <= 9999:
        raise ValueError('sustained horizon must be 3299..9999')
    raw = (ROOT/'tests/manifests/replay/race-crawler-zoom-zoo-3300.json').read_bytes()
    rom = Path((ROOT/'local/rom-location.txt').read_text().strip())
    if sha(raw) != PRIMARY_SHA or sha(library.read_bytes()) != CORE_SHA or sha(rom.read_bytes()) != ROM_SHA:
        raise ValueError('reference identity differs')
    script = derive_script(json.loads(raw))
    rows, whole, guard_rows = [], [], []
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sustained-reference-', dir=out.parent) as directory:
        core = BsnesCore(library, Path(directory), script.get('core_options'))
        try:
            core.load(rom)
            core.set_serialization_method('Strict')
            with out.with_suffix('.wram').open('xb') as series:
                for frame in range(horizon + 1):
                    inputs = inputs_for_frame(script, frame) if frame < 1650 else {0: {'right'}, 1: set()}
                    for port, buttons in inputs.items():
                        core.set_inputs(port, buttons)
                    core.run_frame()
                    if frame < 1649:
                        continue
                    wram, sram = core.wram(), core.cartridge_ram()
                    series.write(wram)
                    rows.append(project(wram, sram, frame).hex())
                    whole.append(sha(wram))
                    guard_rows.append(guards(wram, sram))
        finally:
            core.unload()
    if sha(bytes.fromhex(rows[0])[:394]) != trial.contract()['seed_sha256']:
        raise ValueError('authentic seed differs')
    result = {'kind': 'm4_14_exploratory_reference', 'frames': [1649, horizon],
              'case': {'id': 'continuous-right', 'changes': []},
              'rom_sha256': ROM_SHA, 'core_sha256': CORE_SHA, 'manifest_sha256': PRIMARY_SHA,
              'rows': rows, 'rows_sha256': digest(rows), 'wram_sha256': whole,
              'guard_rows': guard_rows}
    out.write_text(json.dumps(result, indent=2) + '\n')
    return {'frames': len(rows), 'rows_sha256': digest(rows)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--horizon', type=int, default=3299)
    args = parser.parse_args()
    print(json.dumps(capture(args.out, args.core, args.horizon)))


if __name__ == '__main__':
    main()
