import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

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
        case = {"id": "boundary", "frame": 3678,
                "state_file": "states/state.bin", "state_sha256": "a" * 64,
                "reference_file": "frames/frame.png", "reference_png_sha256": "b" * 64,
                "camera_x": -(1 << 31), "bg1_scroll": [-32768, 32767],
                "bg2_scroll": [0, 0], "comparison_rect": [0, 0, 256, 224],
                "maximum_mismatch_fraction": 0.15}
        contract = {"schema_version": 1, "kind": "native_presentation_contract",
                    "frame_size": [256, 224], "pixel_format": "rgb888",
                    "reference_cases": [case]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text(json.dumps(contract))
            self.assertEqual(presentation.load_contract(path)["reference_cases"][0]["frame"], 3678)
            bad = copy.deepcopy(contract)
            bad["reference_cases"][0]["state_file"] = "../state.bin"
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
