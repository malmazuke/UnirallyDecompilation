"""Exact comparison of the frozen M2-01 projection with native output.

This module computes no gameplay and cannot establish that a producer is native.
The future runner must enforce that separately. Rows carry the initial sample
and every subsequent frame; a comparison window never excuses missing warmup
rows or omitted fields. Malformed reference/request data is distinct from a
malformed native producer, so the command layer can preserve exit codes 3/1.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..replay import manifest as replay
from .freeze_reference import DIAGNOSTIC, PROJECTION

COLUMNS = ["frame"] + [item["name"] for item in PROJECTION]


class ReferenceError(ValueError):
    """Invalid reference projection, identity binding, or comparison request."""


class NativeOutputError(ValueError):
    """The native producer did not supply the complete declared contract."""


def _integer(value: Any) -> bool:
    return type(value) is int  # JSON booleans are not integer state samples.


def _validate_rows(rows: Any, initial: int, last: int,
                   error: type[ValueError]) -> None:
    if not isinstance(rows, list) or len(rows) != last - initial + 1:
        raise error("rows must include the initial sample and every update")
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(COLUMNS):
            raise error(f"row {index} must contain all {len(COLUMNS)} columns")
        if not all(_integer(value) for value in row):
            raise error(f"row {index} contains a non-integer value")
        if row[0] != initial + index:
            raise error(f"row {index} has a missing, duplicate or unordered frame")
        for item, value in zip(PROJECTION, row[1:], strict=True):
            bits = item["length"] * 8
            minimum = -(1 << (bits - 1)) if item["signed"] else 0
            maximum = (1 << (bits - int(item["signed"]))) - 1
            if not minimum <= value <= maximum:
                raise error(f"frame {row[0]}: {item['name']} exceeds its declared integer width")


def validate_reference(reference: Any) -> dict:
    if not isinstance(reference, dict):
        raise ReferenceError("reference must be an object")
    if type(reference.get("schema_version")) is not int or reference["schema_version"] != 1:
        raise ReferenceError("unsupported reference schema")
    if reference.get("kind") != "frozen_reference_projection":
        raise ReferenceError("expected a frozen reference projection")
    if reference.get("projection") != PROJECTION or reference.get("columns") != COLUMNS:
        raise ReferenceError("required projection cannot be changed or shortened")
    if reference.get("diagnostic_only") != DIAGNOSTIC:
        raise ReferenceError("diagnostic exclusions differ from the frozen contract")
    initial, first, last = (reference.get(key) for key in
                            ("initial_frame", "first_update_frame", "last_frame"))
    if not all(_integer(value) for value in (initial, first, last)):
        raise ReferenceError("frame bounds must be integers")
    if initial < 0 or first != initial + 1 or last < first:
        raise ReferenceError("reference must have an initial sample followed by updates")
    _validate_rows(reference.get("rows"), initial, last, ReferenceError)
    return reference


def load_reference(expected_path: Path, replay_path: Path) -> tuple[dict, dict]:
    """Read and bind expectations to their exact frozen replay manifest bytes.

    Missing files intentionally propagate FileNotFoundError (command exit 2).
    The reference freeze/history establish observation provenance; this loader
    does not independently rerun the emulator or authenticate edited row data.
    """
    expected_bytes, replay_bytes = expected_path.read_bytes(), replay_path.read_bytes()
    try:
        reference = validate_reference(json.loads(expected_bytes))
        manifest = replay.validate_manifest(json.loads(replay_bytes))
        bindings = [
            (reference.get("replay_manifest_sha256"), hashlib.sha256(replay_bytes).hexdigest()),
            (reference.get("scenario_id"), manifest["scenario_id"]),
            (reference.get("rom_sha256"), manifest["rom"]["sha256"]),
            (reference.get("core"), manifest["core"]),
            (reference.get("reference_sample_digest"), manifest["expected"]["sample_digest"]),
            (reference.get("reference_final_state_sha256"), manifest["expected"]["final_state_sha256"]),
        ]
        if any(left != right for left, right in bindings):
            raise ReferenceError("expectations do not identify this exact replay manifest")
        if reference["last_frame"] != manifest["run"]["frames"] - 1:
            raise ReferenceError("reference does not cover the replay's final frame")
    except (ValueError, KeyError, TypeError) as error:
        raise ReferenceError(str(error)) from error
    return reference, manifest


def compare_rows(reference: dict, native_rows: Any, manifest: dict, *,
                 from_frame: int | None = None, to_frame: int | None = None) -> dict:
    """Compare an exact projection; use load_reference for file/identity binding.

    Native output must include the whole frozen frame domain even for a narrowed
    reporting window. A wrong seed is a producer/setup error, not an update
    comparison. A valid series with differing gameplay values returns a first
    divergence; callers map that result to exit 1, never a tolerance adjustment.
    """
    validate_reference(reference)
    initial, first, last = (reference[key] for key in
                            ("initial_frame", "first_update_frame", "last_frame"))
    start = first if from_frame is None else from_frame
    end = last if to_frame is None else to_frame
    if not _integer(start) or not _integer(end) or not first <= start <= end <= last:
        raise ReferenceError("comparison window must be nonempty and inside the update domain")
    _validate_rows(native_rows, initial, last, NativeOutputError)
    if native_rows[0] != reference["rows"][0]:
        raise NativeOutputError("native initial projection differs from the reference seed")
    divergence = None
    compared_frames = 0
    for frame in range(start, end + 1):
        compared_frames += 1
        index = frame - initial
        original, native = reference["rows"][index], native_rows[index]
        differing = [column for column in range(1, len(COLUMNS)) if original[column] != native[column]]
        if differing:
            def values(row: list[int]) -> dict[str, int]:
                return dict(zip(COLUMNS[1:], row[1:], strict=True))
            divergence = {
                "frame": frame,
                "differing_fields": [COLUMNS[column] for column in differing],
                "differences": [{"field": COLUMNS[column], "native": native[column],
                                 "reference": original[column]} for column in differing],
                "prior_sample": {"frame": frame - 1,
                                 "native": values(native_rows[index - 1]),
                                 "reference": values(reference["rows"][index - 1])},
                "inputs": {"previous": replay.inputs_at(manifest, frame - 1),
                           "current": replay.inputs_at(manifest, frame)},
            }
            break
    return {"identical": divergence is None, "first_divergence": divergence,
            "fields": COLUMNS[1:], "diagnostic_only": reference["diagnostic_only"],
            "window": {"from": start, "to": end}, "compared_frames": compared_frames,
            "validated_native_frames": len(native_rows)}
