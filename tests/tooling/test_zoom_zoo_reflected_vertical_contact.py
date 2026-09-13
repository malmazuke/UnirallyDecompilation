"""ROM-free checks for the M4-07 reflected vertical-contact component."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.native.zoom_zoo_contact import compare_preprocessing  # noqa: E402
from unirally_lab.native.zoom_zoo_reflected_vertical_contact import (  # noqa: E402
    COEFFICIENT_IDENTITY, compare_inputs, preprocess_reflected_call,
    resolve_reflected_response, response_scratch, suffix_inventory,
    validate_manifest,
)


COEFFICIENTS = bytes((0, 4, 4, 4, 2, 4, 4, 4, 1, 0, 1, 2, 3, 1, 5, 6, 7, 1))


def call(**overrides: int) -> dict:
    incoming = {
        "x": 0x1237, "y": 0x0459, "vx": 483, "vy": 19,
        "response_a": 0, "response_b": 0, "response_impulse": 0,
        "unsupported_count": 0, "unsupported_duration": 0,
        "surface_angle": 0, "angle_sentinel": 0, "auxiliary_flag": 0,
        "mode": 0, "special": 0, "phase": 1, "reflection": 1,
        "pose": 0, "previous_x": 0x1228, "previous_y": 0x0458,
    }
    incoming.update(overrides)
    return {"frame": 1684, "rider": 0, "input": incoming}


def summary(angle: int = 8) -> dict:
    return {
        "supported": True, "support_summary": 4, "vertical_correction": 4,
        "angle": angle, "selected_word": 0x4CE0, "selected_high": 0x4C,
        "tile_flags": 0, "vertical_axis": 0,
        "horizontal_correction": 0, "horizontal_axis": 0,
    }


class ZoomZooReflectedVerticalTests(unittest.TestCase):
    def test_authored_manifests_bind_source_inventory_and_coefficients(self) -> None:
        paths = [
            ROOT / "tests/manifests/native/zoom-zoo-reflected-vertical-primary.reference.json",
            ROOT / "tests/manifests/native/zoom-zoo-reflected-vertical-right-release-1684.reference.json",
        ]
        for path in paths:
            document = json.loads(path.read_text())
            validate_manifest(document)
            for key in ("access_sha256", "calls", "points", "prefix", "suffix", "static_content", "description", "limits"):
                changed = copy.deepcopy(document)
                if key in ("calls", "points"):
                    changed[key] -= 1
                elif key == "access_sha256":
                    changed[key] = "0" * 64
                elif key == "static_content":
                    changed[key]["reached_indices"] = [6, 7]
                elif key == "description":
                    changed[key] = "contradictory"
                elif key == "limits":
                    changed[key] = "autonomous production support"
                else:
                    changed[key]["calls"] -= 1
                with self.subTest(path=path.name, key=key):
                    with self.assertRaises(ValueError):
                        validate_manifest(changed)

    def test_worker_replay_is_the_preregistered_one_frame_release(self) -> None:
        path = ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1684.json"
        document = json.loads(path.read_text())
        events = document["inputs"]["controllers"][0]["events"]
        right = [e for e in events if e["buttons"] == ["right"]]
        self.assertEqual(right, [
            {"from": 1650, "to": 1683, "buttons": ["right"]},
            {"from": 1685, "to": 3299, "buttons": ["right"]},
        ])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         "202403bebbf2ae281b625076cbedc1a807a7d239863daab2a629ce3e3c403b78")

    def test_reflected_column_and_angle_are_computed_not_captured(self) -> None:
        raw = 0x4044
        tile = 18
        tables = bytearray(6496)
        # point x 3 plus local x 7 gives direct 10, reflected 5.
        tables[tile * 32 + 5 * 2:tile * 32 + 5 * 2 + 2] = bytes((8, 0xFF))
        content = {
            "collision-poses": b"", "collision-templates": b"",
            "tile-tables": bytes(tables), "tile-flags": bytes(203),
        }
        tested = call()
        tested["raw_samples"] = [0x5400] * 9 + [raw]
        tested["observed_penetrations"] = [0xA0] * 9 + [2]
        tested["observed_angles"] = [0] * 9 + [1]
        tested["observed_descriptors"] = [0] * 9 + [raw]
        with patch("unirally_lab.native.zoom_zoo_reflected_vertical_contact.expand_points",
                   return_value=[(0, 0)] * 9 + [(3, 0)]):
            probes, columns = preprocess_reflected_call(tested, content)
        self.assertEqual(probes[-1], (2, 1, raw))
        self.assertEqual(columns[-1]["direct_column"], 10)
        self.assertEqual(columns[-1]["column"], 5)
        compare_preprocessing(tested, probes)
        changed = list(probes); changed[8] = (1, 0, 0)
        with self.assertRaisesRegex(ValueError, "computed preprocessing differs"):
            compare_preprocessing(tested, changed)

    def test_unobserved_descriptor_and_horizontal_paths_reject(self) -> None:
        for raw in (0x0044, 0x8044, 0x4045):
            tested = call(); tested["raw_samples"] = [0x5400] * 9 + [raw]
            content = {"collision-poses": b"", "collision-templates": b"",
                       "tile-tables": bytes(6496), "tile-flags": bytes(203)}
            with patch("unirally_lab.native.zoom_zoo_reflected_vertical_contact.expand_points",
                       return_value=[(0, 0)] * 10):
                with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "descriptor"):
                    preprocess_reflected_call(tested, content)
        tested = call(); tested["raw_samples"] = [0x5400] * 9 + [0x4044]
        flags = bytearray(203); flags[18] = 1
        content["tile-flags"] = bytes(flags)
        with patch("unirally_lab.native.zoom_zoo_reflected_vertical_contact.expand_points",
                   return_value=[(0, 0)] * 10):
            with self.assertRaisesRegex(ValueError, "horizontal"):
                preprocess_reflected_call(tested, content)

    def test_positive_response_authenticates_indices_six_through_eight(self) -> None:
        expected = {6: (30, 6, 180, 3), 7: (30, 7, 210, 3), 8: (241, 1, 241, 4)}
        for angle, (shifted, multiplier, vy, vx_add) in expected.items():
            resolved, scratch = resolve_reflected_response(call(), summary(angle), COEFFICIENTS)
            self.assertEqual((scratch["shifted_velocity"], scratch["slope_multiplier"]),
                             (shifted, multiplier))
            self.assertEqual((resolved["motion"]["vy"], resolved["motion"]["vx"]),
                             (vy, 483 + vx_add))
            self.assertEqual(scratch["coefficient_index"], angle)
        self.assertEqual(COEFFICIENT_IDENTITY, (18, hashlib.sha256(COEFFICIENTS).hexdigest()))

    def test_coefficient_and_response_mutations_change_computation(self) -> None:
        original = resolve_reflected_response(call(), summary(7), COEFFICIENTS)
        changed = bytearray(COEFFICIENTS); changed[16] = 6
        self.assertNotEqual(resolve_reflected_response(call(), summary(7), bytes(changed)), original)
        self.assertNotEqual(resolve_reflected_response(call(vx=482), summary(7), COEFFICIENTS), original)

    def test_signed_shift_and_positive_product_order(self) -> None:
        scratch = response_scratch(summary(8), 0xFFFE, COEFFICIENTS)
        self.assertEqual(scratch["shifted_velocity"], 0xFFFF)
        resolved, _ = resolve_reflected_response(call(vx=0xFFFE), summary(8), COEFFICIENTS)
        self.assertEqual(resolved["motion"]["vy"], 0xFFFF)
        self.assertEqual(resolved["motion"]["vx"], 2)

    def test_response_rejects_unobserved_state_domains(self) -> None:
        cases = [
            (call(unsupported_count=9), summary()),
            (call(mode=1), summary()),
            (call(special=1), summary()),
            (call(), {**summary(), "supported": False}),
            (call(), summary(9)),
        ]
        for tested_call, tested_summary in cases:
            with self.assertRaisesRegex(ValueError, "bounded reflected"):
                resolve_reflected_response(tested_call, tested_summary, COEFFICIENTS)

    def test_suffix_order_and_count_are_hash_sensitive(self) -> None:
        calls = [
            {"ordinal": i, "frame": 1683 + i // 2, "rider": i % 2,
             "raw_samples": [0x4044 if i % 2 == 0 else 0x0002] + [0x5400] * 9}
            for i in range(36)
        ]
        _rows, raw = suffix_inventory(calls)
        reversed_calls = list(reversed(calls))
        self.assertNotEqual(suffix_inventory(reversed_calls)[1], raw)
        self.assertNotEqual(suffix_inventory(calls[:-1])[1], raw)

    def test_input_comparison_rejects_non_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = root / "primary.json"; variation = root / "variation.json"
            primary.write_text("[]"); variation.write_text("[]")
            with self.assertRaisesRegex(ValueError, "complete sample documents"):
                compare_inputs(primary, variation, root / "report.json")


if __name__ == "__main__":
    unittest.main()
