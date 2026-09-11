"""ROM-free checks for replay manifests and the comparator (M0-04).

Runs that need the pinned core and the ROM go through ``project.py replay
run|compare`` and are recorded as task evidence. Here we prove the manifest
contract (invalid manifests are rejected with exit 3), the derivation of the
reference script, the comparison and divergence logic on synthetic samples,
the origin resolution (absent state or restore-check evidence is missing,
not a pass) and the command error paths.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK  # noqa: E402
from unirally_lab import report as reportmod  # noqa: E402
from unirally_lab.compare import samples as cmp  # noqa: E402
from unirally_lab.reference import worker  # noqa: E402
from unirally_lab.replay import commands as replay  # noqa: E402
from unirally_lab.replay import manifest as mf  # noqa: E402

PROJECT = ROOT / "tools" / "project.py"
MANIFESTS = ROOT / "tests" / "manifests" / "replay"
PRIMARY = MANIFESTS / "boot-start-600.json"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROJECT), *args], capture_output=True, text=True, timeout=300)


def primary() -> dict:
    return json.loads(PRIMARY.read_text())


def outcomes(report: Path) -> dict[str, str]:
    return {c["name"]: c["outcome"] for c in json.loads(report.read_text())["checks"]}


class ManifestSchemaTests(unittest.TestCase):
    def test_tracked_manifests_are_valid(self) -> None:
        paths = sorted(MANIFESTS.glob("*.json"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(manifest=path.name):
                m = mf.load_manifest(path)
                self.assertEqual(m["scenario_id"], path.stem)
                r = run_cli("replay", "validate", "--manifest", str(path))
                self.assertEqual(r.returncode, EXIT_OK, r.stderr)

    def test_invalid_manifests_are_rejected(self) -> None:
        def mutate(**changes):
            m = primary()
            for dotted, value in changes.items():
                target = m
                keys = dotted.split(".")
                for k in keys[:-1]:
                    target = target[int(k)] if isinstance(target, list) else target[k]
                last = keys[-1]
                if value is KeyError:
                    del target[last]
                elif isinstance(target, list):
                    target[int(last)] = value
                else:
                    target[last] = value
            return m
        state_origin = {"kind": "state", "path": "local/states/x.bst", "sha256": "a" * 64, "script": "tests/manifests/reference/boot-start-600.json",
                        "script_sha256": "b" * 64, "after_frame": 150, "restore_check": {"report": "local/states/rc.json", "save_after": 150}}
        bad = {
            "schema": mutate(schema_version=2),
            "scenario id": mutate(scenario_id="bad id!"),
            "no description": mutate(description=KeyError),
            "empty regeneration": mutate(regeneration_command=" "),
            "rom digest": mutate(**{"rom.sha256": "abc"}),
            "absolute rom manifest": mutate(**{"rom.manifest": "/etc/passwd"}),
            "parent path": mutate(**{"rom.manifest": "../outside.json"}),
            "other core": mutate(**{"core.name": "mesen"}),
            "short commit": mutate(**{"core.commit": "7d5aa1e"}),
            "method": mutate(**{"core.serialization_method": "Loose"}),
            "unknown option": mutate(**{"core.options": {"bsnes_turbo": "ON"}}),
            "option type": mutate(**{"core.options": {"bsnes_entropy": 1}}),
            "zero frames": mutate(**{"run.frames": 0}),
            "bool frames": mutate(**{"run.frames": True}),
            "sample_every": mutate(**{"run.sample_every": 0}),
            "trace": mutate(**{"run.trace_entries": -1}),
            "timing unit": mutate(**{"inputs.timing_unit": "ms"}),
            "injection": mutate(**{"inputs.injection_point": ""}),
            "one controller": mutate(**{"inputs.controllers": [{"port": 0, "events": []}]}),
            "duplicate port": mutate(**{"inputs.controllers": [{"port": 0, "events": []}, {"port": 0, "events": []}]}),
            "event order": mutate(**{"inputs.controllers.0.events.0": {"from": 305, "to": 300, "buttons": ["start"]}}),
            "event past end": mutate(**{"inputs.controllers.0.events.0": {"from": 300, "to": 600, "buttons": ["start"]}}),
            "event button": mutate(**{"inputs.controllers.0.events.0": {"from": 300, "to": 305, "buttons": ["turbo"]}}),
            "event empty buttons": mutate(**{"inputs.controllers.0.events.0": {"from": 300, "to": 305, "buttons": []}}),
            "event port": mutate(**{"inputs.controllers.0.events.0": {"from": 300, "to": 305, "port": 1, "buttons": ["start"]}}),
            "no fields": mutate(fields=[]),
            "duplicate field": mutate(fields=[{"name": "a", "kind": "wram_range", "start": 0, "length": 1}, {"name": "a", "kind": "wram_range", "start": 1, "length": 1}]),
            "field kind": mutate(fields=[{"name": "a", "kind": "vram_range", "start": 0, "length": 1}]),
            "negative start": mutate(fields=[{"name": "a", "kind": "wram_range", "start": -1, "length": 1}]),
            "beyond wram": mutate(fields=[{"name": "a", "kind": "wram_range", "start": 0x1FFFF, "length": 2}]),
            "zero length": mutate(fields=[{"name": "a", "kind": "wram_range", "start": 0, "length": 0}]),
            "reserved name": mutate(fields=[{"name": "wram_sha256", "kind": "wram_range", "start": 0, "length": 1}]),
            "misnamed builtin": mutate(fields=[{"name": "regs", "kind": "registers"}]),
            "origin kind": mutate(origin={"kind": "snapshot"}),
            "state without path": mutate(origin={k: v for k, v in state_origin.items() if k != "path"}),
            "state after last frame": mutate(origin={**state_origin, "after_frame": 599, "restore_check": {"report": "r.json", "save_after": 599}}),
            "restore check mismatch": mutate(origin={**state_origin, "restore_check": {"report": "r.json", "save_after": 149}}),
            "restore check missing": mutate(origin={k: v for k, v in state_origin.items() if k != "restore_check"}),
            "expected key": mutate(expected={"av_digest": "a" * 64}),
            "expected digest": mutate(expected={"sample_digest": "xyz"}),
        }
        for label, data in bad.items():
            with self.subTest(case=label):
                with self.assertRaises(mf.ManifestError):
                    mf.validate_manifest(data)
        mf.validate_manifest(mutate(origin=state_origin))  # the state origin itself is well-formed

    def test_cli_rejects_invalid_or_absent_manifest_with_exit_3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"schema_version": 1}))
            bad_range = Path(tmp) / "bad-range.json"  # review 1, M1: escaped as a traceback (exit 1) before
            m = primary()
            m["fields"].append({"name": "neg", "kind": "wram_range", "start": -1, "length": 1})
            bad_range.write_text(json.dumps(m))
            nested = Path(tmp) / "nested.json"
            nested.write_text(json.dumps({**primary(), "inputs": {"timing_unit": "frame", "injection_point": "x", "controllers": [0, 1]}}))
            report = Path(tmp) / "report.json"
            for sub in ("validate", "run", "compare"):
                for path in (bad, bad_range, nested):
                    with self.subTest(command=sub, manifest=path.name):
                        report.unlink(missing_ok=True)
                        r = run_cli("replay", sub, "--manifest", str(path), "--report", str(report))
                        self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)
                        self.assertNotIn("Traceback", r.stderr)
                        self.assertEqual(json.loads(report.read_text())["status"], "failed")
            r = run_cli("replay", "validate", "--manifest", str(Path(tmp) / "absent.json"))
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)

    def test_validate_reports_lock_and_rom_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            m = primary()
            m["core"]["commit"] = "0" * 40
            path = Path(tmp) / "m.json"
            path.write_text(json.dumps(m))
            report = Path(tmp) / "report.json"
            r = run_cli("replay", "validate", "--manifest", str(path), "--report", str(report))
            self.assertEqual(r.returncode, EXIT_FAILURE, r.stderr)
            self.assertEqual(outcomes(report)["replay_core_identity_matches_lock"], "failed")
            m = primary()
            m["rom"]["sha256"] = "f" * 64
            path.write_text(json.dumps(m))
            r = run_cli("replay", "validate", "--manifest", str(path), "--report", str(report))
            self.assertEqual(r.returncode, EXIT_FAILURE, r.stderr)
            self.assertEqual(outcomes(report)["replay_rom_identity_matches_manifest"], "failed")


class DerivationTests(unittest.TestCase):
    def test_derived_script_is_a_valid_schema_1_script(self) -> None:
        script = mf.derive_script(mf.load_manifest(PRIMARY))
        self.assertEqual(script["schema_version"], 1)
        self.assertEqual(script["frames"], 600)
        self.assertEqual(script["inputs"], [{"from": 300, "to": 305, "port": 0, "buttons": ["start"]}])
        self.assertEqual(script["core_options"], {})
        worker.validate_script(script)

    def test_derived_script_matches_the_tracked_reference_script(self) -> None:
        tracked = worker.load_script(ROOT / "tests" / "manifests" / "reference" / "boot-start-600.json")
        self.assertEqual(mf.script_equivalent(tracked, mf.derive_script(mf.load_manifest(PRIMARY))), [])

    def test_script_equivalence_reports_the_differing_keys(self) -> None:
        derived = mf.derive_script(mf.load_manifest(PRIMARY))
        other = copy.deepcopy(derived)
        other["frames"] = 601
        other["inputs"] = []
        self.assertEqual(mf.script_equivalent(other, derived), ["frames", "inputs"])
        reordered = copy.deepcopy(derived)
        reordered["inputs"][0]["buttons"] = ["start"]
        self.assertEqual(mf.script_equivalent(reordered, derived), [])

    def test_inputs_at_frame_covers_both_ports(self) -> None:
        m = mf.load_manifest(PRIMARY)
        self.assertEqual(mf.inputs_at(m, 299), {"0": [], "1": []})
        self.assertEqual(mf.inputs_at(m, 300), {"0": ["start"], "1": []})
        self.assertEqual(mf.inputs_at(m, 305), {"0": ["start"], "1": []})
        self.assertEqual(mf.inputs_at(m, 306), {"0": [], "1": []})
        self.assertEqual(mf.range_fields(m), [{"name": "wram_0000_0200", "start": 0, "length": 512}])
        self.assertEqual(mf.field_names(m), ["wram_sha256", "registers", "wram_0000_0200"])


def make_samples(frames, final="F", range_len=4, tweak=None, schema=2):
    out = {
        "schema_version": schema,
        "fields": [{"name": "r", "start": 0x100, "length": range_len}],
        "frames": [{"frame": n, "wram_sha256": f"w{n}", "registers": {"pc": n, "a": 1},
                    "fields": {"r": "00" * range_len}, "video": [1, 1, f"v{n}"], "audio_sha256": f"a{n}"} for n in frames],
        "final": {"state_sha256": final},
        "sample_digest": "d",
        "end_frame": max(frames) if frames else None,
        "trace": {"instructions_executed": 10, "window": [{"pc": 1}]},
    }
    if tweak:
        tweak(out)
    return out


FIELDS = ["wram_sha256", "registers", "r"]
STARTS = {"r": 0x100}


class ComparatorTests(unittest.TestCase):
    def test_identical_runs(self) -> None:
        r = cmp.compare_samples(make_samples(range(5)), make_samples(range(5)), FIELDS, STARTS)
        self.assertTrue(r["identical"])
        self.assertIsNone(r["first_divergence"])
        self.assertEqual(r["compared"], 5)
        self.assertTrue(r["av_identical"] and r["final_state_identical"])

    def test_digest_divergence_reports_frame_prior_sample_and_values(self) -> None:
        def poke(out):
            out["frames"][3]["wram_sha256"] = "other"
        r = cmp.compare_samples(make_samples(range(5)), make_samples(range(5), tweak=poke), FIELDS, STARTS)
        self.assertFalse(r["identical"])
        fd = r["first_divergence"]
        self.assertEqual(fd["frame"], 3)
        self.assertEqual(fd["differing_fields"], ["wram_sha256"])
        self.assertEqual(fd["differences"][0], {"field": "wram_sha256", "left": "w3", "right": "other"})
        self.assertEqual(fd["prior_sample"]["frame"], 2)
        self.assertEqual(fd["prior_sample"]["left"]["wram_sha256"], "w2")
        self.assertEqual(fd["prior_sample"]["right"]["registers"], {"pc": 2, "a": 1})

    def test_divergence_on_the_first_frame_has_no_prior_sample(self) -> None:
        def poke(out):
            out["frames"][0]["registers"] = {"pc": 9, "a": 1}
        fd = cmp.compare_samples(make_samples(range(3)), make_samples(range(3), tweak=poke), FIELDS, STARTS)["first_divergence"]
        self.assertEqual(fd["frame"], 0)
        self.assertIsNone(fd["prior_sample"])
        self.assertEqual(fd["differences"][0]["differing_registers"], [{"register": "pc", "left": 0, "right": 9}])

    def test_range_divergence_lists_absolute_offsets(self) -> None:
        def poke(out):
            out["frames"][2]["fields"]["r"] = "00100000"
        fd = cmp.compare_samples(make_samples(range(4)), make_samples(range(4), tweak=poke), FIELDS, STARTS)["first_divergence"]
        self.assertEqual(fd["differing_fields"], ["r"])
        self.assertEqual(fd["differences"][0]["differing_bytes"], 1)
        self.assertEqual(fd["differences"][0]["first"], [{"offset": "0x00101", "left": "0x00", "right": "0x10"}])

    def test_only_declared_fields_are_compared(self) -> None:
        def poke(out):
            out["frames"][2]["fields"]["r"] = "ff" * 4
        r = cmp.compare_samples(make_samples(range(4)), make_samples(range(4), tweak=poke), ["wram_sha256", "registers"], {})
        self.assertIsNone(r["first_divergence"])

    def test_frame_sets_and_final_state(self) -> None:
        r = cmp.compare_samples(make_samples([0, 1, 2, 3]), make_samples([0, 2, 3, 4]), FIELDS, STARTS)
        self.assertEqual(r["only_in_left"], [1])
        self.assertEqual(r["only_in_right"], [4])
        self.assertEqual(r["compared"], 3)
        self.assertFalse(r["identical"])
        self.assertIsNone(r["first_divergence"])
        r = cmp.compare_samples(make_samples(range(3)), make_samples(range(3), final="G"), FIELDS, STARTS)
        self.assertFalse(r["identical"])
        self.assertFalse(r["final_state_identical"])
        self.assertFalse(cmp.compare_samples(make_samples([0]), make_samples([5]), FIELDS, STARTS)["identical"])

    def test_samples_without_the_declared_field_or_schema_are_refused(self) -> None:
        with self.assertRaises(cmp.SamplesError):
            cmp.compare_samples(make_samples(range(2)), make_samples(range(2)), ["wram_sha256", "missing"], {})
        with self.assertRaises(cmp.SamplesError):
            cmp.compare_samples(make_samples(range(2), schema=1), make_samples(range(2)), FIELDS, STARTS)

    def test_byte_diff_counts_all_and_lists_a_bounded_prefix(self) -> None:
        left, right = bytes(200), bytes([1]) * 200
        d = cmp.diff_bytes(left, right, base=0x73)
        self.assertEqual(d["differing_bytes"], 200)
        self.assertEqual(len(d["first"]), cmp.MAX_LISTED_DIFFERENCES)
        self.assertEqual(d["first"][0], {"offset": "0x00073", "left": "0x00", "right": "0x01"})
        self.assertIsNone(cmp.diff_bytes(bytes(2), bytes(3))["differing_bytes"])
        self.assertEqual(cmp.diff_registers({"pc": 1, "a": 2}, {"pc": 1, "a": 3}), [{"register": "a", "left": 2, "right": 3}])

    def test_trace_windows_come_from_both_samples(self) -> None:
        t = cmp.trace_windows(make_samples(range(3)), make_samples(range(3)))
        self.assertEqual(t["left"]["end_frame"], 2)
        self.assertEqual(t["right"]["window"], [{"pc": 1}])


class OriginResolutionTests(unittest.TestCase):
    """The origin of a state manifest must exist, match its digests and carry
    passing restore-check evidence; anything else is missing or failed."""

    SCRIPT_REL = "tests/manifests/reference/boot-start-600.json"

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "root"
        (self.root / "tests" / "manifests" / "reference").mkdir(parents=True)
        shutil.copy(ROOT / self.SCRIPT_REL, self.root / self.SCRIPT_REL)
        self.script_sha = reportmod.file_sha256(self.root / self.SCRIPT_REL)
        self.state = self.root / "local" / "states" / "s.bst"
        self.state.parent.mkdir(parents=True)
        self.state.write_bytes(b"state bytes")
        self.state_sha = reportmod.file_sha256(self.state)
        self.write_sidecar()
        self.report = self.root / "local" / "states" / "rc.json"
        self.write_report()
        self.art = self.tmp / "art"
        self.art.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_sidecar(self, **overrides) -> None:
        meta = {"after_frame": 150, "sha256": self.state_sha, "script_sha256": self.script_sha, "serialization_method": "Strict"}
        meta.update(overrides)
        self.state.with_suffix(".bst.json").write_text(json.dumps(meta))

    def write_report(self, failing: str | None = None, state_sha: str | None = None, save_after: int = 150) -> None:
        checks = [{"name": c, "outcome": "failed" if c == failing else "passed", "required": True} for c in mf.RESTORE_CHECKS]
        rep = {"checks": checks, "inputs": {"script": {"sha256": self.script_sha}},
               "artifacts": [{"kind": "state", "sha256": state_sha or self.state_sha}],
               "samples": {"restore_and_continue": {"start_frame": save_after + 1}}}
        self.report.write_text(json.dumps(rep))

    def manifest(self, **origin_overrides) -> dict:
        m = primary()
        m["origin"] = {"kind": "state", "path": "local/states/s.bst", "sha256": self.state_sha, "script": self.SCRIPT_REL,
                       "script_sha256": self.script_sha, "after_frame": 150,
                       "restore_check": {"report": "local/states/rc.json", "save_after": 150}}
        m["origin"].update(origin_overrides)
        return mf.validate_manifest(m)

    def resolve(self, manifest: dict):
        rep = reportmod.Report(["test"])
        side = replay._resolve_side(rep, self.root, self.art, replay.Side("x", manifest))
        return side, {c["name"]: c for c in rep.data["checks"]}

    def test_cold_start_writes_the_derived_script_and_fields(self) -> None:
        side, checks = self.resolve(mf.load_manifest(PRIMARY))
        self.assertEqual(side.status, EXIT_OK)
        self.assertEqual(checks["x_origin_available"]["outcome"], "passed")
        self.assertEqual(worker.load_script(side.script)["frames"], 600)
        self.assertEqual(json.loads(side.fields.read_text()), [{"name": "wram_0000_0200", "start": 0, "length": 512}])
        self.assertIsNone(side.state_in)

    def test_valid_state_origin_is_accepted(self) -> None:
        side, checks = self.resolve(self.manifest())
        self.assertEqual(side.status, EXIT_OK, checks)
        self.assertEqual(checks["x_origin_available"]["outcome"], "passed")
        self.assertEqual(checks["x_origin_restore_check"]["outcome"], "passed")
        self.assertEqual(side.state_in, self.state)
        self.assertEqual(side.script, self.root / self.SCRIPT_REL)

    def test_absent_state_is_missing(self) -> None:
        self.state.unlink()
        side, checks = self.resolve(self.manifest())
        self.assertEqual(side.status, EXIT_MISSING_PREREQUISITE)
        self.assertEqual(checks["x_origin_available"]["outcome"], "missing")
        self.assertIn("regenerate", checks["x_origin_available"]["detail"])

    def test_absent_sidecar_or_script_is_missing(self) -> None:
        self.state.with_suffix(".bst.json").unlink()
        side, checks = self.resolve(self.manifest())
        self.assertEqual(side.status, EXIT_MISSING_PREREQUISITE)
        self.write_sidecar()
        (self.root / self.SCRIPT_REL).unlink()
        side, checks = self.resolve(self.manifest())
        self.assertEqual(side.status, EXIT_MISSING_PREREQUISITE)

    def test_state_or_sidecar_mismatch_fails(self) -> None:
        for label, manifest_override, sidecar_override in (
            ("state digest", {"sha256": "0" * 64}, {}),
            ("script digest", {"script_sha256": "0" * 64}, {}),
            ("sidecar frame", {}, {"after_frame": 149}),
            ("sidecar method", {}, {"serialization_method": "Fast"}),
            ("sidecar state", {}, {"sha256": "0" * 64}),
        ):
            with self.subTest(case=label):
                self.write_sidecar(**sidecar_override)
                side, checks = self.resolve(self.manifest(**manifest_override))
                self.assertEqual(side.status, EXIT_FAILURE)
                self.assertEqual(checks["x_origin_available"]["outcome"], "failed")
        self.write_sidecar()

    def test_absent_restore_check_report_is_missing(self) -> None:
        self.report.unlink()
        side, checks = self.resolve(self.manifest())
        self.assertEqual(side.status, EXIT_MISSING_PREREQUISITE)
        self.assertEqual(checks["x_origin_restore_check"]["outcome"], "missing")

    def test_perturbing_or_foreign_restore_check_fails(self) -> None:
        for c in mf.RESTORE_CHECKS:
            with self.subTest(failing=c):
                self.write_report(failing=c)
                side, checks = self.resolve(self.manifest())
                self.assertEqual(side.status, EXIT_FAILURE)
                self.assertIn(c, checks["x_origin_restore_check"]["detail"])
        self.write_report(state_sha="0" * 64)
        side, checks = self.resolve(self.manifest())
        self.assertEqual(side.status, EXIT_FAILURE)
        self.assertIn("another", checks["x_origin_restore_check"]["detail"])

    def test_restore_check_must_be_for_the_manifests_save_point(self) -> None:
        """Editing after_frame in both sidecar and manifest must not be enough (review 1, m1):
        the report's measured resume frame ties the evidence to the save point."""
        self.write_sidecar(after_frame=151)
        self.write_report(save_after=150)
        side, checks = self.resolve(self.manifest(after_frame=151, restore_check={"report": "local/states/rc.json", "save_after": 151}))
        self.assertEqual(side.status, EXIT_FAILURE)
        self.assertIn("save point 150", checks["x_origin_restore_check"]["detail"])
        self.write_report(save_after=151)
        side, checks = self.resolve(self.manifest(after_frame=151, restore_check={"report": "local/states/rc.json", "save_after": 151}))
        self.assertEqual(side.status, EXIT_OK)
        report = self.report.read_text()
        self.report.write_text(report.replace('"samples"', '"samples_gone"'))
        side, checks = self.resolve(self.manifest(after_frame=151, restore_check={"report": "local/states/rc.json", "save_after": 151}))
        self.assertEqual(side.status, EXIT_FAILURE)
        self.assertIn("unreadable", checks["x_origin_restore_check"]["detail"])


