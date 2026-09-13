"""M4-15 instruction audit with mandatory controller and whole-WRAM checks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from .zoom_zoo_trial_reference import digest
from .zoom_zoo_race_explore import timeline
from ..replay.manifest import derive_script
from ..reference.worker import inputs_for_frame

def preflight(manifest, reference):
    last=reference['frames'][1]
    if manifest['run']['frames']!=last+1:raise ValueError('audit horizon differs')
    script=derive_script(manifest)
    actual=[[sorted(inputs_for_frame(script,f).get(p,[])) for p in (0,1)] for f in range(last+1)]
    if digest(actual)!=reference['timeline_sha256']:raise ValueError('audit controller timeline differs')
    return digest(actual)

def authenticate_samples(samples,reference):
    first,last=reference['frames']
    observed={r['frame']:r['wram_sha256'] for r in samples['frames']}
    for f,wanted in enumerate(reference['wram_sha256'],first):
        if observed.get(f)!=wanted:raise ValueError(f'audit whole-WRAM differs at {f}')
    if len(reference['wram_sha256'])!=last-first+1:raise ValueError('reference WRAM horizon differs')
    return last-first+1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--from-frame',type=int,required=True);p.add_argument('--to-frame',type=int,required=True)
    p.add_argument('--watch-address',action='append',default=[]);p.add_argument('--watch-pc',action='append',default=[])
    p.add_argument('--frame-image',action='append',default=[]);p.add_argument('--timeout',type=int,default=600)
    a=p.parse_args();reference=json.loads(a.reference.read_text());identity=preflight(json.loads(a.manifest.read_text()),reference)
    if a.out.exists():raise ValueError('fresh audit output required')
    command=[sys.executable,'tools/project.py','access','capture','--manifest',str(a.manifest),'--out',str(a.out),
             '--from-frame',str(a.from_frame),'--to-frame',str(a.to_frame),'--wram-series-range','0','0x2200',
             '--timeout',str(a.timeout),'--report',str(a.out/'report.json')]
    for flag,values in [('--watch-address',a.watch_address),('--watch-pc',a.watch_pc),('--frame-image',a.frame_image)]:
        for value in values:command.extend([flag,value])
    result=subprocess.run(command,timeout=a.timeout+30)
    if result.returncode:raise RuntimeError(f'audit capture failed: {result.returncode}')
    count=authenticate_samples(json.loads((a.out/'samples.json').read_text()),reference)
    (a.out/'authentication.json').write_text(json.dumps({'status':'passed','timeline_sha256':identity,'whole_wram_frames':count,'command':command},indent=2)+'\n')
    print(f'authenticated {count} whole-WRAM frames')
if __name__=='__main__':main()
