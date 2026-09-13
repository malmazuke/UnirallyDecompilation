"""Reconstruct the bounded M4-06 ZOOM ZOO vertical-contact episode.

This research component evaluates captured incoming call arguments against
independently extracted static content. Captured preprocessing, reducer,
response and publication values are comparison targets, never inputs to the
calculation. It does not provide autonomous movement or production support.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ..content import rnc
from ..content.zoom_zoo_contract import _bus, _rom_slice
from ..content.zoom_zoo_contract import validate as validate_content_contract
from ..reference.commands import compare_runs
from .contact_research.preprocess import expand_points
from .contact_research.summarize import events_for_frame
from .zoom_zoo_contact import (
    CONTENT_IDENTITIES as FOUNDATION_CONTENT_IDENTITIES,
    CONTRACT,
    CONTRACT_SHA256,
    PRIMARY,
    PRIMARY_SHA256,
    ROM_SHA256,
    captured_calls,
    classify_calls,
    compare_preprocessing,
    tile_index,
    validate_identity,
)


ROOT = Path(__file__).resolve().parents[3]
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-1653-3300.json"
VARIATION_SHA256 = "5cfdd52e0a05ebcb9498a3f3da5fc3b1e6a411eb5286550868f4891b11ccf93d"
COEFFICIENT_IDENTITY = (
    12,
    "33cde9a32f2ba289253c747ffa9119a006ab4887766cec642ebef4b50acd9f86",
)
CONTENT_IDENTITIES = {
    **FOUNDATION_CONTENT_IDENTITIES,
    "vertical-slope-coefficients": COEFFICIENT_IDENTITY,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_content(contract_path: Path, rom_path: Path, out: Path) -> None:
    """Extract only authenticated static inputs used by this episode."""
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty content directory")
    contract_raw = contract_path.read_bytes()
    if sha256_bytes(contract_raw) != CONTRACT_SHA256:
        raise ValueError("accepted ZOOM ZOO content contract identity differs")
    contract = json.loads(contract_raw)
    rom = rom_path.read_bytes()
    if sha256_bytes(rom) != ROM_SHA256:
        raise ValueError("source ROM identity differs")
    validate_content_contract(contract, rom)

    source = contract["source"]
    source_bus = _bus(source["bus"], "source.bus")
    decoded, _ = rnc.decompress(
        rnc.lorom_reader(rom), source_bus >> 16, source_bus & 0xFFFF
    )
    entries = contract["load_contract"]["entries"]
    tables = b"".join(
        _rom_slice(rom, _bus(entry["table_source_bus"], "table"), entry["table_bytes"])
        for entry in entries
    )
    flags = b"".join(
        _rom_slice(rom, _bus(entry["flags_source_bus"], "flags"), entry["flags_bytes"])
        for entry in entries
    )
    collision = contract["collision_content"]
    poses = rom[
        collision["poses_file_offset"]:
        collision["poses_file_offset"] + collision["poses_length"]
    ]
    templates = rom[
        collision["templates_file_offset"]:
        collision["templates_file_offset"] + collision["templates_length"]
    ]
    payloads = {
        "track-data": decoded,
        "collision-poses": poses,
        "collision-templates": templates,
        "tile-tables": tables,
        "tile-flags": flags,
        # `$00:822B+abs(angle)` and `$00:824B+abs(angle)`, indices 0..5.
        "vertical-slope-coefficients": rom[0x022B:0x0231] + rom[0x024B:0x0251],
    }
    # Retain the accepted M4-05 two-byte subset as a separately authenticated
    # foundation input rather than silently changing its identity.
    payloads["slope-coefficients"] = bytes((rom[0x022C], rom[0x024C]))
    for name, payload in payloads.items():
        length, digest = CONTENT_IDENTITIES[name]
        if len(payload) != length or sha256_bytes(payload) != digest:
            raise ValueError(f"static content identity differs: {name}")
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (out / f"{name}.bin").write_bytes(payload)
    document = {
        "schema_version": 1,
        "kind": "zoom_zoo_vertical_contact_content",
        "contract": {"path": str(contract_path), "sha256": CONTRACT_SHA256},
        "rom_sha256": ROM_SHA256,
        "items": {
            name: {"length": len(payload), "sha256": sha256_bytes(payload)}
            for name, payload in payloads.items()
        },
    }
    (out / "content.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n"
    )


def load_content(directory: Path) -> dict[str, bytes]:
    document = json.loads((directory / "content.json").read_text())
    if document.get("schema_version") != 1 or document.get("kind") != "zoom_zoo_vertical_contact_content":
        raise ValueError("vertical-contact content metadata schema differs")
    if document.get("contract") != {"path": CONTRACT, "sha256": CONTRACT_SHA256}:
        raise ValueError("vertical-contact content contract differs")
    if document.get("rom_sha256") != ROM_SHA256 or set(document.get("items", {})) != set(CONTENT_IDENTITIES):
        raise ValueError("vertical-contact content source or inventory differs")
    result = {}
    for name, (length, digest) in CONTENT_IDENTITIES.items():
        payload = (directory / f"{name}.bin").read_bytes()
        if document["items"][name] != {"length": length, "sha256": digest}:
            raise ValueError(f"vertical-contact metadata differs: {name}")
        if len(payload) != length or sha256_bytes(payload) != digest:
            raise ValueError(f"vertical-contact content identity differs: {name}")
        result[name] = payload
    return result


def preprocess_call(call: dict, content: dict[str, bytes]) -> tuple[list[tuple[int, int, int]], list[dict]]:
    """Compute all ten tuples and distinguish written from stale axis bytes."""
    incoming = call["input"]
    points = expand_points(
        incoming["pose"], incoming["reflection"],
        content["collision-poses"], content["collision-templates"],
    )
    probes = []
    axes = []
    for point_index, (raw, point) in enumerate(zip(call["raw_samples"], points, strict=True)):
        if raw & 0x03FF == 0:
            probes.append((0xA0, 0, 0))
            axes.append({
                "point": point_index, "computed": "not_written",
                "captured": call["observed_axes"][point_index], "match": True,
            })
            continue
        if raw & 0xC001:
            raise ValueError(
                f"direction/special boundary at {call['frame']}/{call['rider']} point {point_index}"
            )
        tile = tile_index(raw)
        if content["tile-flags"][tile] & 1:
            raise ValueError("vertical episode reaches horizontal tile geometry")
        column = (point[0] + (incoming["x"] & 15)) & 15
        local_y = (point[1] + (incoming["y"] & 15)) & 15
        offset = tile * 32 + column * 2
        height, angle = content["tile-tables"][offset:offset + 2]
        penetration = 0xA0 if height == 0xA0 else (local_y - ((height - 1) & 0xFF)) & 0xFF
        probes.append((penetration, angle, raw))
        observed_axis = call["observed_axes"][point_index]
        if observed_axis != 0:
            raise ValueError(
                f"computed vertical axis differs at {call['frame']}/{call['rider']} point {point_index}"
            )
        axes.append({
            "point": point_index, "computed": 0,
            "captured": observed_axis, "match": True,
        })
    return probes, axes


def _nonnegative_u8_difference(left: int, right: int) -> bool:
    """Return true when N is clear after the original eight-bit subtraction."""
    return ((left - right) & 0x80) == 0


def reduce_vertical(probes: list[tuple[int, int, int]], flags: bytes) -> dict:
    """Translate the exercised ascending point reducer in original byte order."""
    if len(probes) != 10 or probes[0][0] != 0xA0:
        raise ValueError("first-point support is outside the bounded vertical episode")
    selected_word = 0
    support_summary = 0xFF
    vertical_correction = 0
    selected_high = 0
    last_winning_angle = 0xE0
    for point_index, (penetration, angle, raw) in enumerate(probes[1:], start=1):
        if penetration == 0xA0:
            if raw & 0x01FF and selected_word == 0:
                selected_word = raw
            continue
        if _nonnegative_u8_difference(penetration, support_summary):
            support_summary = penetration
            if raw & 1 or selected_word == 0:
                selected_word = raw
            if _nonnegative_u8_difference(angle, last_winning_angle):
                selected_high = raw >> 8
            last_winning_angle = angle
        # BMI at `$81:90EB` prevents signed-negative penetrations from
        # entering either correction axis. Ties update in point order.
        if penetration < 0x80 and _nonnegative_u8_difference(penetration, vertical_correction):
            vertical_correction = penetration
    return {
        "supported": support_summary < 0x80,
        "support_summary": support_summary,
        "vertical_correction": vertical_correction,
        "angle": last_winning_angle,
        "selected_word": selected_word,
        "selected_high": selected_high,
        "tile_flags": flags[tile_index(selected_word)],
        "vertical_axis": 0,
        "horizontal_correction": 0,
        "horizontal_axis": 0,
    }


def _signed16(value: int) -> int:
    return value if value < 0x8000 else value - 0x10000


def _arithmetic_shift_u16(value: int, count: int) -> int:
    return (_signed16(value) >> count) & 0xFFFF


def response_scratch(call: dict, summary: dict, coefficients: bytes) -> dict:
    if not summary["supported"]:
        return {"shifted_velocity": None, "angle_contribution": None}
    angle = summary["angle"] if summary["angle"] < 0x80 else summary["angle"] - 0x100
    magnitude = abs(angle)
    shifts = coefficients[:6]
    multipliers = coefficients[6:]
    if magnitude >= len(shifts) or shifts[magnitude] >= 16:
        raise ValueError("vertical slope coefficient dependency is missing")
    shifted = _arithmetic_shift_u16(call["input"]["vx"], shifts[magnitude])
    contribution = -(magnitude >> 1) if angle < 0 else magnitude >> 1
    return {
        "shifted_velocity": shifted,
        "slope_multiplier": multipliers[magnitude],
        "angle_contribution": contribution & 0xFFFF,
    }


def resolve_response(call: dict, summary: dict, coefficients: bytes) -> tuple[dict, dict]:
    """Compute the bounded unsupported, continuous and one recontact paths."""
    incoming = call["input"]
    motion = {name: incoming[name] for name in (
        "x", "y", "vx", "vy", "response_a", "response_b", "response_impulse"
    )}
    state = {name: incoming[name] for name in (
        "unsupported_count", "unsupported_duration", "surface_angle",
        "angle_sentinel", "auxiliary_flag",
    )}
    state.update({
        "previous_unsupported_count": incoming["unsupported_count"],
        "previous_x": incoming["x"], "previous_y": incoming["y"],
        "selected_word": summary["selected_word"],
        "selected_high": summary["selected_high"], "recontact": 0,
    })
    scratch = response_scratch(call, summary, coefficients)
    if not summary["supported"]:
        branch = "unsupported"
        state["unsupported_count"] = min(9, incoming["unsupported_count"] + 1)
        state["unsupported_duration"] = (incoming["unsupported_duration"] + 1) & 0xFFFF
        state["angle_sentinel"] = 1
        state["auxiliary_flag"] = 0
    else:
        angle = summary["angle"] if summary["angle"] < 0x80 else summary["angle"] - 0x100
        if abs(angle) > 5 or incoming["mode"] != 0 or incoming["special"] != 0:
            raise ValueError("response leaves the bounded vertical family")
        state["surface_angle"] = angle & 0xFFFF
        state["angle_sentinel"] = int(abs(angle) == 31)
        state["unsupported_count"] = 0
        state["unsupported_duration"] = 0
        if incoming["unsupported_count"] >= 9:
            branch = "recontact"
            if call["rider"] != 1 or summary["selected_high"] & 0x80:
                raise ValueError("recontact identity leaves the bounded episode")
            if call.get("live_dependencies") != {
                    "cartridge_option": 0xC200, "rider_selector": 2}:
                raise ValueError("recontact live option/rider dependency differs")
            dx = abs(_signed16((incoming["x"] - incoming["previous_x"]) & 0xFFFF))
            half_dy = abs(_signed16((incoming["y"] - incoming["previous_y"]) & 0xFFFF)) >> 1
            if half_dy == 0:
                raise ValueError("recontact coarse-angle divisor is zero")
            remainder = dx
            coarse_angle = 16
            while remainder - half_dy >= 0:
                remainder -= half_dy
                coarse_angle -= 4
            if abs(coarse_angle - _signed16(incoming["surface_angle"])) >= 5:
                raise ValueError("recontact coarse-angle bucket leaves the captured sentinel path")
            state["recontact"] = 1
            motion["response_a"] = 0
            motion["response_b"] = 0
            motion["response_impulse"] = 0
            scratch = {
                "shifted_velocity": None, "angle_contribution": None,
                "recontact_dx": dx, "recontact_half_dy": half_dy,
                "recontact_coarse_angle": coarse_angle,
                "recontact_bucket": 0xFFFF,
            }
        else:
            branch = "continuous"
            if summary["selected_high"] & 0x80:
                raise ValueError("selected direction bit leaves the vertical response")
            if incoming["phase"] == 0:
                motion["response_a"] = 0
                motion["response_b"] = 0
            magnitude = abs(angle)
            shifted = scratch["shifted_velocity"]
            product = (shifted * scratch["slope_multiplier"]) & 0xFFFF
            motion["vy"] = ((-product + 1) if angle < 0 else product) & 0xFFFF
            motion["vx"] = (incoming["vx"] + _signed16(scratch["angle_contribution"])) & 0xFFFF
    motion["y"] = (incoming["y"] - summary["vertical_correction"]) & 0xFFFF
    return {"branch": branch, "motion": motion, "state": state}, scratch


def _last_write(call: dict, address: int) -> int | None:
    values = [value for _pc, target, _width, value in call["writes"] if target == address]
    return values[-1] if values else None


def _writes(call: dict, address: int) -> list[int]:
    return [value for _pc, target, _width, value in call["writes"] if target == address]


def attach_live_dependencies(access: dict, calls: list[dict]) -> None:
    """Attach shared reads before later writers can change their values."""
    by_key = {(call["frame"], call["rider"]): call for call in calls}
    for frame in range(access["frames"]["start"], access["frames"]["end"] + 1):
        rider = -1
        active = None
        for _sequence, pc, kind, address, _width, value in events_for_frame(access, frame):
            if pc == 0x818F9D and kind == "write":
                rider += 1
                active = by_key[(frame, rider)]
                active["live_dependencies"] = {}
            if active is None or kind != "read":
                continue
            if pc == 0x8194A8 and address == 0x770750:
                active["live_dependencies"]["cartridge_option"] = value
            elif pc == 0x8194B4 and address == 0x0FF9:
                active["live_dependencies"]["rider_selector"] = value


def compare_call(call: dict, content: dict[str, bytes]) -> dict:
    probes, axes = preprocess_call(call, content)
    preprocessing = compare_preprocessing(call, probes)
    summary = reduce_vertical(probes, content["tile-flags"])
    classified = call["classified"]
    expected_summary = {
        "support_summary": call["support_summary"],
        "vertical_correction": classified["vertical_correction"],
        "angle": classified["angle"] & 0xFF,
        "selected_word": classified["selected_word"],
        "selected_high": classified["selected_high"],
        "tile_flags": classified["tile_flags"],
        "vertical_axis": classified["vertical_axis"],
        "horizontal_correction": classified["horizontal_correction"],
        "horizontal_axis": classified["horizontal_axis"],
    }
    for name, observed in expected_summary.items():
        if summary[name] != observed:
            raise ValueError(f"computed reducer differs at {call['frame']}/{call['rider']}: {name}")
    resolved, scratch = resolve_response(
        call, summary, content["vertical-slope-coefficients"]
    )
    output = call["output"]
    published = call["published"]
    comparisons = {
        "x": (resolved["motion"]["x"], published["x"]),
        "y": (resolved["motion"]["y"], published["y"]),
        "vx": (resolved["motion"]["vx"], published["vx"]),
        "vy": (resolved["motion"]["vy"], published["vy"]),
        "unsupported_count": (resolved["state"]["unsupported_count"], published["unsupported_count"]),
        "unsupported_duration": (resolved["state"]["unsupported_duration"], published["unsupported_duration"]),
        "previous_unsupported_count": (resolved["state"]["previous_unsupported_count"], output["previous_unsupported_count"]),
        "previous_x": (resolved["state"]["previous_x"], output["previous_x"]),
        "previous_y": (resolved["state"]["previous_y"], output["previous_y"]),
        "surface_angle": (resolved["state"]["surface_angle"], output["surface_angle"]),
        "angle_sentinel": (resolved["state"]["angle_sentinel"], output["angle_sentinel"]),
        "auxiliary_flag": (resolved["state"]["auxiliary_flag"], output["auxiliary_flag"]),
        "selected_word": (resolved["state"]["selected_word"], output["selected_word"]),
        "selected_high": (resolved["state"]["selected_high"], output["selected_high"]),
        "recontact": (resolved["state"]["recontact"], output["recontact"]),
        "response_a": (resolved["motion"]["response_a"], output["response_a"]),
        "response_b": (resolved["motion"]["response_b"], output["response_b"]),
        "response_impulse": (resolved["motion"]["response_impulse"], output["response_impulse"]),
    }
    for name, (computed, observed) in comparisons.items():
        if computed != observed:
            raise ValueError(f"computed response/publication differs at {call['frame']}/{call['rider']}: {name}")
    if scratch["shifted_velocity"] is not None:
        observed_shifted = _last_write(call, 0x02D4)
        observed_contribution = _last_write(call, 0x0026)
        if observed_shifted != scratch["shifted_velocity"]:
            raise ValueError(f"computed shifted-velocity scratch differs at {call['frame']}/{call['rider']}")
        if observed_contribution != scratch["angle_contribution"]:
            raise ValueError(f"computed angle-contribution scratch differs at {call['frame']}/{call['rider']}")
    if resolved["branch"] == "recontact":
        observed_scratch = {
            "recontact_dx": _writes(call, 0x0250)[0],
            "recontact_half_dy": _writes(call, 0x0252)[0],
            "recontact_coarse_angle": _writes(call, 0x0254)[-2],
            "recontact_bucket": _writes(call, 0x00A3)[-1],
        }
        for name, observed in observed_scratch.items():
            if scratch[name] != observed:
                raise ValueError(f"computed recontact scratch differs at {call['frame']}/{call['rider']}: {name}")
    return {
        "ordinal": call["ordinal"], "frame": call["frame"], "rider": call["rider"],
        "preprocessing": preprocessing, "axes": axes, "reducer": summary,
        "branch": resolved["branch"], "scratch": scratch,
        "response_and_publication": {
            name: {"computed": computed, "captured": observed, "match": True}
            for name, (computed, observed) in comparisons.items()
        },
    }


def compact_classification(calls: list[dict], flags: bytes) -> tuple[list[dict], bytes]:
    rows = classify_calls(calls, flags)
    compact = [{
        "ordinal": row["ordinal"], "frame": row["frame"], "rider": row["rider"],
        "first_incompatible": row["first_incompatible"],
    } for row in rows]
    raw = (json.dumps(compact, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return compact, raw


def validate_manifest(manifest: dict) -> None:
    expected_keys = {
        "schema_version", "kind", "scenario_id", "description", "source",
        "capture_frames", "episode_frames", "calls", "points", "access_sha256",
        "classification_sha256", "classification_counts", "direction_boundary",
        "static_content", "limits",
    }
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "zoom_zoo_vertical_contact_reference":
        raise ValueError("vertical-contact manifest schema differs")
    if set(manifest) != expected_keys:
        raise ValueError("vertical-contact manifest shape differs")
    sources = {
        "race-crawler-zoom-zoo-3300": (PRIMARY, PRIMARY_SHA256),
        "race-crawler-zoom-zoo-right-1653-3300": (VARIATION, VARIATION_SHA256),
    }
    if manifest.get("scenario_id") not in sources:
        raise ValueError("vertical-contact scenario differs")
    replay, replay_hash = sources[manifest["scenario_id"]]
    expected_source = {
        "rom_sha256": ROM_SHA256,
        "core_commit": "7d5aa1e656b9171524d01b1b22917197d8121cb4",
        "core_patch_sha256": "a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885",
        "replay_manifest": replay,
        "replay_manifest_sha256": replay_hash,
    }
    if manifest["source"] != expected_source:
        raise ValueError("vertical-contact source identity differs")
    expected_episode = {
        "race-crawler-zoom-zoo-3300": {
            "capture_frames": {"start": 1650, "end": 1682, "count": 33},
            "episode_frames": {"start": 1650, "end": 1682, "count": 33},
            "calls": 66, "points": 660,
            "access_sha256": "c270cb19d28cab4e07044fcbde8e673f09c3aa79eeb13d3614f9b1e52a080f05",
            "classification_sha256": "f480ef6841d9c52de16dfb3203ac1ea1eda0648b55b6478e874472627bae574c",
            "classification_counts": {"compatible": 49, "non_flat_angle": 17, "direction_or_special": 0},
            "direction_boundary": None,
        },
        "race-crawler-zoom-zoo-right-1653-3300": {
            "capture_frames": {"start": 1650, "end": 1700, "count": 51},
            "episode_frames": {"start": 1650, "end": 1685, "count": 36},
            "calls": 72, "points": 720,
            "access_sha256": "1965151f925d0917c01f400f2cffd2431db5da39fa664a7bae8def2707b4d21e",
            "classification_sha256": "40db34d7fd2ce13b582f6333b9bcef9087824d9d05ae964fd7aee53bbd24878d",
            "classification_counts": {"compatible": 70, "non_flat_angle": 17, "direction_or_special": 15},
            "direction_boundary": {
                "ordinal": 72, "frame": 1686, "rider": 0,
                "first_incompatible": {"point": 8, "predicate": "direction_or_special"},
            },
        },
    }[manifest["scenario_id"]]
    for name, expected in expected_episode.items():
        if manifest[name] != expected:
            raise ValueError(f"vertical-contact authored identity differs: {name}")
    if manifest["static_content"] != {
        "contract": CONTRACT,
        "contract_sha256": CONTRACT_SHA256,
        "vertical_slope_coefficients_sha256": COEFFICIENT_IDENTITY[1],
    }:
        raise ValueError("vertical-contact static-content identity differs")


def verify(access_path: Path, content_dir: Path, manifest_path: Path, report_path: Path) -> int:
    access_raw = access_path.read_bytes()
    access = json.loads(access_raw)
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    validate_manifest(manifest)
    if sha256_bytes(access_raw) != manifest["access_sha256"]:
        raise ValueError("vertical-contact capture identity differs")
    validate_identity(access)
    if access["status"] != "complete" or access["watch_pcs_truncated"]:
        raise ValueError("complete nontruncated vertical-contact evidence is required")
    if access["frames"] != manifest["capture_frames"]:
        raise ValueError("vertical-contact capture frame range differs")
    content = load_content(content_dir)
    all_calls = captured_calls(access)
    attach_live_dependencies(access, all_calls)
    compact, compact_raw = compact_classification(all_calls, content["tile-flags"])
    if sha256_bytes(compact_raw) != manifest["classification_sha256"]:
        raise ValueError("vertical-contact classification identity differs")
    counts = {"compatible": 0, "non_flat_angle": 0, "direction_or_special": 0}
    for row in compact:
        key = "compatible" if row["first_incompatible"] is None else row["first_incompatible"]["predicate"]
        if key not in counts:
            raise ValueError(f"unexpected vertical-contact classification: {key}")
        counts[key] += 1
    if counts != manifest["classification_counts"]:
        raise ValueError("vertical-contact classification counts differ")
    boundary = next((row for row in compact if row["first_incompatible"] and row["first_incompatible"]["predicate"] == "direction_or_special"), None)
    if boundary != manifest["direction_boundary"]:
        raise ValueError("direction/special boundary differs")
    episode = [call for call in all_calls if manifest["episode_frames"]["start"] <= call["frame"] <= manifest["episode_frames"]["end"]]
    if len(episode) != manifest["calls"] or sum(len(call["raw_samples"]) for call in episode) != manifest["points"]:
        raise ValueError("vertical-contact call or point inventory differs")
    rows = [compare_call(call, content) for call in episode]
    report = {
        "schema_version": 1, "kind": "zoom_zoo_vertical_contact_component_report",
        "status": "passed", "access_sha256": sha256_bytes(access_raw),
        "manifest_sha256": sha256_bytes(manifest_raw), "calls": len(rows),
        "points": sum(len(row["preprocessing"]) for row in rows),
        "classification_sha256": sha256_bytes(compact_raw),
        "direction_boundary": boundary, "episode": rows,
        "domain": "captured-argument vertical-contact research; no autonomous movement or production native support",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def compare_inputs(primary_samples: Path, variation_samples: Path, report_path: Path) -> int:
    primary = json.loads(primary_samples.read_text())
    variation = json.loads(variation_samples.read_text())
    if not isinstance(primary, dict) or not isinstance(variation, dict):
        raise ValueError("comparison inputs must be complete sample documents")
    expected = (
        (primary, "791a786370913136e21ed34c841e9a3d892852bf6804e2e0aef21e1df6557b68",
         "2a843314d19e60d13dab746541d43ffa9ad84adfe6f95b9cc6d3c45bd9a16aeb",
         "3f51305c6bb71556ac672a03590998d62dba4cc7e51ae940a39caf8b49af5eaa"),
        (variation, "b17677ef0a910d82fb2cd9b8270328f1cc261a6267e6f373cd0af20dfeee5bbb",
         "d3fbf5dd2d56c941ac1515c1d84aa3f528c29353f8c4ee8cd6e6237afd569951",
         "7b7561dc5960416631969ebe667efc95fc07f338f76b58459948cb197625ba28"),
    )
    for document, digest, final_state, script in expected:
        if document.get("schema_version") != 2 or len(document.get("frames", [])) != 3300:
            raise ValueError("comparison sample shape or frame count differs")
        if document.get("sample_digest") != digest:
            raise ValueError("comparison sample identity differs")
        if document.get("final", {}).get("state_sha256") != final_state:
            raise ValueError("comparison final-state identity differs")
        if document.get("script", {}).get("sha256") != script:
            raise ValueError("comparison script identity differs")
    comparison = compare_runs(primary, variation)
    if comparison["only_in_x"] or comparison["only_in_y"]:
        raise ValueError("comparison frame sets differ")
    first = comparison["first_differing_frame"]
    if first != 1650:
        raise ValueError("Right-1653 first state divergence differs")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_right_1653_comparison",
        "status": "passed", "exact_through": 1649, "first_divergence": 1650,
        "prediction": "exact through 1649 and first input divergence 1650; no contact timing was preregistered",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract-content")
    extract.add_argument("--contract", type=Path, default=Path(CONTRACT))
    extract.add_argument("--rom", type=Path, required=True)
    extract.add_argument("--out", type=Path, required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--access", type=Path, required=True)
    verify_parser.add_argument("--content", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)
    verify_parser.add_argument("--report", type=Path, required=True)
    compare = subparsers.add_parser("compare-inputs")
    compare.add_argument("--primary", type=Path, required=True)
    compare.add_argument("--variation", type=Path, required=True)
    compare.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "extract-content":
            extract_content(args.contract, args.rom, args.out)
            return 0
        if args.command == "verify":
            return verify(args.access, args.content, args.manifest, args.report)
        if args.command == "compare-inputs":
            return compare_inputs(args.primary, args.variation, args.report)
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        if isinstance(error, subprocess.TimeoutExpired):
            return 4
        return 3 if isinstance(error, ValueError) else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
