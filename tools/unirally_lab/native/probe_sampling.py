"""Check the isolated C++ sampler on captured incoming arguments.

This is a dependency experiment, NOT a simulation replay. Per-call reference
arguments are deliberate here and must never be used by native compare.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .. import report as reportmod
from ..access.derive import validate_document
from ..replay.manifest import derive_script
from ..reference.bsnes import DEFAULT_OPTIONS


class NativeProbeFailure(RuntimeError):
    """A native process failed or returned incomplete/malformed output."""


def run_probe(command: list[str], text: str, expected_rows: int, columns: int) -> tuple[str, list[list[int]]]:
    run = subprocess.run(command, input=text, text=True, capture_output=True, timeout=30)
    if run.returncode != 0:
        raise NativeProbeFailure(f"native process exit {run.returncode}: {run.stderr.strip()}")
    try:
        actual = [[int(value) for value in line.split()] for line in run.stdout.splitlines()]
    except ValueError as error:
        raise NativeProbeFailure("native output contains a non-integer value") from error
    if len(actual) != expected_rows or any(len(row) != columns for row in actual):
        raise NativeProbeFailure(f"native output must contain {expected_rows} rows of {columns} values; got {len(actual)} rows")
    return run.stdout, actual


def validate_primary_access(access: dict) -> None:
    root = Path(__file__).resolve().parents[3]
    relative_path = "tests/manifests/replay/race-crawler-dragster-3000-fields.json"
    path = root / relative_path
    manifest = json.loads(path.read_text())
    if access["scenario_id"] != manifest["scenario_id"]:
        raise ValueError("access scenario is not the primary case")
    if access["manifest"] != {"path": relative_path, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}:
        raise ValueError("access primary manifest identity differs")
    expected_core = manifest["core"]
    for key in ["name", "commit", "patch_sha256", "serialization_method"]:
        if access["core"][key] != expected_core[key]:
            raise ValueError(f"access pinned core {key} differs")
    if access["core"].get("api_version") != 1 or access["core"]["options"] != (DEFAULT_OPTIONS | expected_core.get("options", {})):
        raise ValueError("access core API/options differ")
    if access["rom"]["sha256"] != manifest["rom"]["sha256"]:
        raise ValueError("access primary ROM identity differs")
    script = (json.dumps(derive_script(manifest), indent=2, sort_keys=True) + "\n").encode()
    if access["script"] != {"frames": 3000, "sample_every": 1, "sample_from_frame": None, "sha256": hashlib.sha256(script).hexdigest()}:
        raise ValueError("access primary input script identity differs")
    if access["status"] != "complete" or access["failure"] is not None or access["watch_pcs_truncated"] is not False:
        raise ValueError("access capture is incomplete or truncated")
    if access["instructions"]["max_frame_delta"] > access["ring_capacity"]:
        raise ValueError("access instruction ring overflowed")


def capture_cases(access: dict, coarse_width: int) -> list[dict]:
    logs = access["watch_addresses"]
    frames = access["frames"]
    if frames != {"start": 1534, "end": 2999, "count": 1466}:
        raise ValueError("this experiment requires complete primary frames 1534..2999")
    observed: dict[int, list] = {}
    for row in access["watch_pcs"][str(0x818B6A)]:
        observed.setdefault(row[0], []).append(row)
    cases = []
    for frame in range(1534, 3000):
        rows = observed.get(frame, [])
        if len(rows) != 20:
            raise ValueError(f"frame {frame}: expected 20 sample stores, got {len(rows)}")
        for rider, writers in enumerate([
            (0x818D97, 0x818D9C, 0x818D15, 0x818D0F),
            (0x818EF1, 0x818EF6, 0x818E6F, 0x818E69),
        ]):
            values = []
            for address, writer in zip([0xA5, 0xA7, 0xF85, 0xF51], writers, strict=True):
                matches = [row for row in logs[str(address)][str(frame)]["w"] if row[1] == writer]
                if len(matches) != 1 or matches[0][5] is None:
                    raise ValueError(f"frame {frame}: expected one known parameter store at {writer:x}")
                values.append(matches[0][5])
            x, y, pose, reflected = values
            trace = rows[rider * 10:(rider + 1) * 10]
            if [row[3] for row in trace] != list(range(18, -1, -2)):
                raise ValueError(f"frame {frame}: unexpected sample-store order")
            cases.append({"frame": frame, "rider": rider,
                          "input": [pose, int(reflected != 0), x, y, coarse_width],
                          "expected": [row[1] for row in reversed(trace)]})
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--access", required=True, type=Path)
    parser.add_argument("--content-manifest", required=True, type=Path)
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--coarse-width", required=True, type=int)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    rep = reportmod.Report(sys.argv, task_id="M2-01")
    status = 0
    try:
        for name, path in [("access", args.access), ("content_manifest", args.content_manifest), ("native_probe", args.probe)]:
            rep.add_input(name, path, hashlib.sha256(path.read_bytes()).hexdigest())
        access = validate_document(json.loads(args.access.read_text()))
        validate_primary_access(access)
        rep.add_check("primary_reference_identity", "passed", detail="pinned core, ROM, manifest, inputs and complete capture verified")
        manifest = json.loads(args.content_manifest.read_text())
        if not 0 < args.coarse_width <= 65535:
            raise ValueError("coarse width must fit a nonzero u16")
        if access["rom"]["sha256"] != manifest["rom"]["sha256"]:
            raise ValueError("access/content ROM identity differs")
        if [item["id"] for item in manifest["items"]] != ["track-data", "collision-poses", "collision-templates"]:
            raise ValueError("expected the three movement sampling content items in order")
        paths = []
        for item in manifest["items"]:
            path = args.content / f"{item['id']}.bin"
            content = path.read_bytes()
            if len(content) != item["expected"]["length"] or hashlib.sha256(content).hexdigest() != item["expected"]["sha256"]:
                raise ValueError(f"content identity differs: {item['id']}")
            rep.add_input(item["id"], path, item["expected"]["sha256"])
            paths.append(path)
        rep.add_check("content_identity", "passed", detail="all three extracted content hashes match")
        cases = capture_cases(access, args.coarse_width)
        rep.add_check("complete_capture", "passed", detail=f"{len(cases)} calls, ten ordered samples each")
        stdin = ''.join(' '.join(map(str, case["input"])) + '\n' for case in cases)
        stdout, actual = run_probe([str(args.probe.resolve()), *map(str, paths)], stdin, len(cases), 10)
        rep.add_check("native_probe", "passed", detail="exit 0; complete native output")
        divergence = next(({"frame": case["frame"], "rider": case["rider"], "inputs": case["input"], "native": row, "reference": case["expected"]}
                           for case, row in zip(cases, actual, strict=True) if row != case["expected"]), None)
        rep.data["first_divergence"] = divergence
        output_path = args.report.with_suffix(".native.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(stdout)
        rep.add_artifact("native_output", output_path)
        rep.data["native_output_sha256"] = hashlib.sha256(stdout.encode()).hexdigest()
        rep.data["domain"] = "isolated sampler; captured incoming arguments; not a native gameplay replay"
        rep.add_check("sample_words_equal", "passed" if divergence is None else "failed", detail=f"{len(cases) * 10} words compared; first divergence {divergence}")
        status = 1 if divergence is not None else 0
    except NativeProbeFailure as error:
        rep.add_check("native_probe", "failed", detail=str(error))
        status = 1
    except FileNotFoundError as error:
        rep.add_check("prerequisite", "missing", detail=str(error))
        status = 2
    except (ValueError, KeyError) as error:
        rep.add_check("experiment_input", "failed", detail=str(error))
        status = 3
    except subprocess.TimeoutExpired as error:
        rep.add_check("native_probe", "timeout", detail=str(error))
        status = 4
    rep.finish("passed" if status == 0 else "failed")
    rep.write(args.report)
    print(f"probe status={status}; report={args.report}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
