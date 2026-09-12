"""Authored boundaries for the isolated contact research checker."""
import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from unirally_lab.native.contact_research.preprocess import preprocess, reduce_samples
from unirally_lab.native.contact_research.summarize import verify_call, events_for_frame, calls


class ContactResearchTests(unittest.TestCase):
    def test_marker_only_samples_do_not_become_solid(self):
        result=preprocess([0x800,0],[(0,0),(0,0)],0,0,bytes(32),bytes(1))
        self.assertEqual(result,[(160,0,0),(160,0,0)])

    def test_column_height_uses_wrapped_subtraction(self):
        columns=bytearray(64);columns[32:34]=bytes([0,0])
        self.assertEqual(preprocess([2],[(0,15)],0,0,columns,bytes(2)),[(16,0,2)])
        columns[32]=160
        self.assertEqual(preprocess([2],[(0,15)],0,0,columns,bytes(2)),[(160,0,2)])

    def test_later_equal_probe_updates_high_word_but_not_first_descriptor(self):
        probes=[(160,0,0),(160,0,0),(2,0,2),(2,0,0x802)]+[(160,0,0)]*6
        result=reduce_samples(probes,bytes(2))
        self.assertEqual(result['selected_word'],2)
        self.assertEqual(result['selected_high'],8)
        self.assertEqual(result['vertical_correction'],2)

    def test_nonprimary_geometry_rejected(self):
        with self.assertRaises(ValueError):preprocess([0x8002],[(0,0)],0,0,bytes(64),bytes(2))
        with self.assertRaises(ValueError):reduce_samples([(1,0,2)]+[(160,0,0)]*9,bytes(2))

    def test_duplicate_byte_watches_are_one_event(self):
        e=[1,0x818F9D,'write',0xF4F,2,9]
        access={'watch_addresses':{'3919':{'1':{'w':[e]}},'3920':{'1':{'w':[e]}}}}
        self.assertEqual(events_for_frame(access,1),[tuple(e)])

    def test_incomplete_capture_rejected(self):
        with self.assertRaises(ValueError):calls({'status':'complete','watch_pcs_truncated':True})

    def test_empty_or_inconsistent_frame_ranges_rejected(self):
        for frames in [{'start':1619,'end':1618,'count':0},
                       {'start':1,'end':2,'count':1},
                       {'start':True,'end':2,'count':2},
                       {'start':-1,'end':0,'count':2}]:
            with self.subTest(frames=frames):
                with self.assertRaises(ValueError):
                    calls({'status':'complete','watch_pcs_truncated':False,'frames':frames})

    def test_counter_cap_and_precorrection_position_are_checked_independently(self):
        incoming={'unsupported_count':9,'unsupported_duration':65535,'vx':321,'vy':-1&65535,'x':100,'y':1}
        output={'previous_x':100,'previous_y':1}
        published={'unsupported_count':9,'unsupported_duration':0,'vx':321,'vy':65535,'x':100,'y':65535}
        c={'input':incoming,'output':output,'published':published,'support_summary':255,
           'classified':{'vertical_axis':0,'horizontal_axis':0,'vertical_correction':2}}
        branch,checks=verify_call(c)
        self.assertEqual(branch,'unsupported');self.assertTrue(all(r['passed'] for r in checks))
        mutant=copy.deepcopy(c);mutant['output']['previous_y']=65535
        self.assertEqual([r['name'] for r in verify_call(mutant)[1] if not r['passed']],['save_precorrection_y'])
        mutant=copy.deepcopy(c);mutant['published']['unsupported_count']=10
        self.assertEqual([r['name'] for r in verify_call(mutant)[1] if not r['passed']],['counter'])

if __name__=='__main__':unittest.main()
