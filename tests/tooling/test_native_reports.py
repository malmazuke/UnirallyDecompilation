"""Prove the test command reports native failures and timeouts as such.

Needs the isolated toolchain (bootstrap). Without it the checks are skipped,
and a skip is reported as a skip, never as a pass.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab import EXIT_OK, EXIT_TIMEOUT  # noqa: E402
from unirally_lab import toolchain  # noqa: E402

PROJECT = ROOT / "tools" / "project.py"
MANIFEST = ROOT / "local" / "toolchain" / "manifest.json"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROJECT), *args], capture_output=True, text=True, timeout=900)


@unittest.skipUnless(toolchain.load_manifest(MANIFEST), "isolated toolchain not bootstrapped")
class NativeReportTests(unittest.TestCase):
    def test_failure_and_timeout_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "build.json"
            r = run_cli("build", "--preset", "lab-failure-probe", "--report", str(report))
            self.assertEqual(r.returncode, EXIT_OK, r.stderr[-2000:])
            report = Path(tmp) / "test.json"
            r = run_cli("test", "--suite", "synthetic", "--preset", "lab-failure-probe", "--no-python-tests",
                        "--artifacts", str(Path(tmp) / "art"), "--report", str(report), "--test-timeout", "1")
            self.assertEqual(r.returncode, EXIT_TIMEOUT, r.stderr[-2000:])
            rep = json.loads(report.read_text())
            self.assertEqual(rep["status"], "failed")
            outcomes = {c["name"]: c["outcome"] for c in rep["checks"]}
            self.assertEqual(outcomes["ctest:lab_probe_expected_failure"], "failed")
            self.assertEqual(outcomes["ctest:lab_probe_expected_timeout"], "timeout")
            self.assertEqual(outcomes["ctest:lab_state_known_hash"], "passed")
            self.assertEqual(outcomes["python_tooling_tests"], "skipped")
            self.assertEqual(outcomes["native_fresh_process_repeatability"], "passed")
            self.assertEqual(rep["summary"]["failed"], 1)
            self.assertEqual(rep["summary"]["timeout"], 1)
            junit = [a for a in rep["artifacts"] if a["kind"] == "ctest_junit"]
            self.assertTrue(junit and Path(junit[0]["path"]).is_file(), "junit artifact must be recorded")

    def test_results_follow_the_current_source_not_stale_binaries(self) -> None:
        """A changed expectation must fail even when nobody ran build in between."""
        cmakelists = ROOT / "tests" / "synthetic" / "CMakeLists.txt"
        original = cmakelists.read_text()
        self.assertIn("LAB_KNOWN_HASH=0x0be347c529fadda9ull", original)
        with tempfile.TemporaryDirectory() as tmp:
            r = run_cli("build", "--preset", "lab-failure-probe")
            self.assertEqual(r.returncode, EXIT_OK, r.stderr[-2000:])
            try:
                cmakelists.write_text(original.replace("0x0be347c529fadda9ull", "0x0be347c529fadda8ull"))
                report = Path(tmp) / "test.json"
                r = run_cli("test", "--suite", "synthetic", "--preset", "lab-failure-probe", "--no-python-tests",
                            "--artifacts", str(Path(tmp) / "art"), "--report", str(report))
            finally:
                cmakelists.write_text(original)
            self.assertNotEqual(r.returncode, EXIT_OK)
            rep = json.loads(report.read_text())
            outcomes = {c["name"]: c["outcome"] for c in rep["checks"]}
            self.assertEqual(outcomes["ctest:lab_state_known_hash"], "failed")
            self.assertTrue(rep["source"]["dirty"])
            self.assertEqual(rep["build"]["source"]["dirty_diff_sha256"], rep["source"]["dirty_diff_sha256"])
        # Restore the binaries for later runs.
        self.assertEqual(run_cli("build", "--preset", "lab-failure-probe").returncode, EXIT_OK)

    def test_failed_build_is_not_reported_as_available(self) -> None:
        source = ROOT / "src" / "lab" / "lab_state.cpp"
        original = source.read_text()
        with tempfile.TemporaryDirectory() as tmp:
            # Each test builds what it needs; test order and prior runs must not matter.
            self.assertEqual(run_cli("build", "--preset", "lab-failure-probe").returncode, EXIT_OK)
            try:
                source.write_text(original + "\nthis is not C++\n")
                report = Path(tmp) / "test.json"
                r = run_cli("test", "--suite", "synthetic", "--preset", "lab-failure-probe", "--no-python-tests",
                            "--artifacts", str(Path(tmp) / "art"), "--report", str(report))
            finally:
                source.write_text(original)
            self.assertNotEqual(r.returncode, EXIT_OK)
            rep = json.loads(report.read_text())
            outcomes = {c["name"]: c["outcome"] for c in rep["checks"]}
            self.assertEqual(outcomes["native_build_available"], "failed")
            self.assertNotIn("ctest:lab_state_known_hash", outcomes)
            self.assertEqual(rep["build"]["outcome"], "failed")
        self.assertEqual(run_cli("build", "--preset", "lab-failure-probe").returncode, EXIT_OK)

    def test_nested_run_with_python_tests_is_refused(self) -> None:
        import os
        env = {**os.environ, "UNIRALLY_LAB_NESTED_TEST": "1"}
        r = subprocess.run([sys.executable, str(PROJECT), "test", "--suite", "synthetic"],
                           capture_output=True, text=True, timeout=120, env=env)
        self.assertEqual(r.returncode, 3)
        self.assertIn("recursive invocation", r.stderr)


if __name__ == "__main__":
    unittest.main()
