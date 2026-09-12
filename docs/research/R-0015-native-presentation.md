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

## OAM association and asset-backed reduction

An initial `$0A00` series sampled the OAM DMA staging area, not the semantic
shadow, and was rejected as a descriptor source. The corrected `$138B` shadow
capture (`access.json` SHA-256 `9acb899c...4c58`) passed all identity checks.
Across frames 1600/2000/2400/3213/3453, shadow entries 98 and 99 are the
player/opponent 64-by-64 objects: tile bases 0 and 136, attributes `$66/$68`.
Their descriptor bases remain fixed while semantic pose changes select new
32-byte tile DMAs. At frame 2000 the opponent's high X bit represents wrapped
screen X -26. This associates pose keys with tile payload selection rather than
inventing per-pose OAM geometry.

The first real SNES tile/palette decode reconstructs VRAM/CGRAM entirely from
the twenty-entry pack, including observed BG1 tile destinations, 4bpp planes,
16-by-16 subtile addressing, flips, palette selection and the calibrated
one-line vertical phase. The first preregistered frame-3213 reduction, using
fresh scroll values BG1 `(24367,208)` and BG2 `(12183,104)`, differs in
33,561/50,176 pixels (66.89%). This fails the frozen 3% limit. It proves that
the 30-by-16 region is a metatile-definition source for the rolling gather,
not a complete static BG1 screen map; the `$81:B270` selector construction must
drive map expansion before another visual claim.

## Rolling BG1 selector relationship

A bounded frame-3212--3214 capture first established that `$81:B270` runs once
for each newly exposed column and publishes sixteen words for a vertical VRAM
column.  A second capture over frames 1599--3454 watched the five direct-page
selector inputs at `$00..$08` and the complete builder.  Its `access.json` has
SHA-256 `39fa19e2871b392d...` and passed the unchanged full-race sample and final
state identities.  The smaller capture has SHA-256 `f8685461a3931ba0...`.

For frozen updating frames 1600, 2000, 2400 and 3213, the five selector words
come from decoded-track byte offset
`$5831 + 2 * floor(BG1_scroll_x / 64)`, then from the four corresponding
vertical planes at successive `$0800` offsets.  The selector tuples are
`(7,7,7,28,0)`, `(6,6,6,28,0)`, `(9,9,9,28,0)` and
`(0,0,0,26,0)`.  The horizontal subcolumn passed to `$81:B270` is exactly
`(floor(BG1_scroll_x / 16) + 1) & 3` in all four cases.  The observed vertical
subrow is 2 at scroll Y 203 and 3 at scroll Y 208.  `$81:B270` then gathers
four-word groups from the selector's 32-byte metatile definition with an
eight-byte stride, clipping the first and last groups by that vertical subrow.
Frame 3453 no longer invokes the builder and retains the completed race map.

This closes the metatile selector and gather relationship on the four declared
updating frames.  Ring-column placement and the exact screen-edge phase remain
to be checked against the staged DMA destination before replacing the failed
static expansion.

The native port uses the DMA destination phase to reconstruct the 32-by-32
ring statelessly from scroll position.  A separate capture watching VMAIN,
VMADD, VMDATA and CGRAM over frames 1599--3454 passed the unchanged identities
and has access SHA-256 `c69d43694055d6cd...`.  It associates all 108 packed
rider tiles with their exact VRAM words in the five frozen DMA inventories
(27, 20, 21, 21 and 19 tiles).  The 64-by-64 objects use the already observed
tile bases 0/136, palettes 3/4 and horizontal reflection.  Original screen X
is `position_x - camera_x - 832`; all five frozen player coordinates and the
frame-2000 opponent wrap agree exactly.  Screen Y is `position_y - 752`.

The same capture closes the race palette rewrite: CGRAM colours 96--111 are a
semantic race/late-finish cycle, and colour zero changes from `$7FFF` to
`$7DAD` at the late-finish pose.  With those observed writes, packed rider
tiles and rolling map, the frame-3213 regional comparison is 445/50,176
pixels (0.89%), down from the rejected static renderer's 33,561/50,176
(66.89%) and within the preregistered 3% limit.  The residual is confined to
the declared HUD and colour-math omissions.  Other frozen cases and the result
screen still require automated reference checks before candidate submission.

