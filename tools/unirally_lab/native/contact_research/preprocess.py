"""Primary-domain collision sample preprocessing and reduction experiment.

This is an isolated semantic research model. Unsupported geometry is rejected;
there is no processor, instruction decoding, or autonomous movement simulation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from ..probe_sampling import capture_cases, validate_primary_access
from .summarize import calls


def load_content(manifest_path, directory, required):
    manifest=json.loads(Path(manifest_path).read_text()); result={}
    for item in manifest['items']:
        if item['id'] not in required:continue
        raw=(Path(directory)/(item['id']+'.bin')).read_bytes()
        if len(raw)!=item['expected']['length'] or hashlib.sha256(raw).hexdigest()!=item['expected']['sha256']:
            raise ValueError('content identity differs: '+item['id'])
        result[item['id']]=raw
    if set(result)!=set(required):raise ValueError('missing content item')
    return result


def expand_points(pose, reflected, poses, templates):
    record=poses[pose*8:pose*8+8]
    if len(record)!=8:raise ValueError('pose bounds')
    selector=int.from_bytes(record[6:8],'big')
    offset=(selector<<4)&65535
    template=templates[offset:offset+16]
    if len(template)!=16:raise ValueError('template bounds')
    points=[(record[0],record[1]),(record[2],record[3])]
    points += [((template[i]+record[4])&255,(template[i+1]+record[5])&255) for i in range(0,16,2)]
    return [((((47-x)&255) if reflected else x)+8 & 255,y) for x,y in points]


def preprocess(samples, points, x, y, columns, flags):
    result=[]
    for raw,(px,py) in zip(samples,points,strict=True):
        if raw&0x3ff==0:
            result.append((160,0,0));continue
        tile=((raw&0x3f0)>>2)+((raw&15)>>1)
        if raw&0xc000 or flags[tile]&1:
            raise ValueError('outside primary vertical unreflected tile geometry')
        column=((px+(x&15))&15)
        local_y=(py+(y&15))&15
        height,angle=columns[tile*32+column*2:tile*32+column*2+2]
        penetration=160 if height==160 else (local_y-((height-1)&255))&255
        result.append((penetration,angle,raw))
    return result


def reduce_samples(samples,flags):
    # Point zero has a separate original branch, unentered in this domain.
    if samples[0][0]!=160:raise ValueError('first probe support outside primary domain')
    selected=0;summary=255;correction=0;selected_high=0;angle=224
    for index,(penetration,slope,raw) in enumerate(samples[1:],start=1):
        if penetration==160:
            if raw&511 and selected==0:selected=raw
            continue
        if penetration>=128 or slope!=0 or raw&1:
            raise ValueError('non-flat or negative sample outside primary domain')
        # Original compares using N of u8 subtraction, not host signed compare.
        if (penetration-summary)&128==0:
            summary=penetration
            if selected==0:selected=raw
            if index<2:raise ValueError('second-probe support outside primary domain')
            selected_high=raw>>8
            angle=slope
        correction=max(correction,penetration)
    tile=((selected&0x3f0)>>2)+((selected&15)>>1)
    return {'support_summary':summary,'selected_word':selected,'selected_high':selected_high,
            'angle_byte':angle,'vertical_correction':correction,'tile_flags':flags[tile]}


def main():
    p=argparse.ArgumentParser();p.add_argument('--sampling-access',type=Path,required=True)
    p.add_argument('--contact-access',type=Path,required=True);p.add_argument('--pose-content',type=Path,required=True)
    p.add_argument('--tile-content',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    args=p.parse_args();access=json.loads(args.sampling_access.read_text());validate_primary_access(access)
    cases=capture_cases(access,1024);contact_access=json.loads(args.contact_access.read_text());validate_primary_access(contact_access);contact=calls(contact_access)
    poses=load_content('tests/manifests/native/movement-sampling.content.json',args.pose_content,['collision-poses','collision-templates'])
    tiles=load_content('tests/manifests/native/contact-research/contact/tile-tables.content.json',args.tile_content,['tile-tables','tile-flags'])
    failures=[];checks=0
    for case,call in zip(cases,contact,strict=True):
        if (case['frame'],case['rider'])!=(call['frame'],call['rider']):raise ValueError('call ordering differs')
        pose,reflect,x,y,_=case['input']
        points=expand_points(pose,reflect,poses['collision-poses'],poses['collision-templates'])
        samples=preprocess(case['expected'],points,x,y,tiles['tile-tables'],tiles['tile-flags'])
        actual=reduce_samples(samples,tiles['tile-flags'])
        expected={k:(call['support_summary'] if k=='support_summary' else call['classified']['angle']&255 if k=='angle_byte' else call['classified'][k]) for k in actual}
        for key,value in actual.items():
            checks+=1
            if value!=expected[key]:failures.append({'frame':case['frame'],'rider':case['rider'],'field':key,'computed':value,'observed':expected[key]})
    report={'kind':'isolated-primary-preprocessing','calls':len(cases),'checks':checks,'failures':failures,'status':'passed' if not failures else 'failed',
            'inputs':{str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.sampling_access,args.contact_access]}}
    args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report if failures else {k:report[k] for k in ['status','calls','checks']}))
    return bool(failures)

if __name__=='__main__':raise SystemExit(main())
