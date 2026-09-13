"""Preregistered M4-10 response-B producer and recurrence experiment.

This additive research surface observes original execution only. It does not
modify or invoke production native gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .zoom_zoo_composition import (
    WATCH_ADDRESSES as COMPOSITION_WATCH_ADDRESSES,
    WATCH_PCS as COMPOSITION_WATCH_PCS,
    _digest,
    compare_composed_contact,
    composition_rows,
    load_content,
)
from .zoom_zoo_contact import captured_calls
from .zoom_zoo_position import _series_rows
from .zoom_zoo_vertical_contact import attach_live_dependencies
from .contact_research.summarize import events_for_frame, validate_identity


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1668.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION_SHA256 = "852351c866a35462caddf07bb58338e3887fe342ad2bf6c6059cc1018552d898"
FIRST_CAPTURE_FRAME = 1649
LAST_CAPTURE_FRAME = 1700
ROM_SHA256 = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
PRODUCER_ROM_SHA256 = "92c1eda01ff0d0fe27d8e5a6f6744216c86105457f53410e0f133aa148531c96"
CAPTURE_IDENTITIES = {
    "race-crawler-zoom-zoo-3300": (
        PRIMARY, PRIMARY_SHA256,
        "f8488406dc6efb29fa09918c6425416c6d9d8184a9e5ea2c2394d14904b25bcd",
        "53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d",
    ),
    "race-crawler-zoom-zoo-right-release-1668": (
        VARIATION, VARIATION_SHA256,
        "e2e526937b2c9ccc20d9183c5af76f9bde1456ddb7535db9d83904edc8de6f54",
        "1f5f269efb0cf7de0e22a0bf77045ed395bce9692f0c2b0ff2534304451077d9",
    ),
}
COMPONENT_MANIFEST_SHA256 = {
    "race-crawler-zoom-zoo-3300": "6d5d4b0f1dae3b83e8c85b8d289b95d9e1a47eeb79089fd0d34382a50a5e6684",
    "race-crawler-zoom-zoo-right-release-1668": "eee84520ac15a32fc7f8b23cfc5d76a14a71f25a6b5d696c5aa2f16f804a8f8d",
}
MANIFEST_FIELDS = {"schema_version", "kind", "source", "frames", "calls", "seed",
                   "rows_sha256", "writer_counts", "active_counts", "transition_254_to_0",
                   "final_response_b", "pose_comparisons", "composition",
                   "external_producer_inputs", "producer_routine", "description", "limits"}

# Address watches expose the actual PCs and widths of every read/write. Broad
# scratch/persistent ranges retain adjacent overlap needed to distinguish the
# two response words and orientation state without assigning meanings early.
RESPONSE_WATCH_ADDRESSES = sorted(set(
    list(range(0x0BB3, 0x0BBB))
    + list(range(0x0F51, 0x0F5B))
    + list(range(0x0F7F, 0x0FB0))
    + [0x0300, 0x0302, 0x031D, 0x031F, 0x04C7, 0x0DE7, 0x0DE9,
       0x0FF9, 0x1003, 0x1005]
))
WATCH_ADDRESSES = sorted(set(COMPOSITION_WATCH_ADDRESSES + RESPONSE_WATCH_ADDRESSES))

# Watching each byte is deliberate: capture records only actual instruction
# starts, while preregistration does not silently omit a decoded branch target.
PRODUCER_PC_RANGE = list(range(0x82A49F, 0x82A5FA))
POSE_PC_RANGE = list(range(0x83EF54, 0x83F0FB))
ORDER_PCS = [
    0x818B75, 0x818CF4, 0x818F98,  # sampling/contact boundaries
    0x82A49F, 0x82A5F9,            # suspected producer entry/exit
    0x83CD8B, 0x83CD94,            # pose publication before contact
]
WATCH_PCS = sorted(set(COMPOSITION_WATCH_PCS + PRODUCER_PC_RANGE + POSE_PC_RANGE + ORDER_PCS))

MOTION_BOUNDARIES = {
    0: {"load_read": 0x828A9A, "load_write": 0x828A9D,
        "publish_read": 0x828DA0, "publish_write": 0x828DA3,
        "persistent": 0x0BB7},
    1: {"load_read": 0x828FA2, "load_write": 0x828FA5,
        "publish_read": 0x82928E, "publish_write": 0x829291,
        "persistent": 0x0BB9},
}


def _u16(value: int) -> int:
    return value & 0xFFFF


def _s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def evaluate_active_producer(incoming: int, inputs: dict[str, int | None]) -> dict[str, int | str | None]:
    """Translate the response-B writes reached in `$82:A49F--A5F9`.

    The initial predicates and angle arithmetic are 16-bit. After `$82:A4CA`
    the mode is 8-bit until either the low-byte writer or the word-clear path
    explicitly restores 16-bit accumulator width. A low-byte store therefore
    preserves the incoming high byte.
    """
    def required(name: str) -> int:
        value = inputs[name]
        if value is None:
            raise ValueError(f"producer evidence omits reached input {name}")
        return int(value)

    f1b = _u16(required("f1b"))
    # The first conjunction short-circuits: a zero F1B does not read F1D.
    # Keep that omitted input unavailable unless a later reached predicate
    # supplies it; do not turn absence into a guessed zero.
    if f1b:
        if _u16(required("f1d")):
            return {"branch": "word_clear_initial_pair", "width": 2, "value": 0}
    angle = abs(_s16(required("surface_angle")))
    if angle < 30 and _s16(_u16(required("unsupported_count") - 9)) < 0:
        return {"branch": "word_clear_low_angle_count", "width": 2, "value": 0}
    if required("guard_f49") & 0xFF:
        return {"branch": "word_clear_f49", "width": 2, "value": 0}
    if required("guard_f89") & 0xFF:
        return {"branch": "word_clear_f89", "width": 2, "value": 0}
    if required("mode_f23") & 0xFF:
        return {"branch": "preserve_mode", "width": None, "value": _u16(incoming)}
    if required("special_f5d") & 0xFF:
        return {"branch": "preserve_special", "width": None, "value": _u16(incoming)}
    f1d = _u16(required("f1d"))
    if f1d == 0 and f1b == 0:
        return {"branch": "word_clear_zero_pair", "width": 2, "value": 0}
    control = required("indexed_control") & 0xFF
    if f1d == 0 and f1b != 0:
        low = (0xFE + control) & 0xFF
        return {"branch": "low_byte_fe_plus_control", "width": 1,
                "value": (incoming & 0xFF00) | low}
    if f1d != 0 and f1b == 0:
        low = (2 - control) & 0xFF
        return {"branch": "low_byte_two_minus_control", "width": 1,
                "value": (incoming & 0xFF00) | low}
    raise ValueError("unreachable response-B producer pair")


def _one(block: list[tuple], pc: int, kind: str, address: int | None = None,
         required: bool = True) -> tuple | None:
    rows = [event for event in block if event[1] == pc and event[2] == kind
            and (address is None or event[3] == address)]
    if not rows and not required:
        return None
    if len(rows) != 1 or rows[0][5] is None:
        raise ValueError(f"expected one complete ${pc:06X} {kind} event")
    return rows[0]


def _producer_inputs(block: list[tuple], indexed_control: int) -> dict[str, int | None]:
    def optional(pc: int, address: int) -> int | None:
        row = _one(block, pc, "read", address, required=False)
        return None if row is None else int(row[5])

    first_f1b = int(_one(block, 0x82A4A1, "read", 0x0F1B)[5])
    early_f1d = optional(0x82A4A6, 0x0F1D)
    f1d = early_f1d
    if f1d is None:
        f1d = optional(0x82A4EC, 0x0F1D)
    if f1d is None:
        f1d = optional(0x82A55D, 0x0F1D)
    later_f1b = optional(0x82A4F4, 0x0F1B)
    if later_f1b is None:
        later_f1b = optional(0x82A4FF, 0x0F1B)
    control_events = [event for event in block if event[1] in (0x82A50A, 0x82A565)
                      and event[2] == "read" and event[3] in (0x031D, 0x031F)]
    if len(control_events) > 1:
        raise ValueError("producer has duplicate indexed-control reads")
    values: dict[str, int | None] = {
        "f1b": first_f1b,
        "f1d": f1d,
        "surface_angle": optional(0x82A4B1, 0x0F17),
        "unsupported_count": optional(0x82A4BF, 0x0F33),
        "guard_f49": optional(0x82A4CC, 0x0F49),
        "guard_f89": optional(0x82A4D4, 0x0F89),
        "mode_f23": optional(0x82A4DC, 0x0F23),
        "special_f5d": optional(0x82A4E4, 0x0F5D),
        # The access decoder resolves the indexed address but the trace ring
        # does not carry this read value. The caller supplies the byte from the
        # preceding authenticated end-of-frame WRAM row after proving there is
        # no intervening watched writer.
        "indexed_control": indexed_control if control_events else None,
    }
    if later_f1b is not None and later_f1b != first_f1b:
        raise ValueError("producer F1B changed inside one invocation")
    return values


def _event_block(access: dict, frame: int, rider: int) -> tuple[list[tuple], dict]:
    events = events_for_frame(access, frame)
    boundary = MOTION_BOUNDARIES[rider]
    start = _one(events, boundary["load_read"], "read", boundary["persistent"])
    load = _one(events, boundary["load_write"], "write", 0x0F57)
    publish_read = _one(events, boundary["publish_read"], "read", 0x0F57)
    end = _one(events, boundary["publish_write"], "write", boundary["persistent"])
    if not (start[0] < load[0] < publish_read[0] < end[0]):
        raise ValueError(f"frame {frame} rider {rider}: response-B motion order differs")
    return [event for event in events if load[0] < event[0] < publish_read[0]], {
        "persistent_input": int(start[5]), "scratch_load": int(load[5]),
        "scratch_publication": int(publish_read[5]), "persistent_publication": int(end[5]),
        "sequence": [start[0], load[0], publish_read[0], end[0]],
    }


def _phase_for_frame(access: dict, frame: int) -> int:
    writes = [event for event in events_for_frame(access, frame)
              if event[2] == "write" and event[3] == 0x0302 and event[0] < 5000]
    if not writes or writes[-1][5] is None:
        raise ValueError(f"frame {frame}: active phase publication is missing")
    phase = int(writes[-1][5]) & 0xFF
    if phase not in (0, 1):
        raise ValueError(f"frame {frame}: active phase is outside 0/1")
    return phase


def _seed_responses(access_path: Path, access: dict) -> tuple[dict[int, int], str]:
    series = _series_rows(access_path, access, [1649])[1649]
    def word(address: int) -> int:
        return series[address] | series[address + 1] << 8
    return {0: word(0x0BB7), 1: word(0x0BB9)}, access["wram_series"]["sha256"]


def validate_recurrence_chain(rows: list[dict], seed: dict[int, int],
                              first_frame: int = 1650) -> None:
    """Reject replacement, rider/order, phase, writer and publication gaps."""
    required = {"ordinal", "frame", "rider", "phase_0302", "active",
                "recurrent_input", "producer_inputs", "producer", "pose_consumed",
                "motion_publication", "contact_input", "contact_output"}
    recurrent = {0: _u16(seed[0]), 1: _u16(seed[1])}
    for ordinal, row in enumerate(rows):
        if set(row) != required:
            raise ValueError("response-B row schema differs or captured substitution was added")
        expected = (ordinal, first_frame + ordinal // 2, ordinal & 1)
        if (row["ordinal"], row["frame"], row["rider"]) != expected:
            raise ValueError("response-B call order or rider differs")
        rider = row["rider"]
        if row["recurrent_input"] != recurrent[rider]:
            raise ValueError("response-B chain was reseeded or replaced")
        active = rider == 1 - row["phase_0302"]
        if row["active"] is not active:
            raise ValueError("response-B active phase differs")
        producer = row["producer"]
        if active:
            if row["producer_inputs"] is None:
                raise ValueError("active response-B producer inputs are omitted")
            computed = evaluate_active_producer(recurrent[rider], row["producer_inputs"])
            if producer != computed:
                raise ValueError("response-B producer writer/result differs")
        elif producer != {"branch": "inactive_preserve", "width": None,
                          "value": recurrent[rider]} or row["producer_inputs"] is not None:
            raise ValueError("inactive response-B preservation differs")
        produced = int(producer["value"])
        if (row["pose_consumed"], row["motion_publication"], row["contact_input"]) != (
                produced, produced, produced):
            raise ValueError("response-B pose/contact publication order differs")
        recurrent[rider] = _u16(row["contact_output"])


def response_composition(access_path: Path, content_dir: Path) -> tuple[list[dict], dict]:
    access_raw = access_path.read_bytes()
    access = json.loads(access_raw)
    validate_identity(access)
    if access.get("frames") != {"start": 1649, "end": 1700, "count": 52}:
        raise ValueError("response-B capture frame domain differs")
    if access.get("status") != "complete" or access.get("watch_pcs_truncated"):
        raise ValueError("complete nontruncated response-B capture is required")
    if access.get("residual", {}).get("unresolved_stores") != 0:
        raise ValueError("response-B capture has unresolved stores")
    scenario = access.get("scenario_id")
    if scenario not in CAPTURE_IDENTITIES:
        raise ValueError("response-B scenario differs")
    replay, replay_sha, access_sha, series_sha = CAPTURE_IDENTITIES[scenario]
    if access["manifest"] != {"path": replay, "sha256": replay_sha}:
        raise ValueError("response-B replay binding differs")
    if hashlib.sha256(access_raw).hexdigest() != access_sha:
        raise ValueError("response-B access identity differs")
    if access["wram_series"]["sha256"] != series_sha:
        raise ValueError("response-B WRAM-series identity differs")

    # Running the frozen M4-09 evaluator first proves the accepted eight-word
    # recurrence and all 1,020 authenticated samples still hold on this capture.
    composition, composition_meta = composition_rows(access_path, content_dir)
    all_calls = captured_calls(access)
    attach_live_dependencies(access, all_calls)
    calls = [call for call in all_calls if call["frame"] >= 1650]
    if len(calls) != 102 or len(composition) != 102:
        raise ValueError("response-B composition call count differs")
    recurrent, seed_series_sha = _seed_responses(access_path, access)
    series = _series_rows(access_path, access, range(1649, 1701))
    seed = {"frame": 1649, "player_response_b": recurrent[0],
            "opponent_response_b": recurrent[1], "wram_series_sha256": seed_series_sha}
    rows = []
    writer_counts: dict[str, int] = {}
    active_counts = {"player": 0, "opponent": 0}
    transition = None
    content = load_content(content_dir)
    for ordinal, (call, accepted_row) in enumerate(zip(calls, composition, strict=True)):
        frame, rider = call["frame"], call["rider"]
        if (ordinal, frame, rider) != (accepted_row["ordinal"], accepted_row["frame"], accepted_row["rider"]):
            raise ValueError("response-B and accepted composition order differ")
        block, motion = _event_block(access, frame, rider)
        incoming = recurrent[rider]
        if motion["persistent_input"] != incoming or motion["scratch_load"] != incoming:
            raise ValueError(f"frame {frame} rider {rider}: response-B did not consume recurrent state")
        phase = _phase_for_frame(access, frame)
        active_rider = 1 - phase
        inputs = None
        if rider == active_rider:
            active_counts["player" if rider == 0 else "opponent"] += 1
            control_address = 0x031D + rider * 2
            control_reads = [event for event in block if event[1] in (0x82A50A, 0x82A565)
                             and event[2] == "read"]
            if control_reads:
                if len(control_reads) != 1 or control_reads[0][3] != control_address:
                    raise ValueError("producer indexed-control address differs")
                before = [event for event in events_for_frame(access, frame)
                          if event[0] < control_reads[0][0] and event[2] in ("write", "rmw")
                          and event[3] <= control_address < event[3] + event[4]]
                if before:
                    last = before[-1]
                    if last[5] is None:
                        raise ValueError("producer indexed-control writer value is unresolved")
                    control_value = (int(last[5]) >> (8 * (control_address - last[3]))) & 0xFF
                else:
                    control_value = series[frame - 1][control_address]
            else:
                control_value = series[frame - 1][control_address]
            inputs = _producer_inputs(block, control_value)
            producer = evaluate_active_producer(incoming, inputs)
            writer_pc = {1: 0x82A568, 2: 0x82A5B9, None: None}[producer["width"]]
            writes = [event for event in block if event[2] == "write" and event[3] == 0x0F57
                      and event[1] in (0x82A568, 0x82A5B9)]
            if writer_pc is None:
                if writes:
                    raise ValueError("preserve producer unexpectedly wrote response B")
            elif len(writes) != 1 or writes[0][1] != writer_pc or writes[0][4] != producer["width"] or writes[0][5] != producer["value"]:
                raise ValueError(f"frame {frame} rider {rider}: instruction-derived producer differs")
        else:
            if any(event[1] == 0x82A4A1 for event in block):
                raise ValueError("inactive rider unexpectedly entered response-B producer")
            producer = {"branch": "inactive_preserve", "width": None, "value": incoming}
        produced = int(producer["value"])
        writer_counts[str(producer["branch"])] = writer_counts.get(str(producer["branch"]), 0) + 1
        pose_reads = [event for event in block if event[1] == 0x83F00D and event[2] == "read" and event[3] == 0x0F57]
        if len(pose_reads) != 1 or pose_reads[0][5] != produced:
            raise ValueError(f"frame {frame} rider {rider}: pose did not consume computed response B")
        if motion["scratch_publication"] != produced or motion["persistent_publication"] != produced:
            raise ValueError(f"frame {frame} rider {rider}: motion response-B publication differs")
        if call["input"]["response_b"] != produced:
            raise ValueError(f"frame {frame} rider {rider}: contact entry response B differs")

        computed_call = json.loads(json.dumps(call))
        computed_call["input"]["response_b"] = produced
        contact = compare_composed_contact(computed_call, content)
        output = int(contact["response_and_publication"]["response_b"]["computed"])
        if output != call["output"]["response_b"]:
            raise ValueError(f"frame {frame} rider {rider}: contact response-B output differs")
        recurrent[rider] = output
        if frame == 1662 and rider == 1:
            prior_same_rider = next(row for row in reversed(rows) if row["rider"] == rider)
            transition = {"prior_contact_output": prior_same_rider["contact_output"],
                          "frame": frame, "rider": rider,
                          "producer": producer, "contact_input": produced}
        rows.append({
            "ordinal": ordinal, "frame": frame, "rider": rider,
            "phase_0302": phase, "active": rider == active_rider,
            "recurrent_input": incoming, "producer_inputs": inputs,
            "producer": producer, "pose_consumed": int(pose_reads[0][5]),
            "motion_publication": motion["persistent_publication"],
            "contact_input": produced, "contact_output": output,
        })
    if transition != {"prior_contact_output": 254, "frame": 1662, "rider": 1,
                       "producer": {"branch": "word_clear_zero_pair", "width": 2, "value": 0},
                       "contact_input": 0}:
        raise ValueError(f"observed opponent 254-to-0 transition differs: {transition}")
    validate_recurrence_chain(rows, {0: seed["player_response_b"],
                                     1: seed["opponent_response_b"]})
    metadata = {
        "source": {"scenario_id": scenario, "replay_manifest": replay,
                   "replay_manifest_sha256": replay_sha, "access_sha256": access_sha,
                   "wram_series_sha256": series_sha, "rom_sha256": ROM_SHA256},
        "frames": {"seed": 1649, "first": 1650, "last": 1700},
        "calls": len(rows), "seed": seed, "rows_sha256": _digest(rows),
        "writer_counts": dict(sorted(writer_counts.items())),
        "active_counts": active_counts, "transition_254_to_0": transition,
        "final_response_b": {"player": recurrent[0], "opponent": recurrent[1]},
        "pose_comparisons": len(rows),
        "composition": {
            "calls": len(composition), "points": composition_meta["sample_words"],
            "sample_words_sha256": composition_meta["sample_words_sha256"],
            "sample_sources_sha256": composition_meta["sample_sources_sha256"],
            "final": composition_meta["final"],
        },
        "external_producer_inputs": [
            "f1b", "f1d", "surface_angle", "unsupported_count", "guard_f49",
            "guard_f89", "mode_f23", "special_f5d", "indexed_control",
        ],
        "rows": rows,
    }
    return rows, metadata


def derive(access_path: Path, content_dir: Path, report_path: Path) -> dict:
    _rows, metadata = response_composition(access_path, content_dir)
    report = {"schema_version": 1, "kind": "zoom_zoo_response_b_composition",
              "status": "passed", **metadata,
              "domain": "bounded ten-word response-B/position composition with velocity, pose and other contact fields external; no native ZOOM ZOO gameplay"}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def validate_component_manifest(manifest: dict) -> None:
    if set(manifest) != MANIFEST_FIELDS or manifest.get("schema_version") != 1 or manifest.get("kind") != "zoom_zoo_response_b_reference":
        raise ValueError("response-B manifest schema differs")
    if manifest["producer_routine"] != {"bus": "82:A49F-82:A5F9", "bytes": 347,
                                         "sha256": PRODUCER_ROM_SHA256}:
        raise ValueError("response-B producer identity differs")
    if manifest["description"] != "Ten recurrent words: both riders' response B plus the accepted eight position/residue words over all 102 calls":
        raise ValueError("response-B description differs")
    if manifest["limits"] != "Frames 1650-1700 only; velocity, pose and contact fields other than response B remain captured external inputs; no native ZOOM ZOO support":
        raise ValueError("response-B limits differ")
    scenario = manifest.get("source", {}).get("scenario_id")
    if scenario not in COMPONENT_MANIFEST_SHA256 or _digest(manifest) != COMPONENT_MANIFEST_SHA256[scenario]:
        raise ValueError("response-B authored manifest identity differs")


def verify(access_path: Path, content_dir: Path, manifest_path: Path,
           report_path: Path) -> dict:
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    validate_component_manifest(manifest)
    _rows, metadata = response_composition(access_path, content_dir)
    compared = {name: metadata[name] for name in MANIFEST_FIELDS - {
        "schema_version", "kind", "producer_routine", "description", "limits"
    }}
    if compared != {name: manifest[name] for name in compared}:
        raise ValueError("response-B result differs from authored manifest")
    report = derive(access_path, content_dir, report_path)
    report["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def compare_inputs(primary_path: Path, variation_path: Path, content_dir: Path,
                   report_path: Path) -> dict:
    primary_rows, primary = response_composition(primary_path, content_dir)
    variation_rows, variation = response_composition(variation_path, content_dir)
    primary_access = json.loads(primary_path.read_text())
    variation_access = json.loads(variation_path.read_text())
    frames = range(1649, 1701)
    primary_series = _series_rows(primary_path, primary_access, frames)
    variation_series = _series_rows(variation_path, variation_access, frames)
    controller = [frame for frame in frames
                  if primary_series[frame][0x0313] != variation_series[frame][0x0313]]
    if controller != [1668]:
        raise ValueError("worker response-B controller divergence differs")
    differences = [(left["frame"], left["rider"]) for left, right
                   in zip(primary_rows, variation_rows, strict=True) if left != right]
    response_differences = [(left["frame"], left["rider"]) for left, right
                            in zip(primary_rows, variation_rows, strict=True)
                            if (left["contact_input"], left["contact_output"])
                            != (right["contact_input"], right["contact_output"])]
    primary_composition, _ = composition_rows(primary_path, content_dir)
    variation_composition, _ = composition_rows(variation_path, content_dir)
    composition_differences = [(left["frame"], left["rider"]) for left, right
                               in zip(primary_composition, variation_composition, strict=True)
                               if left != right]
    sample_differences = [(left["frame"], left["rider"]) for left, right
                          in zip(primary_composition, variation_composition, strict=True)
                          if [sample["word"] for sample in left["samples"]]
                          != [sample["word"] for sample in right["samples"]]]
    if not composition_differences or composition_differences[0] != (1668, 0):
        raise ValueError("worker full-composition divergence differs")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_response_b_input_comparison",
        "status": "passed", "prediction": {"exact_through": 1667,
            "controller_divergence_frames": [1668], "relevance_preclaimed": False},
        "first_component_difference": None if not differences else {
            "frame": differences[0][0], "rider": differences[0][1]},
        "response_b_differences": response_differences,
        "first_full_composition_difference": {"frame": 1668, "rider": 0},
        "first_sample_difference": None if not sample_differences else {
            "frame": sample_differences[0][0], "rider": sample_differences[0][1]},
        "opponent_full_composition_exact": not any(rider == 1 for _frame, rider in composition_differences),
        "player_full_composition_reconverged_by_1700": (1700, 0) not in composition_differences,
        "primary_rows_sha256": primary["rows_sha256"],
        "variation_rows_sha256": variation["rows_sha256"],
    }
    report["comparison_sha256"] = _digest(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def capture_command(manifest: Path, out: Path) -> list[str]:
    resolved = manifest.resolve()
    if resolved == (ROOT / PRIMARY).resolve():
        expected = PRIMARY_SHA256
    elif resolved == (ROOT / VARIATION).resolve():
        expected = VARIATION_SHA256
    else:
        raise ValueError("response-B capture accepts only preregistered scenarios")
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
        raise ValueError("response-B replay manifest identity differs")
    command = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(FIRST_CAPTURE_FRAME),
        "--to-frame", str(LAST_CAPTURE_FRAME),
        "--wram-series-range", "0", "0x2200", "--timeout", "180",
        "--report", str(out / "report.json"),
    ]
    for address in WATCH_ADDRESSES:
        command += ["--watch-address", hex(address)]
    for pc in WATCH_PCS:
        command += ["--watch-pc", hex(pc)]
    return command


def capture(manifest: Path, out: Path) -> int:
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty capture directory")
    out.mkdir(parents=True, exist_ok=True)
    command = capture_command(manifest, out)
    (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    return subprocess.run(command, timeout=200).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--manifest", type=Path, required=True)
    cap.add_argument("--out", type=Path, required=True)
    derive_parser = sub.add_parser("derive")
    derive_parser.add_argument("--access", type=Path, required=True)
    derive_parser.add_argument("--content", type=Path, required=True)
    derive_parser.add_argument("--report", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--access", type=Path, required=True)
    verify_parser.add_argument("--content", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, required=True)
    verify_parser.add_argument("--report", type=Path, required=True)
    compare_parser = sub.add_parser("compare-inputs")
    compare_parser.add_argument("--primary-access", type=Path, required=True)
    compare_parser.add_argument("--variation-access", type=Path, required=True)
    compare_parser.add_argument("--content", type=Path, required=True)
    compare_parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "capture":
        return capture(args.manifest, args.out)
    if args.command == "derive":
        derive(args.access, args.content, args.report)
    elif args.command == "verify":
        verify(args.access, args.content, args.manifest, args.report)
    else:
        compare_inputs(args.primary_access, args.variation_access, args.content, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
