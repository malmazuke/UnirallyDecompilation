"""``coverage`` subcommands (M1-01): capture instruction coverage of a replay
manifest in a fresh worker process, and derive the tracked code map.

Exit codes follow the repository convention: 0 success, 1 failed check
(digest mismatch, ring overflow, inconsistent totals), 2 missing
prerequisite (ROM, core, coverage file), 3 invalid input, 4 timeout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .. import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK
from .. import report as reportmod
from .. import rom as rommod
from ..reference import commands as refcmd
from ..replay import commands as replaycmd
from ..replay import manifest as mf
from . import derive, drain

ROOT = reportmod.repo_root()
DEFAULT_RING = 262144
DEFAULT_EXPECT = ROOT / "tests" / "manifests" / "rom" / "unirally-pal.json"


def _finish(rep: reportmod.Report, args: argparse.Namespace, status: int) -> int:
    return refcmd._finish(rep, args, status)


def _write_coverage(path: Path, doc: dict[str, Any]) -> str:
    path.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return refcmd.sha256_file(path)


# ------------------------------------------------------------- capture


def cmd_capture(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    root = Path(args.root).resolve()
    if args.timeout <= 0 or args.ring <= 0:
        rep.add_check("arguments", "failed", detail="--timeout and --ring must be positive")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    manifest = replaycmd._load_manifest(rep, Path(args.manifest), "replay")
    if manifest is None:
        return _finish(rep, args, EXIT_INVALID_INPUT)
    status = replaycmd._lock_checks(rep, root, manifest, "replay")
    if status != EXIT_OK:
        return _finish(rep, args, status)
    p = replaycmd._prepare(rep, args, manifest)
    if p.status != EXIT_OK:
        return _finish(rep, args, p.status)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    side = replaycmd._resolve_side(rep, root, out_dir, replaycmd.Side("capture", manifest))
    if side.status != EXIT_OK:
        return _finish(rep, args, side.status)

    samples_out = out_dir / "samples.json"
    coverage_out = out_dir / "coverage.json"
    cmd = refcmd._worker_command(p, side.script, samples_out, state_in=side.state_in) + ["--fields", str(side.fields)]
    cmd += ["--coverage-out", str(coverage_out), "--coverage-ring", str(args.ring)]
    for frame in args.frame_image or []:
        cmd += ["--frame-image", str(frame)]
    if args.frame_image:
        cmd += ["--frame-image-dir", str(out_dir / "frames")]
    samples, status = refcmd._run_worker(rep, "capture_run", p, cmd, samples_out, args.timeout, out_dir)
    if samples is None:
        if coverage_out.is_file():
            try:
                failed = json.loads(coverage_out.read_text(encoding="utf-8"))
                rep.add_check("ring_not_overflowed", "failed", detail=str(failed.get("failure")))
            except ValueError:
                pass
        return _finish(rep, args, status)
    refcmd._check_identity_and_region(rep, p, samples, argparse.Namespace(expect_region=args.expect_region))
    replaycmd._check_expected(rep, "capture", manifest, samples)

    try:
        cov = drain.validate_document(json.loads(coverage_out.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        rep.add_check("coverage_written", "failed", detail=f"{coverage_out}: {exc}")
        return _finish(rep, args, EXIT_FAILURE)
    # Identity the worker cannot know: scenario, manifest and the pinned core commit/patch.
    cov["scenario_id"] = manifest["scenario_id"]
    cov["manifest"] = {"path": str(Path(args.manifest)), "sha256": refcmd.sha256_file(Path(args.manifest))}
    cov["core"].update({"name": manifest["core"]["name"], "commit": p.core["commit"], "patch_sha256": p.core["patch_sha256"]})
    sha = _write_coverage(coverage_out, cov)
    rep.add_artifact("coverage", coverage_out)
    rep.add_check("coverage_written", "passed", detail=f"{coverage_out} sha256 {sha[:16]}; {len(cov['sites'])} sites, {len(cov['pairs'])} pairs")

    ins = cov["instructions"]
    ring_ok = cov.get("status") == "complete" and ins["max_frame_delta"] <= cov["ring_capacity"]
    rep.add_check("ring_not_overflowed", "passed" if ring_ok else "failed",
                  detail=f"largest frame delta {ins['max_frame_delta']} of ring {cov['ring_capacity']}; status {cov.get('status')}")
    traced = samples.get("trace", {}).get("instructions_executed")
    totals_ok = traced is not None and traced == ins["total"] == sum(ins["per_frame"]) + 0 and ins["initial_total"] == 0
    rep.add_check("instruction_total_consistent", "passed" if totals_ok else "failed",
                  detail=f"samples trace {traced}; coverage total {ins['total']} = sum of {len(ins['per_frame'])} per-frame deltas "
                         f"{sum(ins['per_frame'])}; ring total before frame {cov['frames']['start']}: {ins['initial_total']}; "
                         f"after final serialize {samples.get('trace', {}).get('instructions_executed_after_final_serialize')}")
    window = samples.get("trace", {}).get("window", [])
    tail = cov.get("tail_sites", [])
    window_sites = [[w["pc"], drain.mode_from_flags(w["p"], w["e"]), w["b"]] for w in window]
    suffix_ok = bool(window) and window_sites == tail[-len(window_sites):]
    rep.add_check("trace_window_is_suffix_of_capture", "passed" if suffix_ok else "failed",
                  detail=f"{len(window)}-entry samples window vs the capture's newest {len(tail)} sites")
    reset = None
    try:
        reset = rommod.load_manifest(Path(args.expect))["header"]["vectors"]["emu_reset"] if args.expect else None
    except (rommod.RomError, KeyError, TypeError):
        reset = None
    first = cov.get("first_site")
    if reset is not None and side.state_in is None:
        ok = first is not None and first[0] == reset and first[1] == 7  # bank $00, emulation mode with M=X=1
        rep.add_check("first_instruction_is_reset_vector", "passed" if ok else "failed",
                      detail=f"first site {derive.addr(first[0]) if first else None} mode {derive.mode_name(first[1]) if first else None}; "
                             f"header emulation reset vector ${reset:04X}")
    else:
        rep.add_check("first_instruction_is_reset_vector", "skipped", required=False,
                      detail="not a cold start or no ROM manifest to read the vector from")
    rep.data["coverage"] = {"path": str(coverage_out), "sha256": sha, "scenario_id": manifest["scenario_id"], "frames": cov["frames"],
                            "instructions": ins["total"], "max_frame_delta": ins["max_frame_delta"], "ring_capacity": cov["ring_capacity"],
                            "sites": len(cov["sites"]), "pairs": len(cov["pairs"]), "frame_images": samples.get("frame_images", [])}
    rep.data["samples"] = replaycmd._samples_summary(samples)
    return _finish(rep, args, replaycmd._status_from_checks(rep))


# ----------------------------------------------------------------- map


def regeneration_command(scenario_id: str) -> str:
    return (f"python3 tools/project.py coverage capture --manifest tests/manifests/replay/{scenario_id}.json --out artifacts/coverage/{scenario_id} "
            f"&& python3 tools/project.py coverage map --coverage artifacts/coverage/{scenario_id}/coverage.json "
            f"--out docs/map/{scenario_id}.map.json --summary docs/map/{scenario_id}.md")


def cmd_map(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    coverage_path = Path(args.coverage)
    if not coverage_path.is_file():
        rep.add_check("coverage_available", "missing", detail=f"{coverage_path} not found; run `coverage capture` first")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    try:
        cov = drain.validate_document(json.loads(coverage_path.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        rep.add_check("coverage_available", "failed", detail=f"{coverage_path}: {exc}")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    if cov.get("status") != "complete":
        rep.add_check("coverage_available", "failed", detail=f"coverage status {cov.get('status')!r}: {cov.get('failure')}")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    coverage_sha = refcmd.sha256_file(coverage_path)
    scenario = args.scenario or cov.get("scenario_id")
    if not scenario:
        rep.add_check("coverage_available", "failed", detail="coverage lacks a scenario_id; pass --scenario")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    rep.add_input("coverage", coverage_path, coverage_sha, scenario_id=scenario)
    rep.add_check("coverage_available", "passed", detail=f"{coverage_path} ({scenario}, {len(cov['sites'])} sites)")

    rom = Path(args.rom).expanduser() if args.rom else refcmd._default_rom_path()
    if rom is None or not rom.is_file():
        rep.add_check("rom_available", "missing", detail=f"{rom or 'no --rom and no local/rom-location.txt'}")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    try:
        observed = rommod.inspect_rom(rom)
    except rommod.RomMissingError as exc:
        rep.add_check("rom_available", "missing", detail=str(exc))
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    except rommod.RomError as exc:
        rep.add_check("rom_available", "failed", detail=str(exc))
        return _finish(rep, args, EXIT_INVALID_INPUT)
    rep.add_input("rom", rom, observed["file"]["sha256"], size=observed["file"]["size"])
    rep.add_check("rom_available", "passed", detail=str(rom))
    same = observed["file"]["sha256"] == cov["rom"]["sha256"] and not observed["copier_header"]["present"]
    rep.add_check("rom_matches_coverage", "passed" if same else "failed",
                  detail=f"ROM {observed['file']['sha256'][:16]}…, coverage {cov['rom']['sha256'][:16]}…; copier header {observed['copier_header']['present']}")
    if not same:
        return _finish(rep, args, EXIT_FAILURE)
    if observed["header_location"] != "lorom":
        rep.add_check("mapping_rule_applies", "failed", detail=f"header location {observed['header_location']}; only LoROM is implemented")
        return _finish(rep, args, EXIT_FAILURE)
    rep.add_check("mapping_rule_applies", "passed", detail=f"LoROM header at 0x{observed['header']['offset']:X}; {derive.MAPPING_RULE}")

    rom_bytes = rom.read_bytes()
    core = {k: cov["core"].get(k) for k in ("name", "commit", "patch_sha256", "sha256", "serialization_method")}
    core["library_sha256"] = core.pop("sha256")
    doc, detail = derive.build_map(cov, rom_bytes, scenario, core, coverage_sha, regeneration_command(scenario), observed["header"]["offset"])

    baseline = None
    if args.baseline:
        bpath = Path(args.baseline)
        if not bpath.is_file():
            rep.add_check("baseline_available", "missing", detail=f"{bpath} not found")
            return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
        try:
            baseline = json.loads(bpath.read_text(encoding="utf-8"))
            if baseline.get("kind") != "code_map" or baseline.get("rom", {}).get("sha256") != cov["rom"]["sha256"]:
                raise ValueError("not a code map of the same ROM")
        except (OSError, ValueError) as exc:
            rep.add_check("baseline_available", "failed", detail=f"{bpath}: {exc}")
            return _finish(rep, args, EXIT_INVALID_INPUT)
        rep.add_input("baseline_map", bpath, refcmd.sha256_file(bpath), scenario_id=baseline.get("scenario_id"))
        rep.add_check("baseline_available", "passed", detail=f"{bpath} ({baseline.get('scenario_id')})")
        doc["compared_to"] = derive.compare_maps(doc, baseline)

    t = doc["totals"]
    total_ok = t["executed_opcode_bytes"] + t["executed_operand_bytes"] + t["unclassified_bytes"] == t["rom_size"] == len(rom_bytes)
    rep.add_check("byte_classes_sum_to_rom_size", "passed" if total_ok else "failed",
                  detail=f"{t['executed_opcode_bytes']} + {t['executed_operand_bytes']} + {t['unclassified_bytes']} = {t['rom_size']}")
    reset = next(v for v in doc["vectors"] if v["name"] == "emu_reset")
    first = doc["coverage"]["first_site"]
    cold = cov.get("script", {}).get("path") is not None and cov["frames"]["start"] == 0
    if cold:
        ok = first is not None and first["address"] == reset["target"] and reset["executed"]
        rep.add_check("reset_vector_is_first_instruction", "passed" if ok else "failed",
                      detail=f"first executed {first}; emulation reset vector {reset['target']} executed {reset['count']} time(s)")
    else:
        rep.add_check("reset_vector_is_first_instruction", "skipped", required=False, detail="capture did not start at frame 0")
    nmi = next(v for v in doc["vectors"] if v["name"] == "native_nmi")
    frames_after = None if not nmi["executed"] else doc["coverage"]["frames"]["end"] - nmi["first_frame"] + 1
    nmi_ok = nmi["executed"] and nmi["count"] == frames_after
    rep.add_check("nmi_vector_once_per_frame", "passed" if nmi_ok else "failed", required=False,
                  detail=f"native NMI target {nmi['target']} executed {nmi['count']} times from frame {nmi['first_frame']} "
                         f"({frames_after} frames to the end)")
    unknown = t["unknown_edges"]
    rep.add_check("edges_classified", "passed", required=False,
                  detail=f"{t['edge_steps']} non-sequential steps, {t['sequential_steps']} sequential; {unknown} unknown edge(s) "
                         f"(from sites outside ROM: {sum(1 for e in doc['unknown_edges'] if e['from_region'] != 'rom')})")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(derive.dump_map(doc), encoding="utf-8")
    rep.add_artifact("map", out)
    if args.summary:
        summary = Path(args.summary)
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(derive.summary_markdown(doc, doc.get("compared_to")), encoding="utf-8")
        rep.add_artifact("summary", summary)
    if args.detail:
        detail_path = Path(args.detail)
        detail_path.parent.mkdir(parents=True, exist_ok=True)
        detail_path.write_text(json.dumps({"scenario_id": scenario, "coverage_sha256": coverage_sha, "rom_sha256": cov["rom"]["sha256"],
                                           "note": "ignored artifact: carries opcode bytes; regenerate with the map's regeneration_command plus --detail",
                                           "addresses": detail}, indent=None, separators=(",", ":")) + "\n", encoding="utf-8")
        rep.add_artifact("detail", detail_path)
    size_ok = out.stat().st_size <= (1 << 20)
    rep.add_check("map_written", "passed" if size_ok else "failed",
                  detail=f"{out} ({out.stat().st_size} bytes, limit 1 MiB); {len(doc['ranges'])} ranges, {len(doc['entry_points'])} entry points, "
                         f"{len(doc['static_references'])} static references")
    rep.data["totals"] = t
    rep.data["vectors"] = doc["vectors"]
    if baseline is not None:
        c = doc["compared_to"]
        rep.data["compared_to"] = {k: c[k] for k in c if k not in ("new_ranges", "new_entry_points")}
    return _finish(rep, args, replaycmd._status_from_checks(rep))


# --------------------------------------------------------------- parser


def register(sub: argparse._SubParsersAction) -> None:
    cov = sub.add_parser("coverage", help="instruction coverage capture and the observed code map (M1-01)")
    csub = cov.add_subparsers(dest="coverage_command", required=True)

    capture = csub.add_parser("capture", help="run a replay manifest in a fresh worker with the per-frame trace drain")
    capture.add_argument("--manifest", required=True, help="replay manifest JSON (see tests/manifests/replay/)")
    capture.add_argument("--out", required=True, help="directory for coverage.json, samples, scripts, logs and frame images")
    capture.add_argument("--ring", type=int, default=DEFAULT_RING, help=f"trace ring capacity (default {DEFAULT_RING}); a frame executing more instructions fails the run")
    capture.add_argument("--frame-image", type=int, action="append", help="write this frame's video output as PNG under <out>/frames (repeatable)")
    capture.add_argument("--rom", help="ROM file; defaults to the path in local/rom-location.txt")
    capture.add_argument("--expect", default=str(DEFAULT_EXPECT), help="ROM identity manifest whose reset vector the first instruction must match; '' disables")
    capture.add_argument("--expect-region", default="PAL", help="region the core must report (default PAL)")
    capture.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    capture.add_argument("--timeout", type=float, default=900, help="seconds for the worker process (default 900)")
    capture.add_argument("--report", help="write the JSON run report here")
    capture.add_argument("--task", help="task ID to record in the report")
    capture.set_defaults(func=cmd_capture)

    mp = csub.add_parser("map", help="derive the tracked code map from a coverage file and the ROM")
    mp.add_argument("--coverage", required=True, help="coverage.json written by `coverage capture`")
    mp.add_argument("--out", required=True, help="tracked map JSON to write (docs/map/<scenario>.map.json)")
    mp.add_argument("--summary", help="Markdown summary to write (docs/map/<scenario>.md)")
    mp.add_argument("--detail", help="per-address detail JSON (ignored artifact; carries opcode bytes)")
    mp.add_argument("--baseline", help="another scenario's map: list what this scenario executes that it does not")
    mp.add_argument("--scenario", help="scenario id (default: the coverage file's)")
    mp.add_argument("--rom", help="ROM file; defaults to the path in local/rom-location.txt")
    mp.add_argument("--report", help="write the JSON run report here")
    mp.add_argument("--task", help="task ID to record in the report")
    mp.set_defaults(func=cmd_map)
