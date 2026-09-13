"""Preregistered M4-11 vertical-velocity recurrence experiment.

This additive research surface observes original execution only. It does not
modify or invoke production native gameplay.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .zoom_zoo_response_b import (
    WATCH_ADDRESSES as RESPONSE_WATCH_ADDRESSES,
    WATCH_PCS as RESPONSE_WATCH_PCS,
    _event_block as _response_event_block,
    _phase_for_frame,
    _producer_inputs, evaluate_active_producer,
)
from .zoom_zoo_composition import (
    _digest, compare_composed_contact, composition_rows, load_content,
    reached_y_adjustment,
)
from .zoom_zoo_contact import captured_calls
from .zoom_zoo_position import _series_rows
from .zoom_zoo_vertical_contact import attach_live_dependencies
from .contact_research.summarize import events_for_frame, validate_identity


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1672.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION_SHA256 = "c6dcb0e542feeae04c02c9d425072852c32d31a40bae149ffcb753265b16347a"
FIRST_CAPTURE_FRAME = 1649
LAST_CAPTURE_FRAME = 1700
ROM_SHA256 = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
CAP_ROM_SHA256 = "abfe21846d6e3d2f91bc649e510db6d5616fb5d7ea879192ec1aa5b8e72aac31"
JUMP_ROM_SHA256 = "2a21e360ddac360508870de522d2a779c6e75bfdb21f46645690728302077078"
GRAVITY_ROM_SHA256 = "5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c"
CAPTURE_IDENTITIES = {
    "race-crawler-zoom-zoo-3300": (
        PRIMARY, PRIMARY_SHA256,
        "0bf7d3fbae726c20585a281f628ba42c72d9cff4405ee7c2d3fcd518df68467c",
        "53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d",
    ),
    "race-crawler-zoom-zoo-right-release-1672": (
        VARIATION, VARIATION_SHA256,
        "cc68b84031db523ef9a0ee50ce8956c50f4b69f89e24661746142d2d20b2e731",
        "62b24483d7f83eecfcee35077146b6238a9667a1deccb2734bb9db6aee5b3afd",
    ),
}
COMPONENT_MANIFEST_SHA256 = {
    "race-crawler-zoom-zoo-3300": "5b02a1c37fd40a676ecd474ed9b70acd8c40de3f40be328c55652258cb77021f",
    "race-crawler-zoom-zoo-right-release-1672": "d1ccc58e2ffb4b9b20a891fe9a8fc05d38e880820da73c098772b499b2846aa7",
}
MANIFEST_FIELDS = {
    "schema_version", "kind", "source", "frames", "calls", "seed",
    "rows_sha256", "writer_counts", "jump_branches", "gravity_branches",
    "cap_branches", "final_velocity_y", "composition", "external_inputs",
    "routines", "phase_order", "description", "limits",
}

# Persistent rider fields and broad scratch/input neighborhoods expose every
# actual read/write and any writer outside the preregistered motion ranges.
VELOCITY_WATCH_ADDRESSES = sorted(set(
    list(range(0x04BB, 0x04C7))
    + list(range(0x0BDB, 0x0BE7))
    + list(range(0x0D35, 0x0D3D))
    + list(range(0x0F8F, 0x0FB0))
    + list(range(0x11D1, 0x11E3))
    + list(range(0x11F1, 0x11F7))
    + [0x0300, 0x0302, 0x031D, 0x031F, 0x04C7, 0x0547, 0x0549,
       0x0F1D, 0x0F1F, 0x0F21, 0x0F2B, 0x0F31, 0x0F33, 0x0F41,
       0x0F4B, 0x0F5D, 0x0FF9, 0x1225, 0x1227, 0x127F]
))
WATCH_ADDRESSES = sorted(set(RESPONSE_WATCH_ADDRESSES + VELOCITY_WATCH_ADDRESSES))

# Every byte is deliberately requested. The capture retains only reached
# instruction starts and therefore does not presume decoding or branch reach.
MOTION_PC_RANGE = list(range(0x82A81A, 0x82A9B3))
ORDER_PCS = [
    0x818CF4, 0x818E28, 0x818F7C, 0x818F98,
    0x828A63, 0x828A66, 0x828D9A, 0x828D9D,
    0x828F6B, 0x828F6E, 0x829288, 0x82928B,
    0x82A61F, 0x82A622,
]
WATCH_PCS = sorted(set(RESPONSE_WATCH_PCS + MOTION_PC_RANGE + ORDER_PCS))

MOTION_BOUNDARIES = {
    0: {"load_read": 0x828B9D, "load_write": 0x828BA0,
        "publish_read": 0x828E9D, "publish_write": 0x828EA0,
        "persistent": 0x04BF, "contact_read": 0x818D64,
        "contact_load": 0x818D67, "contact_publish": 0x818E28},
    1: {"load_read": 0x8290A5, "load_write": 0x8290A8,
        "publish_read": 0x82938B, "publish_write": 0x82938E,
        "persistent": 0x04C1, "contact_read": 0x818EBE,
        "contact_load": 0x818EC1, "contact_publish": 0x818F7C},
}
PHASE_ORDER = [
    "persistent_load", "active_jump_or_inactive_preserve", "gravity",
    "vertical_cap", "position_integration", "motion_publication", "contact",
    "contact_publication",
]


def _u16(value: int) -> int:
    return value & 0xFFFF


def _s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def evaluate_vertical_cap(velocity: int, extra: int, cartridge_mode: int,
                          vertical_boost: int) -> dict:
    """Execute `$82:A81A--A872` with wrapped subtraction-sign predicates."""
    if cartridge_mode in (2, 42):
        raise ValueError("alternate vertical-cap cartridge mode is unrecovered here")
    cap = _u16((extra >> 1) + 0x0300)
    output = _u16(velocity)
    branch = "ordinary_preserve"
    if output & 0x8000:
        negative_cap = _u16(-cap)
        if not _u16(negative_cap - output) & 0x8000:
            output, branch = negative_cap, "ordinary_negative_clamp"
    elif _u16(cap - output) & 0x8000:
        output, branch = cap, "ordinary_positive_clamp"
    boost_candidate = _u16(vertical_boost - 1)
    boost_output = vertical_boost if boost_candidate & 0x8000 else boost_candidate
    return {"branch": branch, "input": _u16(velocity), "extra": _u16(extra),
            "cartridge_mode": _u16(cartridge_mode), "cap": cap,
            "velocity_y": output, "vertical_boost_input": _u16(vertical_boost),
            "vertical_boost_output": _u16(boost_output),
            "vertical_boost_written": not bool(boost_candidate & 0x8000)}


def evaluate_bounded_jump(velocity: int, inputs: dict[str, int | None]) -> dict:
    """Execute the reached no-latch `$82:A8C9--A96E` family.

    The bounded episode reaches the complete guard chain but no held impulse or
    latch writer. Inputs after a taken short circuit must remain unavailable.
    """
    def required(name: str) -> int:
        value = inputs.get(name)
        if value is None:
            raise ValueError(f"jump evidence omits reached input {name}")
        return int(value)

    for name in ("indexed_inhibit", "guard_f41", "special_f5d"):
        if required(name):
            return {"branch": f"preserve_{name}", "velocity_y": _u16(velocity),
                    "previous_input_publication": None}
    if required("direction_f31") & 0x80:
        return {"branch": "preserve_direction_high", "velocity_y": _u16(velocity),
                "previous_input_publication": None}
    if required("held_phase") or required("jump_latch"):
        raise ValueError("bounded M4-11 episode unexpectedly reaches jump latch/impulse")
    previous = required("previous_input")
    current = required("current_input")
    if not previous and current:
        unsupported = required("unsupported_count")
        if _s16(_u16(unsupported - 2)) < 0:
            raise ValueError("bounded M4-11 episode unexpectedly arms jump latch")
    branch = "previous_input_preserve" if previous else (
        "neutral_no_arm" if not current else "unsupported_no_arm")
    return {"branch": branch, "velocity_y": _u16(velocity),
            "previous_input_publication": _u16(current)}


def validate_recurrence_chain(rows: list[dict], seed: dict[int, int]) -> None:
    expected_fields = {
        "ordinal", "frame", "rider", "phase_0302", "active",
        "recurrent_input", "jump_inputs", "post_jump", "gravity", "cap",
        "integrator_input", "motion_publication", "contact_input",
        "contact_output", "response_b", "composition", "writer_evidence",
    }
    recurrent = {0: _u16(seed[0]), 1: _u16(seed[1])}
    for ordinal, row in enumerate(rows):
        if set(row) != expected_fields:
            raise ValueError("vertical-velocity row schema differs or captured substitution was added")
        if (row["ordinal"], row["frame"], row["rider"]) != (
                ordinal, 1650 + ordinal // 2, ordinal & 1):
            raise ValueError("vertical-velocity call order or rider differs")
        rider = row["rider"]
        if row["recurrent_input"] != recurrent[rider]:
            raise ValueError("vertical-velocity chain was reseeded or replaced")
        if row["active"] is not (rider == 1 - row["phase_0302"]):
            raise ValueError("vertical-velocity phase differs")
        if row["post_jump"]["velocity_y"] != recurrent[rider]:
            raise ValueError("unobserved jump changed vertical velocity")
        if row["integrator_input"] != row["cap"]["velocity_y"]:
            raise ValueError("vertical-velocity cap/integrator order differs")
        if (row["motion_publication"], row["contact_input"]) != (
                row["integrator_input"], row["integrator_input"]):
            raise ValueError("vertical-velocity motion/contact publication differs")
        recurrent[rider] = _u16(row["contact_output"])


def _one(events: list[tuple], pc: int, kind: str, address: int | None = None,
         required: bool = True) -> tuple | None:
    rows = [event for event in events if event[1] == pc and event[2] == kind
            and (address is None or event[3] == address)]
    if not rows and not required:
        return None
    if len(rows) != 1 or rows[0][5] is None:
        raise ValueError(f"expected one complete ${pc:06X} {kind} event")
    return rows[0]


def _overlaps(event: tuple, address: int) -> bool:
    return event[2] in ("write", "rmw") and event[3] <= address < event[3] + event[4]


def validate_pose_consumption(block: list[tuple], produced: int,
                              frame: int = 0, rider: int = 0) -> int:
    """Bind the width-two `$83:F00D` pose read to computed response B."""
    reads = [event for event in block if event[1] == 0x83F00D
             and event[2] == "read" and event[3] == 0x0F57]
    if (len(reads) != 1 or reads[0][4] != 2 or reads[0][5] is None
            or int(reads[0][5]) != _u16(produced)):
        raise ValueError(
            f"frame {frame} rider {rider}: pose did not consume width-two computed response B"
        )
    return int(reads[0][5])


def validate_domain_writer_inventory(events: list[tuple],
                                     classified: list[tuple], frame: int = 0) -> None:
    """Require every reached `$0FAB` writer in a frame to be classified once."""
    observed = [event for event in events if _overlaps(event, 0x0FAB)]
    expected = sorted(classified, key=lambda event: event[0])
    if observed != expected or len({event[0] for event in expected}) != len(expected):
        raise ValueError(f"frame {frame}: complete $0FAB writer inventory differs")


def validate_velocity_event_sequence(*, frame: int, rider: int,
                                     boundaries: dict[str, tuple],
                                     jump_events: list[tuple],
                                     jump_state: tuple | None,
                                     gravity_input: tuple,
                                     gravity_write: tuple,
                                     cap_input: tuple,
                                     cap_writes: list[tuple],
                                     boost_input: tuple,
                                     boost_writes: list[tuple],
                                     integrator: tuple,
                                     motion_writers: list[tuple],
                                     contact_response: tuple | None,
                                     contact_writers: list[tuple]) -> None:
    """Validate semantic widths, writer inventory and original event order.

    This deliberately accepts decoded event tuples rather than an access
    document so mutation tests can challenge semantics independently of the
    outer capture SHA-256 binding.
    """
    required_boundaries = {
        "persistent_load", "scratch_load", "scratch_publication",
        "persistent_publication", "contact_persistent_load",
        "contact_scratch_load", "contact_publication",
    }
    if set(boundaries) != required_boundaries:
        raise ValueError("vertical-velocity boundary inventory differs")
    for name, event in boundaries.items():
        if event[4] != 2 or event[5] is None:
            raise ValueError(
                f"frame {frame} rider {rider}: {name} is not a complete width-two event"
            )
    for name, event in (("gravity input", gravity_input),
                        ("gravity writer", gravity_write),
                        ("cap input", cap_input), ("boost input", boost_input),
                        ("integrator", integrator)):
        if event[4] != 2 or event[5] is None:
            raise ValueError(f"frame {frame} rider {rider}: {name} width/value differs")
    if ((gravity_input[1:4], gravity_write[1:4], cap_input[1:4],
         boost_input[1:4], integrator[1:4]) != (
            (0x82A97E, "read", 0x0FAB),
            (0x82A9AA, "write", 0x0FAB),
            (0x82A832, "read", 0x0FAB),
            (0x82A86C, "read", 0x11DD),
            (0x82A674, "read", 0x0FAB))):
        raise ValueError(f"frame {frame} rider {rider}: stage instruction identity differs")
    for name, rows in (("cap", cap_writes), ("boost", boost_writes)):
        if len(rows) > 1 or any(event[4] != 2 or event[5] is None for event in rows):
            raise ValueError(f"frame {frame} rider {rider}: {name} writer inventory differs")
    if boost_writes and boost_writes[0][1:4] != (0x82A872, "write", 0x11DD):
        raise ValueError(f"frame {frame} rider {rider}: boost writer identity differs")
    if jump_events:
        if (jump_state is None or jump_state not in jump_events
                or jump_state[1:5] != (0x82A96B, "write", 0x0FA5, 2)
                or jump_state[5] is None):
            raise ValueError(f"frame {frame} rider {rider}: active jump state writer differs")
        if max(event[0] for event in jump_events) != jump_state[0]:
            raise ValueError(f"frame {frame} rider {rider}: jump state was not published last")
    elif jump_state is not None:
        raise ValueError(f"frame {frame} rider {rider}: inactive jump state writer differs")

    ordered = [boundaries["persistent_load"], boundaries["scratch_load"]]
    ordered += sorted(jump_events, key=lambda event: event[0])
    ordered += [gravity_input, gravity_write, cap_input]
    ordered += cap_writes + [boost_input] + boost_writes
    ordered += [integrator, boundaries["scratch_publication"],
                boundaries["persistent_publication"],
                boundaries["contact_persistent_load"],
                boundaries["contact_scratch_load"]]
    if contact_response is not None:
        if contact_response[1:4] != (0x81970B, "write", 0x0FAB):
            raise ValueError(f"frame {frame} rider {rider}: contact writer identity differs")
        ordered.append(contact_response)
    ordered.append(boundaries["contact_publication"])
    if any(left[0] >= right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError(f"frame {frame} rider {rider}: vertical-velocity stage order differs")

    expected_motion = [boundaries["scratch_load"], gravity_write, *cap_writes]
    expected_contact = [boundaries["contact_scratch_load"]]
    if contact_response is not None:
        expected_contact.append(contact_response)
    for name, observed, expected in (
            ("motion", motion_writers, expected_motion),
            ("contact", contact_writers, expected_contact)):
        if observed != expected or any(
                not _overlaps(event, 0x0FAB) or event[4] != 2 or event[5] is None
                for event in observed):
            raise ValueError(
                f"frame {frame} rider {rider}: {name} $0FAB writer inventory differs"
            )


def _motion_block(access: dict, frame: int, rider: int) -> tuple[list[tuple], dict]:
    events = events_for_frame(access, frame)
    boundary = MOTION_BOUNDARIES[rider]
    start = _one(events, boundary["load_read"], "read", boundary["persistent"])
    load = _one(events, boundary["load_write"], "write", 0x0FAB)
    publication = _one(events, boundary["publish_read"], "read", 0x0FAB)
    end = _one(events, boundary["publish_write"], "write", boundary["persistent"])
    contact_read = _one(events, boundary["contact_read"], "read", boundary["persistent"])
    contact_load = _one(events, boundary["contact_load"], "write", 0x0FAB)
    contact_publish = _one(events, boundary["contact_publish"], "write", boundary["persistent"])
    named_events = {
        "persistent_load": start, "scratch_load": load,
        "scratch_publication": publication, "persistent_publication": end,
        "contact_persistent_load": contact_read,
        "contact_scratch_load": contact_load,
        "contact_publication": contact_publish,
    }
    for name, event in named_events.items():
        if event[4] != 2:
            raise ValueError(
                f"frame {frame} rider {rider}: {name} is not width two"
            )
    if not (start[0] < load[0] < publication[0] < end[0] < contact_read[0]
            < contact_load[0] < contact_publish[0]):
        raise ValueError(f"frame {frame} rider {rider}: velocity phase order differs")
    return [event for event in events if load[0] < event[0] < publication[0]], {
        "persistent_input": int(start[5]), "scratch_load": int(load[5]),
        "motion_publication": int(publication[5]), "persistent_publication": int(end[5]),
        "contact_read": int(contact_read[5]), "contact_load": int(contact_load[5]),
        "contact_publication": int(contact_publish[5]),
        "events": named_events,
        "motion_writers": [event for event in events
                           if load[0] <= event[0] <= end[0]
                           and _overlaps(event, 0x0FAB)],
        "contact_writers": [event for event in events
                            if contact_load[0] <= event[0] <= contact_publish[0]
                            and _overlaps(event, 0x0FAB)],
    }


def _accumulator(access: dict, pc: int, frame: int, rider: int) -> int:
    rows = [row for row in access["watch_pcs"].get(str(pc), [])
            if row[0] == frame and row[3] == rider * 2]
    if len(rows) != 1:
        raise ValueError(f"frame {frame} rider {rider}: incomplete ${pc:06X} register evidence")
    return int(rows[0][1])


def _jump_inputs(access: dict, frame: int, rider: int,
                 block: list[tuple]) -> dict[str, int | None]:
    def optional(pc: int, address: int | None = None) -> int | None:
        row = _one(block, pc, "read", address, required=False)
        return None if row is None else int(row[5])
    return {
        "indexed_inhibit": _accumulator(access, 0x82A8D3, frame, rider),
        "guard_f41": optional(0x82A8D8, 0x0F41),
        "special_f5d": optional(0x82A8E0, 0x0F5D), "direction_f31": optional(0x82A8E8, 0x0F31),
        "held_phase": optional(0x82A8F0, 0x0F93), "jump_latch": optional(0x82A8F5, 0x0F91),
        "previous_input": optional(0x82A8FA, 0x0FA5),
        "current_input": optional(0x82A8FF, 0x0F1F) if optional(0x82A8FF, 0x0F1F) is not None else optional(0x82A968, 0x0F1F),
        "unsupported_count": optional(0x82A909, 0x0F33),
    }


def _computed_response_rows(access_path: Path, access: dict, calls: list[dict],
                            content: dict[str, bytes]) -> tuple[list[dict], dict]:
    """Run the accepted M4-10 equations under this M4-11 capture identity."""
    series = _series_rows(access_path, access, range(1649, 1701))
    word = lambda address: series[1649][address] | series[1649][address + 1] << 8
    recurrent = {0: word(0x0BB7), 1: word(0x0BB9)}
    rows = []
    for ordinal, call in enumerate(calls):
        frame, rider = call["frame"], call["rider"]
        block, motion = _response_event_block(access, frame, rider)
        incoming = recurrent[rider]
        if (motion["persistent_input"], motion["scratch_load"]) != (incoming, incoming):
            raise ValueError("M4-10 response-B recurrence was replaced")
        phase = _phase_for_frame(access, frame)
        active = rider == 1 - phase
        inputs = None
        if active:
            control_address = 0x031D + rider * 2
            control_reads = [event for event in block if event[1] in (0x82A50A, 0x82A565)
                             and event[2] == "read"]
            if control_reads:
                if len(control_reads) != 1 or control_reads[0][3] != control_address:
                    raise ValueError("response-B indexed control address differs")
                before = [event for event in events_for_frame(access, frame)
                          if event[0] < control_reads[0][0] and event[2] in ("write", "rmw")
                          and event[3] <= control_address < event[3] + event[4]]
                if before:
                    last = before[-1]
                    if last[5] is None:
                        raise ValueError("response-B control writer is unresolved")
                    control = (int(last[5]) >> (8 * (control_address - last[3]))) & 0xFF
                else:
                    control = series[frame - 1][control_address]
            else:
                control = series[frame - 1][control_address]
            inputs = _producer_inputs(block, control)
            producer = evaluate_active_producer(incoming, inputs)
        else:
            producer = {"branch": "inactive_preserve", "width": None, "value": incoming}
        produced = int(producer["value"])
        if (motion["scratch_publication"], motion["persistent_publication"],
                call["input"]["response_b"]) != (produced,) * 3:
            raise ValueError("computed M4-10 response B was not consumed in order")
        pose_consumed = validate_pose_consumption(block, produced, frame, rider)
        computed_call = copy.deepcopy(call)
        computed_call["input"]["response_b"] = produced
        contact = compare_composed_contact(computed_call, content)
        output = int(contact["response_and_publication"]["response_b"]["computed"])
        recurrent[rider] = output
        rows.append({"ordinal": ordinal, "frame": frame, "rider": rider,
                     "phase_0302": phase, "active": active, "recurrent_input": incoming,
                     "producer_inputs": inputs, "producer": producer,
                     "pose_consumed": pose_consumed,
                     "contact_input": produced, "contact_output": output})
    return rows, {"rows_sha256": _digest(rows),
                  "final_response_b": {"player": recurrent[0], "opponent": recurrent[1]}}


def velocity_composition(access_path: Path, content_dir: Path) -> tuple[list[dict], dict]:
    raw = access_path.read_bytes()
    access = json.loads(raw)
    validate_identity(access)
    if access.get("frames") != {"start": 1649, "end": 1700, "count": 52}:
        raise ValueError("vertical-velocity capture frame domain differs")
    if access.get("status") != "complete" or access.get("watch_pcs_truncated"):
        raise ValueError("complete nontruncated vertical-velocity capture is required")
    if access.get("residual", {}).get("unresolved_stores") != 0 or access.get("residual", {}).get("non_rom_pcs"):
        raise ValueError("vertical-velocity capture has unresolved stores or non-ROM PCs")
    scenario = access.get("scenario_id")
    if scenario not in CAPTURE_IDENTITIES:
        raise ValueError("vertical-velocity scenario differs")
    replay, replay_sha, access_sha, series_sha = CAPTURE_IDENTITIES[scenario]
    if access["manifest"] != {"path": replay, "sha256": replay_sha}:
        raise ValueError("vertical-velocity replay binding differs")
    if hashlib.sha256(raw).hexdigest() != access_sha or access["wram_series"]["sha256"] != series_sha:
        raise ValueError("vertical-velocity capture identity differs")

    accepted_rows, accepted_meta = composition_rows(access_path, content_dir)
    calls = captured_calls(access)
    attach_live_dependencies(access, calls)
    calls = [call for call in calls if call["frame"] >= 1650]
    if len(calls) != 102:
        raise ValueError("vertical-velocity call count differs")
    series = _series_rows(access_path, access, [1649])
    seed = {0: int.from_bytes(series[1649][0x04BF:0x04C1], "little"),
            1: int.from_bytes(series[1649][0x04C1:0x04C3], "little")}
    recurrent = dict(seed)
    content = load_content(content_dir)
    response_rows, response_meta = _computed_response_rows(access_path, access, calls, content)
    rows = []
    writer_counts: Counter[str] = Counter()
    classified_writers: dict[int, list[tuple]] = {}
    for ordinal, (call, accepted, response) in enumerate(zip(calls, accepted_rows, response_rows, strict=True)):
        frame, rider = call["frame"], call["rider"]
        block, motion = _motion_block(access, frame, rider)
        incoming = recurrent[rider]
        if (motion["persistent_input"], motion["scratch_load"]) != (incoming, incoming):
            raise ValueError(f"frame {frame} rider {rider}: recurrent velocity was replaced")
        phase = _phase_for_frame(access, frame)
        active = rider == 1 - phase
        if active:
            inputs = _jump_inputs(access, frame, rider, block)
            jump = evaluate_bounded_jump(incoming, inputs)
            publication = jump["previous_input_publication"]
            fa5 = [event for event in block if event[1] == 0x82A96B and event[2] == "write" and event[3] == 0x0FA5]
            if publication is None:
                if fa5:
                    raise ValueError("short-circuited jump unexpectedly published previous input")
            elif len(fa5) != 1 or fa5[0][4:] != (2, publication):
                raise ValueError("jump previous-input writer differs")
            jump_velocity_writes = [event for event in block if 0x82A8C9 <= event[1] <= 0x82A96E and event[2] == "write" and event[3] == 0x0FAB]
            if jump_velocity_writes:
                raise ValueError("bounded M4-11 jump unexpectedly writes vertical velocity")
        else:
            if any(0x82A8C9 <= event[1] <= 0x82A96E for event in block):
                raise ValueError("inactive rider unexpectedly entered jump routine")
            inputs = None
            jump = {"branch": "inactive_preserve", "velocity_y": incoming,
                    "previous_input_publication": None}

        gravity_guard_event = _one(block, 0x82A971, "read", 0x0F4B)
        first_guard = int(gravity_guard_event[5])
        selector = int(_one(block, 0x82A976, "read", 0x0FF9)[5])
        indexed_guard = int(_one(block, 0x82A979, "read", 0x0547 + rider * 2)[5])
        gravity_input_event = _one(block, 0x82A97E, "read", 0x0FAB)
        gravity_input = int(gravity_input_event[5])
        if selector != rider * 2 or gravity_input != jump["velocity_y"]:
            raise ValueError("jump/gravity rider or publication order differs")
        gravity = reached_y_adjustment(0, gravity_input, first_guard, indexed_guard)
        gravity_write_event = _one(block, 0x82A9AA, "write", 0x0FAB)
        if gravity["velocity_y"] != gravity_write_event[5] or gravity_write_event[4] != 2:
            raise ValueError("gravity writer/arithmetic differs")

        mode = _accumulator(access, 0x82A821, frame, rider)
        extra = int(_one(block, 0x82A82B, "read", 0x0000)[5])
        cap_input_event = _one(block, 0x82A832, "read", 0x0FAB)
        cap_input = int(cap_input_event[5])
        boost_input_event = _one(block, 0x82A86C, "read", 0x11DD)
        boost_input = int(boost_input_event[5])
        if cap_input != gravity["velocity_y"]:
            raise ValueError("gravity/cap order differs")
        cap = evaluate_vertical_cap(cap_input, extra, mode, boost_input)
        cap_writes = [event for event in block if event[2] == "write" and event[3] == 0x0FAB and 0x82A81A <= event[1] <= 0x82A872]
        expected_cap_pc = {
            "ordinary_preserve": None,
            "ordinary_negative_clamp": 0x82A840,
            "ordinary_positive_clamp": 0x82A84A,
        }[cap["branch"]]
        if cap["velocity_y"] == cap_input:
            if cap_writes:
                raise ValueError("vertical cap preserve unexpectedly wrote velocity")
        elif (len(cap_writes) != 1 or cap_writes[0][1] != expected_cap_pc
              or cap_writes[0][4:] != (2, cap["velocity_y"])):
            raise ValueError("vertical cap writer differs")
        boost_writes = [event for event in block if event[1] == 0x82A872 and event[2] == "write" and event[3] == 0x11DD]
        if cap["vertical_boost_written"]:
            if len(boost_writes) != 1 or boost_writes[0][4:] != (2, cap["vertical_boost_output"]):
                raise ValueError("vertical boost writer differs")
        elif boost_writes:
            raise ValueError("underflowed vertical boost unexpectedly wrote")
        integrator_event = _one(block, 0x82A674, "read", 0x0FAB)
        integrator = int(integrator_event[5])
        if integrator != cap["velocity_y"]:
            raise ValueError("cap/integrator publication order differs")
        if (motion["motion_publication"], motion["persistent_publication"],
                motion["contact_read"], motion["contact_load"]) != (integrator,) * 4:
            raise ValueError("motion/contact velocity publication differs")

        if accepted["external"]["before_y_adjustment"]["incoming_velocity_y"] != jump["velocity_y"]:
            raise ValueError("computed jump was not injected into accepted gravity")
        if accepted["y_adjustment"]["velocity_y"] != gravity["velocity_y"]:
            raise ValueError("computed gravity was not injected into accepted composition")
        if _u16(accepted["position"]["y"]["velocity_word"]) != integrator:
            raise ValueError("computed cap was not injected into accepted integrator")
        computed_call = copy.deepcopy(call)
        computed_call["input"]["x"] = accepted["position"]["x"]["position"]
        computed_call["input"]["y"] = accepted["position"]["slope_tail"]["position"]
        computed_call["input"]["vy"] = integrator
        computed_call["input"]["response_b"] = response["contact_input"]
        computed_call["raw_samples"] = [sample["word"] for sample in accepted["samples"]]
        contact = compare_composed_contact(computed_call, content)
        contact_output = int(contact["response_and_publication"]["vy"]["computed"])
        if contact_output != motion["contact_publication"]:
            raise ValueError("computed contact vertical-velocity publication differs")
        contact_response_rows = [event for event in motion["contact_writers"]
                                 if event[1] == 0x81970B]
        expects_contact_response = contact["branch"] in (
            "continuous", "continuous_reflected")
        if expects_contact_response:
            if (len(contact_response_rows) != 1
                    or contact_response_rows[0][4:] != (2, contact_output)):
                raise ValueError("accepted contact vertical-velocity writer differs")
            contact_response = contact_response_rows[0]
        else:
            if contact_response_rows:
                raise ValueError("preserving contact branch unexpectedly wrote velocity")
            contact_response = None
        jump_events = [event for event in block
                       if 0x82A8C9 <= event[1] <= 0x82A96E]
        jump_state_rows = [event for event in jump_events
                           if event[1] == 0x82A96B and event[2] == "write"
                           and event[3] == 0x0FA5]
        jump_state = jump_state_rows[0] if len(jump_state_rows) == 1 else None
        validate_velocity_event_sequence(
            frame=frame, rider=rider, boundaries=motion["events"],
            jump_events=jump_events, jump_state=jump_state,
            gravity_input=gravity_input_event,
            gravity_write=gravity_write_event, cap_input=cap_input_event,
            cap_writes=cap_writes, boost_input=boost_input_event,
            boost_writes=boost_writes, integrator=integrator_event,
            motion_writers=motion["motion_writers"],
            contact_response=contact_response,
            contact_writers=motion["contact_writers"],
        )
        classified_writers.setdefault(frame, []).extend(
            motion["motion_writers"] + motion["contact_writers"])
        if rider == 1:
            validate_domain_writer_inventory(
                events_for_frame(access, frame), classified_writers[frame], frame)
        recurrent[rider] = contact_output
        for name, written in (("motion_load", True),
                              ("jump_state", active and jump["previous_input_publication"] is not None),
                              ("jump_velocity", False), ("gravity_velocity", True),
                              ("vertical_cap_velocity", bool(cap_writes)),
                              ("vertical_boost", cap["vertical_boost_written"]),
                              ("motion_publication", True), ("contact_load", True),
                              ("contact_response_velocity", contact_response is not None),
                              ("contact_velocity_publication", True)):
            writer_counts[name] += int(written)
        rows.append({
            "ordinal": ordinal, "frame": frame, "rider": rider,
            "phase_0302": phase, "active": active, "recurrent_input": incoming,
            "jump_inputs": inputs, "post_jump": jump, "gravity": gravity,
            "cap": cap, "integrator_input": integrator,
            "motion_publication": motion["persistent_publication"],
            "contact_input": integrator, "contact_output": contact_output,
            "response_b": response["contact_input"],
            "writer_evidence": {
                "motion": [{"sequence": event[0], "pc": event[1],
                            "width": event[4], "value": event[5]}
                           for event in motion["motion_writers"]],
                "contact": [{"sequence": event[0], "pc": event[1],
                             "width": event[4], "value": event[5]}
                            for event in motion["contact_writers"]],
            },
            "composition": {"x": computed_call["input"]["x"], "y": computed_call["input"]["y"],
                            "samples": [sample["word"] for sample in accepted["samples"]],
                            "contact_branch": contact["branch"]},
        })
    validate_recurrence_chain(rows, seed)
    metadata = {
        "source": {"scenario_id": scenario, "replay_manifest": replay,
                   "replay_manifest_sha256": replay_sha, "access_sha256": access_sha,
                   "wram_series_sha256": series_sha, "rom_sha256": ROM_SHA256},
        "frames": {"seed": 1649, "first": 1650, "last": 1700}, "calls": len(rows),
        "seed": {"frame": 1649, "player_velocity_y": seed[0], "opponent_velocity_y": seed[1],
                 "wram_series_sha256": series_sha}, "rows_sha256": _digest(rows),
        "writer_counts": dict(sorted(writer_counts.items())),
        "jump_branches": dict(sorted(Counter(row["post_jump"]["branch"] for row in rows).items())),
        "gravity_branches": dict(sorted(Counter(
            "increment_negative" if row["gravity"]["shifted_nonnegative_velocity"] is None
            else "increment_nonnegative" for row in rows
        ).items())),
        "cap_branches": dict(sorted(Counter(row["cap"]["branch"] for row in rows).items())),
        "final_velocity_y": {"player": recurrent[0], "opponent": recurrent[1]},
        "composition": {"calls": len(rows), "points": accepted_meta["sample_words"],
            "sample_words_sha256": accepted_meta["sample_words_sha256"],
            "sample_sources_sha256": accepted_meta["sample_sources_sha256"],
            "final_position": accepted_meta["final"],
            "response_b_rows_sha256": response_meta["rows_sha256"],
            "final_response_b": response_meta["final_response_b"]},
        "external_inputs": ["horizontal_velocity", "pose", "reflection", "jump_and_control_state",
                            "vertical_cap_extra_and_boost", "non_velocity_contact_state"],
        "phase_order": PHASE_ORDER, "rows": rows,
    }
    return rows, metadata


def derive(access_path: Path, content_dir: Path, report_path: Path) -> dict:
    _rows, metadata = velocity_composition(access_path, content_dir)
    report = {"schema_version": 1, "kind": "zoom_zoo_vertical_velocity_composition",
              "status": "passed", **metadata,
              "domain": "bounded twelve-word velocity/response-B/position recurrence; horizontal velocity, pose and other state external; no native ZOOM ZOO gameplay"}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def validate_component_manifest(manifest: dict) -> None:
    if set(manifest) != MANIFEST_FIELDS or manifest.get("schema_version") != 1 or manifest.get("kind") != "zoom_zoo_vertical_velocity_reference":
        raise ValueError("vertical-velocity manifest schema differs")
    scenario = manifest.get("source", {}).get("scenario_id")
    if scenario not in COMPONENT_MANIFEST_SHA256:
        raise ValueError("vertical-velocity authored scenario differs")
    if manifest["routines"] != {
        "vertical_cap": {"bus": "82:A81A-82:A872", "bytes": 89, "sha256": CAP_ROM_SHA256},
        "jump": {"bus": "82:A8C9-82:A96E", "bytes": 166, "sha256": JUMP_ROM_SHA256},
        "gravity": {"bus": "82:A96F-82:A9B2", "bytes": 68, "sha256": GRAVITY_ROM_SHA256},
    }:
        raise ValueError("vertical-velocity routine identity differs")
    if manifest["phase_order"] != PHASE_ORDER:
        raise ValueError("vertical-velocity phase order differs")
    if manifest["description"] != "Twelve recurrent words: both riders' vertical velocity and response B plus the accepted eight position/residue words over all 102 calls":
        raise ValueError("vertical-velocity description differs")
    if manifest["limits"] != "Frames 1650-1700 only; horizontal velocity, pose/reflection, jump/control and remaining contact state stay captured external inputs; no native ZOOM ZOO support":
        raise ValueError("vertical-velocity limits differ")
    if _digest(manifest) != COMPONENT_MANIFEST_SHA256[scenario]:
        raise ValueError("vertical-velocity authored manifest identity differs")


def verify(access_path: Path, content_dir: Path, manifest_path: Path,
           report_path: Path) -> dict:
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(manifest_raw)
    validate_component_manifest(manifest)
    _rows, metadata = velocity_composition(access_path, content_dir)
    compared = {name: metadata[name] for name in MANIFEST_FIELDS - {
        "schema_version", "kind", "routines", "description", "limits"
    }}
    if compared != {name: manifest[name] for name in compared}:
        raise ValueError("vertical-velocity result differs from authored manifest")
    report = derive(access_path, content_dir, report_path)
    report["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def compare_inputs(primary_path: Path, variation_path: Path, content_dir: Path,
                   report_path: Path) -> dict:
    primary_rows, primary = velocity_composition(primary_path, content_dir)
    variation_rows, variation = velocity_composition(variation_path, content_dir)
    primary_access = json.loads(primary_path.read_text())
    variation_access = json.loads(variation_path.read_text())
    frames = range(1649, 1701)
    primary_series = _series_rows(primary_path, primary_access, frames)
    variation_series = _series_rows(variation_path, variation_access, frames)
    controller = [frame for frame in frames
                  if primary_series[frame][0x0313] != variation_series[frame][0x0313]]
    if controller != [1672]:
        raise ValueError("worker vertical-velocity controller divergence differs")
    velocity_differences = [(left["frame"], left["rider"]) for left, right
                            in zip(primary_rows, variation_rows, strict=True)
                            if (left["post_jump"], left["gravity"], left["cap"],
                                left["contact_input"], left["contact_output"])
                            != (right["post_jump"], right["gravity"], right["cap"],
                                right["contact_input"], right["contact_output"])]
    primary_composition, _ = composition_rows(primary_path, content_dir)
    variation_composition, _ = composition_rows(variation_path, content_dir)
    composition_differences = [(left["frame"], left["rider"]) for left, right
                               in zip(primary_composition, variation_composition, strict=True)
                               if left != right]
    sample_differences = [(left["frame"], left["rider"]) for left, right
                          in zip(primary_composition, variation_composition, strict=True)
                          if [sample["word"] for sample in left["samples"]]
                          != [sample["word"] for sample in right["samples"]]]
    if not composition_differences or composition_differences[0] != (1672, 0):
        raise ValueError("worker full-composition divergence differs")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_vertical_velocity_input_comparison",
        "status": "passed", "prediction": {"exact_through": 1671,
            "controller_divergence_frames": [1672], "relevance_preclaimed": False},
        "vertical_velocity_differences": velocity_differences,
        "first_full_composition_difference": {"frame": 1672, "rider": 0},
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
        raise ValueError("vertical-velocity capture accepts only preregistered scenarios")
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
        raise ValueError("vertical-velocity replay manifest identity differs")
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
        return 0
    if args.command == "verify":
        verify(args.access, args.content, args.manifest, args.report)
        return 0
    if args.command == "compare-inputs":
        compare_inputs(args.primary_access, args.variation_access, args.content, args.report)
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
