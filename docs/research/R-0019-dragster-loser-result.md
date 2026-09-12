# R-0019 — DRAGSTER loser-result composition

- Task: [M4-01](../../tasks/M4-01.md)
- Status: accepted evidence and implementation; integrated as `3058eb9` after
  approved focused re-review
- Freeze base: task claim `55eadf7`; no presentation source changed before this
  record and the additive loser contract
- ROM: PAL Unirally SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`
- Core: bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
  `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`

## Baseline and terminal state

The accepted pack-backed release-3000 producer passes in two fresh processes
through frame 3800 and from restored boundaries 1600, 3318, 3558 and 3799. The
ignored report is `artifacts/m4-01-release-baseline-verified/report.json`,
SHA-256 `88e898e4ac8f6669a5336f9e9e206fb5ac6d14e21a196b31ceb1195a393fd249`.
The exact command is recorded in M4-01.

The terminal canonical `URMV0003` state was taken from that unchanged
producer's frame-3800 row, not made by mutating a winner state. It is 371 bytes,
SHA-256 `27b465c9495ee74dd405fda36987eeeda1d6ab4352807049616ed2394e0dd921`,
and carries `ResultScreen`, `PlayerLost`, player digits `0:35.66` and opponent
digits `0:33.58`. The source native case is SHA-256
`bb3afe060fe445fa6d4c45b44eb14c25f84cf7b6bdf81dacfee9cbcc1ab7ee30`;
its replay is SHA-256
`b9bc77dacf04dc8cebebf0a54c3b393000d73e1bd08ff92ca45579587b4bdc10`.

## Ordered original observation

A fresh pinned-core capture of frames 3528–3800 watches the complete result map
range, OAM shadow, result copier/map writers and banked/unbanked display, VRAM,
CGRAM and layer registers. It retains the accepted reference sample digest
`d24a12347bcda335...` and final serialized-state digest
`628878bd41e4edec...`; all required completeness checks pass. The ignored
`access.json` SHA-256 is
`afa7abedf63e0bfb5897b54c6624f80a17afb132108f4ec444d0feb6d8485482`.

The corresponding winner capture uses identical instrumentation over frames
3423–3679. Its access SHA-256 is
`5a89b72eac7efff87ca30d7e1bbf4ea2b7062147148c4ce75f571b67bf3fdf78`.
The copier at `$82:B296` executes 53,432 times in each capture, and its complete
register/value stream is byte-identical after removing frame numbers (normalized
SHA-256 `1f92fde2b6ecddb4213889e1949b639793598389d171ec5e7a15cb023252f2d1`).
The same map writer `$80:C431` executes sixteen times at winner frame 3560 and
loser frame 3665. The result assets in the existing 25-entry pack are therefore
sufficient; no extraction-rule or payload change is supported.

The final 2,048-byte loser map is SHA-256
`e217ec39d96686b6e026b6d97c80999ceb0a6dbca3b2a9b9419e4bd5b6ea1acd`.
It differs from the winner map `2d6e563a...0129` at exactly six bytes, all three
changed player-time glyphs and their lower halves:

| Tile `(x,y)` | Winner | Loser | Observed meaning |
| --- | --- | --- | --- |
| `(21,11)` / `(21,12)` | `$3CAC` / `$3CE8` | `$3CAE` / `$3CEA` | `3` to `5` |
| `(23,11)` / `(23,12)` | `$3CAE` / `$3CEA` | `$3CAF` / `$3CEB` | `5` to `6` |
| `(24,11)` / `(24,12)` | `$3CB0` / `$3CEC` | `$3CAF` / `$3CEB` | `7` to `6` |

Everything else in the semantic map is identical: title `DRAGSTER`, subtitle
`COMPLETE`, header `PLAYER     TIME`, row `MIKE      0:35.66`, then three
`SOMEONE   NO TIME` rows. No loser-specific title, ranking or award is observed.

The stable display registers equal the accepted winner configuration. The only
stable palette-cycle distinction needed by the bounded background renderer is
CGRAM words 108–111: loser frame 3797 writes `$4210,$56B5,$4A52,$4631`, while
winner frame 3678 writes `$4A52,$4631,$4210,$56B5`. The native state reaches
`ResultScreen` at frame 3800; original frames 3798 and 3799 are pixel-identical
to one another, and frame 3800 is the first complete result image. This rejects
copying the winner's presentation-only loading-update-225 boundary to the loss
path.

The original loser PNG is SHA-256
`2441b84cec5c047fcfac286389314843e8fb0690531e5bbef0d0c249b7701afb`.
The additive contract
`tests/manifests/presentation/classic-crawler-dragster-loser-v1.json` binds it,
the terminal state, source manifests, semantic map hash/placements and the
existing whole-frame result policy `[0,0,256,224]` at 15%. The older seven-case
contract and its authentication remain unchanged. The frozen contract SHA-256
is `887890a753a6e3223f69a06371ef7bed78d8ead77e66c178045dd377aa751c6b`;
its canonical case-array SHA-256 is
`c6fb70dfb856dae9f602da343cef5841530839e18c895612b46f020c5382e043`.

## Boundaries

This evidence supports only the stable PAL/1P/MIKE/CRAWLER/DRAGSTER
release-3000 loss result and its adjacent 3798–3800 publication boundary. It
does not establish general rankings, awards, other names/tracks/modes, menus,
progression, audio or result objects. Focused map assertions remain necessary:
the 15% visual limit alone is not semantic evidence.

## Candidate reproduction

The bounded compositor at `f438741` reproduces all specified map placements and
differs from the original loser frame at exactly 1,073 of 57,344 whole-frame
pixels (`1.871164%`) in both debug and sanitizer builds. The same builds retain
the seven accepted winner-case mismatch counts exactly. The pack-backed live
runner obtains identical output from fresh and previously used presentation
instances and proves the canonical 371-byte state unchanged across rendering.

The exact clean candidate report hashes and negative identity checks are
recorded in M4-01. These implementation results do not widen the evidence above:
only the independently observed stable loss state and adjacent publication
boundary are claimed.

Independent review reproduced the original capture and returned one semantic
boundary finding: the first candidate accepted `ResultScreen` with a forged
loser loading counter of 241. Correction `a3106f4` binds the compositor to the
observed loser `ResultScreen`/242 tuple and the separately observed winner
`ResultLoading`/225 and `ResultScreen`/226 tuples. Its live pack-backed regression
derives and rejects the counter-241 mutation; all visual counts remain exact.
