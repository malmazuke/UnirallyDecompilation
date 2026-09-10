"""``reference`` subcommands: build the pinned core, run scripts, verify determinism."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .. import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK, EXIT_TIMEOUT
from .. import report as reportmod
from .. import rom as rommod
from ..procs import RunResult, run_bounded

ROOT = reportmod.repo_root()
DEFAULT_LOCK = ROOT / "tools" / "locks" / "emulators.json"
DEFAULT_EXPECT = ROOT / "tests" / "manifests" / "rom" / "unirally-pal.json"
DEFAULT_ROM_LOCATION = ROOT / "local" / "rom-location.txt"
WORKER = Path(__file__).resolve().parent / "worker.py"
LOCK_SCHEMA_VERSION = 1
# The tracked patch is compared by digest against the checkout's own diff, so
# the diff text must not depend on user git configuration. Regenerate patches
# with exactly: git <DIFF_OPTIONS> diff <DIFF_FLAGS> -- . ':!<outputs>'
DIFF_OPTIONS = ["-c", "diff.noprefix=false", "-c", "diff.mnemonicPrefix=false", "-c", "diff.renames=false",
                "-c", "core.abbrev=40", "-c", "diff.algorithm=myers", "-c", "diff.suppressBlankEmpty=false"]
DIFF_FLAGS = ["--no-color", "--no-ext-diff", "--full-index", "--src-prefix=a/", "--dst-prefix=b/", "--no-renames"]
CORE_MANIFEST_SCHEMA_VERSION = 1


class LockError(Exception):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_lock(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LockError(f"emulator lock not found: {path}")
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise LockError(f"unreadable lock {path}: {exc}") from exc
    if not isinstance(lock, dict) or lock.get("lock_schema_version") != LOCK_SCHEMA_VERSION or not isinstance(lock.get("cores"), dict):
        raise LockError(f"unsupported emulator lock schema in {path}")
    return lock


def core_entry(lock: dict[str, Any], name: str) -> dict[str, Any]:
    entry = lock["cores"].get(name)
    if not isinstance(entry, dict):
        raise LockError(f"core {name!r} is not in the lock; known: {sorted(lock['cores'])}")
    for key in ("repository", "commit", "checkout_dir", "build"):
        if key not in entry:
            raise LockError(f"core {name!r}: lock entry lacks {key!r}")
    return entry


def checkout_dir(root: Path, lock: dict[str, Any], entry: dict[str, Any]) -> Path:
    return root / lock["install_dir"] / entry["checkout_dir"]


def core_manifest_path(root: Path, lock: dict[str, Any], entry: dict[str, Any]) -> Path:
    return checkout_dir(root, lock, entry) / "lab-core.json"


def load_core_manifest(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    if not isinstance(data, dict) or data.get("schema_version") != CORE_MANIFEST_SCHEMA_VERSION:
        return None
    return data


def _status_from_checks(rep: reportmod.Report) -> int:
    outcomes = {c["outcome"] for c in rep.required_failures()}
    if "timeout" in outcomes:
        return EXIT_TIMEOUT
    if "missing" in outcomes:
        return EXIT_MISSING_PREREQUISITE
    if outcomes:
        return EXIT_FAILURE
    return EXIT_OK


def _finish(rep: reportmod.Report, args: argparse.Namespace, status: int) -> int:
    rep.finish("passed" if status == EXIT_OK else "failed")
    rep.write(Path(args.report) if getattr(args, "report", None) else None)
    reportmod.print_summary(rep)
    return status


def _git(args: list[str], cwd: Path, timeout: float = 60) -> RunResult:
    return run_bounded(["git", *args], timeout=timeout, cwd=cwd)


def _platform_library(entry: dict[str, Any]) -> str | None:
    key = platform.system().lower()
    return entry["build"].get("library", {}).get(key)


# ----------------------------------------------------------------- build


def _current_patch_digest(checkout: Path, build_outputs: list[str]) -> tuple[str | None, str | None]:
    """SHA-256 of the checkout's working-tree diff including new files, or an error.

    Build outputs named by the lock are excluded; the patch file was produced
    the same way (``git add -N -A`` then ``git diff``).
    """
    pathspec = [".", *(f":!{p}" for p in build_outputs)]
    add = _git(["add", "-N", "-A", "--", *pathspec], checkout)
    if add.outcome != "passed":
        return None, add.tail(300)
    diff = _git([*DIFF_OPTIONS, "diff", *DIFF_FLAGS, "--", *pathspec], checkout, timeout=120)
    _git(["reset", "-q"], checkout)
    if diff.outcome != "passed":
        return None, diff.tail(300)
    return hashlib.sha256(diff.stdout.encode()).hexdigest(), None


def cmd_build(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    root = Path(args.root).resolve()
    if args.timeout <= 0:
        print("--timeout must be positive", file=sys.stderr)
        return EXIT_INVALID_INPUT
    try:
        lock = load_lock(Path(args.lock))
        entry = core_entry(lock, args.core)
    except LockError as exc:
        rep.add_check("emulator_lock", "failed", detail=str(exc))
        return _finish(rep, args, EXIT_INVALID_INPUT)
    rep.add_input("emulator_lock", Path(args.lock), sha256_file(Path(args.lock)))
    rep.add_check("emulator_lock", "passed", detail=f"{args.core} @ {entry['commit'][:12]}")
    if args.core != "bsnes":
        rep.add_check("core_supported", "failed", detail=f"no adapter is implemented for {args.core!r}; only bsnes can be built here")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    if not shutil.which("git"):
        rep.add_check("git", "missing", detail="git is required to obtain the pinned source")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)

    checkout = checkout_dir(root, lock, entry)
    if not checkout.is_dir():
        if args.no_network:
            rep.add_check("checkout_pinned", "missing", detail=f"{checkout} absent and --no-network given")
            return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
        checkout.parent.mkdir(parents=True, exist_ok=True)
        clone = run_bounded(["git", "clone", "--quiet", entry["repository"], str(checkout)], timeout=args.timeout)
        if clone.outcome != "passed":
            rep.add_check("checkout_pinned", clone.outcome, detail=f"git clone failed: {clone.tail(300)}")
            return _finish(rep, args, _status_from_checks(rep))
        co = _git(["checkout", "--quiet", "--detach", entry["commit"]], checkout, timeout=120)
        if co.outcome != "passed":
            rep.add_check("checkout_pinned", "failed", detail=f"git checkout failed: {co.tail(300)}")
            return _finish(rep, args, EXIT_FAILURE)
    head = _git(["rev-parse", "HEAD"], checkout)
    tree = _git(["rev-parse", "HEAD^{tree}"], checkout)
    if head.outcome != "passed" or head.stdout.strip() != entry["commit"]:
        rep.add_check("checkout_pinned", "failed",
                      detail=f"{checkout} is at {head.stdout.strip() or head.tail(100)!r}, lock pins {entry['commit']}; check it out manually")
        return _finish(rep, args, EXIT_FAILURE)
    if entry.get("tree") and tree.stdout.strip() != entry["tree"]:
        rep.add_check("checkout_pinned", "failed", detail=f"tree {tree.stdout.strip()} != locked {entry['tree']}")
        return _finish(rep, args, EXIT_FAILURE)
    rep.add_check("checkout_pinned", "passed", detail=f"{checkout} @ {entry['commit']}")

    patch_path = root / entry["patch"]
    if not patch_path.is_file():
        rep.add_check("patch_applied", "missing", detail=f"patch file {patch_path} not found")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    patch_sha = sha256_file(patch_path)
    if patch_sha != entry.get("patch_sha256"):
        rep.add_check("patch_applied", "failed", detail=f"patch digest {patch_sha} != locked {entry.get('patch_sha256')}")
        return _finish(rep, args, EXIT_FAILURE)
    rep.add_input("core_patch", patch_path, patch_sha)
    build_outputs = entry["build"].get("outputs", [])
    current, err = _current_patch_digest(checkout, build_outputs)
    if err:
        rep.add_check("patch_applied", "failed", detail=err)
        return _finish(rep, args, EXIT_FAILURE)
    if current == hashlib.sha256(b"").hexdigest():
        apply = _git(["apply", str(patch_path)], checkout, timeout=120)
        if apply.outcome != "passed":
            rep.add_check("patch_applied", "failed", detail=f"git apply failed: {apply.tail(300)}")
            return _finish(rep, args, EXIT_FAILURE)
        current, err = _current_patch_digest(checkout, build_outputs)
    if current != patch_sha:
        rep.add_check("patch_applied", "failed",
                      detail=f"working tree diff digest {current} != patch {patch_sha}; the checkout has other modifications")
        return _finish(rep, args, EXIT_FAILURE)
    rep.add_check("patch_applied", "passed", detail=f"{patch_path.name} {patch_sha[:12]}")

    build = entry["build"]
    started = time.monotonic()
    result = run_bounded(build["command"], timeout=args.timeout, cwd=checkout)
    rep.add_check("core_build", result.outcome, detail=f"{' '.join(build['command'])}: {round(result.elapsed, 1)}s"
                  + ("" if result.outcome == "passed" else f"; {result.tail(600)}"))
    if result.outcome != "passed":
        return _finish(rep, args, _status_from_checks(rep))
    rel = _platform_library(entry)
    library = checkout / rel if rel else None
    if library is None or not library.is_file():
        rep.add_check("core_library", "missing", detail=f"no library for platform {platform.system().lower()} ({rel})")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    probe = run_bounded([sys.executable, str(WORKER), "--core", str(library), "--probe"], timeout=60)
    try:
        probe_data = json.loads(probe.stdout or "{}")
    except ValueError:
        probe_data = {}
    if probe.outcome != "passed" or "api_version" not in probe_data:
        rep.add_check("core_exports", "failed", detail=probe_data.get("error") or probe.tail(300))
        return _finish(rep, args, EXIT_FAILURE)
    rep.add_check("core_exports", "passed", detail=f"laboratory API {probe_data['api_version']}")

    compiler = run_bounded(["c++", "--version"], timeout=20)
    manifest = {
        "schema_version": CORE_MANIFEST_SCHEMA_VERSION,
        "core": args.core,
        "repository": entry["repository"],
        "commit": entry["commit"],
        "tree": tree.stdout.strip(),
        "patch": entry["patch"],
        "patch_sha256": patch_sha,
        "library": str(library),
        "library_sha256": probe_data["library_sha256"],
        "api_version": probe_data["api_version"],
        "build_command": build["command"],
        "build_seconds": round(time.monotonic() - started, 1),
        "compiler": (compiler.stdout.strip().splitlines() or [""])[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lock_sha256": rep.data["inputs"]["emulator_lock"]["sha256"],
    }
    out = core_manifest_path(root, lock, entry)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rep.add_artifact("core_manifest", out)
    rep.add_artifact("core_library", library)
    rep.data["core"] = manifest
    return _finish(rep, args, _status_from_checks(rep))


# ------------------------------------------------------------ run helpers


def _default_rom_path() -> Path | None:
    if DEFAULT_ROM_LOCATION.is_file():
        text = DEFAULT_ROM_LOCATION.read_text(encoding="utf-8").strip()
        if text:
            return Path(text).expanduser()
    return None


class Prepared:
    def __init__(self) -> None:
        self.core: dict[str, Any] | None = None
        self.rom: Path | None = None
        self.rom_sha256: str | None = None
        self.expected_sha256: str | None = None
        self.serialization_method = "Strict"
        self.status = EXIT_OK


def _prepare(rep: reportmod.Report, args: argparse.Namespace) -> Prepared:
    """Shared checks: lock, built core, ROM presence and identity."""
    p = Prepared()
    p.serialization_method = getattr(args, "serialization_method", "Strict")
    root = Path(args.root).resolve()
    if args.timeout <= 0:
        rep.add_check("arguments", "failed", detail="--timeout must be positive")
        p.status = EXIT_INVALID_INPUT
        return p
    try:
        lock = load_lock(Path(args.lock))
        entry = core_entry(lock, args.core)
    except LockError as exc:
        rep.add_check("emulator_lock", "failed", detail=str(exc))
        p.status = EXIT_INVALID_INPUT
        return p
    rep.add_input("emulator_lock", Path(args.lock), sha256_file(Path(args.lock)))
    manifest = load_core_manifest(core_manifest_path(root, lock, entry))
    if manifest is None or not Path(manifest["library"]).is_file():
        rep.add_check("core_available", "missing", detail=f"run `python3 tools/project.py reference build --core {args.core}` first")
        p.status = EXIT_MISSING_PREREQUISITE
        return p
    library_sha = sha256_file(Path(manifest["library"]))
    if library_sha != manifest["library_sha256"] or manifest["commit"] != entry["commit"] or manifest["patch_sha256"] != entry.get("patch_sha256"):
        rep.add_check("core_available", "failed", detail="built core does not match the lock (rebuild with `reference build`)")
        p.status = EXIT_FAILURE
        return p
    rep.add_check("core_available", "passed", detail=f"{manifest['core']} {manifest['commit'][:12]} library {library_sha[:12]}")
    rep.add_input("core_library", Path(manifest["library"]), library_sha, commit=manifest["commit"], patch_sha256=manifest["patch_sha256"])
    rep.data["core"] = manifest
    p.core = manifest

    rom = Path(args.rom).expanduser() if args.rom else _default_rom_path()
    if rom is None or not rom.is_file():
        rep.add_check("rom_available", "missing", detail=f"{rom or 'no --rom and no local/rom-location.txt'}")
        p.status = EXIT_MISSING_PREREQUISITE
        return p
    try:
        observed = rommod.inspect_rom(rom)
    except rommod.RomMissingError as exc:
        rep.add_check("rom_available", "missing", detail=str(exc))
        p.status = EXIT_MISSING_PREREQUISITE
        return p
    except rommod.RomError as exc:
        rep.add_check("rom_available", "failed", detail=str(exc))
        p.status = EXIT_INVALID_INPUT
        return p
    p.rom = rom
    p.rom_sha256 = observed["file"]["sha256"]
    rep.add_input("rom", rom, p.rom_sha256, size=observed["file"]["size"])
    rep.add_check("rom_available", "passed", detail=str(rom))
    if args.expect:
        try:
            expected = rommod.load_manifest(Path(args.expect))
        except rommod.RomMissingError as exc:
            rep.add_check("expected_manifest", "missing", detail=str(exc))
            p.status = EXIT_MISSING_PREREQUISITE
            return p
        except rommod.RomError as exc:
            rep.add_check("expected_manifest", "failed", detail=str(exc))
            p.status = EXIT_INVALID_INPUT
            return p
        fields = rommod.compare_identity(observed, expected)
        mismatches = [f for f in fields if not f["matches"]]
        rep.add_check("rom_identity_matches_expected", "passed" if not mismatches else "failed",
                      detail=f"{len(fields) - len(mismatches)}/{len(fields)} identity fields match {args.expect}")
        p.expected_sha256 = expected["file"]["sha256"]
        if mismatches:
            p.status = EXIT_FAILURE
            return p
    return p


def _worker_command(p: Prepared, script: Path, samples_out: Path, state_in: Path | None = None,
                    save_after: int | None = None, state_out: Path | None = None, sample_from: int | None = None) -> list[str]:
    cmd = [sys.executable, str(WORKER), "--core", p.core["library"], "--rom", str(p.rom), "--script", str(script),
           "--samples-out", str(samples_out), "--system-dir", str(samples_out.parent / "core-system"),
           "--serialization-method", p.serialization_method]
    if sample_from is not None:
        cmd += ["--sample-from-frame", str(sample_from)]
    if state_in is not None:
        cmd += ["--state-in", str(state_in)]
    if save_after is not None:
        cmd += ["--save-after", str(save_after), "--state-out", str(state_out)]
    return cmd


def _run_worker(rep: reportmod.Report, name: str, p: Prepared, cmd: list[str], samples_out: Path, timeout: float,
                log_dir: Path) -> tuple[dict[str, Any] | None, int]:
    """Run the worker as a bounded fresh process; returns (samples, exit status)."""
    result = run_bounded(cmd, timeout=timeout)
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"{name}.log").write_text(f"$ {' '.join(cmd)}\n--- stdout\n{result.stdout}\n--- stderr\n{result.stderr}\n", encoding="utf-8")
    outcome = result.outcome
    status = EXIT_OK
    if result.timed_out:
        status = EXIT_TIMEOUT
    elif result.missing:
        status = EXIT_MISSING_PREREQUISITE
    elif result.returncode == EXIT_MISSING_PREREQUISITE:
        outcome, status = "missing", EXIT_MISSING_PREREQUISITE
    elif result.returncode == EXIT_INVALID_INPUT:
        outcome, status = "failed", EXIT_INVALID_INPUT
    elif result.returncode != 0:
        outcome, status = "failed", EXIT_FAILURE
    samples = None
    if status == EXIT_OK:
        try:
            samples = json.loads(samples_out.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            outcome, status, samples = "failed", EXIT_FAILURE, None
            result.stderr += f"\nsamples unreadable: {exc}"
    detail = f"{round(result.elapsed, 3)}s"
    if samples:
        detail += f"; frames {samples['start_frame']}..{samples['end_frame']}; sample digest {samples['sample_digest'][:16]}"
        rep.add_artifact(f"{name}_samples", samples_out)
    elif result.timed_out:
        detail += f"; killed after --timeout {timeout}s"
    else:
        detail += f"; exit {result.returncode}; {result.tail(400)}"
    rep.add_check(name, outcome, detail=detail)
    return samples, status


def _artifacts_dir(args: argparse.Namespace, rep: reportmod.Report) -> Path:
    base = Path(args.artifacts) if args.artifacts else Path(args.root).resolve() / "artifacts" / "reference" / rep.data["run_id"]
    base.mkdir(parents=True, exist_ok=True)
    return base


def _check_identity_and_region(rep: reportmod.Report, p: Prepared, samples: dict[str, Any], args: argparse.Namespace) -> None:
    loaded = samples["rom"]["sha256"]
    if p.expected_sha256:
        rep.add_check("rom_identity_in_adapter", "passed" if loaded == p.expected_sha256 else "failed",
                      detail=f"adapter loaded {loaded[:16]}…, manifest {p.expected_sha256[:16]}…")
    region = samples["rom"].get("region")
    rep.add_check("region_reported", "passed" if region == args.expect_region else "failed",
                  detail=f"core reports {region}, expected {args.expect_region}")


def sample_key(f: dict[str, Any]) -> tuple[str, str]:
    """The comparison domain for restore checks: work RAM and CPU registers."""
    return f["wram_sha256"], json.dumps(f["registers"], sort_keys=True)


def compare_runs(x: dict[str, Any], y: dict[str, Any], from_frame: int = 0) -> dict[str, Any]:
    """Compare two sample sets frame by frame from ``from_frame`` on.

    Runs may have sampled different frame sets (a saving run forces samples
    around the save frame), so only frames present in both are compared; the
    frame sets are reported so a caller can require them to line up.
    """
    fx = {f["frame"]: f for f in x["frames"] if f["frame"] >= from_frame}
    fy = {f["frame"]: f for f in y["frames"] if f["frame"] >= from_frame}
    common = sorted(set(fx) & set(fy))
    first_diff = next((n for n in common if sample_key(fx[n]) != sample_key(fy[n])), None)
    av_same = all(fx[n]["video"] == fy[n]["video"] and fx[n]["audio_sha256"] == fy[n]["audio_sha256"] for n in common)
    return {"compared": len(common), "only_in_x": sorted(set(fx) - set(fy)), "only_in_y": sorted(set(fy) - set(fx)),
            "first_differing_frame": first_diff, "av_identical": av_same,
            "final_state_identical": x["final"]["state_sha256"] == y["final"]["state_sha256"],
            "identical": first_diff is None and len(common) > 0 and x["final"]["state_sha256"] == y["final"]["state_sha256"]}


def perturbation_verdict(ab: dict[str, Any]) -> bool:
    """A vs B in a restore check: both runs sample every frame from the save
    point on, so their frame sets must be equal and every frame identical."""
    return bool(ab["identical"]) and not ab["only_in_x"] and not ab["only_in_y"]


def continuation_verdict(bc: dict[str, Any], c: dict[str, Any]) -> bool:
    """B vs C: every frame after the resume frame present in both, identical, same final state."""
    return (bool(bc["identical"]) and not bc["only_in_x"] and not bc["only_in_y"]
            and bool(c["frames"]) and c["frames"][0]["frame"] == c["start_frame"])


def _samples_summary(s: dict[str, Any]) -> dict[str, Any]:
    return {"sample_digest": s["sample_digest"], "av_digest": s["av_digest"], "start_frame": s["start_frame"],
            "end_frame": s["end_frame"], "final": s["final"], "elapsed_seconds": s["elapsed_seconds"],
            "instructions_executed": s.get("trace", {}).get("instructions_executed")}


# ------------------------------------------------------------------- run


def cmd_run(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    p = _prepare(rep, args)
    if p.status != EXIT_OK:
        return _finish(rep, args, p.status)
    script = Path(args.script)
    if not script.is_file():
        rep.add_check("script_available", "missing", detail=f"{script} not found")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    rep.add_input("script", script, sha256_file(script))
    if (args.save_after is None) != (args.state_out is None):
        rep.add_check("arguments", "failed", detail="--save-after and --state-out must be given together")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    art = _artifacts_dir(args, rep)
    samples_out = Path(args.samples_out) if args.samples_out else art / "samples.json"
    cmd = _worker_command(p, script, samples_out, Path(args.state_in) if args.state_in else None,
                          args.save_after, Path(args.state_out) if args.state_out else None)
    samples, status = _run_worker(rep, "reference_run", p, cmd, samples_out, args.timeout, art)
    if samples:
        _check_identity_and_region(rep, p, samples, args)
        rep.data["samples"] = _samples_summary(samples)
        if "state_out" in samples:
            rep.add_artifact("state", Path(samples["state_out"]["path"]))
    return _finish(rep, args, status if status != EXIT_OK else _status_from_checks(rep))


# ---------------------------------------------------------------- verify


def cmd_verify(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    if args.runs < 2:
        rep.add_check("arguments", "failed", detail="--runs must be at least 2")
        return _finish(rep, args, EXIT_INVALID_INPUT)
    p = _prepare(rep, args)
    if p.status != EXIT_OK:
        return _finish(rep, args, p.status)
    script = Path(args.script)
    if not script.is_file():
        rep.add_check("script_available", "missing", detail=f"{script} not found")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    rep.add_input("script", script, sha256_file(script))
    art = _artifacts_dir(args, rep)
    runs: list[dict[str, Any]] = []
    for i in range(args.runs):
        samples_out = art / f"run{i + 1}-samples.json"
        samples, status = _run_worker(rep, f"cold_start_run_{i + 1}", p, _worker_command(p, script, samples_out), samples_out, args.timeout, art)
        if samples is None:
            rep.add_check("cold_start_identical", "skipped", detail=f"run {i + 1} did not complete")
            return _finish(rep, args, status)
        runs.append(samples)
    _check_identity_and_region(rep, p, runs[0], args)
    digests = {s["sample_digest"] for s in runs}
    av = {s["av_digest"] for s in runs}
    finals = {s["final"]["state_sha256"] for s in runs}
    first_diff = None
    for frames in zip(*(s["frames"] for s in runs)):
        keys = {(f["wram_sha256"], json.dumps(f["registers"], sort_keys=True)) for f in frames}
        if len(keys) > 1:
            first_diff = frames[0]["frame"]
            break
    identical = len(digests) == 1 and len(finals) == 1
    rep.add_check("cold_start_identical", "passed" if identical else "failed",
                  detail=f"{args.runs} fresh processes; memory+register sample digests {sorted(d[:16] for d in digests)}; final state digests {sorted(f[:16] for f in finals)}"
                  + ("" if first_diff is None else f"; first differing frame {first_diff}"))
    rep.add_check("cold_start_av_identical", "passed" if len(av) == 1 else "failed", required=False,
                  detail=f"video/audio digests {sorted(d[:16] for d in av)}")
    rep.data["samples"] = [_samples_summary(s) for s in runs]
    return _finish(rep, args, _status_from_checks(rep))


# --------------------------------------------------------- restore-check


def cmd_restore_check(args: argparse.Namespace) -> int:
    rep = reportmod.Report(sys.argv, task_id=args.task)
    p = _prepare(rep, args)
    if p.status != EXIT_OK:
        return _finish(rep, args, p.status)
    script = Path(args.script)
    if not script.is_file():
        rep.add_check("script_available", "missing", detail=f"{script} not found")
        return _finish(rep, args, EXIT_MISSING_PREREQUISITE)
    rep.add_input("script", script, sha256_file(script))
    art = _artifacts_dir(args, rep)
    state = art / f"state-after-{args.save_after}.bst"
    a_out, b_out, c_out = art / "uninterrupted-samples.json", art / "save-and-continue-samples.json", art / "restore-and-continue-samples.json"
    # All three runs sample every frame from the save point on, so the
    # comparisons below have the adapter's full (per-frame) resolution
    # whatever the script's sample_every says (review 4).
    dense = args.save_after
    a, status = _run_worker(rep, "uninterrupted_run", p, _worker_command(p, script, a_out, sample_from=dense), a_out, args.timeout, art)
    if a is None:
        return _finish(rep, args, status)
    b, status = _run_worker(rep, "save_and_continue_run", p, _worker_command(p, script, b_out, save_after=args.save_after, state_out=state, sample_from=dense), b_out, args.timeout, art)
    if b is None:
        return _finish(rep, args, status)
    rep.add_artifact("state", state)
    c, status = _run_worker(rep, "restore_and_continue_run", p, _worker_command(p, script, c_out, state_in=state, sample_from=dense), c_out, args.timeout, art)
    if c is None:
        return _finish(rep, args, status)
    _check_identity_and_region(rep, p, a, args)

    ab = compare_runs(a, b)
    ab_ok = perturbation_verdict(ab)
    rep.add_check("save_does_not_perturb", "passed" if ab_ok else "failed",
                  detail=f"uninterrupted vs save-and-continue: {ab['compared']} frames compared on WRAM+registers, every frame from {args.save_after} on"
                  + ("" if ab["first_differing_frame"] is None else f"; first differing frame {ab['first_differing_frame']}")
                  + f"; final states {a['final']['state_sha256'][:16]} / {b['final']['state_sha256'][:16]}"
                  + ("" if not (ab["only_in_x"] or ab["only_in_y"]) else f"; frame sets differ {ab['only_in_x']} / {ab['only_in_y']}"))
    restored_ok = bool(c.get("state_in", {}).get("matches_post_serialize"))
    rep.add_check("restore_matches_saved_state", "passed" if restored_ok else "failed",
                  detail=f"WRAM and registers right after restore equal the saving run's post-serialize sample after frame {args.save_after}: {restored_ok}")
    # B vs C: both runs force a sample at the resume frame and the last frame;
    # every frame C sampled must exist in B and match.
    bc = compare_runs(b, c, from_frame=c["start_frame"])
    bc_ok = continuation_verdict(bc, c)
    rep.add_check("restore_continuation_identical", "passed" if bc_ok else "failed",
                  detail=f"frames {c['start_frame']}..{c['end_frame']} after restore in a fresh process: {bc['compared']} samples compared on WRAM+registers"
                  + ("" if bc["first_differing_frame"] is None else f"; first differing frame {bc['first_differing_frame']}")
                  + ("" if not (bc["only_in_x"] or bc["only_in_y"]) else f"; frame sets differ {bc['only_in_x']} / {bc['only_in_y']}")
                  + f"; final states {b['final']['state_sha256'][:16]} / {c['final']['state_sha256'][:16]}")
    rep.add_check("restore_av_identical", "passed" if bc["av_identical"] else "failed", required=False,
                  detail="video/audio output after a restore is not part of the serialized state; informational only")
    rep.data["comparisons"] = {"uninterrupted_vs_save": ab, "save_vs_restore": bc}
    rep.data["samples"] = {"uninterrupted": _samples_summary(a), "save_and_continue": _samples_summary(b), "restore_and_continue": _samples_summary(c)}
    return _finish(rep, args, _status_from_checks(rep))


# --------------------------------------------------------------- parser


def _common(parser: argparse.ArgumentParser, timeout: float) -> None:
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--lock", default=str(DEFAULT_LOCK), help="emulator lock file")
    parser.add_argument("--core", default="bsnes", help="core name from the lock (default bsnes)")
    parser.add_argument("--timeout", type=float, default=timeout, help=f"seconds per bounded step (default {timeout})")
    parser.add_argument("--report", help="write the JSON run report here")
    parser.add_argument("--task", help="task ID to record in the report")


def _run_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--script", required=True, help="run script JSON (see tests/manifests/reference/)")
    parser.add_argument("--rom", help="ROM file; defaults to the path in local/rom-location.txt")
    parser.add_argument("--expect", default=str(DEFAULT_EXPECT), help="ROM identity manifest; '' disables the check")
    parser.add_argument("--expect-region", default="PAL", help="region the core must report (default PAL)")
    parser.add_argument("--artifacts", help="directory for samples, states and logs (default artifacts/reference/<run-id>/)")
    parser.add_argument("--serialization-method", default="Strict", choices=("Fast", "Strict"),
                        help="bsnes save-state synchronization method (default Strict)")


def register(sub: argparse._SubParsersAction) -> None:
    ref = sub.add_parser("reference", help="pinned reference emulator: build, run scripts, verify determinism")
    refsub = ref.add_subparsers(dest="reference_command", required=True)

    build = refsub.add_parser("build", help="obtain the pinned source, apply the tracked patch and build the core")
    _common(build, timeout=1800)
    build.add_argument("--no-network", action="store_true", help="fail as missing instead of cloning")
    build.set_defaults(func=cmd_build)

    run = refsub.add_parser("run", help="execute one script in a fresh core process and record samples")
    _common(run, timeout=600)
    _run_common(run)
    run.add_argument("--samples-out", help="samples JSON path (default inside --artifacts)")
    run.add_argument("--state-in", help="serialized state to restore before running (with its .json sidecar)")
    run.add_argument("--save-after", type=int, help="serialize after this frame")
    run.add_argument("--state-out", help="where to write the serialized state")
    run.set_defaults(func=cmd_run)

    verify = refsub.add_parser("verify", help="repeat a script in fresh processes and compare sampled outputs")
    _common(verify, timeout=600)
    _run_common(verify)
    verify.add_argument("--runs", type=int, default=3)
    verify.set_defaults(func=cmd_verify)

    rc = refsub.add_parser("restore-check", help="save after a frame, restore in a fresh process and compare the continuation")
    _common(rc, timeout=600)
    _run_common(rc)
    rc.add_argument("--save-after", type=int, required=True)
    rc.set_defaults(func=cmd_restore_check)
