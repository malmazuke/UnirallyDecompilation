# R-0011 contact response research

Work in progress; not accepted. Base `ba71142a6d766216772360949dd8c04760fa9ffe`.
ROM/core identity and primary scenario are unchanged from R-0010.

## Preregistered experiments

Before capture, 12 September 2026: primary frames 1576–1618 should show each
rider loaded into scratch, sample preprocessing, contact response, then
publication. Opponent's 1578 jump trigger precedes the first no-contact counter
increment at 1580. The counter should saturate at nine rather than counting
jump triggers, and recontact at 1617 should reset it through a different path
from the player's continued contact. Test using `contact_research.capture`.

Separate research variation: release player Right after frame 1569 (retain
all menu inputs and the later Up input). Prediction: the contact routine still
runs for both riders every frame; while samples show no support the same
saturating-counter recurrence applies regardless of speed, and positive player
support remains on the continued-contact path. Opponent timing may shift via
its player-relative dependencies; identical jump timing is not predicted.
No M2-01 withheld series will be opened or used.

## Identity, tested domain and result

ROM SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`,
Strict serialization, unchanged default options. No autonomous native simulation is run.
The initial observation remains end-of-frame 1533; all claims below concern
contact calls during primary 1534–2999 unless a narrower interval is named.
Whole-run coverage includes startup paths which do **not** run in this domain.

There are 2,932 calls, player then opponent every frame: 2,889 continuous
contacts, 42 unsupported calls and one recontact. Unsupported calls are opponent
1580–1616, 1625–1626 and 1629, and player 1749 and 1751. The recontact is
opponent 1617. The research model reconstructs six preprocessing/reduction
outputs for all calls: **17,592 values match**. Independently checked arithmetic
relations for counter, duration, velocities and position publication pass
**37,989 checks** across those calls. These are isolated functions with captured
arguments, not an autonomous movement test and not M2-01 acceptance.

The separately preregistered release-1570 variation has 86 calls in 1576–1618:
48 continuous, 37 unsupported and one recontact; all 1,006 checked relations
match. The predicted counter/response invariance holds. The actual opponent
jump/contact schedule also stays the same; that was not required by the
prediction. Input release changes the sample digest, so this is a distinct
research execution. Its expected field is deliberately empty: observations
come from the identified original, not a newly installed gameplay baseline.

## Call order and persistent state

The caller `$81:8CF8` loads player state, expands the pose (`$81:9E1B`), gathers
and preprocesses the ten samples (`$81:8B75`), calls response (`$81:8DBC → 8F98`),
then publishes. It repeats for opponent (`$81:8F10 → 8F98`). Response returns
at `$81:982B`. This happens after motion; the pose worker has separately traced
new pose publication immediately before this caller. Contact itself runs on
both riders every frame; its counter must not be updated only on alternating
physics/progress phases.

All numeric persistent fields below are little-endian 16-bit words in the
observed caller. Several are logically small flags/counters; low-byte stores
preserve their existing high byte. The primary seed and every checked output
have zero high bytes for those flags. Native code should represent this
explicitly and reject an unsupported high-byte state, rather than silently
altering the original word's meaning. Scratch addresses are shared by the two
calls; they are not independent game-state records.

| Proposed concept | Scratch | Player / opponent persistent source and destination | Role and confidence |
| --- | --- | --- | --- |
| Position x,y | `$A5,$A7` | `$0415,$0419` / `$0417,$041B` | Incoming integrated position; x preserved, y corrected; established |
| Horizontal/vertical velocity | `$0FA9,$0FAB` | `$04BB,$04BF` / `$04BD,$04C1` | Continued contact clears vertical component; landing can preserve it for one frame; established numerical role |
| Unsupported count | `$0F33` | `$054B` / `$054D` | Increments once per unsupported frame, saturates at nine; zeroed on supported response; established |
| Previous unsupported count | `$0F4F` | output `$054F` / `$0551` | Snapshot of incoming count, saved before any response mutation; established |
| Unsupported duration | `$0FBF` | `$0FC1` / `$0FC3` | Unsaturated u16 count of successive unsupported calls; resets on support; established |
| Previous pre-correction x,y | `$0EED,$0EEF` | `$04D7,$04DB` / `$04D9,$04DD` | Needed by recontact angle calculation; overwritten with current **uncorrected** x,y before correction; established |
| Surface angle | `$0F17` | `$0B6E` / `$0B70` | Set to zero on flat support; preserved unsupported. Angle interpretation supported by consumer/math, domain value zero |
| Angle sentinel flag | `$0F2B` | `$04EB` / `$04ED` | Low byte starts one each call; becomes zero for supported angle other than31; high byte remains zero here |
| Response channels A,B | `$0F55,$0F57` | `$0BB3,$0BB7` / `$0BB5,$0BB9` | On continuous contact cleared when `$0300==0`, otherwise preserved; A stays zero; B is2 on the24 opponent unsupported calls1590–1613 and is preserved there. Neutral names until motion semantics establish more |
| Orientation impulse | `$0FAD` | `$0D35` / `$0D37` | Preserved except recontact, which writes4; next motion phase consumes/damps it (motion worker contract). Numerical dependence established |
| Mode flag | `$0F23` | `$0B93` / `$0B95` | Incoming zero in the supported flat paths; alternate modes are unsupported |
| Prior x displacement | `$0F73` | `$0BBB` / `$0BBD` | Contact caller loads this separately from motion's reuse of same scratch; recontact value14 determines impulse4 |
| Previous auxiliary flag | `$0EF1` | `$04DF` / `$04E1` | Zero in this domain; cleared on no solid sample, otherwise preserved; other behavior unsupported |
| Selected sample high byte | `$0F31` | output `$0B72` / `$0B74` | Last winning sample's high byte, zero-extended. Feeds later motion; a metadata value, not guessed surface normal |
| Selected sample word | `$0F13,$0FB3` | outputs `$0E9F,$0FFB` / `$0EA1,$0FFD` | First eligible descriptor, can differ from deepest sample; old `$0F13` is discarded at response entry |
| Recontact flag | `$1279` | output `$127B` / `$127D` | Initialized zero every call, set one on incoming count>=9 with support |
| Marker word | `$0FB5` | `$0FC5` / `$0FC7` | Existing sampling/progress contract; preprocessing may update it before contact; response does not modify it |

Pose `$0411/$0413` and reflection `$0BA7/$0BA9` determine sample points. The
response also reads their scratch copies at the sole recontact, calculates
`pose&63` and its reflected form, and writes diagnostic temporary `$0256`.
That temporary is not read on the executed response path; this does not add a
second causal pose input beyond the already required sample geometry.
`$0F53,$0F39,$0F41,$0F81` are caller-loaded words not used to change outputs by
the primary response paths. `$0F81` is simply republished unchanged here.
`$0F5D` is reset at entry and remains zero, so its caller-loaded old value is
not a response dependency in this domain.

The proposed native boundary is a small `resolve_flat_contact(rider,
sample_summary, update_phase)` function with explicit rider fields from the
table, after `preprocess_collision_samples`. Keep marker/progress observation
separate. The summary contains support status, penetration, selected word,
selected high byte and angle. It must be computed from static content and
current native geometry, not captured each frame. Preserve the previous count
and pre-correction position in rider state for downstream motion. No register
file or emulator execution is needed.

## Preprocessing and reduction contract

`$81:8B75–8CF3` receives the ten native gathered words and the ten expanded
collision point pairs documented in R-0010. It scans sample indices9 down to0.
For each word `raw`, retain its descriptor. If `raw & 0x03FF == 0`, apply the
existing marker update, clear the descriptor and mark penetration as `0xA0`
(empty). Otherwise the content-tile index is
`((raw & 0x03F0) >> 2) + ((raw & 0x000F) >> 1)`.
The raw direction bits `$C000` are zero for every nonempty descriptor in this
domain. The tile flag's low bit is also zero, selecting vertical columns.

Use local column `(point.x + (x & 15)) & 15` and local y
`(point.y + (y & 15)) & 15`. At `tile*32 + local_column*2`, the first static
column byte is height and the second is angle. Height `$A0` produces empty;
otherwise penetration is `u8(local_y - u8(height - 1))`. Every actually solid
height is zero in this domain; every sampled angle is zero. This formula and
content lookup explain penetration from geometry rather than fitting y values.
The arrays `$0230..0243` hold byte penetration/angle pairs, `$0290..02A3`
hold axis selectors, `$02C0..02D3` hold descriptors. These arrays are scratch,
not persistent simulation state.

The response's first point takes a separate branch, but is always empty here.
Then process indices1 through9 in ascending order. Initialize summary penetration
`$FF`, chosen descriptor0, correction0, selected high byte0 and angle byte`$E0`.
An empty point can supply the first descriptor if its low nine bits are nonzero;
otherwise it does not establish support. A nonempty point competes against the
summary using the sign bit of **8-bit subtraction**. On greater-or-equal it
replaces the summary; the first eligible descriptor is retained, while the
last winning sample at index>=2 replaces the selected high byte and angle.
Every nonempty competitor here is nonnegative and flat; support at index0 or1
is outside the checked contract. Vertical correction is the maximum solid
penetration, with axis selector0; horizontal correction and axis are zero.
The reducer preserves the distinction between first descriptor and last/deepest
sample metadata, including ties.

Descriptor flags are read from `$7E:C000 + tile_index` at `$81:917C`. Values
are0,18,20 here; none selects the special response branches. `$0F13` becomes
the descriptor; `$0FB3` receives the same word; `$0F31` receives selected high
byte. On no support the angle stays signed -32; on support it is zero. The
original sign-extends the angle byte at `$81:921F–9227`. The compact capture
watches `$2A` but not every write to `$2B`; the checker compares the **observed
low angle byte**, not a falsely assembled intermediate 16-bit snapshot.

Static columns/flags are the existing R-0008 raw copies, now restricted into
`tile-tables.content.json`: 640 column bytes SHA-256
`bb95427aa2a307c9…` and20 flag bytes `590e52f2640bb1b7…`. The manifest records
all source pieces; decoded bytes remain ignored. No newly guessed geometry
format or content table is introduced.

## Response predicates, arithmetic and publication

At entry `$81:8F9A–8FD7`, copy count to previous-count, reset temporary selection,
correction and recontact fields, and initialize the angle-sentinel low byte1.
The original routine then executes one of these primary-domain paths:

1. **Unsupported (`$81:9235–924B`).** Load summary as an8-bit value. Its sign
   bit remains the branch predicate after changing accumulator width. If
   negative, increment duration modulo65536. Compute `next=u16(count+1)`;
   store it only if the sign bit of `u16(next-10)` is set (the
   primary values0..9 make this exactly `next<10`). Thus count saturates9.
   Preserve velocities, surface angle and response channels. Execute common
   correction/publication below. The42 unsupported calls all have summary`$FF`.
2. **Continuous flat support (`$81:924E–92D0`, `$81:9610–97E1`).** The observed
   incoming vertical velocity is nonnegative, the angle is0 and special flag0.
   Write surface angle0, clear angle-sentinel low byte, then use incoming
   count<9 to choose this path. If phase word`$0300==0`, clear response A,B;
   otherwise preserve them. Clear count and duration. The two ROM slope entries
   read at `$00:822B` and `$00:824B` are zero (file offsets`$022B,$024B`), so
   horizontal velocity remains unchanged and vertical velocity becomes0 at
   `$81:970B`. The angle contribution added to horizontal velocity is0.
3. **Recontact (`$81:92D3–94CD`).** Incoming count>=9 sets recontact1. The only
   primary case is1617 opponent. Before correction, x=2264,y=865 and saved
   x=2250,y=857. `$81:982C` uses `abs(dx)=14`, `abs(dy)>>1=4`. Starting angle16,
   repeated subtraction of4 from14 reduces the angle by4 for each successful
   subtraction:12,8,4, then stops when the remainder turns negative. Compared
   with surface angle0, the four-step difference lies in the first five-unit
   bucket, so the helper returns sentinel`$FFFF` in `$A3`. The reflected pose
   temporary is55; it does not change this result. Contact computes response A
   `(14>>4)+1=1` and impulse `(14>>2)+1=4` at `$81:93F9/9428`. Duration37 is
   below120, so A is cleared at `$81:9474`; B stays0. The sample-high flag`$80`
   is absent. The cartridge option check does not select its alternate branch,
   and rider selector`$0FF9=2` takes the opponent path. Explicitly, `$81:94A8`
   loads `$77:0750`; bit`$0008` tested at`$81:94AF` is clear, so`$81:94B4`
   reads the nonzero opponent selector and bypasses the`$132B` replacement at
   `$81:94B9`. Native context must guard that clear bit and opponent identity.
   Negative sentinel causes
   count/duration to clear at `$81:94C7/94CA`, **preserving vx448 and vy222**.
   This is not the continuous-contact vertical reset. The static coefficient
   transform at`$81:950C–960D` never executes during primary1534–2999.

Common tail `$81:97E4–982B`: the primary flags bypass special correction.
Vertical correction is at least horizontal correction0, so horizontal correction
is zeroed. Save incoming y to`$0EEF`, then write `u16(y-penetration)` to`$A7`
(axis selector0); save incoming x to`$0EED`. Horizontal axis0 does not adjust x.
At1617, penetration5 yields corrected y860. At1618, penetration10 yields y858
and continuous response sets vy0. Saving corrected y as previous y would change
future movement-angle calculations and is demonstrably wrong.

The caller publishes duration/marker/selection first, then response channels,
count and saved coordinates, then corrected positions and velocities, previous
count, selected high byte and descriptor. Player corrected position/velocity
stores are`$81:8E17,8E1C,8E22,8E28`; opponent stores are`$81:8F6B,8F70,8F76,8F7C`.
This order matters for evidence interpretation even when an explicit native
rider record permits grouping the final assignments.

## Limits and independent review target

The primary contract is implementable with explicit guards. It does not recover
negative-angle ramps, reflected terrain, horizontal collision, supported upward
velocity, first/second probe support, special tiles/modes, a second long landing
angle bucket, general coefficient transforms, or recontact from a different
trajectory. Those paths must be rejected or separately researched if a future
case reaches them. Do not infer their formulas from these pass counts. The
coarse angle helper is described at its sole tested input, not claimed generally
validated. RNG is not read by these executed response paths. Option flags are
read once but take no effect-producing branch; a different mode is unsupported.

An independent reviewer should regenerate the primary, reproduce both models,
and choose a fresh contact variation or crafted boundary. Native M2-01 must
still generate all incoming positions, velocities, poses, input and phase from
its one initial state, and pass its unchanged primary/withheld movement outputs.
No frozen withheld output was read during this research.

## Reproduction and hashes

Run in the isolated worktree. Baseline `doctor`, `bootstrap`, `build --preset
lab-debug` and `test --suite synthetic` passed (211 checks at dispatch base).
The unchanged C++ sampling probe reproduced29,320 words using R-0010's primary
capture and static content, report`artifacts/m2-01a-contact/sampling-baseline.json`.
Regenerate those old inputs with R-0010 if the old worktree is unavailable.

```sh
python3 -m tools.unirally_lab.native.contact_research.capture --out artifacts/m2-01a-contact/primary
python3 -m tools.unirally_lab.native.contact_research.capture --manifest tests/manifests/native/contact-research/contact/release-1570.json --out artifacts/m2-01a-contact/release-1570
python3 -m tools.unirally_lab.native.contact_research.capture --compact --from-frame 1534 --to-frame 2999 --out artifacts/m2-01a-contact/primary-full
python3 tools/project.py content decode --manifest tests/manifests/native/contact-research/contact/tile-tables.content.json --out artifacts/m2-01a-contact/content
python3 -m tools.unirally_lab.native.contact_research.summarize --access artifacts/m2-01a-contact/primary-full/access.json --report artifacts/m2-01a-contact/primary-relations.json
python3 -m tools.unirally_lab.native.contact_research.summarize --access artifacts/m2-01a-contact/release-1570/access.json --report artifacts/m2-01a-contact/release-relations.json
python3 -m tools.unirally_lab.native.contact_research.preprocess --sampling-access ../m2-01/artifacts/m2-01/sampling-access/access.json --contact-access artifacts/m2-01a-contact/primary-full/access.json --pose-content ../m2-01/artifacts/m2-01/content-expanded --tile-content artifacts/m2-01a-contact/content --report artifacts/m2-01a-contact/preprocessing.json
python3 -m unittest discover -s tests/tooling -p test_native_contact_research.py
```

Each capture directory saves exact expanded argv in`command.json`;`access.json`
also contains the full regeneration command. Primary focused capture took9.4s,
full capture52.8s, variation9.2s on this host; total session/account usage is
not metered. The captures have zero unresolved stores, complete nontruncated
watches, no ring overflow and no address-resolution conflicts. Focused primary:
778,312 instructions/388,664 accesses/1,038 unresolved accesses. Full primary:
27,090,754 instructions/13,466,478 accesses/28,223 unresolved accesses.
Variation:777,382 instructions/387,955 accesses/1,121 unresolved accesses.
Unresolved accesses are not treated as observed values.

| Artifact | SHA-256 |
| --- | --- |
| Primary focused access | `6e5144706276c3a3293711cc3c773c69dd479b4d3c91dba35b89ad3209fd99eb` |
| Primary full access | `8c4d09e6ed11f99ab496b90aebcb286826413b619a7e102735ed5b6b06aacc96` |
| Release variation access | `82785628bba5514773779e70579daeb40e0ec77c9e1f214f3bdde9ba78c903d3` |
| Primary relations report | `e9f4ac114435bac9a8410f4b5c72722dc1ff17c029dbf2c7ab7c52d1bd03c69e` |
| Variation relations report | `e612e526176ca754ef8368c5c476466370a2e675223e74609a675a2ccf31fb48` |
| Preprocessing report | `ea7c31715d6c261187e851dc256f7094a95c827f774519ee279b9d54e5ed8cfa` |

Both primary captures retain sample digest
`72f618f2f7e3416eac64d38f882471b1a9ebee25018ed76143360a92cdd99b1f`
and final-state SHA
`0f3cc38bd5d644012f0c7afbbfaaec772cf3df5b520cbc0c5c7312d84ab322e3`.
Variation sample digest starts`d8bcd6fd65324852`; complete identity is in its
samples/report files. The manifest remains preregistered without added expected
outputs. The core library SHA is build-specific and unchanged on this host:
`e24fd24929535831…`.

Tool development notes: first summarizer attempt used incorrect frame-object
key names and stopped before comparisons. The next attempt exposed2,889 angle
mismatches from assembling an unwatched high-byte update into an intermediate
word; comparing the observed low byte fixed that capture interpretation. No
original expectation changed. All other relation and preprocessing checks passed
on their first valid execution. Authored tests cover duplicate-byte watch
coalescing, incomplete capture rejection, marker-only samples, wrapped height
subtraction, tie metadata, unsupported geometry rejection, saturation and
pre-correction publication. Deliberate changes to expected counter10 or saving
corrected y are detected. Independent reviewer variation remains pending.

## Native interface proposal for coordinator review

Reuse `CollisionPoints` and `TrackSamples` from`track_sampling.hpp`. A proposed
`FlatContactContent` contains two immutable byte spans: column records and tile
flags. `summarize_flat_contact(content, points, samples, x, y)` returns a typed
summary of support, penetration, selected descriptor/high byte and angle; it
rejects the unimplemented geometry predicates listed above. Marker observation
remains the existing `observe_track_markers` call on the same raw samples.

Embed a `RiderContactState` member in the future rider record: unsupported count,
previous unsupported count, duration, previous uncorrected x/y, surface angle,
angle-sentinel flag, auxiliary flag, latest selected descriptor/high byte and
recontact flag. Position and velocity stay in the rider's shared kinematics;
response A/B and orientation impulse stay in its shared orientation state.
Contact must preserve/update those fields, not own duplicate shadow copies.
Use a temporary `ContactMotionInput`/`ContactMotionResult` value to pass current
x/y, velocities, previous x displacement and orientation channels across the
component boundary until the combined RiderState interface is agreed. This is
an explicit function argument/result, not a persistent WRAM scratch bank.

`resolve_flat_contact(contact_state, motion_input, summary, context)` returns
corrected kinematics/orientation values. Context supplies phase`$0300`, rider
identity and supported mode predicates; phase`$0302` used by track progress is
a distinct field. Recontact's arithmetic should compute its coarse-angle
category from actual displacement differences. Do not use frame1617 or the
observed coordinates as a dispatch condition. The recovered category accepts
the flat, nonnegative-displacement sentinel branch; a different category returns
an explicit unsupported-domain result pending research. In particular, compare
the computed surface/coarse-angle difference in five-unit steps, preserving the
original stop-before-storing-zero angle endpoint. The original generic helper
is not replaced by a coordinate lookup.

Call order: integrate motion → publish new collision pose → expand points →
sample track → observe markers/preprocess samples → resolve contact for each
rider → retain contact outputs for next motion phase. Sampling and collision
use current motion output, whereas recontact compares to the saved prior
**pre-correction** positions. Serialization belongs to the later integrated
rider state and must preserve contact counters, positions and orientation
impulse without struct padding.

Final clean-source regression at`f979f0e0bd13c2c4ba709cd3a69879f9ecbf2160`:
218/218 checks pass, including206 Python tests and all existing C++ checks;
report`artifacts/m2-01a-contact/final-synthetic-fixed.json`, SHA-256
`2a0fb2f5b293b41a66840f61b2847b0786e0358b56a2f62292b21c8738a47f14`.
The prior import-path failure is recorded in the handoff. A final persistent
state audit corrected an earlier sentence that said both response channels
were always zero: B is2 during opponent unsupported1590–1613 and is preserved.
The documented update formula already preserved unsupported response state;
no formula, capture, expectation or pass count changed with that correction.

## Native contact component (coordinator-authorized continuation)

The coordinator authorized `src/core/flat_contact.*` and its isolated probe after
independent reproduction of the research contract. `flat_contact.hpp` implements
the interface above: `RiderContactState` holds contact persistence, `ContactMotion`
is an explicit shared-motion input/output value, and `ContactContext` separates
phase0300, mode, rider identity and cartridge options. Existing sampler/progress
interfaces are unchanged. The function validates unsupported predicates before
publishing any mutation, including the cartridge option bit and landing category.

The coarse landing helper executes bounded repeated subtraction and tests the
first five-unit bucket; it contains no frame number, observed coordinate tuple
or table of per-frame outcomes. The response-magnitude branch also requires
`3 <= previous_x_displacement < 32`, keeping the original successful lower
branch of the response-A cap comparison. A different category, displacement
quadrant, response magnitude, long airborne duration or option/player path is
reported unsupported. The temporary response-A value is legitimately omitted
because this supported path always clears it before publication. Orientation
impulse uses `(previous_x_displacement >> 2) + 1`; the authored different-tuple
case proves a result other than the observed original impulse4.

The C++ probe performs native pose expansion and track sampling, then native
sample preprocessing/reduction and contact response. Only incoming motion and
persistent state are captured per call. All24 output values per call are
compared to the original: corrected x/y, velocities, response A/B, impulse,
count/prior count/duration, previous uncorrected x/y, surface angle, angle flag,
auxiliary flag, selected descriptor/high byte, recontact flag and six summary
values. Primary2932calls give**70,368 matching values**; release1570 variation
86calls gives**2,064 matching values**, in both debug and sanitizer builds.
This still is not autonomous native gameplay: the incoming per-call position,
velocity, pose, phase and persistent state come from the original for this
component experiment.

The native-input captures add explicit watches for phase0300, auxiliary flag
and cartridge options to the earlier compact watch list. The original reads the
option byte every frame; the probe requires a known unchanging observed value
within that frame rather than inventing zero. Phase is the known prior write
at`$83:CCED` before contact, not inferred frame parity. Primary sample/final
hashes remain identical. Capture/probe commands:

```sh
python3 -m tools.unirally_lab.native.contact_research.capture --compact --from-frame 1534 --to-frame 2999 --out artifacts/m2-01a-contact/native-primary
python3 -m tools.unirally_lab.native.contact_research.capture --compact --manifest tests/manifests/native/contact-research/contact/release-1570.json --out artifacts/m2-01a-contact/native-release
python3 tools/project.py build --preset lab-debug
python3 -m tools.unirally_lab.native.contact_research.probe --access artifacts/m2-01a-contact/native-primary/access.json --pose-content ../m2-01/artifacts/m2-01/content-expanded --tile-content artifacts/m2-01a-contact/content --probe build/lab-debug/tests/native/contact_probe --report artifacts/m2-01a-contact/native-primary-debug.json
python3 -m tools.unirally_lab.native.contact_research.probe --access artifacts/m2-01a-contact/native-release/access.json --pose-content ../m2-01/artifacts/m2-01/content-expanded --tile-content artifacts/m2-01a-contact/content --probe build/lab-debug/tests/native/contact_probe --report artifacts/m2-01a-contact/native-release-debug.json
python3 tools/project.py build --preset lab-sanitize
local/toolchain/cmake-3.31.10-darwin-arm64/bin/ctest --test-dir build/lab-sanitize -R '^contact_' --output-on-failure
```

Repeat each probe with`build/lab-sanitize/tests/native/contact_probe` and a new
report path. On another host use that bootstrap's ctest path. Existing content
regeneration commands are above/R-0010; no old worktree is required if paths are
adjusted to regenerated inputs. Each probe report records exact source/diff,
input hashes, native executable hash, first divergence and output artifact.

Three authored C++ test groups exercise sample marker exclusion, signed-byte
winner initialization, equal-depth metadata ordering, wrapped byte-height
subtraction, count saturation/duration wrap, phase gating, preserved airborne
channels, pre-correction position order, non-original landing tuple/impulse,
zero-displacement loop termination and eleven rejected response predicates.
Rejected updates must leave state unchanged. Invalid geometry and missing
content are tested separately. No expected original value was changed during
implementation; the first valid native primary/variation executions matched.

The independent research reviewer found that a reversed frame range could
produce a vacuous pass. `summarize.calls` now rejects noninteger, empty/reversed,
negative and inconsistent-count ranges before iteration; the reviewer fixture
returns exit3/status invalid. An authored regression covers these cases. Valid
research checks are unchanged; this fixes evidence validation, not gameplay.
Native review and full-game integration remain separate required gates.

## Clean native candidate evidence

Candidate `d031a0eed7f0cb8895ae9b78052fcaac0c29c05c` passed all222 synthetic checks (207 Python tests and existing/new native checks). Both debug/sanitizer original comparisons pass with the source clean. Sanitizer contact CTest groups pass3/3 without diagnostics.

| Report | SHA-256 |
| --- | --- |
| `native-clean-suite.json` | `ed6593e701386b6745fac5a8a628b1306f8ecd68ca44517df02292a77546b098` |
| `native-clean-primary-debug.json` | `e4cf59489f9f5dfa122d3f75f31eedd65d1f67422030412124419feb2aae3979` |
| `native-clean-release-debug.json` | `b33663d5e15081c40358c94e8b10b2023132e136f6d6cc5d8dfdabf8121a4852` |
| `native-clean-primary-sanitize.json` | `095a50b2e1c09d0193635fb28ba44964c896ce77a59f6eedb85f359f0ef725e5` |
| `native-clean-release-sanitize.json` | `4fe2c97790c5239dfd2ac5dc282ef2039672b7971ac61dd050842c7b901b3e51` |

`native-primary/access.json`: SHA-256 `06d4862939c184e535669b741b82040193f248a57c8d28f415d9378e8354b303`.

`native-release/access.json`: SHA-256 `f51b63f9682a50ab86c6d5de9d564eae7ddda8222b52024d54f3b3db48968cc8`.

Native primary outputs are byte-identical in debug/sanitizer: SHA-256 `6bb5c2c6d19a7101cb0691439978b282c1433ef199d1cf27b94b89dcbb77bc12`.

Native release outputs are byte-identical in debug/sanitizer: SHA-256 `8e3fd846092605a44926e3dda94e842ad3204b3383a32dff12da23db563e3840`.
