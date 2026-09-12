"""Validation for the additive M3-01 full-race native contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..replay import manifest as replay
from . import compare, protocol
from .freeze_reference import DIAGNOSTIC, PROJECTION

STATE_MAGIC_V2 = b"URMV0002"
STATE_MAGIC_V3 = b"URMV0003"
STATE_V1_BYTES = 333
STATE_V2_BYTES = 369
STATE_V3_BYTES = 371


def load_reference(expected_path: Path, replay_path: Path,
                   contract_path: Path) -> tuple[dict, dict, dict, dict]:
    expected_bytes = expected_path.read_bytes()
    replay_bytes = replay_path.read_bytes()
    contract_bytes = contract_path.read_bytes()
    expected = json.loads(expected_bytes)
    manifest = replay.validate_manifest(json.loads(replay_bytes))
    contract = json.loads(contract_bytes)
    if (expected.get("schema_version"), expected.get("kind")) != (1, "frozen_full_race_movement_projection"):
        raise compare.ReferenceError("unsupported full-race reference")
    if expected.get("columns") != compare.COLUMNS or expected.get("projection") != PROJECTION or expected.get("diagnostic_only") != DIAGNOSTIC:
        raise compare.ReferenceError("full-race projection metadata differs")
    initial, last_gameplay, last = (expected.get(k) for k in
                                    ("initial_frame", "last_gameplay_frame", "last_frame"))
    compare._validate_rows(expected.get("rows"), initial, last_gameplay, compare.ReferenceError)
    if expected.get("first_update_frame") != initial + 1 or last < last_gameplay:
        raise compare.ReferenceError("invalid full-race frame bounds")
    bindings = ((expected.get("replay_manifest_sha256"), hashlib.sha256(replay_bytes).hexdigest()),
                (expected.get("finish_contract_sha256"), hashlib.sha256(contract_bytes).hexdigest()),
                (expected.get("scenario_id"), manifest["scenario_id"]),
                (expected.get("rom_sha256"), manifest["rom"]["sha256"]))
    if any(left != right for left, right in bindings):
        raise compare.ReferenceError("full-race identity binding differs")
    if (contract.get("schema_version"), contract.get("kind")) != (1, "frozen_full_race_finish_reference"):
        raise compare.ReferenceError("unsupported finish contract")
    case = next((item for item in contract.get("cases", [])
                 if item.get("name") == expected.get("case_name")), None)
    if (case is None or Path(case.get("replay", "")).name != replay_path.name
            or case.get("sample_digest") != expected.get("reference_sample_digest")):
        raise compare.ReferenceError("finish case does not bind the replay")
    return expected, manifest, contract, case


def parse_output(output: str, initial: int, last: int) -> tuple[list, list[bytes]]:
    lines = output.splitlines()
    if not lines or lines[0] != protocol.HEADER or len(lines) != last - initial + 2:
        raise compare.NativeOutputError("full-race native output is incomplete")
    rows, states, saw_v2 = [], [], False
    for index, line in enumerate(lines[1:]):
        tokens = line.split()
        if len(tokens) != len(compare.COLUMNS) + 1 or any(not protocol.DECIMAL.fullmatch(x) for x in tokens[:-1]) or not protocol.HEX.fullmatch(tokens[-1]):
            raise compare.NativeOutputError("malformed full-race native row")
        row, state = [int(x) for x in tokens[:-1]], bytes.fromhex(tokens[-1])
        if row[0] != initial + index or int.from_bytes(state[8:12], "little") != row[0]:
            raise compare.NativeOutputError("full-race native frames are not contiguous")
        if state[:8] == protocol.STATE_MAGIC and len(state) == STATE_V1_BYTES and not saw_v2:
            pass
        elif state[:8] == STATE_MAGIC_V2 and len(state) == STATE_V2_BYTES:
            saw_v2 = True
        elif state[:8] == STATE_MAGIC_V3 and len(state) == STATE_V3_BYTES:
            saw_v2 = True
        else:
            raise compare.NativeOutputError("invalid or regressing movement-state revision")
        rows.append(row); states.append(state)
    return rows, states


def finish_fields(state: bytes) -> dict:
    if state[:8] == protocol.STATE_MAGIC:
        return {"finished": [False, False], "times": [0, 0],
                "digits": [[0] * 5, [0] * 5], "countdowns": [0, 0],
                "delay": 0, "loading": 0, "phase": 0, "outcome": 0}
    u16 = lambda offset: int.from_bytes(state[offset:offset + 2], "little")
    return {"finished": [bool(state[333]), bool(state[334])],
            "times": [u16(335), u16(337)],
            "digits": [[u16(339 + 2 * (r * 5 + d)) for d in range(5)] for r in range(2)],
            "countdowns": [u16(359), u16(361)], "delay": u16(363),
            "loading": u16(365), "phase": state[367], "outcome": state[368]}


def state_digests(states: list[bytes]) -> dict:
    revisions = {state[:8].decode(): len(state) for state in states}
    return {"canonical_state_revisions": revisions,
            "final_state_sha256": hashlib.sha256(states[-1]).hexdigest(),
            "state_series_sha256": hashlib.sha256(b"".join(states)).hexdigest()}


def validate(rows: list, states: list[bytes], expected: dict, case: dict,
             manifest: dict) -> dict:
    gameplay_count = expected["last_gameplay_frame"] - expected["initial_frame"] + 1
    compare._validate_rows(rows[:gameplay_count], expected["initial_frame"],
                           expected["last_gameplay_frame"], compare.NativeOutputError)
    # Identity and shape were validated while loading the case; compare the
    # frozen tested-domain rows directly and retain the first useful divergence.
    differences = []
    for index, (frozen, native) in enumerate(
            zip(expected["rows"], rows[:gameplay_count], strict=True)):
        if frozen != native:
            prior = None if index == 0 else {
                "frame": frozen[0] - 1,
                "frozen": dict(zip(compare.COLUMNS[1:], expected["rows"][index - 1][1:], strict=True)),
                "native": dict(zip(compare.COLUMNS[1:], rows[index - 1][1:], strict=True)),
            }
            differences.append({"frame": frozen[0], "differences": [
                {"field": compare.COLUMNS[i], "frozen": frozen[i], "native": native[i]}
                for i in range(1, len(frozen)) if frozen[i] != native[i]],
                "prior_sample": prior,
                "inputs": {"previous": replay.inputs_at(manifest, frozen[0] - 1),
                           "current": replay.inputs_at(manifest, frozen[0])}})
            break
    comparison = {"identical": not differences, "compared_frames": gameplay_count}
    if differences: comparison["first_divergence"] = differences[0]
    player, opponent = case["player"], case["opponent"]
    outcome_value = 1 if case["outcome"] == "player_won" else 2
    for row, state in zip(rows, states, strict=True):
        frame, fields = row[0], finish_fields(state)
        for rider, item in enumerate((player, opponent)):
            crossed = frame >= item["finish_frame"]
            if fields["finished"][rider] != crossed:
                raise compare.NativeOutputError(f"finish flag differs at frame {frame}")
            if crossed and (fields["times"][rider] != item["finish_time_centiseconds"] or fields["digits"][rider] != item["digits"]):
                raise compare.NativeOutputError(f"stored finish time differs at frame {frame}")
        if frame < player["finish_frame"]:
            wanted = (0, 0, 0)
        elif frame < case["delay"]["first_frame"]:
            wanted = (1, 0, outcome_value)
        elif frame <= case["delay"]["last_frame"]:
            wanted = (1, frame - case["delay"]["first_frame"] + 1, outcome_value)
        elif frame < case["first_stable_result_frame"]:
            wanted = (2, 240, outcome_value)
        else:
            wanted = (3, 240, outcome_value)
        if (fields["phase"], fields["delay"], fields["outcome"]) != wanted:
            raise compare.NativeOutputError(f"finish dispatcher differs at frame {frame}")
        expected_loading = 0 if frame < case["first_result_transition_frame"] else min(
            frame - case["first_result_transition_frame"] + 1,
            case["first_stable_result_frame"] - case["first_result_transition_frame"] + 1)
        if fields["loading"] != expected_loading:
            raise compare.NativeOutputError(f"result transition counter differs at frame {frame}")
    return comparison
