# R-0034 — ZOOM ZOO race completion from the authentic seed

M4-15 candidate; independent review and final gates remain pending.
PAL ROM `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`,
core `e59bf88d4fc922c9fe3b5438e65ff3a6909d24e1628f0f87141c8de17699a91b`.

## Original feasibility and frozen outcome

The old continuous Right scenario went against the initial track direction:
its progress count decreases, player X remains 9200–14281 through11999, and
only the opponent finishes (6488). Continuous Left reaches count23 then stalls
at a direction reversal. Original-only marker-guided Left/Right completes the
race (player6484/opponent6488); adding marker-selected B also completes
(6485/6488). These are meaningful original strategy families, not native tuning.
The successful primary has21 fixed direction segments. Native receives that
fixed timeline, never original markers as later dynamic input.

Reference freeze `47c9ce4` precedes native implementation. Four fresh fixed
original captures A–D agree on5,076 whole-WRAM hashes, end1649–6724; C/D also
retain cartridge RAM and project canonical state. The initial lap count4 includes
an initial start-line crossing, then three laps. Player crossings are1675,
3208,4840,6484. The last sets finish; opponent finishes6488. The full240-update
player finish display leaves236 updates after the opponent finish. Positions
settle near the finish and poses continue. The next result-screen load is
outside this simulation domain; frontend/rendering/audio are not claimed.
No fallback was selected. This proves race completion from end1649, not native
race-start initialization or a general ZOOM ZOO product.

The newest freeze is `zoom-zoo-race-primary-v4.freeze.json`:565 bytes,
rows SHA-256 `757f629b518a9593074c72a92c6bd01bed569b048a740f8ec9133711575c32d1`.
The original423-byte sustained prefix is retained except task-format magic
`URZZ0003`. Additive discoveries are explicitly retained as earlier freezes:
517 initial lap/result bytes;529 with camera feedback;549 with shared checkpoint
first-seen flags;565 with finish collision-pose selectors. No old M4-12–14
contract or expectation was replaced. Each addition was frozen before tuning
its producer, using the already frozen matching original processes.

## Recovered dependencies and ordering

| Producer | Evidence and native meaning |
| --- | --- |
| Left/Right route | Initial marker bit`0x4000` indicates Left to the original AI. Existing signed motion/reflection equations already reproduce the selected direction changes. No new track geometry was invented. |
| Lap/checkpoint | `$818050–82B6` consumes prior selected tile20, checks ordered checkpoint tags and start-line latch, stores timer digits, subtracts earlier non-sentinel lap times, decrements laps, and writes finish at zero. `$8186EF–86F5` decrements display countdown first. `$81CA38–CA71` clears shared first-seen flags and suppresses the first opponent checkpoint display to2. |
| Progress publication | At3219 the limiter reads player127 at sequence1650, player progress writes128 at2212, opponent limiter reads128 at2869. Publish progress after each rider's motion/pose, preserving player/opponent order. Earlier scenarios did not discriminate this order because player progress stayed behind. |
| Camera feedback | `$819FB0–A16D`, `$81A520–A53F` update lookahead and camera before contact correction. `$82ACAE–AD7A` computes visibility after contact. `$1225` first becomes1 at3002, and `$82A705–A71C` changes next-update speed by3. This is gameplay feedback, so it is reconstructed and serialized. |
| Player leading reward | `$829B87–9BBD` emits event14 into the player queue via`$81C59C`; it must not enter the existing opponent queue. Event14 has class255 and clears both player boosts in the landing producer. All reached player reward-consumer paths have no player boost/feature-state writer in this full audit. |
| Opponent announcements | Last-lap event15 and finish result events37–39 have authenticated class255. Preserve the existing opponent queue bytes/cursors/cooldown and enqueue in source order. They do not add learned rewards. |
| Finish continuation | `$83E803–E83A` counts player finish updates. `$83E8E0–EC13` overrides each finished rider's controls, applies signed ten-unit slowdown on two of three phases, chooses finish animation, and announces result. `$829909–9945` brakes supported riders by24 and returns before publishing previous-brake while speed is outside the asymmetric low-speed interval. |
| Finish collision poses | `$828953–89C2` reads authenticated `$17:C7C8` tables and advances serialized selector/kind/lock/active state. Pose override remains part of collision geometry; it is not discarded as presentation. |

Native functions are in`movement.cpp`, task state in`zoom_zoo_movement.hpp`.
Camera position uses world units, velocities/lookahead signed whole units,
4x horizontal comparisons and original wrapped words. The task only admits
Left/Right/neutral/B; unrecovered trick/brake controller commands fail closed.
Forced post-finish braking is internal original behavior.

## Continuous audit and bounded exclusions

`artifacts/m4-15/full-audit/authentication.json` verifies the expanded complete
controller timeline, including both ports and pre-seed history, before capture;
then all5,076 whole-WRAM samples against the frozen primary. The command is in
that artifact and the capture report. Audit covers92,743,600 instructions,
no unresolved stores, no non-ROM PCs, no resolution conflicts or dropped
resolutions. There are113,833 unresolved accesses across all subsystems, but
zero in the declared recovered producer regions (`dependency-audit.json`).
This is not a claim of complete audio or rendering recovery.

The new reference reader checks82 constant input words on every frame, including
camera scale/bounds, one-player mode, lap count setting and the old excluded
mode guards. `$1225/$1227` were removed from the old constant list because their
new serialized producer is recovered. Supported-ROM identity gates all static
inputs, including additive reward classifications and finish-pose tables.

The player announcement queue is output-only across ordinary racing in this
frozen case: reached consumers do not write gameplay boost/feature state.
There is one reached feedback gate at first finish animation: `$828959` can
query pending queue length while its active flag is zero. Both first animation
calls have zero pending entries; the reference reader explicitly checks this
branch invariant from the preceding end-state. Later calls bypass it through
the serialized active flag. A variation reaching a nonempty queue fails closed
as a new dependency requiring recovery; it cannot silently count as a pass.
Result text cycling`$0F03/$0F07/$11FD`, audio and text drawing have no new
simulation read in this declared domain. No captured runtime repair or CPU
fallback is used.

## Reproduction and pending review

Use the task checkout's real local/artifacts directories and hash-checked core.
`zoom_zoo_race_explore --case CASE --horizon H --keep-wram --core CORE --out A`
captures a fixed original timeline; repeat as B in a fresh process.
`zoom_zoo_race_reference --reference A --repeat B --out FREEZE` freezes original
state only. `zoom_zoo_race --reference A --repeat B --contract FREEZE --binary
build/app-debug/src/core/zoom_zoo_runner --content-dir CONTENT --out REPORT`
compares every byte twice and fresh-process restores. The primary uses C/D,
`zoom-zoo-race-primary-v4.freeze.json`, horizon6724 and task content directory.
The last command writes an ignored identity-bound validation ledger. Audit
preflight and WRAM-authentication mutations pass;21 CTests and8 focused Python
checks pass. Initial diagnostic native comparison matches all565 bytes.

A preliminary465-restore run passed functionally while source validation was
being edited; it is not exact-source acceptance evidence and is superseded by
the final candidate run. Independent fresh Sol review, untuned cases, broad
regressions/sanitizers, denied-access execution and merge/remote CI are pending.
