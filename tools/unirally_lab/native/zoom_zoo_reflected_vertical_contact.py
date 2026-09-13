"""Reconstruct the bounded M4-07 reflected vertical-contact suffix.

The component evaluates captured incoming arguments against independently
authenticated content.  It composes the unchanged M4-06 prefix with the
observed ``0x4000`` player path; it is not an autonomous gameplay update.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ..reference.commands import compare_runs
from .contact_research.preprocess import expand_points
from .zoom_zoo_contact import (
    CONTRACT, CONTRACT_SHA256, PRIMARY, PRIMARY_SHA256, ROM_SHA256,
    captured_calls, compare_preprocessing, tile_index, validate_identity,
)
from .zoom_zoo_vertical_contact import (
    _arithmetic_shift_u16, _last_write, _signed16, attach_live_dependencies,
    compare_call as compare_original_vertical_call,
    extract_content as extract_vertical_content,
    load_content as load_vertical_content, reduce_vertical, sha256_bytes,
)


ROOT = Path(__file__).resolve().parents[3]
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1684.json"
VARIATION_SHA256 = "202403bebbf2ae281b625076cbedc1a807a7d239863daab2a629ce3e3c403b78"
COEFFICIENT_IDENTITY = (
    18, "f5016c76c1f4e60c988c67672b12da1d3b10948934f5f1e8b29135274203e7a1",
)


def extract_content(contract_path: Path, rom_path: Path, out: Path) -> None:
    """Reuse the accepted vertical inputs and add reached indices 6--8."""
    extract_vertical_content(contract_path, rom_path, out)
    rom = rom_path.read_bytes()
    if sha256_bytes(rom) != ROM_SHA256:
        raise ValueError("source ROM identity differs")
    coefficients = rom[0x022B:0x0234] + rom[0x024B:0x0254]
    length, digest = COEFFICIENT_IDENTITY
    if len(coefficients) != length or sha256_bytes(coefficients) != digest:
        raise ValueError("reflected vertical coefficient identity differs")
    (out / "reflected-vertical-slope-coefficients.bin").write_bytes(coefficients)
    metadata = {
        "schema_version": 1,
        "kind": "zoom_zoo_reflected_vertical_content",
        "rom_sha256": ROM_SHA256,
        "contract": {"path": str(contract_path), "sha256": CONTRACT_SHA256},
        "item": {"length": length, "sha256": digest},
        "reached_indices": [6, 7, 8],
    }
    (out / "reflected-content.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )


def load_content(directory: Path) -> dict[str, bytes]:
    content = load_vertical_content(directory)
    metadata = json.loads((directory / "reflected-content.json").read_text())
    length, digest = COEFFICIENT_IDENTITY
    expected = {
        "schema_version": 1,
        "kind": "zoom_zoo_reflected_vertical_content",
        "rom_sha256": ROM_SHA256,
        "contract": {"path": CONTRACT, "sha256": CONTRACT_SHA256},
        "item": {"length": length, "sha256": digest},
        "reached_indices": [6, 7, 8],
    }
    if metadata != expected:
        raise ValueError("reflected vertical content metadata differs")
    coefficients = (directory / "reflected-vertical-slope-coefficients.bin").read_bytes()
    if len(coefficients) != length or sha256_bytes(coefficients) != digest:
        raise ValueError("reflected vertical coefficient identity differs")
    content["reflected-vertical-slope-coefficients"] = coefficients
    return content


def preprocess_reflected_call(
    call: dict, content: dict[str, bytes]
) -> tuple[list[tuple[int, int, int]], list[dict]]:
    """Compute the observed mirrored-column, byte-negated-angle path."""
    incoming = call["input"]
    if call["rider"] != 0 or incoming["reflection"] != 1:
        raise ValueError("reflected player identity differs")
    points = expand_points(
        incoming["pose"], incoming["reflection"],
        content["collision-poses"], content["collision-templates"],
    )
    probes: list[tuple[int, int, int]] = []
    columns = []
    for point_index, (raw, point) in enumerate(zip(call["raw_samples"], points, strict=True)):
        if raw & 0x03FF == 0:
            probes.append((0xA0, 0, 0))
            columns.append({"point": point_index, "kind": "marker", "column": None})
            continue
        if raw & 0xC001 != 0x4000:
            raise ValueError("unobserved descriptor path in reflected suffix")
        tile = tile_index(raw)
        if content["tile-flags"][tile] & 1:
            raise ValueError("reflected suffix reaches horizontal geometry")
        direct_column = (point[0] + (incoming["x"] & 15)) & 15
        column = (~direct_column) & 15
        local_y = (point[1] + (incoming["y"] & 15)) & 15
        offset = tile * 32 + column * 2
        height, table_angle = content["tile-tables"][offset:offset + 2]
        angle = ((table_angle ^ 0xFF) + 1) & 0xFF
        penetration = (
            0xA0 if height == 0xA0
            else (local_y - ((height - 1) & 0xFF)) & 0xFF
        )
        probes.append((penetration, angle, raw))
        columns.append({
            "point": point_index, "kind": "reflected_vertical",
            "direct_column": direct_column, "column": column,
            "table_angle": table_angle, "computed_angle": angle,
        })
    return probes, columns


def response_scratch(summary: dict, incoming_vx: int, coefficients: bytes) -> dict:
    angle = summary["angle"] if summary["angle"] < 0x80 else summary["angle"] - 0x100
    magnitude = abs(angle)
    if len(coefficients) != 18 or magnitude > 8:
        raise ValueError("positive-slope coefficient dependency is missing")
    shifts, multipliers = coefficients[:9], coefficients[9:]
    if shifts[magnitude] >= 16:
        raise ValueError("positive-slope shift is outside the bounded domain")
    shifted = _arithmetic_shift_u16(incoming_vx, shifts[magnitude])
    contribution = (-(magnitude >> 1) if angle < 0 else magnitude >> 1) & 0xFFFF
    return {
        "shifted_velocity": shifted,
        "slope_multiplier": multipliers[magnitude],
        "angle_contribution": contribution,
        "coefficient_index": magnitude,
    }


def resolve_reflected_response(call: dict, summary: dict, coefficients: bytes) -> tuple[dict, dict]:
    """Resolve the observed continuous positive-slope response in original order."""
    incoming = call["input"]
    angle = summary["angle"] if summary["angle"] < 0x80 else summary["angle"] - 0x100
    if (
        not summary["supported"] or not 0 <= angle <= 8
        or incoming["unsupported_count"] >= 9
        or incoming["mode"] != 0 or incoming["special"] != 0
        or summary["selected_high"] & 0x80
    ):
        raise ValueError("response leaves the bounded reflected vertical family")
    scratch = response_scratch(summary, incoming["vx"], coefficients)
    product = (scratch["shifted_velocity"] * scratch["slope_multiplier"]) & 0xFFFF
    motion = {name: incoming[name] for name in (
        "x", "y", "vx", "vy", "response_a", "response_b", "response_impulse",
    )}
    if incoming["phase"] == 0:
        motion["response_a"] = 0
        motion["response_b"] = 0
    motion["vy"] = product
    motion["vx"] = (incoming["vx"] + _signed16(scratch["angle_contribution"])) & 0xFFFF
    motion["y"] = (incoming["y"] - summary["vertical_correction"]) & 0xFFFF
    state = {
        "unsupported_count": 0,
        "unsupported_duration": 0,
        "previous_unsupported_count": incoming["unsupported_count"],
        "previous_x": incoming["x"], "previous_y": incoming["y"],
        "surface_angle": angle & 0xFFFF, "angle_sentinel": 0,
        "auxiliary_flag": incoming["auxiliary_flag"],
        "selected_word": summary["selected_word"],
        "selected_high": summary["selected_high"], "recontact": 0,
    }
    return {"branch": "continuous_reflected", "motion": motion, "state": state}, scratch


def compare_reflected_call(call: dict, content: dict[str, bytes]) -> dict:
    probes, columns = preprocess_reflected_call(call, content)
    preprocessing = compare_preprocessing(call, probes)
    summary = reduce_vertical(probes, content["tile-flags"])
    expected = {
        "support_summary": call["support_summary"],
        "vertical_correction": call["classified"]["vertical_correction"],
        "angle": call["classified"]["angle"] & 0xFF,
        "selected_word": call["classified"]["selected_word"],
        "selected_high": call["classified"]["selected_high"],
        "tile_flags": call["classified"]["tile_flags"],
        "vertical_axis": call["classified"]["vertical_axis"],
        "horizontal_correction": call["classified"]["horizontal_correction"],
        "horizontal_axis": call["classified"]["horizontal_axis"],
    }
    for name, observed in expected.items():
        if summary[name] != observed:
            raise ValueError(f"computed reflected reducer differs at {call['frame']}: {name}")
    resolved, scratch = resolve_reflected_response(
        call, summary, content["reflected-vertical-slope-coefficients"],
    )
    comparisons = {
        "x": (resolved["motion"]["x"], call["published"]["x"]),
        "y": (resolved["motion"]["y"], call["published"]["y"]),
        "vx": (resolved["motion"]["vx"], call["published"]["vx"]),
        "vy": (resolved["motion"]["vy"], call["published"]["vy"]),
        "unsupported_count": (resolved["state"]["unsupported_count"], call["published"]["unsupported_count"]),
        "unsupported_duration": (resolved["state"]["unsupported_duration"], call["published"]["unsupported_duration"]),
        "previous_unsupported_count": (resolved["state"]["previous_unsupported_count"], call["output"]["previous_unsupported_count"]),
        "previous_x": (resolved["state"]["previous_x"], call["output"]["previous_x"]),
        "previous_y": (resolved["state"]["previous_y"], call["output"]["previous_y"]),
        "surface_angle": (resolved["state"]["surface_angle"], call["output"]["surface_angle"]),
        "angle_sentinel": (resolved["state"]["angle_sentinel"], call["output"]["angle_sentinel"]),
        "auxiliary_flag": (resolved["state"]["auxiliary_flag"], call["output"]["auxiliary_flag"]),
        "selected_word": (resolved["state"]["selected_word"], call["output"]["selected_word"]),
        "selected_high": (resolved["state"]["selected_high"], call["output"]["selected_high"]),
        "recontact": (resolved["state"]["recontact"], call["output"]["recontact"]),
        "response_a": (resolved["motion"]["response_a"], call["output"]["response_a"]),
        "response_b": (resolved["motion"]["response_b"], call["output"]["response_b"]),
        "response_impulse": (resolved["motion"]["response_impulse"], call["output"]["response_impulse"]),
    }
    for name, (computed, observed) in comparisons.items():
        if computed != observed:
            raise ValueError(f"computed reflected response differs at {call['frame']}: {name}")
    if _last_write(call, 0x02D4) != scratch["shifted_velocity"]:
        raise ValueError(f"computed shifted velocity differs at {call['frame']}")
    if _last_write(call, 0x0026) != scratch["angle_contribution"]:
        raise ValueError(f"computed angle contribution differs at {call['frame']}")
    return {
        "ordinal": call["ordinal"], "frame": call["frame"], "rider": call["rider"],
        "preprocessing": preprocessing, "columns": columns, "reducer": summary,
        "branch": resolved["branch"], "scratch": scratch,
        "response_and_publication": {
            name: {"computed": computed, "captured": observed, "match": True}
            for name, (computed, observed) in comparisons.items()
        },
    }


def suffix_inventory(calls: list[dict]) -> tuple[list[dict], bytes]:
    rows = []
    for call in calls:
        active = [raw for raw in call["raw_samples"] if raw & 0x03FF]
        paths = sorted({raw & 0xC001 for raw in active})
        rows.append({
            "ordinal": call["ordinal"], "frame": call["frame"], "rider": call["rider"],
            "active_points": len(active), "descriptor_paths": paths,
        })
    raw = (json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return rows, raw


def validate_manifest(manifest: dict) -> None:
    required = {
        "schema_version", "kind", "scenario_id", "description", "source",
        "capture_frames", "prefix", "suffix", "calls", "points", "access_sha256",
        "suffix_inventory_sha256", "static_content", "limits",
    }
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "zoom_zoo_reflected_vertical_reference":
        raise ValueError("reflected vertical manifest schema differs")
    if set(manifest) != required:
        raise ValueError("reflected vertical manifest shape differs")
    scenarios = {
        "race-crawler-zoom-zoo-3300": (PRIMARY, PRIMARY_SHA256, "267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67"),
        "race-crawler-zoom-zoo-right-release-1684": (VARIATION, VARIATION_SHA256, "4161f1de56bfe6bf893ab2a26ce6355d8fdb8109e20aeaf9dd6274a25d7762a9"),
    }
    if manifest.get("scenario_id") not in scenarios:
        raise ValueError("reflected vertical scenario differs")
    replay, replay_hash, access_hash = scenarios[manifest["scenario_id"]]
    expected_source = {
        "rom_sha256": ROM_SHA256,
        "core_commit": "7d5aa1e656b9171524d01b1b22917197d8121cb4",
        "core_patch_sha256": "a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885",
        "replay_manifest": replay, "replay_manifest_sha256": replay_hash,
    }
    if manifest["source"] != expected_source or manifest["access_sha256"] != access_hash:
        raise ValueError("reflected vertical source identity differs")
    if manifest["capture_frames"] != {"start": 1650, "end": 1700, "count": 51}:
        raise ValueError("reflected vertical capture range differs")
    if manifest["prefix"] != {"frames": [1650, 1682], "calls": 66, "points": 660}:
        raise ValueError("reflected vertical prefix identity differs")
    if manifest["suffix"] != {"frames": [1683, 1700], "calls": 36, "points": 360, "player_reflected": 18, "opponent_flat": 18}:
        raise ValueError("reflected vertical suffix identity differs")
    if manifest["calls"] != 102 or manifest["points"] != 1020:
        raise ValueError("reflected vertical composed inventory differs")
    expected_static = {
        "contract": CONTRACT, "contract_sha256": CONTRACT_SHA256,
        "coefficients_sha256": COEFFICIENT_IDENTITY[1], "reached_indices": [6, 7, 8],
    }
    if manifest["static_content"] != expected_static:
        raise ValueError("reflected vertical static content differs")


def verify(access_path: Path, content_dir: Path, manifest_path: Path, report_path: Path) -> int:
    access_raw = access_path.read_bytes(); access = json.loads(access_raw)
    manifest_raw = manifest_path.read_bytes(); manifest = json.loads(manifest_raw)
    validate_manifest(manifest)
    if sha256_bytes(access_raw) != manifest["access_sha256"]:
        raise ValueError("reflected vertical capture identity differs")
    validate_identity(access)
    if access["status"] != "complete" or access["watch_pcs_truncated"]:
        raise ValueError("complete nontruncated reflected evidence is required")
    if access["frames"] != manifest["capture_frames"]:
        raise ValueError("reflected vertical capture frame range differs")
    content = load_content(content_dir)
    calls = captured_calls(access); attach_live_dependencies(access, calls)
    if len(calls) != 102 or sum(len(c["raw_samples"]) for c in calls) != 1020:
        raise ValueError("composed call or point count differs")
    prefix, suffix = calls[:66], calls[66:]
    inventory, inventory_raw = suffix_inventory(suffix)
    if sha256_bytes(inventory_raw) != manifest["suffix_inventory_sha256"]:
        raise ValueError("reflected vertical suffix inventory differs")
    prefix_rows = [compare_original_vertical_call(call, content) for call in prefix]
    suffix_rows = []
    for call in suffix:
        if call["rider"] == 0:
            suffix_rows.append(compare_reflected_call(call, content))
        else:
            suffix_rows.append(compare_original_vertical_call(call, content))
    report = {
        "schema_version": 1, "kind": "zoom_zoo_reflected_vertical_component_report",
        "status": "passed", "access_sha256": sha256_bytes(access_raw),
        "manifest_sha256": sha256_bytes(manifest_raw),
        "calls": len(calls), "points": 1020,
        "prefix": {"calls": 66, "points": 660, "episode": prefix_rows},
        "suffix": {"calls": 36, "points": 360, "inventory": inventory, "episode": suffix_rows},
        "domain": "captured-argument reflected vertical research; no autonomous movement or production support",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def compare_inputs(primary_samples: Path, variation_samples: Path, report_path: Path) -> int:
    primary = json.loads(primary_samples.read_text())
    variation = json.loads(variation_samples.read_text())
    expected = (
        (primary, "791a786370913136e21ed34c841e9a3d892852bf6804e2e0aef21e1df6557b68", "2a843314d19e60d13dab746541d43ffa9ad84adfe6f95b9cc6d3c45bd9a16aeb"),
        (variation, "5685c085bb62aec5d93515197183d5fa0e3b469bdc19b36bcc568318b64d43eb", "037fee6dd7e6003ebca34ab45a16d7b70c95ac554d4d48b68658877df697eb00"),
    )
    for document, digest, final_state in expected:
        if not isinstance(document, dict) or document.get("schema_version") != 2 or len(document.get("frames", [])) != 3300:
            raise ValueError("comparison inputs must be complete sample documents")
        if document.get("sample_digest") != digest or document.get("final", {}).get("state_sha256") != final_state:
            raise ValueError("comparison sample identity differs")
    comparison = compare_runs(primary, variation)
    if comparison["only_in_x"] or comparison["only_in_y"] or comparison["first_differing_frame"] != 1684:
        raise ValueError("Right-release-1684 divergence differs")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_right_release_1684_comparison",
        "status": "passed", "exact_through": 1683, "first_divergence": 1684,
        "prediction": "exact through 1683 and first controller divergence 1684; no contact timing or reconvergence was preregistered",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract-content")
    extract.add_argument("--contract", type=Path, default=Path(CONTRACT))
    extract.add_argument("--rom", type=Path, required=True)
    extract.add_argument("--out", type=Path, required=True)
    check = commands.add_parser("verify")
    check.add_argument("--access", type=Path, required=True)
    check.add_argument("--content", type=Path, required=True)
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--report", type=Path, required=True)
    compare = commands.add_parser("compare-inputs")
    compare.add_argument("--primary", type=Path, required=True)
    compare.add_argument("--variation", type=Path, required=True)
    compare.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "extract-content":
            extract_content(args.contract, args.rom, args.out); return 0
        if args.command == "verify":
            return verify(args.access, args.content, args.manifest, args.report)
        if args.command == "compare-inputs":
            return compare_inputs(args.primary, args.variation, args.report)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        if isinstance(error, subprocess.TimeoutExpired): return 4
        return 3 if isinstance(error, ValueError) else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
