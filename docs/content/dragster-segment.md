# Content record: DRAGSTER (CRAWLER tour) with MIKE — the validated race scenario

Task [M1-03](../../tasks/M1-03.md); evidence [R-0008](../research/R-0008-track-decode.md). Manifest `tests/manifests/content/dragster-segment.json` (content manifest schema 1). No ROM bytes, tiles, palettes, tile maps or images are tracked; this record carries identifiers, offsets, sizes, formats, transformations and digests. Decoded bytes and comparison images are regenerated into ignored `artifacts/` by the commands below.

ROM: PAL Unirally, SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e` (R-0001). File offsets follow the LoROM rule (`bank & 0x7F) << 15 | (address & 0x7FFF)`). Scenario: `race-crawler-dragster-3000` (R-0006/R-0007): 1P, MIKE, CRAWLER tour, DRAGSTER track; the race loads in frames 1208–1328 and runs from frame 1329.

## Stable identifiers

| Identifier | Meaning | How the original selects it |
| --- | --- | --- |
| `tour:CRAWLER`, `track:DRAGSTER` | the track of the scenario | the byte at `$77:074A` (cartridge RAM under the LoROM map, written by the menu) plus `$C2` indexes the asset directory at `$82:B332`; entry `0xC2` is the track asset |
| `asset:track-data` | the track's compressed data block | directory entry `0xC2`: bank `$18` with the compressed flag, address `$8000`, length 387 (file offset `0x0C0000`) |
| `tileset:1,2,20,36,22,24` | the six 16×16 tile sets the track uses | the list at the end of the decoded track data (offset `0x840F`, `$FF`-terminated), indexed into the tile directory at `$82:B7DD` |
| `rider:MIKE` | the rider frames streamed each frame | the per-frame sprite-tile DMA sequence at `$82:B907`–`$82:BDC0` |
| `segment:frames-1600-2400` | the tile-map region compared | the BG1 tile map columns uploaded up to frames 1600 and 2400 |

## Items, ROM offsets, formats and transformations

| Item id | ROM (file offset, length) | Format | Transformation | Destination in the original | Digest of the decoded bytes (SHA-256, prefix) |
| --- | --- | --- | --- | --- | --- |
| `track-data` | `0x0C0000`, 387 bytes packed (`$18:8000`); the decoder consumes `$18:8011`–`$18:8183` | RNC ProPack method 1 (`RNC\x01` header: unpacked 0x8417, packed 0x171, 4 chunks) | `$81:B8E2` decompressor, ported register for register (`tools/unirally_lab/content/rnc.py`) | `$7F:0000`–`$7F:8416` (33,815 bytes) via `$82:E12B` → `$82:B2DD` → `$82:B323`, frames 1232–1242 | `8f5cef67dc57977a` |
| `bg1-tileset` | 40 pieces of 64 bytes: `0x0B0080`, `0x0B00C0`, `0x0B0100`, `0x0B0140`, `0x0B5900`–`0x0B5AC0`, `0x0B7F80`, `0x0B7FC0`, `0x0B8000`–`0x0B83C0`, `0x0B5D00`–`0x0B5EC0`, `0x0B6100`, `0x0B6140` (tile sets at `$16:8080`, `$16:8100`, `$16:D900`, `$16:FF80`, `$16:DD00`, `$16:E100`; 128 bytes per 16×16 tile laid out as up to eight top rows then their bottom rows) | 4bpp planar 8×8 tiles | raw DMA (channel 0, mode 1) | VRAM words `$2000`–`$25E0` (BG1 name base `$2000`, BG12NBA `$12`); top rows at `$2000 + n·$20`, bottom rows at `+$100`; frame 1242 | `5a45c158da5565b8` |
| `bg3-font` | `0x05BCC0`, 2,048 bytes (directory entry `0x81`) | 2bpp tiles | raw copy through `$2118`/`$2119` by `$82:B1DB`/`$82:B296` | VRAM bytes `0x0000`–`0x07FF`, frame 1214 | `1a5b6538fa669bf9` |
| `bg2-tiles` | `0x058000`, 992 bytes (entry `0x70`) | 4bpp tiles | raw copy through the port | VRAM bytes `0x2000`–`0x23DF` (BG2 name base `$1000` words), frame 1219 | `d50aaa4efde3d4b5` |
| `bg2-tilemap` | `0x05C4C0`, 8,192 bytes | 64×64 tile map words | raw copy through the port | VRAM bytes `0xE000`–`0xFFFF` (BG2SC `$73`), frames 1214–1218 | `574a44e71c96b210` |
| `palette` | `0x07B760` +192 → colours 0–95 (entries `0xA4`–`0xA9`, CGADD `$00`–`$50`); `0x07B540` +32 → 112–127 (`$70`); `0x07B9A0` +32 → 128–143 (`$80`); `0x020180` +32 → 176–191 (`$B0`); `0x020380` +32 → 240–255 (`$F0`); `0x0203A0` +32 → 192–207 (`$C0`) | 15-bit BGR words | raw copy through `$2121`/`$2122` by `$82:B183`, frames 1219–1220 | CGRAM; colour 0 and colours 96–111 are rewritten every race frame by `$82:D38E`–`$82:D48A` | `d98f7dfd1f0cd056` |
| `tile-tables` | `0x0BA0A4` +32, `0x0BA0C4` +32, `0x0BB6C4` +128, `0x0BC384` +288, `0x0BB7C4` +128, `0x0BB8C4` +32 (pointer table at `$17:A000`, 4 bytes per tile-set id) | 2 bytes per 16×16-tile column | raw copy by `$82:E2CD`–`$82:E30C` | `$7E:A000`–`$7E:A27F`, frame 1242; read by `$81:8CDD`/`$81:8CBB` during riding | `bb95427aa2a307c9` |
| `tile-flags` | `0x0BC4E4` +1, `0x0BC4E5` +1, `0x0BC595` +4, `0x0BC5FB` +9, `0x0BC59D` +4, `0x0BC5A5` +1 (`$17:C4E4 + (table − $A0A4)/32`) | 1 byte per 16×16 tile | raw copy by `$82:E30E`–`$82:E346` | `$7E:C000`–`$7E:C013`, frame 1242; read by `$81:8C0C`/`$81:82D9` | `590e52f2640bb1b7` |
| `rider-tiles-1600` | 27 pieces of 32 bytes in banks `$27`–`$39` (listed in the manifest) | 4bpp 8×8 tiles | raw DMA, one per tile, frame 1600 | OBJ name base `$6000` words (OBSEL `$83`: 16×16/64×64 sprites), tiles `$02`–`$CC` | `09aace3bf5456501` |
| `rider-tiles-2400` | 21 pieces of 32 bytes | as above | raw DMA, frame 2400 | as above | `23118ba7bedbb293` |

Decoded lengths: 33,815; 2,560; 2,048; 992; 8,192; 352; 640; 20; 864; 672 bytes.

### The track data block

The decompressor at `$81:B8E2` is an RNC method-1 decoder: a 16-bit LSB-first bit window (`$8F`) with one word of look-ahead (`$91`/`$93`), three canonical prefix-code tables per chunk (raw-run counts at `$0220`, distances at `$02A0`, lengths at `$0320`; a 5-bit symbol count, 4-bit lengths, canonical codes stored bit-reversed with their masks), a 16-bit command count, then literal runs copied from the source pointer (the window is re-synchronised after a run) alternating with back-references (`distance + 1` back, `length + 2` bytes; distance 0 repeats the last byte). The header's unpacked/packed lengths and CRCs are not used by the ROM. The port keeps the routine's registers, its bank-wrap rule (`ORA #$8000; INC $84` on carry) and its table layout, so its arithmetic is the original's; the tables start zeroed, which only matters if a scan ever ran past the valid pairs (a complete prefix code never does).

