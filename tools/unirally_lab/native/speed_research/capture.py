"""Reproduce the bounded primary speed-clamp capture."""
import json
from pathlib import Path
import subprocess
import sys

ADDRESSES = [0xff9, 0x547, 0x549, 0x1225, 0x1227, 0xfa9, 0xfab, 0x1513, 0x150b,
             0x11d7, 0x11dd, 0x11f1, 0xc6d, 0xfcd, 0xfcf, 0x1283, 0x343, 0x345,
             0x1281, 0x11d3, 0x127f, 0xf21, 0x77074a, 0x00, 0x0200]


def command(out):
    result = [sys.executable, "tools/project.py", "access", "capture", "--manifest",
              "tests/manifests/replay/race-crawler-dragster-3000-fields.json", "--out", str(out),
              "--from-frame", "1534", "--to-frame", "2999", "--wram-series-range", "0", "0x1600",
              "--timeout", "180", "--report", str(out / "report.json")]
    for address in ADDRESSES:
        result += ["--watch-address", hex(address)]
    for pc in [0x82a6fa, 0x82a627]:
        result += ["--watch-pc", hex(pc)]
    return result


if __name__ == "__main__":
    out = Path("artifacts/speed/primary")
    out.mkdir(parents=True, exist_ok=True)
    cmd = command(out)
    (out / "command.json").write_text(json.dumps(cmd, indent=2) + "\n")
    raise SystemExit(subprocess.run(cmd, timeout=200).returncode)
