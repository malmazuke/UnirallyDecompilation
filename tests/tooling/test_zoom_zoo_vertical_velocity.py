import hashlib
import copy
import json
from pathlib import Path
import unittest

from tools.unirally_lab.native.zoom_zoo_vertical_velocity import (
    MOTION_PC_RANGE, PRIMARY, VARIATION, VELOCITY_WATCH_ADDRESSES,
    WATCH_ADDRESSES, WATCH_PCS, capture_command,
    evaluate_bounded_jump, evaluate_vertical_cap, validate_component_manifest,
    validate_domain_writer_inventory,
    validate_pose_consumption, validate_recurrence_chain,
    validate_velocity_event_sequence,
)


ROOT = Path(__file__).resolve().parents[2]


class ZoomZooVerticalVelocityPreregistrationTests(unittest.TestCase):
    @staticmethod
    def _semantic_events():
        event = lambda sequence, pc, kind, address, value=0, width=2: (
            sequence, pc, kind, address, width, value)
        boundaries = {
            "persistent_load": event(1, 0x828B9D, "read", 0x04BF),
            "scratch_load": event(2, 0x828BA0, "write", 0x0FAB),
            "scratch_publication": event(70, 0x828E9D, "read", 0x0FAB),
            "persistent_publication": event(71, 0x828EA0, "write", 0x04BF),
            "contact_persistent_load": event(80, 0x818D64, "read", 0x04BF),
            "contact_scratch_load": event(81, 0x818D67, "write", 0x0FAB),
            "contact_publication": event(91, 0x818E28, "write", 0x04BF),
        }
        jump_events = [
            event(10, 0x82A8D8, "read", 0x0F41),
            event(20, 0x82A96B, "write", 0x0FA5),
        ]
        result = {
            "frame": 1650, "rider": 0, "boundaries": boundaries,
            "jump_events": jump_events, "jump_state": jump_events[-1],
            "gravity_input": event(30, 0x82A97E, "read", 0x0FAB),
            "gravity_write": event(40, 0x82A9AA, "write", 0x0FAB, 19),
            "cap_input": event(50, 0x82A832, "read", 0x0FAB, 19),
            "cap_writes": [],
            "boost_input": event(55, 0x82A86C, "read", 0x11DD),
            "boost_writes": [],
            "integrator": event(60, 0x82A674, "read", 0x0FAB, 19),
            "contact_response": event(90, 0x81970B, "write", 0x0FAB),
        }
        result["motion_writers"] = [boundaries["scratch_load"], result["gravity_write"]]
        result["contact_writers"] = [boundaries["contact_scratch_load"],
                                     result["contact_response"]]
        return result

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
                         "contact_output": incoming, "response_b": 0,
                         "writer_evidence": {}, "composition": {}})
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

    def test_pose_consumer_rejects_value_width_missing_and_duplicate(self):
        pose = (10, 0x83F00D, "read", 0x0F57, 2, 7)
        self.assertEqual(validate_pose_consumption([pose], 7), 7)
        for changed in (
                [pose[:5] + (8,)],
                [pose[:4] + (1, 7)],
                [], [pose, pose]):
            with self.subTest(events=changed), self.assertRaises(ValueError):
                validate_pose_consumption(changed, 7)

    def test_reviewer_semantic_mutations_reject_without_access_digest(self):
        validate_velocity_event_sequence(**self._semantic_events())
        boundary_widths = (
            "scratch_load", "persistent_publication",
            "contact_scratch_load", "contact_publication",
        )
        for boundary_name in boundary_widths:
            changed = self._semantic_events()
            original = changed["boundaries"][boundary_name]
            replacement = original[:4] + (1,) + original[5:]
            changed["boundaries"][boundary_name] = replacement
            changed["motion_writers"] = [changed["boundaries"]["scratch_load"],
                                         changed["gravity_write"]]
            changed["contact_writers"] = [
                changed["boundaries"]["contact_scratch_load"],
                changed["contact_response"],
            ]
            with self.subTest(width=boundary_name), self.assertRaises(ValueError):
                validate_velocity_event_sequence(**changed)

        changed = self._semantic_events()
        changed["cap_input"] = (35,) + changed["cap_input"][1:]
        with self.assertRaises(ValueError):
            validate_velocity_event_sequence(**changed)

        changed = self._semantic_events()
        same_value_extra = (45, 0x82AAAA, "write", 0x0FAB, 2, 19)
        changed["motion_writers"].append(same_value_extra)
        with self.assertRaises(ValueError):
            validate_velocity_event_sequence(**changed)

    def test_writer_inventory_rejects_missing_duplicate_and_unclassified(self):
        mutations = []
        missing_motion = self._semantic_events()
        missing_motion["motion_writers"].pop()
        mutations.append(("missing motion", missing_motion))
        duplicate_motion = self._semantic_events()
        duplicate_motion["motion_writers"].append(duplicate_motion["gravity_write"])
        mutations.append(("duplicate motion", duplicate_motion))
        missing_contact = self._semantic_events()
        missing_contact["contact_writers"].pop()
        mutations.append(("missing contact", missing_contact))
        duplicate_contact = self._semantic_events()
        duplicate_contact["contact_writers"].append(duplicate_contact["contact_response"])
        mutations.append(("duplicate contact", duplicate_contact))
        unclassified_contact = self._semantic_events()
        unclassified_contact["contact_writers"].append(
            (89, 0x819999, "write", 0x0FAB, 2, 0))
        mutations.append(("unclassified contact", unclassified_contact))
        for name, changed in mutations:
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate_velocity_event_sequence(**changed)

        baseline = self._semantic_events()
        classified = baseline["motion_writers"] + baseline["contact_writers"]
        frame_events = sorted(classified, key=lambda event: event[0])
        validate_domain_writer_inventory(frame_events, classified, 1650)
        outside_intervals = frame_events + [
            (100, 0x829999, "write", 0x0FAB, 2, 0)
        ]
        with self.assertRaises(ValueError):
            validate_domain_writer_inventory(outside_intervals, classified, 1650)


if __name__ == "__main__":
    unittest.main()
