"""Capture the preregistered M4-08 position-integration experiment.

This research-only surface freezes the inputs, intermediate scratch and
publications of $82:A627--A6F7.  It does not modify or invoke native gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1662.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"

# End-of-frame 1649 supplies the one stateful seed.  Calls on 1650--1700 are
# the declared evaluation domain; frame 1649 is captured only for provenance.
FIRST_CAPTURE_FRAME = 1649
FIRST_CALL_FRAME = 1650
LAST_CALL_FRAME = 1700

# Persistent positions, velocities and four signed residues; the track mask;
# every direct-page input/guard/scratch used by the routine; and caller state
# needed to bind the two ordered rider calls and their final publications.
WATCH_ADDRESSES = sorted(set(
    [
        0x0000, 0x00A5, 0x00A7,
        0x0401, 0x0403, 0x0405, 0x0407,
        0x0415, 0x0417, 0x0419, 0x041B,
        0x04BB, 0x04BD, 0x04BF, 0x04C1,
        0x0B6E, 0x0B70, 0x0D4F,
        0x0F17, 0x0F23, 0x0F2D, 0x0F31, 0x0F33,
        0x0FA9, 0x0FAB,
    ]
    + list(range(0x0F13, 0x0FC2))
))

# Pre-instruction snapshots freeze every branch, arithmetic intermediate and
# publication in the bounded routine, plus the two contact caller boundaries.
WATCH_PCS = [
    0x82A627, 0x82A62A, 0x82A62C, 0x82A62D, 0x82A630, 0x82A632,
    0x82A635, 0x82A636, 0x82A637, 0x82A63A, 0x82A63D, 0x82A63E,
    0x82A641, 0x82A642, 0x82A643, 0x82A644, 0x82A645, 0x82A646,
    0x82A647, 0x82A649, 0x82A64B, 0x82A64C, 0x82A64E, 0x82A651,
    0x82A653, 0x82A655, 0x82A656, 0x82A659, 0x82A65B, 0x82A65C,
    0x82A65F, 0x82A662, 0x82A663, 0x82A664, 0x82A665, 0x82A666,
    0x82A667, 0x82A668, 0x82A66A, 0x82A66C, 0x82A66D, 0x82A66F,
    0x82A672, 0x82A674, 0x82A677, 0x82A679, 0x82A67A, 0x82A67D,
    0x82A67F, 0x82A682, 0x82A683, 0x82A684, 0x82A687, 0x82A68A,
    0x82A68B, 0x82A68E, 0x82A68F, 0x82A690, 0x82A691, 0x82A692,
    0x82A693, 0x82A694, 0x82A696, 0x82A698, 0x82A699, 0x82A69B,
    0x82A69D, 0x82A69F, 0x82A6A0, 0x82A6A3, 0x82A6A5, 0x82A6A6,
    0x82A6A9, 0x82A6AC, 0x82A6AD, 0x82A6AE, 0x82A6AF, 0x82A6B0,
    0x82A6B1, 0x82A6B2, 0x82A6B4, 0x82A6B6, 0x82A6B7, 0x82A6B9,
    0x82A6BB, 0x82A6BE, 0x82A6C0, 0x82A6C3, 0x82A6C5, 0x82A6C8,
    0x82A6CB, 0x82A6CD, 0x82A6D0, 0x82A6D3, 0x82A6D5, 0x82A6D7,
    0x82A6DA, 0x82A6DC, 0x82A6DF, 0x82A6E1, 0x82A6E3, 0x82A6E5,
    0x82A6E8, 0x82A6E9, 0x82A6EB, 0x82A6ED, 0x82A6EF, 0x82A6F1,
    0x82A6F2, 0x82A6F5, 0x82A6F7,
    0x818D97, 0x818D9C, 0x818F98, 0x818F9D,
]


def capture_command(manifest: Path, out: Path) -> list[str]:
    if manifest.resolve() == (ROOT / PRIMARY).resolve():
        if hashlib.sha256(manifest.read_bytes()).hexdigest() != PRIMARY_SHA256:
            raise ValueError("accepted primary replay manifest identity differs")
    elif manifest.resolve() != (ROOT / VARIATION).resolve():
        raise ValueError("position capture accepts only the preregistered scenarios")
    result = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(FIRST_CAPTURE_FRAME),
        "--to-frame", str(LAST_CALL_FRAME),
        "--wram-series-range", "0", "0x2200", "--timeout", "180",
        "--report", str(out / "report.json"),
    ]
    for address in WATCH_ADDRESSES:
        result += ["--watch-address", hex(address)]
    for pc in WATCH_PCS:
        result += ["--watch-pc", hex(pc)]
    return result


def capture(manifest: Path, out: Path) -> int:
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty capture directory")
    out.mkdir(parents=True, exist_ok=True)
    command = capture_command(manifest, out)
    (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    return subprocess.run(command, timeout=200).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", choices=["capture"])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        return capture(args.manifest, args.out)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
