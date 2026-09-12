"""Verify the frozen M3-00 finish, coverage and decoded-content contract.

This module consumes ignored reference artifacts and emits a compact result.
It never executes the ROM and does not infer meanings from unlisted bytes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class AnalysisError(ValueError):
    """Invalid or inconsistent experiment input."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(str(path)) from exc
    except (OSError, ValueError) as exc:
        raise AnalysisError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AnalysisError(f"{path} must contain a JSON object")
    return value


def _rows(access: dict[str, Any]) -> list[dict[str, Any]]:
    fields = access.get("access_fields")
    packed = access.get("accesses")
    if not isinstance(fields, list) or not isinstance(packed, list):
        raise AnalysisError("access record lacks packed access rows")
    try:
        return [dict(zip(fields, row, strict=True)) for row in packed]
    except (TypeError, ValueError) as exc:
        raise AnalysisError(f"malformed access row: {exc}") from exc


def _write(rows: list[dict[str, Any]], address: int, pc: int) -> dict[str, Any]:
    matches = [r for r in rows if r.get("kind") == 1 and r.get("address") == address and r.get("pc") == pc]
    if len(matches) != 1:
        raise AnalysisError(f"expected one writer row for ${address:06X} at ${pc:06X}, found {len(matches)}")
    row = matches[0]
    return {k: row[k] for k in ("address", "pc", "width", "count", "first_frame", "last_frame", "values")}


