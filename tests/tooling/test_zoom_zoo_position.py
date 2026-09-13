"""ROM-free checks for the preregistered M4-08 capture surface."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from unirally_lab.native.zoom_zoo_position import (  # noqa: E402
    FIRST_CALL_FRAME, LAST_CALL_FRAME, WATCH_ADDRESSES, WATCH_PCS,
    capture_command, integrate_axis, slope_tail, validate_component_manifest,
    validate_call_order,
)


class ZoomZooPositionPreregistrationTests(unittest.TestCase):
    def test_capture_freezes_full_position_domain_and_a6e9(self):
        command = capture_command(
            ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-3300.json",
            Path("artifacts/test/position"),
        )
        self.assertEqual((FIRST_CALL_FRAME, LAST_CALL_FRAME), (1650, 1700))
        self.assertEqual(command[command.index("--from-frame") + 1], "1649")
        self.assertIn(0x00A7, WATCH_ADDRESSES)
        self.assertIn(0x82A6E9, WATCH_PCS)
        self.assertIn(0x82A6EB, WATCH_PCS)
        self.assertEqual(command.count("--watch-address"), len(WATCH_ADDRESSES))
        self.assertEqual(command.count("--watch-pc"), len(WATCH_PCS))

    def test_worker_variation_is_only_right_release_at_1662(self):
        path = ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1662.json"
        document = json.loads(path.read_text())
        right = [event for event in document["inputs"]["controllers"][0]["events"] if event["buttons"] == ["right"]]
        self.assertEqual(right, [
            {"from": 1650, "to": 1661, "buttons": ["right"]},
            {"from": 1663, "to": 3299, "buttons": ["right"]},
        ])
        self.assertIn("through frame 1661", document["tested_behavior"])
        self.assertIn("frame 1662", document["tested_behavior"])
        self.assertEqual(len(hashlib.sha256(path.read_bytes()).hexdigest()), 64)

    def test_signed_wrapped_division_and_remainder_order(self):
        crossing = integrate_axis(100, 17, -27)
        self.assertEqual((crossing["wrapped_total"], crossing["quotient"], crossing["remainder"]), (-10, 0, -10))
        negative = integrate_axis(100, -32, -1)
        self.assertEqual((negative["position"], negative["quotient"], negative["remainder"]), (99, -1, -1))
        wrapped = integrate_axis(0x7FFF, 0x7FFF, 1, 0x3FFF)
        self.assertEqual((wrapped["wrapped_total"], wrapped["unmasked_position"], wrapped["position"]), (-32768, 0x7BFF, 0x3BFF))
        with self.assertRaisesRegex(ValueError, "sign crossing"):
            integrate_axis(100, -32768, -1)

    def test_reseeding_or_changing_rider_chain_changes_result(self):
        first = integrate_axis(9200, 24, -1)
        recurrent = integrate_axis(9200, 48, first["remainder"])
        reseeded = integrate_axis(9200, 48, -1)
        swapped = integrate_axis(9200, 48, -24)
        self.assertNotEqual(recurrent, reseeded)
        self.assertNotEqual(recurrent, swapped)

    def test_mask_is_applied_after_wrapped_position_add(self):
        result = integrate_axis(0x7FFF, 32, 0, 0x3FFF)
        self.assertEqual((result["unmasked_position"], result["position"]), (0x8000, 0))
        self.assertNotEqual(result["position"], integrate_axis(0x7FFF, 32, 0)["position"])

    def test_slope_tail_preserves_guard_and_adjustment_order(self):
        self.assertEqual(slope_tail(100, 0, 0, 0, 0, 1, 0)["adjustment"], 0)
        self.assertEqual(slope_tail(100, 1, 1, 0, 0, 1, 0)["reason"], "guard_nonzero")
        self.assertEqual(slope_tail(100, 1, 0, 2, 0, 1, 0)["reason"], "unsupported_count_at_least_two")
        self.assertEqual(slope_tail(100, 1, 0, 0, 0x8000, 1, 0)["reason"], "direction_high_bit")
        self.assertEqual(slope_tail(100, 1, 0, 0, 0, -1, 0)["position"], 99)
        self.assertEqual(slope_tail(100, 1, 0, 0, 0, 1, 1)["position"], 101)
        self.assertEqual(slope_tail(100, 1, 0, 0, 0, 1, 0)["position"], 104)

    def test_authored_manifest_is_exact_bound(self):
        paths = [
            ROOT / "tests/manifests/native/zoom-zoo-position-primary.reference.json",
            ROOT / "tests/manifests/native/zoom-zoo-position-right-release-1662.reference.json",
        ]
        mutations = {
            "access": lambda d: d.update(access_sha256="0" * 64),
            "calls": lambda d: d.update(calls=101),
            "seed": lambda d: d["seed"]["values"].update(player_x_residue=0),
            "row": lambda d: d.update(rows_sha256="0" * 64),
            "branches": lambda d: d["slope_tail_counts"].update(ordinary_positive=19),
            "routine": lambda d: d["routine"].update(bytes=208),
            "description": lambda d: d.update(description="stateless"),
            "limits": lambda d: d.update(limits="native ZOOM ZOO support"),
        }
        for path in paths:
            document = json.loads(path.read_text())
            validate_component_manifest(document)
            for name, mutation in mutations.items():
                with self.subTest(path=path.name, name=name), self.assertRaises(ValueError):
                    changed = copy.deepcopy(document)
                    mutation(changed)
                    validate_component_manifest(changed)

    def test_call_loss_or_rider_swap_rejects(self):
        rows = [[frame, 0, 0, rider * 2] for frame in range(1650, 1701) for rider in (0, 1)]
        access = {"watch_pcs": {str(0x82A627): rows}}
        validate_call_order(access)
        lost = copy.deepcopy(access)
        lost["watch_pcs"][str(0x82A627)].pop(20)
        with self.assertRaisesRegex(ValueError, "call order"):
            validate_call_order(lost)
        swapped = copy.deepcopy(access)
        swapped_rows = swapped["watch_pcs"][str(0x82A627)]
        swapped_rows[20], swapped_rows[21] = swapped_rows[21], swapped_rows[20]
        with self.assertRaisesRegex(ValueError, "call order"):
            validate_call_order(swapped)


if __name__ == "__main__":
    unittest.main()
