"""Reproduce contact research observations; no native simulation is performed."""
import argparse
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default='tests/manifests/replay/race-crawler-dragster-3000-fields.json')
    parser.add_argument('--out', required=True)
    parser.add_argument('--from-frame', type=int, default=1576)
    parser.add_argument('--to-frame', type=int, default=1618)
    parser.add_argument('--compact', action='store_true')
    args = parser.parse_args()
    # Scratch inputs, contact output/persistence, and caller publication slots.
    addresses = list(range(0x20, 0x30)) + list(range(0xA3, 0xAA))
    addresses += list(range(0x230, 0x2F2)) + list(range(0xF13, 0xFC2))
    addresses += [0x300,0x302,0x333,0x4EF,0xDE7,0xEED,0xEEF,0xEF1,0xFF9,0x1279,0x132B,0x1349]
    pcs = [0x818F98,0x81982B,0x81923A,0x819246,0x8192CE,0x8194C5,
           0x81924E,0x819278,0x81930C,0x8194CA,0x81960A,0x81970B,
           0x81980C,0x818DBF,0x818F13,0x81982C,0x8198DC]
    if args.compact:
        addresses = [0xA3,0xA5,0xA7,0x20,0x24,0x28,0x2A,0x2C,0x2BE,0x2C0,0x2EC,
                     0xF13,0xF17,0xF23,0xF2B,0xF33,0xF4F,0xF51,0xF55,0xF57,
                     0xF5D,0xF73,0xF85,0xFA9,0xFAB,0xFAD,0xFBF,0xDE7,0xEED,0xEEF,0xFF9,0x1279]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cmd = ['python3','tools/project.py','access','capture','--manifest',args.manifest,
           '--out',str(out),'--from-frame',str(args.from_frame),'--to-frame',str(args.to_frame),
           '--wram-series-range','0','0x2200','--timeout','180','--report',str(out/'report.json')]
    for address in sorted(set(addresses)):
        cmd += ['--watch-address',hex(address)]
    for pc in pcs:
        cmd += ['--watch-pc',hex(pc)]
    (out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    return subprocess.call(cmd)

if __name__ == '__main__':
    raise SystemExit(main())
