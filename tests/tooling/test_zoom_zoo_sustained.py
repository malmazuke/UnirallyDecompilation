import json
from pathlib import Path
import tempfile
import unittest
from tools.unirally_lab.native import zoom_zoo_sustained as lab

class SustainedProtocolTests(unittest.TestCase):
    def test_controller_domain_and_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'case.json'
            for changes in ([{'from':1649,'to':1650,'buttons':[]}],
                            [{'from':2000,'to':2001,'buttons':['left']}],
                            [{'from':2000,'to':2001,'buttons':[]},{'from':2001,'to':2002,'buttons':[]} ]):
                path.write_text(json.dumps({'id':'invalid','changes':changes}))
                with self.assertRaises(ValueError):lab.load_case(path,3299)
    def test_later_input_and_restore_suffix(self):
        case={'id':'pause','changes':[{'from':2200,'to':2201,'buttons':[]}]}
        self.assertEqual(lab.controller_rows(case,2199,2202),'2199 128 0\n2200 0 0\n2201 0 0\n2202 128 0\n')
    def test_no_surface_event_cannot_qualify(self):
        row=bytes(lab.STATE_BYTES).hex()
        with self.assertRaisesRegex(ValueError,'entry and exit'):lab.events([row]*1651)
