"""ROM-free checks for the preregistered M4-09 composition capture."""
from pathlib import Path
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.native.zoom_zoo_composition import (  # noqa: E402
    EXTERNAL_FIELDS, FIRST_CALL_FRAME, LAST_CALL_FRAME, PHASE_ORDER,
    WATCH_ADDRESSES, WATCH_PCS, Y_ADJUSTMENT_PCS, _helper_events,
    capture_command, integrate_composed_axis, reached_y_adjustment,
    sample_track, validate_component_manifest,
)
from unirally_lab.native.zoom_zoo_contact import compare_preprocessing  # noqa: E402


class ZoomZooCompositionPreregistrationTests(unittest.TestCase):
    def test_capture_unites_position_sampling_contact_and_y_helper(self) -> None:
        command = capture_command(
            ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-3300.json",
            Path("artifacts/test/composition"),
        )
        self.assertEqual((FIRST_CALL_FRAME, LAST_CALL_FRAME), (1650, 1700))
        self.assertEqual(command[command.index("--from-frame") + 1], "1649")
        for address in (0x00A7, 0x0547, 0x0549, 0x0F4B, 0x0FAB, 0x0FF9):
            self.assertIn(address, WATCH_ADDRESSES)
        for pc in (0x82A96F, 0x82A9B0, 0x82A61F, 0x818B75, 0x818F98):
            self.assertIn(pc, WATCH_PCS)
        self.assertEqual(len(Y_ADJUSTMENT_PCS), 34)
        self.assertEqual(command.count("--watch-address"), len(WATCH_ADDRESSES))
        self.assertEqual(command.count("--watch-pc"), len(WATCH_PCS))

    def test_worker_variation_releases_right_only_at_1666(self) -> None:
        document = json.loads((ROOT / "tests/manifests/replay/race-crawler-zoom-zoo-right-release-1666.json").read_text())
        right = [event for event in document["inputs"]["controllers"][0]["events"]
                 if event["buttons"] == ["right"]]
        self.assertEqual(right, [
            {"from": 1650, "to": 1665, "buttons": ["right"]},
            {"from": 1667, "to": 3299, "buttons": ["right"]},
        ])
        self.assertIn("through frame 1665", document["tested_behavior"])
        self.assertIn("frame 1666 only", document["tested_behavior"])
        self.assertEqual(document["expected"]["sample_digest"],
                         "080d56aa69c5232f1e1acd6745ad49719ed4d0a09af17f9845c4eaa5165c2c2e")

    def test_y_adjustment_preserves_predicate_width_and_order(self) -> None:
        negative = reached_y_adjustment(100, -68, 0, 0)
        self.assertEqual((negative["velocity_addend"], negative["velocity_y"], negative["position_y"]),
                         (19, (-49) & 0xFFFF, 101))
        positive = reached_y_adjustment(100, 196, 0, 0)
        self.assertEqual((positive["shifted_nonnegative_velocity"], positive["velocity_addend"], positive["velocity_y"]),
                         (6, 13, 209))
        self.assertFalse(reached_y_adjustment(100, 512, 0, 0)["incremented"])
        self.assertEqual(reached_y_adjustment(100, -1, 1, 0)["reason"], "first_guard_nonzero")
        self.assertEqual(reached_y_adjustment(100, -1, 0, 1)["reason"], "indexed_guard_nonzero")

    def test_new_negative_velocity_nonnegative_total_path(self) -> None:
        reached = integrate_composed_axis(1600, -10, 18)
        self.assertEqual((reached["wrapped_total"], reached["branch"], reached["position"], reached["remainder"]),
                         (8, "nonnegative", 1600, 8))
        wrong_velocity_sign_branch = integrate_composed_axis(1600, -8, -10)
        self.assertNotEqual(reached, wrong_velocity_sign_branch)

    def test_sampling_returns_exact_words_and_source_offsets(self) -> None:
        track = bytearray(0x8090)
        for block in range(4):
            track[15 + block * 2:17 + block * 2] = block.to_bytes(2, "little")
            for cell in range(16):
                value = block * 100 + cell
                offset = 0x800F + block * 32 + cell * 2
                track[offset:offset + 2] = value.to_bytes(2, "little")
        points = [(8, 8), (16, 8), (8, 16), (16, 16)]
        rows = sample_track(bytes(track), points, 48, 48, 2)
        self.assertEqual([row["word"] for row in rows], [15, 112, 203, 300])
        self.assertEqual([row["source_offset"] for row in rows],
                         [0x800F + 30, 0x800F + 32 + 24, 0x800F + 64 + 6, 0x800F + 96])
        with self.assertRaisesRegex(ValueError, "coarse-grid edge"):
            sample_track(bytes(track), points, 48, 48, 1)

    def test_contact_feedback_not_per_call_position_replacement(self) -> None:
        first = integrate_composed_axis(1000, 64, 0)
        recurrent = integrate_composed_axis(first["position"] - 3, 64, first["remainder"])
        replaced = integrate_composed_axis(first["position"], 64, first["remainder"])
        self.assertNotEqual(recurrent["position"], replaced["position"])
        self.assertNotIn("response_b", {"x", "y", "rx", "ry"})
        self.assertIn("response_b", EXTERNAL_FIELDS["contact"])
        self.assertEqual(PHASE_ORDER[-2:], ["contact", "caller_publication"])

    def test_summary_preserving_point_mutation_is_rejected(self) -> None:
        call = {
            "frame": 1, "rider": 0,
            "observed_penetrations": [0xA0] * 10,
            "observed_angles": [0] * 10,
            "observed_descriptors": [0] * 10,
        }
        compare_preprocessing(call, [(0xA0, 0, 0)] * 10)
        changed = [(0xA0, 0, 0)] * 10
        changed[8] = (0xA0, 1, 0)
        with self.assertRaisesRegex(ValueError, "computed preprocessing differs"):
            compare_preprocessing(call, changed)

    def test_missing_helper_evidence_rejects(self) -> None:
        with self.assertRaisesRegex(ValueError, "integrator entries"):
            _helper_events({"watch_addresses": {}}, 1650, 0)

    def test_authored_manifests_bind_every_result_and_external_phase(self) -> None:
        paths = [
            ROOT / "tests/manifests/native/zoom-zoo-composition-primary.reference.json",
            ROOT / "tests/manifests/native/zoom-zoo-composition-right-release-1666.reference.json",
        ]
        mutations = {
            "seed": lambda d: d["seed"]["values"].update(player_x=9201),
            "call": lambda d: d.update(calls=101),
            "rider_chain": lambda d: d["final"].update(player_x=d["final"]["opponent_x"]),
            "samples": lambda d: d.update(sample_words_sha256="0" * 64),
            "sources": lambda d: d.update(sample_sources_sha256="0" * 64),
            "increment": lambda d: d.update(helper_counts={"increment": 101, "velocity_cap": 1}),
            "feedback": lambda d: d["external_fields"]["contact"].remove("response_b"),
            "phase": lambda d: d["phase_order"].reverse(),
            "identity": lambda d: d["source"].update(access_sha256="0" * 64),
            "description": lambda d: d.update(description="autonomous gameplay"),
        }
        for path in paths:
            document = json.loads(path.read_text())
            validate_component_manifest(document)
            for name, mutation in mutations.items():
                with self.subTest(path=path.name, mutation=name), self.assertRaises(ValueError):
                    changed = copy.deepcopy(document)
                    mutation(changed)
                    validate_component_manifest(changed)


if __name__ == "__main__":
    unittest.main()
