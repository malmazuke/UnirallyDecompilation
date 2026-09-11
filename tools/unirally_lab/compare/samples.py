"""Frame-by-frame comparison of two reference sample sets on declared fields.

Pure functions over samples files (reference samples schema 2) so that the
comparison logic is testable without a ROM. Field values are compared
exactly: a digest string, the CPU register dictionary, or the hex bytes of a
declared work RAM range. The first frame on which any declared field
differs is the divergence; the report around it carries the prior sample,
both sides' values, the differing bytes or registers, and the trace windows
that the samples recorded.
"""

from __future__ import annotations

from typing import Any

SUPPORTED_SAMPLES_SCHEMAS = (2,)
MAX_LISTED_DIFFERENCES = 64


class SamplesError(ValueError):
    pass


def check_samples(samples: Any, fields: list[str]) -> None:
    """Refuse samples that cannot carry the declared fields."""
    if not isinstance(samples, dict) or samples.get("schema_version") not in SUPPORTED_SAMPLES_SCHEMAS:
        raise SamplesError(f"samples schema_version must be one of {SUPPORTED_SAMPLES_SCHEMAS}")
    declared = {f["name"] for f in samples.get("fields", [])}
    for name in fields:
        if name in ("wram_sha256", "registers"):
            continue
        if name not in declared:
            raise SamplesError(f"samples do not carry declared field {name!r}; captured: {sorted(declared)}")
    if not isinstance(samples.get("frames"), list):
        raise SamplesError("samples lack a frames list")


def field_value(frame: dict[str, Any], name: str) -> Any:
    if name == "wram_sha256":
        return frame["wram_sha256"]
    if name == "registers":
        return frame["registers"]
    return frame["fields"][name]


def diff_hex(left: str, right: str, base: int = 0) -> dict[str, Any]:
    """Byte differences between two hex strings of a range starting at ``base``."""
    lb, rb = bytes.fromhex(left), bytes.fromhex(right)
    if len(lb) != len(rb):
        return {"differing_bytes": None, "length_left": len(lb), "length_right": len(rb), "first": []}
    offsets = [i for i in range(len(lb)) if lb[i] != rb[i]]
    return {"differing_bytes": len(offsets),
            "first": [{"offset": f"0x{base + i:05x}", "left": f"0x{lb[i]:02x}", "right": f"0x{rb[i]:02x}"} for i in offsets[:MAX_LISTED_DIFFERENCES]]}


def diff_bytes(left: bytes, right: bytes, base: int = 0) -> dict[str, Any]:
    return diff_hex(left.hex(), right.hex(), base)


def diff_registers(left: dict[str, int], right: dict[str, int]) -> list[dict[str, Any]]:
    return [{"register": k, "left": left.get(k), "right": right.get(k)} for k in sorted(set(left) | set(right)) if left.get(k) != right.get(k)]


def field_difference(name: str, kind_start: int | None, left: Any, right: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"field": name, "left": left, "right": right}
    if name == "registers":
        out["differing_registers"] = diff_registers(left, right)
    elif name != "wram_sha256":
        out.update(diff_hex(left, right, kind_start or 0))
    return out


def compare_samples(left: dict[str, Any], right: dict[str, Any], fields: list[str],
                    range_starts: dict[str, int] | None = None) -> dict[str, Any]:
    """Compare two sample sets on ``fields`` over their common frames, in frame order.

    Returns the frame sets on one side only, the number of frames compared,
    the first divergence (or None) with per-field differences, the sample
    before it on both sides, and whether the final serialized states and the
    video/audio digests agree.
    """
    check_samples(left, fields)
    check_samples(right, fields)
    starts = range_starts or {}
    fl = {f["frame"]: f for f in left["frames"]}
    fr = {f["frame"]: f for f in right["frames"]}
    common = sorted(set(fl) & set(fr))
    divergence = None
    prior = None
    for n in common:
        differing = [name for name in fields if field_value(fl[n], name) != field_value(fr[n], name)]
        if differing:
            divergence = {
                "frame": n,
                "differing_fields": differing,
                "differences": [field_difference(name, starts.get(name), field_value(fl[n], name), field_value(fr[n], name)) for name in differing],
                "prior_sample": None if prior is None else {
                    "frame": prior,
                    "left": {name: field_value(fl[prior], name) for name in fields},
                    "right": {name: field_value(fr[prior], name) for name in fields},
                },
            }
            break
        prior = n
    av_same = all(fl[n]["video"] == fr[n]["video"] and fl[n]["audio_sha256"] == fr[n]["audio_sha256"] for n in common)
    final_same = left["final"]["state_sha256"] == right["final"]["state_sha256"]
    return {
        "fields": list(fields),
        "compared": len(common),
        "only_in_left": sorted(set(fl) - set(fr)),
        "only_in_right": sorted(set(fr) - set(fl)),
        "first_divergence": divergence,
        "final_state_identical": final_same,
        "av_identical": av_same,
        "sample_digests": {"left": left["sample_digest"], "right": right["sample_digest"]},
        "final_state_sha256": {"left": left["final"]["state_sha256"], "right": right["final"]["state_sha256"]},
        "identical": divergence is None and final_same and len(common) > 0 and not (set(fl) ^ set(fr)),
    }


def trace_windows(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """The instruction trace windows both samples recorded (end of their runs)."""
    def one(s: dict[str, Any]) -> dict[str, Any]:
        t = s.get("trace") or {}
        return {"end_frame": s.get("end_frame"), "instructions_executed": t.get("instructions_executed"), "window": t.get("window", [])}
    return {"left": one(left), "right": one(right)}