The first four additional raw regional comparisons produced: frame 1600
10,230/50,176 (20.39%, failing 2%; the preregistered windowed `G` dominates),
frame 2000 697/50,176 (1.39%, passing 2%), frame 2400 279/50,176 (0.56%,
passing 2%), and frame 3453 5,654/50,176 (11.27%, failing 3%; the fixed-colour
winner overlay dominates).  These failures are retained as failures; no limit
or expected image was changed.  A result-mode PPU capture has access SHA-256
`7096ed7850cfdac0...` and records mode 3, BG map/tile base registers, the
result palette transfer and the two tile transfers needed for the stable
screen reconstruction.

## Additive window-effect prerequisite freeze

The two failed cases exposed a bounded prerequisite after the initial seven
presentation payloads were frozen: the declared GO and winner effects are
channel-6 window compositions backed by static ROM tables. A fresh capture of
frames 3452–3454 watched channel 6 and `$2123..$2132`, passed the unchanged
sample/final-state identities, and produced `access.json` SHA-256
`3a6a0b56141b36da...`. Original setup at `$82:D572` writes channel-6
`DMAP=$04` and `BBAD=$26`; `$80:8691` selects the table address and bank.

At frame 1600 the selected table is `$15:8A89`; at frame 3453 it is
`$15:BF36`. Each is exactly 898 bytes: two repeat-mode HDMA runs containing
224 four-byte scanline rows for WH0, WH1, WH2 and WH3. The displayed mask is
the XOR of the two inclusive horizontal windows. Their source SHA-256 values
are respectively `33f19daed02ec2f968d1a1ba27675a4da794c96772af28edfc1e321e113c4b29`
and `b6fddc697a55984d607220aff50ab465881297de3f94fd9e434c0c9be3d4df20`.

Before committing the consumer, the extraction and presentation manifests
additively freeze these as `presentation.effect.go-window.v1` and
`presentation.effect.winner-window.v1`. The already frozen reference cases,
rectangles and limits do not change. A first reduction from those entries gives
36/26,656 mismatches (0.135%) for frame 1600's exact declared rectangle and
653/50,176 (1.301%) for frame 3453, below the original 2% and 3% limits.

The first stable-result placement remains a recorded failure. A canonical
frame-3678 restore (the last legal interior save boundary) is already in
`ResultScreen` and reproduces the stable frame-3679 presentation inputs. The
diagnostic/first placement differs in 57,280/57,344 pixels (99.89%), far above
the frozen 15% limit. Mode 3, BG map/character registers, the final constructed
2,048-byte map, palette transfer and two tile transfers are observed; the
unresolved relationship is which BG owns each transition tile payload and the
retained tile-76 background used by the filled map. No limit or expected image
was changed.

A narrow follow-up capture at the copier byte load `$82:B296` closes the
missing retained content. It passed the unchanged identities and produced
`access.json` SHA-256 `157073878b192100...`. Partitioning its ordered source
addresses at the observed VMADD writes yields four final-state runs: 8,192
bytes from `$07:A9D8` to VRAM word `$6000`, 2,816 from `$06:CCB8` to `$0000`,
8,960 from `$04:DFF8` to `$2000`, and 21,568 from `$04:8BB8` to `$31A0`.
The previously packed 1,920-byte DMA then starts at the retained `$3D80`
VMADD, the 3,072-byte DMA writes at `$7A00`, and the constructed map is last at
word `$1000`. The four retained runs total 41,536 bytes with concatenated
SHA-256 `c1f19c30...e04f4`.

This content existed before the later result DMAs and was therefore absent
from the first narrow inventory; it is not derivable from the four small
pieces. Before its consumer, the manifests additively freeze it as
`presentation.result.classic.base-vram.v1`. The twenty-three-entry extraction
rules SHA-256 is `43d14175...82a53`; all prior payload identities and the 15%
gate remain unchanged.

The same copier capture corrects the first palette hypothesis. The 216-byte
DMA at frame 3529 is a transition palette; frames 3557–3558 later copy 216
bytes from `$04:8700` to CGRAM indices 0–107. The later payload begins with
stable gray `$39CE`, has SHA-256 `155799e6...0e18`, and is additively frozen as
`presentation.result.classic.palette.v1`. The inventory is twenty-four entries
under rules SHA-256 `11aeefa1...265c3`; the earlier transition payload remains
identified rather than silently replaced.
