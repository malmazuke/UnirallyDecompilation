"""Freeze M2-01 reference fields; this module computes no native gameplay.

Run both reference processes with ``replay compare`` first. This utility
checks their identities and all eleven declared ranges, then writes only
projected observations. It refuses to overwrite an existing expectation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ..replay.manifest import derive_script, range_fields

PROJECTION = [
    {"name": name, "field": name, "offset": 0, "length": length, "signed": signed}
    for name, length, signed in [
        ("joy1l_image", 1, False), ("joy1h_image", 1, False),
        ("axis_v", 1, False), ("axis_h", 1, False), ("pos_x", 2, False),
        ("displacement_x", 2, True), ("throttle", 2, True), ("speed", 2, True),
    ]
] + [
    {"name": name, "field": "timer", "offset": index * 4, "length": 1, "signed": False}
    for index, name in enumerate(["timer_minutes", "timer_tens_seconds", "timer_seconds", "timer_tenths", "timer_frames"])
]
DIAGNOSTIC = [
    {"field": "pos_x", "offsets": [2, 3], "reason": "opponent position"},
    {"field": "timer", "offsets": [i for i in range(20) if i % 4], "reason": "non-digit bytes"},
    {"field": "jump_height", "offsets": [0, 1], "reason": "jump outside riding scope"},
    {"field": "camera_x", "offsets": [0, 1], "reason": "camera outside movement projection"},
]


def project(sample: dict) -> list[int]:
    values = []
    for item in PROJECTION:
        data = bytes.fromhex(sample["fields"][item["field"]])
        data = data[item["offset"]:item["offset"] + item["length"]]
        if len(data) != item["length"]:
            raise ValueError("projected field is truncated")
        values.append(int.from_bytes(data, "little", signed=item["signed"]))
    return values


def freeze(manifest: dict, first: dict, second: dict) -> dict:
    script_bytes = (json.dumps(derive_script(manifest), indent=2, sort_keys=True) + "\n").encode()
    script_sha256 = hashlib.sha256(script_bytes).hexdigest()
    for run in (first, second):
        if run["script"]["sha256"] != script_sha256:
            raise ValueError("reference input script differs from manifest")
        if run["fields"] != range_fields(manifest):
            raise ValueError("reference field declarations differ from manifest")
        if run["sample_digest"] != manifest["expected"]["sample_digest"]:
            raise ValueError("reference digest differs from frozen replay expectation")
        if run["core"]["serialization_method"] != manifest["core"]["serialization_method"]:
            raise ValueError("reference serialization method differs")
        if run["rom"]["sha256"] != manifest["rom"]["sha256"]:
            raise ValueError("ROM identity differs")
        if [sample["frame"] for sample in run["frames"]] != list(range(3000)):
            raise ValueError("expected exactly frames 0..2999")
    if first["process"]["pid"] == second["process"]["pid"]:
        raise ValueError("reference processes must be distinct")
    for key in ("sample_digest", "av_digest"):
        if first[key] != second[key]:
            raise ValueError(f"reference {key} differs")
    if first["final"]["state_sha256"] != second["final"]["state_sha256"]:
        raise ValueError("reference final state differs")
    if first["fields"] != second["fields"]:
        raise ValueError("reference declarations differ")
    for left, right in zip(first["frames"], second["frames"], strict=True):
        if left["fields"] != right["fields"]:
            raise ValueError(f"reference fields differ at {left['frame']}")
    return {
        "schema_version": 1,
        "kind": "frozen_reference_projection",
        "scenario_id": manifest["scenario_id"],
        "rom_sha256": manifest["rom"]["sha256"],
        "core": manifest["core"],
        "reference_sample_digest": first["sample_digest"],
        "reference_final_state_sha256": first["final"]["state_sha256"],
        "initial_frame": 1533,
        "first_update_frame": 1534,
        "last_frame": 2999,
        "projection": PROJECTION,
        "diagnostic_only": DIAGNOSTIC,
        "columns": ["frame"] + [item["name"] for item in PROJECTION],
        "rows": [[s["frame"]] + project(s) for s in first["frames"] if s["frame"] >= 1533],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--samples", required=True, type=Path, nargs=2)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output already exists; freeze into a new path and compare it")
    manifest = json.loads(args.manifest.read_text())
    first, second = (json.loads(path.read_text()) for path in args.samples)
    result = freeze(manifest, first, second)
    result["replay_manifest_sha256"] = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
    # Compact rows avoid turning a bounded observation into a large trace.
    rows = result.pop("rows")
    text = json.dumps(result, indent=2)[:-2] + ',\n  "rows": [\n'
    text += ',\n'.join('    ' + json.dumps(row, separators=(',', ':')) for row in rows)
    text += '\n  ]\n}\n'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"frozen {len(rows)} reference samples: {args.out}; sha256 {hashlib.sha256(args.out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
