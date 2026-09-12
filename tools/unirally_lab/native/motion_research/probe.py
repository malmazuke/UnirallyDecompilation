"""Compare isolated pose/jump contracts with ordered original call arguments."""
import argparse
import hashlib
import json
from pathlib import Path
from .contracts import pose_update, jump_update, integrate_position, gravity_update, rolling_mode, rotation_input, opponent_inputs, completed_rotation, throttle_update, stationary_animation_override, common_motion_reset, reward_queue_step
from ...access.derive import validate_document, wram_offset
from ...replay.manifest import derive_script
from ...reference.bsnes import DEFAULT_OPTIONS
from .capture import WATCH_ADDRESSES

POSE_FIELDS=[0xf53,0xfa3,0xf81,0xfad,0xf71,0xf6f,0xf6d,0xf99,0xf73,0xf9f,0xf8d,0xf4d,0xfe3,0xf9b,0xf9d,0xfa1]
JUMP_FIELDS=[0xf91,0xf93,0xfa5,0xfab]

# Captured word interface, including both rider offsets and scalar globals.
WORD_ADDRESSES = set(range(0xf13,0xfc3,2)) | set(range(0x1203,0x1213,2)) | {
    0xa5,0xa7,0x300,0x302,0x31b,0x31d,0x31f,0x327,0x32b,0x32f,0x333,
    0x33f,0x341,0x359,0x35b,0x401,0x403,0x405,0x407,0x42b,0x42d,
    0x42f,0x431,0x433,0x435,0x4bd,0x4c1,0x4c7,0x547,0x549,0x54d,
    0xb70,0xb95,0xc6d,0xc6f,0xc73,0xc75,0xc77,0xc79,0xca7,0xd11,
    0xd13,0xd4f,0xdeb,0xe7b,0xfc7,0xfcd,0xfcf,0xfe3,0xff9,0x11d1,
    0x11d7,0x11db,0x11dd,0x11e1,0x11f1,0x1249,0x1275,0x1277,0x136b,0x136d,0x2102,
}

def events(document,frame):
    return sorted((row[0],int(address),kind,row) for address,frames in document['watch_addresses'].items() for kind,rows in frames.get(str(frame),{}).items() for row in rows)

class UnknownWord:
    def __bool__(self):raise ValueError('contract reads an unresolved captured word')
    def __eq__(self,other):raise ValueError('contract compares an unresolved captured word')


def snapshot(series, frame, ordered, sequence):
    memory=list(series[(frame-1)*0x2200:frame*0x2200])
    for seq,address,kind,row in ordered:
        if seq>=sequence:break
        if kind!='w':continue
        _,pc,_,actual,width,value=row
        actual=wram_offset(actual)
        if actual is None or actual>=len(memory):continue
        memory[actual:actual+width]=[None]*width if value is None else list(value.to_bytes(width,'little'))
    return {a:UnknownWord() if None in memory[a:a+2] else int.from_bytes(memory[a:a+2],'little') for a in WORD_ADDRESSES}

