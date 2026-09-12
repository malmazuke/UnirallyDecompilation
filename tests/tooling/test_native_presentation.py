import argparse
import copy
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from unirally_lab.content import ppu
from unirally_lab.native import presentation


class NativePresentationCommandTests(unittest.TestCase):
    def test_threshold_logic_reports_exact_pixel_failures(self):
        reference = bytes(256 * 224 * 3)
        native = bytearray(reference)
        native[0] = 1
        passed = presentation.compare_rgb(bytes(native), reference, [0, 0, 10, 10], 0.01)
        failed = presentation.compare_rgb(bytes(native), reference, [0, 0, 10, 10], 0.009)
        self.assertEqual((passed["mismatches"], passed["pixels"]), (1, 100))
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])

    def test_manifest_fixture_and_numeric_boundaries_are_validated(self):
        root = Path(__file__).resolve().parents[2]
        tracked = root / "tests/manifests/presentation/classic-crawler-dragster-v1.json"
        contract = presentation.load_contract(tracked)
        mutated_fields = (
            "profile_id", "source_rom_sha256", "classic_pack_profile_id",
            "classic_pack_start_state_id", "classic_pack_rules_sha256",
            "sampling_schema", "sampling_phase", "state_fields",
            "logical_entries", "declared_omissions", "reference_cases",
        )
        with tempfile.TemporaryDirectory(dir=root / "artifacts") as temp:
            temp_path = Path(temp)
            for index, field in enumerate(mutated_fields):
                with self.subTest(field=field):
                    bad = copy.deepcopy(contract)
                    if field == "source_rom_sha256":
                        bad[field] = "0" * 64
                    elif isinstance(bad[field], list):
                        bad[field] = list(reversed(bad[field]))
                    else:
                        bad[field] += ".unsupported"
                    manifest = temp_path / f"{field}.json"
                    manifest.write_text(json.dumps(bad))
                    artifacts = temp_path / f"run-{index}"
                    args = argparse.Namespace(
                        manifest=str(manifest), fixtures=str(temp_path),
                        content_pack=str(temp_path / "unused.pack"),
                        preset="lab-debug", artifacts=str(artifacts),
                        report=str(artifacts / "report.json"), timeout=10,
                        task="authored-presentation-identity")
                    with contextlib.redirect_stderr(io.StringIO()), \
                         patch.object(presentation.reports, "print_summary"):
                        code = presentation.cmd_presentation_check(args)
                    self.assertEqual(code, 3)
                    report = json.loads((artifacts / "report.json").read_text())
                    self.assertEqual(report["status"], "failed")
                    self.assertNotIn("visual_results", report)

        inspected = {
            "source_rom_sha256": contract["source_rom_sha256"],
            "profile_id": contract["classic_pack_profile_id"],
            "start_state_id": contract["classic_pack_start_state_id"],
            "rules_sha256": contract["classic_pack_rules_sha256"],
            "entries": [{"id": value}
                        for value in contract["logical_entries"]],
        }
        presentation.validate_pack_binding(
            contract, inspected, contract["classic_pack_rules_sha256"])
        for field in ("source_rom_sha256", "profile_id", "start_state_id",
                      "rules_sha256"):
            with self.subTest(pack_field=field):
                bad_pack = copy.deepcopy(inspected)
                bad_pack[field] = "unsupported"
                with self.assertRaises(presentation.PresentationContractError):
                    presentation.validate_pack_binding(
                        contract, bad_pack,
                        contract["classic_pack_rules_sha256"])

    def test_loser_contract_is_separately_authenticated(self):
        root = Path(__file__).resolve().parents[2]
        tracked = root / "tests/manifests/presentation/classic-crawler-dragster-loser-v1.json"
        contract = presentation.load_contract(tracked)
        self.assertEqual(
            contract["profile_id"],
            "classic.pal.crawler.dragster.loser-presentation.v1")
        case = contract["reference_cases"][0]
        self.assertEqual(case["outcome"], "player_lost")
        self.assertEqual(case["player_time_digits"], [0, 3, 5, 6, 6])
        self.assertEqual(case["result_map_observations"]["time_tile_words"][1],
                         {"x": 23, "y": 11, "word": "0x3caf"})
        for mutation in (
                lambda value: value["reference_cases"][0].update(
                    {"outcome": "player_won"}),
                lambda value: value["reference_cases"][0]["player_time_digits"].__setitem__(
                    4, 5),
                lambda value: value["reference_cases"][0]["result_map_observations"][
                    "time_tile_words"][1].update({"word": "0x3cae"}),
                lambda value: value["reference_cases"][0].update(
                    {"maximum_mismatch_fraction": 0.151})):
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(contract)
                mutation(bad)
                with tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / "contract.json"
                    path.write_text(json.dumps(bad))
                    with self.assertRaises(presentation.PresentationContractError):
                        presentation.load_contract(path)

    def test_ppm_parser_and_png_decoder_form_a_rom_free_image_seam(self):
        rgb = bytes((index % 251 for index in range(256 * 224 * 3)))
        ppm = b"P6\n256 224\n255\n" + rgb
        self.assertEqual(presentation.parse_ppm(ppm), rgb)
        self.assertEqual(ppu.read_png(ppu.write_png(256, 224, rgb)), (256, 224, rgb))
        with self.assertRaises(presentation.PresentationContractError):
            presentation.parse_ppm(ppm[:-1])


if __name__ == "__main__":
    unittest.main()
