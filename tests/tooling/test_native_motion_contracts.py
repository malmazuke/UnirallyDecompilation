"""ROM-free boundary checks for isolated M2-01A research contracts."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from unirally_lab.native.motion_research.contracts import (
    completed_rotation, gravity_update, integrate_position, jump_update,
    opponent_inputs, pose_update, reward_queue_step, throttle_update,
)
from unirally_lab.native.motion_research.probe import (
    WORD_ADDRESSES, snapshot, validate_identity,
)
from unirally_lab.native.motion_research.capture import WATCH_ADDRESSES
from unirally_lab.access.derive import wram_offset
from unirally_lab.reference.bsnes import DEFAULT_OPTIONS
from unirally_lab.replay.manifest import derive_script


def state():
    result={a:0 for a in WORD_ADDRESSES}
    result[0xd4f]=65535
    return result


class MotionArithmeticTests(unittest.TestCase):
    def test_signed_residue_crosses_zero_without_unsigned_carry(self):
        s=state();s.update({0xa5:100,0xfa9:456,0x401:65535})
        result=integrate_position(s)
        self.assertEqual((result[0xa5],result[0x401]),(114,7))
        s.update({0xfa9:65505,0x401:65535})
        result=integrate_position(s)
        self.assertEqual((result[0xa5],result[0x401]),(99,0))

    def test_gravity_threshold_and_extra_coordinate_step(self):
        s=state();s[0xfab]=511;s[0xa7]=100
        result=gravity_update(s)
        self.assertEqual((result[0xfab],result[0xa7]),(515,101))
        s[0xfab]=512
        self.assertEqual(gravity_update(s),s)
        s[0xfab]=(-144)&65535
        self.assertEqual(gravity_update(s)[0xfab],(-125)&65535)

    def test_jump_arms_then_applies_impulse_on_next_active_call(self):
        s=state();s[0xf1f]=1;s[0xfab]=19
        armed=jump_update(s,False)
        self.assertEqual((armed[0xf91],armed[0xf93],armed[0xfab]),(1,0,19))
        jumped=jump_update(armed,False)
        self.assertEqual((jumped[0xf91],jumped[0xf93],jumped[0xfab]),(0,1,(-144)&65535))
        jumped[0xf1f]=0
        released=jump_update(jumped,False)
        self.assertEqual((released[0xf93],released[0xfa5]),(0,0))

    def test_contact_impulse_applies_before_damping_and_reflection(self):
        s=state();s.update({0xf53:10,0xf57:2,0xfad:2,0xf33:9,0xf51:1,0xf93:1,0x4c7:2})
        result=pose_update(s,[i*i for i in range(256)],[0]*128)
        self.assertEqual((result[0xf81],result[0xfad],result[0xfa1]),(51,1,51))

    def test_pose_exact_remainder_cancellation_retains_signed_distance(self):
        for old_x,new_x,old_remainder,expected in [(10,11,1,65535),(11,10,65535,1)]:
            s=state();s.update({0xf9b:old_x,0xa5:new_x,0xf9f:old_remainder})
            result=pose_update(s,[i*i for i in range(256)],[0]*128)
            with self.subTest(old_x=old_x):
                self.assertEqual((result[0xf99],result[0xf9f],result[0xf73]),(expected,0,1))

    def test_three_quarters_round_up_only_when_landing(self):
        s=state();s.update({0x33f:1,0x120b:3,0x136b:1,0xf67:3,0xf53:48,0xf33:9})
        airborne,events=completed_rotation(s)
        self.assertEqual(events,[])
        self.assertEqual(airborne[0x120b],3)
        airborne[0xf33]=0
        landed,events=completed_rotation(airborne)
        self.assertEqual(events,[1])
        self.assertEqual((landed[0x1203],landed[0x120b],landed[0x136b]),(0,0,0))

    def test_reward_waits_for_cooldown_and_reads_authored_amount(self):
        s={0xd11:0,0xd13:1,0xca7:2,0x11db:5,0x11e1:7,0x770825:0,0x7e2102:6}
        s.update({0xceb+i:0 for i in range(32)})
        queued=reward_queue_step(s,[1],[73],[0])
        self.assertEqual((queued[0xd13],queued[0x11db]),(2,5))
        queued[0xca7]=0
        rewarded=reward_queue_step(queued,[],[73],[0])
        self.assertEqual((rewarded[0x11db],rewarded[0x11e1],rewarded[0x770825],rewarded[0x7e2102],rewarded[0xca7]),(78,80,6,3,40))

    def test_reward_halves_prior_negative_boost_before_addition(self):
        # Source-derived boundary $81:C286..C290; primary rewards are positive.
        for boost,expected in [(65532,71),(65531,70),(65535,72),(32767,49224)]:
            s={0xd11:0,0xd13:1,0xca7:0,0x11db:boost,0x11e1:7,0x770825:0,0x7e2102:6}
            s.update({0xceb+i:0 for i in range(32)})
            rewarded=reward_queue_step(s,[1],[73],[0])
            with self.subTest(boost=boost):self.assertEqual(rewarded[0x11db],expected)

    def test_learned_feature_total_changes_next_ai_request(self):
        s=state();s.update({0xc6d:1,0x1275:1,0xfc7:0x2000})
        self.assertEqual(opponent_inputs(s,0)[0x333],1)
        self.assertEqual(opponent_inputs(s,4)[0x333],0)
        s[0xfcd]=3
        with self.assertRaisesRegex(ValueError,'catch-up'):opponent_inputs(s,4)

    def test_launch_consumes_stored_throttle_once(self):
        s=state();s.update({0xf21:2,0xf65:1,0xf5f:432,0x11d1:448,0xc77:4})
        launched=throttle_update(s)
        self.assertEqual((launched[0xfa9],launched[0xf5f],launched[0xf65],launched[0x11f1]),(456,0,0,256))
        launched[0x11f1]=0;launched[0xf73]=14
        self.assertEqual(throttle_update(launched)[0xfa9],480)


class MotionEvidenceTests(unittest.TestCase):
    def test_hardware_register_write_does_not_overwrite_wram(self):
        series=bytearray(0x2200);series[0x2102]=7
        ordered=[(1,0x2102,'w',[1,0,'write',0x002102,1,99])]
        self.assertEqual(snapshot(series,1,ordered,2)[0x2102],7)
        ordered.append((2,0x2102,'w',[2,0,'write',0x7e2102,1,2]))
        self.assertEqual(snapshot(series,1,ordered,3)[0x2102],2)

    def test_unresolved_word_cannot_be_used_as_false(self):
        ordered=[(1,0xf41,'w',[1,0,'read_modify_write',0xf41,2,None])]
        captured=snapshot(bytes(0x2200),1,ordered,2)
        with self.assertRaisesRegex(ValueError,'unresolved'):bool(captured[0xf41])

    def test_identity_rejects_changed_core_script_and_missing_watch(self):
        root=Path(__file__).resolve().parents[2]
        relative='tests/manifests/replay/race-crawler-dragster-3000-fields.json'
        path=root/relative;manifest=json.loads(path.read_text())
        script=(json.dumps(derive_script(manifest),indent=2,sort_keys=True)+'\n').encode()
        access={
            'manifest':{'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},
            'scenario_id':manifest['scenario_id'],'core':manifest['core']|{'api_version':1,'options':DEFAULT_OPTIONS},
            'script':{'frames':3000,'sample_every':1,'sample_from_frame':None,'sha256':hashlib.sha256(script).hexdigest()},
            'status':'complete','failure':None,'watch_pcs_truncated':False,'instructions':{'max_frame_delta':10},'ring_capacity':20,
            'watch_addresses':{str(wram_offset(a) if wram_offset(a) is not None else a):{} for a in WATCH_ADDRESSES},
            'wram_series':{'start':0,'length':0x2200,'every':1,'frames':list(range(3000)),'bytes':3000*0x2200},
            'frames':{'start':1533,'end':1700,'count':168},
        }
        validate_identity(access)
        for section,key,value in [('core','commit','changed'),('script','sha256','0'*64),('wram_series','start',1)]:
            bad=copy.deepcopy(access);bad[section][key]=value
            with self.subTest(section=section),self.assertRaises(ValueError):validate_identity(bad)
        for frames in [
            {'start':1600,'end':1700,'count':101},
            {'start':1533,'end':1532,'count':0},
            {'start':1533,'end':3000,'count':1468},
            {'start':1533,'end':1700,'count':0},
            {'start':1533,'end':1700.0,'count':168},
            {'start':1533,'end':1700,'count':True},
        ]:
            bad=copy.deepcopy(access);bad['frames']=frames
            with self.subTest(frames=frames),self.assertRaises(ValueError):validate_identity(bad)
        del access['watch_addresses'][str(0xfe3)]
        with self.assertRaisesRegex(ValueError,'missing motion watches'):validate_identity(access)
