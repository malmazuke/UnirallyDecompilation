"""Capture ordered motion dependencies without opening movement withheld cases."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

WATCH_ADDRESSES = [0x300,0x302,0x333,0x31b,0x32f,0x4c7,0x54d,0xc6f,0xc75,0xfc7,0x1275,0x1277,0xa5,0xa7]
WATCH_ADDRESSES += [0xe7b,0xfe3,0xff9,0x401,0x403,0x405,0x407,0x11f1,0x11d1,0x11d7,0x11f7,0x11dd,0x11c5,0x325,0x327,0xc6d,0xc73,0xb95,0x770825,0x31d,0x31f]
WATCH_ADDRESSES += [0x33f,0x341,0x136b,0x136d,0x1203,0x1205,0x1207,0x1209,0x120b,0x120d,0x120f,0x1211,0x433,0x435,0x42f,0x431,0x42b,0x42d,0x230,0x232,0x234,0x236,0x260,0x262,0x264,0x266,0x26a,0xd11,0xd13,0xca7,0x11db,0x11e1,0x7e2102]
WATCH_ADDRESSES += list(range(0xceb,0xd0b))
WATCH_ADDRESSES += list(range(0xf13, 0xfc3, 2))
WATCH_PCS = [0x83e082,0x83e114,0x83e122,0x83e125,0x83e130,0x83e140,0x83e167,0x83e21f,0x83e253,0x82a914,0x82a921,0x82a92d,0x82a935,0x82a965,0x82a9aa,0x82a61f,0x82a6f7,0x838000,0x83ed7b,0x83ef54,0x83efff,0x83f09b,0x83ef50,0x818f98,0x818d97,0x818ef1,0x819e1b]

def command(manifest, out, start=1576, end=1618):
    result=[sys.executable,'tools/project.py','access','capture','--manifest',str(manifest),'--out',str(out),'--from-frame',str(start),'--to-frame',str(end),'--wram-series-range','0','0x2200','--timeout','180','--report',str(out/'report.json')]
    for address in WATCH_ADDRESSES: result.extend(['--watch-address',hex(address)])
    for pc in WATCH_PCS: result.extend(['--watch-pc',hex(pc)])
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,default=Path('tests/manifests/replay/race-crawler-dragster-3000-fields.json'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--from-frame',type=int,default=1576)
    p.add_argument('--to-frame',type=int,default=1618)
    a=p.parse_args()
    if 'withheld' in str(a.manifest):p.error('withheld movement cases are sealed')
    a.out.mkdir(parents=True,exist_ok=True)
    cmd=command(a.manifest,a.out,a.from_frame,a.to_frame)
    (a.out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    return subprocess.run(cmd,timeout=200).returncode
if __name__=='__main__':raise SystemExit(main())
