"""Run the semantic native process twice and compare identity-bound projections.

Preparation is separate: this command neither loads a ROM nor invokes the
reference emulator. Only a canonical seed, static content and controller inputs
are passed to the native executable. Authored command tests stub that process;
actual gameplay agreement is recorded separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from .. import report as reports
from ..procs import run_bounded
from . import compare, finish, protocol

ROOT = reports.repo_root()
STATIC_SIZES = {
    "track-data.bin": 33815, "collision-poses.bin": 32768,
    "collision-templates.bin": 17249, "progress-transitions.bin": 80,
    "tile-tables.bin": 640, "tile-flags.bin": 20,
    "speed-masks.bin": 9, "speed-decrements.bin": 18,
    "pose-slopes.bin": 128, "displacement-table.bin": 512,
    "idle-pose-table.bin": 64,
    "rotation-reward.bin": 2, "rotation-class.bin": 1,
}


def relative_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise compare.ReferenceError("input paths must be nonempty repository-relative paths")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise compare.ReferenceError("input path escapes repository")
    return path


def checked_file(root: Path, binding: object, rep: reports.Report, name: str) -> Path:
    if not isinstance(binding, dict):
        raise compare.ReferenceError(f"{name} requires path and sha256")
    digest = binding.get("sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise compare.ReferenceError(f"{name} requires a lowercase SHA-256")
    path = relative_path(root, binding.get("path"))
    actual = reports.file_sha256(path)
    if actual != digest:
        raise compare.ReferenceError(f"{name} SHA-256 differs from binding")
    rep.add_input(name, path, actual)
    return path


def load_case(root: Path, case_path: Path, rep: reports.Report) -> tuple:
    case = json.loads(case_path.read_text())
    if not isinstance(case, dict) or type(case.get("schema_version")) is not int or case["schema_version"] != 1 or case.get("kind") != "native_movement_case":
        raise compare.ReferenceError("unsupported native case schema/kind")
    rep.add_input("native_case", case_path, reports.file_sha256(case_path))
    replay_path = checked_file(root, case.get("replay"), rep, "replay")
    expected_path = checked_file(root, case.get("expected"), rep, "expected")
    reference, replay = compare.load_reference(expected_path, replay_path)
    runtime_path = checked_file(root, case.get("runtime"), rep, "runtime")
    runtime = json.loads(runtime_path.read_text())
    if not isinstance(runtime, dict) or type(runtime.get("schema_version")) is not int or runtime["schema_version"] != 1:
        raise compare.ReferenceError("unsupported runtime schema")
    if runtime.get("rom_sha256") != reference["rom_sha256"]:
        raise compare.ReferenceError("runtime and reference ROM identities differ")
    seed = checked_file(root, runtime.get("seed"), rep, "seed")
    frame = runtime["seed"].get("frame")
    if type(frame) is not int or frame != reference["initial_frame"]:
        raise compare.ReferenceError("seed frame differs from initial reference frame")
    seed_bytes = seed.read_bytes()
    if len(seed_bytes) <= 12 or seed_bytes[:8] != protocol.STATE_MAGIC or int.from_bytes(seed_bytes[8:12], "little") != frame:
        raise compare.ReferenceError("seed serialization header/frame invalid")
    content = relative_path(root, runtime.get("content_dir"))
    files = runtime.get("files")
    if not isinstance(files, list) or len(files) != len(STATIC_SIZES):
        raise compare.ReferenceError("runtime must bind the complete static content inventory")
    seen = set()
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise compare.ReferenceError("invalid static content entry")
        name = entry["name"]
        if name not in STATIC_SIZES or name in seen or type(entry.get("size")) is not int or entry["size"] != STATIC_SIZES[name]:
            raise compare.ReferenceError("duplicate, unknown or wrong-sized static content entry")
        seen.add(name)
        path = checked_file(root, {"path": str((content / name).relative_to(root)), "sha256": entry.get("sha256")}, rep, f"content:{name}")
        if path.stat().st_size != entry["size"]:
            raise compare.ReferenceError(f"static file size differs: {name}")
    # Extra files must not become unbound runtime inputs.
    if {p.name for p in content.iterdir()} != seen:
        raise compare.ReferenceError("content directory contains unbound entries")
    return reference, replay, seed, seed_bytes, content


def load_finish_case(root: Path, case_path: Path, rep: reports.Report) -> tuple:
    case = json.loads(case_path.read_text())
    if (case.get("schema_version"), case.get("kind")) != (1, "native_full_race_case"):
        raise compare.ReferenceError("unsupported native full-race case")
    rep.add_input("native_case", case_path, reports.file_sha256(case_path))
    replay_path = checked_file(root, case.get("replay"), rep, "replay")
    expected_path = checked_file(root, case.get("expected"), rep, "expected")
    contract_path = checked_file(root, case.get("finish_contract"), rep, "finish_contract")
    reference, replay, contract, finish_case = finish.load_reference(
        expected_path, replay_path, contract_path)
    runtime_path = checked_file(root, case.get("runtime"), rep, "runtime")
    runtime = json.loads(runtime_path.read_text())
    if runtime.get("schema_version") != 1 or runtime.get("rom_sha256") != reference["rom_sha256"]:
        raise compare.ReferenceError("runtime identity differs from full-race reference")
    seed = checked_file(root, runtime.get("seed"), rep, "seed")
    seed_bytes = seed.read_bytes()
    if (len(seed_bytes) != finish.STATE_V1_BYTES or seed_bytes[:8] != protocol.STATE_MAGIC
            or int.from_bytes(seed_bytes[8:12], "little") != reference["initial_frame"]):
        raise compare.ReferenceError("full-race seed is not canonical URMV0001")
    content = relative_path(root, runtime.get("content_dir"))
    files = runtime.get("files")
    if not isinstance(files, list) or len(files) != len(STATIC_SIZES):
        raise compare.ReferenceError("runtime must bind the complete static content inventory")
    seen = set()
    for entry in files:
        name = entry.get("name") if isinstance(entry, dict) else None
        if name not in STATIC_SIZES or name in seen or entry.get("size") != STATIC_SIZES[name]:
            raise compare.ReferenceError("invalid static content entry")
        seen.add(name)
        path = checked_file(root, {"path": str((content / name).relative_to(root)),
                            "sha256": entry.get("sha256")}, rep, f"content:{name}")
        if path.stat().st_size != entry["size"]:
            raise compare.ReferenceError(f"static file size differs: {name}")
    if {path.name for path in content.iterdir()} != seen:
        raise compare.ReferenceError("content directory contains unbound entries")
    return reference, replay, finish_case, seed, seed_bytes, content


def build_runner(root: Path, preset: str, timeout: float, artifacts: Path):
    return run_bounded([sys.executable, str(root / "tools/project.py"), "build",
                        "--preset", preset, "--timeout", str(timeout),
                        "--report", str(artifacts / "build.json")],
                       timeout=2 * timeout + 15, cwd=root)


def process_exit(result) -> int:
    if result.missing:
        return 2
    if result.timed_out:
        return 4
    return 0 if result.returncode == 0 else 1


def verify_unchanged_inputs(rep: reports.Report, content: Path) -> None:
    if {path.name for path in content.iterdir()} != set(STATIC_SIZES):
        raise compare.NativeOutputError("static content directory changed during execution")
    for name, entry in rep.data["inputs"].items():
        if reports.file_sha256(Path(entry["path"])) != entry["sha256"]:
            raise compare.NativeOutputError(f"input changed during comparison: {name}")


def native_process(runner: Path, seed: Path, content: Path, stream: Path,
                   timeout: float, artifacts: Path, label: str,
                   initial_frame: int, last_frame: int, rep: reports.Report):
    result = run_bounded([str(runner), "--seed", str(seed), "--content-dir", str(content),
                          "--inputs", str(stream)], timeout=timeout, cwd=artifacts)
    rep.add_check(label, result.outcome, detail=result.stderr[-1500:])
    output = artifacts / f"{label}.txt"
    output.write_text(result.stdout)
    (artifacts / f"{label}.stderr.txt").write_text(result.stderr)
    rep.add_artifact(label, output)
    status = process_exit(result)
    if status:
        return status, None, None
    rows, states = protocol.parse_output(result.stdout, initial_frame, last_frame)
    return 0, rows, states


def continuation_divergence(expected_rows, actual_rows, expected_states, actual_states):
    for index, (expected_row, actual_row, expected_state, actual_state) in enumerate(
            zip(expected_rows, actual_rows, expected_states, actual_states)):
        if expected_row == actual_row and expected_state == actual_state:
            continue
        fields = [{"field": compare.COLUMNS[column], "uninterrupted": expected_row[column],
                   "restored": actual_row[column]}
                  for column in range(len(compare.COLUMNS))
                  if expected_row[column] != actual_row[column]]
        offsets = [offset for offset, pair in enumerate(zip(expected_state, actual_state))
                   if pair[0] != pair[1]]
        return {"frame": expected_row[0],
                "prior_frame": expected_rows[index - 1][0] if index else None,
                "projection_differences": fields,
                "canonical_byte_offsets": offsets[:32],
                "canonical_byte_difference_count": len(offsets),
                "uninterrupted_state_sha256": hashlib.sha256(expected_state).hexdigest(),
                "restored_state_sha256": hashlib.sha256(actual_state).hexdigest()}
    return None


def cmd_compare(args: argparse.Namespace) -> int:
    root = ROOT.resolve()
    rep = reports.Report(sys.argv, task_id=args.task)
    # Fresh artifacts prevent stale output being reported as a successful run.
    artifacts = (Path(args.artifacts).resolve() if args.artifacts else
                 Path(args.report).resolve().parent if args.report else
                 root / "artifacts" / f"native-{rep.data['run_id']}")
    report_path = Path(args.report).resolve() if args.report else artifacts / "report.json"
    if (not artifacts.is_relative_to(root / "artifacts") or artifacts == root / "artifacts"
            or not report_path.is_relative_to(artifacts) or report_path == artifacts
            or any(report_path.is_relative_to(artifacts / name) for name in
                   ("inputs.txt", "build.json", "run1.txt", "run2.txt", "run1.stderr.txt", "run2.stderr.txt"))
            or artifacts.exists() or not math.isfinite(args.timeout) or args.timeout <= 0):
        print("native compare requires a fresh directory under artifacts/, its report inside that directory, and a positive timeout", file=sys.stderr)
        return 3
    artifacts.mkdir(parents=True)
    status = 0
    try:
        reference, replay, seed, seed_bytes, content = load_case(root, Path(args.manifest).resolve(), rep)
        # Validate the reporting window before running a producer.
        compare.compare_rows(reference, reference["rows"], replay,
                             from_frame=args.from_frame, to_frame=args.to_frame)
        rep.add_check("input_identities", "passed")
        runner = root / "build" / args.preset / "src" / "core" / "movement_runner"
        # A successful build with no movement target must never reuse an old binary.
        # Remove only this generated executable, leaving source/content untouched.
        if runner.is_file() or runner.is_symlink():
            runner.unlink()
        result = build_runner(root, args.preset, args.timeout, artifacts)
        rep.add_check("native_build", result.outcome, detail=result.tail(1500))
        status = process_exit(result)
        if status and result.returncode in (2, 3, 4):
            status = result.returncode
        if status == 0:
            rep.add_input("native_binary", runner, reports.file_sha256(runner))
            stream = artifacts / "inputs.txt"
            stream.write_text(protocol.input_text(replay, reference["initial_frame"], reference["last_frame"]))
            rep.add_input("controller_inputs", stream, reports.file_sha256(stream))
            series = []
            for number in (1, 2):
                result = run_bounded([str(runner), "--seed", str(seed), "--content-dir", str(content), "--inputs", str(stream)], timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"native_process_{number}", result.outcome, detail=result.stderr[-1500:])
                output = artifacts / f"run{number}.txt"
                output.write_text(result.stdout)
                (artifacts / f"run{number}.stderr.txt").write_text(result.stderr)
                rep.add_artifact(f"native_output_{number}", output)
                status = process_exit(result)
                if status:
                    break
                verify_unchanged_inputs(rep, content)
                rows, states = protocol.parse_output(result.stdout, reference["initial_frame"], reference["last_frame"])
                if states[0] != seed_bytes:
                    raise compare.NativeOutputError("native process changed the initial canonical seed")
                comparison = compare.compare_rows(reference, rows, replay, from_frame=args.from_frame, to_frame=args.to_frame)
                series.append((rows, states))
                rep.data[f"run{number}"] = {**protocol.state_digests(states), "comparison": comparison}
            if status == 0:
                deterministic = series[0] == series[1]
                rep.add_check("native_fresh_process_repeatability", "passed" if deterministic else "failed")
                rep.data["fresh_processes"] = 2
                rep.data["comparison"] = rep.data["run1"]["comparison"]
                equal = rep.data["comparison"]["identical"]
                rep.add_check("projected_fields_identical", "passed" if equal else "failed")
                status = 0 if deterministic and equal else 1
        verify_unchanged_inputs(rep, content)
    except FileNotFoundError as exc:
        rep.add_check("prerequisite", "missing", detail=str(exc)); status = 2
    except compare.NativeOutputError as exc:
        rep.add_check("native_output", "failed", detail=str(exc)); status = 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        rep.add_check("case_or_arguments", "failed", detail=str(exc)); status = 3
    rep.finish("passed" if status == 0 else "failed")
    if rep.data["source_changed_during_run"]:
        rep.add_check("source_stable", "failed", detail="source changed during comparison")
        status = 1
        rep.finish("failed")
    rep.write(report_path)
    reports.print_summary(rep)
    return status


def cmd_restore_check(args: argparse.Namespace) -> int:
    root = ROOT.resolve()
    rep = reports.Report(sys.argv, task_id=args.task)
    artifacts = (Path(args.artifacts).resolve() if args.artifacts else
                 Path(args.report).resolve().parent if args.report else
                 root / "artifacts" / f"native-restore-{rep.data['run_id']}")
    report_path = Path(args.report).resolve() if args.report else artifacts / "report.json"
    reserved = {"build.json", "baseline-inputs.txt", "baseline.txt",
                "baseline.stderr.txt"}
    report_first = report_path.relative_to(artifacts).parts[0] if report_path.is_relative_to(artifacts) else ""
    if (not artifacts.is_relative_to(root / "artifacts") or artifacts == root / "artifacts"
            or not report_path.is_relative_to(artifacts) or report_path == artifacts
            or report_first in reserved
            or report_first.startswith(("prefix-", "suffix-", "state-"))
            or artifacts.exists() or not math.isfinite(args.timeout) or args.timeout <= 0):
        print("native restore-check requires a fresh directory under artifacts/, its report inside that directory, and a positive timeout", file=sys.stderr)
        return 3
    artifacts.mkdir(parents=True)
    status = 0
    try:
        reference, replay, seed, seed_bytes, content = load_case(root, Path(args.manifest).resolve(), rep)
        if len(seed_bytes) != 333:
            raise compare.ReferenceError("M2-02 requires the canonical 333-byte movement state")
        boundaries = args.save_frame
        if (not boundaries or len(set(boundaries)) != len(boundaries)
                or any(frame <= reference["initial_frame"] or frame >= reference["last_frame"]
                       for frame in boundaries)):
            raise ValueError("save frames must be distinct and strictly inside the native case")
        boundaries = sorted(boundaries)
        rep.data["save_frames"] = boundaries
        rep.add_check("input_identities", "passed")
        runner = root / "build" / args.preset / "src" / "core" / "movement_runner"
        if runner.is_file() or runner.is_symlink():
            runner.unlink()
        result = build_runner(root, args.preset, args.timeout, artifacts)
        rep.add_check("native_build", result.outcome, detail=result.tail(1500))
        status = process_exit(result)
        if status and result.returncode in (2, 3, 4):
            status = result.returncode
        if status == 0:
            rep.add_input("native_binary", runner, reports.file_sha256(runner))
            baseline_stream = artifacts / "baseline-inputs.txt"
            baseline_stream.write_text(protocol.input_text(
                replay, reference["initial_frame"], reference["last_frame"]))
            rep.add_input("controller_inputs", baseline_stream, reports.file_sha256(baseline_stream))
            status, baseline_rows, baseline_states = native_process(
                runner, seed, content, baseline_stream, args.timeout, artifacts, "baseline",
                reference["initial_frame"], reference["last_frame"], rep)
            if status == 0:
                verify_unchanged_inputs(rep, content)
        if status == 0:
            if baseline_states[0] != seed_bytes:
                raise compare.NativeOutputError("uninterrupted process changed the initial canonical seed")
            baseline_comparison = compare.compare_rows(reference, baseline_rows, replay)
            rep.data["baseline"] = {**protocol.state_digests(baseline_states),
                                    "comparison": baseline_comparison}
            rep.add_check("baseline_reference_identical",
                          "passed" if baseline_comparison["identical"] else "failed")
            status = 0 if baseline_comparison["identical"] else 1
        if status == 0:
            rep.data["boundaries"] = {}
            process_count = 1
            for frame in boundaries:
                offset = frame - reference["initial_frame"]
                prefix_stream = artifacts / f"prefix-{frame}-inputs.txt"
                suffix_stream = artifacts / f"suffix-{frame}-inputs.txt"
                prefix_stream.write_text(protocol.input_text(replay, reference["initial_frame"], frame))
                suffix_stream.write_text(protocol.input_text(replay, frame, reference["last_frame"]))
                rep.add_input(f"prefix_inputs_{frame}", prefix_stream,
                              reports.file_sha256(prefix_stream))
                rep.add_input(f"suffix_inputs_{frame}", suffix_stream,
                              reports.file_sha256(suffix_stream))
                status, prefix_rows, prefix_states = native_process(
                    runner, seed, content, prefix_stream, args.timeout, artifacts,
                    f"prefix-{frame}", reference["initial_frame"], frame, rep)
                process_count += 1
                if status:
                    break
                verify_unchanged_inputs(rep, content)
                if prefix_rows != baseline_rows[:offset + 1] or prefix_states != baseline_states[:offset + 1]:
                    raise compare.NativeOutputError(f"prefix differs from uninterrupted execution at save frame {frame}")
                saved = prefix_states[-1]
                if (len(saved) != len(seed_bytes) or saved[:8] != protocol.STATE_MAGIC
                        or int.from_bytes(saved[8:12], "little") != frame):
                    raise compare.NativeOutputError(f"saved canonical state is invalid at frame {frame}")
                state_path = artifacts / f"state-{frame}.bin"
                state_path.write_bytes(saved)
                rep.add_artifact(f"saved_state_{frame}", state_path)
                rep.add_input(f"restore_seed_{frame}", state_path,
                              reports.file_sha256(state_path))
                status, suffix_rows, suffix_states = native_process(
                    runner, state_path, content, suffix_stream, args.timeout, artifacts,
                    f"suffix-{frame}", frame, reference["last_frame"], rep)
                process_count += 1
                if status:
                    break
                verify_unchanged_inputs(rep, content)
                divergence = continuation_divergence(
                    baseline_rows[offset:], suffix_rows,
                    baseline_states[offset:], suffix_states)
                identical = divergence is None
                rep.add_check(f"continuation_{frame}_identical",
                              "passed" if identical else "failed")
                rep.data["boundaries"][str(frame)] = {
                    "saved_state_bytes": len(saved),
                    "saved_state_sha256": hashlib.sha256(saved).hexdigest(),
                    **protocol.state_digests(suffix_states),
                }
                if divergence is not None:
                    rep.data["boundaries"][str(frame)]["first_divergence"] = divergence
                if not identical:
                    status = 1
                    break
            rep.data["fresh_processes"] = process_count
        verify_unchanged_inputs(rep, content)
    except FileNotFoundError as exc:
        rep.add_check("prerequisite", "missing", detail=str(exc)); status = 2
    except compare.NativeOutputError as exc:
        rep.add_check("native_output", "failed", detail=str(exc)); status = 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        rep.add_check("case_or_arguments", "failed", detail=str(exc)); status = 3
    rep.finish("passed" if status == 0 else "failed")
    if rep.data["source_changed_during_run"]:
        rep.add_check("source_stable", "failed", detail="source changed during restore check")
        status = 1
        rep.finish("failed")
    rep.write(report_path)
    reports.print_summary(rep)
    return status


def cmd_finish_check(args: argparse.Namespace) -> int:
    """Compare both gameplay and finish state, optionally across restore boundaries."""
    root = ROOT.resolve()
    rep = reports.Report(sys.argv, task_id=args.task)
    artifacts = (Path(args.artifacts).resolve() if args.artifacts else
                 Path(args.report).resolve().parent if args.report else
                 root / "artifacts" / f"native-finish-{rep.data['run_id']}")
    report_path = Path(args.report).resolve() if args.report else artifacts / "report.json"
    if (not artifacts.is_relative_to(root / "artifacts") or artifacts == root / "artifacts"
            or not report_path.is_relative_to(artifacts) or artifacts.exists()
            or not math.isfinite(args.timeout) or args.timeout <= 0):
        print("native finish-check requires a fresh artifacts directory and positive timeout", file=sys.stderr)
        return 3
    artifacts.mkdir(parents=True)
    status = 0
    try:
        reference, replay, finish_case, seed, seed_bytes, content = load_finish_case(
            root, Path(args.manifest).resolve(), rep)
        boundaries = sorted(args.save_frame or [])
        if (len(boundaries) != len(set(boundaries)) or any(frame <= reference["initial_frame"]
                or frame >= reference["last_frame"] for frame in boundaries)):
            raise ValueError("save frames must be unique and interior")
        rep.data["save_frames"] = boundaries
        rep.add_check("input_identities", "passed")
        runner = root / "build" / args.preset / "src" / "core" / "movement_runner"
        if runner.is_file() or runner.is_symlink(): runner.unlink()
        result = build_runner(root, args.preset, args.timeout, artifacts)
        rep.add_check("native_build", result.outcome, detail=result.tail(1500))
        status = process_exit(result)
        if status == 0:
            rep.add_input("native_binary", runner, reports.file_sha256(runner))
            stream = artifacts / "inputs.txt"
            stream.write_text(protocol.input_text(replay, reference["initial_frame"], reference["last_frame"]))
            rep.add_input("controller_inputs", stream, reports.file_sha256(stream))
            series = []
            for number in (1, 2):
                result = run_bounded([str(runner), "--seed", str(seed), "--content-dir", str(content),
                                      "--inputs", str(stream)], timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"native_process_{number}", result.outcome, detail=result.stderr[-1500:])
                output = artifacts / f"run{number}.txt"; output.write_text(result.stdout)
                (artifacts / f"run{number}.stderr.txt").write_text(result.stderr)
                rep.add_artifact(f"native_output_{number}", output)
                status = process_exit(result)
                if status: break
                rows, states = finish.parse_output(result.stdout, reference["initial_frame"], reference["last_frame"])
                if states[0] != seed_bytes: raise compare.NativeOutputError("native process changed the initial seed")
                comparison = finish.validate(rows, states, reference, finish_case)
                series.append((rows, states)); rep.data[f"run{number}"] = {
                    **finish.state_digests(states), "comparison": comparison}
            if status == 0:
                repeatable = series[0] == series[1]
                rep.add_check("native_fresh_process_repeatability", "passed" if repeatable else "failed")
                rep.add_check("gameplay_and_finish_identical", "passed" if rep.data["run1"]["comparison"]["identical"] else "failed")
                status = 0 if repeatable and rep.data["run1"]["comparison"]["identical"] else 1
        if status == 0 and boundaries:
            baseline_rows, baseline_states = series[0]
            rep.data["boundaries"] = {}
            for frame in boundaries:
                offset = frame - reference["initial_frame"]
                prefix = artifacts / f"prefix-{frame}.txt"; suffix = artifacts / f"suffix-{frame}.txt"
                prefix.write_text(protocol.input_text(replay, reference["initial_frame"], frame))
                suffix.write_text(protocol.input_text(replay, frame, reference["last_frame"]))
                prefix_result = run_bounded([str(runner), "--seed", str(seed), "--content-dir", str(content), "--inputs", str(prefix)], timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"prefix_{frame}", prefix_result.outcome,
                              detail=prefix_result.stderr[-1500:])
                if process_exit(prefix_result): raise compare.NativeOutputError(f"prefix process failed at {frame}")
                prefix_rows, prefix_states = finish.parse_output(prefix_result.stdout, reference["initial_frame"], frame)
                if (prefix_rows, prefix_states) != (baseline_rows[:offset + 1], baseline_states[:offset + 1]):
                    raise compare.NativeOutputError(f"prefix differs at {frame}")
                saved = prefix_states[-1]; saved_path = artifacts / f"state-{frame}.bin"; saved_path.write_bytes(saved)
                rep.add_artifact(f"saved_state_{frame}", saved_path)
                suffix_result = run_bounded([str(runner), "--seed", str(saved_path), "--content-dir", str(content), "--inputs", str(suffix)], timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"suffix_{frame}", suffix_result.outcome,
                              detail=suffix_result.stderr[-1500:])
                if process_exit(suffix_result): raise compare.NativeOutputError(f"suffix process failed at {frame}")
                suffix_rows, suffix_states = finish.parse_output(suffix_result.stdout, frame, reference["last_frame"])
                divergence = continuation_divergence(baseline_rows[offset:], suffix_rows,
                                                     baseline_states[offset:], suffix_states)
                rep.add_check(f"continuation_{frame}_identical", "passed" if divergence is None else "failed")
                rep.data["boundaries"][str(frame)] = {"saved_state_bytes": len(saved),
                    "saved_state_sha256": hashlib.sha256(saved).hexdigest(), "first_divergence": divergence}
                if divergence is not None: status = 1; break
                verify_unchanged_inputs(rep, content)
        verify_unchanged_inputs(rep, content)
    except FileNotFoundError as exc:
        rep.add_check("prerequisite", "missing", detail=str(exc)); status = 2
    except compare.NativeOutputError as exc:
        rep.add_check("native_output", "failed", detail=str(exc)); status = 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        rep.add_check("case_or_arguments", "failed", detail=str(exc)); status = 3
    rep.finish("passed" if status == 0 else "failed")
    if rep.data["source_changed_during_run"]:
        rep.add_check("source_stable", "failed", detail="source changed during finish check")
        status = 1; rep.finish("failed")
    rep.write(report_path); reports.print_summary(rep)
    return status


def register(subparsers) -> None:
    parser = subparsers.add_parser("native", help="native movement comparison")
    commands = parser.add_subparsers(dest="native_command", required=True)
    command = commands.add_parser("compare", help="build and run native movement twice against a frozen reference")
    command.add_argument("--manifest", required=True, help="identity-bound native case JSON")
    command.add_argument("--preset", choices=("lab-debug", "lab-release", "lab-sanitize"), default="lab-debug")
    command.add_argument("--artifacts", help="fresh output directory below repository artifacts/")
    command.add_argument("--report", help="report path inside this run's fresh artifacts directory")
    command.add_argument("--from-frame", type=int)
    command.add_argument("--to-frame", type=int)
    command.add_argument("--timeout", type=float, default=120)
    command.add_argument("--task", default="M2-01")
    command.set_defaults(func=cmd_compare)
    restore = commands.add_parser("restore-check", help="compare uninterrupted movement with fresh-process save/restore continuations")
    restore.add_argument("--manifest", required=True, help="identity-bound native case JSON")
    restore.add_argument("--save-frame", type=int, action="append", required=True,
                         help="interior frame to serialize and resume; repeat for multiple boundaries")
    restore.add_argument("--preset", choices=("lab-debug", "lab-release", "lab-sanitize"), default="lab-debug")
    restore.add_argument("--artifacts", help="fresh output directory below repository artifacts/")
    restore.add_argument("--report", help="report path inside this run's fresh artifacts directory")
    restore.add_argument("--timeout", type=float, default=120)
    restore.add_argument("--task", default="M2-02")
    restore.set_defaults(func=cmd_restore_check)
    finish_check = commands.add_parser("finish-check", help="compare full-race gameplay/finish state and optional restored continuations")
    finish_check.add_argument("--manifest", required=True)
    finish_check.add_argument("--save-frame", type=int, action="append")
    finish_check.add_argument("--preset", choices=("lab-debug", "lab-release", "lab-sanitize"), default="lab-debug")
    finish_check.add_argument("--artifacts")
    finish_check.add_argument("--report")
    finish_check.add_argument("--timeout", type=float, default=120)
    finish_check.add_argument("--task", default="M3-01")
    finish_check.set_defaults(func=cmd_finish_check)