def _first_divergence(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    lf, rf = left.get("frames"), right.get("frames")
    if not isinstance(lf, list) or not isinstance(rf, list) or len(lf) != len(rf):
        raise AnalysisError("sample frame lists are absent or unequal in length")
    for a, b in zip(lf, rf, strict=True):
        if a.get("frame") != b.get("frame"):
            raise AnalysisError("sample frame numbers are not aligned")
        different = []
        if a.get("wram_sha256") != b.get("wram_sha256"):
            different.append("wram_sha256")
        if a.get("registers") != b.get("registers"):
            different.append("registers")
        af, bf = a.get("fields", {}), b.get("fields", {})
        different.extend(sorted(k for k in set(af) | set(bf) if af.get(k) != bf.get(k)))
        if different:
            return {"frame": a["frame"], "fields": different}
    raise AnalysisError("the preregistered variation never diverges")


def analyze(contract: dict[str, Any], continuous_samples: dict[str, Any], variation_samples: dict[str, Any],
            continuous_access: dict[str, Any], variation_access: dict[str, Any], coverage: dict[str, Any],
            content: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, observed: Any, expected: Any) -> None:
        checks.append({"name": name, "outcome": "passed" if observed == expected else "failed",
                       "observed": observed, "expected": expected})

    identities = contract["samples"]
    check("continuous_sample_digest", continuous_samples.get("sample_digest"), identities["continuous"])
    check("variation_sample_digest", variation_samples.get("sample_digest"), identities["variation"])
    divergence = _first_divergence(continuous_samples, variation_samples)
    check("first_divergence_frame", divergence["frame"], contract["first_divergence_frame"])

    finish = contract["finish"]
    crows, vrows = _rows(continuous_access), _rows(variation_access)
    result_events: dict[str, Any] = {}
    for name, rows in (("continuous", crows), ("variation", vrows)):
        expected = finish[name]
        player = _write(rows, finish["player_address"], finish["flag_writer_pc"])
        opponent = _write(rows, finish["opponent_address"], finish["flag_writer_pc"])
        counter = _write(rows, finish["counter_address"], finish["counter_writer_pc"])
        result_events[name] = {"player": player, "opponent": opponent, "counter": counter}
        check(f"{name}_player_finish_frame", player["first_frame"], expected["player_frame"])
        check(f"{name}_opponent_finish_frame", opponent["first_frame"], expected["opponent_frame"])
        check(f"{name}_counter_range", [counter["first_frame"], counter["last_frame"], counter["count"]],
              [expected["counter_first"], expected["counter_last"], finish["counter_updates"]])
        check(f"{name}_finish_flag_values", [player["values"], opponent["values"]], [[1], [1]])

    compared = coverage.get("compared_to")
    if not isinstance(compared, dict):
        raise AnalysisError("coverage map lacks compared_to delta")
    coverage_delta = {
        "baseline_scenario": compared.get("baseline_scenario"),
        "bytes_only_here": compared.get("bytes_only_here"),
        "bytes_only_in_baseline": compared.get("bytes_only_in_baseline"),
        "new_ranges": len(compared.get("new_ranges", [])),
        "new_entry_points": len(compared.get("new_entry_points", [])),
    }
    for key, expected in contract["coverage_delta"].items():
        check(f"coverage_{key}", coverage_delta.get(key), expected)

    track = next((i for i in content.get("items", []) if i.get("id") == "track-data"), None)
    if not track:
        raise AnalysisError("content manifest lacks track-data")
    track_start = 0x7F0000
    track_end = track_start + track["expected"]["length"] - 1
    def track_summary(rows: list[dict[str, Any]], access: dict[str, Any]) -> dict[str, Any]:
        reads = [r for r in rows if r.get("kind") == 0 and isinstance(r.get("address"), int)
                 and 0x7F0000 <= r["address"] <= 0x7FFFFF]
        if not reads:
            raise AnalysisError("finish-window access record contains no bank $7F reads")
        outside = sum(r["count"] for r in reads
                      if r["address"] < track_start or r["address"] + r["width"] - 1 > track_end)
        return {"capture_start": access["frames"]["start"], "capture_end": access["frames"]["end"],
                "first_frame": min(r["first_frame"] for r in reads),
                "last_frame": max(r["last_frame"] for r in reads),
                "min": min(r["address"] for r in reads),
                "max": max(r["address"] + r["width"] - 1 for r in reads),
                "count": sum(r["count"] for r in reads), "outside_decoded_track": outside,
                "reader_pcs": sorted({r["pc"] for r in reads})}

    track_reads = track_summary(crows, continuous_access)
    variation_track_reads = track_summary(vrows, variation_access)
    check("continuous_track_reads_within_decoded_block", track_reads["outside_decoded_track"], 0)
    check("variation_track_reads_within_decoded_block", variation_track_reads["outside_decoded_track"], 0)
    check("track_suffix_begins_at_3000", track_reads["capture_start"], 3000)
    check("track_decoded_length", track["expected"]["length"], contract["decoded_track_length"])

    summary = provenance.get("summary")
    if not isinstance(summary, dict):
        raise AnalysisError("provenance record lacks summary")
    content_delta = {k: summary.get(k) for k in ("channel_transfers", "block_moves", "block_move_bytes",
                                                  "destinations_pairable", "destinations_paired")}
    status = "passed" if all(c["outcome"] == "passed" for c in checks) else "failed"
    return {"schema_version": 1, "kind": "finish_analysis", "status": status, "checks": checks,
            "first_divergence": divergence, "finish_events": result_events,
            "coverage_delta": coverage_delta, "decoded_track_suffix_reads": track_reads,
            "variation_finish_track_reads": variation_track_reads, "content_delta": content_delta}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("contract", "continuous-samples", "variation-samples", "continuous-access",
                 "variation-access", "coverage-map", "content-manifest", "provenance", "out"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = analyze(_load(args.contract), _load(args.continuous_samples), _load(args.variation_samples),
                         _load(args.continuous_access), _load(args.variation_access), _load(args.coverage_map),
                         _load(args.content_manifest), _load(args.provenance))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except FileNotFoundError as exc:
        print(f"missing prerequisite: {exc}", file=sys.stderr)
        return 2
    except (AnalysisError, KeyError, TypeError) as exc:
        print(f"invalid experiment input: {exc}", file=sys.stderr)
        return 3
    print(f"status={result['status']} checks={len(result['checks'])}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
