"""ROM-free checks for M2-01 reference freezing and the dependency probe.

No native gameplay replay is implemented yet. Fixtures below are authored
values, and do not read withheld expected series.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import subprocess

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from unirally_lab.native.freeze_reference import freeze, project
from unirally_lab.native.probe_sampling import capture_cases, run_probe, NativeProbeFailure, validate_primary_access
from unirally_lab.replay.manifest import derive_script, range_fields
from unirally_lab.reference.bsnes import DEFAULT_OPTIONS


class FreezeTests(unittest.TestCase):
    def fixture(self):
        manifest = json.loads((ROOT / "tests/manifests/native/primary.replay.json").read_text())
        fields = {item["name"]: "00" * item["length"] for item in range_fields(manifest)}
        fields["pos_x"] = "34127856"
        fields["speed"] = "ffff"
        fields["timer"] = "01aabbcc02aabbcc03aabbcc04aabbcc00aabbcc"
        run = {"rom": manifest["rom"], "process": {"pid": 1},
               "script": {"sha256": hashlib.sha256((json.dumps(derive_script(manifest), indent=2, sort_keys=True) + "\n").encode()).hexdigest()},
               "sample_digest": manifest["expected"]["sample_digest"], "av_digest": "av",
               "final": {"state_sha256": "state"}, "fields": range_fields(manifest),
               "core": {"serialization_method": "Strict"},
               "frames": [{"frame": frame, "fields": dict(fields)} for frame in range(3000)]}
        second = copy.deepcopy(run); second["process"]["pid"] = 2
        return manifest, run, second

    def test_explicit_projection_and_initial_boundary(self):
        manifest, first, second = self.fixture()
        result = freeze(manifest, first, second)
        self.assertEqual(len(result["rows"]), 1467)
        self.assertEqual(result["rows"][0][0], 1533)
        self.assertEqual(result["rows"][0][5], 0x1234)
        self.assertEqual(result["rows"][0][8], -1)
        self.assertEqual(result["rows"][0][-5:], [1,2,3,4,0])

    def test_diagnostic_disagreement_also_rejects_freeze(self):
        manifest, first, second = self.fixture()
        second["frames"][2000]["fields"]["camera_x"] = "0100"
        with self.assertRaisesRegex(ValueError, "fields differ at 2000"):
            freeze(manifest, first, second)

    def test_frame_loss_and_duplicate_are_rejected(self):
        for mutation in (lambda r: r["frames"].pop(100), lambda r: r["frames"][100].update(frame=99)):
            manifest, first, second = self.fixture(); mutation(second)
            with self.assertRaisesRegex(ValueError, "exactly frames"):
                freeze(manifest, first, second)

    def test_wrong_input_identity_is_rejected(self):
        manifest, first, second = self.fixture()
        second["script"]["sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "input script"):
            freeze(manifest, first, second)

    def test_reference_process_must_be_fresh(self):
        manifest, first, second = self.fixture(); second["process"]["pid"] = 1
        with self.assertRaisesRegex(ValueError, "distinct"):
            freeze(manifest, first, second)

    def test_truncated_projection_is_rejected(self):
        _, first, _ = self.fixture(); first["frames"][0]["fields"]["pos_x"] = "01"
        with self.assertRaisesRegex(ValueError, "truncated"):
            project(first["frames"][0])


class SamplingProbeTests(unittest.TestCase):
    def test_empty_or_short_capture_cannot_pass(self):
        for frames in ({"start": 1534, "end": 1534, "count": 1}, {"start": 1534, "end": 2999, "count": 1466}):
            with self.assertRaises(ValueError):
                capture_cases({"watch_addresses": {}, "frames": frames, "watch_pcs": {str(0x818B6A): []}}, 1024)


class NativeProcessTests(unittest.TestCase):
    def test_nonzero_exit_keeps_native_execution_failure(self):
        with mock.patch("unirally_lab.native.probe_sampling.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "deliberate failure")):
            with self.assertRaisesRegex(NativeProbeFailure, "native process exit 1"):
                run_probe(["fake"], "", 1, 10)

    def test_empty_and_malformed_native_output_are_execution_failures(self):
        for output in ["", "bad\n", "1 2\n"]:
            with mock.patch("unirally_lab.native.probe_sampling.subprocess.run", return_value=subprocess.CompletedProcess([], 0, output, "")):
                with self.assertRaises(NativeProbeFailure):
                    run_probe(["fake"], "", 1, 10)


class PrimaryIdentityTests(unittest.TestCase):
    def fixture(self):
        relative = "tests/manifests/replay/race-crawler-dragster-3000-fields.json"
        path = ROOT / relative
        manifest = json.loads(path.read_text())
        return {"scenario_id": manifest["scenario_id"],
                "manifest": {"path":relative,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()},
                "core": {key:manifest["core"][key] for key in ["name","commit","patch_sha256","serialization_method"]} | {"options":DEFAULT_OPTIONS,"api_version":1},
                "rom":manifest["rom"],
                "script":{"frames":3000,"sample_every":1,"sample_from_frame":None,"sha256":hashlib.sha256((json.dumps(derive_script(manifest),indent=2,sort_keys=True)+"\n").encode()).hexdigest()},
                "status":"complete","failure":None,"watch_pcs_truncated":False,
                "instructions":{"max_frame_delta":100},"ring_capacity":200}

    def test_primary_reference_identity(self):
        validate_primary_access(self.fixture())

    def test_changed_core_inputs_or_incomplete_capture_are_rejected(self):
        mutations = [lambda d:d["core"].update(commit="0"*40),
                     lambda d:d["core"].update(serialization_method="Fast"),
                     lambda d:d["script"].update(sha256="wrong"),
                     lambda d:d.update(scenario_id="another-case"),
                     lambda d:d.update(status="failed"),
                     lambda d:d.update(watch_pcs_truncated=True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                access=self.fixture(); mutation(access)
                with self.assertRaises(ValueError): validate_primary_access(access)
