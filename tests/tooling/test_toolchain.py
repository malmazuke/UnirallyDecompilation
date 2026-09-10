"""Error-path and idempotency checks for bootstrap and the bounded runner. No network."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK  # noqa: E402
from unirally_lab import toolchain  # noqa: E402
from unirally_lab.procs import run_bounded  # noqa: E402

PROJECT = ROOT / "tools" / "project.py"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROJECT), *args], capture_output=True, text=True, timeout=120)


def make_wheel(path: Path, version: str = "9.9.9") -> str:
    """A fake wheel whose 'binary' is a shell script printing a version."""
    script = f"#!/bin/sh\necho fake version {version}\n"
    with zipfile.ZipFile(path, "w") as zf:
        info = zipfile.ZipInfo("fake/data/bin/fake")
        info.external_attr = 0o755 << 16
        zf.writestr(info, script)
        zf.writestr("fake/data/share/readme.txt", "synthetic\n")
        zf.writestr("fake-9.9.9.dist-info/WHEEL", "Wheel-Version: 1.0\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_lock(dest: Path, wheel: Path, sha256: str, version: str = "9.9.9") -> Path:
    lock = {
        "lock_schema_version": 1,
        "cache_dir": "cache",
        "install_dir": "toolchain",
        "tools": {
            "fake": {
                "version": version,
                "extract_prefix": "fake/data/",
                "binaries": {"fake": "bin/fake"},
                "artifacts": {
                    toolchain.platform_key(): {
                        "filename": wheel.name,
                        "url": wheel.as_uri(),
                        "sha256": sha256,
                    }
                },
            }
        },
    }
    dest.write_text(json.dumps(lock))
    return dest


class BoundedRunnerTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "process groups are POSIX")
    def test_timeout_kills_grandchildren(self) -> None:
        import signal
        import time
        child = (
            "import subprocess, sys, time; "
            "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
            "print(p.pid, flush=True); time.sleep(60)"
        )
        r = run_bounded([sys.executable, "-c", child], timeout=1.0)
        self.assertEqual(r.outcome, "timeout")
        grandchild = int(r.stdout.strip().splitlines()[0])
        deadline = time.monotonic() + 5
        alive = True
        while time.monotonic() < deadline:
            try:
                os.kill(grandchild, 0)
            except ProcessLookupError:
                alive = False
                break
            time.sleep(0.1)
        if alive:
            os.kill(grandchild, signal.SIGKILL)
        self.assertFalse(alive, "grandchild survived the timeout")

    def test_non_positive_timeout_is_rejected(self) -> None:
        r = run_bounded([sys.executable, "-c", "print(1)"], timeout=0)
        self.assertEqual(r.outcome, "timeout")

    def test_timeout_is_reported_not_raised(self) -> None:
        r = run_bounded([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.3)
        self.assertTrue(r.timed_out)
        self.assertEqual(r.outcome, "timeout")
        self.assertIsNone(r.returncode)

    def test_missing_executable_is_missing(self) -> None:
        r = run_bounded(["/nonexistent/binary-xyz"], timeout=5)
        self.assertTrue(r.missing)
        self.assertEqual(r.outcome, "missing")

    def test_nonzero_exit_is_failed(self) -> None:
        r = run_bounded([sys.executable, "-c", "import sys; sys.exit(7)"], timeout=5)
        self.assertEqual(r.outcome, "failed")
        self.assertEqual(r.returncode, 7)


@unittest.skipIf(os.name == "nt", "fake binary is a POSIX shell script")
class BootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.wheel = self.root / "fake-9.9.9-py3-none-any.whl"
        self.sha = make_wheel(self.wheel)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bootstrap_succeeds_then_reuses_cache(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, self.sha)
        report = self.root / "r1.json"
        r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock), "--report", str(report))
        self.assertEqual(r.returncode, EXIT_OK, r.stderr)
        rep = json.loads(report.read_text())
        check = next(c for c in rep["checks"] if c["name"] == "bootstrap_fake")
        self.assertEqual(check["outcome"], "passed")
        self.assertIn("source=file-copy", check["detail"])
        self.assertIn("extracted=True", check["detail"])
        manifest = json.loads((self.root / "toolchain" / "manifest.json").read_text())
        self.assertEqual(manifest["tools"]["fake"]["sha256"], self.sha)
        self.assertTrue(Path(manifest["tools"]["fake"]["binaries"]["fake"]).is_file())
        self.assertEqual(manifest["lock_sha256"], hashlib.sha256(lock.read_bytes()).hexdigest())
        # Second run: nothing downloaded or re-extracted.
        report2 = self.root / "r2.json"
        r2 = run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock), "--report", str(report2))
        self.assertEqual(r2.returncode, EXIT_OK, r2.stderr)
        check2 = next(c for c in json.loads(report2.read_text())["checks"] if c["name"] == "bootstrap_fake")
        self.assertIn("source=cache", check2["detail"])
        self.assertIn("extracted=False", check2["detail"])

    def test_bootstrap_rejects_wrong_digest(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, "0" * 64)
        report = self.root / "r.json"
        r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock), "--report", str(report))
        self.assertEqual(r.returncode, EXIT_FAILURE)
        check = next(c for c in json.loads(report.read_text())["checks"] if c["name"] == "bootstrap_fake")
        self.assertEqual(check["outcome"], "failed")
        self.assertIn("sha256 mismatch", check["detail"])
        self.assertFalse((self.root / "toolchain" / "manifest.json").exists())
        self.assertFalse((self.root / "cache" / self.wheel.name).exists(), "bad download must not stay cached")

    def test_bootstrap_recovers_from_corrupt_install_stamp(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, self.sha)
        self.assertEqual(run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock)).returncode, EXIT_OK)
        stamps = list((self.root / "toolchain").glob("*/.installed.json"))
        self.assertEqual(len(stamps), 1)
        for corrupt in ("{corrupt", "null", "[]", '"str"'):
            stamps[0].write_text(corrupt)
            report = self.root / "r.json"
            r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock), "--report", str(report))
            self.assertEqual(r.returncode, EXIT_OK, (corrupt, r.stderr))
            check = next(c for c in json.loads(report.read_text())["checks"] if c["name"] == "bootstrap_fake")
            self.assertIn("extracted=True", check["detail"], corrupt)

    def test_bootstrap_rejects_wrong_reported_version(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, self.sha, version="1.0.0")
        r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock))
        self.assertEqual(r.returncode, EXIT_FAILURE)
        self.assertIn("expected 1.0.0", r.stderr)

    def test_bootstrap_reports_unsupported_platform_as_missing(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, self.sha)
        data = json.loads(lock.read_text())
        data["tools"]["fake"]["artifacts"] = {"plan9-mips": data["tools"]["fake"]["artifacts"][toolchain.platform_key()]}
        lock.write_text(json.dumps(data))
        r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(lock))
        self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE)

    def test_bootstrap_rejects_bad_lock(self) -> None:
        bad = self.root / "lock.json"
        bad.write_text('{"lock_schema_version": 42}')
        r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(bad))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)
        r = run_cli("bootstrap", "--root", str(self.root), "--lock", str(self.root / "absent.json"))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)

    def test_build_without_bootstrap_is_missing_prerequisite(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, self.sha)
        r = run_cli("build", "--preset", "lab-debug", "--root", str(self.root), "--lock", str(lock))
        self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE)

    def test_test_without_native_build_is_missing_not_pass(self) -> None:
        lock = make_lock(self.root / "lock.json", self.wheel, self.sha)
        (self.root / "CMakePresets.json").write_bytes((ROOT / "CMakePresets.json").read_bytes())
        report = self.root / "r.json"
        r = run_cli("test", "--suite", "synthetic", "--root", str(self.root), "--lock", str(lock),
                    "--report", str(report), "--artifacts", str(self.root / "art"), "--no-python-tests")
        # No toolchain and no build under the temporary root: never a bare zero.
        self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE, r.stderr)
        rep = json.loads(report.read_text())
        self.assertEqual(rep["status"], "failed")
        names = {c["name"]: c["outcome"] for c in rep["checks"]}
        self.assertEqual(names.get("native_build_available"), "missing")

    def test_unknown_suite_is_invalid_input(self) -> None:
        r = run_cli("test", "--suite", "everything")
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)

    def test_unknown_or_hidden_preset_is_invalid_input(self) -> None:
        for preset in ("lab-nope", "lab-base"):
            r = run_cli("test", "--suite", "synthetic", "--preset", preset, "--no-python-tests")
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, (preset, r.stderr))

    def test_non_positive_timeouts_are_invalid_input(self) -> None:
        r = run_cli("test", "--suite", "synthetic", "--no-python-tests", "--test-timeout", "0")
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)
        r = run_cli("build", "--preset", "lab-debug", "--timeout", "-1")
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)


class SourceStateTests(unittest.TestCase):
    def test_untracked_file_marks_source_dirty(self) -> None:
        from unirally_lab import report as reportmod
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                            "commit", "-q", "--allow-empty", "-m", "base"], check=True)
            original = reportmod.repo_root
            reportmod.repo_root = lambda: repo
            try:
                clean = reportmod.source_state()
                (repo / "new_test.py").write_text("x = 1\n")
                dirty = reportmod.source_state()
                (repo / "new_test.py").write_text("x = 2\n")
                dirty2 = reportmod.source_state()
            finally:
                reportmod.repo_root = original
        self.assertFalse(clean["dirty"])
        self.assertTrue(dirty["dirty"])
        self.assertEqual(dirty["untracked_files"], ["new_test.py"])
        self.assertNotEqual(dirty["dirty_diff_sha256"], dirty2["dirty_diff_sha256"])


if __name__ == "__main__":
    unittest.main()
