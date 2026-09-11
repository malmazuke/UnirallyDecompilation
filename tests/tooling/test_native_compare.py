"""Authored protocol/first-divergence checks; no native gameplay claim."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from unirally_lab.native import compare as cmp
from unirally_lab.native.freeze_reference import PROJECTION, DIAGNOSTIC


def authored():
    reference = {"schema_version": 1, "kind": "frozen_reference_projection",
                 "projection": copy.deepcopy(PROJECTION), "diagnostic_only": copy.deepcopy(DIAGNOSTIC),
                 "columns": cmp.COLUMNS.copy(), "initial_frame": 10, "first_update_frame": 11,
                 "last_frame": 13, "rows": [[frame] + [0] * len(PROJECTION) for frame in range(10, 14)]}
    manifest = {"inputs": {"controllers": [
        {"port": 0, "events": [{"from": 10, "to": 11, "buttons": ["right"]}]},
        {"port": 1, "events": [{"from": 12, "to": 13, "buttons": ["left"]}]},
    ]}}
    return reference, manifest


class NativeCompareTests(unittest.TestCase):
    def test_exact_series_and_diagnostic_exclusions(self):
        ref, inputs = authored()
        result = cmp.compare_rows(ref, copy.deepcopy(ref["rows"]), inputs)
        self.assertTrue(result["identical"])
        self.assertEqual(result["compared_frames"], 3)
        self.assertEqual(result["validated_native_frames"], 4)
        self.assertEqual(result["diagnostic_only"], DIAGNOSTIC)

    def test_first_divergence_contains_signed_values_prior_state_and_both_inputs(self):
        ref, inputs = authored()
        native = copy.deepcopy(ref["rows"])
        speed = cmp.COLUMNS.index("speed")
        ref["rows"][1][speed] = native[1][speed] = -2
        native[2][speed] = -1
        native[3][cmp.COLUMNS.index("pos_x")] = 77
        result = cmp.compare_rows(ref, native, inputs)
        self.assertFalse(result["identical"])
        self.assertEqual(result["compared_frames"], 2)
        d = result["first_divergence"]
        self.assertEqual(d["frame"], 12)
        self.assertEqual(d["differences"], [{"field":"speed", "native":-1, "reference":0}])
        self.assertEqual(d["prior_sample"]["frame"], 11)
        self.assertEqual(d["prior_sample"]["native"]["speed"], -2)
        self.assertEqual(d["inputs"], {"previous":{"0":["right"],"1":[]},
                                       "current":{"0":[],"1":["left"]}})

    def test_first_update_has_initial_sample_as_prior(self):
        ref, inputs = authored()
        native = copy.deepcopy(ref["rows"])
        native[1][1] = 1
        self.assertEqual(cmp.compare_rows(ref,native,inputs)["first_divergence"]["prior_sample"]["frame"],10)

    def test_reporting_window_still_requires_complete_warmup(self):
        ref, inputs = authored()
        native = copy.deepcopy(ref["rows"])
        native[1][1] = 1
        self.assertTrue(cmp.compare_rows(ref,native,inputs,from_frame=12)["identical"])
        with self.assertRaises(cmp.NativeOutputError):
            cmp.compare_rows(ref,native[2:],inputs,from_frame=12)

    def test_invalid_empty_or_outside_window_is_not_a_pass(self):
        ref, inputs = authored()
        for start,end in [(12,11),(10,12),(11,14),(True,13),(11,False)]:
            with self.subTest(start=start,end=end),self.assertRaises(cmp.ReferenceError):
                cmp.compare_rows(ref,ref["rows"],inputs,from_frame=start,to_frame=end)

    def test_incomplete_duplicate_and_reordered_native_rows_rejected(self):
        ref, inputs = authored()
        for kind in ["empty","missing","duplicate","reordered","field","bool","width"]:
            native = copy.deepcopy(ref["rows"])
            if kind == "empty": native=[]
            elif kind == "missing": native.pop()
            elif kind == "duplicate": native[2]=native[1].copy()
            elif kind == "reordered": native[1],native[2]=native[2],native[1]
            elif kind == "field": native[1].pop()
            elif kind == "bool": native[1][1]=False
            else: native[1][cmp.COLUMNS.index("speed")]=32768
            with self.subTest(kind=kind),self.assertRaises(cmp.NativeOutputError):
                cmp.compare_rows(ref,native,inputs)

    def test_initial_seed_cannot_be_replaced(self):
        ref,inputs=authored()
        native=copy.deepcopy(ref["rows"])
        native[0][1]=1
        with self.assertRaises(cmp.NativeOutputError): cmp.compare_rows(ref,native,inputs)

    def test_required_projection_cannot_be_waived(self):
        ref,inputs=authored()
        ref["projection"].pop()
        with self.assertRaises(cmp.ReferenceError): cmp.compare_rows(ref,ref["rows"],inputs)

    def test_metadata_does_not_equate_booleans_and_integers(self):
        for key, value in [("offset", False), ("length", True), ("signed", 0)]:
            ref, _ = authored()
            ref["projection"][0][key] = value
            with self.subTest(key=key), self.assertRaises(cmp.ReferenceError):
                cmp.validate_reference(ref)

    def test_real_primary_binding_and_manifest_tamper(self):
        expected=ROOT/"tests/manifests/native/primary.expected.json"
        replay=ROOT/"tests/manifests/native/primary.replay.json"
        ref,_=cmp.load_reference(expected,replay)
        self.assertEqual(len(ref["rows"]),1467)  # Reference validation, not native agreement.
        with tempfile.TemporaryDirectory() as directory:
            changed=Path(directory)/"replay.json"
            changed.write_bytes(replay.read_bytes()+b"\n")
            with self.assertRaises(cmp.ReferenceError): cmp.load_reference(expected,changed)
        with self.assertRaises(FileNotFoundError): cmp.load_reference(expected,Path("missing-replay.json"))


if __name__ == "__main__": unittest.main()
