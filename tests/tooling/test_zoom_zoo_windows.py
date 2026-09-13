"""ROM-free checks for bounded M4-04 access-window commands."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/"tools"))
from unirally_lab.native.zoom_zoo_windows import WATCH_ADDRESSES, WATCH_PCS, WINDOWS, command  # noqa:E402


class ZoomZooWindowTests(unittest.TestCase):
    def test_only_six_three_frame_windows_are_declared(self):
        self.assertEqual(set(WINDOWS),{"start","reward","up-entry","up-exit","release-entry","release-exit"})
        self.assertTrue(all(end-start==2 for _manifest,start,end in WINDOWS.values()))

    def test_command_has_identity_bound_manifest_and_no_broad_series(self):
        for name,(manifest,start,end) in WINDOWS.items():
            cmd=command(name,Path("artifacts/test")/name)
            self.assertEqual(cmd[cmd.index("--manifest")+1],manifest)
            self.assertEqual((int(cmd[cmd.index("--from-frame")+1]),int(cmd[cmd.index("--to-frame")+1])),(start,end))
            self.assertNotIn("--wram-series-range",cmd)
            self.assertEqual(cmd.count("--watch-address"),len(WATCH_ADDRESSES))
            self.assertEqual(cmd.count("--watch-pc"),len(WATCH_PCS))


if __name__=="__main__":unittest.main()
