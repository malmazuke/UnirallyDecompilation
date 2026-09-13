"""Capture the preregistered M4-08 position-integration experiment.

This research-only surface freezes the inputs, intermediate scratch and
publications of $82:A627--A6F7.  It does not modify or invoke native gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .contact_research.summarize import events_for_frame, validate_identity


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1662.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
ROM_SHA256 = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
ROUTINE_FILE_OFFSET = 0x12627
ROUTINE_BYTES = 209
ROUTINE_SHA256 = "1b6497ea4306faa243c685f0f23b9ac7d22232db57ce3299f4627bbc22291adc"
PRIMARY_COMPONENT_MANIFEST = "tests/manifests/native/zoom-zoo-position-primary.reference.json"
COMPONENT_MANIFEST_SHA256 = {
    "race-crawler-zoom-zoo-3300": "b09b339f9d8f48cf4fe3a919d4d4f4c9e8c47aa531747329a4ca8d73ff44fbaa",
    "race-crawler-zoom-zoo-right-release-1662": "7c05c332467c057b0a8e715d9d32ab6b8a135d1cd85b6775120e3f27474fee52",
}
SEED_VALUES = {
    "player_x": 9200, "opponent_x": 8248,
    "player_y": 1561, "opponent_y": 1452,
    "player_x_residue": -1, "opponent_x_residue": -24,
    "player_y_residue": 22, "opponent_y_residue": -1,
}

# End-of-frame 1649 supplies the one stateful seed.  Calls on 1650--1700 are
# the declared evaluation domain; frame 1649 is captured only for provenance.
FIRST_CAPTURE_FRAME = 1649
FIRST_CALL_FRAME = 1650
LAST_CALL_FRAME = 1700

# Persistent positions, velocities and four signed residues; the track mask;
# every direct-page input/guard/scratch used by the routine; and caller state
# needed to bind the two ordered rider calls and their final publications.
WATCH_ADDRESSES = sorted(set(
    [
        0x0000, 0x00A5, 0x00A7,
        0x0401, 0x0403, 0x0405, 0x0407,
        0x0415, 0x0417, 0x0419, 0x041B,
        0x04BB, 0x04BD, 0x04BF, 0x04C1,
        0x0B6E, 0x0B70, 0x0D4F,
        0x0F17, 0x0F23, 0x0F2D, 0x0F31, 0x0F33,
        0x0FA9, 0x0FAB,
    ]
    + list(range(0x0F13, 0x0FC2))
))

# Pre-instruction snapshots freeze every branch, arithmetic intermediate and
# publication in the bounded routine, plus the two contact caller boundaries.
WATCH_PCS = [
    0x82A627, 0x82A62A, 0x82A62C, 0x82A62D, 0x82A630, 0x82A632,
    0x82A635, 0x82A636, 0x82A637, 0x82A63A, 0x82A63D, 0x82A63E,
    0x82A641, 0x82A642, 0x82A643, 0x82A644, 0x82A645, 0x82A646,
    0x82A647, 0x82A649, 0x82A64B, 0x82A64C, 0x82A64E, 0x82A651,
    0x82A653, 0x82A655, 0x82A656, 0x82A659, 0x82A65B, 0x82A65C,
    0x82A65F, 0x82A662, 0x82A663, 0x82A664, 0x82A665, 0x82A666,
    0x82A667, 0x82A668, 0x82A66A, 0x82A66C, 0x82A66D, 0x82A66F,
    0x82A672, 0x82A674, 0x82A677, 0x82A679, 0x82A67A, 0x82A67D,
    0x82A67F, 0x82A682, 0x82A683, 0x82A684, 0x82A687, 0x82A68A,
    0x82A68B, 0x82A68E, 0x82A68F, 0x82A690, 0x82A691, 0x82A692,
    0x82A693, 0x82A694, 0x82A696, 0x82A698, 0x82A699, 0x82A69B,
    0x82A69D, 0x82A69F, 0x82A6A0, 0x82A6A3, 0x82A6A5, 0x82A6A6,
    0x82A6A9, 0x82A6AC, 0x82A6AD, 0x82A6AE, 0x82A6AF, 0x82A6B0,
    0x82A6B1, 0x82A6B2, 0x82A6B4, 0x82A6B6, 0x82A6B7, 0x82A6B9,
    0x82A6BB, 0x82A6BE, 0x82A6C0, 0x82A6C3, 0x82A6C5, 0x82A6C8,
    0x82A6CB, 0x82A6CD, 0x82A6D0, 0x82A6D3, 0x82A6D5, 0x82A6D7,
    0x82A6DA, 0x82A6DC, 0x82A6DF, 0x82A6E1, 0x82A6E3, 0x82A6E5,
    0x82A6E8, 0x82A6E9, 0x82A6EB, 0x82A6ED, 0x82A6EF, 0x82A6F1,
    0x82A6F2, 0x82A6F5, 0x82A6F7,
    0x818D97, 0x818D9C, 0x818F98, 0x818F9D,
]


def capture_command(manifest: Path, out: Path) -> list[str]:
    if manifest.resolve() == (ROOT / PRIMARY).resolve():
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != PRIMARY_SHA256:
            raise ValueError("accepted primary replay manifest identity differs")
    elif manifest.resolve() != (ROOT / VARIATION).resolve():
        raise ValueError("position capture accepts only the preregistered scenarios")
    result = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(FIRST_CAPTURE_FRAME),
        "--to-frame", str(LAST_CALL_FRAME),
        "--wram-series-range", "0", "0x2200", "--timeout", "180",
        "--report", str(out / "report.json"),
    ]
    for address in WATCH_ADDRESSES:
        result += ["--watch-address", hex(address)]
    for pc in WATCH_PCS:
        result += ["--watch-pc", hex(pc)]
    return result


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


def integrate_axis(position: int, velocity: int, residue: int,
                   mask: int | None = None) -> dict[str, int | str]:
    """Execute the reached 16-bit signed /32 recurrence.

    The original uses wrapped 16-bit ADC before sign restoration. Its two
    velocity-sign entry paths only reach totals with the same sign in this
    bounded capture; crossing that unobserved branch domain rejects.
    """
    velocity_word = _u16(velocity)
    residue_word = _u16(residue)
    total_word = _u16(velocity_word + residue_word)
    if velocity_word & 0x8000 and not total_word & 0x8000:
        raise ValueError(f"unobserved velocity/residue sign crossing: velocity={_s16(velocity_word)} residue={_s16(residue_word)} total={_s16(total_word)}")
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


def slope_tail(y: int, surface: int, guard: int, unsupported_count: int,
               direction_word: int, velocity_y: int, mode: int) -> dict[str, int | str]:
    """Apply the reached post-integration Y adjustment in instruction order."""
    reason = "surface_zero"
    adjustment = 0
    if surface:
        if guard:
            reason = "guard_nonzero"
        elif _s16(_u16(unsupported_count - 2)) >= 0:
            reason = "unsupported_count_at_least_two"
        elif direction_word & 0x8000:
            reason = "direction_high_bit"
        elif _s16(velocity_y) < 0:
            reason, adjustment = "negative_velocity", -1
        elif mode:
            reason, adjustment = "mode_increment", 1
        else:
            reason, adjustment = "ordinary_positive", 4
    return {"reason": reason, "adjustment": adjustment, "position": _u16(y + adjustment)}


def _register_rows(access: dict, pc: int, frame: int) -> list[list[int]]:
    return [row for row in access["watch_pcs"].get(str(pc), []) if row[0] == frame]


def _reg(access: dict, pc: int, frame: int, rider: int) -> list[int]:
    rows = [row for row in _register_rows(access, pc, frame) if row[3] == rider * 2]
    if len(rows) != 1:
        raise ValueError(f"frame {frame} rider {rider}: expected one ${pc:06X} register row, got {len(rows)}")
    return rows[0]


def _maybe_reg(access: dict, pc: int, frame: int, rider: int) -> list[int] | None:
    rows = [row for row in _register_rows(access, pc, frame) if row[3] == rider * 2]
    if len(rows) > 1:
        raise ValueError(f"frame {frame} rider {rider}: duplicate ${pc:06X} register rows")
    return rows[0] if rows else None


def _event_value(access: dict, frame: int, pc: int, kind: str,
                 address: int | None = None) -> int:
    rows = [event for event in events_for_frame(access, frame)
            if event[1] == pc and event[2] == kind
            and (address is None or event[3] == address)]
    if len(rows) != 1 or rows[0][5] is None:
        raise ValueError(f"frame {frame}: incomplete ${pc:06X} {kind} provenance")
    return rows[0][5]


def _captured_axis(access: dict, frame: int, rider: int, axis: str) -> dict[str, int]:
    if axis == "x":
        velocity = _reg(access, 0x82A62A, frame, rider)[1]
        positive = _maybe_reg(access, 0x82A65F, frame, rider) is not None
        total_pc = 0x82A630 if velocity & 0x8000 else 0x82A659
        input_pc = 0x82A66C if positive else 0x82A64B
        residue_pc = 0x82A65F if positive else 0x82A63E
        position_pc = 0x82A672 if positive else 0x82A651
        magnitude_pc = 0x82A636
        quotient_pc = 0x82A668 if positive else 0x82A647
    else:
        velocity = _reg(access, 0x82A677, frame, rider)[1]
        positive = _maybe_reg(access, 0x82A6A9, frame, rider) is not None
        total_pc = 0x82A67D if velocity & 0x8000 else 0x82A6A3
        input_pc = 0x82A6B6 if positive else 0x82A698
        residue_pc = 0x82A6A9 if positive else 0x82A68B
        position_pc = 0x82A6B9 if positive else 0x82A69B
        magnitude_pc = 0x82A683
        quotient_pc = 0x82A6B2 if positive else 0x82A694
    total = _reg(access, total_pc, frame, rider)[1]
    magnitude_row = _maybe_reg(access, magnitude_pc, frame, rider)
    return {
        "velocity": velocity,
        "input_position": _reg(access, input_pc, frame, rider)[1],
        "wrapped_total": _s16(total),
        "magnitude": magnitude_row[1] if magnitude_row else total,
        "quotient_magnitude": _reg(access, quotient_pc, frame, rider)[1],
        "residue": _s16(_reg(access, residue_pc, frame, rider)[1]),
        "integrated_position": _reg(access, position_pc, frame, rider)[1],
    }


def _seed_from_series(access_path: Path, access: dict) -> tuple[dict[str, int], str, int]:
    series = access.get("wram_series", {})
    frames = series.get("frames")
    if not isinstance(frames, list) or 1649 not in frames or series.get("start") != 0 or series.get("length") != 0x2200:
        raise ValueError("complete end-1649 work-RAM seed series is unavailable")
    path = access_path.parent / series.get("path", "")
    raw = path.read_bytes()
    if len(raw) != series.get("bytes") or hashlib.sha256(raw).hexdigest() != series.get("sha256"):
        raise ValueError("work-RAM seed series identity differs")
    size = series["length"]
    start = frames.index(1649) * size
    row = raw[start:start + size]
    if len(row) != size:
        raise ValueError("end-1649 seed row is incomplete")
    def word(address: int) -> int:
        return int.from_bytes(row[address:address + 2], "little")
    result = {
        "player_x": word(0x0415), "opponent_x": word(0x0417),
        "player_y": word(0x0419), "opponent_y": word(0x041B),
        "player_x_residue": _s16(word(0x0401)), "opponent_x_residue": _s16(word(0x0403)),
        "player_y_residue": _s16(word(0x0405)), "opponent_y_residue": _s16(word(0x0407)),
    }
    if result != SEED_VALUES:
        raise ValueError("authenticated end-1649 seed differs")
    mask = word(0x0D4F)
    if mask != 0x3FFF:
        raise ValueError("authenticated track mask differs")
    for frame_index, frame in enumerate(frames):
        if frame < 1649:
            continue
        frame_row = raw[frame_index * size:(frame_index + 1) * size]
        frame_mask = int.from_bytes(frame_row[0x0D4F:0x0D51], "little")
        if frame_mask != mask:
            raise ValueError(f"track mask differs at frame {frame}")
    return result, hashlib.sha256(row).hexdigest(), mask


def position_calls(access_path: Path, access: dict) -> tuple[list[dict], dict]:
    """Compute 102 calls with four recurrent residues and compare the capture."""
    validate_identity(access)
    if access.get("frames") != {"start": 1649, "end": 1700, "count": 52}:
        raise ValueError("position capture frame domain differs")
    if access.get("residual", {}).get("unresolved_stores") != 0 or access.get("watch_pcs_truncated"):
        raise ValueError("position capture is incomplete")
    seed, seed_row_sha256, mask = _seed_from_series(access_path, access)
    residues = {
        (0, "x"): seed["player_x_residue"], (1, "x"): seed["opponent_x_residue"],
        (0, "y"): seed["player_y_residue"], (1, "y"): seed["opponent_y_residue"],
    }
    rows: list[dict] = []
    ordinal = 0
    validate_call_order(access)
    for frame in range(FIRST_CALL_FRAME, LAST_CALL_FRAME + 1):
        for rider in (0, 1):
            x_capture = _captured_axis(access, frame, rider, "x")
            y_capture = _captured_axis(access, frame, rider, "y")
            x = integrate_axis(x_capture["input_position"], x_capture["velocity"], residues[(rider, "x")], mask)
            y = integrate_axis(y_capture["input_position"], y_capture["velocity"], residues[(rider, "y")])
            surface = _reg(access, 0x82A6BE, frame, rider)[1]
            guard = _reg(access, 0x82A6C3, frame, rider)[1] if surface else 0
            unsupported = _reg(access, 0x82A6C8, frame, rider)[1] if surface and not guard else 0
            direction = _reg(access, 0x82A6D0, frame, rider)[1] if surface and not guard and _s16(_u16(unsupported - 2)) < 0 else 0
            velocity_tail = _reg(access, 0x82A6DA, frame, rider)[1] if surface and not guard and _s16(_u16(unsupported - 2)) < 0 and not direction & 0x8000 else 0
            mode_row = _maybe_reg(access, 0x82A6DF, frame, rider)
            mode = mode_row[1] if mode_row else 0
            tail = slope_tail(y["position"], surface, guard, unsupported, direction, velocity_tail, mode)
            # Store-PC register snapshots retain the rider index and the value
            # about to be published, avoiding ambiguity when both riders take
            # the same branch in one frame.
            if tail["adjustment"] == 0:
                captured_final_y = y_capture["integrated_position"]
            elif tail["adjustment"] == 4:
                captured_final_y = _reg(access, 0x82A6EB, frame, rider)[1]
            elif tail["adjustment"] == -1:
                captured_final_y = _reg(access, 0x82A6F5, frame, rider)[1]
            elif tail["adjustment"] == 1:
                captured_final_y = _event_value(access, frame, 0x82A6E1, "rmw", 0x00A7)
            expected = {
                "x_residue": x_capture["residue"], "y_residue": y_capture["residue"],
                "x_integrated": x_capture["integrated_position"],
                "y_integrated": y_capture["integrated_position"], "y_final": captured_final_y,
                "x_published": _event_value(access, frame, 0x828DB9 if rider == 0 else 0x8292A7, "write", 0x0415 + 2 * rider),
                "y_published": _event_value(access, frame, 0x828DB4 if rider == 0 else 0x8292A2, "write", 0x0419 + 2 * rider),
            }
            actual = {
                "x_residue": x["remainder"], "y_residue": y["remainder"],
                "x_integrated": x["position"], "y_integrated": y["position"],
                "y_final": tail["position"], "x_published": x["position"],
                "y_published": tail["position"],
            }
            for name, computed, captured in (
                ("x wrapped total", x["wrapped_total"], x_capture["wrapped_total"]),
                ("x magnitude", x["magnitude"], x_capture["magnitude"]),
                ("x quotient", abs(int(x["quotient"])), x_capture["quotient_magnitude"]),
                ("y wrapped total", y["wrapped_total"], y_capture["wrapped_total"]),
                ("y magnitude", y["magnitude"], y_capture["magnitude"]),
                ("y quotient", abs(int(y["quotient"])), y_capture["quotient_magnitude"]),
            ):
                if computed != captured:
                    raise ValueError(f"frame {frame} rider {rider}: {name} intermediate differs")
            if actual != expected:
                raise ValueError(f"frame {frame} rider {rider}: computed position publication differs: {actual} != {expected}")
            # `$82:A6E9` consumes the value written at `$82:A6B9` in the same
            # call (or `$82:A69B` after a negative Y total). The accumulator snapshots before ADC and before STA prove
            # the ordered producer/consumer relation without a default.
            if tail["adjustment"] == 4:
                producer = y_capture["integrated_position"]
                addend = _reg(access, 0x82A6E9, frame, rider)[1]
                consumer = _reg(access, 0x82A6EB, frame, rider)[1]
                if producer != y["position"] or addend != 4 or consumer != _u16(producer + addend):
                    raise ValueError(f"frame {frame} rider {rider}: $82:A6E9 producer/register provenance differs")
            rows.append({
                "ordinal": ordinal, "frame": frame, "rider": rider,
                "inputs": {"position_x": x_capture["input_position"], "position_y": y_capture["input_position"],
                           "velocity_x": _s16(x_capture["velocity"]), "velocity_y": _s16(y_capture["velocity"]),
                           "surface": _s16(surface), "guard": guard, "unsupported_count": unsupported,
                           "direction_word": direction, "mode": mode, "track_mask": mask},
                "x": x, "y": y, "slope_tail": tail, "publications": actual,
            })
            residues[(rider, "x")] = int(x["remainder"])
            residues[(rider, "y")] = int(y["remainder"])
            ordinal += 1
    return rows, {"values": seed, "row_sha256": seed_row_sha256, "track_mask": mask}


def validate_call_order(access: dict) -> None:
    for frame in range(FIRST_CALL_FRAME, LAST_CALL_FRAME + 1):
        entries = _register_rows(access, 0x82A627, frame)
        if len(entries) != 2 or [row[3] for row in entries] != [0, 2]:
            raise ValueError(f"frame {frame}: player/opponent call order differs")


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_component_manifest(document: dict) -> None:
    required = {"schema_version", "kind", "scenario_id", "access_sha256", "wram_series_sha256",
                "routine", "frames", "calls", "seed", "rows_sha256", "slope_tail_counts",
                "description", "limits"}
    if set(document) != required or document.get("schema_version") != 1 or document.get("kind") != "zoom_zoo_position_reference":
        raise ValueError("position component manifest schema differs")
    if document["scenario_id"] not in COMPONENT_MANIFEST_SHA256 or document["frames"] != {"seed": 1649, "first": 1650, "last": 1700} or document["calls"] != 102:
        raise ValueError("position component source domain differs")
    if document["routine"] != {"bus": "82:A627-82:A6F7", "bytes": ROUTINE_BYTES, "sha256": ROUTINE_SHA256}:
        raise ValueError("position routine identity differs")
    if document["description"] != "Stateful four-residue position recurrence with captured position, velocity and contact inputs":
        raise ValueError("position component description differs")
    if document["limits"] != "Frames 1650-1700 only; no autonomous movement, wrap-crossing claim or native ZOOM ZOO support":
        raise ValueError("position component limits differ")
    expected_digest = COMPONENT_MANIFEST_SHA256.get(document["scenario_id"])
    if expected_digest is None or _canonical_digest(document) != expected_digest:
        raise ValueError("position component authored identity differs")


def verify(access_path: Path, manifest_path: Path, report_path: Path) -> dict:
    raw = access_path.read_bytes()
    access = json.loads(raw)
    manifest = json.loads(manifest_path.read_text())
    validate_component_manifest(manifest)
    if hashlib.sha256(raw).hexdigest() != manifest["access_sha256"]:
        raise ValueError("position access identity differs")
    if access.get("wram_series", {}).get("sha256") != manifest["wram_series_sha256"]:
        raise ValueError("position work-RAM series identity differs")
    rows, seed = position_calls(access_path, access)
    counts: dict[str, int] = {}
    for row in rows:
        name = str(row["slope_tail"]["reason"])
        counts[name] = counts.get(name, 0) + 1
    if seed != manifest["seed"]:
        raise ValueError("position seed identity differs")
    digest = _canonical_digest(rows)
    if digest != manifest["rows_sha256"] or counts != manifest["slope_tail_counts"]:
        raise ValueError("position row or branch identity differs")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_position_component",
        "status": "passed", "access_sha256": manifest["access_sha256"],
        "frames": manifest["frames"], "calls": len(rows), "seed": seed,
        "rows_sha256": digest, "slope_tail_counts": counts, "rows": rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _series_rows(access_path: Path, access: dict, frames: range) -> dict[int, bytes]:
    series = access["wram_series"]
    raw = (access_path.parent / series["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != series["sha256"] or len(raw) != series["bytes"]:
        raise ValueError("comparison work-RAM series identity differs")
    size = series["length"]
    indices = {frame: index for index, frame in enumerate(series["frames"])}
    if any(frame not in indices for frame in frames):
        raise ValueError("comparison work-RAM frame is missing")
    return {frame: raw[indices[frame] * size:(indices[frame] + 1) * size] for frame in frames}


def compare_inputs(primary_path: Path, variation_path: Path, report_path: Path) -> dict:
    primary_access = json.loads(primary_path.read_text())
    variation_access = json.loads(variation_path.read_text())
    primary, primary_seed = position_calls(primary_path, primary_access)
    variation, variation_seed = position_calls(variation_path, variation_access)
    if primary_seed != variation_seed:
        raise ValueError("variation does not share the authenticated end-1649 seed")
    if [(row["ordinal"], row["frame"], row["rider"]) for row in primary] != [(row["ordinal"], row["frame"], row["rider"]) for row in variation]:
        raise ValueError("variation call/rider sequence differs")
    different = [(left["frame"], left["rider"]) for left, right in zip(primary, variation, strict=True) if left != right]
    branch_different = [(left["frame"], left["rider"]) for left, right in zip(primary, variation, strict=True)
                        if left["slope_tail"]["reason"] != right["slope_tail"]["reason"]]
    frames = range(1649, 1701)
    primary_series = _series_rows(primary_path, primary_access, frames)
    variation_series = _series_rows(variation_path, variation_access, frames)
    controller_differences = [frame for frame in frames if primary_series[frame][0x0313] != variation_series[frame][0x0313]]
    if controller_differences != [1662] or not different or different[0] != (1662, 0):
        raise ValueError("preregistered first controller/component divergence differs")
    if any(rider != 0 for _frame, rider in different):
        raise ValueError("variation unexpectedly changes opponent calls through the cap")
    report = {
        "schema_version": 1, "kind": "zoom_zoo_position_input_comparison",
        "status": "passed", "first_controller_divergence": 1662,
        "controller_divergence_frames": controller_differences,
        "first_component_divergence": {"frame": different[0][0], "rider": different[0][1]},
        "first_branch_divergence": {"frame": branch_different[0][0], "rider": branch_different[0][1]},
        "branch_divergence_frames": sorted(set(frame for frame, _rider in branch_different)),
        "opponent_calls_exact_through_cap": True,
        "player_reconverged_through_1700": not any(frame == 1700 for frame, _rider in different),
        "primary_rows_sha256": _canonical_digest(primary),
        "variation_rows_sha256": _canonical_digest(variation),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def extract_routine(rom: Path, out: Path) -> None:
    raw = rom.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROM_SHA256:
        raise ValueError("source ROM identity differs")
    routine = raw[ROUTINE_FILE_OFFSET:ROUTINE_FILE_OFFSET + ROUTINE_BYTES]
    if len(routine) != ROUTINE_BYTES or hashlib.sha256(routine).hexdigest() != ROUTINE_SHA256:
        raise ValueError("position routine identity differs")
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty routine directory")
    out.mkdir(parents=True, exist_ok=True)
    (out / "position-integrator.bin").write_bytes(routine)
    (out / "routine.json").write_text(json.dumps({
        "schema_version": 1, "rom_sha256": ROM_SHA256,
        "file_offset": ROUTINE_FILE_OFFSET, "bus": "82:A627-82:A6F7",
        "bytes": ROUTINE_BYTES, "sha256": ROUTINE_SHA256,
    }, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--manifest", type=Path, required=True)
    capture_parser.add_argument("--out", type=Path, required=True)
    routine_parser = sub.add_parser("extract-routine")
    routine_parser.add_argument("--rom", type=Path, required=True)
    routine_parser.add_argument("--out", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--access", type=Path, required=True)
    verify_parser.add_argument("--manifest", type=Path, default=Path(PRIMARY_COMPONENT_MANIFEST))
    verify_parser.add_argument("--report", type=Path, required=True)
    compare_parser = sub.add_parser("compare-inputs")
    compare_parser.add_argument("--primary-access", type=Path, required=True)
    compare_parser.add_argument("--variation-access", type=Path, required=True)
    compare_parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "capture":
            return capture(args.manifest, args.out)
        if args.command == "extract-routine":
            extract_routine(args.rom, args.out)
            return 0
        if args.command == "compare-inputs":
            compare_inputs(args.primary_access, args.variation_access, args.report)
            return 0
        verify(args.access, args.manifest, args.report)
        return 0
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr)
        return 3
    except subprocess.TimeoutExpired as error:
        print(error, file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