Decoded layout as observed (not decoded further in M1-03): words at 0: `0000 0044 0032 0044 0032 840F 0004 …`; the tile-set id list at `0x840F` (`01 02 14 24 16 18 FF`); the tile map region `0x800F`–`0x83CD` read by the column builder `$81:B31C` (`LDA $7F000F,X`, X from `$0234 + $0559 + column·32`, stepping by `$0236`) and by `$81:8B66`; the regions `0x4031`–`0x7ACB` (`$81:AD95`) and `0x6031`–`0x72C7` (`$81:8AA1`–`$81:8AC0`) read by the riding code. The loader increments the word at `0x000B` as it walks the tile-set list (`0x840F` → `0x8416`), the only byte of the block that differs from the decoded data in the work RAM dump after frame 1243.

### How the segment reaches the PPU during the race

Every race frame (from 1334) the NMI code starts 26–28 DMA transfers on channel 0: one 32-byte sprite tile per DMA from ROM banks `$27`–`$39` to the OBJ name area (`$82:B907`–`$82:BDC0`, an unrolled sequence whose length varies with the rider frame), one 32-byte tile-map column from the staging buffer at `$00:0437` with VMAIN `$81` (16 entries down a column of the 32×32 BG1 map at word `$0C00`; consecutive frames fill consecutive columns, e.g. `$0D8E`…`$0D96` in frames 1590–1600), and during the first riding frames a 34-byte row from `$00:0459`. The staging buffers are filled by `$81:B3D3` from the decoded track data. OAM is DMA'd once at frames 1332–1333 from `$00:138B` (544 bytes); afterwards only sprites 96–99 (16 bytes at OAM word `$C0`) and one high-table byte are rewritten per frame through `$2104`. BG1 and BG2 scroll come from HDMA channels 4 and 3 (tables at `$7E:2046` and `$7E:2058`, one entry of 112 lines), BG1SC from channel 2 (`$7E:207F`), colour math and the GO-letter window from channels 5 and 6.

