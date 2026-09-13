"""ROM-free checks for the preregistered M4-09 composition capture."""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.native.zoom_zoo_composition import (  # noqa: E402
    FIRST_CALL_FRAME, LAST_CALL_FRAME, WATCH_ADDRESSES, WATCH_PCS,
    Y_ADJUSTMENT_PCS, capture_command,
)


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
        self.assertEqual(document["expected"], {
            "sample_digest": "0" * 64, "final_state_sha256": "0" * 64,
        })


if __name__ == "__main__":
    unittest.main()
