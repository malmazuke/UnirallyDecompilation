"""Additive M4-15 reference state inventory, frozen before native tuning.

The original lap/checkpoint routine $818050-$8182B6 owns the appended rider
words and lap-time slots; $83E81D owns the finish delay. $1225/$1227 remain
provisional pending the continuous read/writer audit. No native equations here.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .zoom_zoo_trial_reference import sha,digest
from .zoom_zoo_sustained import sustained_project

RIDER_WORDS=[('laps_remaining',0xefb),('checkpoint',0x119f),('next_checkpoint',0x11a3),
             ('start_line_latch',0x11a7),('checkpoint_display_countdown',0xfff),('finished',0xeff),
             ('time_minutes',0xe43),('time_tens_seconds',0xe47),('time_seconds',0xe4b),
             ('time_tenths',0xe4f),('time_hundredths',0xe3f)]
GLOBAL_WORDS=[('provisional_1225',0x1225),('provisional_1227',0x1227),('finish_delay',0xf0f)]
STATE_BYTES=517

def project(wram,sram,frame):
    result=bytearray(sustained_project(wram,sram,frame));result[7]=ord('3')
    for rider in (0,1):
        for _,a in RIDER_WORDS:result+=wram[a+2*rider:a+2*rider+2]
    for base in (0x755,0x7bf):result+=sram[base:base+20]
    for a in (0x769,0x7d3):result+=sram[a:a+2]
    for _,a in GLOBAL_WORDS:result+=wram[a:a+2]
    assert len(result)==STATE_BYTES
    return bytes(result)

def rows(path):
    reference=json.loads(path.read_text());result=[]
    with path.with_suffix('.wram').open('rb') as ws,path.with_suffix('.sram').open('rb') as ss:
        for i,f in enumerate(range(reference['frames'][0],reference['frames'][1]+1)):
            w,s=ws.read(0x20000),ss.read(0x2000)
            if sha(w)!=reference['wram_sha256'][i]:raise ValueError('raw WRAM differs')
            result.append(project(w,s,f).hex())
        if ws.read(1) or ss.read(1):raise ValueError('extra raw memory')
    return reference,result

def freeze(a,b,out):
    if out.exists():raise ValueError('fresh freeze required')
    reference,left=rows(a);repeat,right=rows(b)
    if reference!=repeat or left!=right:raise ValueError('fresh references differ')
    finish=[next((1649+i for i,row in enumerate(reference['rows']) if row[r][11]),None) for r in (0,1)]
    if any(f is None for f in finish) or reference['frames'][1]-max(finish)<200:raise ValueError('both finishes and 200 subsequent updates required')
    result={k:reference[k] for k in ['case','frames','rom_sha256','core_sha256','manifest_sha256','timeline_sha256','seed_wram_sha256','wram_sha256']}
    result.update(kind='m4_15_race_freeze',state_bytes=STATE_BYTES,rider_words=RIDER_WORDS,global_words=GLOBAL_WORDS,
                  cartridge_lap_slots=[0x755,0x7bf],cartridge_totals=[0x769,0x7d3],
                  rows_sha256=digest(left),state_sha256=[sha(bytes.fromhex(r)) for r in left],finish_frames=finish,
                  outcome='player_won' if finish[0]<finish[1] else 'player_lost',
                  horizon_rationale='Complete three-lap race and entire 240-update post-player-finish display; 236 updates after opponent finish. Result-screen loading/rendering follows this simulation domain.',
                  escape_criterion='Advance from authentic seed into distinct downstream sections, cross all ordered lap checkpoints and set both finish flags. Initial Left follows the initial marker direction; this leaves the old repeated Right section without a later seed.')
    out.write_text(json.dumps(result,indent=2)+'\n');return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=freeze(a.reference,a.repeat,a.out);print(r['finish_frames'],r['rows_sha256'])
if __name__=='__main__':main()
