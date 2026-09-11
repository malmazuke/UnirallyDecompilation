# R-0010 — Native movement prerequisite investigation

- Status: in progress; no native gameplay agreement claimed.
- Task: [M2-01](../../tasks/M2-01.md), dispatched base `a9f86e590e4be0d76369a975ece2d556883aa51f`.
- ROM: PAL Unirally, SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`; unchanged bsnes commit `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`, Strict serialization.
- Domain: primary Crawler/DRAGSTER race; end-of-frame samples, first native update intended at 1534 from initial observation 1533. Reference baseline is unchanged. Native implementation has not begun.

## Coordinator-approved scope amendment (12 September 2026)

The required player speed depends on opponent-derived state. The coordinator
explicitly includes the minimum track-grid gather/progress transition and
opponent motion that causally feed player speed. Unrelated opponent features
remain excluded. Required player projections and frozen outputs stay unchanged;
no expected per-frame state or dynamic table read may drive a native update.
Investigate this prerequisite for at most 45 minutes before reassessment. A
substantial unresolved format may become a separate prerequisite with standalone
evidence, rather than a partial gameplay acceptance.

## Verified observations

1. The entry range in M1 mostly copies player state into shared scratch and back.
   Position is copied `$0415 → $A5` at `$82:8AB1–8AB4` and back at
   `$82:8DB7–8DB9`; speed `$04BB → $0FA9` at `$82:8B97–8B9A` and back at
   `$82:8E97–8E9A`. Actual arithmetic is in callees dispatched by
   `$82:8C3A–8C87`, not the final field stores.
2. **Opponent progress affects required player speed.** At primary frame 1632,
   `$82:A7BA` reads opponent counter `$0FCF=6`; `$82:A7BE` subtracts the player
   counter `$0FCD=5`. `$82:A7CE` writes player adjustment `$0343` from 1 to 2.
   The positive-speed clamp `$82:A7E3–A817` combines zero `$11D7` with that 2,
   halves it and adds `$11D3=448`, then writes 449 to `$0FA9`. Earlier in the
   frame `$82:A9EC` wrote 472 (448+24). The published speed is 449. At frame
   1631, the adjustment is 1 and the cap is 448. The first nonzero adjustment
   in the observed window is at 1587; its first effect on the required speed
   is at 1632. These are primary observations, not withheld-case results.
3. The counter dependency extends through track traversal: `$82:91DD` publishes
   the opponent `$0FCF` from scratch `$0FB9`; `$82:9805` increments `$0FB9`
   after comparing a transition encoded in bits 10–12 of `$0FB5` with the ROM
   transition table at `$80:84CB`. `$81:8BC6` fills `$0FB5` from sampled track
   words, which `$81:8B66` gathers from `$7F:800F,X` into `$0260,Y`.
   The exact spatial gather and opponent motion remain under investigation.
   This is a concrete dependency beyond a player-only isolated update.
4. **The pose/table concern is resolved for the sampling component.** The
   preliminary sprite-only interpretation was wrong: `$81:8DB6` calls
   `$81:9E1B` immediately before `$81:8DB9` calls the sampler `$81:8B75` (and
   the opponent follows the same pair at `$81:8F0A/8F0D`). The bank $21 records
   produce collision sample positions. An eight-byte record is indexed by
   the pose index `$0F85 * 8`; its first four bytes are two x/y pairs, bytes
   four/five are an origin, and its last word selects eight additional pairs
   in the byte template region starting `$20:BC9F`. Template byte offset is
   `u16(byteswap16(selector) << 4)`, **not just the high selector byte times
   16**. Each pair adds the origin modulo 256. When `$0F51 != 0`, every x
   becomes `u8(47-x)`, then every x gets `+8` modulo 256. The source operand
   offsets for 47 and 8 are `0x009F14` and `0x009F5D`.
5. **Spatial gather reconstructed.** `$81:8A2A–8B74`: x/y divided by 64 select
   four neighbouring coarse-map words at decoded offsets `0x000F +
   2*(row*width+column)`, next column, next row, and both. Each word indexes a
   32-byte block at decoded offset `0x800F`; the ten points choose a quadrant
   using the sign bit of 8-bit subtraction against `64-(coordinate&63)`.
   Fine-cell offset is `(((point.x+x)&0x30)/4 + ((point.y+y)&0x30))/2`, added
   to the block base. Intermediate word arithmetic wraps at 16 bits. Coarse
   width is `$04F5=1024`, stride `$04F7=2048` in every primary series record
   1533–2999. Negative-y and the last-column alternate branch are not covered.
6. **Native isolated sampler equals all observed words.**
   `src/core/track_sampling.cpp`, using static extracted content and captured
   incoming x/y, pose index and reflection flag, matches 29,320 words from
   2,932 original calls (both riders; primary frames 1534–2999). Incoming x/y
   are sampled at `$81:8D97/8D9C` for the player and `$81:8EF1/8EF6` for the
   opponent, before collision correction; end-of-frame y can differ and
   cannot substitute. Each call's ten outputs are captured at `$81:8B6A`,
   with Y counting 18,16,...,0. This proves an isolated dependency, not an
   autonomous native update. The first native implementation matched without
   changing any reference value. The first harness attempt rejected the
   capture's extra `frames.count` metadata before invoking native code;
   correcting that schema check yielded agreement.

## Reproduction and evidence

Baseline commands, all exit 0, under `artifacts/m2-01/baseline/`: `doctor`,
`bootstrap`, `build --preset lab-debug`, `test --suite synthetic` (196 checks),
`reference build`, and `replay compare --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json`.
The administrative checkpoint occurred during the long chained command: its
synthetic report records the source transition. No implementation or baseline
changed; a stable-source rerun is required before submission.

Reference freeze: three cases in `tests/manifests/native/`, each compared in two
fresh processes under `artifacts/m2-01/freeze/<case>/`; each reports all original
ranges, final state and A/V identical. Primary sample digest is
`72f618f2f7e3416eac64d38f882471b1a9ebee25018ed76143360a92cdd99b1f`.
Withheld series are sealed for implementation; only their identity and comparator
outcomes were inspected. Their compact projected series are generated by
`tools/unirally_lab/native/freeze_reference.py`, which computes no native field.
Regeneration instructions are in the native manifest README.

Capture 1, unchanged sample digest and final state, exit 0:

```sh
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json --out artifacts/m2-01/movement-access --from-frame 1533 --to-frame 1700 --watch-address 0x0000A5 --watch-address 0x000F5F --watch-address 0x000F73 --watch-address 0x000FA9 --watch-pc 0x819E42 --watch-pc 0x819E54 --watch-pc 0x83F2F1 --watch-pc 0x83F2FB --wram-series-range 0 0x2200 --timeout 120 --report artifacts/m2-01/movement-access/report.json
```

Access SHA-256 `8027f268b22e5b1d…`; 3,061,594 instructions, 1,523,897
accesses over frames 1533–1700; 3,847 unresolved accesses, zero unresolved
stores. Series SHA-256 `b54da2c8bd5d6cdd561752d669c8d04be898b2f711d715a75719407f044d9a51`,
3,000 records of 0x2200 bytes, offset 0, no header. Read each record's words
little-endian. This series contains primary state only.

Capture 2 isolates the speed dependency (unchanged sample digest, exit 0):

```sh
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json --out artifacts/m2-01/speed-dependency --from-frame 1580 --to-frame 1642 --watch-address 0x000FCD --watch-address 0x000FCF --watch-address 0x000FB5 --watch-address 0x000FB7 --watch-address 0x000FB9 --watch-address 0x000343 --watch-address 0x000FA9 --watch-address 0x0011D3 --watch-address 0x0011D7 --watch-address 0x0011F1 --watch-pc 0x82A7BA --watch-pc 0x82A7BE --watch-pc 0x82A7F8 --watch-pc 0x82A817 --watch-pc 0x829805 --timeout 120 --report artifacts/m2-01/speed-dependency/report.json
```

Frame 1632 sequence numbers: opponent-progress read 1457; player-progress
subtraction 1459; adjustment store 1466; speed-clamp store 1484; speed loaded
for position integration 1526; speed publication load 2147. The same capture
shows the prior frame and first adjustment at 1587. Watch values on arithmetic
reads may be null by the existing access contract; the loaded register and
prior stores resolve the expression, without treating null as a value.

Local-only disassembly was read from ROM and retained under
`artifacts/m2-01/`. To recover observed modes and offsets:

```sh
python3 tools/project.py coverage capture --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json --out artifacts/m2-01/coverage --timeout 120 --report artifacts/m2-01/coverage/report.json
python3 tools/project.py coverage map --coverage artifacts/m2-01/coverage/coverage.json --out artifacts/m2-01/coverage/map.json --detail artifacts/m2-01/coverage/detail.json --report artifacts/m2-01/coverage/map-report.json
```

Both exit 0; 49,465,866 instructions; the sample digest is unchanged. No ROM
bytes, full disassembly, extracted content or emulator states are tracked.

## Not established

No native simulation, comparison, serialization, sanitizer result or native
withheld-case agreement exists yet. The exact full riding dependency closure,
track-grid gather and opponent input/motion are not yet recovered. The five
timer digits and input axes have not yet been implemented. Frozen values are
observations and do not satisfy gameplay acceptance by themselves.

## Sampling checkpoint

Native source is readable C++20 with explicit byte/word wrapping and checked
content bounds. Static content manifest `tests/manifests/native/movement-sampling.content.json`
extracts the existing track data plus bank $21's first 32 KiB (ROM offset
`0x108000`) and the available template-region tail from `$20:BC9F` through
`$20:FFFF` (ROM `0x103C9F`, 17,249 bytes). Extracting the available tail is a
bounds choice, not a claim that every byte is one template. Observed primary
selectors include offsets 0,16,8560,8576,8592,8608,9632,9680; a first proposed
4 KiB extent was insufficient and was expanded **before the probe**. Pose
indices fit the extracted bank in this domain. The identity-checked content
stays ignored; authored tests contain no original tables.

```sh
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json --out artifacts/m2-01/sampling-access --from-frame 1534 --to-frame 2999 --watch-address 0x0000A5 --watch-address 0x0000A7 --watch-address 0x000F85 --watch-address 0x000F51 --watch-pc 0x818B6A --watch-pc 0x819E1D --watch-pc 0x818A2A --timeout 180 --report artifacts/m2-01/sampling-access/report.json
python3 tools/project.py content decode --manifest tests/manifests/native/movement-sampling.content.json --out artifacts/m2-01/content-expanded
python3 -m tools.unirally_lab.native.probe_sampling --access artifacts/m2-01/sampling-access/access.json --content-manifest tests/manifests/native/movement-sampling.content.json --content artifacts/m2-01/content-expanded --probe build/lab-debug/tests/native/sampling_probe --coarse-width 1024 --report artifacts/m2-01/sampling-probe-3.json
```

All exit 0. Capture access SHA-256 `bebe75c349332a55…`, 27,090,754 instructions,
13,466,478 accesses, 28,223 unresolved accesses and zero unresolved stores;
original sample digest unchanged. Native pose/grid/bounds C++ tests 3/3 and
reference-freeze/capture-input Python tests 7/7 pass. These are not the full
M2-01 native movement acceptance tests. Full suite and sanitizers pending this
checkpoint; withheld native tests remain unrun.

Independent coordinator evidence: separately reproduced the speed chain at
1631/1632 (`artifacts/m2-01-coordinator/speed-dependency/access.json` in root,
SHA-256 `3e362d4b48180cb0f3f12d684b86c8d4d9e6f336509ab12aac20d4a224d5474d`).
It also independently projected all 1,467 primary rows from both its pre-freeze
captures, matching the primary expected-file SHA-256
`5b6b2f6f2d513d1ef2b230f21b0774229bdbc6a207ff4a530245e8c7051fb640` without
using the freeze utility. No withheld output was inspected in either check.
