import hashlib
import copy
import json
from pathlib import Path
import unittest

from tools.unirally_lab.native.zoom_zoo_vertical_velocity import (
    MOTION_PC_RANGE, PRIMARY, VARIATION, VELOCITY_WATCH_ADDRESSES,
    WATCH_ADDRESSES, WATCH_PCS, capture_command,
    evaluate_bounded_jump, evaluate_vertical_cap, validate_component_manifest,
    validate_recurrence_chain,
)


ROOT = Path(__file__).resolve().parents[2]


class ZoomZooVerticalVelocityPreregistrationTests(unittest.TestCase):
    def test_capture_retains_m4_10_and_complete_motion_range(self):
        command = capture_command(ROOT / PRIMARY, Path("artifacts/m4-11/test"))
        for address in (0x04BF, 0x04C1, 0x0FAB, 0x0F91, 0x0F93, 0x0F95,
                        0x0FA5, 0x11DD, 0x11DF, 0x11E1, 0x0302, 0x0FF9):
            self.assertIn(address, VELOCITY_WATCH_ADDRESSES)
            self.assertIn(address, WATCH_ADDRESSES)
        self.assertEqual(MOTION_PC_RANGE, list(range(0x82A81A, 0x82A9B3)))
        for pc in MOTION_PC_RANGE:
            self.assertIn(pc, WATCH_PCS)
        self.assertEqual(command.count("--watch-address"), len(WATCH_ADDRESSES))
        self.assertEqual(command.count("--watch-pc"), len(WATCH_PCS))

    def test_worker_variation_releases_right_only_at_1672(self):
        primary = json.loads((ROOT / PRIMARY).read_text())
        variation_path = ROOT / VARIATION
        variation = json.loads(variation_path.read_text())
        self.assertEqual(variation["expected"], {
            "sample_digest": "66c45999667bda235318f90ca883ba56046a86dc8f999100fd0d287b2f410fe2",
            "final_state_sha256": "037fee6dd7e6003ebca34ab45a16d7b70c95ac554d4d48b68658877df697eb00",
        })
        self.assertIn("exact primary evidence through frame 1671", variation["tested_behavior"])
        self.assertIn("frame 1672 only", variation["tested_behavior"])

        def buttons(document, frame):
            return tuple(sorted(button for event in document["inputs"]["controllers"][0]["events"]
                                if event["from"] <= frame <= event["to"]
                                for button in event["buttons"]))

        differences = [frame for frame in range(3300)
                       if buttons(primary, frame) != buttons(variation, frame)]
        self.assertEqual(differences, [1672])
        self.assertEqual(hashlib.sha256(variation_path.read_bytes()).hexdigest(),
                         "c6dcb0e542feeae04c02c9d425072852c32d31a40bae149ffcb753265b16347a")

    def test_vertical_cap_uses_wrapped_signed_predicates_and_word_semantics(self):
        self.assertEqual(evaluate_vertical_cap(900, 0, 1, 0)["velocity_y"], 768)
        self.assertEqual(evaluate_vertical_cap(-900, 0, 1, 0)["velocity_y"], 0xFD00)
        preserved = evaluate_vertical_cap(0xFFF0, 62, 1, 0)
        self.assertEqual(preserved["velocity_y"], 0xFFF0)
        self.assertFalse(preserved["vertical_boost_written"])
        decremented = evaluate_vertical_cap(0, 0, 1, 0x0080)
        self.assertEqual(decremented["vertical_boost_output"], 0x007F)
        self.assertTrue(decremented["vertical_boost_written"])
        with self.assertRaises(ValueError):
            evaluate_vertical_cap(0, 0, 2, 0)

    def test_jump_short_circuits_keep_unread_inputs_unavailable(self):
        short = {"indexed_inhibit": 1, "guard_f41": None, "special_f5d": None,
                 "direction_f31": None, "held_phase": None, "jump_latch": None,
                 "previous_input": None, "current_input": None, "unsupported_count": None}
        self.assertEqual(evaluate_bounded_jump(0xFF00, short), {
            "branch": "preserve_indexed_inhibit", "velocity_y": 0xFF00,
            "previous_input_publication": None,
        })
        reached = {"indexed_inhibit": 0, "guard_f41": 0, "special_f5d": 0,
                   "direction_f31": 0, "held_phase": 0, "jump_latch": 0,
                   "previous_input": 0, "current_input": 0, "unsupported_count": None}
        self.assertEqual(evaluate_bounded_jump(19, reached)["branch"], "neutral_no_arm")
        with self.assertRaises(ValueError):
            evaluate_bounded_jump(19, dict(reached, current_input=1))

    def test_authored_manifests_are_exact_bound(self):
        for name in ("zoom-zoo-vertical-velocity-primary.reference.json",
                     "zoom-zoo-vertical-velocity-right-release-1672.reference.json"):
            document = json.loads((ROOT / "tests/manifests/native" / name).read_text())
            validate_component_manifest(document)
            for mutation in (
                lambda d: d["seed"].update(player_velocity_y=1),
                lambda d: d["routines"]["vertical_cap"].update(bytes=88),
                lambda d: d["writer_counts"].update(gravity_velocity=101),
                lambda d: d["phase_order"].reverse(),
                lambda d: d["external_inputs"].remove("jump_and_control_state"),
                lambda d: d.update(captured_velocity_substitution=True),
            ):
                changed = copy.deepcopy(document)
                mutation(changed)
                with self.assertRaises(ValueError):
                    validate_component_manifest(changed)

    def test_chain_rejects_reseed_rider_order_and_captured_substitution(self):
        rows = []
        seed = {0: 0, 1: 0xFF00}
        for ordinal in range(2):
            rider = ordinal
            incoming = seed[rider]
            gravity = {"velocity_y": incoming}
            cap = {"velocity_y": incoming}
            rows.append({"ordinal": ordinal, "frame": 1650, "rider": rider,
                         "phase_0302": 1, "active": rider == 0,
                         "recurrent_input": incoming, "jump_inputs": {} if rider == 0 else None,
                         "post_jump": {"velocity_y": incoming}, "gravity": gravity,
                         "cap": cap, "integrator_input": incoming,
                         "motion_publication": incoming, "contact_input": incoming,
                         "contact_output": incoming, "response_b": 0, "composition": {}})
        validate_recurrence_chain(rows, seed)
        for mutation in (
            lambda d: d[0].update(rider=1),
            lambda d: d[0].update(recurrent_input=7),
            lambda d: d[0].update(integrator_input=7),
            lambda d: d[0].update(ordinal=1),
            lambda d: d[0].update(captured_velocity_y=0),
        ):
            changed = copy.deepcopy(rows)
            mutation(changed)
            with self.assertRaises(ValueError):
                validate_recurrence_chain(changed, seed)


if __name__ == "__main__":
    unittest.main()
