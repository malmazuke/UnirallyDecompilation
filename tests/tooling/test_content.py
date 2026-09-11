"""ROM-free tests of the content package (M1-03): the decompressor port on a
hand-built stream, tile/palette/layer rendering and comparison on synthetic
data, the provenance pairing on a synthetic access record, the manifest
validation and the decode command on a synthetic ROM."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from unirally_lab.content import commands as content_commands  # noqa: E402
from unirally_lab.content import ppu, provenance, rnc  # noqa: E402

PROJECT = ROOT / "tools" / "project.py"


# ------------------------------------------------------------ RNC stream builder (test-side encoder)


class BitWriter:
    """LSB-first bits into 16-bit little-endian words; a literal run's raw bytes are placed after the word
    holding the last bit written before them (the decoder keeps a 16-bit window and re-reads from there)."""

    def __init__(self) -> None:
        self.bits: list[int] = []
        self.raw: dict[int, list[bytes]] = {}

    def write(self, value: int, n: int) -> None:
        for k in range(n):
            self.bits.append((value >> k) & 1)

    def write_code(self, code_msb_first: str) -> None:
        for ch in code_msb_first:
            self.write(int(ch), 1)

    def literal_bytes(self, data: bytes) -> None:
        word = (len(self.bits) - 1) // 16
        self.raw.setdefault(word, []).append(data)

    def serialize(self) -> bytes:
        out = bytearray()
        words = (len(self.bits) + 15) // 16
        for w in range(max(words, max(self.raw) + 1 if self.raw else 0)):
            v = 0
            for k in range(16):
                i = w * 16 + k
                if i < len(self.bits):
                    v |= self.bits[i] << k
            out += struct.pack("<H", v)
            for chunk in self.raw.get(w, []):
                out += chunk
        return bytes(out)


def canonical_codes(lengths: list[int]) -> list[str]:
    """Canonical prefix codes (MSB-first strings) for symbol code lengths, as RNC assigns them."""
    codes = [""] * len(lengths)
    code = 0
    for length in range(1, 17):
        for i, ln in enumerate(lengths):
            if ln == length:
                codes[i] = format(code, f"0{length}b")
                code += 1
        code <<= 1
    return codes


def write_table(bw: BitWriter, lengths: list[int]) -> list[str]:
    bw.write(len(lengths), 5)
    for ln in lengths:
        bw.write(ln, 4)
    return canonical_codes(lengths)


def build_stream(chunks: int = 1) -> tuple[bytes, bytes]:
    """An RNC method-1 asset: header, then one chunk producing b'ABCBCDDDD'."""
    bw = BitWriter()
    bw.write(0, 2)
    raw_codes = write_table(bw, [1, 2, 2])      # symbols 0, 1, 2(+1 extra bit)
    dist_codes = write_table(bw, [1, 1])        # distance 0 (repeat last byte) or 1 (two back)
    len_codes = write_table(bw, [1, 1])         # length 2 or 3
    bw.write(3, 16)                             # three literal runs
    # literal 1: symbol 2 with extra bit 1 -> 3 bytes; the code ends exactly on a word boundary (bit 64)
    bw.write_code(raw_codes[2])
    bw.write(1, 1)
    assert len(bw.bits) == 64
    bw.literal_bytes(b"ABC")
    # copy 1: distance 1 (two back), length 2 -> "BC"
    bw.write_code(dist_codes[1])
    bw.write_code(len_codes[0])
    # literal 2: symbol 1 -> 1 byte, not on a word boundary
    bw.write_code(raw_codes[1])
    bw.literal_bytes(b"D")
    # copy 2: distance 0 (repeat), length 3 -> "DDD"
    bw.write_code(dist_codes[0])
    bw.write_code(len_codes[1])
    # literal 3: symbol 0 -> no bytes
    bw.write_code(raw_codes[0])
    data = bw.serialize()
    expected = b"ABCBCDDDD"
    header = b"RNC\x01" + struct.pack(">II", len(expected), len(data)) + b"\x00\x00\x00\x00\x00" + bytes([chunks])
    return header + data, expected


class RncTests(unittest.TestCase):
    def test_hand_built_stream_decodes(self) -> None:
        asset, expected = build_stream()
        read = rnc.flat_reader(asset, bank=0x18, base=0x8000)
        out, end = rnc.decompress(read, 0x18, 0x8000)
        self.assertEqual(out, expected)
        self.assertEqual(end[0], 0x18)
        hdr = rnc.parse_header(read, 0x18, 0x8000)
        self.assertEqual((hdr["magic"], hdr["method"], hdr["unpacked_length"], hdr["chunks"]), ("RNC", 1, len(expected), 1))

    def test_bank_wrap_of_the_source_pointer(self) -> None:
        """An asset that straddles a LoROM bank end decodes identically."""
        asset, expected = build_stream()
        pad = 0x8000 - 7
        read = rnc.flat_reader(b"\0" * pad + asset, bank=0x18, base=0x8000)
        out, end = rnc.decompress(read, 0x18, 0x8000 + pad)
        self.assertEqual(out, expected)
        self.assertEqual(end[0], 0x19)

    def test_masks_and_bases(self) -> None:
        self.assertEqual(rnc.MASK[16], 0xFFFF)
        self.assertEqual(rnc.BASE[15], 0x8000)
        self.assertEqual(rnc.MASK[5], 31)

    def test_getbits_is_lsb_first(self) -> None:
        data = b"RNC\x01" + b"\0" * 14 + bytes([0b10110010, 0b00000001, 0xFF, 0xFF])
        d = rnc.Decompressor(rnc.flat_reader(data, bank=1, base=0x8000), 1, 0x8000)
        d.adv(0x12)
        d.r8F = d.peek16()
        d.r93 = 0
        self.assertEqual(d.getbits(3), 0b010)
        self.assertEqual(d.getbits(5), 0b10110)
        self.assertEqual(d.getbits(1), 1)


# ------------------------------------------------------------ PPU helpers


def make_tile_4bpp(pixels: list[int]) -> bytes:
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            v = pixels[y * 8 + x]
            bit = 7 - x
            out[2 * y] |= ((v >> 0) & 1) << bit
            out[2 * y + 1] |= ((v >> 1) & 1) << bit
            out[16 + 2 * y] |= ((v >> 2) & 1) << bit
            out[17 + 2 * y] |= ((v >> 3) & 1) << bit
    return bytes(out)


class PpuTests(unittest.TestCase):
    def test_tile_round_trip(self) -> None:
        px = [(x + y) & 15 for y in range(8) for x in range(8)]
        self.assertEqual(ppu.decode_tile_4bpp(make_tile_4bpp(px), 0), px)

    def test_colour_conversion(self) -> None:
        self.assertEqual(ppu.channel8(31), 255)
        self.assertEqual(ppu.channel8(0), 0)
        self.assertEqual(ppu.cgram_rgb(0x7FFF), (255, 255, 255))
        r, g, b = ppu.cgram_rgb(0x001F)
        self.assertEqual((r, g, b), (255, 0, 0))
        self.assertLess(ppu.channel8(8), (8 << 3) | (8 >> 2))   # the gamma curve darkens the lower half

    def test_background_placement_scroll_and_flip(self) -> None:
        vram = bytearray(0x10000)
        tile = [0] * 64
        tile[0] = 5          # top-left pixel only
        vram[0x4000 + 32:0x4000 + 64] = make_tile_4bpp(tile)      # tile 1 at tile base 0x4000
        map_base = 0x1800
        entry = (1) | (2 << 10)                                     # tile 1, palette 2
        vram[map_base + (3 * 32 + 4) * 2] = entry & 0xFF
        vram[map_base + (3 * 32 + 4) * 2 + 1] = entry >> 8
        layer = ppu.render_bg(bytes(vram), map_base, False, False, 0x4000, 4, False, 0, 0)
        # row 3 column 4: pixel (32, 24) but the PPU's first line is line 1, so it lands on screen y 23
        self.assertEqual(layer.index[23 * 256 + 32], (2 << 4) + 5)
        self.assertEqual(sum(layer.index), (2 << 4) + 5)
        scrolled = ppu.render_bg(bytes(vram), map_base, False, False, 0x4000, 4, False, 2, 1)
        self.assertEqual(scrolled.index[22 * 256 + 30], (2 << 4) + 5)
        vram[map_base + (3 * 32 + 4) * 2 + 1] = (entry >> 8) | 0x40    # horizontal flip
        flipped = ppu.render_bg(bytes(vram), map_base, False, False, 0x4000, 4, False, 0, 0)
        self.assertEqual(flipped.index[23 * 256 + 39], (2 << 4) + 5)

    def test_16x16_tiles_use_the_next_row_of_names(self) -> None:
        vram = bytearray(0x10000)
        tile = [0] * 64
        tile[63] = 1
        vram[0x4000 + 17 * 32:0x4000 + 18 * 32] = make_tile_4bpp(tile)   # name 17 = bottom-right quarter of 16x16 tile 0
        layer = ppu.render_bg(bytes(vram), 0x1800, False, False, 0x4000, 4, True, 0, 0)
        self.assertEqual(layer.index[14 * 256 + 15], 1)

    def test_sprite_rendering(self) -> None:
        vram = bytearray(0x10000)
        tile = [3] * 64
        vram[0xC000 + 5 * 32:0xC000 + 6 * 32] = make_tile_4bpp(tile)
        oam = bytearray(544)
        oam[0:4] = bytes([10, 20, 5, (1 << 1)])        # x 10, y 20, tile 5, palette 1, priority 0
        layer = ppu.render_sprites(bytes(vram), bytes(oam), 0x83)
        self.assertEqual(layer.index[20 * 256 + 10], 128 + 16 + 3)
        self.assertEqual(layer.index[27 * 256 + 17], 128 + 16 + 3)
        self.assertEqual(layer.index[28 * 256 + 18], 0)

    def test_compose_and_compare(self) -> None:
        palette = [(i, i, i) for i in range(256)]
        a = ppu.Layer()
        a.index[0] = 7
        b = ppu.Layer()
        b.index[0] = 9
        b.priority[0] = 1
        img = ppu.compose(palette, 1, [(a, 0), (b, 1)])
        self.assertEqual(img[0:3], bytes((9, 9, 9)))
        self.assertEqual(img[3:6], bytes((1, 1, 1)))
        other = bytearray(img)
        other[0] = 0
        mism, total, diff = ppu.compare(img, bytes(other), 256, (0, 0, 4, 2))
        self.assertEqual((mism, total), (1, 8))
        self.assertEqual(diff[:3], b"\xff\xff\xff")

    def test_png_round_trip(self) -> None:
        rgb = bytes(range(256)) * 3
        png = ppu.write_png(16, 16, rgb)
        self.assertEqual(ppu.read_png(png), (16, 16, rgb))


# ------------------------------------------------------------ provenance


def synthetic_record() -> dict:
    channels = {"0": {"DMAP": 1, "BBAD": 0x18, "A1T": 0x168080, "DAS": 64, "DASB": 0, "A2A": 0, "NTRL": 0}}
    wram_ch = {"0": {"DMAP": 1, "BBAD": 0x18, "A1T": 0x000459, "DAS": 32, "DASB": 0, "A2A": 0, "NTRL": 0}}
    return {
        "schema_version": 1, "kind": "access_record", "rom": {}, "core": {}, "frames": {"start": 0, "end": 2, "count": 3},
        "instructions": {"total": 3, "max_frame_delta": 1, "per_frame": [1, 1, 1]}, "accesses": [], "rom_reads": [], "resolutions": [],
        "kind_names": ["read", "write", "rmw", "push", "pull", "block_read", "block_write"],
        "residual": {"dma_triggers": 3, "unresolved_total": 0},
        "dma_log": [[1, 10, 0x82E1FB, "MDMAEN", 1, channels], [1, 30, 0x82E263, "MDMAEN", 1, channels], [2, 5, 0x82D28B, "MDMAEN", 1, wram_ch]],
        "watch_addresses": {
            str(0x002116): {"1": {"w": [[5, 0x82E1F4, "write", 0x002116, 2, 0x2000], [25, 0x82E25C, "write", 0x002116, 2, 0x2100]], "r": []}},
            str(0x002115): {"1": {"w": [[2, 0x82E168, "write", 0x002115, 1, 0x80]], "r": []}},
        },
        "watch_pcs": {"409": [[404, 2, 0x100, 0x200, 0, 0, 0x80, 0, 0], [404, 1, 0x101, 0x201, 0, 0, 0, 0, 0], [404, 0, 0x102, 0x202, 0, 0, 0, 0, 0],
                              [405, 0, 0x300, 0x400, 0, 0, 0x26, 0, 0]]},
    }


class ProvenanceTests(unittest.TestCase):
    def test_dma_rows_pair_with_the_last_address_write(self) -> None:
        rows = provenance.dma_inventory(synthetic_record())
        self.assertEqual(len(rows), 3)
        self.assertEqual((rows[0]["vmadd"], rows[0]["vmain"], rows[0]["rom_file_offset"], rows[0]["a_bus_region"]), (0x2000, 0x80, 0xB0080, "rom"))
        self.assertEqual(rows[1]["vmadd"], 0x2100)
        self.assertEqual((rows[2]["vmadd"], rows[2]["a_bus_region"]), (None, "wram"))    # no address write in frame 2
        self.assertEqual(provenance.dma_inventory(synthetic_record(), 2, 2)[0]["frame"], 2)

    def test_block_moves_group_by_the_count_register(self) -> None:
        moves = provenance.block_moves(synthetic_record())
        self.assertEqual(len(moves), 2)
        self.assertEqual((moves[0]["source_offset"], moves[0]["destination_offset"], moves[0]["length"], moves[0]["destination_bank"], moves[0]["complete"]),
                         (0x100, 0x200, 3, 0, True))
        self.assertEqual((moves[1]["length"], moves[1]["caller_dbr"]), (1, 0x26))

    def test_summary_reconciles_triggers(self) -> None:
        doc = synthetic_record()
        rows = provenance.dma_inventory(doc)
        summ = provenance.summary(doc, rows, provenance.block_moves(doc))
        self.assertEqual((summ["mdmaen_stores"], summ["record_dma_triggers"], summ["destinations_paired"], summ["destinations_pairable"]), (3, 3, 2, 3))

    def test_port_images_follow_vmain(self) -> None:
        doc = synthetic_record()
        doc["watch_addresses"][str(0x002118)] = {"1": {"w": [[6, 0, "write", 0x002118, 2, 0xBBAA], [7, 0, "write", 0x002118, 2, 0xDDCC]], "r": []}}
        img = provenance.port_images(doc)
        self.assertEqual(img["vram"][0x4000:0x4004], bytes([0xAA, 0xBB, 0xCC, 0xDD]))
        self.assertEqual(img["vram_ranges"], [[0x4000, 4]])


# ------------------------------------------------------------ manifest and decode command


def synthetic_rom() -> bytes:
    rom = bytearray(0x10000)
    asset, _ = build_stream()
    rom[0x0000:len(asset)] = asset            # bank $80:8000 under the LoROM rule (file offset 0)
    rom[0x1000:0x1010] = bytes(range(16))
    return bytes(rom)


def synthetic_manifest(rom: bytes) -> dict:
    _, expected = build_stream()
    raw = rom[0x1000:0x1008] + rom[0x100C:0x1010]
    return {
        "schema_version": 1, "kind": "content_manifest", "id": "synthetic", "scenario_id": "none",
        "rom": {"sha256": hashlib.sha256(rom).hexdigest(), "size": len(rom)},
        "items": [
            {"id": "packed", "kind": "rnc", "source": {"bank": 0, "address": 0x8000}, "expected": {"length": len(expected), "sha256": hashlib.sha256(expected).hexdigest()},
             "runtime": {"work_ram_offset": 0x10, "known_runtime_writes": [1]}},
            {"id": "pieces", "kind": "raw", "pieces": [{"file_offset": 0x1000, "length": 8}, {"file_offset": 0x100C, "length": 4}],
             "expected": {"length": 12, "sha256": hashlib.sha256(raw).hexdigest()}},
        ],
    }


class ManifestTests(unittest.TestCase):
    def test_validation_rejects_malformed(self) -> None:
        m = synthetic_manifest(synthetic_rom())
        content_commands.validate_manifest(m)
        bad = json.loads(json.dumps(m))
        bad["items"][1]["pieces"][0]["length"] = 0
        with self.assertRaises(ValueError):
            content_commands.validate_manifest(bad)
        bad = json.loads(json.dumps(m))
        bad["items"].append(dict(m["items"][0]))
        with self.assertRaises(ValueError):
            content_commands.validate_manifest(bad)
        with self.assertRaises(ValueError):
            content_commands.validate_manifest({"schema_version": 2})

    def test_decode_command_on_a_synthetic_rom(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            rom = synthetic_rom()
            (tmp_path / "rom.bin").write_bytes(rom)
            manifest = synthetic_manifest(rom)
            (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            _, expected = build_stream()
            dump = bytearray(0x20000)
            dump[0x10:0x10 + len(expected)] = expected
            dump[0x11] ^= 0xFF          # a known runtime write
            (tmp_path / "wram.bin").write_bytes(dump)
            cmd = [sys.executable, str(PROJECT), "content", "decode", "--manifest", str(tmp_path / "manifest.json"), "--rom", str(tmp_path / "rom.bin"),
                   "--out", str(tmp_path / "out"), "--wram-dump", str(tmp_path / "wram.bin"), "--report", str(tmp_path / "report.json")]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((tmp_path / "report.json").read_text())
            names = {c["name"]: c["outcome"] for c in report["checks"]}
            self.assertEqual(names["decode_packed"], "passed")
            self.assertEqual(names["work_ram_packed"], "passed")
            self.assertEqual(names["decode_pieces"], "passed")
            self.assertEqual((tmp_path / "out" / "packed.bin").read_bytes(), expected)
            # a wrong expected digest fails with exit 1
            manifest["items"][1]["expected"]["sha256"] = "0" * 64
            (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            # a missing ROM is a missing prerequisite
            cmd[cmd.index("--rom") + 1] = str(tmp_path / "absent.bin")
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)

    def test_provenance_command_on_a_synthetic_record(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "access.json").write_text(json.dumps(synthetic_record()), encoding="utf-8")
            cmd = [sys.executable, str(PROJECT), "content", "provenance", "--access", str(tmp_path / "access.json"), "--out", str(tmp_path / "prov"),
                   "--report", str(tmp_path / "report.json")]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            inv = json.loads((tmp_path / "prov" / "provenance.json").read_text())
            self.assertEqual(len(inv["dma"]), 3)
            self.assertEqual(len(inv["block_moves"]), 2)
            cmd[cmd.index("--access") + 1] = str(tmp_path / "absent.json")
            self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
