"""24-bit SNES address -> ROM offset under the LoROM rule of this cartridge.

The pinned core maps this ROM as board ``LOROM-RAM#A`` (bsnes heuristics for
map mode 0x30, cartridge type 2, 8 KiB save RAM, 2 MiB): program ROM answers
banks $00-$6F and $80-$EF at offsets $8000-$FFFF with mask 0x8000, so ROM
offset = ((bank & 0x7F) << 15 | (address & 0x7FFF)) modulo the ROM size and
a ROM byte is reachable through several banks (mirrors). Work RAM is banks
$7E-$7F entirely and $0000-$1FFF of banks $00-$3F and $80-$BF. Everything
else (registers, save RAM at banks $70-$7D/$F0-$FF, open bus) is ``other``.
"""

from __future__ import annotations

from typing import Final

REGION_ROM: Final = "rom"
REGION_WRAM: Final = "wram"
REGION_OTHER: Final = "other"


def classify(address: int) -> str:
    bank = (address >> 16) & 0xFF
    offset = address & 0xFFFF
    if bank in (0x7E, 0x7F):
        return REGION_WRAM
    if offset < 0x2000 and (bank <= 0x3F or 0x80 <= bank <= 0xBF):
        return REGION_WRAM
    if offset >= 0x8000 and (bank <= 0x6F or 0x80 <= bank <= 0xEF):
        return REGION_ROM
    return REGION_OTHER


def rom_offset(address: int, rom_size: int) -> int | None:
    """ROM file offset for a ROM-mapped address, else None."""
    if classify(address) != REGION_ROM:
        return None
    bank = (address >> 16) & 0x7F
    return ((bank << 15) | (address & 0x7FFF)) % rom_size


def wram_offset(address: int) -> int | None:
    """Offset into the 128 KiB work RAM for a WRAM-mapped address, else None."""
    if classify(address) != REGION_WRAM:
        return None
    bank = (address >> 16) & 0xFF
    if bank in (0x7E, 0x7F):
        return ((bank - 0x7E) << 16) | (address & 0xFFFF)
    return address & 0x1FFF


def canonical_rom_address(offset: int) -> int:
    """The lowest bank through which a ROM offset is reachable ($00-$3F for 2 MiB)."""
    return ((offset >> 15) << 16) | 0x8000 | (offset & 0x7FFF)
