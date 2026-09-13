import hashlib
import copy
import json
from pathlib import Path
import unittest

from tools.unirally_lab.native.zoom_zoo_response_b import (
    PRIMARY, PRODUCER_PC_RANGE, POSE_PC_RANGE, RESPONSE_WATCH_ADDRESSES,
    VARIATION, WATCH_ADDRESSES, WATCH_PCS, capture_command,
    evaluate_active_producer, validate_component_manifest,
    validate_recurrence_chain,
)


ROOT = Path(__file__).resolve().parents[2]


class ZoomZooResponseBPreregistrationTests(unittest.TestCase):
    def test_capture_retains_composition_and_full_producer_consumer_ranges(self):
        command = capture_command(ROOT / PRIMARY, Path("artifacts/m4-10/test"))
        for address in (0x0BB7, 0x0BB9, 0x0F55, 0x0F57, 0x0300, 0x0302,
                        0x031D, 0x031F, 0x04C7, 0x1003, 0x1005):
            self.assertIn(address, RESPONSE_WATCH_ADDRESSES)
            self.assertIn(address, WATCH_ADDRESSES)
        self.assertEqual(PRODUCER_PC_RANGE, list(range(0x82A49F, 0x82A5FA)))
        self.assertEqual(POSE_PC_RANGE, list(range(0x83EF54, 0x83F0FB)))
        for pc in PRODUCER_PC_RANGE + POSE_PC_RANGE:
            self.assertIn(pc, WATCH_PCS)
        self.assertEqual(command.count("--watch-address"), len(WATCH_ADDRESSES))
        self.assertEqual(command.count("--watch-pc"), len(WATCH_PCS))

    def test_worker_variation_releases_right_only_at_1668(self):
        primary = json.loads((ROOT / PRIMARY).read_text())
        variation_path = ROOT / VARIATION
        variation = json.loads(variation_path.read_text())
        self.assertEqual(variation["expected"], {
            "sample_digest": "f616369d41063af61b8cc567c1d2ca4b3c2748b117cb25a67826a271a6705d32",
            "final_state_sha256": "201a4bbd64e6080ef4ffab95505133af0614eda640935514005cfeb53935e1bc",
        })
        self.assertIn("exact primary evidence through frame 1667", variation["tested_behavior"])
        self.assertIn("frame 1668 only", variation["tested_behavior"])

        def buttons(document, frame):
            return tuple(sorted(button for event in document["inputs"]["controllers"][0]["events"]
                                if event["from"] <= frame <= event["to"]
                                for button in event["buttons"]))

        differences = [frame for frame in range(3300)
                       if buttons(primary, frame) != buttons(variation, frame)]
        self.assertEqual(differences, [1668])
        self.assertEqual(hashlib.sha256(variation_path.read_bytes()).hexdigest(),
                         "852351c866a35462caddf07bb58338e3887fe342ad2bf6c6059cc1018552d898")

    def test_byte_word_width_and_high_byte_preservation_are_explicit(self):
        base = {"f1b": 1, "f1d": 0, "surface_angle": 31,
                "unsupported_count": 0, "guard_f49": 0, "guard_f89": 0,
                "mode_f23": 0, "special_f5d": 0, "indexed_control": 1}
        self.assertEqual(evaluate_active_producer(0xAB00, base), {
            "branch": "low_byte_fe_plus_control", "width": 1, "value": 0xABFF,
        })
        cleared = dict(base, f1b=0, f1d=0, surface_angle=0)
        self.assertEqual(evaluate_active_producer(0xABFE, cleared), {
            "branch": "word_clear_low_angle_count", "width": 2, "value": 0,
        })
        short_circuit_clear = dict(cleared, f1d=None, indexed_control=None)
        self.assertEqual(evaluate_active_producer(0xABFE, short_circuit_clear), {
            "branch": "word_clear_low_angle_count", "width": 2, "value": 0,
        })
        zero_pair = dict(base, f1b=0, f1d=0, indexed_control=None)
        self.assertEqual(evaluate_active_producer(0xABFE, zero_pair), {
            "branch": "word_clear_zero_pair", "width": 2, "value": 0,
        })
        with self.assertRaises(ValueError):
            evaluate_active_producer(0xABFE, dict(base, indexed_control=None))
        preserved = dict(base, mode_f23=1)
        self.assertEqual(evaluate_active_producer(0xABFE, preserved), {
            "branch": "preserve_mode", "width": None, "value": 0xABFE,
        })

    def test_authored_manifests_are_exact_bound(self):
        for name in ("zoom-zoo-response-b-primary.reference.json",
                     "zoom-zoo-response-b-right-release-1668.reference.json"):
            document = json.loads((ROOT / "tests/manifests/native" / name).read_text())
            validate_component_manifest(document)
            for mutation in (
                lambda d: d["seed"].update(player_response_b=1),
                lambda d: d["producer_routine"].update(bytes=346),
                lambda d: d["composition"].update(points=1019),
                lambda d: d["external_producer_inputs"].remove("indexed_control"),
                lambda d: d.update(captured_response_b_substitution=True),
            ):
                changed = copy.deepcopy(document)
                mutation(changed)
                with self.assertRaises(ValueError):
                    validate_component_manifest(changed)

    def test_chain_mutations_reject_seed_rider_phase_writer_reseed_and_order(self):
        clear_inputs = {"f1b": 0, "f1d": 0, "surface_angle": 0,
                        "unsupported_count": 0, "guard_f49": None, "guard_f89": None,
                        "mode_f23": None, "special_f5d": None, "indexed_control": 0}
        rows = []
        recurrent = {0: 0, 1: 254}
        for ordinal in range(4):
            rider = ordinal & 1
            phase = 1 if ordinal < 2 else 0
            active = rider == 1 - phase
            producer = (evaluate_active_producer(recurrent[rider], clear_inputs)
                        if active else {"branch": "inactive_preserve", "width": None,
                                        "value": recurrent[rider]})
            output = int(producer["value"])
            rows.append({"ordinal": ordinal, "frame": 1650 + ordinal // 2,
                         "rider": rider, "phase_0302": phase, "active": active,
                         "recurrent_input": recurrent[rider],
                         "producer_inputs": clear_inputs if active else None,
                         "producer": producer, "pose_consumed": output,
                         "motion_publication": output, "contact_input": output,
                         "contact_output": output})
            recurrent[rider] = output
        validate_recurrence_chain(rows, {0: 0, 1: 254})
        mutations = [
            lambda d: d[0].update(rider=1),
            lambda d: d[0].update(phase_0302=0),
            lambda d: d[0]["producer"].update(width=None),
            lambda d: d[2].update(recurrent_input=7),
            lambda d: d[0].update(contact_input=7),
            lambda d: d[0].update(ordinal=1),
            lambda d: d[0].update(captured_response_b=0),
        ]
        for mutation in mutations:
            changed = copy.deepcopy(rows)
            mutation(changed)
            with self.assertRaises(ValueError):
                validate_recurrence_chain(changed, {0: 0, 1: 254})


if __name__ == "__main__":
    unittest.main()
