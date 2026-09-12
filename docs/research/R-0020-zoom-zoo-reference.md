# R-0020 — ZOOM ZOO reference discovery and coverage delta

- Task: [M4-02](../../tasks/M4-02.md)
- Evidence date: 13 September 2026
- Base: task evidence base `2b40aea`; claimed branch head `1c8657e`
- ROM: supported headerless 2 MiB PAL image, SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
- Core: bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`,
  `Strict` serialization, PAL
- Tested domain: one cold-start `1P` path selecting MIKE, CRAWLER and ZOOM
  ZOO, then `Race`; 3,300 PAL frames, controller 1 only, controller 2 silent.
  It does not establish native support, completion/result behavior, a general
  track schema, other initial SRAM histories, other riders/opponents/events,
  or a track-only cause for every coverage difference.

## Method and frozen inputs

The accepted DRAGSTER navigation prefix remains unchanged through selection of
CRAWLER. The new input is one Down press at frames 1000-1005, released before
Start at 1050-1055. Start at 1200-1205 selects `Race`. Right is withheld until
frame 1650 and held through 3299; the existing Up window remains 2200-2259.
The tracked replay and equivalent low-level reference script are:

- `tests/manifests/replay/race-crawler-zoom-zoo-3300.json`
- `tests/manifests/reference/race-crawler-zoom-zoo-3300.json`

Every reference worker created a private empty system directory. The accepted
runs begin with WRAM SHA-256 `fa43239bcee7b97c...`, cartridge-RAM SHA-256
`7d2c7ac4888bfd75...`, and no save file present. Generated SRAM, samples,
frames, traces, decoded bytes and PPU images remain ignored.

Before executing the perturbation, M4-02 recorded this prediction: release
Right on frames 2500-2599 and resume it at 2600; expect identity through frame
2499, input-image and throttle divergence at 2500, then a speed or position
response at or after that boundary. The frozen variant is
`race-crawler-zoom-zoo-3300-release-2500-2599.json`. The adjacent boundary is
withheld for review.

## Observations

### 1. Navigation and coupling gate

Fresh frame images show the selector on DRAGSTER at 999, moving during the Down
window and stably on ZOOM ZOO after release. The complete `NOW PLAYING` screen
shows `MIKE vs BRONSEN`, `OVER 3 LAPS ON ZOOM ZOO`, `RACE` and `EXIT`.
Consequently, in this clean-SRAM path the displayed player count, rider, tour,
opponent and three-lap Race event stay the same as the accepted DRAGSTER path.
This is an observation of displayed and executed coupling, not a claim that the
game has independent track/opponent/event variables in general.

The first discovery attempt delayed both subsequent Start windows by 50 frames.
It completed with sample digest `81cd821a0c65745e...` but correctly failed the
copied DRAGSTER expectations. That useful failure established that ZOOM ZOO was
reachable and preserved its frame hashes; it was not used as the frozen replay.

### 2. Independently observed timing

On the frozen schedule the screen is fully black from frame 1207 through 1377;
the first visible race frame sampled here is 1400. Instruction coverage records
no native NMI in frames 1208-1376 and exactly one per frame from 1377 onward.
The primary position, displacement, throttle and speed writers first execute at
1377. The timer frame-counter writer begins at 1583, then advances once per PAL
frame and carries every five frames in the observed window. Frames 1583-3299
therefore provide 1,717 timer-active riding frames within 3,300 total frames.

Right is first presented at 1650. In that same frame `$7E:0313` changes to
`0x01`, `$7E:0BEB` changes from 0 to 16 and `$7E:04BB` changes from 0 to 24;
the primary position writer remains ordered in the same update. The input was
therefore consumed during confirmed riding rather than placed by analogy with
DRAGSTER's earlier load/countdown.

### 3. Deterministic freeze and perturbation

`replay compare --runs 2` used worker PIDs 47542 and 47604 and passed all
required checks: 3,300 common frames, exact `wram_sha256`, registers and
`wram_0000_0200`, final state and aggregate video/audio identity. Both sample
digests are `791a786370913136e21ed34c841e9a3d892852bf6804e2e0aef21e1df6557b68`;
the final state is
`2a843314d19e60d13dab746541d43ffa9ad84adfe6f95b9cc6d3c45bd9a16aeb`;
the A/V digest is
`dc7ca8ff6db1c2bbef17efd639c74f0d238a93f920e3b8f72b1c5ad80b1be22a`.
The compare report SHA-256 is `28a9417d93835cb7...`.

The predeclared release comparison fails identity as expected, with exact
agreement through 2499 and first divergence at 2500. Fresh localization finds
18 differing WRAM bytes, including `$7E:0313`, `$7E:0415`, `$7E:04BB` and
`$7E:0BEB`, plus two registers. The variant's sample digest is
`c253de4bce372be26b0457fa870b72c7a1acddb953a3ecf9ee187006ad55d63e`
and final state is
`00bf36ed74988b785f96c9e21116b2920915d85a81896b275255961d0330127d`.
The compare and divergence-report hashes are `3ef4711190e1706...` and
`877d113a46bfb5d...`. This proves delivered input and subsequent state response;
the differing set is not itself a semantic definition of every byte.

### 4. Reproducible coverage and bounded delta

Two fresh complete captures are byte-identical, coverage SHA-256
`476de96fa13b2cff31166037d654c5724634d280de0945ae4baf10e1d9ccd41d`.
Each records 54,677,608 instructions, a maximum 19,399 in one frame, 17,194
sites and 18,718 pairs without ring overflow. The tracked [map](../map/race-crawler-zoom-zoo-3300.map.json)
and [summary](../map/race-crawler-zoom-zoo-3300.md) regenerate byte-identically
from either capture (map SHA-256 `b1e17356f656be5d...`).

Against `race-crawler-dragster-3000` (`a075220e58ecd355...`), the ZOOM ZOO run
executes 4,014 bytes not in the baseline, omits 1,185 baseline bytes and shares
33,715 bytes. It has 268 entry points not in the baseline and omits 45 baseline
entry points. The map reports 15,951 opcode bytes plus 21,778 operand bytes,
1.799% of the ROM. All ten unknown edges originate outside ROM.

This is a scenario delta, not a pure track-causal delta: ZOOM ZOO changes the
menu input, load duration, movement start, riding path and total duration (3,300
versus 3,000 frames). A matched-duration DRAGSTER control would be required
before attributing each new/lost range to track identity alone.

### 5. Access safety and learned-state coupling

The accepted targeted record covers frames 1150-1750: 10,270,015 instructions,
5,000,173 derived accesses, 25,650 unresolved accesses, no unresolved stores,
no resolution conflicts and no PCs outside ROM. Its SHA-256 is
`25c47f266e393ad7071727e88475cf890974ce35b0750969c86ee07fcb51f85f`.

Reused state is classified only in this window:

| Classification | Observation |
| --- | --- |
| Supported address/writer/cadence | Player/opponent positions use the established primary writers `$82:8DB9` / `$82:92A7`; player displacement `$82:8DF8`, throttle `$82:8DBF` and speed `$82:8E9A` each write once per update for all 374 frames 1377-1750. The timer uses `$81:C6C9` / `$81:C6ED` from 1583 at five PAL frames per tenth. |
| Supported input delivery | `$80:87EC` / `$80:87F2` store the joypad images once per NMI frame from 1382; `$82:AB36` writes neutral vertical axis and `$82:AB52` / `$82:AB59` select horizontal values on the observed path. |
| Provisional meaning | Position, displacement, throttle, speed, axes and timer retain their established widths and writers, but numeric ranges and relationships beyond the captured windows are ZOOM ZOO-specific until separately checked. In particular the opponent moves in the opposite coordinate direction before player acceleration. |
| Unsafe to reuse | The DRAGSTER camera-offset relation, jump-height interpretation, collision-table value set, finish boundaries and pose/result meanings were not tested here. They are excluded from the frozen manifest's semantic fields. |

The clean initial `$77:0825` word is zeroed during load at frame 1291, read on
frames 1628-1634 and changed from 0 to 4 by the established reward path at frame
1672. This is consistent with the accepted bounded learned-feature behavior for
the same BRONSEN path, shifted with the new load/race timing. It does not prove
unchanged AI for other initial SRAM, opponents or later track regions.

### 6. Track/content seam and PPU provenance

At frame 1220 `$82:E12B` begins the same loader family. At frame 1232
`$82:B2DD` is entered with A=`0xC3`, selecting the next asset after DRAGSTER's
`0xC2`; `$81:B8E2` receives the source address `$18:8183` and destination bank
`$7F`. The source is a 6,599-byte RNC method-1 object (header plus 6,581 packed
bytes), ROM file offset `0x0C0183`, SHA-256 `3a8b470c673d0db3...`. It decodes to
50,665 bytes, SHA-256
`db6770152e399f9d16fc6937b5d56588a8f67e825ae70d6578b77d36053fdd28`.
The tracked reference-only content manifest reproduces this identity without
adding it to the Classic pack.

The decoded tail drives 25 executions of the tile-set cursor during frames
1287-1290. The resulting load performs 406 64-byte ROM-to-VRAM transfers
(25,984 bytes), sourced across ROM file offsets `0x0B0080`-`0x0B83FF` and
targeting observed VRAM words `0x2020`-`0x5340`. This contrasts with the 40
64-byte transfers in the DRAGSTER load and accounts for a concrete new load
seam; it does not yet decode the tile-map gather or assign geometry meanings.

The load-window provenance report reconciles all 10,664 MDMAEN stores in the
1150-1750 access record and lists 1,697 transfers for frames 1200-1426:
66,464 ROM-to-VRAM bytes, 532 WRAM-to-VRAM bytes and 5,440 WRAM-to-OAM bytes.
Two early OAM destinations are unpaired because the known `$80:2102` mirror was
not watched; this is recorded as an optional failure, not a pass. The load port
images have SHA-256 `970b3988be3e31f...` (VRAM) and
`c47e9fe5e16c7936...` (CGRAM).

For frames 1645-1700, 1,523 transfers are all paired: 46,304 ROM-to-VRAM bytes
in 1,447 transfers and 2,058 WRAM-to-VRAM bytes in 76 transfers. Their source
envelopes are ROM bus `$27:8000`-`$34:E2BF` (file offsets `0x138000`-`0x1A62BF`)
and WRAM `$00:0437`-`$00:0478`. Riding port-image hashes are
`691c3d755f993fda...` (VRAM) and `618765681108d4cc...` (CGRAM). Envelopes are
not claims that every intervening byte was read; exact transfer rows remain in
the ignored provenance record.

## Interpretation and limits

ZOOM ZOO is no longer label-only: it has an identity-bound, deterministic,
controller-2-silent reference path with observed opponent/event coupling,
timing, input response, coverage and content provenance. The evidence supports
a future prerequisite to decode the larger `0xC3` block and its tile-set list
before native work. It does not justify reusing DRAGSTER collision, camera,
finish or presentation contracts, and M4-02 deliberately changes no native
source or Classic-pack identity.

The access capture is a 601-frame targeted window, not a whole-run access map.
The coverage delta includes different duration/input/load confounders. Aggregate
A/V identity establishes deterministic output from this core/configuration, not
audio reconstruction. Execution remains local macOS reference evidence; CI is
ROM-free.

## Reproduction

From a checkout with the supported local ROM and pinned core:

```sh
python3 tools/project.py replay validate --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --runs 2 --artifacts artifacts/m4-02/freeze-two-runs/runs
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --against tests/manifests/replay/race-crawler-zoom-zoo-3300-release-2500-2599.json --artifacts artifacts/m4-02/perturb-compare/runs
python3 tools/project.py coverage capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-02/coverage/capture-1
python3 tools/project.py coverage map --coverage artifacts/m4-02/coverage/capture-1/coverage.json --out docs/map/race-crawler-zoom-zoo-3300.map.json --summary docs/map/race-crawler-zoom-zoo-3300.md --detail artifacts/m4-02/coverage/capture-1/detail.json --baseline docs/map/race-crawler-dragster-3000.map.json --scenario race-crawler-zoom-zoo-3300
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/access/race-crawler-zoom-zoo-3300 --from-frame 1150 --to-frame 1750 --watch-address 0x002115 --watch-address 0x002116 --watch-address 0x002117 --watch-address 0x002118 --watch-address 0x002119 --watch-address 0x002121 --watch-address 0x002122 --watch-address 0x002102 --watch-address 0x002103 --watch-address 0x002104 --watch-address 0x00420B --watch-address 0x00420C --watch-address 0x770825 --watch-address 0x7E0415 --watch-address 0x7E04BB --watch-address 0x7E0BEB --watch-address 0x7E0E19 --watch-address 0x7E0E1D --watch-address 0x7E0E21 --watch-address 0x7E0E25 --watch-address 0x7E0E29 --watch-pc 0x82B2DD --watch-pc 0x81B8E2 --watch-pc 0x82E12B --watch-pc 0x82E1A7 --watch-pc 0x828DB9 --watch-pc 0x828E9A --watch-pc 0x82AAA4 --watch-pc 0x82AADF --watch-pc 0x81C6C9 --watch-pc 0x81C6ED
python3 tools/project.py content provenance --access artifacts/m4-02/access/load-riding/access.json --out artifacts/m4-02/provenance/load --from-frame 1200 --to-frame 1426 --task M4-02 --report artifacts/m4-02/provenance/load-report.json
python3 tools/project.py content provenance --access artifacts/m4-02/access/load-riding/access.json --out artifacts/m4-02/provenance/riding --from-frame 1645 --to-frame 1700 --task M4-02 --report artifacts/m4-02/provenance/riding-report.json
python3 tools/project.py content decode --manifest tests/manifests/content/zoom-zoo-reference-inventory.json --out artifacts/m4-02/content/decode-tracked
```

The access line above is the exact canonical `regeneration_command` recovered
from the ignored accepted record. It includes every watched port, field and PC;
because it has no explicit `--ring`, it uses the recorded default ring of
262,144 entries. A fresh execution regenerated access SHA-256
`25c47f266e393ad7071727e88475cf890974ce35b0750969c86ee07fcb51f85f`.
The following two provenance lines are the exact successful worker invocations,
including their access path, output path, frame bounds, task and report values;
they regenerated provenance SHA-256 values `f968585d7736986b...` and
`ad78116903821d9f...`. Independent focused re-review should verify these
commands and the record-only diff; the first review already exercised the
adjacent withheld boundary and reproduced the other candidate claims.
