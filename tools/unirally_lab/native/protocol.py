"""Native movement process protocol, independent of reference execution."""
from __future__ import annotations
import hashlib
import re

from ..replay.manifest import inputs_at
from .compare import COLUMNS, NativeOutputError

HEADER = "unirally-movement-v1"
STATE_MAGIC = b"URMV0001"
# The same libretro button-bit order used by the recorded input adapter.
BUTTON_ORDER = ("b", "y", "select", "start", "up", "down", "left", "right", "a", "x", "l", "r")
DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)\Z")
HEX = re.compile(r"(?:[0-9a-f]{2})+\Z")


def input_text(manifest: dict, initial_frame: int, last_frame: int) -> str:
    """Only frame numbers and both input masks enter the native process."""
    lines = []
    for frame in range(initial_frame + 1, last_frame + 1):
        ports = inputs_at(manifest, frame)
        masks = [sum(1 << bit for bit, button in enumerate(BUTTON_ORDER)
                     if button in ports[str(port)]) for port in (0, 1)]
        lines.append(f"{frame} {masks[0]} {masks[1]}")
    return "\n".join(lines) + "\n"


def parse_output(output: str, initial_frame: int, last_frame: int) -> tuple[list, list[bytes]]:
    lines = output.splitlines()
    if not lines or lines[0] != HEADER:
        raise NativeOutputError("native runner protocol header is missing or unsupported")
    if len(lines) != last_frame - initial_frame + 2:
        raise NativeOutputError("native runner omitted initial/update rows or emitted extra rows")
    rows, states = [], []
    for index, line in enumerate(lines[1:]):
        tokens = line.split()
        if len(tokens) != len(COLUMNS) + 1:
            raise NativeOutputError("native row must contain frame, all projected fields and canonical state")
        if any(not DECIMAL.fullmatch(token) for token in tokens[:-1]):
            raise NativeOutputError("native projection contains a non-decimal integer")
        row = [int(token) for token in tokens[:-1]]
        if row[0] != initial_frame + index:
            raise NativeOutputError("native frames must be complete and contiguous")
        if not HEX.fullmatch(tokens[-1]):
            raise NativeOutputError("native state must be nonempty canonical lowercase byte hex")
        state = bytes.fromhex(tokens[-1])
        if len(state) <= 12 or state[:8] != STATE_MAGIC:
            raise NativeOutputError("native state serialization header is invalid")
        if int.from_bytes(state[8:12], "little") != row[0]:
            raise NativeOutputError("serialized native frame differs from projection frame")
        if states and len(state) != len(states[0]):
            raise NativeOutputError("native canonical state width changed during the run")
        rows.append(row)
        states.append(state)
    return rows, states


def state_digests(states: list[bytes]) -> dict:
    if not states:
        raise NativeOutputError("native state series is empty")
    return {"canonical_state_bytes": len(states[0]),
            "final_state_sha256": hashlib.sha256(states[-1]).hexdigest(),
            "state_series_sha256": hashlib.sha256(b"".join(states)).hexdigest()}
