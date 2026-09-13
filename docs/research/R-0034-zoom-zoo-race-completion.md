# R-0034 — ZOOM ZOO race completion from the authentic seed

M4-15 candidate; independent review and final gates remain pending.
PAL ROM `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`,
core `e59bf88d4fc922c9fe3b5438e65ff3a6909d24e1628f0f87141c8de17699a91b`.

## Original feasibility and frozen outcome

The old continuous Right scenario went against the initial track direction:
its progress count decreases, player X remains 9200–14281 through 11999, and
only the opponent finishes (6488). Continuous Left reaches count 23 then stalls
at a direction reversal. Original-only marker-guided Left/Right completes the
race (player 6484/opponent 6488); adding marker-selected B also completes
(6485/6488). These are meaningful original strategy families, not native tuning.
The successful primary has 21 fixed direction segments. Native receives that
fixed timeline, never original markers as later dynamic input.

Reference freeze `47c9ce4` precedes native implementation. Four fresh fixed
original captures A–D agree on 5,076 whole-WRAM hashes, end 1649–6724; C/D also
retain cartridge RAM and project canonical state. The initial lap count 4 includes
an initial start-line crossing, then three laps. Player crossings are 1675,
3208,4840,6484. The last sets finish; opponent finishes 6488. The full 240-update
player finish display leaves 236 updates after the opponent finish. Positions
settle near the finish and poses continue. The next result-screen load is
outside this simulation domain; frontend/rendering/audio are not claimed.
No fallback was selected. This proves race completion from end 1649, not native
race-start initialization or a general ZOOM ZOO product.

The newest freeze is `zoom-zoo-race-primary-v4.freeze.json`: 565 bytes,
rows SHA-256 `757f629b518a9593074c72a92c6bd01bed569b048a740f8ec9133711575c32d1`.
The original 423-byte sustained prefix is retained except task-format magic
`URZZ0003`. Additive discoveries are explicitly retained as earlier freezes:
517 initial lap/result bytes;529 with camera feedback; 549 with shared checkpoint
first-seen flags; 565 with finish collision-pose selectors. No old M4-12–14
contract or expectation was replaced. Each addition was frozen before tuning
its producer, using the already frozen matching original processes.

## Recovered dependencies and ordering

| Producer | Evidence and native meaning |
| --- | --- |
| Left/Right route | Initial marker bit`0x4000` indicates Left to the original AI. Existing signed motion/reflection equations already reproduce the selected direction changes. No new track geometry was invented. |
| Lap/checkpoint | `$818050–82B6` consumes prior selected tile 20, checks ordered checkpoint tags and start-line latch, stores timer digits, subtracts earlier non-sentinel lap times, decrements laps, and writes finish at zero. `$8186EF–86F5` decrements display countdown first. `$81CA38–CA71` clears shared first-seen flags and suppresses the first opponent checkpoint display to 2. |
| Progress publication | At 3219 the limiter reads player 127 at sequence 1650, player progress writes 128 at 2212, opponent limiter reads 128 at 2869. Publish progress after each rider's motion/pose, preserving player/opponent order. Earlier scenarios did not discriminate this order because player progress stayed behind. |
| Camera feedback | `$819FB0–A16D`, `$81A520–A53F` update lookahead and camera before contact correction. `$82ACAE–AD7A` computes visibility after contact. `$1225` first becomes 1 at 3002, and `$82A705–A71C` changes next-update speed by 3. This is gameplay feedback, so it is reconstructed and serialized. |
| Player leading reward | `$829B87–9BBD` emits event 14 into the player queue via `$81C59C`; it must not enter the existing opponent queue. Event14 has class 255 and clears both player boosts in the landing producer. All reached player reward-consumer paths have no player boost/feature-state writer in this full audit. |
| Opponent announcements | Last-lap event 15 and finish result events 37–39 have authenticated class 255. Preserve the existing opponent queue bytes/cursors/cooldown and enqueue in source order. They do not add learned rewards. |
| Finish continuation | `$83E803–E83A` counts player finish updates. `$83E8E0–EC13` overrides each finished rider's controls, applies signed ten-unit slowdown on two of three phases, chooses finish animation, and announces result. `$829909–9945` brakes supported riders by 24 and returns before publishing previous-brake while speed is outside the asymmetric low-speed interval. |
| Finish collision poses | `$828953–89C2` reads authenticated `$17:C7C8` tables and advances serialized selector/kind/lock/active state. Pose override remains part of collision geometry; it is not discarded as presentation. |

