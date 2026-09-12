"""ROM-free mutation tests for the narrow M4-03 reference contract."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.content import zoom_zoo_contract as contractmod  # noqa: E402


CONTRACT = ROOT / "tests/manifests/content/zoom-zoo-reference-contract.json"


class ZoomZooManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_tracked_contract_has_the_narrow_schema(self) -> None:
        observed = contractmod.validate_manifest(self.contract)
        self.assertEqual(len(observed["load_contract"]["selected_ids"]), 24)
        self.assertEqual(len(observed["gather_samples"]), 2)
        self.assertEqual(len(observed["collision_samples"]), 4)

    def test_wrong_source_identity_fails(self) -> None:
        for mutate in (
            lambda value: value["identity"].__setitem__("rom_sha256", "0" * 64),
            lambda value: value["source"].__setitem__("file_offset", 786820),
            lambda value: value["source"].__setitem__("runtime_base", "0x7E0000"),
        ):
            with self.subTest(mutate=mutate):
                changed = copy.deepcopy(self.contract)
                mutate(changed)
                with self.assertRaises(contractmod.ContractError):
                    contractmod.validate_manifest(changed)

    def test_contradictory_rnc_metadata_fails(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["source"]["rnc_header"]["packed_length"] -= 1
        with self.assertRaisesRegex(contractmod.ContractError, "RNC header"):
            contractmod.validate_manifest(changed)

    def test_malformed_or_overlapping_region_bounds_fail(self) -> None:
        for start, length in ((-1, 15), (0, 0), (50660, 10)):
            with self.subTest(start=start, length=length):
                changed = copy.deepcopy(self.contract)
                changed["decoded_regions"][0].update(start=start, length=length)
                with self.assertRaises(contractmod.ContractError):
                    contractmod.validate_manifest(changed)
        changed = copy.deepcopy(self.contract)
        changed["decoded_regions"][1]["start"] = 14
        with self.assertRaises(contractmod.ContractError):
            contractmod.validate_manifest(changed)

    def test_changed_payload_region_fails_without_a_rom(self) -> None:
        decoded = bytearray(50665)
        changed = copy.deepcopy(self.contract)
        changed["source"]["decoded_sha256"] = hashlib.sha256(decoded).hexdigest()
        for region in changed["decoded_regions"]:
            start, length = region["start"], region["length"]
            region["sha256"] = hashlib.sha256(decoded[start:start + length]).hexdigest()
        contractmod._validate_regions(changed, decoded)
        decoded[32783] = 1
        changed["source"]["decoded_sha256"] = hashlib.sha256(decoded).hexdigest()
        with self.assertRaisesRegex(contractmod.ContractError, "bounded-consumer-data"):
            contractmod._validate_regions(changed, decoded)

    def test_gather_uses_decoded_words_not_captured_upload_bytes(self) -> None:
        decoded = bytearray(50665)
        decoded[contractmod.COARSE_MAP_OFFSET + 20:contractmod.COARSE_MAP_OFFSET + 22] = b"\x34\x12"
        changed = copy.deepcopy(self.contract)
        changed["gather_samples"] = [
            {"frame": 1, "input": "Right", "builder_frame": 1, "destination": "0x0437-0x0438",
             "runs": [{"source_x": 20, "step": 2, "words": 1}],
             "expected_sha256": hashlib.sha256(b"\x34\x12").hexdigest()},
            {"frame": 2, "input": "Right+Up", "builder_frame": 4, "destination": "0x0437-0x0438",
             "runs": [{"source_x": 20, "step": 2, "words": 1}],
             "expected_sha256": hashlib.sha256(b"\x34\x12").hexdigest()},
        ]
        self.assertEqual(contractmod._validate_gather(changed, decoded), 4)
        decoded[contractmod.COARSE_MAP_OFFSET + 20] ^= 1
        with self.assertRaisesRegex(contractmod.ContractError, "gather reconstruction"):
            contractmod._validate_gather(changed, decoded)

    def test_collision_addressing_preserves_width_stride_and_wrapping(self) -> None:
        decoded = bytearray(0x18020)
        width, x, y = 256, 64, 64
        coarse = [514, 516, 1026, 1028]
        for index, value in zip(coarse, (1, 2, 3, 4), strict=True):
            decoded[contractmod.COARSE_MAP_OFFSET + index:contractmod.COARSE_MAP_OFFSET + index + 2] = value.to_bytes(2, "little")
        points = [[0, 0]] * 10
        offsets, values = contractmod._sample_track(decoded, points, x, y, width)
        self.assertEqual(offsets, [contractmod.SAMPLE_BLOCKS_OFFSET + 32] * 10)
        self.assertEqual(values, [0] * 10)
        with self.assertRaisesRegex(contractmod.ContractError, "bounded"):
            contractmod._sample_track(decoded, points, x, y, 1024)


if __name__ == "__main__":
    unittest.main()
