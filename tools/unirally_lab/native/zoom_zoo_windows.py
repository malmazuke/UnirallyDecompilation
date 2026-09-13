"""Capture only the predeclared narrow M4-04 producer/consumer windows."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
PRIMARY = "tests/manifests/replay/race-crawler-zoom-zoo-3300.json"
RELEASE = "tests/manifests/replay/race-crawler-zoom-zoo-3300-release-2500-2599.json"
WINDOWS = {
    "start": (PRIMARY, 1649, 1651), "reward": (PRIMARY, 1671, 1673),
    "up-entry": (PRIMARY, 2199, 2201), "up-exit": (PRIMARY, 2259, 2261),
    "release-entry": (RELEASE, 2499, 2501), "release-exit": (RELEASE, 2599, 2601),
}
MANIFEST_SHA256 = {
    PRIMARY: "acd29bfb72aeaad0791923e22e17a791f5c182220f64b6686dd687984411aefd",
    RELEASE: "66399d29b7da16bb52111dc93ada2b62aa14cbf10db4a2644dcbd85bb2c88ff7",
}

# Persistent state plus the shared contact/motion arguments needed to order the
# exposed producers and consumers. Access captures contain only three frames.
WATCH_ADDRESSES = sorted(set([
    0x300,0x302,0x311,0x313,0x315,0x319,0x333,0x32f,0x33f,0x341,
    0x401,0x403,0x405,0x407,0x411,0x413,0x415,0x417,0x419,0x41b,
    0x4bb,0x4bd,0x4bf,0x4c1,0x4c3,0x4c5,0x4c7,0x4cb,0x4cd,0x4d7,0x4d9,0x4db,0x4dd,0x4df,0x4e1,0x4eb,0x4ed,
    0x54b,0x54d,0x54f,0x551,0xb5a,0xb5c,0xb5e,0xb60,0xb62,0xb64,0xb66,0xb68,0xb6a,0xb6c,0xb6e,0xb70,0xb72,0xb74,
    0xba7,0xba9,0xbb3,0xbb5,0xbb7,0xbb9,0xbbb,0xbbd,0xbdb,0xbdd,0xbe3,0xbe5,0xbeb,0xbed,
    0xc6f,0xc75,0xc77,0xc79,0xca7,0xd11,0xd13,0xd25,0xd27,0xd35,0xd37,0xd39,0xd3b,0xd41,0xd43,0xd4f,
    0xde9,0xdeb,0xe9f,0xea1,0xea3,0xea5,0xeff,0xf01,0xf0f,
    0xfc1,0xfc3,0xfc5,0xfc7,0xfc9,0xfcb,0xfcd,0xfcf,0x11c5,0x1203,0x1205,0x1207,0x1209,0x120b,0x120d,0x120f,0x1211,0x1277,0x1279,0x127b,0x127d,0x127f,0x136b,0x136d,
    0x2102,0x770825,0x770750,
] + list(range(0xceb,0xd0b)) + list(range(0xf13,0xfc2,2))))

WATCH_PCS = [
    0x8087ec,0x8087f2,0x82ab36,0x82ab52,
    0x83e0a7,0x83e114,0x83e122,0x83e21f,
    0x8298e4,0x82a627,0x82a6f3,0x82a6f7,0x83ed7b,0x83ef54,0x83ef50,
    0x818cf8,0x818f98,0x819235,0x81982b,0x818e17,0x818f6b,
    0x818d97,0x818d9c,0x818ef1,0x818ef6,0x818aa1,0x818ac0,0x818b66,0x818b6a,0x818cbb,0x818cdd,
    0x81bef1,0x81c219,0x81c2a2,0x81c2ad,0x81c6c9,0x81c6ed,
]


def command(window: str, out: Path) -> list[str]:
    manifest,start,end=WINDOWS[window]; path=ROOT/manifest
    if hashlib.sha256(path.read_bytes()).hexdigest()!=MANIFEST_SHA256[manifest]:
        raise ValueError("accepted replay manifest identity differs")
    result=[sys.executable,"tools/project.py","access","capture","--manifest",manifest,"--out",str(out),
            "--from-frame",str(start),"--to-frame",str(end),"--timeout","180","--report",str(out/"report.json")]
    for address in WATCH_ADDRESSES: result += ["--watch-address",hex(address)]
    for pc in WATCH_PCS: result += ["--watch-pc",hex(pc)]
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--window",choices=WINDOWS,required=True);parser.add_argument("--out",type=Path,required=True);args=parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):parser.error("refusing to overwrite a nonempty capture directory")
    args.out.mkdir(parents=True,exist_ok=True)
    try:cmd=command(args.window,args.out)
    except (OSError,ValueError) as error:parser.error(str(error))
    (args.out/"command.json").write_text(json.dumps(cmd,indent=2)+"\n")
    return subprocess.run(cmd,timeout=200).returncode


if __name__ == "__main__":raise SystemExit(main())
