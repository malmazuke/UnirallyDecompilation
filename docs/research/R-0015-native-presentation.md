# R-0015 — Native presentation contract and DRAGSTER gather

- Task: [M3-02](../../tasks/M3-02.md)
- Status: presentation contract frozen before native renderer implementation
- ROM/core: accepted PAL identity and pinned bsnes identity from R-0008/R-0013
- Machine contract: `tests/manifests/presentation/classic-crawler-dragster-v1.json`

## Pre-implementation reproduction

The accepted R-0008 comparisons were re-run from the original ignored access,
WRAM and image artifacts. Frame 1600 again differs in 490/26,656 pixels
(1.84%) and frame 2400 in 791/50,176 (1.58%), with the existing declared PPU
omissions. The accepted M3-02A pack-backed continuous race and fresh-process
restores at 3213/3453 passed all twelve checks. Reports under the worker's
ignored `artifacts/m3-02-baseline/` have SHA-256 `ae63550b...ff3db`,
`def31f6d...163` and `1456b901...bb05` respectively.

A fresh three-frame access capture around frame 2000 reproduced the accepted
sample/final-state identities and froze frame 2000 PNG SHA-256
`024de09e...189f`. Captures, decoded bytes, generated frames and packs remain
ignored.

## Observed BG1 gather

The bounded frame-1328–1340 capture watches `$81:B31C`, `$81:B366`,
`$81:B3CF/$B3D3`, `$0234`, `$0236`, `$0559` and both staging buffers. It has
`access.json` SHA-256 `20b78722...6b8` and the unchanged reference sample
digest `72f618f2...b1f`.

At `$81:B3D3`, the original loads a little-endian word from
`$7F:000F + X`, stores it at the current staging destination and advances X by
the current `$0236`. Every one of the 347 watched loads in frames 1329–1339
equals the same word in the independently decoded 33,815-byte track entry. In
frame 1334 all 33/33 words agree; source X spans `$8004`–`$801C` and the
destination spans `$0437`–`$0477`. `$81:B31C` constructs its source from a
column selector multiplied by 32, plus `$0234` and `$0559`; the two calls in
frame 1334 see the preceding writers publish the two observed parameter sets
`($0234,$0236)=(16,2)` and `(0,8)`. `$0559` remains `$8000` in this loading
and riding boundary. This establishes a 32-byte/16-word column region beginning
at decoded offset `$800F`, and a strided gather from it; it does not assign a
gameplay meaning to the builder's scratch selectors.

## Frozen presentation boundary

Presentation samples occur after the same PAL game update as the accepted
semantic movement state. The renderer receives semantic phase/outcome/timer,
both riders' positions, pose indices and reflection flags, plus presentation-
only camera/BG scroll values. These fields do not enter `URMV0001/2` and no
gameplay serialization changes are authorized. The pose index is already the
direct semantic counterpart of the original published `$0FF3/$0FF5`: native
and reference are `0x04F9/0x0263` at 1600 and `0x0895/0x0895` at 2400.

The contract freezes race frames 1600/2000/2400, finish-delay frames 3213/3453
and stable result frame 3679 before renderer code. It also freezes logical pack
IDs and comparison rectangles/limits. The wider result-screen limit is
provisional and may only be tightened by implementation; it must not be enlarged
after observing output.

## Limits at freeze

The gather is byte-exact for the watched primary boundary, not another track.
The meaning of the decoded header/geometry regions is still unknown. Rider DMA
rows are observed, but the mapping from each semantic pose to an authored frame
descriptor remains the next experiment. Stable-result graphics provenance has
not yet been closed; only the font-backed minimum layout is frozen.

## Native boundary checkpoint

Commit `9c2bcb3` implements the byte-exact strided gather, deterministic 30 by
16 column-major expansion, and an explicit lookup for the seven pose keys in
the preregistered cases. Unsupported pose keys fail closed. The offscreen
runner accepts only a validated Classic pack plus canonical movement state and
writes a 256 by 224 RGB PPM; rendering leaves canonical gameplay bytes
unchanged. A ROM-absent frame-3213 run produced SHA-256
`8c975f8f...ca651`.

This is an intermediate diagnostic composition, not a visual acceptance
result. The first 13-entry pack did not contain the seven frozen presentation
assets. The rules have since been extended to twenty exact entries, but the
renderer still uses diagnostic map colours and rider shapes and has not
satisfied the frozen mismatch limits.
Sprite frame descriptors, BG tile/palette placement and stable-result
provenance remain required; the frozen limits must not be enlarged.

## Result-loading provenance narrowing

The existing continuous finish capture closes the large result-screen loads,
which occur well before the stable frame rather than at frame 3679. Frame 3529
DMA-copies 216 palette bytes from ROM file offset `0x0028D4`. Frame 3556 copies
1,920 bytes from `0x022378`, and frame 3559 copies 3,072 bytes from
`0x03D5D8`, both to VRAM. Frame 3561 then copies the constructed 2,048-byte
WRAM map at `$000200` to VRAM word `$1000`. Frame 3560 contains the 16-byte
template/block-move activity that precedes this map upload. At stable frame
3679 the only DMA is the normal 544-byte WRAM-to-OAM transfer.

This establishes the result palette/tile payload sources and that the layout
must be represented as a deterministic template expansion, not extracted as a
captured WRAM image. The exact 16-byte template source and its expansion
semantics, plus OAM-to-pose frame descriptors, remain to be closed before the
pack rule can honestly claim the frozen `font-layout` logical entry.

A fresh bounded capture (`artifacts/m3-02-result-map/access.json`, SHA-256
`34247f71...e90c`) sampled the full `$0200..$09FF` map buffer and frames
3559–3561. It passed all identity/completeness checks and retained the accepted
full-run digests. `$83:8B7D` first fills all 1,024 map words with `$004C`; the
loop at `$83:8B85` is byte-visible as `A9 4C 00 / A0 FF 03 / 9D 00 00 / E8
E8 / 88 / 10 F8`. Frame 3560 overlays 444 bytes from `$0290` through `$0771`;
one confirmed overlay writer is `$80:C431`. The final map is unchanged from
frame 3560 through stable result and has SHA-256 `2d6e563a...0129`. This closes
the base expansion and exact result, but not the semantic overlay algorithm.
