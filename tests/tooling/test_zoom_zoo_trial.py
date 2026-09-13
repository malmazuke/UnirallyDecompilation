"""ROM-free boundaries for the M4-12 laboratory protocol."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.unirally_lab.native.zoom_zoo_trial import load_case, controller_rows, check_content

class ZoomZooTrialTests(unittest.TestCase):
    def test_variation_has_full_horizon_and_resumes_primary(self):
        case={'id':'synthetic','changes':[{'from':1700,'to':1702,'buttons':[]}]}
        rows=controller_rows(case).splitlines()
        self.assertEqual(len(rows),200)
        self.assertEqual(rows[50:54],['1700 0 0','1701 0 0','1702 0 0','1703 128 0'])
        self.assertEqual(controller_rows(case,1849),'1849 128 0\n')

    def test_case_cannot_change_seed_or_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'case.json'
            for changes in [[{'from':1649,'to':1700,'buttons':[]}],
                            [{'from':1700,'to':1702,'buttons':[]},{'from':1702,'to':1710,'buttons':['right']}],
                            [{'from':1700,'to':1701,'buttons':['unknown']}]]:
                path.write_text(json.dumps({'id':'bad','changes':changes}))
                with self.assertRaises(ValueError):load_case(path)

    def test_static_mutation_is_rejected(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'table.bin').write_bytes(b'ab')
            inventory={'table.bin':{'bytes':2,'sha256':hashlib.sha256(b'ab').hexdigest()}}
            with patch('tools.unirally_lab.native.zoom_zoo_trial.content_inventory',return_value=inventory):
                check_content(path)
                (path/'table.bin').write_bytes(b'ac')
                with self.assertRaisesRegex(ValueError,'static content differs'):check_content(path)

if __name__=='__main__':unittest.main()
