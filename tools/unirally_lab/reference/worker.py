#!/usr/bin/env python3
"""Fresh-process reference run: execute one script on the core and write samples.

Usage: worker.py --core LIB --rom ROM --script S --samples-out OUT
                 [--system-dir D] [--state-in P] [--save-after N --state-out P]

Exit codes follow the repository convention: 0 success, 1 run failure,
2 missing core/ROM, 3 invalid script or arguments. Timeouts are enforced by
the parent (``project.py reference ...``), which kills this process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from unirally_lab import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK  # noqa: E402
from unirally_lab.reference import bsnes  # noqa: E402

SCRIPT_SCHEMA_VERSION = 1
SAMPLES_SCHEMA_VERSION = 1


class ScriptError(ValueError):
    pass


def load_script(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ScriptError(f"cannot read script {path}: {exc}") from exc
    return validate_script(data)


def validate_script(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != SCRIPT_SCHEMA_VERSION:
        raise ScriptError(f"script schema_version must be {SCRIPT_SCHEMA_VERSION}")
    if data.get("core", "bsnes") != "bsnes":
        raise ScriptError(f"unsupported core {data.get('core')!r}")
    frames = data.get("frames")
    if not isinstance(frames, int) or isinstance(frames, bool) or frames <= 0:
        raise ScriptError("frames must be a positive integer")
    every = data.get("sample_every", 1)
    if not isinstance(every, int) or isinstance(every, bool) or every <= 0:
        raise ScriptError("sample_every must be a positive integer")
    trace = data.get("trace_entries", 64)
    if not isinstance(trace, int) or isinstance(trace, bool) or trace < 0 or trace > 1_000_000:
        raise ScriptError("trace_entries must be an integer in 0..1000000")
    inputs = data.get("inputs", [])
    if not isinstance(inputs, list):
        raise ScriptError("inputs must be a list")
    for i, entry in enumerate(inputs):
        if not isinstance(entry, dict):
            raise ScriptError(f"inputs[{i}] must be an object")
        lo, hi, port = entry.get("from"), entry.get("to"), entry.get("port", 0)
        buttons = entry.get("buttons")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (lo, hi, port)):
            raise ScriptError(f"inputs[{i}]: from, to and port must be integers")
        if lo < 0 or hi < lo or port not in (0, 1):
            raise ScriptError(f"inputs[{i}]: need 0 <= from <= to and port in (0, 1)")
        if not isinstance(buttons, list) or not buttons or any(b not in bsnes.BUTTONS for b in buttons):
            raise ScriptError(f"inputs[{i}]: buttons must be a non-empty list from {sorted(bsnes.BUTTONS)}")
    options = data.get("core_options", {})
    if not isinstance(options, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in options.items()):
        raise ScriptError("core_options must map strings to strings")
    if set(options) - set(bsnes.DEFAULT_OPTIONS):
        raise ScriptError(f"unknown core_options {sorted(set(options) - set(bsnes.DEFAULT_OPTIONS))}")
    return data


STATE_IDENTITY_KEYS = ("sha256", "core_sha256", "rom_sha256", "script_sha256", "serialization_method")


def validate_state_sidecar(meta: Any, actual: dict[str, Any], script_frames: int) -> tuple[int, dict[str, Any]]:
    """Check a state's sidecar against the current run; returns (resume frame, post-serialize sample).

    A state is only meaningful for the exact core build, ROM, script and
    synchronization method it was taken with, and must leave frames to run.
    """
    if not isinstance(meta, dict):
        raise ScriptError("state sidecar must be a JSON object")
    try:
        after = meta["after_frame"]
        expected = {k: meta[k] for k in STATE_IDENTITY_KEYS}
        post = meta["post_serialize"]
        post_ok = isinstance(post, dict) and isinstance(post.get("wram_sha256"), str) and isinstance(post.get("registers"), dict)
    except (KeyError, TypeError) as exc:
        raise ScriptError(f"state sidecar incomplete: {exc}") from exc
    if not post_ok:
        raise ScriptError("state sidecar lacks a post_serialize sample")
    mismatched = [k for k in STATE_IDENTITY_KEYS if expected[k] != actual.get(k)]
    if mismatched:
        raise ScriptError(f"state does not belong to this run: {', '.join(mismatched)} differ from the sidecar")
    if not isinstance(after, int) or isinstance(after, bool) or not (0 <= after < script_frames - 1):
        raise ScriptError(f"state after frame {after!r} leaves no frames to run in a {script_frames}-frame script")
    return after + 1, post


def inputs_for_frame(script: dict[str, Any], frame: int) -> dict[int, set[str]]:
    result: dict[int, set[str]] = {0: set(), 1: set()}
    for entry in script.get("inputs", []):
        if entry["from"] <= frame <= entry["to"]:
            result[entry.get("port", 0)].update(entry["buttons"])
    return result


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(args: argparse.Namespace) -> int:
    script_path = Path(args.script)
    try:
        script = load_script(script_path)
    except ScriptError as exc:
        print(f"invalid script: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT
    if (args.save_after is None) != (args.state_out is None):
        print("--save-after and --state-out must be given together", file=sys.stderr)
        return EXIT_INVALID_INPUT
    if args.save_after is not None and not (0 <= args.save_after < script["frames"]):
        print("--save-after must lie inside the script's frame range", file=sys.stderr)
        return EXIT_INVALID_INPUT

    rom = Path(args.rom)
    if not rom.is_file():
        print(f"ROM not found: {rom}", file=sys.stderr)
        return EXIT_MISSING_PREREQUISITE
    # The core reads and writes cartridge RAM (save.ram) in its system/save
    # directory. Every run gets a private, empty directory so that a previous
    # run's save file cannot become this run's initial SRAM (M0-03 attempt 8).
    base = Path(args.system_dir) if args.system_dir else Path(args.samples_out).parent / "core-system"
    base.mkdir(parents=True, exist_ok=True)
    system_dir = Path(tempfile.mkdtemp(prefix="run-", dir=base))
    try:
        core = bsnes.BsnesCore(Path(args.core), system_dir, script.get("core_options"))
    except bsnes.CoreMissingError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_MISSING_PREREQUISITE
    except bsnes.CoreError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_FAILURE

    started = time.monotonic()
    out: dict[str, Any] = {
        "schema_version": SAMPLES_SCHEMA_VERSION,
        "core": {"library": str(core.library), "sha256": sha256_file(core.library), "api_version": core.api_version,
                 "options": dict(core.options)},
        "rom": {"path": str(rom), "sha256": sha256_file(rom), "size": rom.stat().st_size},
        "script": {"path": str(script_path), "sha256": sha256_file(script_path), "frames": script["frames"],
                   "sample_every": script.get("sample_every", 1)},
        "frames": [],
    }
    try:
        core.load(rom)
    except bsnes.CoreMissingError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_MISSING_PREREQUISITE
    except bsnes.CoreError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_FAILURE
    try:
        core.set_serialization_method(args.serialization_method)
    except bsnes.CoreError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_INVALID_INPUT
    out["core"]["serialization_method"] = core.serialization_method
    out["rom"]["region"] = core.region
    out["wram_size"] = len(core.wram())
    out["cartridge_ram_size"] = len(core.cartridge_ram())
    out["initial"] = {"wram_sha256": hashlib.sha256(core.wram()).hexdigest(),
                      "cartridge_ram_sha256": hashlib.sha256(core.cartridge_ram()).hexdigest(),
                      "registers": core.registers(), "save_files_present": sorted(p.name for p in system_dir.iterdir())}
    trace_entries = script.get("trace_entries", 64)
    if trace_entries:
        core.trace_enable(trace_entries)

    start = 0
    if args.state_in:
        state_in = Path(args.state_in)
        if not state_in.is_file():
            print(f"state file not found: {state_in}", file=sys.stderr)
            return EXIT_MISSING_PREREQUISITE
        blob = state_in.read_bytes()
        actual = {"sha256": hashlib.sha256(blob).hexdigest(), "core_sha256": out["core"]["sha256"], "rom_sha256": out["rom"]["sha256"],
                  "script_sha256": out["script"]["sha256"], "serialization_method": core.serialization_method}
        try:
            meta = json.loads((state_in.with_suffix(state_in.suffix + ".json")).read_text(encoding="utf-8"))
            start, post = validate_state_sidecar(meta, actual, script["frames"])
        except (OSError, ValueError) as exc:  # ScriptError is a ValueError
            print(f"state sidecar rejected: {exc}", file=sys.stderr)
            return EXIT_INVALID_INPUT
        if not core.unserialize(blob):
            print("core rejected the state", file=sys.stderr)
            return EXIT_FAILURE
        regs = core.registers()
        wram_sha = hashlib.sha256(core.wram()).hexdigest()
        out["state_in"] = {"path": str(state_in), **actual, "after_frame": start - 1, "resumed_at_frame": start,
                           "wram_sha256": wram_sha, "registers": regs,
                           "matches_post_serialize": wram_sha == post["wram_sha256"] and regs == post["registers"]}

    sample_every = script.get("sample_every", 1)
    state_digest = hashlib.sha256()
    state_digest.update(b"initial" + bytes.fromhex(out["initial"]["wram_sha256"]) + bytes.fromhex(out["initial"]["cartridge_ram_sha256"]))
    av_digest = hashlib.sha256()
    for frame in range(start, script["frames"]):
        for port, buttons in inputs_for_frame(script, frame).items():
            core.set_inputs(port, buttons)
        output = core.run_frame()
        if frame % sample_every == 0 or frame == script["frames"] - 1:
            wram_sha = hashlib.sha256(core.wram()).hexdigest()
            regs_raw = core.registers_raw()
            state_digest.update(frame.to_bytes(4, "little") + bytes.fromhex(wram_sha) + regs_raw)
            av_digest.update(frame.to_bytes(4, "little") + (output.video[2] if output.video else "").encode() + output.audio_sha256.encode())
            out["frames"].append({"frame": frame, "wram_sha256": wram_sha, "registers": bsnes.registers_to_dict(regs_raw),
                                  "video": output.video, "audio_sha256": output.audio_sha256, "audio_frames": output.audio_frames})
        if args.save_after is not None and frame == args.save_after:
            blob = core.serialize()
            state_out = Path(args.state_out)
            state_out.parent.mkdir(parents=True, exist_ok=True)
            state_out.write_bytes(blob)
            # Serializing first runs the cores to a synchronization point, so the
            # state corresponds to this post-serialize sample, not to the
            # frame-end sample above (M0-03 review finding).
            meta = {"after_frame": frame, "sha256": hashlib.sha256(blob).hexdigest(), "size": len(blob),
                    "core_sha256": out["core"]["sha256"], "rom_sha256": out["rom"]["sha256"], "script_sha256": out["script"]["sha256"],
                    "serialization_method": core.serialization_method,
                    "post_serialize": {"wram_sha256": hashlib.sha256(core.wram()).hexdigest(), "registers": core.registers()}}
            state_out.with_suffix(state_out.suffix + ".json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            out["state_out"] = {"path": str(state_out), **meta}

    out["start_frame"], out["end_frame"] = start, script["frames"] - 1
    out["sample_digest"] = state_digest.hexdigest()
    out["av_digest"] = av_digest.hexdigest()
    final_state = core.serialize()
    out["final"] = {"wram_sha256": hashlib.sha256(core.wram()).hexdigest(),
                    "cartridge_ram_sha256": hashlib.sha256(core.cartridge_ram()).hexdigest(),
                    "state_sha256": hashlib.sha256(final_state).hexdigest(), "state_size": len(final_state),
                    "registers": core.registers()}
    if trace_entries:
        out["trace"] = {"instructions_executed": core.trace_total(), "window": core.trace_read(trace_entries)}
    out["input_polls"] = core.input_polls
    out["unknown_environment_commands"] = sorted(core.unknown_env)
    out["elapsed_seconds"] = round(time.monotonic() - started, 3)
    core.unload()
    out["final"]["save_files_written"] = sorted(p.name for p in system_dir.iterdir())
    shutil.rmtree(system_dir, ignore_errors=True)
    samples = Path(args.samples_out)
    samples.parent.mkdir(parents=True, exist_ok=True)
    samples.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return EXIT_OK


def probe(args: argparse.Namespace) -> int:
    """Load the core without a ROM and print its laboratory API version."""
    try:
        core = bsnes.BsnesCore(Path(args.core), Path(args.system_dir or Path(args.core).parent / "core-system"))
    except bsnes.CoreMissingError as exc:
        print(json.dumps({"error": str(exc)}))
        return EXIT_MISSING_PREREQUISITE
    except bsnes.CoreError as exc:
        print(json.dumps({"error": str(exc)}))
        return EXIT_FAILURE
    print(json.dumps({"api_version": core.api_version, "library_sha256": sha256_file(core.library)}))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--core", required=True)
    parser.add_argument("--system-dir")
    parser.add_argument("--probe", action="store_true", help="only load the core and report its API version")
    parser.add_argument("--rom")
    parser.add_argument("--script")
    parser.add_argument("--samples-out")
    parser.add_argument("--state-in")
    parser.add_argument("--save-after", type=int)
    parser.add_argument("--state-out")
    parser.add_argument("--serialization-method", default="Strict", choices=("Fast", "Strict"),
                        help="bsnes save-state synchronization method (default Strict; see R-0002)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_INVALID_INPUT if exc.code not in (0, None) else EXIT_OK
    if args.probe:
        return probe(args)
    if not (args.rom and args.script and args.samples_out):
        print("--rom, --script and --samples-out are required", file=sys.stderr)
        return EXIT_INVALID_INPUT
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
