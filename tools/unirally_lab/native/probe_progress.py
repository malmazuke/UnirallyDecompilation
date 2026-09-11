"""Check progress recurrence on the previously validated native sample words.

The sampler still takes captured positions and poses; this is not autonomous
movement. The progress recurrence itself is initialized only once at 1533.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from .. import report as reportmod
from .probe_sampling import NativeProbeFailure, run_probe, validate_primary_access


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ["sampling-output", "sampling-report", "series", "series-access", "content-manifest", "content", "probe", "report"]:
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    rep = reportmod.Report(sys.argv, task_id="M2-01")
    status = 0
    try:
        for name, path in vars(args).items():
            if name != "report": rep.add_input(name, path, hashlib.sha256(path.read_bytes()).hexdigest())
        sampling_report = json.loads(args.sampling_report.read_text())
        text = args.sampling_output.read_text()
        rows = [[int(value) for value in line.split()] for line in text.splitlines()]
        if sampling_report["status"] != "passed" or hashlib.sha256(text.encode()).hexdigest() != sampling_report["native_output_sha256"]:
            raise ValueError("sampler output does not match its passing report")
        if len(rows) != 2932 or any(len(row) != 10 or any(not 0 <= value <= 65535 for value in row) for row in rows):
            raise ValueError("expected exactly 2932 ten-word native sample rows")
        access = json.loads(args.series_access.read_text())
        validate_primary_access(access)
        series = args.series.read_bytes(); declaration = access["wram_series"]
        if declaration["start"] != 0 or declaration["length"] != 0x2200 or declaration["frames"] != list(range(3000)):
            raise ValueError("series must contain complete WRAM offsets 0..0x21FF for frames 0..2999")
        if len(series) != 3000 * 0x2200 or hashlib.sha256(series).hexdigest() != declaration["sha256"]:
            raise ValueError("series identity differs")
        manifest = json.loads(args.content_manifest.read_text()); item = manifest["items"][0]
        if len(manifest["items"]) != 1 or item["id"] != "progress-transitions" or access["rom"]["sha256"] != manifest["rom"]["sha256"]:
            raise ValueError("progress content or ROM identity differs")
        content = args.content.read_bytes()
        if len(content) != item["expected"]["length"] or hashlib.sha256(content).hexdigest() != item["expected"]["sha256"]:
            raise ValueError("progress transition content differs")
        rep.add_check("prerequisite_identities", "passed", detail="native sample output, original series, static transition tables verified")
        def word(frame: int, address: int) -> int:
            offset = frame * 0x2200 + address
            return int.from_bytes(series[offset:offset + 2], "little")
        seed = [word(1533, address) for address in [0xFC5,0xFC9,0xFCD,0xFC7,0xFCB,0xFCF]] + [series[1533 * 0x2200 + 0x302]]
        rep.data["seed"] = {"frame": 1533, "values": seed, "addresses": [0xFC5,0xFC9,0xFCD,0xFC7,0xFCB,0xFCF,0x302]}
        stdout, actual = run_probe([str(args.probe.resolve()),str(args.content),*map(str,seed)], text, 2932, 4)
        rep.add_check("native_progress_probe", "passed", detail="exit 0; complete native output")
        divergence = None
        for index, row in enumerate(actual):
            frame, rider = 1534 + index // 2, index % 2
            expected = [word(frame, address + rider * 2) for address in [0xFC5,0xFC9,0xFCD,0xFD1]]
            if row != expected:
                divergence = {"frame":frame,"rider":rider,"native":row,"reference":expected}
                break
        rep.data["first_divergence"] = divergence
        output_path = args.report.with_suffix(".native.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(stdout)
        rep.add_artifact("native_output", output_path)
        rep.data["native_output_sha256"] = hashlib.sha256(stdout.encode()).hexdigest()
        rep.data["domain"] = "progress recurrence on captured-argument native sampling; not autonomous movement"
        rep.add_check("progress_state_equal", "passed" if divergence is None else "failed", detail=f"11728 fields compared; first divergence {divergence}")
        status = 1 if divergence is not None else 0
    except NativeProbeFailure as error:
        rep.add_check("native_progress_probe", "failed", detail=str(error)); status = 1
    except FileNotFoundError as error:
        rep.add_check("prerequisite", "missing", detail=str(error)); status = 2
    except (ValueError,KeyError) as error:
        rep.add_check("experiment_input", "failed", detail=str(error)); status = 3
    except subprocess.TimeoutExpired as error:
        rep.add_check("native_progress_probe", "timeout", detail=str(error)); status = 4
    rep.finish("passed" if status == 0 else "failed"); rep.write(args.report)
    print(f"progress probe status={status}; report={args.report}")
    return status

if __name__ == "__main__":
    raise SystemExit(main())
