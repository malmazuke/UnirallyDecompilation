"""ROM-free checks for the bounded M4-06 vertical-contact component."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.native.zoom_zoo_vertical_contact import (  # noqa: E402
    COEFFICIENT_IDENTITY,
    _arithmetic_shift_u16,
    compare_inputs,
    reduce_vertical,
    resolve_response,
    validate_manifest,
)


COEFFICIENTS = bytes((0, 4, 4, 4, 2, 4, 0, 1, 2, 3, 1, 5))


def contact_call(**overrides: int) -> dict:
    incoming = {
        "x": 100, "y": 50, "vx": 359, "vy": 19,
        "response_a": 0, "response_b": 0, "response_impulse": 0,
        "unsupported_count": 0, "unsupported_duration": 0,
        "surface_angle": 0, "angle_sentinel": 0, "auxiliary_flag": 0,
        "mode": 0, "special": 0, "phase": 1,
        "previous_x": 90, "previous_y": 48,
    }
    incoming.update(overrides)
    return {"frame": 1, "rider": 0, "input": incoming}


def summary(angle: int = 0xFD, penetration: int = 6) -> dict:
    return {
        "supported": True, "support_summary": penetration,
        "vertical_correction": penetration, "angle": angle,
        "selected_word": 0x0C08, "selected_high": 0x0C,
        "tile_flags": 0, "vertical_axis": 0,
        "horizontal_correction": 0, "horizontal_axis": 0,
    }


class ZoomZooVerticalContactTests(unittest.TestCase):
    def test_both_authored_manifests_are_exact_bound(self) -> None:
        manifests = [
            json.loads((ROOT / "tests/manifests/native/zoom-zoo-vertical-contact-primary.reference.json").read_text()),
            json.loads((ROOT / "tests/manifests/native/zoom-zoo-vertical-contact-right-1653.reference.json").read_text()),
        ]
        for manifest in manifests:
            validate_manifest(manifest)
            for mutate in ("calls", "points", "access_sha256", "classification_sha256"):
                changed = copy.deepcopy(manifest)
                changed[mutate] = 0 if mutate in ("calls", "points") else "0" * 64
                with self.subTest(scenario=manifest["scenario_id"], mutate=mutate):
                    with self.assertRaisesRegex(ValueError, "authored identity"):
                        validate_manifest(changed)

    def test_source_content_and_boundary_identities_are_exact(self) -> None:
        manifest = json.loads((ROOT / "tests/manifests/native/zoom-zoo-vertical-contact-right-1653.reference.json").read_text())
        mutations = []
        changed = copy.deepcopy(manifest); changed["source"]["replay_manifest_sha256"] = "0" * 64; mutations.append(changed)
        changed = copy.deepcopy(manifest); changed["static_content"]["vertical_slope_coefficients_sha256"] = "0" * 64; mutations.append(changed)
        changed = copy.deepcopy(manifest); changed["direction_boundary"]["frame"] = 1685; mutations.append(changed)
        for changed in mutations:
            with self.assertRaises(ValueError):
                validate_manifest(changed)

    def test_signed_penetrations_do_not_enter_vertical_correction(self) -> None:
        probes = [(0xA0, 0, 0)] * 4 + [
            (250, 0xFE, 0x0006), (0xA0, 0, 0), (254, 0xFE, 0x0006),
            (2, 0xFF, 0x0020), (4, 0xFF, 0x0022), (6, 0xFF, 0x0020),
        ]
        reduced = reduce_vertical(probes, bytes(203))
        self.assertEqual(reduced["support_summary"], 6)
        self.assertEqual(reduced["vertical_correction"], 6)
        self.assertEqual(reduced["angle"], 0xFF)
        self.assertEqual(reduced["selected_word"], 0x20)

    def test_reducer_order_and_ties_are_observable(self) -> None:
        probes = [(0xA0, 0, 0)] * 7 + [
            (0, 0xFD, 0x0C2E), (254, 0xFC, 0x002C), (0, 0xFC, 0x002C),
        ]
        original = reduce_vertical(probes, bytes(203))
        reordered = reduce_vertical(probes[:7] + [probes[9], probes[8], probes[7]], bytes(203))
        self.assertEqual(original["selected_word"], 0x0C2E)
        self.assertEqual(original["selected_high"], 0x0C)
        self.assertNotEqual(reordered, original)

    def test_negative_slope_response_uses_authenticated_tables(self) -> None:
        resolved, scratch = resolve_response(contact_call(), summary(), COEFFICIENTS)
        self.assertEqual(scratch["shifted_velocity"], 22)
        self.assertEqual(scratch["slope_multiplier"], 3)
        self.assertEqual(resolved["motion"]["vy"], 0xFFBF)
        self.assertEqual(resolved["motion"]["vx"], 358)
        changed = bytearray(COEFFICIENTS); changed[9] = 4
        self.assertNotEqual(resolve_response(contact_call(), summary(), bytes(changed))[0], resolved)
        self.assertEqual(COEFFICIENT_IDENTITY[0], len(COEFFICIENTS))

    def test_negative_incoming_vertical_velocity_does_not_short_circuit(self) -> None:
        resolved, _ = resolve_response(
            contact_call(vx=382, vy=0xFFD2), summary(angle=0xFD, penetration=2), COEFFICIENTS
        )
        self.assertEqual(resolved["motion"]["vx"], 381)
        self.assertEqual(resolved["motion"]["vy"], 0xFFBC)
        self.assertEqual(resolved["state"]["surface_angle"], 0xFFFD)

    def test_support_loss_and_reacquisition_preserve_original_order(self) -> None:
        unsupported = summary(); unsupported.update({
            "supported": False, "support_summary": 0xFF,
            "vertical_correction": 0, "angle": 0xE0,
            "selected_word": 0, "selected_high": 0,
        })
        lost, _ = resolve_response(
            contact_call(unsupported_count=0, unsupported_duration=0, vx=405, vy=0xFFCF),
            unsupported, COEFFICIENTS,
        )
        self.assertEqual((lost["state"]["unsupported_count"], lost["state"]["unsupported_duration"]), (1, 1))
        self.assertEqual((lost["motion"]["vx"], lost["motion"]["vy"]), (405, 0xFFCF))
        reacquired, _ = resolve_response(
            contact_call(unsupported_count=1, unsupported_duration=1, vx=429, vy=0xFFE2),
            summary(angle=0xFC, penetration=1), COEFFICIENTS,
        )
        self.assertEqual((reacquired["state"]["unsupported_count"], reacquired["state"]["unsupported_duration"]), (0, 0))
        self.assertEqual((reacquired["motion"]["vx"], reacquired["motion"]["vy"]), (427, 0xFF96))

    def test_bounded_recontact_is_computed_from_incoming_coordinates(self) -> None:
        call = contact_call(
            x=7996, y=1521, previous_x=8010, previous_y=1513,
            vx=0xFE40, vy=222, unsupported_count=9,
            unsupported_duration=37, surface_angle=0,
        )
        call["rider"] = 1
        call["live_dependencies"] = {"cartridge_option": 0xC200, "rider_selector": 2}
        resolved, scratch = resolve_response(call, summary(angle=0, penetration=1), COEFFICIENTS)
        self.assertEqual(resolved["branch"], "recontact")
        self.assertEqual(scratch["recontact_dx"], 14)
        self.assertEqual(scratch["recontact_half_dy"], 4)
        self.assertEqual(scratch["recontact_coarse_angle"], 4)
        self.assertEqual(scratch["recontact_bucket"], 0xFFFF)
        self.assertEqual((resolved["motion"]["vx"], resolved["motion"]["vy"]), (0xFE40, 222))
        changed = copy.deepcopy(call); changed["input"]["previous_y"] = 1521
        with self.assertRaisesRegex(ValueError, "divisor is zero"):
            resolve_response(changed, summary(angle=0, penetration=1), COEFFICIENTS)

    def test_arithmetic_right_shift_is_signed_sixteen_bit(self) -> None:
        self.assertEqual(_arithmetic_shift_u16(0xFE40, 4), 0xFFE4)
        self.assertEqual(_arithmetic_shift_u16(0x0167, 4), 0x0016)

    def test_input_comparison_rejects_non_document_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary = root / "primary.json"
            variation = root / "variation.json"
            report = root / "report.json"
            primary.write_text("[]")
            variation.write_text("[]")
            with self.assertRaisesRegex(ValueError, "complete sample documents"):
                compare_inputs(primary, variation, report)
            self.assertFalse(report.exists())

    def test_documented_capture_command_exists_and_dispatches(self) -> None:
        research = (ROOT / "docs/research/R-0024-zoom-zoo-vertical-contact.md").read_text()
        match = re.search(r"python3 -m ([\w.]+) capture --manifest", research)
        self.assertIsNotNone(match, "R-0024 must publish a capture command")
        module = match.group(1)

        help_result = subprocess.run(
            [sys.executable, "-m", module, "capture", "--help"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for option in ("--manifest", "--out", "--from-frame", "--to-frame"):
            self.assertIn(option, help_result.stdout)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "must-not-exist"
            dispatch = subprocess.run(
                [
                    sys.executable, "-m", module, "capture",
                    "--manifest", str(root / "missing-manifest.json"),
                    "--out", str(output),
                    "--from-frame", "1650", "--to-frame", "1682",
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(dispatch.returncode, 2, dispatch.stderr)
            self.assertIn("No such file or directory", dispatch.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
