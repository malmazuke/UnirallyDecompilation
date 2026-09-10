"""Synthetic checks for tools/project.py rom inspect. No ROM required."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab import rom as rommod  # noqa: E402
from unirally_lab import EXIT_FAILURE, EXIT_INVALID_INPUT, EXIT_MISSING_PREREQUISITE, EXIT_OK  # noqa: E402

PROJECT = ROOT / "tools" / "project.py"


def make_rom(size: int, header_base: int, map_mode: int, country: int = 0x02, title: bytes = b"SYNTHETIC") -> bytes:
    """Build a synthetic image with a self-consistent internal header."""
    rom = bytearray(b"\x00" * size)
    # Give the body some content so the checksum is not trivially zero.
    for i in range(0, size, 977):
        rom[i] = (i // 977) & 0xFF
    h = header_base
    rom[h : h + 21] = title.ljust(21, b" ")
    rom[h + 21] = map_mode
    rom[h + 22] = 0x02
    rom[h + 23] = (size // 1024).bit_length() - 1
    rom[h + 24] = 0x03
    rom[h + 25] = country
    rom[h + 26] = 0x01
    rom[h + 27] = 0x00
    # Emulation-mode reset vector, non-trivial.
    rom[h + 32 + 28 : h + 32 + 30] = (0x8000).to_bytes(2, "little")
    rom[h + 28 : h + 32] = b"\x00\x00\x00\x00"
    checksum = sum(rom) & 0xFFFF
    # Adding complement+checksum contributes 0xFF+0xFF+... ; solve iteratively.
    for _ in range(4):
        complement = checksum ^ 0xFFFF
        rom[h + 28 : h + 30] = complement.to_bytes(2, "little")
        rom[h + 30 : h + 32] = checksum.to_bytes(2, "little")
        new = sum(rom) & 0xFFFF
        if new == checksum:
            break
        checksum = new
    return bytes(rom)


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(PROJECT), *args], capture_output=True, text=True, timeout=60)


class InspectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, data: bytes) -> Path:
        p = self.dir / name
        p.write_bytes(data)
        return p

    def test_lorom_detected_and_checksum_valid(self) -> None:
        p = self.write("lo.sfc", make_rom(0x40000, 0x7FC0, 0x20))
        m = rommod.inspect_rom(p)
        self.assertEqual(m["header_location"], "lorom")
        self.assertFalse(m["copier_header"]["present"])
        self.assertTrue(m["header"]["complement_matches"])
        self.assertTrue(m["checksum"]["matches"])
        self.assertEqual(m["header"]["title"], "SYNTHETIC")
        self.assertEqual(m["header"]["video_standard"], "PAL")
        self.assertEqual(m["header"]["vectors"]["emu_reset"], 0x8000)

    def test_hirom_detected(self) -> None:
        p = self.write("hi.sfc", make_rom(0x100000, 0xFFC0, 0x21, country=0x01))
        m = rommod.inspect_rom(p)
        self.assertEqual(m["header_location"], "hirom")
        self.assertEqual(m["header"]["video_standard"], "NTSC")
        self.assertTrue(m["checksum"]["matches"])

    def test_copier_header_reported_not_stripped_from_file_hash(self) -> None:
        body = make_rom(0x40000, 0x7FC0, 0x20)
        data = b"\xAB" * 512 + body
        p = self.write("headered.smc", data)
        m = rommod.inspect_rom(p)
        self.assertTrue(m["copier_header"]["present"])
        self.assertEqual(m["file"]["size"], len(data))
        self.assertEqual(m["rom_data"]["size"], len(body))
        self.assertEqual(m["header_location"], "lorom")
        self.assertTrue(m["checksum"]["matches"])
        self.assertNotEqual(m["file"]["sha256"], m["rom_data"]["sha256"])
        self.assertEqual(p.read_bytes(), data, "input must be untouched")

    def test_corrupted_body_fails_checksum(self) -> None:
        body = bytearray(make_rom(0x40000, 0x7FC0, 0x20))
        body[0x1000] ^= 0x5A
        p = self.write("bad.sfc", bytes(body))
        m = rommod.inspect_rom(p)
        self.assertTrue(m["header"]["complement_matches"])
        self.assertFalse(m["checksum"]["matches"])
        r = run_cli("rom", "inspect", "--path", str(p))
        self.assertEqual(r.returncode, EXIT_FAILURE, r.stderr)

    def test_non_power_of_two_checksum_mirrors_tail(self) -> None:
        self.assertEqual(rommod.snes_checksum(b"\x01" * 1024), 1024 & 0xFFFF)
        # 1024 + 512: tail of 512 mirrored twice to fill 1024.
        data = b"\x01" * 1024 + b"\x02" * 512
        self.assertEqual(rommod.snes_checksum(data), (1024 + 2 * 512 * 2) & 0xFFFF)

    def test_cli_manifest_roundtrip_and_expect_match(self) -> None:
        p = self.write("lo.sfc", make_rom(0x40000, 0x7FC0, 0x20))
        manifest = self.dir / "m.json"
        report = self.dir / "r.json"
        r = run_cli("rom", "inspect", "--path", str(p), "--manifest-out", str(manifest), "--report", str(report))
        self.assertEqual(r.returncode, EXIT_OK, r.stderr)
        rep = json.loads(report.read_text())
        self.assertEqual(rep["status"], "passed")
        self.assertEqual({c["name"]: c["outcome"] for c in rep["checks"]}["internal_checksum"], "passed")
        self.assertEqual(rep["inputs"]["rom"]["sha256"], json.loads(manifest.read_text())["file"]["sha256"])
        self.assertEqual(rep["artifacts"][0]["kind"], "rom_manifest")
        r2 = run_cli("rom", "inspect", "--path", str(p), "--expect", str(manifest))
        self.assertEqual(r2.returncode, EXIT_OK, r2.stderr)

    def test_cli_expect_rejects_other_revision(self) -> None:
        a = self.write("a.sfc", make_rom(0x40000, 0x7FC0, 0x20))
        b = self.write("b.sfc", make_rom(0x40000, 0x7FC0, 0x20, country=0x01, title=b"OTHER"))
        manifest = self.dir / "a.json"
        self.assertEqual(run_cli("rom", "inspect", "--path", str(a), "--manifest-out", str(manifest)).returncode, EXIT_OK)
        report = self.dir / "r.json"
        r = run_cli("rom", "inspect", "--path", str(b), "--expect", str(manifest), "--report", str(report))
        self.assertEqual(r.returncode, EXIT_FAILURE)
        self.assertIn("mismatch file.sha256", r.stderr)
        self.assertIn("mismatch header.country_code", r.stderr)
        rep = json.loads(report.read_text())
        self.assertEqual(rep["status"], "failed")
        check = next(c for c in rep["checks"] if c["name"] == "identity_matches_expected")
        self.assertEqual(check["outcome"], "failed")
        self.assertTrue(any(not f["matches"] for f in check["fields"]))

    def test_cli_missing_file_is_missing_prerequisite(self) -> None:
        report = self.dir / "r.json"
        r = run_cli("rom", "inspect", "--path", str(self.dir / "nope.sfc"), "--report", str(report))
        self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE)
        rep = json.loads(report.read_text())
        self.assertEqual(rep["checks"][0]["outcome"], "missing")
        self.assertEqual(rep["status"], "failed")

    def test_cli_missing_expected_manifest_is_missing_prerequisite(self) -> None:
        p = self.write("lo.sfc", make_rom(0x40000, 0x7FC0, 0x20))
        r = run_cli("rom", "inspect", "--path", str(p), "--expect", str(self.dir / "absent.json"))
        self.assertEqual(r.returncode, EXIT_MISSING_PREREQUISITE)

    def test_cli_too_small_file_is_invalid_input(self) -> None:
        p = self.write("tiny.sfc", b"\x00" * 100)
        r = run_cli("rom", "inspect", "--path", str(p))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)

    def test_cli_refuses_to_overwrite_input(self) -> None:
        data = make_rom(0x40000, 0x7FC0, 0x20)
        p = self.write("lo.sfc", data)
        r = run_cli("rom", "inspect", "--path", str(p), "--manifest-out", str(p))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)
        self.assertEqual(p.read_bytes(), data)
        r = run_cli("rom", "inspect", "--path", str(p), "--report", str(self.dir / "." / "lo.sfc"))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)
        self.assertEqual(p.read_bytes(), data)

    def test_cli_empty_path_does_not_fall_back_to_local_rom(self) -> None:
        r = run_cli("rom", "inspect", "--path", "")
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)
        self.assertNotIn("rom_available", r.stderr, "no ROM may be inspected for an empty path")

    def test_cli_directory_is_invalid_input(self) -> None:
        r = run_cli("rom", "inspect", "--path", str(self.dir))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)

    def test_manifest_schema_version_and_shape_are_validated(self) -> None:
        p = self.write("lo.sfc", make_rom(0x40000, 0x7FC0, 0x20))
        good = self.dir / "good.json"
        self.assertEqual(run_cli("rom", "inspect", "--path", str(p), "--manifest-out", str(good)).returncode, EXIT_OK)
        m = json.loads(good.read_text())
        for bad in ({**m, "manifest_schema_version": 99}, {**m, "file": 5}, [], {"header": {}}):
            f = self.dir / "bad.json"
            f.write_text(json.dumps(bad))
            r = run_cli("rom", "inspect", "--path", str(p), "--expect", str(f))
            self.assertEqual(r.returncode, EXIT_INVALID_INPUT, (bad, r.stderr))
        (self.dir / "bad.json").write_text("{nope")
        r = run_cli("rom", "inspect", "--path", str(p), "--expect", str(self.dir / "bad.json"))
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)

    def test_cli_usage_error_is_invalid_input(self) -> None:
        r = run_cli("rom", "inspect", "--bogus")
        self.assertEqual(r.returncode, EXIT_INVALID_INPUT)


if __name__ == "__main__":
    unittest.main()
