"""Capture the preregistered M4-09 position/contact composition experiment.

This additive research surface observes the position integrator, the reached
pre-integration Y adjustment, sampling, and contact in one ordered window.  It
does not modify or invoke production native gameplay.
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

from .zoom_zoo_contact import WATCH_ADDRESSES as CONTACT_WATCH_ADDRESSES
from .zoom_zoo_contact import WATCH_PCS as CONTACT_WATCH_PCS
from .zoom_zoo_contact import captured_calls, compare_preprocessing, tile_index
from .contact_research.preprocess import expand_points
from .contact_research.summarize import events_for_frame, validate_identity
from .zoom_zoo_reflected_vertical_contact import load_content, resolve_reflected_response
from .zoom_zoo_vertical_contact import (
    _last_write, attach_live_dependencies, reduce_vertical, resolve_response,
)
from .zoom_zoo_position import WATCH_ADDRESSES as POSITION_WATCH_ADDRESSES
from .zoom_zoo_position import WATCH_PCS as POSITION_WATCH_PCS
from .zoom_zoo_position import (
    _captured_axis, _event_value, _maybe_reg, _reg, _seed_from_series, _series_rows,
    slope_tail, validate_call_order,
)


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1666.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION_SHA256 = "3f51643950d2050209e8795e468d801c7ea20f660d4d338175d7bba2a32f9abc"
FIRST_CAPTURE_FRAME = 1649
FIRST_CALL_FRAME = 1650
LAST_CALL_FRAME = 1700
COARSE_WIDTH = 256
Y_ROUTINE_SHA256 = "5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c"
COMPONENT_MANIFEST_SHA256 = {
    "race-crawler-zoom-zoo-3300": "80caeee43c187971adab62e5d3b3b8fc2926b2dd7c3749f40bc7597f63b40785",
    "race-crawler-zoom-zoo-right-release-1666": "d6fb2e130bd208741c2910c110be0afeeb966f8777635057418eaf367616ba66",
}

# $82:A96F--A9B2 is decoded at 16-bit accumulator/index width.  Every reached
# instruction is watched, including both early exits and the final $A7 store.
Y_ADJUSTMENT_PCS = [
    0x82A96F, 0x82A971, 0x82A974, 0x82A976, 0x82A979, 0x82A97C,
    0x82A97E, 0x82A981, 0x82A984, 0x82A986, 0x82A989, 0x82A98B,
    0x82A98E, 0x82A991, 0x82A993, 0x82A994, 0x82A995, 0x82A996,
    0x82A997, 0x82A998, 0x82A99A, 0x82A99D, 0x82A99E, 0x82A9A0,
    0x82A9A1, 0x82A9A2, 0x82A9A3, 0x82A9A6, 0x82A9A7, 0x82A9AA,
    0x82A9AD, 0x82A9AF, 0x82A9B0, 0x82A9B2,
]

# The two indexed predicate words are $0547/$0549 because caller selector
# $0FF9 is preregistered as 0 then 2.  $0F4B, vertical velocity $0FAB, direct
# page scratch $00/$02 and the transient position $A7 close the reached helper.
WATCH_ADDRESSES = sorted(set(
    CONTACT_WATCH_ADDRESSES + POSITION_WATCH_ADDRESSES
    + [0x0000, 0x0002, 0x00A7, 0x0547, 0x0549, 0x0F4B, 0x0FAB, 0x0FF9]
))

# Caller boundaries establish helper -> integrator -> collision-point expansion
# -> track sampling -> contact for player and opponent in their original order.
WATCH_PCS = sorted(set(
    CONTACT_WATCH_PCS + POSITION_WATCH_PCS + Y_ADJUSTMENT_PCS
    + [0x828C81, 0x828C84, 0x828C87, 0x82916B, 0x82916E, 0x829171,
       0x82A61F, 0x82A622, 0x819E1B, 0x818B75, 0x818F98]
))


def capture_command(manifest: Path, out: Path) -> list[str]:
    resolved = manifest.resolve()
    if resolved == (ROOT / PRIMARY).resolve():
        expected = PRIMARY_SHA256
    elif resolved == (ROOT / VARIATION).resolve():
        expected = VARIATION_SHA256
    else:
        raise ValueError("composition capture accepts only preregistered scenarios")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError("composition replay manifest identity differs")
    command = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(FIRST_CAPTURE_FRAME),
        "--to-frame", str(LAST_CALL_FRAME),
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


def _u16(value: int) -> int:
    return value & 0xFFFF


def _s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def integrate_composed_axis(position: int, velocity: int, residue: int,
                            mask: int | None = None) -> dict[str, int | str]:
    """Execute the full reached total-sign branch, including the new crossing.

    M4-08 did not reach negative velocity plus a nonnegative wrapped total and
    rejected it.  The M4-09 frame-1666 variation reaches `$82:A630` BPL to the
    shared nonnegative path, so total sign—not incoming velocity sign—selects
    quotient/remainder restoration.
    """
    velocity_word = _u16(velocity)
    residue_word = _u16(residue)
    total_word = _u16(velocity_word + residue_word)
    if total_word & 0x8000:
        magnitude = _u16(-total_word)
        remainder = _u16(-(magnitude & 31))
        displacement = -(magnitude >> 5)
        branch = "negative"
    else:
        magnitude = total_word
        remainder = magnitude & 31
        displacement = magnitude >> 5
        branch = "nonnegative"
    unmasked = _u16(position + displacement)
    output = unmasked if mask is None else unmasked & mask
    return {
        "branch": branch, "velocity_word": velocity_word,
        "incoming_residue": _s16(residue_word), "wrapped_total": _s16(total_word),
        "magnitude": magnitude, "quotient": displacement,
        "remainder": _s16(remainder), "unmasked_position": unmasked,
        "position": output,
    }


def reached_y_adjustment(position_y: int, velocity_y: int, first_guard: int,
                         indexed_guard: int) -> dict[str, int | str | bool]:
    """Execute the reached 16-bit `$82:A96F--A9B2` helper.

    `CMP #$0200; BPL` tests N from wrapped subtraction.  The later BMI tests
    the original velocity word.  All arithmetic and the five LSRs are 16-bit.
    """
    velocity = _u16(velocity_y)
    increment = False
    reason = "first_guard_nonzero"
    amount = 0
    shifted = None
    if first_guard == 0:
        reason = "indexed_guard_nonzero"
        if indexed_guard == 0:
            reason = "velocity_cap"
            if _u16(velocity - 0x0200) & 0x8000:
                increment = True
                reason = "increment"
                y_index = 0x0010
                if not velocity & 0x8000:
                    shifted = velocity >> 5
                    y_index = _u16(0x0010 - shifted)
                amount = _u16(y_index + 3)
                velocity = _u16(velocity + amount)
    return {
        "reason": reason, "incremented": increment,
        "incoming_y": _u16(position_y), "incoming_velocity_y": _u16(velocity_y),
        "shifted_nonnegative_velocity": shifted,
        "velocity_addend": amount, "velocity_y": velocity,
        "position_y": _u16(position_y + int(increment)),
    }


def _helper_events(access: dict, frame: int, rider: int) -> dict[str, int]:
    """Select the helper invocation immediately preceding this integrator."""
    events = events_for_frame(access, frame)
    integrators = [index for index, event in enumerate(events)
                   if event[1] == 0x82A627 and event[2] == "read" and event[3] == 0x0FA9]
    if len(integrators) != 2:
        raise ValueError(f"frame {frame}: expected two ordered integrator entries")
    end = integrators[rider]
    starts = [index for index, event in enumerate(events[:end])
              if event[1] == 0x82A971 and event[2] == "read" and event[3] == 0x0F4B]
    if not starts:
        raise ValueError(f"frame {frame} rider {rider}: preceding Y helper is missing")
    block = events[starts[-1]:end]

    def one(pc: int, kind: str, address: int) -> int:
        rows = [event for event in block if event[1:4] == (pc, kind, address)]
        if len(rows) != 1 or rows[0][5] is None:
            raise ValueError(f"frame {frame} rider {rider}: incomplete ${pc:06X} helper evidence")
        return rows[0][5]

    selector = one(0x82A976, "read", 0x0FF9)
    if selector != rider * 2:
        raise ValueError(f"frame {frame}: Y helper rider selector differs")
    indexed_address = 0x0547 + selector
    return {
        "first_guard": one(0x82A971, "read", 0x0F4B),
        "selector": selector,
        "indexed_guard": one(0x82A979, "read", indexed_address),
        "incoming_velocity_y": one(0x82A97E, "read", 0x0FAB),
        "published_velocity_y": one(0x82A9AA, "write", 0x0FAB),
        "incoming_y": one(0x82A9AD, "read", 0x00A7),
        "published_y": one(0x82A9B0, "write", 0x00A7),
    }


def sample_track(track: bytes, points: list[tuple[int, int]], position_x: int,
                 position_y: int, coarse_width: int = COARSE_WIDTH) -> list[dict]:
    """Return all sample words and their logical track-data source offsets."""
    column = position_x >> 6
    row = position_y >> 6
    if coarse_width == 0 or column + 1 >= coarse_width or position_y >= 0x8000:
        raise ValueError("composition reaches an unrecovered coarse-grid edge")
    row_words = (row * coarse_width) & 0xFFFF
    upper_left = ((row_words + column) * 2) & 0xFFFF
    stride = (coarse_width * 2) & 0xFFFF
    coarse_addresses = [
        upper_left, (upper_left + 2) & 0xFFFF,
        (upper_left + stride) & 0xFFFF, (upper_left + stride + 2) & 0xFFFF,
    ]

    def word(offset: int) -> int:
        if offset < 0 or offset + 2 > len(track):
            raise ValueError("composition track-data source offset is unavailable")
        return int.from_bytes(track[offset:offset + 2], "little")

    coarse_offsets = [0x000F + address for address in coarse_addresses]
    blocks = [(word(offset) * 32) & 0xFFFF for offset in coarse_offsets]
    boundary_x = 64 - (position_x & 63)
    boundary_y = 64 - (position_y & 63)
    rows = []
    for point_index, (point_x, point_y) in enumerate(points):
        left = ((point_x - boundary_x) & 0x80) != 0
        upper = ((point_y - boundary_y) & 0x80) != 0
        quadrant = (0 if left else 1) + (0 if upper else 2)
        fine_x = ((point_x + position_x) & 48) >> 2
        fine_y = (point_y + position_y) & 48
        within_block = (fine_x + fine_y) >> 1
        source_offset = 0x800F + ((blocks[quadrant] + within_block) & 0xFFFF)
        rows.append({
            "point": point_index, "quadrant": quadrant,
            "coarse_source_offset": coarse_offsets[quadrant],
            "block": blocks[quadrant] // 32, "within_block": within_block,
            "source_offset": source_offset, "word": word(source_offset),
        })
    return rows


def _captured_position_targets(access_path: Path, access: dict) -> tuple[list[dict], dict]:
    """Read comparison targets without running the accepted M4-08 evaluator."""
    seed, seed_row_sha256, mask = _seed_from_series(access_path, access)
    validate_call_order(access)
    rows = []
    for frame in range(FIRST_CALL_FRAME, LAST_CALL_FRAME + 1):
        for rider in (0, 1):
            x = _captured_axis(access, frame, rider, "x")
            y = _captured_axis(access, frame, rider, "y")
            surface = _reg(access, 0x82A6BE, frame, rider)[1]
            guard = _reg(access, 0x82A6C3, frame, rider)[1] if surface else 0
            unsupported = _reg(access, 0x82A6C8, frame, rider)[1] if surface and not guard else 0
            direction = _reg(access, 0x82A6D0, frame, rider)[1] if surface and not guard and _s16(_u16(unsupported - 2)) < 0 else 0
            velocity_tail = _reg(access, 0x82A6DA, frame, rider)[1] if surface and not guard and _s16(_u16(unsupported - 2)) < 0 and not direction & 0x8000 else 0
            mode_row = _maybe_reg(access, 0x82A6DF, frame, rider)
            mode = mode_row[1] if mode_row else 0
            tail = slope_tail(y["integrated_position"], surface, guard, unsupported, direction, velocity_tail, mode)
            rows.append({
                "ordinal": len(rows), "frame": frame, "rider": rider,
                "inputs": {
                    "position_x": x["input_position"], "position_y": y["input_position"],
                    "velocity_x": _s16(x["velocity"]), "velocity_y": _s16(y["velocity"]),
                    "surface": _s16(surface), "guard": guard,
                    "unsupported_count": unsupported, "direction_word": direction,
                    "mode": mode, "track_mask": mask,
                },
                "x": {"remainder": x["residue"], "position": x["integrated_position"]},
                "y": {"remainder": y["residue"], "position": y["integrated_position"]},
                "slope_tail": tail,
                "publications": {
                    "x_published": _event_value(access, frame, 0x828DB9 if rider == 0 else 0x8292A7, "write", 0x0415 + 2 * rider),
                    "y_published": _event_value(access, frame, 0x828DB4 if rider == 0 else 0x8292A2, "write", 0x0419 + 2 * rider),
                },
            })
    return rows, {"values": seed, "row_sha256": seed_row_sha256, "track_mask": mask}


def compare_composed_contact(call: dict, content: dict[str, bytes]) -> dict:
    """Compose already accepted direct and reflected point predicates.

    The worker variation newly mixes path 0 and mask $4000 within one call;
    each point still follows an M4-06 or M4-07 preprocessing equation and the
    reducer/positive response are unchanged.
    """
    incoming = call["input"]
    points = expand_points(
        incoming["pose"], incoming["reflection"],
        content["collision-poses"], content["collision-templates"],
    )
    probes = []
    columns = []
    paths = set()
    for point_index, (raw, point) in enumerate(zip(call["raw_samples"], points, strict=True)):
        if raw & 0x03FF == 0:
            probes.append((0xA0, 0, 0))
            columns.append({"point": point_index, "kind": "marker", "column": None})
            continue
        path = raw & 0xC001
        paths.add(path)
        if path not in (0, 0x4000):
            raise ValueError("mixed call reaches an unaccepted descriptor path")
        tile = tile_index(raw)
        if content["tile-flags"][tile] & 1:
            raise ValueError("mixed call reaches horizontal geometry")
        direct_column = (point[0] + (incoming["x"] & 15)) & 15
        column = ((~direct_column) & 15) if path == 0x4000 else direct_column
        local_y = (point[1] + (incoming["y"] & 15)) & 15
        offset = tile * 32 + column * 2
        height, table_angle = content["tile-tables"][offset:offset + 2]
        angle = ((table_angle ^ 0xFF) + 1) & 0xFF if path == 0x4000 else table_angle
        penetration = 0xA0 if height == 0xA0 else (local_y - ((height - 1) & 0xFF)) & 0xFF
        probes.append((penetration, angle, raw))
        columns.append({
            "point": point_index,
            "kind": "reflected_vertical" if path else "direct_vertical",
            "direct_column": direct_column, "column": column,
            "table_angle": table_angle, "computed_angle": angle,
        })
    preprocessing = compare_preprocessing(call, probes)
    summary = reduce_vertical(probes, content["tile-flags"])
    expected = {
        "supported": not bool(call["support_summary"] & 0x80),
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
    if summary != expected:
        raise ValueError(f"computed mixed reducer differs at {call['frame']}/{call['rider']}: {summary} != {expected}")
    signed_angle = _s16(summary["angle"] if summary["angle"] < 0x80 else summary["angle"] | 0xFF00)
    if summary["supported"] and 0x4000 in paths and signed_angle >= 0:
        resolved, scratch = resolve_reflected_response(
            call, summary, content["reflected-vertical-slope-coefficients"],
        )
    else:
        resolved, scratch = resolve_response(
            call, summary, content["vertical-slope-coefficients"],
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
    for name, (computed, captured) in comparisons.items():
        if computed != captured:
            raise ValueError(f"computed mixed response differs at {call['frame']}: {name}")
    if scratch["shifted_velocity"] is not None:
        if _last_write(call, 0x02D4) != scratch["shifted_velocity"]:
            raise ValueError(f"computed mixed shifted velocity differs at {call['frame']}")
        if _last_write(call, 0x0026) != scratch["angle_contribution"]:
            raise ValueError(f"computed mixed angle contribution differs at {call['frame']}")
    return {
        "ordinal": call["ordinal"], "frame": call["frame"], "rider": call["rider"],
        "preprocessing": preprocessing, "columns": columns, "reducer": summary,
        "branch": resolved["branch"] + ("_mixed" if paths == {0, 0x4000} else ""),
        "response_and_publication": {
            name: {"computed": computed, "captured": captured, "match": True}
            for name, (computed, captured) in comparisons.items()
        },
    }


EXTERNAL_FIELDS = {
    "before_y_adjustment": ["first_guard", "indexed_guard", "incoming_velocity_y"],
    "position_integrator": [
        "velocity_x", "surface", "guard", "unsupported_count",
        "direction_word", "mode", "track_mask",
    ],
    "sampling": ["pose", "reflection"],
    "contact": [
        "vx", "vy", "response_a", "response_b", "response_impulse",
        "unsupported_count", "unsupported_duration", "surface_angle",
        "angle_sentinel", "auxiliary_flag", "mode", "special", "phase",
        "previous_x", "previous_y",
    ],
    "contact_live_dependencies": ["cartridge_option", "rider_selector"],
}
PHASE_ORDER = [
    "y_adjustment", "position_integration", "collision_point_expansion",
    "track_sampling", "contact", "caller_publication",
]


def composition_rows(access_path: Path, content_dir: Path) -> tuple[list[dict], dict]:
    access = json.loads(access_path.read_text())
    validate_identity(access)
    if access.get("frames") != {"start": 1649, "end": 1700, "count": 52}:
        raise ValueError("composition capture frame domain differs")
    if access.get("status") != "complete" or access.get("watch_pcs_truncated"):
        raise ValueError("complete nontruncated composition capture is required")
    if access.get("residual", {}).get("unresolved_stores") != 0:
        raise ValueError("composition capture has unresolved stores")
    content = load_content(content_dir)
    captured = captured_calls(access)
    attach_live_dependencies(access, captured)
    calls = [call for call in captured if call["frame"] >= FIRST_CALL_FRAME]
    for ordinal, call in enumerate(calls):
        call["ordinal"] = ordinal
    position_targets, seed = _captured_position_targets(access_path, access)
    if len(calls) != 102 or len(position_targets) != 102:
        raise ValueError("composition call count differs")

    values = seed["values"]
    recurrent = {
        0: {"x": values["player_x"], "y": values["player_y"],
            "rx": values["player_x_residue"], "ry": values["player_y_residue"]},
        1: {"x": values["opponent_x"], "y": values["opponent_y"],
            "rx": values["opponent_x_residue"], "ry": values["opponent_y_residue"]},
    }
    rows = []
    helper_counts: dict[str, int] = {}
    for ordinal, (call, target) in enumerate(zip(calls, position_targets, strict=True)):
        frame, rider = call["frame"], call["rider"]
        if (target["ordinal"], target["frame"], target["rider"]) != (ordinal, frame, rider):
            raise ValueError("position/contact call order differs")
        state = recurrent[rider]
        observed_helper = _helper_events(access, frame, rider)
        if observed_helper["incoming_y"] != state["y"]:
            raise ValueError(f"frame {frame} rider {rider}: helper did not consume recurrent contact Y")
        helper = reached_y_adjustment(
            state["y"], observed_helper["incoming_velocity_y"],
            observed_helper["first_guard"], observed_helper["indexed_guard"],
        )
        if (helper["velocity_y"], helper["position_y"]) != (
                observed_helper["published_velocity_y"], observed_helper["published_y"]):
            raise ValueError(f"frame {frame} rider {rider}: computed Y adjustment differs")
        helper_counts[str(helper["reason"])] = helper_counts.get(str(helper["reason"]), 0) + 1

        inputs = target["inputs"]
        if (inputs["position_x"], inputs["position_y"], _u16(inputs["velocity_y"])) != (
                state["x"], helper["position_y"], helper["velocity_y"]):
            raise ValueError(f"frame {frame} rider {rider}: integrator publication order differs")
        x = integrate_composed_axis(state["x"], inputs["velocity_x"], state["rx"], inputs["track_mask"])
        y = integrate_composed_axis(int(helper["position_y"]), int(helper["velocity_y"]), state["ry"])
        tail = slope_tail(
            int(y["position"]), inputs["surface"], inputs["guard"],
            inputs["unsupported_count"], inputs["direction_word"],
            inputs["velocity_y"], inputs["mode"],
        )
        publications = {
            "x_residue": x["remainder"], "y_residue": y["remainder"],
            "x_integrated": x["position"], "y_integrated": y["position"],
            "y_final": tail["position"], "x_published": x["position"],
            "y_published": tail["position"],
        }
        target_publications = {
            "x_residue": target["x"]["remainder"], "y_residue": target["y"]["remainder"],
            "x_integrated": target["x"]["position"], "y_integrated": target["y"]["position"],
            "y_final": target["slope_tail"]["position"],
            "x_published": target["publications"]["x_published"],
            "y_published": target["publications"]["y_published"],
        }
        if publications != target_publications or tail != target["slope_tail"]:
            raise ValueError(f"frame {frame} rider {rider}: recurrent position result differs")
        if (call["input"]["x"], call["input"]["y"]) != (x["position"], tail["position"]):
            raise ValueError(f"frame {frame} rider {rider}: sampling/contact position publication differs")

        points = expand_points(
            call["input"]["pose"], call["input"]["reflection"],
            content["collision-poses"], content["collision-templates"],
        )
        sample_rows = sample_track(
            content["track-data"], points, int(x["position"]), int(tail["position"]),
        )
        samples = [sample["word"] for sample in sample_rows]
        if samples != call["raw_samples"]:
            raise ValueError(f"frame {frame} rider {rider}: computed track samples differ")
        computed_call = copy.deepcopy(call)
        computed_call["input"]["x"] = int(x["position"])
        computed_call["input"]["y"] = int(tail["position"])
        computed_call["raw_samples"] = samples
        try:
            contact = compare_composed_contact(computed_call, content)
        except ValueError as error:
            raise ValueError(f"frame {frame} rider {rider}: composed contact: {error}") from error
        contact_x = contact["response_and_publication"]["x"]["computed"]
        contact_y = contact["response_and_publication"]["y"]["computed"]
        recurrent[rider] = {
            "x": contact_x, "y": contact_y,
            "rx": int(x["remainder"]), "ry": int(y["remainder"]),
        }
        external_contact = {name: call["input"][name] for name in EXTERNAL_FIELDS["contact"]}
        rows.append({
            "ordinal": ordinal, "frame": frame, "rider": rider,
            "recurrent_input": dict(state), "y_adjustment": helper,
            "external": {
                "before_y_adjustment": {name: observed_helper[name] for name in EXTERNAL_FIELDS["before_y_adjustment"]},
                "position_integrator": {name: inputs[name] for name in EXTERNAL_FIELDS["position_integrator"]},
                "sampling": {name: call["input"][name] for name in EXTERNAL_FIELDS["sampling"]},
                "contact": external_contact,
                "contact_live_dependencies": call.get("live_dependencies", {}),
            },
            "position": {"x": x, "y": y, "slope_tail": tail},
            "samples": sample_rows, "contact": contact,
            "recurrent_output": dict(recurrent[rider]),
        })
    final = {
        "player_x": recurrent[0]["x"], "opponent_x": recurrent[1]["x"],
        "player_y": recurrent[0]["y"], "opponent_y": recurrent[1]["y"],
        "player_x_residue": recurrent[0]["rx"], "opponent_x_residue": recurrent[1]["rx"],
        "player_y_residue": recurrent[0]["ry"], "opponent_y_residue": recurrent[1]["ry"],
    }
    metadata = {
        "seed": seed, "helper_counts": helper_counts,
        "external_fields": EXTERNAL_FIELDS, "phase_order": PHASE_ORDER, "final": final,
        "sample_words": sum(len(row["samples"]) for row in rows),
        "sample_words_sha256": _digest([
            [sample["word"] for sample in row["samples"]] for row in rows
        ]),
        "sample_sources_sha256": _digest([
            [sample["source_offset"] for sample in row["samples"]] for row in rows
        ]),
        "position_branch_counts": dict(sorted(Counter(
            f"{axis}_{row['position'][axis]['branch']}"
            for row in rows for axis in ("x", "y")
        ).items())),
        "contact_branch_counts": dict(sorted(Counter(
            row["contact"]["branch"] for row in rows
        ).items())),
    }
    return rows, metadata


def _build_report(access_path: Path, content_dir: Path) -> dict:
    rows, metadata = composition_rows(access_path, content_dir)
    return {
        "schema_version": 1, "kind": "zoom_zoo_position_contact_composition",
        "status": "passed", "access_sha256": hashlib.sha256(access_path.read_bytes()).hexdigest(),
        "frames": {"seed": 1649, "first": 1650, "last": 1700},
        "calls": len(rows), "points": metadata["sample_words"],
        "rows_sha256": _digest(rows), **metadata, "rows": rows,
        "domain": "bounded reference composition with captured external velocity, pose, reflection and contact state; no native ZOOM ZOO support",
    }


def derive(access_path: Path, content_dir: Path, report_path: Path) -> dict:
    report = _build_report(access_path, content_dir)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def validate_component_manifest(document: dict) -> None:
    required = {
        "schema_version", "kind", "scenario_id", "source", "frames", "calls",
        "points", "seed", "y_adjustment_routine", "coarse_width",
        "rows_sha256", "sample_words_sha256", "sample_sources_sha256",
        "position_branch_counts", "helper_counts", "contact_branch_counts",
        "final", "external_fields", "phase_order", "static_content", "description", "limits",
    }
    if set(document) != required or document.get("schema_version") != 1 or document.get("kind") != "zoom_zoo_position_contact_reference":
        raise ValueError("composition manifest schema differs")
    scenario = document.get("scenario_id")
    if scenario not in COMPONENT_MANIFEST_SHA256:
        raise ValueError("composition scenario differs")
    replay, replay_sha, access_sha, series_sha = {
        "race-crawler-zoom-zoo-3300": (
            PRIMARY, PRIMARY_SHA256,
            "f3d0013aa84bfa1d5ab795fe62269745abf93a402d816326c3d2b56ded961465",
            "53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d",
        ),
        "race-crawler-zoom-zoo-right-release-1666": (
            VARIATION, VARIATION_SHA256,
            "e853375ec890afa527c67cd1abeef8c0a9c8ef6d071ff06d830c2226d230f69c",
            "335263f2a2f3b763198afb1d0bcfb6f4dadf48c945d30c35c4ce579ed282addc",
        ),
    }[scenario]
    expected_source = {
        "rom_sha256": "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e",
        "core_commit": "7d5aa1e656b9171524d01b1b22917197d8121cb4",
        "core_patch_sha256": "a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885",
        "replay_manifest": replay, "replay_manifest_sha256": replay_sha,
        "access_sha256": access_sha, "wram_series_sha256": series_sha,
    }
    if document["source"] != expected_source:
        raise ValueError("composition source identity differs")
    if document["frames"] != {"seed": 1649, "first": 1650, "last": 1700} or document["calls"] != 102 or document["points"] != 1020:
        raise ValueError("composition domain differs")
    if document["y_adjustment_routine"] != {
        "bus": "82:A96F-82:A9B2", "bytes": 68, "sha256": Y_ROUTINE_SHA256,
        "accumulator_width": 16, "index_width": 16,
    } or document["coarse_width"] != 256:
        raise ValueError("composition helper/sampling identity differs")
    if document["external_fields"] != EXTERNAL_FIELDS:
        raise ValueError("composition external field inventory differs")
    if document["phase_order"] != PHASE_ORDER:
        raise ValueError("composition phase order differs")
    if document["static_content"] != {
        "contract": "tests/manifests/content/zoom-zoo-reference-contract.json",
        "contract_sha256": "017a4eb941abb0e87ea0e3be4509d9043198466cb461f560517f355938c1d699",
        "track_data_sha256": "db6770152e399f9d16fc6937b5d56588a8f67e825ae70d6578b77d36053fdd28",
        "collision_poses_sha256": "9d1754d38c20cb2900239557550211ab6fc23d9b0237e17b78fb29f3bf272c32",
        "collision_templates_sha256": "2f03a8cb985899436603ef36b233b28f7b4213e4ba106fca328a6b02cdb081c7",
        "tile_tables_sha256": "649b96ff43ef467fe57bac16eb876f96a1ebc6f0307a5270f97a7ce1f63a84c7",
        "tile_flags_sha256": "11aa211a148bced17e6c1b63a19e6e9c71ff1f8fed83954613f2ea62b15069c4",
        "slope_coefficients_sha256": "f5016c76c1f4e60c988c67672b12da1d3b10948934f5f1e8b29135274203e7a1",
    }:
        raise ValueError("composition static content inventory differs")
    if document["description"] != "Recurrent eight-word position state feeding width-256 sampling and accepted vertical contact for 102 calls":
        raise ValueError("composition description differs")
    if document["limits"] != "Frames 1650-1700 only; velocity, pose, reflection and non-position contact state remain captured external inputs; no native ZOOM ZOO support":
        raise ValueError("composition limits differ")
    expected = COMPONENT_MANIFEST_SHA256[scenario]
    if _digest(document) != expected:
        raise ValueError("composition authored manifest identity differs")


def verify(access_path: Path, content_dir: Path, manifest_path: Path,
           report_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    validate_component_manifest(manifest)
    report = _build_report(access_path, content_dir)
    if report["access_sha256"] != manifest["source"]["access_sha256"]:
        raise ValueError("composition capture identity differs")
    compared = {
        "frames": report["frames"], "calls": report["calls"], "points": report["points"],
        "seed": report["seed"], "rows_sha256": report["rows_sha256"],
        "sample_words_sha256": report["sample_words_sha256"],
        "sample_sources_sha256": report["sample_sources_sha256"],
        "position_branch_counts": report["position_branch_counts"],
        "helper_counts": report["helper_counts"],
        "contact_branch_counts": report["contact_branch_counts"],
        "final": report["final"], "external_fields": report["external_fields"],
        "phase_order": report["phase_order"],
    }
    expected = {name: manifest[name] for name in compared}
    if compared != expected:
        raise ValueError("composition result differs from authored manifest")
    report["manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def compare_inputs(primary_path: Path, variation_path: Path, content_dir: Path,
                   report_path: Path) -> dict:
    primary = _build_report(primary_path, content_dir)
    variation = _build_report(variation_path, content_dir)
    if primary["access_sha256"] != "f3d0013aa84bfa1d5ab795fe62269745abf93a402d816326c3d2b56ded961465" or variation["access_sha256"] != "e853375ec890afa527c67cd1abeef8c0a9c8ef6d071ff06d830c2226d230f69c":
        raise ValueError("composition comparison capture identity differs")
    if primary["seed"] != variation["seed"]:
        raise ValueError("composition variation seed differs")
    primary_access = json.loads(primary_path.read_text())
    variation_access = json.loads(variation_path.read_text())
    frames = range(1649, 1701)
    primary_series = _series_rows(primary_path, primary_access, frames)
    variation_series = _series_rows(variation_path, variation_access, frames)
    controller = [frame for frame in frames
                  if primary_series[frame][0x0313] != variation_series[frame][0x0313]]
    if controller != [1666]:
        raise ValueError("worker variation controller divergence differs")
    row_differences = [(left["frame"], left["rider"])
                       for left, right in zip(primary["rows"], variation["rows"], strict=True)
                       if left != right]
    if not row_differences or row_differences[0] != (1666, 0):
        raise ValueError("worker variation first composition divergence differs")
    if any(rider != 0 for _frame, rider in row_differences):
        raise ValueError("worker variation unexpectedly changes opponent composition")
    sample_differences = [(left["frame"], left["rider"])
                          for left, right in zip(primary["rows"], variation["rows"], strict=True)
                          if [sample["word"] for sample in left["samples"]]
                          != [sample["word"] for sample in right["samples"]]]
    branch_differences = [
        {"frame": left["frame"], "rider": left["rider"],
         "primary": left["contact"]["branch"], "variation": right["contact"]["branch"]}
        for left, right in zip(primary["rows"], variation["rows"], strict=True)
        if left["contact"]["branch"] != right["contact"]["branch"]
    ]
    crossings = []
    for row in variation["rows"]:
        for axis in ("x", "y"):
            position = row["position"][axis]
            if position["velocity_word"] & 0x8000 and position["wrapped_total"] >= 0:
                crossings.append({"frame": row["frame"], "rider": row["rider"], "axis": axis})
    if sample_differences[0] != (1670, 0) or crossings != [{"frame": 1685, "rider": 0, "axis": "y"}]:
        raise ValueError("worker variation sampling/crossing relevance differs")
    if not any(row["contact"]["branch"] == "continuous_reflected_mixed" and row["frame"] == 1683
               for row in variation["rows"]):
        raise ValueError("worker variation mixed contact path is missing")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_composition_input_comparison",
        "status": "passed", "prediction": {
            "exact_through": 1665, "controller_divergence_frames": [1666],
            "branch_and_reconvergence_preclaimed": False,
        },
        "first_composition_divergence": {"frame": 1666, "rider": 0},
        "first_sample_divergence": {"frame": 1670, "rider": 0},
        "contact_branch_differences": branch_differences,
        "new_reached_position_path": crossings[0],
        "new_reached_contact_path": {"frame": 1683, "rider": 0, "kind": "mixed_direct_reflected_vertical"},
        "opponent_exact_through_1700": True,
        "player_reconverged_through_1700": not any(frame == 1700 for frame, _rider in row_differences),
        "primary_rows_sha256": primary["rows_sha256"],
        "variation_rows_sha256": variation["rows_sha256"],
    }
    report["comparison_sha256"] = _digest(report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--manifest", type=Path, required=True)
    capture_parser.add_argument("--out", type=Path, required=True)
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
    args = parser.parse_args()
    try:
        if args.command == "capture":
            return capture(args.manifest, args.out)
        if args.command == "derive":
            derive(args.access, args.content, args.report)
        elif args.command == "verify":
            verify(args.access, args.content, args.manifest, args.report)
        else:
            compare_inputs(args.primary_access, args.variation_access, args.content, args.report)
        return 0
    except FileNotFoundError as error:
        print(error, file=sys.stderr); return 2
    except (OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr); return 3
    except subprocess.TimeoutExpired as error:
        print(error, file=sys.stderr); return 4


if __name__ == "__main__":
    raise SystemExit(main())