def validate_identity(access):
    root=Path(__file__).resolve().parents[4]
    allowed={"tests/manifests/replay/race-crawler-dragster-3000-fields.json", "tests/manifests/native/contact-research/motion/release-before-jump.json"}
    relative=access['manifest']['path']
    if relative not in allowed:raise ValueError('capture is outside the preregistered research scenarios')
    path=root/relative;manifest=json.loads(path.read_text())
    if access['scenario_id']!=manifest['scenario_id'] or access['manifest']['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('manifest identity mismatch')
    for key in ['name','commit','patch_sha256','serialization_method']:
        if access['core'][key]!=manifest['core'][key]:raise ValueError('core identity mismatch: '+key)
    if access['core']['api_version']!=1 or access['core']['options']!=(DEFAULT_OPTIONS | manifest['core'].get('options',{})):raise ValueError('core options/API mismatch')
    script=(json.dumps(derive_script(manifest),indent=2,sort_keys=True)+'\n').encode()
    if access['script']!={'frames':3000,'sample_every':1,'sample_from_frame':None,'sha256':hashlib.sha256(script).hexdigest()}:raise ValueError('input script identity mismatch')
    if access['status']!='complete' or access['failure'] is not None or access['watch_pcs_truncated'] or access['instructions']['max_frame_delta']>access['ring_capacity']:raise ValueError('incomplete capture')
    required={wram_offset(a) if wram_offset(a) is not None else a for a in WATCH_ADDRESSES}
    if not required<=set(map(int,access['watch_addresses'])):raise ValueError('missing motion watches; regenerate with the current capture tool')
    meta=access['wram_series']
    if meta['start']!=0 or meta['length']!=0x2200 or meta['every']!=1 or meta['frames']!=list(range(3000)) or meta['bytes']!=3000*0x2200:raise ValueError('unexpected series layout')
    frames=access['frames']
    if any(type(frames[key]) is not int for key in ('start','end','count')):
        raise ValueError('frame range must contain integers')
    if frames['start']!=1533:
        raise ValueError('evolving reward queue requires the established 1533 window start')
    if not frames['start']<=frames['end']<=2999 or frames['count']!=frames['end']-frames['start']+1:
        raise ValueError('empty, reversed, out-of-domain or count-inconsistent frame range')


def compare(access,series,rom):
    validate_document(access)
    validate_identity(access)
    if access['status']!='complete' or access['watch_pcs_truncated']:raise ValueError('incomplete capture')
    if hashlib.sha256(rom).hexdigest()!=access['rom']['sha256']:raise ValueError('ROM identity mismatch')
    if access['rom']['sha256']!='a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e':raise ValueError('wrong revision')
    if access['wram_series']['sha256']!=hashlib.sha256(series).hexdigest():raise ValueError('series identity mismatch')
    square=[int.from_bytes(rom[0xbdd74+2*i:0xbdd76+2*i],'little') for i in range(256)]
    slope=rom[8:8+128]
    mismatches=[];counts={'values':0};feature_flag=0
    first=access['frames']['start']
    raw_seed=series[(first-1)*0x2200:first*0x2200]
    queue_state={a:int.from_bytes(raw_seed[a:a+2],'little') for a in [0xd11,0xd13,0xca7,0x11db,0x11e1]}
    queue_state.update({0xceb+i:raw_seed[0xceb+i] for i in range(32)})
    queue_state.update({0x7e2102+i:raw_seed[0x2102+i] for i in range(0x47)})
    queue_state[0x770825]=0
    reward_words=[int.from_bytes(rom[0xc493+2*i:0xc495+2*i],'little') for i in range(0x47)]
    event_classes=rom[0xc50a:0xc551]
    for frame in range(first,access['frames']['end']+1):
        ordered=events(access,frame);reward_events=[];snapshots={}
        def state_at(sequence):
            if sequence not in snapshots:snapshots[sequence]=snapshot(series,frame,ordered,sequence)
            return snapshots[sequence]
        specs=[('common',0x818594,0x818704,[0xf5b,0xf35,0xf23,0xf27,0xf3b,0xf3d,0xf3f,0xf41,0xf2d,0x11f1,0xfa7,0xf4b,0xf49,0xfb1,0xf39],'w'),('wheel_override',0x82a06d,0x82a8f0,[0xf3d],'r'),('throttle',0x8298e4,0x829a4f,[0xf5f,0xfa9,0xf65,0xf63,0xf3d,0xe7b,0x11f1],'w'),('pose',0x83ef5c,0x83ef50,POSE_FIELDS,'w'),('jump',0x82a8f0,0x82a96b,JUMP_FIELDS,'w'),('integrate',0x82a627,0x83ef5c,[0xa5,0xa7,0x401,0x403,0x405,0x407],'r'),('gravity',0x82a971,0x82a627,[0xa7,0xfab],'r'),('rolling',0x82a28a,0x83ef5c,[0xf15],'r'),('rotation',0x82a4a1,0x83ef5c,[0xf57],'r')]
        if str(0x136b) in access['watch_addresses']:
            specs.append(('quarters',0x829a58,0x82a8f0,[0xf67,0x1203,0x1205,0x1207,0x1209,0x120b,0x120d,0x120f,0x1211,0x136b,0x136d,0x33f,0x341],'r'))
        if frame>=1534:specs.append(('ai',0x83e0a7,0x8289e3,[0x31b,0x333,0x32f,0xc6f,0xc75,0x1277],'w'))
        for kind,anchor,endpc,fields,endkind in specs:
            starts=[seq for seq,a,k,row in ordered if k=='r' and row[1]==anchor]
            expected_calls=2 if kind in {'common','throttle','pose','integrate','gravity','rolling'} else 1
            if len(starts)!=expected_calls:raise ValueError(f'{kind} needs {expected_calls} call anchors at frame{frame}; got {len(starts)}')
            for start in starts:
                ends=[seq for seq,a,k,row in ordered if seq>start and k==endkind and row[1]==endpc]
                if not ends:raise ValueError('missing call return')
                end=min(ends)
                state=state_at(start)
                feature_before=feature_flag
                for seq,addr,k,row in ordered:
                    if seq<start and addr==0x770825 and k=='w':feature_before=row[-1]
                expected=state_at(end+(endkind=='w'))
                functions={'pose':lambda:pose_update(state,square,slope),'jump':lambda:jump_update(state,False),'integrate':lambda:integrate_position(state),'gravity':lambda:gravity_update(state),'rolling':lambda:rolling_mode(state),'rotation':lambda:rotation_input(state),'ai':lambda:opponent_inputs(state,feature_before),'quarters':lambda:completed_rotation(state)[0],'throttle':lambda:throttle_update(state),'wheel_override':lambda:stationary_animation_override(state),'common':lambda:common_motion_reset(state)}
                actual=functions[kind]()
                if kind=='quarters':
                    _,produced=completed_rotation(state)
                    if state[0xff9]==2:reward_events.extend(produced)
                counts[kind+'_calls']=counts.get(kind+'_calls',0)+1
                for address in fields:
                    counts['values']+=1
                    if actual[address]!=expected[address]:mismatches.append({'frame':frame,'call':kind,'start':start,'field':hex(address),'expected':expected[address],'actual':actual[address]})
        if str(0x136b) in access['watch_addresses']:
            queue_state[0xca7]=max(0,queue_state[0xca7]-2)
            call=next(seq for seq,a,k,row in ordered if row[1]==0x81bef1 and k=='r')
            incoming=state_at(call)
            for a in [0x11db,0x11e1]:queue_state[a]=incoming[a]
            queue_state=reward_queue_step(queue_state,reward_events,reward_words,event_classes)
            current=series[frame*0x2200:(frame+1)*0x2200]
            for address in [0xd11,0xd13,0xca7,0x11db,0x11e1,0x7e2102]+list(range(0xceb,0xd0b)):
                offset=address&65535
                width=1 if address==0x7e2102 or 0xceb<=address<0xd0b else 2
                expected=int.from_bytes(current[offset:offset+width],'little')
                counts['values']+=1
                if queue_state[address]!=expected:mismatches.append({'frame':frame,'call':'reward_queue','field':hex(address),'expected':expected,'actual':queue_state[address]})
            counts['reward_queue_frames']=counts.get('reward_queue_frames',0)+1
        for seq,addr,k,row in ordered:
            if addr==0x770825 and k=='w':feature_flag=row[-1]
        if str(0x136b) in access['watch_addresses']:
            counts['values']+=1
            if queue_state[0x770825]!=feature_flag:mismatches.append({'frame':frame,'call':'reward_feature_total','expected':feature_flag,'actual':queue_state[0x770825]})
    return {'experiment':'isolated captured-argument contracts; not autonomous movement','counts':counts,'mismatches':mismatches,'status':'passed' if not mismatches else 'failed'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    access_path=a.capture/'access.json';series_path=a.capture/'wram-series.bin'
    access=json.loads(access_path.read_text());rom=Path(Path('local/rom-location.txt').read_text().strip()).read_bytes()
    try:result=compare(access,series_path.read_bytes(),rom)
    except (ValueError,KeyError,TypeError,IndexError,StopIteration) as error:
        result={'status':'failed','failure':f'{type(error).__name__}: {error}','counts':{},'mismatches':[]}
    result['access_sha256']=hashlib.sha256(access_path.read_bytes()).hexdigest();result['series_sha256']=hashlib.sha256(series_path.read_bytes()).hexdigest()
    a.report.write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['counts'],result['mismatches'][:8]);return result['status']!='passed'
if __name__=='__main__':raise SystemExit(main())
