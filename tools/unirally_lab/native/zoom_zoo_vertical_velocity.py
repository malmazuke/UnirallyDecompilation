"""Preregistered M4-11 vertical-velocity recurrence experiment.

This additive research surface observes original execution only. It does not
modify or invoke production native gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .zoom_zoo_response_b import (
    WATCH_ADDRESSES as RESPONSE_WATCH_ADDRESSES,
    WATCH_PCS as RESPONSE_WATCH_PCS,
)


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1672.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION_SHA256 = "8d993da929f2cc7810bd97b6eb2188b857004b638d2408b6220bd4103560c933"
FIRST_CAPTURE_FRAME = 1649
LAST_CAPTURE_FRAME = 1700

# Persistent rider fields and broad scratch/input neighborhoods expose every
# actual read/write and any writer outside the preregistered motion ranges.
VELOCITY_WATCH_ADDRESSES = sorted(set(
    list(range(0x04BB, 0x04C7))
    + list(range(0x0BDB, 0x0BE7))
    + list(range(0x0D35, 0x0D3D))
    + list(range(0x0F8F, 0x0FB0))
    + list(range(0x11D1, 0x11E3))
    + list(range(0x11F1, 0x11F7))
    + [0x0300, 0x0302, 0x031D, 0x031F, 0x04C7, 0x0547, 0x0549,
       0x0F1D, 0x0F1F, 0x0F21, 0x0F2B, 0x0F31, 0x0F33, 0x0F41,
       0x0F4B, 0x0F5D, 0x0FF9, 0x1225, 0x1227, 0x127F]
))
WATCH_ADDRESSES = sorted(set(RESPONSE_WATCH_ADDRESSES + VELOCITY_WATCH_ADDRESSES))

# Every byte is deliberately requested. The capture retains only reached
# instruction starts and therefore does not presume decoding or branch reach.
MOTION_PC_RANGE = list(range(0x82A81A, 0x82A9B3))
ORDER_PCS = [
    0x818CF4, 0x818E28, 0x818F7C, 0x818F98,
    0x828A63, 0x828A66, 0x828D9A, 0x828D9D,
    0x828F6B, 0x828F6E, 0x829288, 0x82928B,
    0x82A61F, 0x82A622,
]
WATCH_PCS = sorted(set(RESPONSE_WATCH_PCS + MOTION_PC_RANGE + ORDER_PCS))


def capture_command(manifest: Path, out: Path) -> list[str]:
    resolved = manifest.resolve()
    if resolved == (ROOT / PRIMARY).resolve():
        expected = PRIMARY_SHA256
    elif resolved == (ROOT / VARIATION).resolve():
        expected = VARIATION_SHA256
    else:
        raise ValueError("vertical-velocity capture accepts only preregistered scenarios")
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
        raise ValueError("vertical-velocity replay manifest identity differs")
    command = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(FIRST_CAPTURE_FRAME),
        "--to-frame", str(LAST_CAPTURE_FRAME),
        "--wram-series-range", "0", "0x2200", "--timeout", "180",
        "--report", str(out / "report.json"),
    ]
    for address in WATCH_ADDRESSES:
        command += ["--watch-address", hex(address)]
    for pc in WATCH_PCS:
        command += ["--watch-pc", hex(pc)]
    return command


def capture(manifest: Path, out: Path) -> int:
    if out.exists() and any(out.iterdir()):
        raise ValueError("refusing to overwrite a nonempty capture directory")
    out.mkdir(parents=True, exist_ok=True)
    command = capture_command(manifest, out)
    (out / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    return subprocess.run(command, timeout=200).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    cap = sub.add_parser("capture")
    cap.add_argument("--manifest", type=Path, required=True)
    cap.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "capture":
        return capture(args.manifest, args.out)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
