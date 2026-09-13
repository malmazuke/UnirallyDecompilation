"""ROM-free checks for the preregistered M4-08 capture surface."""
from pathlib import Path
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from unirally_lab.native.zoom_zoo_position import (  # noqa: E402
    FIRST_CALL_FRAME, LAST_CALL_FRAME, WATCH_ADDRESSES, WATCH_PCS,
    capture_command,
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


if __name__ == "__main__":
    unittest.main()
