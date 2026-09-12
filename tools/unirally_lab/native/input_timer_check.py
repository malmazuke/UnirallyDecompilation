"""Primary input/timer component check; timer enable is a harness input.

This cannot establish autonomous movement or race-start behavior. It compares
nine fields independently of motion and never feeds later expected digits back
into the native component. The full native comparator must still require all
13 projected fields; this narrower experiment cannot replace it.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ..replay.manifest import inputs_at
from .compare import load_reference

BUTTONS = ["a", "b", "x", "y", "l", "r", "select", "start", "up", "down", "left", "right"]
FIELDS = ["joy1l_image", "joy1h_image", "axis_v", "axis_h", "timer_minutes",
          "timer_tens_seconds", "timer_seconds", "timer_tenths", "timer_frames"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    reference, manifest = load_reference(Path("tests/manifests/native/primary.expected.json"),
                                         Path("tests/manifests/native/primary.replay.json"))
    if (reference["initial_frame"], reference["last_frame"]) != (1533, 2999):
        raise ValueError("this isolated experiment covers primary frames1534–2999 only")
    indices = [reference["columns"].index(field) for field in FIELDS]
    seed = [reference["rows"][0][index] for index in indices[4:]]
    lines = [" ".join(map(str, seed))]
    for frame in range(1534, 3000):
        buttons = inputs_at(manifest, frame)["0"]
        # Original gate capture: no tick1534, latched enable1 from1535 onward.
        # The gate is an explicit research input, not claimed as native state.
        lines.append(" ".join(map(str, [frame, int(frame >= 1535)] +
                                      [int(button in buttons) for button in BUTTONS])))
    request = "\n".join(lines) + "\n"
    process = subprocess.run([str(args.probe.resolve())], input=request, text=True,
                             capture_output=True, timeout=30)
    if process.returncode:
        raise RuntimeError(f"native component failed: {process.stderr}")
    try:
        actual = [[int(value) for value in row.split()] for row in process.stdout.splitlines()]
    except ValueError as error:
        raise RuntimeError("native component emitted a non-integer value") from error
    expected = [[row[0]] + [row[index] for index in indices] for row in reference["rows"][1:]]
    identical = actual == expected
    report = {"kind": "isolated_input_timer_component", "identical": identical,
              "frames": len(expected), "compared_values": len(expected) * len(FIELDS),
              "fields": FIELDS, "timer_enable": "captured gate supplied by harness",
              "native_movement": "not tested", "native_stdout_sha256":
              hashlib.sha256(process.stdout.encode()).hexdigest(),
              "native_stdin_sha256": hashlib.sha256(request.encode()).hexdigest(),
              "reference_manifest_sha256": reference["replay_manifest_sha256"]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
    return 0 if identical else 1


if __name__ == "__main__":
    try:
        result = main()
    except FileNotFoundError as error:
        print(f"missing prerequisite: {error}", file=sys.stderr)
        result = 2
    except subprocess.TimeoutExpired as error:
        print(f"native component timeout: {error}", file=sys.stderr)
        result = 4
    except ValueError as error:
        print(f"invalid input: {error}", file=sys.stderr)
        result = 3
    except (RuntimeError, OSError) as error:
        print(f"native component failure: {error}", file=sys.stderr)
        result = 1
    raise SystemExit(result)