## Comparison with the original's rendering

`content decode` verifies every item's digest against the ROM and, with the whole-WRAM dump after frame 1243, compares `track-data`, `tile-tables` and `tile-flags` byte for byte with the work RAM the original filled: 33,814 of 33,815 bytes equal (the loader's cursor at `0x000B` is the exception), 640 of 640 and 20 of 20. The raw items copied through the ports equal the VRAM/CGRAM bytes reconstructed from the recorded port writes (the load-phase reconstruction in R-0008).

`content compare` rebuilds VRAM, CGRAM and OAM at a frame from the decoded items plus the access record (ROM→VRAM DMAs and the tile-map column DMAs replayed with the previous frame's staging buffer from the work RAM series; CGRAM and OAM port writes from the watch logs; scroll from the HDMA tables of the dump after the frame), renders BG2, BG1 and the sprites with the core's colour conversion (5-bit channel replicated to 8, gamma 1.5 on the lower half, as the libretro target's palette does) and compares pixel for pixel with the frame image:

| Frame | Rectangle (x, y, w, h) | Pixels | Mismatches | Explanation |
| --- | --- | --- | --- | --- |
| 1600 | 120, 28, 136, 196 (right of the GO letter, below the HUD) | 26,656 | 490 (1.84 %) | a four-line band below the ribbon (rows 154–157) where HDMA channel 5 applies colour math and a fixed colour (declared omission; located by review 1), the timer digits (BG3, not rendered) and the edge of the window-drawn letter G at the rectangle's left edge |
| 2400 | 0, 28, 256, 196 (all but the HUD rows) | 50,176 | 791 (1.58 %) | 512 pixels in a four-line band below the ribbon (rows 149–152) where HDMA channel 5 applies colour math and a fixed colour from the table at `$7E:2084` (declared omission; located by review 1), and the `RACE`/`+0:00:1` text (BG3, not rendered) |

Omitted by the renderer (declared in every report): windows and colour math, BG3, per-scanline HDMA register changes (the tables carry one entry, so scroll is constant within the frame), mosaic/interlace/offset-per-tile, sprite-per-line limits and finer priority rules. Two facts were calibrated against the frame image and are recorded in the code: a background row is `VOFS + y + 1` (the PPU's first visible line is line 1), and a tile-map DMA in frame N copies the staging buffer as the game loop left it at the end of frame N − 1.

## Regeneration

```
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-3000.json --out artifacts/access/race-ports \
  --watch-pc 0x000199 --watch-address 0x002116 --watch-address 0x822116 --watch-address 0x002115 --watch-address 0x822115 \
  --watch-address 0x002121 --watch-address 0x822121 --watch-address 0x002102 --watch-address 0x00210D --watch-address 0x00210E \
  --watch-address 0x00210F --watch-address 0x002110 --watch-address 0x002107 --watch-address 0x00212C \
  --wram-series-range 0x437 0x44 --wram-series-every 1 --frame-image 1600 --frame-image 2400
python3 tools/project.py content provenance --access artifacts/access/race-ports/access.json --out artifacts/content/provenance
python3 tools/project.py content decode --manifest tests/manifests/content/dragster-segment.json --out artifacts/content/decode [--wram-dump <dump after frame 1243>]
python3 tools/project.py content compare --manifest tests/manifests/content/dragster-segment.json --access artifacts/access/race-ports/access.json \
  --access <windowed record 1595-1605 with $2121/$2122/$2102/$2104 watched> --frame 1600 --frame-image artifacts/access/race-ports/frames/frame-01600.png \
  --oam-dump <dump after frame 1333> --scroll-dump <dump after frame 1600> --out artifacts/content/compare --rect 120 28 136 196
```

Work RAM dumps come from the worker directly (`--stop-after-frame N --wram-dump-out P`, as in the M1-02 lean experiment); the exact commands are in the M1-03 handoff.
