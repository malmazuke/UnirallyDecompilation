"""Checks for the reference adapter tooling that need neither the ROM nor a built core.

Runs that need the pinned core and the ROM are performed through
``project.py reference ...`` and recorded as task evidence; here we prove the
error paths and the script contract, and that a missing prerequisite is
reported as missing rather than as a pass.
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

from unirally_lab import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK  # noqa: E402
from unirally_lab.reference import commands, worker  # noqa: E402

PROJECT = ROOT / "tools" / "project.py"
SCRIPTS = ROOT / "tests" / "manifests" / "reference"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROJECT), *args], capture_output=True, text=True, timeout=300)


def write_lock(tmp: Path, **overrides) -> Path:
    lock = json.loads((ROOT / "tools" / "locks" / "emulators.json").read_text())
    lock["install_dir"] = str(tmp / "emulators")
    lock["cores"]["bsnes"].update(overrides)
    path = tmp / "emulators.json"
    path.write_text(json.dumps(lock))
    return path


class ScriptContractTests(unittest.TestCase):
    def test_tracked_scripts_are_valid(self) -> None:
        for path in sorted(SCRIPTS.glob("*.json")):
            with self.subTest(script=path.name):
                worker.load_script(path)

    def test_invalid_scripts_are_rejected(self) -> None:
        bad = [
            {"schema_version": 2, "frames": 1},
            {"schema_version": 1, "frames": 0},
            {"schema_version": 1, "frames": True},
            {"schema_version": 1, "frames": 10, "sample_every": 0},
            {"schema_version": 1, "frames": 10, "core": "mesen"},
            {"schema_version": 1, "frames": 10, "inputs": [{"from": 5, "to": 4, "buttons": ["start"]}]},
            {"schema_version": 1, "frames": 10, "inputs": [{"from": 0, "to": 1, "port": 2, "buttons": ["start"]}]},
            {"schema_version": 1, "frames": 10, "inputs": [{"from": 0, "to": 1, "buttons": ["turbo"]}]},
            {"schema_version": 1, "frames": 10, "inputs": [{"from": 0, "to": 1, "buttons": []}]},
            {"schema_version": 1, "frames": 10, "core_options": {"bsnes_entropy": 1}},
            {"schema_version": 1, "frames": 10, "core_options": {"not_an_option": "x"}},
            {"schema_version": 1, "frames": 10, "trace_entries": -1},
        ]
        for data in bad:
            with self.subTest(script=data):
                with self.assertRaises(worker.ScriptError):
                    worker.validate_script(data)

    def test_inputs_apply_only_inside_their_window(self) -> None:
        script = worker.validate_script({"schema_version": 1, "frames": 10,
                                         "inputs": [{"from": 3, "to": 4, "buttons": ["start", "a"]}, {"from": 4, "to": 9, "port": 1, "buttons": ["b"]}]})
        self.assertEqual(worker.inputs_for_frame(script, 2), {0: set(), 1: set()})
        self.assertEqual(worker.inputs_for_frame(script, 3), {0: {"start", "a"}, 1: set()})
        self.assertEqual(worker.inputs_for_frame(script, 4), {0: {"start", "a"}, 1: {"b"}})
        self.assertEqual(worker.inputs_for_frame(script, 5), {0: set(), 1: {"b"}})


class WorkerErrorPathTests(unittest.TestCase):
    def test_missing_core_is_missing_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(commands.WORKER), "--core", f"{tmp}/absent.dylib", "--probe"],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE, r.stdout + r.stderr)
            self.assertIn("error", json.loads(r.stdout))

    def test_invalid_script_is_invalid_input_before_loading_anything(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "bad.json"
            script.write_text(json.dumps({"schema_version": 1, "frames": -5}))
            r = subprocess.run([sys.executable, str(commands.WORKER), "--core", f"{tmp}/absent.dylib", "--rom", f"{tmp}/absent.sfc",
                                "--script", str(script), "--samples-out", f"{tmp}/s.json"], capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)

    def test_missing_rom_is_missing_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(commands.WORKER), "--core", f"{tmp}/absent.dylib", "--rom", f"{tmp}/absent.sfc",
                                "--script", str(SCRIPTS / "boot-300.json"), "--samples-out", f"{tmp}/s.json"], capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE, r.stderr)

    def test_save_arguments_must_pair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([sys.executable, str(commands.WORKER), "--core", f"{tmp}/absent.dylib", "--rom", f"{tmp}/absent.sfc",
                                "--script", str(SCRIPTS / "boot-300.json"), "--samples-out", f"{tmp}/s.json", "--save-after", "3"],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)


class CommandPrerequisiteTests(unittest.TestCase):
    def test_unbuilt_core_is_missing_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = write_lock(Path(tmp))
            report = Path(tmp) / "report.json"
            r = run_cli("reference", "run", "--lock", str(lock), "--script", str(SCRIPTS / "boot-300.json"),
                        "--rom", str(Path(tmp) / "absent.sfc"), "--report", str(report))
            self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE, r.stderr)
            rep = json.loads(report.read_text())
            outcomes = {c["name"]: c["outcome"] for c in rep["checks"]}
            self.assertEqual(outcomes["core_available"], "missing")
            self.assertEqual(rep["status"], "failed")
            self.assertNotIn("reference_run", outcomes)

    def test_unknown_core_and_bad_lock_are_invalid_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = write_lock(Path(tmp))
            r = run_cli("reference", "verify", "--lock", str(lock), "--core", "nonesuch", "--script", str(SCRIPTS / "boot-300.json"))
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)
            bad = Path(tmp) / "bad.json"
            bad.write_text("{}")
            r = run_cli("reference", "build", "--lock", str(bad))
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)
            r = run_cli("reference", "run", "--lock", str(lock), "--script", str(SCRIPTS / "boot-300.json"), "--timeout", "0")
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)

    def test_build_without_checkout_and_network_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = write_lock(Path(tmp))
            report = Path(tmp) / "report.json"
            r = run_cli("reference", "build", "--lock", str(lock), "--no-network", "--report", str(report))
            self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE, r.stderr)
            outcomes = {c["name"]: c["outcome"] for c in json.loads(report.read_text())["checks"]}
            self.assertEqual(outcomes["checkout_pinned"], "missing")

    def test_build_refuses_a_core_without_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lock = write_lock(Path(tmp))
            r = run_cli("reference", "build", "--lock", str(lock), "--core", "mesen", "--no-network")
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)

    def test_stale_core_manifest_is_rejected(self) -> None:
        """A built core recorded against another commit or patch must not be used."""
        with tempfile.TemporaryDirectory() as tmp:
            lock = write_lock(Path(tmp))
            lockdata = json.loads(lock.read_text())
            checkout = Path(lockdata["install_dir"]) / "bsnes"
            checkout.mkdir(parents=True)
            fake_lib = checkout / "core.dylib"
            fake_lib.write_bytes(b"not a core")
            manifest = {"schema_version": 1, "core": "bsnes", "commit": "0" * 40, "patch_sha256": lockdata["cores"]["bsnes"]["patch_sha256"],
                        "library": str(fake_lib), "library_sha256": commands.sha256_file(fake_lib), "api_version": 1}
            (checkout / "lab-core.json").write_text(json.dumps(manifest))
            report = Path(tmp) / "report.json"
            r = run_cli("reference", "run", "--lock", str(lock), "--script", str(SCRIPTS / "boot-300.json"), "--report", str(report))
            self.assertEqual(r.returncode, EXIT_FAILURE, r.stderr)
            outcomes = {c["name"]: c["outcome"] for c in json.loads(report.read_text())["checks"]}
            self.assertEqual(outcomes["core_available"], "failed")


if __name__ == "__main__":
    unittest.main()
