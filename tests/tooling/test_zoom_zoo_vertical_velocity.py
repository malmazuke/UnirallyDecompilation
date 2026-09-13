import hashlib
import json
from pathlib import Path
import unittest

from tools.unirally_lab.native.zoom_zoo_vertical_velocity import (
    MOTION_PC_RANGE, PRIMARY, VARIATION, VELOCITY_WATCH_ADDRESSES,
    WATCH_ADDRESSES, WATCH_PCS, capture_command,
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
            "sample_digest": "0" * 64, "final_state_sha256": "0" * 64,
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
                         "8d993da929f2cc7810bd97b6eb2188b857004b638d2408b6220bd4103560c933")


if __name__ == "__main__":
    unittest.main()
