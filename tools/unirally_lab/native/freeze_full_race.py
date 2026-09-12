"""Freeze the M3-01 movement projection before native finish computation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ..replay.manifest import derive_script, range_fields, validate_manifest
from .freeze_reference import DIAGNOSTIC, PROJECTION, project


def freeze(manifest: dict, first: dict, second: dict, finish_contract: dict,
           case_name: str) -> dict:
    manifest = validate_manifest(manifest)
    case = next(item for item in finish_contract["cases"] if item["name"] == case_name)
    if case["sample_digest"] != manifest["expected"]["sample_digest"]:
        raise ValueError("finish contract and replay sample identities differ")
    script = (json.dumps(derive_script(manifest), indent=2, sort_keys=True) + "\n").encode()
    script_sha256 = hashlib.sha256(script).hexdigest()
    for run in (first, second):
        if run["script"]["sha256"] != script_sha256 or run["fields"] != range_fields(manifest):
            raise ValueError("reference input or field declarations differ")
        if run["sample_digest"] != case["sample_digest"]:
            raise ValueError("reference sample digest differs from the freeze contract")
        if run["rom"]["sha256"] != finish_contract["rom_sha256"]:
            raise ValueError("reference ROM differs from the freeze contract")
    if first["process"]["pid"] == second["process"]["pid"]:
        raise ValueError("reference processes must be distinct")
    if first["final"]["state_sha256"] != second["final"]["state_sha256"]:
        raise ValueError("reference final states differ")
    if len(first["frames"]) != manifest["run"]["frames"] or len(second["frames"]) != len(first["frames"]):
        raise ValueError("reference frame series is incomplete")
    last = case["first_result_transition_frame"] - 1
    rows = []
    for left, right in zip(first["frames"], second["frames"], strict=True):
        if left["frame"] != right["frame"] or left["fields"] != right["fields"]:
            raise ValueError(f"reference fields differ at frame {left['frame']}")
        if 1533 <= left["frame"] <= last:
            rows.append([left["frame"]] + project(left))
    return {
        "schema_version": 1,
        "kind": "frozen_full_race_movement_projection",
        "scenario_id": manifest["scenario_id"],
        "case_name": case_name,
        "rom_sha256": finish_contract["rom_sha256"],
        "core": manifest["core"],
        "reference_sample_digest": first["sample_digest"],
        "reference_final_state_sha256": first["final"]["state_sha256"],
        "initial_frame": 1533,
        "first_update_frame": 1534,
        "last_gameplay_frame": last,
        "last_frame": case["first_stable_result_frame"],
        "projection": PROJECTION,
        "diagnostic_only": DIAGNOSTIC,
        "columns": ["frame"] + [item["name"] for item in PROJECTION],
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--samples", required=True, type=Path, nargs=2)
    parser.add_argument("--finish-contract", required=True, type=Path)
    parser.add_argument("--case", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists")
    manifest_bytes = args.manifest.read_bytes()
    result = freeze(json.loads(manifest_bytes),
                    *(json.loads(path.read_bytes()) for path in args.samples),
                    json.loads(args.finish_contract.read_bytes()), args.case)
    result["replay_manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    result["finish_contract_sha256"] = hashlib.sha256(args.finish_contract.read_bytes()).hexdigest()
    rows = result.pop("rows")
    text = json.dumps(result, indent=2)[:-2] + ',\n  "rows": [\n'
    text += ',\n'.join('    ' + json.dumps(row, separators=(',', ':')) for row in rows)
    text += '\n  ]\n}\n'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"frozen {len(rows)} rows; sha256 {hashlib.sha256(args.out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
