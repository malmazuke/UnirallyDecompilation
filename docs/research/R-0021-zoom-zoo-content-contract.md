# R-0021 — ZOOM ZOO decoded content and read-boundary contract

- Task: [M4-03](../../tasks/M4-03.md)
- Status: accepted; integrated as `0856621` after a returned independent review
  and approved focused re-review
- Evidence date: 13 September 2026
- Source base: `9dacdf800325947e9141887934282a494910710d`
- ROM: supported headerless PAL image, SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
- Core: bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`,
  `Strict` serialization, PAL
- Domain: the accepted cold-start 1P MIKE/CRAWLER/ZOOM ZOO 3,300-frame
  replay. Right is held from 1650; Up is also held on 2200--2259. Controller 2
  is silent. No native ZOOM ZOO execution is claimed.

## Method and identities

The accepted `0xC3` content object was decoded twice before interpretation.
Both 50,665-byte results have SHA-256
`db6770152e399f9d16fc6937b5d56588a8f67e825ae70d6578b77d36053fdd28`;
both `decode.json` projections have SHA-256
`bb15b647290826f28cd9e4ee75ac15e318623bef1e0ba04f69006f410b2c395b`.
The RNC header remains method 1, 6,581 packed bytes, 50,665 unpacked bytes,
five chunks and two leeway bytes. The consumed source ends at `$18:9B4A`.

Five fresh targeted captures are complete, have no PC-log truncation, have
maximum per-frame instruction counts below the 262,144-entry ring and retain
the accepted sample/final-state identities. Ignored access-record hashes:

| Window | Access SHA-256 | Purpose |
| --- | --- | --- |
| 1286--1291 | `bc733d1c39bda5076f4548897510aa1b9f09bce4baa139e0ad9f0435b94cd56c` | loader cursor, directories and 406 DMA triggers |
| 1376--1384 | `36aeac919fa7f48bccf31fba35d064a0c550096829a96e203bd9244a03fe4b78` | first rolling gather and staging/upload ordering |
| 1699--1701 | `02f497194d481e370ce07935e825edd3a664dc6463ae691567437cc178628285` | preregistered Right-only gather/collision sample |
| 2219--2221 | `fa3e5e2d4352e79391461a09b9219127b133d5c592d6c24f0ff22f82ad794b3a` | preregistered Right+Up collision sample |
| 2220--2280 | `ecb45a173dafca37d56258162082ec2c3216fad81c79051d243cd4d6c47e71d9` | first subsequent builder, frame 2224 |

The tracked contract is
`tests/manifests/content/zoom-zoo-reference-contract.json`. Its validator reads
the exact-gated ROM, independently decodes the object and derives selected
payloads and addresses; it never uses captured staging or upload bytes as
reconstruction input.

## Verified observations

### Decoded layout and loader mutation

The first 15 decoded bytes are a header consumed by the established loader and
sampling family. `$82:E1A1` reads its word at offset `0x000B` as `0xC5CF`.
Each execution of `$82:E1A7` stores the incremented cursor. There are exactly
25 executions on frames 1287--1290: `$82:E1AD` consumes the 24 bytes at
`0xC5CF..0xC5E6`, then consumes `0xFF` at `0xC5E7`. By end of frame 1291 the
runtime image differs from the immutable decode at one byte only: decoded
offset `0x000B` advances from `0xCF` to `0xE8`. The second `0xFF` at decoded
offset `0xC5E8` is not consumed and remains explicitly opaque.

The bounded region identities are:

| Region | Decoded bounds | SHA-256 | Observed consumers |
| --- | --- | --- | --- |
| header | `0x0000+0x000F` | `751000f1becd23f7...` | cursor setup and sampler width/stride setup |
| coarse words | `0x000F+0x8000` | `ae19151909104ee2...` | `$81:8AA1/$81:8AC0` |
| bounded consumer data | `0x800F+0x45C0` | `e1b8b6a90c9e966...` | `$81:8B66` and `$81:B3CF` in the sampled domain |
| ordered tile list | `0xC5CF+0x0019` | `4e6dd9088b4bbd85...` | `$82:E1AD` including its terminator |

These names describe observed access boundaries, not a general file format.
In particular, bytes not reached by the declared gather/collision samples have
not individually acquired meanings merely because they lie within a hashed
region.

### Ordered tile-set and table load

The selected ids, including repeated id 13, are:

`01 02 03 04 05 06 07 08 09 0A 0B 12 1E 0D 0F 0E 10 16 18 14 0D 24 1D 11`

Each id resolves a five-byte directory entry based at `$82:B7DD`, and its
table pointer resolves through `$17:A000 + 4*id`. The runtime copies
`tile_bytes / 4` bytes into `$7E:A000` in selection order; its flag source is
`$17:C4E4 + (table_address - $A0A4)/32`, with `tile_bytes / 128` bytes copied
into `$7E:C000`. The ordered concatenations are:

- tile payload: 25,984 bytes, SHA-256 `cb9e05e0d2dde093...`;
- per-tile table payload: 6,496 bytes, SHA-256 `649b96ff43ef467f...`;
- flag payload: 203 bytes, SHA-256 `11aa211a148bced1...`.

The 203 directory-derived tiles account for all 406 64-byte transfers. Within
each group of at most eight 16-by-16 tiles, top halves precede bottom halves in
the source layout; runtime transfers each top then bottom. Destination tile
numbering advances in eight-tile rows from VRAM word `$2000`, with bottom
halves at `+0x0100`. LoROM source crossing `$16:FFFF` continues at `$17:8000`.
Canonical ordered rows `source-bus:destination-word:64` hash to
`6d28534ed765be8532d1181f560c877f519c14bd2d6b1305798e1b249662cc0e`,
exactly the 406 observed transfer rows after carrying the two VMADD values set
in the preceding frame. The source envelopes alone were not used as evidence.

### Rolling gather

`$81:B270` derives row/column work and `$81:B366` receives explicit source X,
count and step inputs. `$81:B3CF` loads 16-bit words from `$7F:000F+X`;
`$81:B3D3` stores them successively into the staging range. Replaying only
these address calculations against the immutable decoded object gives:

| Declared condition | Builder | Destination | Compared bytes | SHA-256 |
| --- | ---: | --- | ---: | --- |
| Right-only frame 1700 | 1700 | `$0437-$0478` | 66 | `aa95348d6c11d421...` |
| Right+Up frame 2220 | next observed builder, 2224 | `$0437-$0456` | 32 | `6094b3066c8bf444...` |

The first gather window also confirms the previously established ordering:
the DMA beginning frame N uploads the staging completed at end of frame N-1.
The preregistered frame 2220 has no builder execution, so the recorded rule
selects the first later builder (2224); no convenient substitute was silently
made.

### Collision/read boundary

The incoming positions are the Y register stored at `$81:8D97/$81:8D9C` for
the player and `$81:8EF1/$81:8EF6` for the opponent, before correction. Pose
and reflection inputs are the ordered writes at `$81:8D15/$81:8D0F` and
`$81:8E6F/$81:8E69`. The accepted pose/template payload identities are reused
only to derive the ten incoming point offsets; no DRAGSTER track values are
reused.

The observed ZOOM ZOO width is 256 coarse cells and its byte stride is 512,
not DRAGSTER's 1024/2048. The established arithmetic (64-position-unit coarse
cells, 32-byte fine blocks, 16-bit wrapping, four-neighbour selection and
wrapped sign-bit quadrant tests) reproduces all ten `$81:8B66` words for both
riders at frames 1700 and 2220: 40/40 exact. `$81:8CBB/$81:8CDD` then read the
ordered per-tile byte tables at `$7E:A000+X`; their branch meanings remain
provisional. The contract freezes widths, derived decoded addresses and values,
not labels such as height, wall, floor or surface type.

## Hypotheses and limits

- Family resemblance to DRAGSTER is useful at the instruction level, but two
  tracks do not establish a general decoder. The differing 256/512 width and
  stride directly reject blind reuse of DRAGSTER's 1024/2048 values.
- The decoded consumer-data region may contain several logical structures.
  Its subdivision beyond the observed bases and accesses is unknown.
- Returned collision words and `$7E:A000` bytes remain opaque values. Edge,
  negative-Y and other unsampled branches are not covered.
- The evidence does not cover contact response, AI, camera, finish, result,
  presentation, other SRAM histories or native execution.

## Reproduction

From this checkout with the supported private ROM and pinned core available:

```sh
python3 tools/project.py rom inspect --expect tests/manifests/rom/unirally-pal.json --report artifacts/m4-03-rom-inspect.json
python3 tools/project.py content decode --manifest tests/manifests/content/zoom-zoo-reference-inventory.json --out artifacts/m4-03/decode-1 --report artifacts/m4-03/decode-1-report.json
python3 tools/project.py content decode --manifest tests/manifests/content/zoom-zoo-reference-inventory.json --out artifacts/m4-03/decode-2 --report artifacts/m4-03/decode-2-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03/load-1286-1291 --from-frame 1286 --to-frame 1291 --watch-address 0x002115 --watch-address 0x002116 --watch-address 0x002117 --watch-address 0x002118 --watch-address 0x002119 --watch-address 0x00420B --watch-address 0x00420C --watch-address 0x7F0000 --watch-address 0x7F000B --watch-pc 0x82E1A7 --watch-pc 0x82E2CD --watch-pc 0x82E2D8 --watch-pc 0x82E2F5 --watch-pc 0x82E31A --watch-pc 0x82E346 --watch-pc 0x82B7DD --wram-series-range 0x10000 0xC5E9 --timeout 240 --report artifacts/m4-03/load-1286-1291-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03/gather-1376-1384 --from-frame 1376 --to-frame 1384 --watch-address 0x00234 --watch-address 0x00236 --watch-address 0x00559 --watch-address 0x00437 --watch-address 0x00458 --watch-address 0x00459 --watch-address 0x00478 --watch-address 0x002115 --watch-address 0x002116 --watch-address 0x002117 --watch-address 0x002118 --watch-address 0x002119 --watch-address 0x00420B --watch-pc 0x81B270 --watch-pc 0x81B31C --watch-pc 0x81B366 --watch-pc 0x81B3CF --watch-pc 0x81B3D3 --wram-series-range 0 0x20000 --timeout 240 --report artifacts/m4-03/gather-1376-1384-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03/sample-1700 --from-frame 1699 --to-frame 1701 --watch-address 0x0000A5 --watch-address 0x0000A7 --watch-address 0x000F85 --watch-address 0x000F51 --watch-address 0x000234 --watch-address 0x000236 --watch-address 0x000559 --watch-address 0x000437 --watch-address 0x000458 --watch-address 0x000459 --watch-address 0x000478 --watch-pc 0x81B270 --watch-pc 0x81B31C --watch-pc 0x81B366 --watch-pc 0x81B3CF --watch-pc 0x81B3D3 --watch-pc 0x818D97 --watch-pc 0x818D9C --watch-pc 0x818EF1 --watch-pc 0x818EF6 --watch-pc 0x818AA1 --watch-pc 0x818AC0 --watch-pc 0x818B66 --watch-pc 0x818B6A --watch-pc 0x818CBB --watch-pc 0x818CDD --wram-series-range 0 0x20000 --timeout 240 --report artifacts/m4-03/sample-1700-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03/sample-2220 --from-frame 2219 --to-frame 2221 --watch-address 0x0000A5 --watch-address 0x0000A7 --watch-address 0x000F85 --watch-address 0x000F51 --watch-address 0x000234 --watch-address 0x000236 --watch-address 0x000559 --watch-address 0x000437 --watch-address 0x000458 --watch-address 0x000459 --watch-address 0x000478 --watch-pc 0x81B270 --watch-pc 0x81B31C --watch-pc 0x81B366 --watch-pc 0x81B3CF --watch-pc 0x81B3D3 --watch-pc 0x818D97 --watch-pc 0x818D9C --watch-pc 0x818EF1 --watch-pc 0x818EF6 --watch-pc 0x818AA1 --watch-pc 0x818AC0 --watch-pc 0x818B66 --watch-pc 0x818B6A --watch-pc 0x818CBB --watch-pc 0x818CDD --wram-series-range 0 0x20000 --timeout 240 --report artifacts/m4-03/sample-2220-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-03/next-builder-2220 --from-frame 2220 --to-frame 2280 --watch-pc 0x81B270 --watch-pc 0x81B31C --watch-pc 0x81B366 --watch-pc 0x81B3CF --watch-pc 0x81B3D3 --timeout 240 --report artifacts/m4-03/next-builder-2220-report.json
python3 tools/project.py content zoom-zoo-contract --contract tests/manifests/content/zoom-zoo-reference-contract.json --report artifacts/m4-03/contract-report.json
python3 -m unittest tests.tooling.test_zoom_zoo_contract -v
```

These are the exact successful worker invocations, including fresh output and
report paths. They use only the watches required by the Astra checkpoint, plus
a bounded work-RAM series for end-of-frame staging comparison. Original ROM,
decoded bytes, series, access records and provenance rows remain ignored.
