"""Read-only SNES ROM identification.

The input bytes are never modified or normalised. A copier header, if
present, is reported and the internal header is located relative to it;
hashes are always taken over the file exactly as supplied.

Header field meanings follow the commonly documented SNES cartridge header
layout. They are diagnostic: region and mapping are read from the header,
not confirmed by execution.
"""

from __future__ import annotations

import hashlib
import json
import zlib
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = 1
COPIER_HEADER_SIZE = 512

# Internal header offsets relative to the start of ROM data (no copier header).
HEADER_OFFSETS = {"lorom": 0x7FC0, "hirom": 0xFFC0, "exhirom": 0x40FFC0}

COUNTRY_CODES = {
    0x00: ("Japan", "NTSC"),
    0x01: ("USA/Canada", "NTSC"),
    0x02: ("Europe", "PAL"),
    0x03: ("Sweden/Scandinavia", "PAL"),
    0x04: ("Finland", "PAL"),
    0x05: ("Denmark", "PAL"),
    0x06: ("France", "PAL"),
    0x07: ("Netherlands", "PAL"),
    0x08: ("Spain", "PAL"),
    0x09: ("Germany/Austria/Switzerland", "PAL"),
    0x0A: ("Italy", "PAL"),
    0x0B: ("China/Hong Kong", "PAL"),
    0x0C: ("Indonesia", "PAL"),
    0x0D: ("South Korea", "NTSC"),
    0x0F: ("Canada", "NTSC"),
    0x10: ("Brazil", "PAL-M"),
    0x11: ("Australia", "PAL"),
}

MAP_MODES = {
    0x20: "LoROM",
    0x21: "HiROM",
    0x23: "SA-1",
    0x25: "ExHiROM",
    0x30: "LoROM FastROM",
    0x31: "HiROM FastROM",
    0x32: "ExLoROM",
    0x35: "ExHiROM FastROM",
}

VECTOR_NAMES = (
    "native_unused0", "native_unused1", "native_cop", "native_brk", "native_abort",
    "native_nmi", "native_reset_unused", "native_irq",
    "emu_unused0", "emu_unused1", "emu_cop", "emu_unused2", "emu_abort",
    "emu_nmi", "emu_reset", "emu_irq_brk",
)


class RomError(Exception):
    """Raised for input problems; the CLI maps these to exit codes."""


def _hashes(data: bytes) -> dict[str, Any]:
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
    }


def _decode_header(rom: bytes, base: int) -> dict[str, Any] | None:
    if base + 32 > len(rom):
        return None
    h = rom[base : base + 32]
    complement = int.from_bytes(h[28:30], "little")
    checksum = int.from_bytes(h[30:32], "little")
    title_bytes = h[0:21]
    country = h[25]
    developer = h[26]
    fields: dict[str, Any] = {
        "offset": base,
        "title_raw_hex": title_bytes.hex(),
        "title": title_bytes.decode("ascii", errors="replace").rstrip(" "),
        "map_mode": h[21],
        "map_mode_name": MAP_MODES.get(h[21], "unknown"),
        "cartridge_type": h[22],
        "rom_size_code": h[23],
        "ram_size_code": h[24],
        "country_code": country,
        "country": COUNTRY_CODES.get(country, ("unknown", "unknown"))[0],
        "video_standard": COUNTRY_CODES.get(country, ("unknown", "unknown"))[1],
        "developer_code": developer,
        "version": h[27],
        "checksum_complement": complement,
        "checksum": checksum,
        "complement_matches": (complement ^ checksum) == 0xFFFF,
    }
    if developer == 0x33 and base >= 16:
        ext = rom[base - 16 : base]
        fields["extended_header"] = {
            "maker_code": ext[0:2].decode("ascii", errors="replace"),
            "game_code": ext[2:6].decode("ascii", errors="replace"),
            "expansion_ram_size_code": ext[13],
            "special_version": ext[14],
            "cartridge_subtype": ext[15],
        }
    vectors = rom[base + 32 : base + 64]
    fields["vectors"] = {
        name: int.from_bytes(vectors[2 * i : 2 * i + 2], "little")
        for i, name in enumerate(VECTOR_NAMES)
        if 2 * i + 2 <= len(vectors)
    }
    return fields


