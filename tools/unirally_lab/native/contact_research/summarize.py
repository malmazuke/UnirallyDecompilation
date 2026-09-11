"""Check narrow semantic contact relations against original call observations.

Captured incoming values are function arguments, never autonomous game state.
Read/modify/write observations with unknown values are not fabricated. Published
values are taken from the caller's observed reads after contact returns.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from ...access.derive import validate_document
from ...replay.manifest import derive_script
from ...reference.bsnes import DEFAULT_OPTIONS

FIELDS = {0xA5:'x',0xA7:'y',0xF33:'unsupported_count',0xFBF:'unsupported_duration',
          0xF4F:'previous_unsupported_count',0xFA9:'vx',0xFAB:'vy',0xF55:'response_a',0xF57:'response_b',0xFAD:'response_impulse',
          0xF17:'surface_angle',0xF2B:'angle_sentinel',0xF51:'reflection',0xF85:'pose',
          0xF73:'displacement_x',0xF23:'mode',0xEED:'previous_x',0xEEF:'previous_y',
          0x1279:'recontact',0xF13:'selected_word',0x2EC:'selected_high',0xF5D:'special',
          0x28:'vertical_correction',0x2A:'angle',0x2C:'horizontal_correction',
          0xEF1:'auxiliary_flag',0x20:'vertical_axis',0x24:'horizontal_axis',0xDE7:'tile_flags'}
PUBLICATION_PCS = {0x818DC7:0xFBF,0x818F1B:0xFBF,0x818E03:0xF33,0x818F57:0xF33,
                   0x818E15:0xA5,0x818F69:0xA5,0x818E1A:0xA7,0x818F6E:0xA7,
                   0x818E1F:0xFA9,0x818F73:0xFA9,0x818E25:0xFAB,0x818F79:0xFAB}


def events_for_frame(access, frame):
    # A multi-byte access can be listed by several watched byte addresses.
    return sorted({tuple(e) for watch in access['watch_addresses'].values()
                   for rows in watch.get(str(frame),{}).values() for e in rows})


def put(memory, address, width, value):
    if value is not None:
        for i in range(width):
            memory[address+i] = (value >> (8*i)) & 255


def word(memory, address):
    return memory[address] | memory[address+1] << 8 if address in memory and address+1 in memory else None


def snapshot(memory):
    result={name:word(memory,address) for address,name in FIELDS.items()}
    result['phase']=memory.get(0x300)
    return result


def validate_identity(access):
    validate_document(access)
    root=Path(__file__).resolve().parents[4]
    path=root/access['manifest']['path']
    raw=path.read_bytes();manifest=json.loads(raw)
    if hashlib.sha256(raw).hexdigest()!=access['manifest']['sha256']:
        raise ValueError('manifest identity differs')
    if access['rom']['sha256']!='a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e':
        raise ValueError('ROM identity differs')
    pinned=json.loads((root/'tests/manifests/replay/race-crawler-dragster-3000-fields.json').read_text())['core']
    for key in ['name','commit','patch_sha256','serialization_method']:
        if access['core'][key]!=pinned[key]:raise ValueError('core identity differs')
    if access['core']['options']!=(DEFAULT_OPTIONS | pinned.get('options',{})):
        raise ValueError('core options differ')
    script=(json.dumps(derive_script(manifest),indent=2,sort_keys=True)+'\n').encode()
    if access['script']['sha256']!=hashlib.sha256(script).hexdigest():raise ValueError('input script differs')
    if access['failure'] is not None or access['instructions']['max_frame_delta']>access['ring_capacity']:
        raise ValueError('capture failure or ring overflow')


def calls(access):
    if access['status'] != 'complete' or access['watch_pcs_truncated']:
        raise ValueError('complete nontruncated capture required')
    frames=access['frames']
    first,last=frames['start'],frames['end']
    count=frames['count']
    if any(type(value) is not int for value in (first,last,count)) or first < 0 or last < first or count != last-first+1:
        raise ValueError('capture requires a nonempty integer frame range with consistent count')
    result=[]
    for frame in range(first,last+1):
        memory={}; active=None; rider=0
        for e in events_for_frame(access,frame):
            seq,pc,kind,address,width,value=e
            if pc==0x818F9D and kind=='write':
                active={'frame':frame,'rider':rider,'input':snapshot(memory),'writes':[], 'published':{}}
                rider+=1;result.append(active)
            put(memory,address,width,value)
            if active is not None:
                if 0x818F98<=pc<=0x8199C6 and kind in ('write','rmw'):
                    active['writes'].append([pc,address,width,value])
                if pc==0x819235:
                    active['support_summary']=value
                    active['classified']=snapshot(memory)
                if pc==0x819810:
                    active['output']=snapshot(memory)
                if pc in PUBLICATION_PCS and kind=='read':
                    active['published'][FIELDS[PUBLICATION_PCS[pc]]]=value
        if rider!=2:
            raise ValueError(f'frame {frame}: expected two caller-identified entries, got {rider}')
    return result


def verify_call(call):
    incoming=call['input'];out=call['output'];published=call['published'];c=call['classified']
    summary=call['support_summary'];checks=[]
    def check(name,expected,actual):
        checks.append({'name':name,'expected':expected,'actual':actual,'passed':expected==actual})
    if not 0 <= incoming['unsupported_count'] <= 9:
        raise ValueError('unsupported count outside primary domain')
    unsupported=bool(summary & 0x80)
    if unsupported:
        branch='unsupported'
        check('counter',min(9,incoming['unsupported_count']+1),published['unsupported_count'])
        check('duration',(incoming['unsupported_duration']+1)&65535,published['unsupported_duration'])
        check('unsupported_velocity_x',incoming['vx'],published['vx'])
        check('unsupported_velocity_y',incoming['vy'],published['vy'])
    elif incoming['unsupported_count']<9:
        branch='continuous'
        check('counter',0,published['unsupported_count'])
        check('duration',0,published['unsupported_duration'])
        # These verified domain guards are part of the narrow formula.
        check('flat_angle_byte',0,c['angle'] & 255)
        check('ordinary_mode',0,c['mode'])
        check('ordinary_special',0,c['special'])
        check('continuous_velocity_x',incoming['vx'],published['vx'])
        check('continuous_velocity_y',0,published['vy'])
    else:
        branch='recontact'
        check('counter',0,published['unsupported_count'])
        check('duration',0,published['unsupported_duration'])
        check('recontact_flag',1,out['recontact'])
        check('sentinel_branch',True,any(w[0]==0x8194CA for w in call['writes']))
        check('recontact_velocity_x',incoming['vx'],published['vx'])
        check('recontact_velocity_y',incoming['vy'],published['vy'])
    check('vertical_axis',0,c['vertical_axis'])
    check('horizontal_axis',0,c['horizontal_axis'])
    check('save_precorrection_x',incoming['x'],out['previous_x'])
    check('save_precorrection_y',incoming['y'],out['previous_y'])
    check('correct_x',incoming['x'],published['x'])
    check('correct_y',(incoming['y']-c['vertical_correction'])&65535,published['y'])
    return branch,checks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--access',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    try:
        raw=args.access.read_bytes();access=json.loads(raw);validate_identity(access);observations=calls(access)
    except (FileNotFoundError,ValueError,KeyError) as error:
        missing=isinstance(error,FileNotFoundError)
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps({'status':'missing' if missing else 'invalid','error':str(error)},indent=2)+'\n')
        print(str(error))
        return 2 if missing else 3
    counts=Counter();failures=[];total=0
    for call in observations:
        branch,checks=verify_call(call);call['branch']=branch;counts[branch]+=1
        total+=len(checks)
        failures += [{'frame':call['frame'],'rider':call['rider'],**c} for c in checks if not c['passed']]
    report={'schema_version':1,'kind':'isolated-contact-relations','access_sha256':hashlib.sha256(raw).hexdigest(),
            'rom':access['rom'],'core':access['core'],'manifest':access['manifest'],'frames':access['frames'],
            'calls':len(observations),'branches':dict(counts),'checks':total,'failures':failures,
            'status':'passed' if not failures else 'failed'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    args.report.with_suffix('.calls.json').write_text(json.dumps(observations,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','calls','branches','checks')}))
    if failures:print(json.dumps(failures[:8]))
    return bool(failures)

if __name__=='__main__':
    raise SystemExit(main())
