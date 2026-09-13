import copy
import json
from pathlib import Path
import unittest
from tools.unirally_lab.native.zoom_zoo_race_audit import preflight, authenticate_samples
from tools.unirally_lab.native.zoom_zoo_race_explore import timeline
from tools.unirally_lab.native.zoom_zoo_trial_reference import digest
from tools.unirally_lab.replay.manifest import derive_script

class RaceAuditTests(unittest.TestCase):
    def test_legacy_pulse_and_second_controller_fail_preflight(self):
        manifest=json.loads(Path('tests/manifests/replay/m4-15-zoom-zoo-primary.json').read_text())
        case=json.loads(Path('tests/manifests/native/zoom-zoo-race-primary.case.json').read_text())
        reference={'frames':[1649,6724],'timeline_sha256':digest(timeline(case,6724,derive_script(manifest)))}
        self.assertEqual(preflight(manifest,reference),reference['timeline_sha256'])
        for event,port in [({'from':2200,'to':2259,'buttons':['up']},0),({'from':1660,'to':1661,'buttons':['b']},1),({'from':299,'to':299,'buttons':['start']},0)]:
            changed=copy.deepcopy(manifest)
            controller=next((p for p in changed['inputs']['controllers'] if p['port']==port),None)
            if controller is None:
                controller={'port':port,'events':[]};changed['inputs']['controllers'].append(controller)
            controller['events'].append(event)
            with self.assertRaises(ValueError):preflight(changed,reference)
    def test_missing_or_changed_wram_fails(self):
        reference={'frames':[1649,1650],'wram_sha256':['a','b']}
        self.assertEqual(authenticate_samples({'frames':[{'frame':1649,'wram_sha256':'a'},{'frame':1650,'wram_sha256':'b'}]},reference),2)
        for rows in [[{'frame':1649,'wram_sha256':'a'}],[{'frame':1649,'wram_sha256':'a'},{'frame':1650,'wram_sha256':'c'}]]:
            with self.assertRaises(ValueError):authenticate_samples({'frames':rows},reference)
