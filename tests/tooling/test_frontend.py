from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from unirally_lab import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK
from unirally_lab.content import pack
from unirally_lab.frontend import commands

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "tools" / "project.py"


class FrontendLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.rom = b"authored-rom"
        entry = b"entry"
        self.rules = {
            "schema_version": 1,
            "kind": "classic_pack_rules",
            "profile_id": pack.PROFILE_ID,
            "start_state_id": pack.START_STATE_ID,
            "source_rom": {"size": len(self.rom), "sha256": hashlib.sha256(self.rom).hexdigest()},
            "entries": [{"id": "test.entry",
                         "source": {"kind": "raw", "pieces": [{"file_offset": 0, "length": len(entry)}]},
                         "size": len(entry), "sha256": hashlib.sha256(self.rom[:len(entry)]).hexdigest()}],
        }
        self.rules_path = self.root / "rules.json"
        self.rules_path.write_text(json.dumps(self.rules))
        self.rom_path = self.root / "rom.sfc"
        self.rom_path.write_bytes(self.rom)

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **changed):
        values = dict(pack=str(self.root / "classic.pack"), rom=None, preset="app-debug",
                      executable="/usr/bin/true", rules=str(self.rules_path), updates=1,
                      fixed_controller_mask=None, hidden=True, timeout=10,
                      report=None, task="M3-03")
        values.update(changed)
        return Namespace(**values)

    def test_first_launch_then_pack_only_relaunch(self):
        self.assertEqual(commands.cmd_run(self.args(rom=str(self.rom_path))), EXIT_OK)
        self.rom_path.unlink()
        self.assertEqual(commands.cmd_run(self.args(rom=None)), EXIT_OK)

    def test_cancel_missing_wrong_and_corrupt_inputs_fail(self):
        self.assertEqual(commands.cmd_run(self.args()), EXIT_MISSING_PREREQUISITE)
        self.assertEqual(commands.cmd_run(self.args(rom="")), EXIT_MISSING_PREREQUISITE)
        self.assertEqual(commands.cmd_run(self.args(rom=str(self.root / "missing.sfc"))), EXIT_MISSING_PREREQUISITE)
        wrong = self.root / "wrong.sfc"
        wrong.write_bytes(b"wrong")
        self.assertEqual(commands.cmd_run(self.args(rom=str(wrong))), EXIT_INVALID_INPUT)
        Path(self.args().pack).write_bytes(b"corrupt")
        self.assertEqual(commands.cmd_run(self.args(rom=str(self.rom_path))), EXIT_INVALID_INPUT)

    def test_frontend_failure_is_not_a_successful_launch(self):
        self.assertEqual(commands.cmd_run(self.args(rom=str(self.rom_path), executable="/usr/bin/false")), EXIT_FAILURE)

    def test_nonfinite_timeout_reports_without_starting_child(self):
        for index, timeout in enumerate((float("nan"), float("inf"), float("-inf"))):
            with self.subTest(timeout=timeout):
                report = self.root / f"nonfinite-{index}.json"
                with mock.patch.object(commands, "run_bounded") as child:
                    status = commands.cmd_run(self.args(timeout=timeout, report=str(report)))
                self.assertEqual(status, EXIT_INVALID_INPUT)
                child.assert_not_called()
                self.assertTrue(report.is_file())
                document = json.loads(report.read_text())
                self.assertEqual(document["status"], "failed")
                check = next(c for c in document["checks"] if c["name"] == "arguments")
                self.assertEqual(check["outcome"], "failed")
                self.assertIn("finite and positive", check["detail"])

    def test_cli_nonfinite_timeout_spellings_report_without_starting_child(self):
        marker = self.root / "child-started"
        child = self.root / "child"
        child.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('started')\n"
        )
        child.chmod(0o755)
        spellings = (("nan",), ("inf",), ("-inf",), ("--equals", "-inf"))
        for index, spelling in enumerate(spellings):
            with self.subTest(spelling=spelling):
                report = self.root / f"cli-nonfinite-{index}.json"
                timeout_arguments = (
                    [f"--timeout={spelling[1]}"]
                    if spelling[0] == "--equals"
                    else ["--timeout", spelling[0]]
                )
                result = subprocess.run(
                    [sys.executable, str(PROJECT), "frontend", "run",
                     "--pack", str(self.root / "absent.pack"),
                     "--executable", str(child), "--report", str(report),
                     *timeout_arguments],
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, EXIT_INVALID_INPUT,
                                 result.stderr)
                self.assertTrue(report.is_file())
                self.assertEqual(json.loads(report.read_text())["status"],
                                 "failed")
                self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
