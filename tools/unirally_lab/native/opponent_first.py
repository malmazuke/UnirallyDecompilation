"""Identity-bound M3-04 opponent-first continuation check."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

from .. import report as reports
from ..content import pack as packmod
from ..procs import run_bounded
from ..replay import manifest as replaymod
from . import commands, compare, finish, protocol


def _u16(state: bytes, offset: int) -> int:
    return int.from_bytes(state[offset:offset + 2], "little")


def projection(state: bytes) -> list[int]:
    finished = state[:8] != protocol.STATE_MAGIC
    return [_u16(state, 144), _u16(state, 146), _u16(state, 148),
            _u16(state, 216), _u16(state, 16),
            int(finished and bool(state[333])), int(finished and bool(state[334])),
            _u16(state, 363) if finished else 0,
            *(_u16(state, 272 + 2 * index) for index in range(5))]


def projection_digest(states: list[bytes], initial: int) -> tuple[str, dict[str, list[int]]]:
    encoded = bytearray()
    rows = {}
    for index, state in enumerate(states):
        frame = initial + index
        values = projection(state)
        encoded += struct.pack("<I13H", frame, *values)
        rows[str(frame)] = values
    return hashlib.sha256(encoded).hexdigest(), rows


def _load(root: Path, case_path: Path, pack_path: Path, rep: reports.Report):
    case = json.loads(case_path.read_text())
    if (case.get("schema_version"), case.get("kind")) != (1, "native_opponent_first_case"):
        raise compare.ReferenceError("unsupported opponent-first case")
    rep.add_input("native_case", case_path, reports.file_sha256(case_path))
    replay_path = commands.checked_file(root, case.get("replay"), rep, "replay")
    expected_path = commands.checked_file(root, case.get("expected"), rep, "expected")
    replay = replaymod.validate_manifest(json.loads(replay_path.read_text()))
    expected = json.loads(expected_path.read_text())
    if (expected.get("schema_version"), expected.get("kind")) != (1, "frozen_opponent_first_projection"):
        raise compare.ReferenceError("unsupported opponent-first projection")
    if (expected.get("replay_manifest_sha256") != reports.file_sha256(replay_path)
            or expected.get("scenario_id") != replay["scenario_id"]
            or expected.get("rom_sha256") != replay["rom"]["sha256"]):
        raise compare.ReferenceError("opponent-first reference identity differs")
    rules, rules_digest = packmod.load_rules(root / packmod.RULES_PATH)
    inspected = packmod.validate_pack(pack_path.read_bytes(), rules, rules_digest)
    if inspected["source_rom_sha256"] != expected["rom_sha256"]:
        raise compare.ReferenceError("Classic pack and opponent-first ROM identities differ")
    rep.add_input("classic_pack", pack_path, reports.file_sha256(pack_path))
    return replay, expected


def cmd(args: argparse.Namespace) -> int:
    root = reports.repo_root().resolve()
    rep = reports.Report(sys.argv, task_id=args.task)
    artifacts = (Path(args.artifacts).resolve() if args.artifacts else
                 Path(args.report).resolve().parent if args.report else
                 root / "artifacts" / f"native-opponent-first-{rep.data['run_id']}")
    report_path = Path(args.report).resolve() if args.report else artifacts / "report.json"
    if (not artifacts.is_relative_to(root / "artifacts") or artifacts == root / "artifacts"
            or not report_path.is_relative_to(artifacts) or artifacts.exists()
            or not math.isfinite(args.timeout) or args.timeout <= 0):
        print("native opponent-first-check requires a fresh artifacts directory and positive timeout", file=sys.stderr)
        return 3
    artifacts.mkdir(parents=True)
    status = 0
    try:
        pack_path = Path(args.content_pack).resolve()
        replay, expected = _load(root, Path(args.manifest).resolve(), pack_path, rep)
        initial, last = expected["initial_frame"], expected["last_frame"]
        boundaries = sorted(args.save_frame or [])
        if (len(boundaries) != len(set(boundaries)) or
                any(frame <= initial or frame >= last for frame in boundaries)):
            raise ValueError("save frames must be unique and interior")
        rep.data["save_frames"] = boundaries
        runner = root / "build" / args.preset / "src" / "core" / "movement_runner"
        if runner.is_file() or runner.is_symlink():
            runner.unlink()
        build = commands.build_runner(root, args.preset, args.timeout, artifacts)
        rep.add_check("native_build", build.outcome, detail=build.tail(1500))
        status = commands.process_exit(build)
        stream = artifacts / "inputs.txt"
        stream.write_text(protocol.input_text(replay, initial, last))
        if status == 0:
            rep.add_input("native_binary", runner, reports.file_sha256(runner))
            rep.add_input("controller_inputs", stream, reports.file_sha256(stream))
            series = []
            for number in (1, 2):
                result = run_bounded([str(runner), *commands.runner_arguments(
                    None, pack_path, stream, pack_mode=True, start_state=True)],
                    timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"native_process_{number}", result.outcome, detail=result.stderr[-1500:])
                output = artifacts / f"run{number}.txt"
                output.write_text(result.stdout)
                rep.add_artifact(f"native_output_{number}", output)
                status = commands.process_exit(result)
                if status:
                    break
                rows, states = finish.parse_output(result.stdout, initial, last)
                digest, projected = projection_digest(states, initial)
                checkpoint_differences = {frame: {"original": values, "native": projected.get(frame)}
                    for frame, values in expected["checkpoints"].items()
                    if projected.get(frame) != values}
                exact = digest == expected["projection_sha256"] and not checkpoint_differences
                rep.data[f"run{number}"] = {**finish.state_digests(states),
                    "projection_sha256": digest, "checkpoint_differences": checkpoint_differences}
                rep.add_check(f"original_projection_{number}", "passed" if exact else "failed")
                if not exact:
                    status = 1
                    break
                series.append((rows, states))
            if status == 0:
                repeatable = series[0] == series[1]
                rep.add_check("native_fresh_process_repeatability", "passed" if repeatable else "failed")
                status = 0 if repeatable else 1
        if status == 0:
            baseline_rows, baseline_states = series[0]
            rep.data["boundaries"] = {}
            for frame in boundaries:
                offset = frame - initial
                prefix = artifacts / f"prefix-{frame}.txt"
                suffix = artifacts / f"suffix-{frame}.txt"
                prefix.write_text(protocol.input_text(replay, initial, frame))
                suffix.write_text(protocol.input_text(replay, frame, last))
                first = run_bounded([str(runner), *commands.runner_arguments(None, pack_path, prefix,
                    pack_mode=True, start_state=True)], timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"prefix_{frame}", first.outcome, detail=first.stderr[-1500:])
                if commands.process_exit(first):
                    raise compare.NativeOutputError(f"prefix process failed at {frame}")
                prefix_rows, prefix_states = finish.parse_output(first.stdout, initial, frame)
                if (prefix_rows, prefix_states) != (baseline_rows[:offset + 1], baseline_states[:offset + 1]):
                    raise compare.NativeOutputError(f"prefix differs at {frame}")
                saved = artifacts / f"state-{frame}.bin"
                saved.write_bytes(prefix_states[-1])
                second = run_bounded([str(runner), *commands.runner_arguments(saved, pack_path, suffix,
                    pack_mode=True)], timeout=args.timeout, cwd=artifacts)
                rep.add_check(f"suffix_{frame}", second.outcome, detail=second.stderr[-1500:])
                if commands.process_exit(second):
                    raise compare.NativeOutputError(f"suffix process failed at {frame}")
                suffix_rows, suffix_states = finish.parse_output(second.stdout, frame, last)
                divergence = commands.continuation_divergence(
                    baseline_rows[offset:], suffix_rows, baseline_states[offset:], suffix_states)
                rep.add_check(f"continuation_{frame}_identical", "passed" if divergence is None else "failed")
                rep.data["boundaries"][str(frame)] = {"saved_state_bytes": len(prefix_states[-1]),
                    "saved_state_sha256": hashlib.sha256(prefix_states[-1]).hexdigest(),
                    "first_divergence": divergence}
                if divergence is not None:
                    status = 1
                    break
    except FileNotFoundError as exc:
        rep.add_check("prerequisite", "missing", detail=str(exc)); status = 2
    except compare.NativeOutputError as exc:
        rep.add_check("native_output", "failed", detail=str(exc)); status = 1
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        rep.add_check("case_or_arguments", "failed", detail=str(exc)); status = 3
    rep.finish("passed" if status == 0 else "failed")
    rep.write(report_path)
    reports.print_summary(rep)
    return status


def register(commands_parser) -> None:
    parser = commands_parser.add_parser(
        "opponent-first-check", help="compare the frozen opponent-first continuation and restores")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--content-pack", required=True)
    parser.add_argument("--save-frame", type=int, action="append")
    parser.add_argument("--preset", choices=("lab-debug", "lab-release", "lab-sanitize"), default="lab-debug")
    parser.add_argument("--artifacts")
    parser.add_argument("--report")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--task", default="M3-04")
    parser.set_defaults(func=cmd)
