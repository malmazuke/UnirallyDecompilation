"""Capture and inspect the bounded M4-05 ZOOM ZOO contact experiment.

This module is research-only. It records original calls and never drives the
production native movement implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ..content import rnc
from ..content.zoom_zoo_contract import validate as validate_content_contract
from ..content.zoom_zoo_contract import _bus, _rom_slice
from .contact_research.preprocess import expand_points
from .contact_research.summarize import (
    calls as response_calls,
    events_for_frame,
    put,
    validate_identity,
    word,
)


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-1652-3300.json"
VARIATION_SHA256 = "4bfda9be656118c39c64b6e1c0027b15a8a6de3d7736c86a166cf7e0d056df71"
ROM_SHA256 = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
CONTRACT = "tests/manifests/content/zoom-zoo-reference-contract.json"
CONTRACT_SHA256 = "017a4eb941abb0e87ea0e3be4509d9043198466cb461f560517f355938c1d699"
CONTENT_IDENTITIES = {
    "track-data": (50665, "db6770152e399f9d16fc6937b5d56588a8f67e825ae70d6578b77d36053fdd28"),
    "collision-poses": (32768, "9d1754d38c20cb2900239557550211ab6fc23d9b0237e17b78fb29f3bf272c32"),
    "collision-templates": (17249, "2f03a8cb985899436603ef36b233b28f7b4213e4ba106fca328a6b02cdb081c7"),
    "tile-tables": (6496, "649b96ff43ef467fe57bac16eb876f96a1ebc6f0307a5270f97a7ce1f63a84c7"),
    "tile-flags": (203, "11aa211a148bced17e6c1b63a19e6e9c71ff1f8fed83954613f2ea62b15069c4"),
    "slope-coefficients": (2, "38b8bc5c86db41a80615b2f4694fc754cccffb95e8933d5b376021feab83cea3"),
}

# Complete contact scratch, direct-page arguments, caller publications and
# persistent fields used by the bounded response. Multi-byte accesses are
# deduplicated by the access derivation and later call parser.
WATCH_ADDRESSES = sorted(set(
    list(range(0x20, 0x30))
    + list(range(0xA3, 0xAA))
    + list(range(0x230, 0x2F2))
    + list(range(0xF13, 0xFC2))
    + list(range(0xB5A, 0xB76))
    + [
        0x300, 0x302, 0x333, 0x4EF, 0xDE7, 0xEED, 0xEEF, 0xEF1,
        0xFF9, 0x1279, 0x132B, 0x1349, 0x770750,
    ]
))

# Snapshots are pre-instruction. These landmarks expose actual guard order,
# table indices and caller/response boundaries; ordering itself comes from the
# watched access sequence numbers, never from separate snapshot arrays.
WATCH_PCS = [
    0x818B75, 0x818B98, 0x818BB5, 0x818BE3, 0x818C0C, 0x818CBB,
    0x818CDD, 0x818CD6, 0x818CF3,
    0x818DB9, 0x818DBC, 0x818F0D, 0x818F10,
    0x818F98, 0x818F9D, 0x818FDC, 0x818FEB, 0x81905C, 0x819065,
    0x81908B, 0x819098, 0x8190BE, 0x8190E8, 0x8190F2, 0x8190F9,
    0x819114, 0x819132, 0x81917C, 0x819235, 0x81923A, 0x81924E,
    0x8192CE, 0x8194C5, 0x8194CA, 0x81960A, 0x81970B, 0x81980C,
    0x819610, 0x819617, 0x81961C, 0x819650, 0x819661, 0x819696,
    0x8196AA, 0x8196AC, 0x8196B0, 0x8196B6, 0x8196C2, 0x8196C8,
    0x8196CD, 0x8196D0, 0x8196D7, 0x8196DE, 0x8196E1, 0x8196EC,
    0x8196FA, 0x81970B, 0x81970E, 0x8197B7, 0x8197CA, 0x8197E1,
    0x81982B, 0x81982C, 0x8198DC,
    0x818DBF, 0x818F13,
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(manifest: Path, out: Path, first: int, last: int) -> int:
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty capture directory")
    raw = manifest.read_bytes()
    if manifest.as_posix().endswith(PRIMARY) and hashlib.sha256(raw).hexdigest() != PRIMARY_SHA256:
        raise ValueError("accepted primary replay manifest identity differs")
    out.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(first), "--to-frame", str(last),
        "--wram-series-range", "0", "0x2200", "--timeout", "180",
        "--report", str(out / "report.json"),
    ]
    for address in WATCH_ADDRESSES:
        command += ["--watch-address", hex(address)]
    for pc in WATCH_PCS:
        command += ["--watch-pc", hex(pc)]
    (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    return subprocess.run(command, timeout=200).returncode


def extract_content(contract_path: Path, rom_path: Path, out: Path) -> None:
    """Derive the authenticated static inputs without using captured bytes."""
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty content directory")
    contract_raw = contract_path.read_bytes()
    if hashlib.sha256(contract_raw).hexdigest() != CONTRACT_SHA256:
        raise ValueError("accepted ZOOM ZOO content contract identity differs")
    contract = json.loads(contract_raw)
    rom_bytes = rom_path.read_bytes()
    if hashlib.sha256(rom_bytes).hexdigest() != ROM_SHA256:
        raise ValueError("source ROM identity differs")
    # The accepted M4-03 validator independently re-derives every declared
    # loader entry and collision read before this component writes any bytes.
    validate_content_contract(contract, rom_bytes)
    source = contract["source"]
    decoded, _ = rnc.decompress(
        rnc.lorom_reader(rom_bytes), _bus(source["bus"], "source.bus") >> 16,
        _bus(source["bus"], "source.bus") & 0xFFFF,
    )
    entries = contract["load_contract"]["entries"]
    tables = b"".join(_rom_slice(rom_bytes, _bus(e["table_source_bus"], "table"), e["table_bytes"]) for e in entries)
    flags = b"".join(_rom_slice(rom_bytes, _bus(e["flags_source_bus"], "flags"), e["flags_bytes"]) for e in entries)
    collision = contract["collision_content"]
    poses = rom_bytes[collision["poses_file_offset"]:collision["poses_file_offset"] + collision["poses_length"]]
    templates = rom_bytes[collision["templates_file_offset"]:collision["templates_file_offset"] + collision["templates_length"]]
    # `$00:822B+abs(angle)` and `$00:824B+abs(angle)` are the two tables
    # reached by the first slope case. Only index one is in M4-05 scope.
    coefficients = bytes((rom_bytes[0x022C], rom_bytes[0x024C]))
    payloads = {
        "track-data": decoded,
        "collision-poses": poses,
        "collision-templates": templates,
        "tile-tables": tables,
        "tile-flags": flags,
        "slope-coefficients": coefficients,
    }
    for name, payload in payloads.items():
        length, digest = CONTENT_IDENTITIES[name]
        if len(payload) != length or hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError(f"static content identity differs: {name}")
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (out / f"{name}.bin").write_bytes(payload)
    document = {
        "schema_version": 1,
        "kind": "zoom_zoo_contact_content",
        "contract": {"path": str(contract_path), "sha256": CONTRACT_SHA256},
        "rom_sha256": ROM_SHA256,
        "items": {name: {"length": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in payloads.items()},
    }
    (out / "content.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")


def load_content(directory: Path) -> dict[str, bytes]:
    document = json.loads((directory / "content.json").read_text())
    if document.get("schema_version") != 1 or document.get("kind") != "zoom_zoo_contact_content":
        raise ValueError("contact content metadata schema differs")
    if document.get("contract") != {"path": CONTRACT, "sha256": CONTRACT_SHA256} or document.get("rom_sha256") != ROM_SHA256:
        raise ValueError("contact content source identity differs")
    if set(document.get("items", {})) != set(CONTENT_IDENTITIES):
        raise ValueError("contact content inventory differs")
    result = {}
    for name, (length, digest) in CONTENT_IDENTITIES.items():
        path = directory / f"{name}.bin"
        data = path.read_bytes()
        declared = document["items"][name]
        if declared != {"length": length, "sha256": digest} or len(data) != length or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"contact content identity differs: {name}")
        result[name] = data
    return result


def captured_calls(access: dict) -> list[dict]:
    """Bind preprocessing arguments to response calls in actual call order."""
    observations = response_calls(access)
    arguments = []
    for frame in range(access["frames"]["start"], access["frames"]["end"] + 1):
        memory: dict[int, int] = {}
        rider = 0
        for event in events_for_frame(access, frame):
            _seq, pc, kind, address, width, value = event
            if pc == 0x818F9D and kind == "write":
                arguments.append({
                    "frame": frame,
                    "rider": rider,
                    "raw_samples": [word(memory, 0x260 + 2 * index) for index in range(10)],
                    "observed_penetrations": [memory.get(0x230 + 2 * index) for index in range(10)],
                    "observed_angles": [memory.get(0x231 + 2 * index) for index in range(10)],
                    "observed_axes": [memory.get(0x290 + 2 * index) for index in range(10)],
                    "observed_descriptors": [word(memory, 0x2C0 + 2 * index) for index in range(10)],
                })
                rider += 1
            put(memory, address, width, value)
        if rider != 2:
            raise ValueError(f"frame {frame}: expected two captured argument rows, got {rider}")
    if len(arguments) != len(observations):
        raise ValueError("captured argument and response call counts differ")
    result = []
    for ordinal, (argument, observation) in enumerate(zip(arguments, observations, strict=True)):
        if (argument["frame"], argument["rider"]) != (observation["frame"], observation["rider"]):
            raise ValueError("captured argument/response order differs")
        for key in ("raw_samples", "observed_penetrations", "observed_angles", "observed_descriptors"):
            if any(value is None for value in argument[key]):
                raise ValueError(f"captured argument row is incomplete: {key}")
        result.append({"ordinal": ordinal, **argument, **observation})
    validate_call_sequence(result, access["frames"]["start"], access["frames"]["end"])
    return result


def validate_call_sequence(calls: list[dict], first: int, last: int) -> None:
    expected = [(frame, rider) for frame in range(first, last + 1) for rider in (0, 1)]
    actual = [(call.get("frame"), call.get("rider")) for call in calls]
    if actual != expected or [call.get("ordinal") for call in calls] != list(range(len(expected))):
        raise ValueError("call presence, order, rider or ordinal differs")


def tile_index(descriptor: int) -> int:
    return ((descriptor & 0x03F0) >> 2) + ((descriptor & 0x000F) >> 1)


def classify_calls(calls: list[dict], flags: bytes) -> list[dict]:
    """Classify every call in the native guard order without widening scope."""
    rows = []
    for call in calls:
        first_failure = None
        samples = []
        for index, (raw, penetration, angle, axis, descriptor) in enumerate(zip(
                call["raw_samples"], call["observed_penetrations"], call["observed_angles"],
                call["observed_axes"], call["observed_descriptors"], strict=True)):
            guards = []
            marker = (raw & 0x03FF) == 0
            guards.append({"predicate": "marker_empty", "result": marker})
            failure = None
            if not marker:
                direction = (raw & 0xC001) != 0
                guards.append({"predicate": "direction_or_special", "result": direction})
                if direction:
                    failure = "direction_or_special"
                else:
                    horizontal = (flags[tile_index(raw)] & 1) != 0
                    guards.append({"predicate": "horizontal_tile_flag", "result": horizontal})
                    if horizontal:
                        failure = "horizontal_tile_flag"
                    else:
                        nonflat = angle != 0
                        guards.append({"predicate": "non_flat_angle", "result": nonflat})
                        if nonflat:
                            failure = "non_flat_angle"
                        elif penetration != 0xA0:
                            negative = (penetration & 0x80) != 0
                            guards.append({"predicate": "negative_penetration", "result": negative})
                            if negative:
                                failure = "negative_penetration"
            if failure is not None and first_failure is None:
                first_failure = {"point": index, "predicate": failure}
            samples.append({
                "point": index, "raw": raw, "descriptor": descriptor,
                "penetration": penetration, "angle": angle, "axis": axis,
                "guards": guards, "first_incompatible": failure,
            })
        rows.append({
            "ordinal": call["ordinal"], "frame": call["frame"], "rider": call["rider"],
            "first_incompatible": first_failure, "samples": samples,
        })
    return rows


def preprocess_neighbourhood(call: dict, content: dict[str, bytes], allow_slope: bool) -> list[tuple[int, int, int]]:
    incoming = call["input"]
    points = expand_points(incoming["pose"], incoming["reflection"], content["collision-poses"], content["collision-templates"])
    result = []
    for raw, point in zip(call["raw_samples"], points, strict=True):
        if raw & 0x03FF == 0:
            result.append((0xA0, 0, 0))
            continue
        if raw & 0xC001:
            raise ValueError("neighbourhood reaches direction/special geometry")
        tile = tile_index(raw)
        if content["tile-flags"][tile] & 1:
            raise ValueError("neighbourhood reaches horizontal geometry")
        column = (point[0] + (incoming["x"] & 15)) & 15
        local_y = (point[1] + (incoming["y"] & 15)) & 15
        offset = tile * 32 + column * 2
        height, angle = content["tile-tables"][offset:offset + 2]
        if angle not in ((0, 0xFF) if allow_slope else (0,)):
            raise ValueError("neighbourhood reaches an unrecovered slope")
        penetration = 0xA0 if height == 0xA0 else (local_y - ((height - 1) & 0xFF)) & 0xFF
        if penetration & 0x80:
            raise ValueError("neighbourhood reaches negative penetration")
        result.append((penetration, angle, raw))
    return result


def reduce_neighbourhood(probes: list[tuple[int, int, int]], flags: bytes) -> dict[str, int | bool]:
    if probes[0][0] != 0xA0:
        raise ValueError("neighbourhood reaches first-probe support")
    selected = 0
    deepest = 0xFF
    correction = 0
    selected_high = 0
    angle = 0xE0
    for index, (penetration, slope, raw) in enumerate(probes[1:], start=1):
        if penetration == 0xA0:
            if raw & 0x01FF and selected == 0:
                selected = raw
            continue
        if index < 2:
            raise ValueError("neighbourhood reaches second-probe support")
        if ((penetration - deepest) & 0x80) == 0:
            deepest = penetration
            if selected == 0:
                selected = raw
            selected_high = raw >> 8
            angle = slope
        correction = max(correction, penetration)
    return {
        "supported": (deepest & 0x80) == 0,
        "support_summary": deepest,
        "vertical_correction": correction,
        "angle": angle,
        "selected_word": selected,
        "selected_high": selected_high,
        "tile_flags": flags[tile_index(selected)],
    }


def compare_preprocessing(call: dict, probes: list[tuple[int, int, int]]) -> list[dict]:
    """Require and report every captured preprocessing result in point order."""
    if len(probes) != 10:
        raise ValueError("computed preprocessing point count differs")
    captured = list(zip(
        call["observed_penetrations"], call["observed_angles"],
        call["observed_descriptors"], strict=True,
    ))
    if len(captured) != 10:
        raise ValueError("captured preprocessing point count differs")
    comparisons = []
    for point, (computed, observed) in enumerate(zip(probes, captured, strict=True)):
        if computed != observed:
            raise ValueError(
                f"computed preprocessing differs at {call['frame']}/{call['rider']} "
                f"point {point}: computed {computed}, captured {observed}"
            )
        values = {
            "penetration": computed[0], "angle": computed[1],
            "descriptor": computed[2],
        }
        comparisons.append({
            "point": point, "computed": values,
            "captured": dict(values), "match": True,
        })
    return comparisons


def resolve_neighbourhood(call: dict, summary: dict, coefficients: bytes) -> dict:
    if len(coefficients) != 2 or coefficients[0] >= 16:
        raise ValueError("slope coefficient dependency is missing or invalid")
    incoming = call["input"]
    motion = {name: incoming[name] for name in ("x", "y", "vx", "vy", "response_a", "response_b", "response_impulse")}
    state = {name: incoming[name] for name in (
        "unsupported_count", "unsupported_duration", "previous_x", "previous_y",
        "surface_angle", "angle_sentinel", "auxiliary_flag",
    )}
    state.update({"previous_unsupported_count": incoming["unsupported_count"], "selected_word": summary["selected_word"],
                  "selected_high": summary["selected_high"], "recontact": 0})
    if not summary["supported"]:
        state["unsupported_count"] = min(9, incoming["unsupported_count"] + 1)
        state["unsupported_duration"] = (incoming["unsupported_duration"] + 1) & 0xFFFF
        state["angle_sentinel"] = 1
        state["auxiliary_flag"] = 0
    else:
        if incoming["unsupported_count"] >= 9:
            raise ValueError("neighbourhood reaches recontact")
        signed_angle = summary["angle"] if summary["angle"] < 0x80 else summary["angle"] - 0x100
        if signed_angle not in (0, -1) or incoming["vy"] >= 0x8000:
            raise ValueError("neighbourhood reaches an unrecovered response")
        state["surface_angle"] = signed_angle & 0xFFFF
        state["angle_sentinel"] = int(abs(signed_angle) == 31)
        state["unsupported_count"] = 0
        state["unsupported_duration"] = 0
        if incoming["phase"] == 0:
            motion["response_a"] = motion["response_b"] = 0
        if signed_angle == 0:
            motion["vy"] = 0
        else:
            shift, multiplier = coefficients
            scaled = incoming["vx"] >> shift
            product = (scaled * multiplier) & 0xFFFF
            motion["vy"] = (-product + 1) & 0xFFFF
            contribution = -(abs(signed_angle) >> 1)
            motion["vx"] = (incoming["vx"] + contribution) & 0xFFFF
    state["previous_x"] = incoming["x"]
    state["previous_y"] = incoming["y"]
    motion["y"] = (incoming["y"] - summary["vertical_correction"]) & 0xFFFF
    return {"motion": motion, "state": state}


def verify_neighbourhood(calls: list[dict], content: dict[str, bytes], target_ordinal: int) -> list[dict]:
    if not 0 < target_ordinal < len(calls) - 1:
        raise ValueError("branch neighbourhood has no preceding or following call")
    selected_calls = calls[target_ordinal - 1:target_ordinal + 2]
    selected = {(call["frame"], call["rider"]) for call in selected_calls}
    target_key = (calls[target_ordinal]["frame"], calls[target_ordinal]["rider"])
    rows = []
    for call in calls:
        if (call["frame"], call["rider"]) not in selected:
            continue
        probes = preprocess_neighbourhood(call, content, allow_slope=(call["frame"], call["rider"]) == target_key)
        if (call["frame"], call["rider"]) == target_key and call["observed_axes"][9] != 0:
            raise ValueError("first slope call's vertical axis selector is missing or differs")
        preprocessing = compare_preprocessing(call, probes)
        summary = reduce_neighbourhood(probes, content["tile-flags"])
        resolved = resolve_neighbourhood(call, summary, content["slope-coefficients"])
        expected_summary = {
            "support_summary": call["support_summary"],
            "vertical_correction": call["classified"]["vertical_correction"],
            "angle": call["classified"]["angle"] & 0xFF,
            "selected_word": call["classified"]["selected_word"],
            "selected_high": call["classified"]["selected_high"],
            "tile_flags": call["classified"]["tile_flags"],
        }
        for name, expected in expected_summary.items():
            if summary[name] != expected:
                raise ValueError(f"computed summary differs at {call['frame']}/{call['rider']}: {name}")
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
                raise ValueError(f"computed output differs at {call['frame']}/{call['rider']}: {name}")
        rows.append({"frame": call["frame"], "rider": call["rider"],
                     "preprocessing": preprocessing, "summary": summary,
                     "changed_outputs": {name: computed for name, (computed, _) in comparisons.items()}})
    if [(row["frame"], row["rider"]) for row in rows] != [
            (call["frame"], call["rider"]) for call in selected_calls]:
        raise ValueError("preceding/target/following call evidence is incomplete")
    return rows


def validate_component_manifest(manifest: dict) -> None:
    """Exact-bind the authored component contract before reading evidence."""
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "zoom_zoo_contact_reference":
        raise ValueError("component manifest schema differs")
    expected_keys = {"schema_version", "kind", "scenario_id", "description", "source", "frames", "calls",
                     "access_sha256", "classification_sha256", "guard_order", "classification_counts",
                     "first_incompatible", "branch_neighbourhood", "static_content", "limits"}
    if set(manifest) != expected_keys or manifest.get("scenario_id") not in {
            "race-crawler-zoom-zoo-3300", "race-crawler-zoom-zoo-right-1652-3300"}:
        raise ValueError("component manifest shape or scenario differs")
    source_manifest = manifest["source"].get("replay_manifest")
    allowed_sources = {PRIMARY: PRIMARY_SHA256, VARIATION: VARIATION_SHA256}
    expected_scenario = {
        PRIMARY: "race-crawler-zoom-zoo-3300",
        VARIATION: "race-crawler-zoom-zoo-right-1652-3300",
    }.get(source_manifest)
    if manifest["scenario_id"] != expected_scenario:
        raise ValueError("component scenario/source pairing differs")
    expected_source = {
        "rom_sha256": ROM_SHA256,
        "core_commit": "7d5aa1e656b9171524d01b1b22917197d8121cb4",
        "core_patch_sha256": "a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885",
        "replay_manifest": source_manifest,
        "replay_manifest_sha256": allowed_sources.get(source_manifest),
    }
    if manifest["source"] != expected_source or manifest["frames"] != {"start": 1650, "end": 1700, "count": 51}:
        raise ValueError("component source or frame identity differs")
    if manifest["guard_order"] != ["marker_empty", "direction_or_special", "horizontal_tile_flag", "non_flat_angle", "negative_penetration"]:
        raise ValueError("guard order differs")
    if manifest["static_content"].get("contract") != CONTRACT or manifest["static_content"].get("contract_sha256") != CONTRACT_SHA256:
        raise ValueError("static-content contract identity differs")


def verify_component(access_path: Path, content_dir: Path, manifest_path: Path, report_path: Path) -> int:
    access_raw = access_path.read_bytes()
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    validate_component_manifest(manifest)
    if manifest.get("access_sha256") != hashlib.sha256(access_raw).hexdigest():
        raise ValueError("contact capture identity differs")
    access = json.loads(access_raw)
    validate_identity(access)
    if access["frames"] != {"start": 1650, "end": 1700, "count": 51} or access["status"] != "complete" or access["watch_pcs_truncated"]:
        raise ValueError("complete 1650--1700 evidence is required")
    content = load_content(content_dir)
    calls = captured_calls(access)
    classifications = classify_calls(calls, content["tile-flags"])
    compact = [{"ordinal": row["ordinal"], "frame": row["frame"], "rider": row["rider"],
                "first_incompatible": row["first_incompatible"]} for row in classifications]
    compact_raw = (json.dumps(compact, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(calls) != manifest.get("calls") or hashlib.sha256(compact_raw).hexdigest() != manifest.get("classification_sha256"):
        raise ValueError("call classification identity differs")
    first = next((row for row in compact if row["first_incompatible"] is not None), None)
    if first != manifest.get("first_incompatible"):
        raise ValueError("first incompatible call differs")
    target_ordinal = first["ordinal"]
    expected_neighbourhood = [
        {"frame": calls[target_ordinal - 1]["frame"], "rider": calls[target_ordinal - 1]["rider"], "role": "preceding_call"},
        {"frame": calls[target_ordinal]["frame"], "rider": calls[target_ordinal]["rider"], "role": "first_incompatible_call"},
        {"frame": calls[target_ordinal + 1]["frame"], "rider": calls[target_ordinal + 1]["rider"], "role": "following_call"},
    ]
    if manifest["branch_neighbourhood"] != expected_neighbourhood:
        raise ValueError("branch neighbourhood differs")
    counts = {"compatible": 0, "non_flat_angle": 0, "direction_or_special": 0}
    for row in compact:
        key = "compatible" if row["first_incompatible"] is None else row["first_incompatible"]["predicate"]
        if key not in counts:
            raise ValueError(f"unexpected classified predicate: {key}")
        counts[key] += 1
    if counts != manifest["classification_counts"]:
        raise ValueError("classification counts differ")
    neighbourhood = verify_neighbourhood(calls, content, target_ordinal)
    report = {
        "schema_version": 1, "kind": "zoom_zoo_contact_component_report", "status": "passed",
        "access_sha256": hashlib.sha256(access_raw).hexdigest(), "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "calls": len(calls), "classification_sha256": hashlib.sha256(compact_raw).hexdigest(),
        "first_incompatible": first, "neighbourhood": neighbourhood,
        "domain": "captured-argument research component; no autonomous movement or production native support",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--manifest", type=Path, default=Path(PRIMARY))
    capture_parser.add_argument("--out", type=Path, required=True)
    capture_parser.add_argument("--from-frame", type=int, default=1650)
    capture_parser.add_argument("--to-frame", type=int, default=1700)
    extract_parser = subparsers.add_parser("extract-content")
    extract_parser.add_argument("--contract", type=Path, default=Path(CONTRACT))
    extract_parser.add_argument("--rom", type=Path, required=True)
    extract_parser.add_argument("--out", type=Path, required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--access", type=Path, required=True)
    verify_parser.add_argument("--content", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)
    verify_parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "capture":
            return capture(args.manifest, args.out, args.from_frame, args.to_frame)
        if args.command == "extract-content":
            extract_content(args.contract, args.rom, args.out)
            return 0
        if args.command == "verify":
            return verify_component(args.access, args.content, args.manifest, args.report)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        return 3 if isinstance(error, ValueError) else 4 if isinstance(error, subprocess.TimeoutExpired) else 2
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
