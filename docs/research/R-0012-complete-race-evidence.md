# R-0012 — Complete-race reference evidence and playable-slice inventory

- Task: [M3-00](../../tasks/M3-00.md)
- Status: candidate for fresh independent review
- Input freeze: commit `135ae38`; continuous manifest SHA-256
  `d03102fc33c22738466bfc9ae81fb55107ced9d693904ebd3132fa1f76afced2`;
  release-3000–3299 manifest SHA-256
  `8f449cd1a59a50904a9d208176a1bb015ebcd4ad128978942e8294d72f294cd1`
- ROM: PAL Unirally SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
- Core: bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`

## Experiment and result

Both 12,000-frame controller streams were committed before either ran. They
preserve the accepted menu/riding stream through frame 2999. Continuous holds
Right through 11999. The variation releases Right for 3000–3299 and resumes at
3300. The preregistered prediction was agreement through 2999, first controller
difference at 3000, later speed/progress divergence, and no earlier variation
finish.

Two fresh continuous processes matched every declared field and A/V on all
12,000 frames. Sample digest is
`22e9babdcb867936245e7c4a52fdf53a1bf8dc9433e91b77066818a4fc3484d6`;
final serialized state is
`6606f9411e05d00feab16b57183b8133de322e4e324c28f7aac710a345bb9ba0`.
The variation sample/final digests are
`d24a12347bcda3352244ecdb1d5e1ffc88985827a7725ac00da5a9f8ec866c74`
and `628878bd41e4edecf2ca3efd5b8cedb7b3144385f1edb726c0f198727c4e5dcd`.
The cross-manifest comparison returned the expected failure verdict: first
difference at frame 3000 in WRAM digest, registers, controller image, horizontal
axis, throttle and speed; localization found six WRAM bytes, beginning
`$7E0313`. This is evidence of the intended perturbation, not a failed
repeatability check.

| Observation | Continuous | Release variation | Difference |
| --- | ---: | ---: | ---: |
| Opponent finish flag set | 3214 | 3214 | 0 |
| Player finish flag set | 3213 | 3318 | +105 |
| First player-finish delay update / forced neutral axes | 3214 | 3319 | +105 |
| Delay reaches 240; last visible finish frame | 3453 (`WINNER`) | 3558 (`LOSER`) | +105 |
| First black result-load frame | 3454 | 3559 | +105 |
| Captured complete screen | 3679 | 3800 | — |
| Result-screen player time | `0:33.57` | `0:35.66` | +2.09 s displayed |

Thus both finish well inside the bound, and the variation is later, as
predicted. The exact fields, writer PCs, instances and subframe order are frozen
in [the finish-state record](../state/race-finish.md) and machine-checked by
`tests/manifests/finish/dragster-complete-race.json`.

## Finish/access capture

The complete suffix access record covers frames 3000–3679, including at least
120 frames on either side of the player crossing and finish/result boundary:
11,646,553 instructions, 5,858,791 derived accesses, 20,452 unresolved accesses,
zero unresolved stores. Its SHA-256 is
`06bf2769df2f6af21f9c78c0ccb9ec3820baf33f019eefcd071efab8bafa7f65`.
A four-frame focused capture fixes the continuous within-frame order; its access
SHA-256 is
`17fbd19656d3ff796c4b5dbab88290113d85a1463963e033225c1e47e9c61d25`.
The variation access window fixes both rider instances independently; SHA-256
`6fda1f7f1f47cf9e23324158e7a931cdb52fb4a22664b378ee046b90de251567`.

Verified writes:

- `$81:823B` writes word 1 once to player `$7E0EFF` and opponent `$7E0F01`.
- `$83:E81D` writes `$7E0F0F` once per frame for 240 frames after the player's
  finish becomes visible to the dispatcher.
- Ordinary derived axes are written first; `$83:E8F8` and `$83:E908` then force
  player/opponent horizontal values to neutral during the delay.
- In the continuous boundary, the dispatcher reads the player flag and writes
  counter 1 / neutral axes before the opponent writer later sets its flag in
  the same frame. In the variation, the player writer occurs late in 3318 and
  the dispatcher observes it in 3319. This rules out an “after both riders”
  interpretation of the counter.

The frame image changes lag the late rider write: continuous frame 3213 still
says `RACE` even though the end-of-frame state has the player flag set; 3214
first says `FINISH`. Timer formatting also changes: race HUD shows tenths while
the finish/result screens show two digits after the separator. No equivalence
between the shared timer digits and stored result time is claimed.

## Coverage delta

[The whole-run map](../map/race-crawler-dragster-12000-continuous-right-fields.md)
comes from 174,989,005 instructions and coverage SHA-256
`7654ac204a7a130f66a0dfe8228cf367dd88a35ffc7b2eec5a16ac3f3839337e`.
Relative to the accepted 3000-frame map:

- all 34,900 previously executed bytes remain covered and none is lost;
- 3,467 additional bytes execute in 92 ranges across banks `$80`–`$83`;
- 180 additional entry points appear;
- the largest groups first appear at player/opponent crossings (3213–3215),
  black/result initialization (3558–3561), and the first complete-screen frames;
- NMIs are absent for result loading in frames 3455–3554, a second NMI-off
  interval distinct from the accepted race load at 1208–1328.

These are executed-byte observations, not claims that the remaining ROM is
data or irrelevant.

## Content delta and track-buffer sufficiency

R-0008 already observed complete decoded-track reads from race start through
frame 2999. The new contiguous access suffix begins at 3000. Through the last
finish-display frame it records 16,849 reads by `$81:8AA1/$81:8AAA`,
`$81:8AB7/$81:8AC0`, `$81:8B66`, `$81:AD95` and `$81:B3CF` from
`$7F5ACB`–`$7F840E`. Every read lies within the accepted 33,815-byte decoded
block `$7F0000`–`$7F8416`; no bank `$7F` track read occurs outside it. Combined
with R-0008, the accepted block is therefore sufficient for every observed
track-data read from race start through the complete continuous finish path.
The variation's independently captured 3180–3558 track-read window adds 12,103
reads over `$7F5B0B`–`$7F840E`, also wholly inside the block; frames 3000–3179
were not access-captured for that input. This does not decode the block's
tile-map gather or generalize to another track.

Paired provenance for 3000–3679 lists 9,817 transfers: 9,495 ROM→VRAM,
198 WRAM→VRAM, 123 WRAM→OAM and one ROM→CGRAM. 9,814/9,817 destinations pair;
the three unpaired transfers are at the first capture frame because the
address-port setup preceded the window. The result load adds five block moves
(80 bytes total) at frame 3560. Phase totals are:

| Phase | Transfers | Bytes | Observed role |
| --- | ---: | ---: | --- |
| Race suffix 3000–3212 | 4,668 | 149,376 | streamed rider tiles and BG1 columns |
| Crossings 3213–3214 | 43 | 1,376 | same race presentation path |
| Finish display 3215–3453 | 4,960 | 158,720 | finish/rider animation |
| Black load 3454–3558 | 26 | 5,464 | new ROM tiles/palette plus OAM clears |
| Result init 3559–3560 | 1 DMA + 5 block moves | 3,152 | result tilemap/text setup |
| Results 3561–3679 | 119 | 66,240 | OAM animation and one WRAM→VRAM update |

## Playable-slice dependency inventory

| Interface | Evidence-backed state | M3 dependency / boundary |
| --- | --- | --- |
| Deterministic movement | M2 matches 13 fields through 2999 from a 333-byte state | Extend the existing native update through at least player frame 3318; do not feed it captured positions or CPU state. |
| Completion | Rider flags, per-player delay and derived-axis override are fixed above | Add an explicit state-format revision, stored finish times/outcome and transition phase; compare both winner and loser paths. |
| Controls | Reference polls once per PAL frame; native runner already consumes two controller masks | Add a 50 Hz real-time scheduler and device mapping. Right acceleration is validated. Up/Down affects visible pose without persistent WRAM state; Y/trick meaning remains unresolved and cannot be advertised as complete trick support. |
| Track/collision content | The accepted decoded block covers all observed race/finish reads | Preserve the proven gameplay sampler; separately implement the still-unrecovered BG1 column gather for native presentation. |
| Rider presentation | Original streams sprite tiles every race/finish frame; research renderer reproduces selected original frames from original OAM/VRAM | Map native pose/finish state to logical rider frames and anchors. The Python PPU renderer and emulator OAM are research inputs, not a native frontend. |
| Track/HUD/results rendering | Static BG assets are decoded; result loading introduces new ROM assets, five block moves and new code | Inventory/decode result/HUD assets and implement only the minimal readable native renderer. Existing omissions remain BG3, windows/colour math, fine priority and some flips. |
| Frontend | No `src/app/` exists; SDL3, live input and display scheduling are unexercised | Add a minimal desktop app around `step(state, inputs, content, rules)` without changing simulation timing. Audio may remain explicitly omitted for the M3 slice. |

Proposed split, for coordinator registry amendments after review:

1. **M3-01 — native finish and full-race state:** extend simulation and explicit
   serialization through both frozen finish paths, including first-divergence
   checks and stored-time investigation.
2. **M3-02 — native presentation contract:** recover rider-frame mapping, BG1
   gather and minimum HUD/result assets against selected reference frames.
3. **M3-03 — minimal frontend and controls:** SDL3 window, keyboard/gamepad
   masks, PAL scheduler, native renderer integration and declared audio omission.
4. **M3-04 — playable-slice acceptance:** clean-checkout build, sustained play,
   complete-track differential suite, real control/readability check and fresh
   independent review.

This split keeps gameplay/state, presentation extraction and platform I/O at
measured interfaces. It does not create a general engine or claim full trick,
rendering, audio, menu or other-track coverage.

## Reproduction

After `doctor`, debug build, synthetic suite and `reference build`:

```sh
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-dragster-3000-fields.json --runs 2
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json --runs 2
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json --against tests/manifests/replay/race-crawler-dragster-12000-release-3000-3299-fields.json
python3 tools/project.py coverage capture --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json --out artifacts/coverage/race-crawler-dragster-12000-continuous-right-fields --frame-image 3213 --frame-image 3214 --frame-image 3453 --frame-image 3454 --frame-image 3679
python3 tools/project.py coverage map --coverage artifacts/coverage/race-crawler-dragster-12000-continuous-right-fields/coverage.json --out docs/map/race-crawler-dragster-12000-continuous-right-fields.map.json --summary docs/map/race-crawler-dragster-12000-continuous-right-fields.md --baseline docs/map/race-crawler-dragster-3000.map.json
```

The exact access/provenance commands used for the verifier were:

```sh
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json --out artifacts/m3-00-complete-access/capture --from-frame 3000 --to-frame 3679 --watch-pc 0x000199 --watch-address 0x002116 --watch-address 0x822116 --watch-address 0x002115 --watch-address 0x822115 --watch-address 0x002121 --watch-address 0x822121 --watch-address 0x002102 --watch-address 0x802102 --watch-address 0x002103 --watch-address 0x802103 --watch-address 0x00210D --watch-address 0x00210E --watch-address 0x00210F --watch-address 0x002110 --watch-address 0x002107 --watch-address 0x00212C --watch-address '$7E:0319' --watch-address '$7E:0325' --watch-address '$7E:034B' --watch-address '$7E:034F' --watch-address '$7E:0E19' --watch-address '$7E:0E1D' --watch-address '$7E:0E21' --watch-address '$7E:0E25' --watch-address '$7E:0E29' --wram-series-range 0x300 0x100 --wram-series-every 1 --task M3-00 --report artifacts/m3-00-complete-access/capture-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json --out artifacts/m3-00-order-access/capture --from-frame 3212 --to-frame 3215 --watch-address '$7E:0EFF' --watch-address '$7E:0F01' --watch-address '$7E:0F0F' --watch-address '$7E:0319' --watch-address '$7E:0325' --task M3-00 --report artifacts/m3-00-order-access/capture-report.json
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-dragster-12000-release-3000-3299-fields.json --out artifacts/m3-00-variation-access/capture --from-frame 3180 --to-frame 3800 --watch-address '$7E:0EFF' --watch-address '$7E:0F01' --watch-address '$7E:0F0F' --watch-address '$7E:0319' --watch-address '$7E:0325' --task M3-00 --report artifacts/m3-00-variation-access/capture-report.json
python3 tools/project.py content provenance --access artifacts/m3-00-complete-access/capture/access.json --out artifacts/m3-00-content/complete-provenance --task M3-00 --report artifacts/m3-00-content/complete-provenance-report.json
```

Run the compact verifier against those regenerated ignored files:

```sh
python3 -m tools.unirally_lab.finish.analyze --contract tests/manifests/finish/dragster-complete-race.json --continuous-samples <continuous-samples.json> --variation-samples <variation-samples.json> --continuous-access <continuous-access.json> --variation-access <variation-access.json> --coverage-map docs/map/race-crawler-dragster-12000-continuous-right-fields.map.json --content-manifest tests/manifests/content/dragster-segment.json --provenance <provenance.json> --out artifacts/m3-00-finish-analysis.json
```

The analyzer is ROM-free once artifacts exist. It passed 20/20 contract checks;
the compact result SHA-256 is
`2c1467d062ba5c6f6dc6b07199b60bad5edd97b377b95bb23623e196dfbb31bc`. It
rejects a changed finish boundary, missing writer, out-of-block track read and
wrong digest/coverage value. Large samples, access records, frame images,
decoded bytes and ROM content remain ignored.

## Limits

- One PAL ROM, one track, one menu path and two input streams on one macOS host.
- The result-screen stored-time fields and ranking/award semantics are unknown.
- Full trick rules remain unverified; the variation happens to display
  `TO ROLL`, but that is presentation evidence, not recovered trick logic.
- The result asset bytes are inventoried by transfers, not yet assigned stable
  logical identities or decoded for native use.
- No native full-race comparison, renderer, audio path, live controls or
  frontend exists. M3 is not accepted by this research candidate.
