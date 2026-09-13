"""Capture the preregistered M4-09 position/contact composition experiment.

This additive research surface observes the position integrator, the reached
pre-integration Y adjustment, sampling, and contact in one ordered window.  It
does not modify or invoke production native gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from .zoom_zoo_contact import WATCH_ADDRESSES as CONTACT_WATCH_ADDRESSES
from .zoom_zoo_contact import WATCH_PCS as CONTACT_WATCH_PCS
from .zoom_zoo_position import WATCH_ADDRESSES as POSITION_WATCH_ADDRESSES
from .zoom_zoo_position import WATCH_PCS as POSITION_WATCH_PCS


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
VARIATION = "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1666.json"
PRIMARY_SHA256 = "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd"
VARIATION_SHA256 = "3b8e34076366e247b43e05a94cbcacfe3a8fa56f809a8ab3d250acec28fb013b"
FIRST_CAPTURE_FRAME = 1649
FIRST_CALL_FRAME = 1650
LAST_CALL_FRAME = 1700

# $82:A96F--A9B2 is decoded at 16-bit accumulator/index width.  Every reached
# instruction is watched, including both early exits and the final $A7 store.
Y_ADJUSTMENT_PCS = [
    0x82A96F, 0x82A971, 0x82A974, 0x82A976, 0x82A979, 0x82A97C,
    0x82A97E, 0x82A981, 0x82A984, 0x82A986, 0x82A989, 0x82A98B,
    0x82A98E, 0x82A991, 0x82A993, 0x82A994, 0x82A995, 0x82A996,
    0x82A997, 0x82A998, 0x82A99A, 0x82A99D, 0x82A99E, 0x82A9A0,
    0x82A9A1, 0x82A9A2, 0x82A9A3, 0x82A9A6, 0x82A9A7, 0x82A9AA,
    0x82A9AD, 0x82A9AF, 0x82A9B0, 0x82A9B2,
]

# The two indexed predicate words are $0547/$0549 because caller selector
# $0FF9 is preregistered as 0 then 2.  $0F4B, vertical velocity $0FAB, direct
# page scratch $00/$02 and the transient position $A7 close the reached helper.
WATCH_ADDRESSES = sorted(set(
    CONTACT_WATCH_ADDRESSES + POSITION_WATCH_ADDRESSES
    + [0x0000, 0x0002, 0x00A7, 0x0547, 0x0549, 0x0F4B, 0x0FAB, 0x0FF9]
))

# Caller boundaries establish helper -> integrator -> collision-point expansion
# -> track sampling -> contact for player and opponent in their original order.
WATCH_PCS = sorted(set(
    CONTACT_WATCH_PCS + POSITION_WATCH_PCS + Y_ADJUSTMENT_PCS
    + [0x828C81, 0x828C84, 0x828C87, 0x82916B, 0x82916E, 0x829171,
       0x82A61F, 0x82A622, 0x819E1B, 0x818B75, 0x818F98]
))


def capture_command(manifest: Path, out: Path) -> list[str]:
    resolved = manifest.resolve()
    if resolved == (ROOT / PRIMARY).resolve():
        expected = PRIMARY_SHA256
    elif resolved == (ROOT / VARIATION).resolve():
        expected = VARIATION_SHA256
    else:
        raise ValueError("composition capture accepts only preregistered scenarios")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if digest != expected:
        raise ValueError("composition replay manifest identity differs")
    command = [
        sys.executable, "tools/project.py", "access", "capture",
        "--manifest", str(manifest), "--out", str(out),
        "--from-frame", str(FIRST_CAPTURE_FRAME),
        "--to-frame", str(LAST_CALL_FRAME),
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--manifest", type=Path, required=True)
    capture_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        return capture(args.manifest, args.out)
    except FileNotFoundError as error:
        print(error, file=sys.stderr); return 2
    except (OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr); return 3
    except subprocess.TimeoutExpired as error:
        print(error, file=sys.stderr); return 4


if __name__ == "__main__":
    raise SystemExit(main())
