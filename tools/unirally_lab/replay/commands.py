"""``replay`` subcommands: validate manifests, run one, compare fresh-process runs.

Every reference execution goes through ``reference/worker.py`` in its own
process (``reference.commands._run_worker``); the comparator never loads
the core in the process that compares. Exit codes follow the repository
convention: 0 identical, 1 divergence or failed check, 2 missing
prerequisite (ROM, built core, state, restore-check evidence), 3 invalid
manifest or arguments, 4 timeout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from .. import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK, EXIT_TIMEOUT
from .. import report as reportmod
from ..compare import samples as cmp
from ..reference import commands as refcmd
from ..reference import worker as workermod
from . import manifest as mf

ROOT = reportmod.repo_root()
DEFAULT_ROM_LOCATION = ROOT / "local" / "rom-location.txt"


def _status_from_checks(rep: reportmod.Report) -> int:
    return refcmd._status_from_checks(rep)


def _finish(rep: reportmod.Report, args: argparse.Namespace, status: int) -> int:
    return refcmd._finish(rep, args, status)


def _load_manifest(rep: reportmod.Report, path: Path, name: str) -> dict[str, Any] | None:
    try:
        manifest = mf.load_manifest(path)
    except mf.ManifestError as exc:
        rep.add_check(f"{name}_manifest_valid", "failed", detail=f"{path}: {exc}")
        return None
    rep.add_input(f"{name}_manifest", path, refcmd.sha256_file(path), scenario_id=manifest["scenario_id"])
    rep.add_check(f"{name}_manifest_valid", "passed", detail=f"{manifest['scenario_id']} ({path})")
    return manifest


# ----------------------------------------------------------- validation


def _lock_checks(rep: reportmod.Report, root: Path, manifest: dict[str, Any], name: str) -> int:
    """ROM-free identity checks against tracked files: emulator lock and ROM manifest."""
    status = EXIT_OK
    lock_path = root / manifest["core"]["lock"]
    try:
        lock = refcmd.load_lock(lock_path)
        entry = refcmd.core_entry(lock, manifest["core"]["name"])
    except refcmd.LockError as exc:
        rep.add_check(f"{name}_core_identity_matches_lock", "missing" if not lock_path.is_file() else "failed", detail=str(exc))
        return EXIT_MISSING_PREREQUISITE if not lock_path.is_file() else EXIT_FAILURE
    mismatches = [k for k, v in (("commit", entry["commit"]), ("patch_sha256", entry.get("patch_sha256"))) if manifest["core"][k] != v]
    rep.add_check(f"{name}_core_identity_matches_lock", "passed" if not mismatches else "failed",
                  detail=f"{manifest['core']['name']} {manifest['core']['commit'][:12]} patch {manifest['core']['patch_sha256'][:12]}"
                  + ("" if not mismatches else f"; lock differs in {mismatches}"))
    if mismatches:
        status = EXIT_FAILURE
    rom_manifest = root / manifest["rom"]["manifest"]
    if not rom_manifest.is_file():
        rep.add_check(f"{name}_rom_identity_matches_manifest", "missing", detail=f"{rom_manifest} not found")
        return EXIT_MISSING_PREREQUISITE
    try:
        expected = json.loads(rom_manifest.read_text(encoding="utf-8"))["file"]["sha256"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        rep.add_check(f"{name}_rom_identity_matches_manifest", "failed", detail=f"unreadable ROM manifest {rom_manifest}: {exc}")
        return EXIT_FAILURE
    ok = expected == manifest["rom"]["sha256"]
    rep.add_check(f"{name}_rom_identity_matches_manifest", "passed" if ok else "failed",
                  detail=f"manifest {manifest['rom']['sha256'][:16]}…, {rom_manifest.name} {expected[:16]}…")
    if not ok:
        status = EXIT_FAILURE
    if manifest["origin"]["kind"] == "state":
        script = root / manifest["origin"]["script"]
        if not script.is_file():
            rep.add_check(f"{name}_origin_script_matches", "missing", detail=f"{script} not found")
            return EXIT_MISSING_PREREQUISITE
        sha = refcmd.sha256_file(script)
        try:
            diffs = mf.script_equivalent(workermod.load_script(script), mf.derive_script(manifest))
        except workermod.ScriptError as exc:
            rep.add_check(f"{name}_origin_script_matches", "failed", detail=f"{script}: {exc}")
            return EXIT_FAILURE
        ok = sha == manifest["origin"]["script_sha256"] and not diffs
        rep.add_check(f"{name}_origin_script_matches", "passed" if ok else "failed",
                      detail=f"{script} sha256 {sha[:12]} (manifest {manifest['origin']['script_sha256'][:12]})"
                      + ("" if not diffs else f"; script differs from the manifest's run/inputs in {diffs}"))
        if not ok:
            status = EXIT_FAILURE
    return status


def cmd_validate(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    root = Path(args.root).resolve()
    manifest = _load_manifest(rep, Path(args.manifest), "replay")
    if manifest is None:
        return _finish(rep, args, EXIT_INVALID_INPUT)
    status = _lock_checks(rep, root, manifest, "replay")
    rep.data["derived_script"] = mf.derive_script(manifest)
    return _finish(rep, args, status if status != EXIT_OK else _status_from_checks(rep))


# ------------------------------------------------------------ execution


def _prepare(rep: reportmod.Report, args: argparse.Namespace, manifest: dict[str, Any]) -> refcmd.Prepared:
    """Reference prerequisites with lock, core, method and ROM identity taken from the manifest."""
    root = Path(args.root).resolve()
    ns = argparse.Namespace(root=str(root), timeout=args.timeout, lock=str(root / manifest["core"]["lock"]),
                            core=manifest["core"]["name"], rom=args.rom, expect=str(root / manifest["rom"]["manifest"]),
                            serialization_method=manifest["core"]["serialization_method"])
    p = refcmd._prepare(rep, ns)
    if p.status != EXIT_OK:
        return p
    core = p.core or {}
    mismatches = [k for k, v in (("commit", core.get("commit")), ("patch_sha256", core.get("patch_sha256"))) if manifest["core"][k] != v]
    rep.add_check("core_matches_manifest", "passed" if not mismatches else "failed",
                  detail=f"built core {str(core.get('commit'))[:12]} patch {str(core.get('patch_sha256'))[:12]}; manifest {manifest['core']['commit'][:12]} / {manifest['core']['patch_sha256'][:12]}")
    rom_ok = p.rom_sha256 == manifest["rom"]["sha256"]
    rep.add_check("rom_matches_manifest", "passed" if rom_ok else "failed",
                  detail=f"ROM {str(p.rom_sha256)[:16]}…, manifest {manifest['rom']['sha256'][:16]}…")
    if mismatches or not rom_ok:
        p.status = EXIT_FAILURE
    return p


class Side:
    """One manifest prepared for execution: its script file, optional state and fields file."""

    def __init__(self, label: str, manifest: dict[str, Any]) -> None:
        self.label = label
        self.manifest = manifest
        self.script: Path | None = None
        self.state_in: Path | None = None
        self.fields: Path | None = None
        self.status = EXIT_OK


def _resolve_side(rep: reportmod.Report, root: Path, art: Path, side: Side) -> Side:
    """Write the derived script and fields file; for a state origin, verify the state, its
    sidecar and the recorded restore-check evidence (D-0001) before it may be a reference origin."""
    m = side.manifest
    side.fields = art / f"{side.label}-fields.json"
    mf.write_json(side.fields, mf.range_fields(m))
    derived = mf.derive_script(m)
    if m["origin"]["kind"] == "cold_start":
        side.script = art / f"{side.label}-script.json"
        mf.write_json(side.script, derived)
        rep.add_artifact(f"{side.label}_script", side.script)
        rep.add_check(f"{side.label}_origin_available", "passed", detail=f"cold start; derived script {side.script.name}")
        return side
    origin = m["origin"]
    script = root / origin["script"]
    state = root / origin["path"]
    sidecar = state.with_suffix(state.suffix + ".json")
    report = root / origin["restore_check"]["report"]
    for label, path in (("script", script), ("state", state), ("state sidecar", sidecar)):
        if not path.is_file():
            rep.add_check(f"{side.label}_origin_available", "missing",
                          detail=f"{label} {path} not found; regenerate with `{m['regeneration_command']}`")
            side.status = EXIT_MISSING_PREREQUISITE
            return side
    script_sha, state_sha = refcmd.sha256_file(script), refcmd.sha256_file(state)
    try:
        diffs = mf.script_equivalent(workermod.load_script(script), derived)
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        rep.add_check(f"{side.label}_origin_available", "failed", detail=f"unreadable origin files: {exc}")
        side.status = EXIT_INVALID_INPUT
        return side
    problems = []
    if script_sha != origin["script_sha256"]:
        problems.append("script digest differs from the manifest")
    if diffs:
        problems.append(f"script differs from the manifest's run/inputs in {diffs}")
    if state_sha != origin["sha256"]:
        problems.append("state digest differs from the manifest")
    if not isinstance(meta, dict) or meta.get("sha256") != state_sha or meta.get("script_sha256") != script_sha:
        problems.append("sidecar does not describe this state and script")
    elif meta.get("after_frame") != origin["after_frame"] or meta.get("serialization_method") != m["core"]["serialization_method"]:
        problems.append(f"sidecar after_frame {meta.get('after_frame')} / method {meta.get('serialization_method')} differ from the manifest")
    if problems:
        rep.add_check(f"{side.label}_origin_available", "failed", detail="; ".join(problems))
        side.status = EXIT_FAILURE
        return side
    rep.add_input(f"{side.label}_state", state, state_sha, after_frame=origin["after_frame"])
    rep.add_check(f"{side.label}_origin_available", "passed", detail=f"state {state} after frame {origin['after_frame']}, script {script}")
    # Restore-check evidence: the report must belong to this script and save point and have
    # passed the three required checks; a state whose capture perturbed the run is refused.
    if not report.is_file():
        rep.add_check(f"{side.label}_origin_restore_check", "missing",
                      detail=f"{report} not found; run `reference restore-check --script {origin['script']} --save-after {origin['after_frame']} --report {origin['restore_check']['report']}`")
        side.status = EXIT_MISSING_PREREQUISITE
        return side
    try:
        rc = json.loads(report.read_text(encoding="utf-8"))
        outcomes = {c["name"]: c["outcome"] for c in rc["checks"]}
        rc_script = rc["inputs"]["script"]["sha256"]
        rc_state = next((a["sha256"] for a in rc["artifacts"] if a["kind"] == "state"), None)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        rep.add_check(f"{side.label}_origin_restore_check", "failed", detail=f"unreadable restore-check report {report}: {exc}")
        side.status = EXIT_FAILURE
        return side
    failed = [c for c in mf.RESTORE_CHECKS if outcomes.get(c) != "passed"]
    belongs = rc_script == script_sha and rc_state == state_sha
    ok = belongs and not failed
    rep.add_check(f"{side.label}_origin_restore_check", "passed" if ok else "failed",
                  detail=f"{report}: " + ("all three required checks passed for this script and state" if ok else
                                          ("report is for another script or state" if not belongs else f"checks not passed: {failed}")))
    rep.add_input(f"{side.label}_restore_check_report", report, refcmd.sha256_file(report))
    if not ok:
        side.status = EXIT_FAILURE
    side.script = script
    side.state_in = state
    return side


def _run_side(rep: reportmod.Report, p: refcmd.Prepared, side: Side, name: str, art: Path, timeout: float,
              stop_after: int | None = None, wram_dump: Path | None = None) -> tuple[dict[str, Any] | None, int]:
    samples_out = art / f"{name}-samples.json"
    cmd = refcmd._worker_command(p, side.script, samples_out, state_in=side.state_in) + ["--fields", str(side.fields)]
    if stop_after is not None:
        cmd += ["--stop-after-frame", str(stop_after)]
    if wram_dump is not None:
        cmd += ["--wram-dump-out", str(wram_dump)]
    return refcmd._run_worker(rep, name, p, cmd, samples_out, timeout, art)


def _artifacts_dir(args: argparse.Namespace, rep: reportmod.Report) -> Path:
    base = Path(args.artifacts) if args.artifacts else Path(args.root).resolve() / "artifacts" / "replay" / rep.data["run_id"]
    base.mkdir(parents=True, exist_ok=True)
    return base


def _check_expected(rep: reportmod.Report, name: str, manifest: dict[str, Any], samples: dict[str, Any]) -> None:
    expected = manifest.get("expected", {})
    for key, observed in (("sample_digest", samples["sample_digest"]), ("final_state_sha256", samples["final"]["state_sha256"])):
        if key in expected:
            ok = expected[key] == observed
            rep.add_check(f"{name}_{key}_matches_expected", "passed" if ok else "failed",
                          detail=f"observed {observed[:16]}…, manifest {expected[key][:16]}…")


def _samples_summary(s: dict[str, Any]) -> dict[str, Any]:
    out = refcmd._samples_summary(s)
    out["process"] = s.get("process", {}).get("pid")
    out["fields"] = [f["name"] for f in s.get("fields", [])]
    return out


def cmd_run(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    root = Path(args.root).resolve()
    if args.timeout <= 0:
        rep.add_check("arguments", "failed", detail="--timeout must be positive")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    manifest = _load_manifest(rep, Path(args.manifest), "replay")
    if manifest is None:
        return _finish(rep, args, EXIT_INVALID_INPUT)
    status = _lock_checks(rep, root, manifest, "replay")
    if status != EXIT_OK:
        return _finish(rep, args, status)
    p = _prepare(rep, args, manifest)
    if p.status != EXIT_OK:
        return _finish(rep, args, p.status)
    art = _artifacts_dir(args, rep)
    side = _resolve_side(rep, root, art, Side("run", manifest))
    if side.status != EXIT_OK:
        return _finish(rep, args, side.status)
    samples, status = _run_side(rep, p, side, "reference_run", art, args.timeout)
    if samples is None:
        return _finish(rep, args, status)
    refcmd._check_identity_and_region(rep, p, samples, argparse.Namespace(expect_region=args.expect_region))
    _check_expected(rep, "run", manifest, samples)
    rep.data["samples"] = _samples_summary(samples)
    rep.data["manifest"] = {"scenario_id": manifest["scenario_id"], "origin": manifest["origin"]["kind"], "fields": mf.field_names(manifest)}
    return _finish(rep, args, _status_from_checks(rep))


# ------------------------------------------------------------ comparison


def _localize(rep: reportmod.Report, p: refcmd.Prepared, left: Side, right: Side, frame: int, art: Path,
              timeout: float) -> dict[str, Any]:
    """Re-run both sides in fresh processes up to the divergence frame, dump work RAM
    and read the trace windows at the end of that frame."""
    dumps = {}
    outs = {}
    for side, name in ((left, "left"), (right, "right")):
        dump = art / f"localize-{name}-wram-after-{frame}.bin"
        samples, status = _run_side(rep, p, side, f"localize_{name}", art, timeout, stop_after=frame, wram_dump=dump)
        if samples is None:
            return {"after_frame": frame, "skipped": f"{name} re-run did not complete (exit {status})"}
        dumps[name] = dump.read_bytes()
        outs[name] = samples
    wram = cmp.diff_bytes(dumps["left"], dumps["right"])
    consistent = all(outs[n]["frames"][-1]["frame"] == frame and outs[n]["wram_dump"]["sha256"] == hashlib.sha256(dumps[n]).hexdigest() for n in outs)
    return {
        "after_frame": frame,
        "consistent_with_first_runs": consistent,
        "wram": wram,
        "wram_sha256": {n: outs[n]["frames"][-1]["wram_sha256"] for n in outs},
        "registers": {n: outs[n]["frames"][-1]["registers"] for n in outs},
        "differing_registers": cmp.diff_registers(outs["left"]["frames"][-1]["registers"], outs["right"]["frames"][-1]["registers"]),
        "trace": cmp.trace_windows(outs["left"], outs["right"]),
    }


def cmd_compare(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    root = Path(args.root).resolve()
    if args.timeout <= 0:
        rep.add_check("arguments", "failed", detail="--timeout must be positive")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    if args.runs < 2 or (args.against and args.runs != 2):
        rep.add_check("arguments", "failed", detail="--runs must be at least 2, and exactly 2 with --against")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    left_m = _load_manifest(rep, Path(args.manifest), "left")
    right_m = _load_manifest(rep, Path(args.against), "right") if args.against else left_m
    if left_m is None or right_m is None:
        return _finish(rep, args, EXIT_INVALID_INPUT)
    if args.against and (left_m["core"] != right_m["core"] or left_m["rom"] != right_m["rom"] or left_m["fields"] != right_m["fields"]):
        rep.add_check("manifests_comparable", "failed", detail="the two manifests must share core, rom and fields")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    status = _lock_checks(rep, root, left_m, "left")
    if status == EXIT_OK and args.against:
        status = _lock_checks(rep, root, right_m, "right")
    if status != EXIT_OK:
        return _finish(rep, args, status)
    p = _prepare(rep, args, left_m)
    if p.status != EXIT_OK:
        return _finish(rep, args, p.status)
    art = _artifacts_dir(args, rep)
    fields = mf.field_names(left_m)
    starts = {f["name"]: f["start"] for f in mf.range_fields(left_m)}

    if args.against:
        sides = [_resolve_side(rep, root, art, Side("left", left_m)), _resolve_side(rep, root, art, Side("right", right_m))]
    else:
        sides = [_resolve_side(rep, root, art, Side("left", left_m))]
    for s in sides:
        if s.status != EXIT_OK:
            return _finish(rep, args, s.status)
    plan = [(sides[0], "left"), (sides[1], "right")] if args.against else [(sides[0], f"run{i + 1}") for i in range(args.runs)]
    runs: list[tuple[str, dict[str, Any]]] = []
    for side, name in plan:
        samples, status = _run_side(rep, p, side, name, art, args.timeout)
        if samples is None:
            rep.add_check("fields_identical", "skipped", detail=f"{name} did not complete")
            return _finish(rep, args, status)
        refcmd._check_identity_and_region(rep, p, samples, argparse.Namespace(expect_region=args.expect_region))
        _check_expected(rep, name, side.manifest, samples)
        runs.append((name, samples))

    pids = [s.get("process", {}).get("pid") for _, s in runs]
    fresh = len(set(pids)) == len(pids) and None not in pids and os.getpid() not in pids
    rep.add_check("fresh_processes", "passed" if fresh else "failed",
                  detail=f"worker pids {pids}, comparator pid {os.getpid()}")

    comparisons = []
    divergence = None
    for name, samples in runs[1:]:
        base_name, base = runs[0]
        pair = f"{base_name}_vs_{name}"
        try:
            result = cmp.compare_samples(base, samples, fields, starts)
        except cmp.SamplesError as exc:
            rep.add_check(f"fields_identical", "failed", detail=f"{pair}: {exc}")
            return _finish(rep, args, EXIT_FAILURE)
        comparisons.append({"pair": pair, **result})
        sets_ok = not result["only_in_left"] and not result["only_in_right"] and result["compared"] > 0
        rep.add_check(f"frame_sets_identical" if len(runs) == 2 else f"frame_sets_identical_{pair}", "passed" if sets_ok else "failed",
                      detail=f"{pair}: {result['compared']} common frames" + ("" if sets_ok else f"; only left {result['only_in_left'][:8]}, only right {result['only_in_right'][:8]}"))
        fd = result["first_divergence"]
        rep.add_check(f"fields_identical" if len(runs) == 2 else f"fields_identical_{pair}", "passed" if fd is None else "failed",
                      detail=f"{pair}: fields {fields} identical on {result['compared']} frames" if fd is None else
                             f"{pair}: first divergence at frame {fd['frame']} in {fd['differing_fields']}")
        rep.add_check(f"final_state_identical" if len(runs) == 2 else f"final_state_identical_{pair}", "passed" if result["final_state_identical"] else "failed",
                      detail=f"{pair}: {result['final_state_sha256']['left'][:16]} / {result['final_state_sha256']['right'][:16]}")
        rep.add_check(f"av_identical" if len(runs) == 2 else f"av_identical_{pair}", "passed" if result["av_identical"] else "failed", required=False,
                      detail=f"{pair}: video/audio digests over common frames; informational after a restore")
        if fd is not None and divergence is None:
            left_side = plan[0][0]
            right_side = next(s for s, n in plan if n == name)
            divergence = {
                "pair": pair,
                "scenario": {"left": left_side.manifest["scenario_id"], "right": right_side.manifest["scenario_id"]},
                **fd,
                "inputs": {n: {"prior_frame": mf.inputs_at(s.manifest, fd["frame"] - 1) if fd["frame"] > 0 else None,
                               "at_frame": mf.inputs_at(s.manifest, fd["frame"])} for s, n in ((left_side, "left"), (right_side, "right"))},
                "trace_end_of_run": cmp.trace_windows(base, samples),
            }
            if args.localize:
                divergence["localization"] = _localize(rep, p, left_side, right_side, fd["frame"], art, args.timeout)
                loc = divergence["localization"]
                if "skipped" in loc:
                    rep.add_check("divergence_localized", "skipped", required=False, detail=loc["skipped"])
                else:
                    n = loc["wram"]["differing_bytes"]
                    rep.add_check("divergence_localized", "passed" if loc["consistent_with_first_runs"] else "failed", required=False,
                                  detail=f"after frame {fd['frame']}: {n} differing work RAM bytes, first {[d['offset'] for d in loc['wram']['first'][:8]]}; "
                                         f"{len(loc['differing_registers'])} differing registers; trace windows recorded")
            else:
                divergence["localization"] = {"after_frame": fd["frame"], "skipped": "--no-localize"}
    rep.data["comparisons"] = comparisons
    rep.data["samples"] = {name: _samples_summary(s) for name, s in runs}
    rep.data["manifests"] = {"left": left_m["scenario_id"], "right": right_m["scenario_id"], "fields": fields}
    if divergence is not None:
        out = art / "divergence.json"
        mf.write_json(out, divergence)
        rep.add_artifact("divergence_report", out)
        rep.data["divergence"] = divergence
    else:
        rep.data["divergence"] = None
    return _finish(rep, args, _status_from_checks(rep))


# --------------------------------------------------------------- parser


def _common(parser: argparse.ArgumentParser, timeout: float) -> None:
    parser.add_argument("--manifest", required=True, help="replay manifest JSON (see tests/manifests/replay/)")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=float, default=timeout, help=f"seconds per bounded step (default {timeout})")
    parser.add_argument("--report", help="write the JSON run report here")
    parser.add_argument("--task", help="task ID to record in the report")


def _run_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--rom", help="ROM file; defaults to the path in local/rom-location.txt")
    parser.add_argument("--expect-region", default="PAL", help="region the core must report (default PAL)")
    parser.add_argument("--artifacts", help="directory for scripts, samples, dumps and logs (default artifacts/replay/<run-id>/)")


def register(sub: argparse._SubParsersAction) -> None:
    replay = sub.add_parser("replay", help="replay manifests: validate, run in a fresh process, compare fresh-process runs")
    rsub = replay.add_subparsers(dest="replay_command", required=True)

    validate = rsub.add_parser("validate", help="check a manifest's schema and its identity against tracked files (ROM-free)")
    _common(validate, timeout=60)
    validate.set_defaults(func=cmd_validate)

    run = rsub.add_parser("run", help="execute one manifest in a fresh core process and record samples")
    _common(run, timeout=600)
    _run_common(run)
    run.set_defaults(func=cmd_run)

    compare = rsub.add_parser("compare", help="run a manifest in fresh processes (or two manifests) and report the first divergence")
    _common(compare, timeout=600)
    _run_common(compare)
    compare.add_argument("--against", help="second manifest to run and compare against the first (default: repeat the first)")
    compare.add_argument("--runs", type=int, default=2, help="fresh-process repetitions of the manifest without --against (default 2)")
    compare.add_argument("--no-localize", dest="localize", action="store_false",
                         help="do not re-run both sides to the divergence frame for a work RAM diff and trace windows")
    compare.set_defaults(func=cmd_compare)