class CommandPrerequisiteTests(unittest.TestCase):
    def make_root(self, tmp: Path) -> Path:
        root = tmp / "root"
        for rel in ("tools/locks/emulators.json", "tests/manifests/rom/unirally-pal.json"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, root / rel)
        return root

    def test_unbuilt_core_is_missing_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(Path(tmp))
            report = Path(tmp) / "report.json"
            for sub in ("run", "compare"):
                with self.subTest(command=sub):
                    r = run_cli("replay", sub, "--manifest", str(PRIMARY), "--root", str(root), "--rom", str(Path(tmp) / "absent.sfc"), "--report", str(report))
                    self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE, r.stderr)
                    out = outcomes(report)
                    self.assertEqual(out["core_available"], "missing")
                    self.assertNotIn("fields_identical", out)
                    self.assertNotIn("reference_run", out)

    def test_incomparable_manifests_and_bad_arguments_are_invalid_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            other = primary()
            other["scenario_id"] = "other-fields"
            other["fields"] = other["fields"][:2]
            path = Path(tmp) / "other.json"
            path.write_text(json.dumps(other))
            report = Path(tmp) / "report.json"
            r = run_cli("replay", "compare", "--manifest", str(PRIMARY), "--against", str(path), "--report", str(report))
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)
            self.assertEqual(outcomes(report)["manifests_comparable"], "failed")
            for args in (("--runs", "1"), ("--against", str(PRIMARY), "--runs", "3"), ("--timeout", "0")):
                with self.subTest(args=args):
                    r = run_cli("replay", "compare", "--manifest", str(PRIMARY), *args)
                    self.assertEqual(r.returncode, EXIT_INVALID_INPUT, r.stderr)


if __name__ == "__main__":
    unittest.main()
