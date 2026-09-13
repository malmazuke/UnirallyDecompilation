"""ROM-free integrity tests for the isolated M4-05 contact component."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.native.zoom_zoo_contact import (  # noqa: E402
    captured_calls,
    classify_calls,
    reduce_neighbourhood,
    resolve_neighbourhood,
    validate_component_manifest,
    validate_call_sequence,
)


def call(frame: int, rider: int, ordinal: int, raw: int = 0x5800,
         penetration: int = 0xA0, angle: int = 0) -> dict:
    raws = [0x5800] * 10
    penetrations = [0xA0] * 10
    angles = [0] * 10
    descriptors = [0] * 10
    raws[9] = raw
    penetrations[9] = penetration
    angles[9] = angle
    descriptors[9] = 0 if raw & 0x03FF == 0 else raw
    return {
        "frame": frame, "rider": rider, "ordinal": ordinal,
        "raw_samples": raws, "observed_penetrations": penetrations,
        "observed_angles": angles, "observed_axes": [None] * 9 + [0],
        "observed_descriptors": descriptors,
    }


class ZoomZooContactTests(unittest.TestCase):
    def test_component_source_and_guard_identities_are_exact(self) -> None:
        manifest = json.loads((ROOT / "tests/manifests/native/zoom-zoo-contact-reference.json").read_text())
        validate_component_manifest(manifest)
        mutations = []
        changed = copy.deepcopy(manifest); changed["source"]["replay_manifest_sha256"] = "0" * 64; mutations.append(changed)
        changed = copy.deepcopy(manifest); changed["scenario_id"] = "race-crawler-zoom-zoo-right-1652-3300"; mutations.append(changed)
        changed = copy.deepcopy(manifest); changed["guard_order"][0:2] = reversed(changed["guard_order"][0:2]); mutations.append(changed)
        changed = copy.deepcopy(manifest); changed["static_content"]["contract_sha256"] = "0" * 64; mutations.append(changed)
        for changed in mutations:
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    validate_component_manifest(changed)

    def test_marker_predicate_precedes_direction_bits(self) -> None:
        row = classify_calls([call(1, 0, 0, raw=0x5800)], bytes(203))[0]
        self.assertIsNone(row["first_incompatible"])
        self.assertEqual(row["samples"][9]["guards"], [{"predicate": "marker_empty", "result": True}])

    def test_first_failed_guard_is_stable_in_actual_order(self) -> None:
        flags = bytearray(203)
        slope = classify_calls([call(1, 0, 0, raw=0x20, penetration=2, angle=0xFF)], flags)[0]
        self.assertEqual(slope["first_incompatible"], {"point": 9, "predicate": "non_flat_angle"})
        directional = classify_calls([call(1, 0, 0, raw=0x4020, penetration=2, angle=0xFF)], flags)[0]
        self.assertEqual(directional["first_incompatible"], {"point": 9, "predicate": "direction_or_special"})
        flags[8] = 1
        horizontal = classify_calls([call(1, 0, 0, raw=0x20, penetration=2, angle=0xFF)], flags)[0]
        self.assertEqual(horizontal["first_incompatible"], {"point": 9, "predicate": "horizontal_tile_flag"})

    def test_call_presence_order_rider_and_ordinal_are_exact(self) -> None:
        rows = [call(1, 0, 0), call(1, 1, 1), call(2, 0, 2), call(2, 1, 3)]
        validate_call_sequence(rows, 1, 2)
        mutations = [rows[:-1], rows + [copy.deepcopy(rows[-1])],
                     [rows[1], rows[0], *rows[2:]]]
        changed_rider = copy.deepcopy(rows); changed_rider[1]["rider"] = 0; mutations.append(changed_rider)
        changed_ordinal = copy.deepcopy(rows); changed_ordinal[2]["ordinal"] = 0; mutations.append(changed_ordinal)
        for changed in mutations:
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, "presence, order, rider or ordinal"):
                    validate_call_sequence(changed, 1, 2)

    def test_minus_one_slope_reduction_and_response(self) -> None:
        probes = [(0xA0, 0, 0)] * 9 + [(2, 0xFF, 0x20)]
        summary = reduce_neighbourhood(probes, bytes(203))
        self.assertEqual(summary, {
            "supported": True, "support_summary": 2, "vertical_correction": 2,
            "angle": 0xFF, "selected_word": 0x20, "selected_high": 0, "tile_flags": 0,
        })
        source = {
            "input": {
                "x": 9258, "y": 1562, "vx": 287, "vy": 19,
                "response_a": 0, "response_b": 0, "response_impulse": 0,
                "unsupported_count": 0, "unsupported_duration": 0,
                "previous_x": 9249, "previous_y": 1563, "surface_angle": 0,
                "angle_sentinel": 0, "auxiliary_flag": 0, "phase": 1,
            }
        }
        resolved = resolve_neighbourhood(source, summary, bytes((4, 1)))
        self.assertEqual((resolved["motion"]["x"], resolved["motion"]["y"]), (9258, 1560))
        self.assertEqual((resolved["motion"]["vx"], resolved["motion"]["vy"]), (287, 0xFFF0))
        self.assertEqual((resolved["state"]["surface_angle"], resolved["state"]["angle_sentinel"]), (0xFFFF, 0))

    def test_state_and_static_coefficient_mutations_change_reconstruction(self) -> None:
        probes = [(0xA0, 0, 0)] * 9 + [(2, 0xFF, 0x20)]
        summary = reduce_neighbourhood(probes, bytes(203))
        base = {
            "input": {
                "x": 100, "y": 20, "vx": 287, "vy": 19,
                "response_a": 0, "response_b": 0, "response_impulse": 0,
                "unsupported_count": 0, "unsupported_duration": 0,
                "previous_x": 90, "previous_y": 18, "surface_angle": 0,
                "angle_sentinel": 0, "auxiliary_flag": 0, "phase": 1,
            }
        }
        expected = resolve_neighbourhood(base, summary, bytes((4, 1)))
        changed = copy.deepcopy(base); changed["input"]["vx"] = 288
        self.assertNotEqual(resolve_neighbourhood(changed, summary, bytes((4, 1))), expected)
        self.assertNotEqual(resolve_neighbourhood(base, summary, bytes((3, 1))), expected)
        with self.assertRaises(ValueError):
            resolve_neighbourhood(base, summary, b"")

    def test_incomplete_capture_is_not_defaulted(self) -> None:
        with self.assertRaises(ValueError):
            captured_calls({"status": "complete", "watch_pcs_truncated": True})


if __name__ == "__main__":
    unittest.main()
