import hashlib
import json
from pathlib import Path
import unittest

from tools.unirally_lab.native.zoom_zoo_response_b import (
    PRIMARY, PRODUCER_PC_RANGE, POSE_PC_RANGE, RESPONSE_WATCH_ADDRESSES,
    VARIATION, WATCH_ADDRESSES, WATCH_PCS, capture_command,
)


ROOT = Path(__file__).resolve().parents[2]


class ZoomZooResponseBPreregistrationTests(unittest.TestCase):
    def test_capture_retains_composition_and_full_producer_consumer_ranges(self):
        command = capture_command(ROOT / PRIMARY, Path("artifacts/m4-10/test"))
        for address in (0x0BB7, 0x0BB9, 0x0F55, 0x0F57, 0x0300, 0x0302, 0x04C7):
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
            "sample_digest": "0" * 64, "final_state_sha256": "0" * 64,
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
                         "e246ab346d2f9acca21bb0212e0b78c908dea3f94a9d823e809f4ae71bafcc92")


if __name__ == "__main__":
    unittest.main()
