"""ROM-free schema-1 Classic pack tests using only authored bytes."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.content import pack  # noqa: E402


class ClassicPackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rom = bytes(range(64))
        self.rules = {
            "schema_version": 1, "kind": "classic_pack_rules",
            "profile_id": pack.PROFILE_ID, "start_state_id": pack.START_STATE_ID,
            "source_rom": {"size": len(self.rom), "sha256": hashlib.sha256(self.rom).hexdigest()},
            "entries": [
                {"id": "fixture.a", "source": {"kind": "raw", "pieces": [{"file_offset": 3, "length": 9}]},
                 "size": 9, "sha256": hashlib.sha256(self.rom[3:12]).hexdigest()},
                {"id": "fixture.b", "source": {"kind": "raw", "pieces": [{"file_offset": 20, "length": 5}, {"file_offset": 40, "length": 4}]},
                 "size": 9, "sha256": hashlib.sha256(self.rom[20:25] + self.rom[40:44]).hexdigest()},
            ],
        }
        self.rules_sha = "a5" * 32
        self.payload, self.rows = pack.build_pack(self.rom, self.rules, self.rules_sha)

    def test_deterministic_round_trip_and_logical_lookup_table(self) -> None:
        again, rows = pack.build_pack(self.rom, self.rules, self.rules_sha)
        self.assertEqual(again, self.payload)
        self.assertEqual(rows, self.rows)
        inspected = pack.validate_pack(self.payload, self.rules, self.rules_sha)
        self.assertEqual([row["id"] for row in inspected["entries"]], ["fixture.a", "fixture.b"])
        self.assertEqual(inspected["pack_sha256"], hashlib.sha256(self.payload).hexdigest())

    def test_wrong_source_rom_is_rejected_before_pack_creation(self) -> None:
        with self.assertRaisesRegex(ValueError, "source ROM identity"):
            pack.build_pack(self.rom[:-1], self.rules, self.rules_sha)

    def test_atomic_interruption_leaves_no_output_or_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "classic.pack"
            with self.assertRaises(InterruptedError):
                pack.write_atomic(path, self.payload, interrupt_before_commit=True)
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_header_schema_and_identity_mutations_are_rejected(self) -> None:
        cases = {"magic": 0, "schema": 8, "source": 12, "rules": 44,
                 "profile": 78, "start": 78 + len(pack.PROFILE_ID) + 2}
        for label, offset in cases.items():
            with self.subTest(label=label):
                changed = bytearray(self.payload); changed[offset] ^= 1
                with self.assertRaises(ValueError):
                    pack.validate_pack(bytes(changed), self.rules, self.rules_sha)

    def test_manifest_and_entry_payload_mutations_are_rejected(self) -> None:
        first = self.rows[0]
        for label, offset in (("logical_id", 78 + len(pack.PROFILE_ID) + 2 + len(pack.START_STATE_ID) + 4),
                              ("payload", first["offset"]), ("truncated", len(self.payload) - 1)):
            with self.subTest(label=label):
                changed = bytearray(self.payload)
                if label == "truncated": changed = changed[:-1]
                else: changed[offset] ^= 1
                with self.assertRaises(ValueError):
                    pack.validate_pack(bytes(changed), self.rules, self.rules_sha)

    def test_duplicate_missing_and_extra_entries_are_rejected(self) -> None:
        duplicate = {**self.rules, "entries": [self.rules["entries"][0], self.rules["entries"][0]]}
        payload, _ = pack.build_pack(self.rom, duplicate, self.rules_sha)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            pack.validate_pack(payload, duplicate, self.rules_sha)
        for entries in (self.rules["entries"][:1], self.rules["entries"] + [{
                "id": "fixture.c", "source": {"kind": "raw", "pieces": [{"file_offset": 0, "length": 1}]},
                "size": 1, "sha256": hashlib.sha256(self.rom[:1]).hexdigest()}]):
            changed_rules = {**self.rules, "entries": entries}
            with self.assertRaises(ValueError):
                pack.validate_pack(self.payload, changed_rules, self.rules_sha)

    def test_stable_commands_report_success_missing_invalid_and_interrupted(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "artifacts") as temporary:
            base = Path(temporary)
            rom = base / "authored.rom"; rom.write_bytes(self.rom)
            rules = base / "rules.json"; rules.write_text(json.dumps(self.rules))
            first, second = base / "first.pack", base / "second.pack"
            def run(*arguments: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run([sys.executable, str(ROOT / "tools/project.py"), "content", *arguments],
                                      cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(run("pack", "--rom", str(rom), "--rules", str(rules), "--out", str(first),
                                 "--report", str(base / "first.json")).returncode, 0)
            self.assertEqual(run("pack", "--rom", str(rom), "--rules", str(rules), "--out", str(second),
                                 "--report", str(base / "second.json")).returncode, 0)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(run("pack-inspect", "--pack", str(first), "--rules", str(rules),
                                 "--report", str(base / "inspect.json")).returncode, 0)
            self.assertEqual(run("pack", "--rom", str(base / "absent.rom"), "--rules", str(rules),
                                 "--out", str(base / "missing.pack")).returncode, 2)
            wrong = base / "wrong.rom"; wrong.write_bytes(self.rom[:-1])
            self.assertEqual(run("pack", "--rom", str(wrong), "--rules", str(rules),
                                 "--out", str(base / "wrong.pack")).returncode, 3)
            stopped = base / "stopped.pack"
            self.assertEqual(run("pack", "--rom", str(rom), "--rules", str(rules), "--out", str(stopped),
                                 "--simulate-interruption-before-commit").returncode, 1)
            self.assertFalse(stopped.exists())


if __name__ == "__main__":
    unittest.main()