def _title_plausible(title: str) -> bool:
    return bool(title) and all(32 <= ord(ch) < 127 for ch in title)


def _score(candidate: str, fields: dict[str, Any]) -> int:
    """Higher is a more plausible internal header. Deterministic and explicit."""
    score = 0
    if fields["complement_matches"]:
        score += 4
    if _title_plausible(fields["title"]):
        score += 2
    mode = fields["map_mode"]
    expected = {"lorom": (0x20, 0x30, 0x32), "hirom": (0x21, 0x31), "exhirom": (0x25, 0x35)}
    if mode in expected[candidate]:
        score += 2
    if fields["vectors"].get("emu_reset", 0xFFFF) not in (0x0000, 0xFFFF):
        score += 1
    return score


def snes_checksum(rom: bytes) -> int:
    """Byte sum with the customary mirroring of a non power-of-two tail."""
    size = len(rom)
    if size == 0:
        return 0
    if size & (size - 1) == 0:
        return sum(rom) & 0xFFFF
    # Split into the largest power-of-two prefix and a mirrored remainder.
    top = 1 << (size.bit_length() - 1)
    head, tail = rom[:top], rom[top:]
    if not tail:
        return sum(head) & 0xFFFF
    repeats = top // len(tail)
    return (sum(head) + sum(tail) * repeats) & 0xFFFF


def inspect_rom(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise RomError(f"file not found: {path}")
    if not path.is_file():
        raise RomError(f"not a regular file: {path}")
    data = path.read_bytes()
    if len(data) < 0x8000:
        raise RomError(f"file too small to hold a SNES header ({len(data)} bytes)")

    copier = len(data) % 1024 == COPIER_HEADER_SIZE
    rom = data[COPIER_HEADER_SIZE:] if copier else data

    candidates = {}
    for name, base in HEADER_OFFSETS.items():
        fields = _decode_header(rom, base)
        if fields is not None:
            fields["score"] = _score(name, fields)
            candidates[name] = fields
    best = max(candidates, key=lambda k: (candidates[k]["score"], k == "lorom"))
    header = candidates[best]

    computed = snes_checksum(rom)
    manifest: dict[str, Any] = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "file": {"name": path.name, **_hashes(data)},
        "copier_header": {
            "present": copier,
            "size": COPIER_HEADER_SIZE if copier else 0,
            "note": "hashes above cover the whole file as supplied; rom_data hashes exclude the copier header",
        },
        "rom_data": _hashes(rom) if copier else None,
        "header_candidates": {k: v["score"] for k, v in candidates.items()},
        "header_location": best,
        "header": header,
        "checksum": {
            "header": header["checksum"],
            "computed": computed,
            "matches": computed == header["checksum"],
        },
    }
    return manifest


# Fields compared by ``--expect``. Anything else in the manifest is informational.
IDENTITY_FIELDS = (
    ("file.size", ("file", "size")),
    ("file.sha256", ("file", "sha256")),
    ("copier_header.present", ("copier_header", "present")),
    ("header_location", ("header_location",)),
    ("header.title", ("header", "title")),
    ("header.map_mode", ("header", "map_mode")),
    ("header.country_code", ("header", "country_code")),
    ("header.version", ("header", "version")),
    ("header.checksum", ("header", "checksum")),
    ("checksum.matches", ("checksum", "matches")),
)


def _lookup(tree: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = tree
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def compare_identity(observed: dict[str, Any], expected: dict[str, Any]) -> list[dict[str, Any]]:
    """Return one entry per identity field, with a match flag."""
    results = []
    for label, key_path in IDENTITY_FIELDS:
        obs, exp = _lookup(observed, key_path), _lookup(expected, key_path)
        results.append({"field": label, "expected": exp, "observed": obs, "matches": obs == exp})
    return results


def load_manifest(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise RomError(f"manifest not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except json.JSONDecodeError as exc:
        raise RomError(f"manifest is not valid JSON: {path}: {exc}") from exc
    if not isinstance(manifest, dict) or "file" not in manifest:
        raise RomError(f"manifest lacks a 'file' section: {path}")
    return manifest


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