Native functions are in `movement.cpp`, task state in `zoom_zoo_movement.hpp`.
Camera position uses world units, velocities/lookahead signed whole units,
4x horizontal comparisons and original wrapped words. The task only admits
Left/Right/neutral/B; unrecovered trick/brake controller commands fail closed.
Forced post-finish braking is internal original behavior.

## Continuous audit and bounded exclusions

`artifacts/m4-15/full-audit/authentication.json` verifies the expanded complete
controller timeline, including both ports and pre-seed history, before capture;
then all 5,076 whole-WRAM samples against the frozen primary. The command is in
that artifact and the capture report. Audit covers 92,743,600 instructions,
no unresolved stores, no non-ROM PCs, no resolution conflicts or dropped
resolutions. There are 113,833 unresolved accesses across all subsystems, but
zero in the declared recovered producer regions (`dependency-audit.json`).
This is not a claim of complete audio or rendering recovery.

The new reference reader checks 82 constant input words on every frame, including
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
Result text cycling `$0F03/$0F07/$11FD`, audio and text drawing have no new
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
`zoom-zoo-race-primary-v4.freeze.json`, horizon 6724 and task content directory.
The last command writes an ignored identity-bound validation ledger. Audit
preflight and WRAM-authentication mutations pass; 21 CTests and 8 focused Python
checks pass. Initial diagnostic native comparison matches all 565 bytes.

A preliminary 465-restore run passed functionally while source validation was
being edited; it is not exact-source acceptance evidence and is superseded by
the final candidate run. Independent fresh Sol review, untuned cases, broad
regressions/sanitizers, denied-access execution and merge/remote CI are pending.

Candidate `e038a5b` passes the final source-bound primary comparison, all 465
fresh-process restores and the accepted sustained primary. Denied-reference
execution matches all 5,076 states; `/bin/cat` negative controls prove both ROM
and repository denial, and deleting required finish-pose content fails. Native
primary stored race totals match player 9,802 and opponent 9,810 centiseconds;
the authenticated original final frame displays WINNER.

## Independent review corrections

Review of e038a5b froze two original-completing material variations before native evaluation: every turn delayed three updates (player finish6485), and B during1681–1695 (finish6483). Both exposed player throttle at canonical136: first divergence2513 and2853 respectively. The drive source `$82A9CC/$82AA29` returns on inverted tile plus zero velocity before accumulating throttle. Native now preserves that early return; both entire565-byte traces pass diagnostic comparison. Full restores and fresh withheld replacements remain required. Finish-pose deserialization also now restricts kind1 selector to48 and kind2 to88, rejecting impossible kinds.

A further review finding exposed unchecked checkpoint flags access before the existing later tile check. A malformed selected descriptor0x03F0 produces tile252 against20 flags. The checkpoint now validates its own access before reading; an authored malformed-state test confirms rejection and unchanged input state. Broad results interrupted by this source correction are superseded and rerun on the corrected candidate.

Finish-pose restore validation is further restricted to reached state relations: inactive is all zero; active requires locked=1 and kind1 or2 with the corresponding selector bound. Review demonstrated that inactive+locked could otherwise index kind0, and inactive+kind1 could publish state rejected by the next restore. Six authored mutations cover both riders. This changes malformed-input rejection only.

The queue invariant is a reference-domain admission check, not a reconstructed arbitrary player-queue restore capability. All accepted seeds/restores come from authenticated rows. Each new case is rejected before native evaluation if its first animation has pending announcements; the full primary audit finds no reached player-queue gameplay writer during ordinary racing. Independent review accepts this finite-domain boundary.
