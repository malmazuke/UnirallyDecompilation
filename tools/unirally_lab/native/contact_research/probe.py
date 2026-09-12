"""Compare native sampling/contact with original calls on captured motion input.

No expected output is fed to native code. Persistent inputs are captured for
this isolated component experiment; this cannot stand in for native gameplay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from ... import report as reportmod
from ..probe_sampling import NativeProbeFailure, run_probe
from .preprocess import load_content
from .summarize import calls, validate_identity

OUTPUT_FIELDS = [
    'x','y','vx','vy','response_a','response_b','orientation_impulse',
    'unsupported_count','previous_unsupported_count','unsupported_duration',
    'previous_uncorrected_x','previous_uncorrected_y','surface_angle',
    'angle_unspecified','auxiliary_flag','selected_word','selected_high','recontact',
    'summary.supported','summary.penetration','summary.angle',
    'summary.selected_word','summary.selected_high','summary.tile_flags',
]


def prepare_rows(access):
    observations=calls(access); rows=[]; expected=[]
    for call in observations:
        incoming=call['input'];out=call['output'];published=call['published'];c=call['classified']
        # This context byte is read by the original every frame and is stable
        # throughout that frame. It is neither gameplay output nor a guessed
        # zero. All duplicate byte-watch observations have the same value.
        option_reads=access['watch_addresses'][str(0x770750)][str(call['frame'])]['r']
        options={row[5]&255 for row in option_reads if row[5] is not None}
        if len(options)!=1:raise ValueError('missing or changing cartridge option context')
        if incoming['reflection'] not in [0,1] or incoming['angle_sentinel'] not in [0,1]:
            raise ValueError('invalid incoming flag word')
        values=[incoming['pose'],incoming['reflection'],1024,
                incoming['x'],incoming['y'],incoming['vx'],incoming['vy'],
                incoming['displacement_x'],incoming['response_a'],incoming['response_b'],incoming['response_impulse'],
                incoming['unsupported_count'],incoming['unsupported_duration'],incoming['previous_x'],incoming['previous_y'],
                incoming['surface_angle'],incoming['angle_sentinel'],incoming['auxiliary_flag'],
                incoming['phase'],call['rider'],incoming['mode'],next(iter(options))]
        if any(type(v) is not int or not 0<=v<=65535 for v in values):
            raise ValueError('missing or invalid captured component input')
        rows.append(values)
        angle=c['angle']&255
        angle_word=angle if angle<128 else angle+0xFF00
        output=[published['x'],published['y'],published['vx'],published['vy'],
                out['response_a'],out['response_b'],out['response_impulse'],
                published['unsupported_count'],out['previous_unsupported_count'],published['unsupported_duration'],
                out['previous_x'],out['previous_y'],out['surface_angle'],out['angle_sentinel'],out['auxiliary_flag'],
                out['selected_word'],out['selected_high'],out['recontact'],
                int(call['support_summary']<128),c['vertical_correction'],angle_word,
                c['selected_word'],c['selected_high'],c['tile_flags']]
        if any(type(v) is not int or not 0<=v<=65535 for v in output):
            raise ValueError('missing or invalid original output')
        expected.append(output)
    return observations,rows,expected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--access',type=Path,required=True)
    parser.add_argument('--pose-content',type=Path,required=True)
    parser.add_argument('--tile-content',type=Path,required=True)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args();rep=reportmod.Report(sys.argv,task_id='M2-01A-contact');status=0
    try:
        for name,path in [('access',args.access),('native_probe',args.probe)]:
            rep.add_input(name,path,hashlib.sha256(path.read_bytes()).hexdigest())
        access=json.loads(args.access.read_text());validate_identity(access)
        rep.add_check('original_identity','passed',detail='pinned ROM/core, manifest and inputs; complete nonempty capture')
        content_paths=[]
        for manifest,directory,required in [
            ('tests/manifests/native/movement-sampling.content.json',args.pose_content,['track-data','collision-poses','collision-templates']),
            ('tests/manifests/native/contact-research/contact/tile-tables.content.json',args.tile_content,['tile-tables','tile-flags'])]:
            content=load_content(manifest,directory,required)
            for name in required:
                path=directory/(name+'.bin');content_paths.append(path)
                rep.add_input(name,path,hashlib.sha256(content[name]).hexdigest())
        observations,rows,expected=prepare_rows(access)
        stdin=''.join(' '.join(map(str,row))+'\n' for row in rows)
        stdout,actual=run_probe([str(args.probe.resolve()),*map(str,content_paths)],stdin,len(rows),len(OUTPUT_FIELDS))
        rep.add_check('native_probe_complete','passed',detail=f'{len(rows)} calls, {len(OUTPUT_FIELDS)} outputs per call')
        failure=None
        for call,want,got in zip(observations,expected,actual,strict=True):
            for field,reference,native in zip(OUTPUT_FIELDS,want,got,strict=True):
                if reference!=native:
                    failure={'frame':call['frame'],'rider':call['rider'],'field':field,'original':reference,'native':native}
                    break
            if failure:break
        rep.data['first_divergence']=failure
        rep.add_check('contact_outputs_equal','passed' if failure is None else 'failed',detail=f'{len(rows)*len(OUTPUT_FIELDS)} values; first divergence {failure}')
        rep.data['domain']='isolated captured-input component; no autonomous movement agreement'
        output_path=args.report.with_suffix('.native.txt');output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(stdout)
        rep.add_artifact('native_outputs',output_path)
        status=int(failure is not None)
    except FileNotFoundError as error:
        rep.add_check('prerequisite','missing',detail=str(error));status=2
    except NativeProbeFailure as error:
        rep.add_check('native_execution','failed',detail=str(error));status=1
    except (ValueError,KeyError) as error:
        rep.add_check('experiment_input','failed',detail=str(error));status=3
    except subprocess.TimeoutExpired as error:
        rep.add_check('native_execution','timeout',detail=str(error));status=4
    rep.finish('passed' if status==0 else 'failed');rep.write(args.report)
    print(f'contact probe status={status}; report={args.report}')
    if rep.data.get('first_divergence'):print(rep.data['first_divergence'])
    return status

if __name__=='__main__':raise SystemExit(main())
