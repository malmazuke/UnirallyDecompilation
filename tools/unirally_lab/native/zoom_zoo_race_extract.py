"""Extract the identity-bound M4-15 static runtime; no captured dynamic state."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .zoom_zoo_sustained import extract_content
from .zoom_zoo_trial_reference import ROOT,ROM_SHA,sha
from .zoom_zoo_race import inventory

def extract(out,core):
    if out.exists():raise ValueError('fresh extraction directory required')
    rom=Path((ROOT/'local/rom-location.txt').read_text().strip()).read_bytes()
    if sha(rom)!=ROM_SHA:raise ValueError('ROM identity differs')
    additions=json.loads((ROOT/'tests/manifests/native/zoom-zoo-race-content.reference.json').read_text())['items']
    extracted={}
    for name,item in additions.items():
        data=rom[item['file_offset']:item['file_offset']+item['bytes']]
        if len(data)!=item['bytes'] or sha(data)!=item['sha256']:raise ValueError(f'static extraction differs: {name}')
        extracted[name]=data
    extract_content(out,core)
    for name,data in extracted.items():(out/name).write_bytes(data)
    result={'status':'passed','rom_sha256':ROM_SHA,'core_sha256':sha(core.read_bytes()),'items':inventory()}
    (out/'extraction-report.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--core',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();result=extract(a.out,a.core.resolve());print('passed',len(result['items']),'static inputs')
if __name__=='__main__':main()
