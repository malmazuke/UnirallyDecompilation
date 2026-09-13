"""M4-15 authenticated full-race differential and restore laboratory."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from . import zoom_zoo_race_reference as reference
from .zoom_zoo_race_explore import timeline
from .zoom_zoo_trial_reference import ROOT,sha,digest
from .zoom_zoo_trial import BUTTONS
from .zoom_zoo_sustained import inventory as sustained_inventory
from ..replay.manifest import derive_script

def inventory():
    items=sustained_inventory()
    items.update(json.loads((ROOT/'tests/manifests/native/zoom-zoo-race-content.reference.json').read_text())['items'])
    return items

def controllers(case,last):
    script=derive_script(json.loads((ROOT/'tests/manifests/replay/race-crawler-zoom-zoo-3300.json').read_text()))
    return timeline(case,last,script)

def restore_frames(rows):
    def word(row,a):return int.from_bytes(bytes.fromhex(row)[a:a+2],'little')
    boundaries={1650,1849,3299,1649+len(rows)-201}
    # Before/after each full landing, direction transition, checkpoint/lap,
    # finish, off-screen entry/exit and animation-start transition.
    watched=[14,395,409,423,425,427,429,433,445,447,449,451,455,511,513,555,563]
    for i in range(1,len(rows)):
        if any(word(rows[i],a)!=word(rows[i-1],a) for a in watched) or any(
            word(rows[i],32+r*128)==0 and word(rows[i],34+r*128)==9 and bytes.fromhex(rows[i])[50+r*128] for r in (0,1)):
            boundaries.update([1648+i,1649+i])
    return sorted(f for f in boundaries if 1649<f<1648+len(rows))

def execute(binary,seed,content,inputs):
    run=subprocess.run([str(binary),'--seed',str(seed),'--content-dir',str(content),'--inputs',str(inputs)],capture_output=True,text=True,cwd=seed.parent,timeout=30)
    if run.returncode:raise ValueError(f'native exit {run.returncode}: {run.stderr}')
    rows=[]
    for line in run.stdout.splitlines():
        frame,row=line.split();data=bytes.fromhex(row)
        if len(data)!=reference.STATE_BYTES or data[:8]!=b'URZZ0003' or int.from_bytes(data[8:12],'little')!=int(frame):raise ValueError('native framing differs')
        rows.append(row)
    return rows

def compare(a,b,contract,binary,content,out,restores=True):
    if out.exists():raise ValueError('fresh comparison output required')
    binary=binary.resolve();binary_identity=sha(binary.read_bytes())
    source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)
    source_identity=sha(subprocess.check_output(['git','diff','HEAD'],cwd=ROOT))
    source,rows=reference.rows(a);repeat,other=reference.rows(b);frozen=json.loads(contract.read_text())
    if source!=repeat or rows!=other:raise ValueError('fresh reference processes differ')
    for key in ['frames','case','rom_sha256','core_sha256','manifest_sha256','timeline_sha256','wram_sha256']:
        if source[key]!=frozen[key]:raise ValueError(f'frozen {key} differs')
    if frozen['state_bytes']!=reference.STATE_BYTES or digest(rows)!=frozen['rows_sha256'] or [sha(bytes.fromhex(r)) for r in rows]!=frozen['state_sha256']:raise ValueError('frozen state differs')
    last=source['frames'][1];timeline_rows=controllers(source['case'],last)
    if digest(timeline_rows)!=frozen['timeline_sha256']:raise ValueError('expanded controller timeline differs')
    binary=binary.resolve();content=content.resolve();boundaries=restore_frames(rows) if restores else []
    with tempfile.TemporaryDirectory(prefix='zoom-race-native-') as directory:
        root=Path(directory);static=root/'content';static.mkdir()
        for name,identity in inventory().items():
            data=(content/name).read_bytes()
            if len(data)!=identity['bytes'] or sha(data)!=identity['sha256']:raise ValueError(f'static content differs: {name}')
            (static/name).write_bytes(data)
        seed=root/'seed.bin';inputs=root/'inputs.txt'
        def prepare(frame):
            seed.write_bytes(bytes.fromhex(rows[frame-1649]));inputs.write_text(''.join(f'{f} {sum(1<<BUTTONS.index(b) for b in timeline_rows[f][0])} 0\n' for f in range(frame+1,last+1)))
        prepare(1649);actual=execute(binary,seed,static,inputs)
        if actual!=rows:
            for i,(x,y) in enumerate(zip(actual,rows)):
                if x!=y:raise ValueError(f'first divergence at {1649+i}, offsets {[j for j,(l,r) in enumerate(zip(bytes.fromhex(x),bytes.fromhex(y))) if l!=r]}')
            raise ValueError('native frame count differs')
        if execute(binary,seed,static,inputs)!=rows:raise ValueError('native fresh process differs')
        for frame in boundaries:
            # The restored bytes are the already-equal uninterrupted native state.
            prepare(frame)
            if execute(binary,seed,static,inputs)!=actual[frame-1649:]:raise ValueError(f'restore differs at {frame}')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT)!=source_head or sha(binary.read_bytes())!=binary_identity or sha(subprocess.check_output(['git','diff','HEAD'],cwd=ROOT))!=source_identity:raise ValueError('source or binary changed during validation')
    result={'status':'passed','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'source_diff_sha256':sha(subprocess.check_output(['git','diff','HEAD'],cwd=ROOT)),
            'case':source['case']['id'],'frames':source['frames'],'updates':last-1649,'state_bytes':reference.STATE_BYTES,
            'rows_sha256':digest(rows),'binary_sha256':sha(binary.read_bytes()),'contract_sha256':sha(contract.read_bytes()),
            'timeline_sha256':frozen['timeline_sha256'],'static_inventory_sha256':digest(inventory()),
            'finish_frames':frozen['finish_frames'],'outcome':frozen['outcome'],'restore_frames':boundaries,
            'native_inputs':'one canonical seed, static content and fixed controllers; no later original state'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    ledger=out.parent/'validation-ledger.jsonl'
    build_info=binary.parents[2]/'lab-build-info.json'
    entry=dict(result,command=__import__('sys').argv,report=str(out),report_sha256=sha(out.read_bytes()),
               build_info=json.loads(build_info.read_text()) if build_info.exists() else None,
               rom_sha256=source['rom_sha256'],core_sha256=source['core_sha256'],
               coverage='two complete native processes and '+str(len(boundaries))+' fresh restores')
    with ledger.open('a') as stream:stream.write(json.dumps(entry,sort_keys=True)+'\n')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference',type=Path,required=True);p.add_argument('--repeat',type=Path,required=True);p.add_argument('--contract',type=Path,required=True);p.add_argument('--binary',type=Path,required=True);p.add_argument('--content-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--no-restores',action='store_true')
    a=p.parse_args();r=compare(a.reference,a.repeat,a.contract,a.binary,a.content_dir,a.out,not a.no_restores);print(json.dumps({k:v for k,v in r.items() if k!='restore_frames'},indent=2));print('restores',len(r['restore_frames']))
if __name__=='__main__':main()
