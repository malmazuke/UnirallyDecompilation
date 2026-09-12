"""Create the identity-bound end-1533 semantic seed and static runtime.

This is preparation only. It accepts the one original WRAM/SRAM observation
approved by R-0011-motion, extracts named semantic fields, and copies the exact
static inventory. The resulting native process never receives either memory
dump or the ROM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[3]
ROM_SHA = "a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e"
WRAM_SHA = "f87f42ddfcdae3010bef8da6823216664f655cb5fcdb54af8b7bbd7876605fdf"
SRAM_SHA = "774410886d8e20e123924251c49230fb94a3bfb51438497ea070ba3421b889eb"
REPORT_SHA = "2e187dc5cba609ffc8ad611eeeaffd857528f13677cf2167c13bd3b6f685d49c"
STATIC_SIZES = {
    "track-data.bin":33815,"collision-poses.bin":32768,"collision-templates.bin":17249,
    "progress-transitions.bin":80,"tile-tables.bin":640,"tile-flags.bin":20,
    "speed-masks.bin":9,"speed-decrements.bin":18,"pose-slopes.bin":128,
    "displacement-table.bin":512,"rotation-reward.bin":2,"rotation-class.bin":1,
}

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def word(data: bytes, address: int) -> int: return int.from_bytes(data[address:address+2],"little")
def flag(value: int) -> int:
    if value not in (0,1): raise ValueError("seed flag is outside the recovered binary domain")
    return value

class Writer:
    def __init__(self): self.data=bytearray(b"URMV0001")
    def u8(self,*values): self.data.extend(values)
    def u16(self,*values):
        for value in values:self.data.extend(struct.pack("<H",value))
    def u32(self,value):self.data.extend(struct.pack("<I",value))

def rider_seed(w: Writer, ram: bytes, rider: int) -> None:
    p=2*rider
    # ContactMotion, then RiderContactState: the same records used by the
    # reviewed contact component, with no duplicate velocity/response state.
    w.u16(word(ram,0x415+p),word(ram,0x419+p),word(ram,0x4bb+p),word(ram,0x4bf+p),
          word(ram,0xbbb+p),word(ram,0xbb3+p),word(ram,0xbb7+p),word(ram,0xd35+p))
    w.u16(word(ram,0x54b+p),word(ram,0x54f+p),word(ram,0xfc1+p),word(ram,0x4d7+p),
          word(ram,0x4db+p),word(ram,0xb6e+p),word(ram,0x4df+p),word(ram,0xe9f+p))
    w.u8(flag(word(ram,0x4eb+p)),ram[0xb72+p],flag(word(ram,0x127b+p)))
    # Speed modifiers and progress recurrence.
    w.u16(word(ram,0x11d9+p),word(ram,0x11df+p),word(ram,0x343+p),
          word(ram,0xfc5+p),word(ram,0xfc9+p),word(ram,0xfcd+p))
    w.u8(0) # rejection is transient and false at the established stationary seed
    # Jump and pose/animation state. The three displacement-history words are
    # zero at this stationary seed; later states serialize their evolved values.
    w.u16(word(ram,0xd39+p),word(ram,0x4c3+p),word(ram,0xbdb+p),word(ram,0xbe3+p),
          word(ram,0x4cb+p),word(ram,0xde9+p),word(ram,0xb62+p),word(ram,0xb6a+p),
          word(ram,0xb5a+p),word(ram,0xb5e+p),word(ram,0xb66+p),word(ram,0xb76+p),
          word(ram,0x411+p),0,0,0,word(ram,0xb9f+p),word(ram,0xfe5+p))
    w.u8(flag(word(ram,0xea3+p)))
    w.u16(word(ram,0xd25+p),word(ram,0x1203+p),word(ram,0x1207+p),
          word(ram,0x120b+p),word(ram,0x120f+p))
    w.u8(flag(word(ram,0x136b+p)),flag(word(ram,0x33f+p)))
    w.u16(word(ram,0x401+p),word(ram,0x405+p),word(ram,0xbeb+p),word(ram,0xd41+p),
          word(ram,0x11f3+p),word(ram,0xc77+p))

def canonical_seed(wram: bytes, sram: bytes) -> bytes:
    if len(wram)!=0x20000 or len(sram)!=0x2000: raise ValueError("seed dumps must be 128 KiB WRAM and 8 KiB SRAM")
    out=Writer(); out.u32(1533); out.u8(wram[0x311],wram[0x313],wram[0x315],wram[0x319])
    for rider in (0,1): rider_seed(out,wram,rider)
    out.u16(*(word(wram,address) for address in (0xe19,0xe1d,0xe21,0xe25,0xe29)))
    out.u16(word(wram,0xc6f),word(wram,0xc75),word(wram,0x1277))
    out.data.extend(wram[0xceb:0xd0b]); out.u8(wram[0xd11],wram[0xd13])
    out.u16(word(wram,0xca7),word(sram,0x825)); out.u8(wram[0x2102])
    out.u16(word(wram,0x11c5)); out.u8(wram[0x300],wram[0x302],wram[0x4c7],wram[0x127f])
    if len(out.data)!=295: raise AssertionError("canonical movement width changed")
    return bytes(out.data)

def validate_observation(wram_path:Path,sram_path:Path,report_path:Path)->tuple[bytes,bytes]:
    if sha(wram_path)!=WRAM_SHA or sha(sram_path)!=SRAM_SHA or sha(report_path)!=REPORT_SHA:
        raise ValueError("seed observation identity differs from R-0011-motion")
    report=json.loads(report_path.read_text()); wram=wram_path.read_bytes(); sram=sram_path.read_bytes()
    required={"schema_version":1,"kind":"original_single_seed","after_frame":1533,
              "rom_sha256":ROM_SHA,"wram_sha256":WRAM_SHA,"cartridge_sha256":SRAM_SHA,
              "cartridge_bytes":8192,"feature_total_770825":0,"event_one_weight_7e2102":4}
    if any(report.get(k)!=v for k,v in required.items()):raise ValueError("seed report metadata differs from R-0011-motion")
    if word(sram,0x825)!=0 or wram[0x2102]!=4:raise ValueError("direct SRAM/WRAM seed guards differ")
    return wram,sram

def prepare(wram_path:Path,sram_path:Path,report_path:Path,bindings:list[str],out_dir:Path)->dict:
    wram,sram=validate_observation(wram_path,sram_path,report_path)
    sources={}
    for binding in bindings:
        name,sep,value=binding.partition("=")
        if not sep or name not in STATIC_SIZES or name in sources:raise ValueError("--content requires each exact name=path once")
        sources[name]=Path(value)
    if set(sources)!=set(STATIC_SIZES):raise ValueError("complete 12-file static content inventory is required")
    if out_dir.exists() and any(out_dir.iterdir()):raise ValueError("refusing to overwrite a nonempty runtime directory")
    content=out_dir/"content"; content.mkdir(parents=True,exist_ok=True)
    files=[]
    for name in STATIC_SIZES:
        source=sources[name]
        if source.stat().st_size!=STATIC_SIZES[name]:raise ValueError(f"wrong static content size: {name}")
        target=content/name; shutil.copyfile(source,target)
        files.append({"name":name,"size":STATIC_SIZES[name],"sha256":sha(target)})
    seed=out_dir/"seed.bin"; seed.write_bytes(canonical_seed(wram,sram))
    def relative(path):return str(path.resolve().relative_to(ROOT.resolve()))
    runtime={"schema_version":1,"rom_sha256":ROM_SHA,
             "seed":{"path":relative(seed),"sha256":sha(seed),"frame":1533},
             "content_dir":relative(content),"files":files}
    (out_dir/"runtime.json").write_text(json.dumps(runtime,indent=2)+"\n")
    return runtime

def main()->None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wram",type=Path,required=True); parser.add_argument("--cartridge",type=Path,required=True)
    parser.add_argument("--seed-report",type=Path,required=True); parser.add_argument("--content",action="append",default=[])
    parser.add_argument("--out-dir",type=Path,default=ROOT/"local/native/dragster")
    args=parser.parse_args(); print(json.dumps(prepare(args.wram,args.cartridge,args.seed_report,args.content,args.out_dir),indent=2))

if __name__=="__main__":main()
