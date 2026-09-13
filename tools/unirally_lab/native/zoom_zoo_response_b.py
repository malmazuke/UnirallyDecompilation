"""Preregistered M4-10 response-B producer and recurrence experiment.

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

from .zoom_zoo_composition import (
    WATCH_ADDRESSES as COMPOSITION_WATCH_ADDRESSES,
    WATCH_PCS as COMPOSITION_WATCH_PCS,
)


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1668.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION_SHA256 = "e246ab346d2f9acca21bb0212e0b78c908dea3f94a9d823e809f4ae71bafcc92"
FIRST_CAPTURE_FRAME = 1649
LAST_CAPTURE_FRAME = 1700

# Address watches expose the actual PCs and widths of every read/write. Broad
# scratch/persistent ranges retain adjacent overlap needed to distinguish the
# two response words and orientation state without assigning meanings early.
RESPONSE_WATCH_ADDRESSES = sorted(set(
    list(range(0x0BB3, 0x0BBB))
    + list(range(0x0F51, 0x0F5B))
    + list(range(0x0F7F, 0x0FB0))
    + [0x0300, 0x0302, 0x04C7, 0x0DE7, 0x0DE9, 0x0FF9]
))
WATCH_ADDRESSES = sorted(set(COMPOSITION_WATCH_ADDRESSES + RESPONSE_WATCH_ADDRESSES))

# Watching each byte is deliberate: capture records only actual instruction
# starts, while preregistration does not silently omit a decoded branch target.
PRODUCER_PC_RANGE = list(range(0x82A49F, 0x82A5FA))
POSE_PC_RANGE = list(range(0x83EF54, 0x83F0FB))
ORDER_PCS = [
    0x818B75, 0x818CF4, 0x818F98,  # sampling/contact boundaries
    0x82A49F, 0x82A5F9,            # suspected producer entry/exit
    0x83CD8B, 0x83CD94,            # pose publication before contact
]
WATCH_PCS = sorted(set(COMPOSITION_WATCH_PCS + PRODUCER_PC_RANGE + POSE_PC_RANGE + ORDER_PCS))


def capture_command(manifest: Path, out: Path) -> list[str]:
    resolved = manifest.resolve()
    if resolved == (ROOT / PRIMARY).resolve():
        expected = PRIMARY_SHA256
    elif resolved == (ROOT / VARIATION).resolve():
        expected = VARIATION_SHA256
    else:
        raise ValueError("response-B capture accepts only preregistered scenarios")
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != expected:
        raise ValueError("response-B replay manifest identity differs")
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
