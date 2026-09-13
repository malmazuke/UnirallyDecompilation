# M4-15 independent review

Initial candidate: `e038a5b1a3fe9e1064024eb51b1749400319431e`.
Accepted corrected candidate: upstream `6faff68`, represented by equivalent local
cherry-pick `f11fd19`.
Reviewer: fresh OpenAI Sol/medium session in
`.worktrees/m4-15-review`, branch `codex/review-m4-15-race-completion`.
Startup shared weekly usage was 45% used; task allocation was 38% used. Preserve
the final 20% reserve; no reset, purchase, provider switch, or child dispatch.

## Preregistered cases

These cases were fixed before inspecting or executing the candidate native
implementation. Their exploratory horizon is 11999. If a case completes in the
original, only its final segment endpoint will be trimmed to exactly 240 updates
after player finish before the two acceptance captures and freeze. Controller
buttons before that endpoint will not be tuned from native results.

1. `zoom-zoo-race-review-delayed-turns.case.json` delays every one of the
   primary's twenty direction changes by three updates. This changes sixty
   steering updates across all three laps while preserving the route family.
   It is intended to discriminate boundary timing, contact, progress ordering,
   lap transitions, and finish behavior rather than repeat an inert suffix.
2. `zoom-zoo-race-review-left-jumps.case.json` holds B throughout every Left
   segment and releases it throughout every Right segment. Each Left transition
   can therefore initiate a new jump. This changes thousands of controller
   rows and exercises jump/contact/landing state along the same complete route,
   while retaining the authentic seed and unmodified original opponent.

The choices use only the frozen primary controller manifest and documented
original controls. No native result or implementation detail informed them.

Original exploration disqualified case 2: through11999 the player never set its
finish flag, while the unchanged opponent finished at6488. Its final observed
`$0FCD` progress transition count was10; lap count is not part of the explorer's
compact row projection. The absent player finish flag is the disqualifier.
The failed fixed case and capture remain evidence and will not be evaluated
against native.

Before any native evaluation, the fresh replacement is
`zoom-zoo-race-review-early-jump.case.json`. It changes frames1681--1695 from
Left to Left+B and otherwise retains the complete primary steering timeline.
The interval is the independently accepted M4-13 support-loss/landing stimulus,
selected from historical project evidence rather than this candidate. It is a
material full jump and landing early in lap one, while limiting the perturbation
so the fixed later route can still test all lap and finish transitions.

## Results

Initial candidate `e038a5b` passes its independently recaptured primary through
6724, all565 bytes and465 restores, but both qualifying withheld cases fail.
Delayed turns first differs at2513 and early jump at2853, both in player
`throttle` (canonical offsets136--137): native accumulates `-16` one update
before the original after an inverted zero-speed reversal. Both cases remain
regressions.

Corrected implementation candidate `0dda676` was supplied after that finding
and applied to this isolated branch as `bc52a28`. Before inspecting or executing
its native behavior, two fresh fixed replacements are preregistered:

1. `zoom-zoo-race-review-early-turns.case.json` advances all twenty primary
   direction changes by three updates. It complements the retained delayed-turn
   regression and changes sixty steering rows across all laps, with the same
   timing/contact/progress discrimination in the opposite boundary direction.
2. `zoom-zoo-race-review-lap-two-jump.case.json` changes only4096--4110 from
   Left to Left+B. This initiates a fixed full jump stimulus near the start of
   the second repeated route cycle, materially separating it from the retained
   first-lap1681--1695 jump regression while preserving later steering.

Both replacements use only original case timing and historical B-jump behavior.
No corrected native output informed them. They will first explore the original
through11999; qualifying cases will be trimmed to player finish+240 and captured
twice before freeze and native evaluation.

Original exploration disqualified early turns: the opponent finished at6488
but the player had no finish through11999. Lap-two jump qualified at6484/6488.
Before any corrected native evaluation, the fresh replacement
`zoom-zoo-race-review-two-step-delay.case.json` delays all twenty direction
changes by two updates. It changes forty steering rows, samples different
alternating update phases from the retained three-update-delay regression, and
was chosen solely from the fixed primary and qualifying original timing family.

The two-step delay completes but ties at6488/6488, rather than retaining the
primary's player-win outcome, so it is preserved but not used as a qualifying
replacement. Before corrected native evaluation, the next fixed replacement is
`zoom-zoo-race-review-one-step-delay.case.json`: all twenty reversals are delayed
one update. It changes every route boundary and samples the remaining alternating
phase, again without any corrected native result.

## Findings

1. **Required correction — inverted zero-speed throttle ordering.** Both initial
   withheld cases diverged in player throttle after a direction reversal on an
   inverted selected tile with zero velocity. Native accumulated throttle one
   update early because it continued past original returns at `$82A9CC/$82AA29`.
   The retained regressions first differ at2513 (three-update delayed turns) and
   2853 (first-lap B jump), offsets136--137. Corrected by `0dda676`.
2. **Required correction — malformed finish-pose restore bounds and relations.**
   `e038a5b` admitted selectors up to160 and kinds through6 although reached kind1
   has48 entries and kind2 has88. `0dda676` fixes those bounds, but still admitted
   impossible inactive combinations such as `locked=1,kind=0` or
   `kind=1,locked=0`. A future finish can then select the wrong table or emit an
   active state that its own decoder rejects. Require the observed all-zero
   inactive tuple or active+locked kind1/2 with its per-kind selector bound.
   Corrected by `c0979ac`, included in `6faff68`.
3. **Required correction — checkpoint flag bounds.** `e038a5b` indexed the
   203-byte runtime tile-flag span in `update_zoom_checkpoint` before the existing
   tile bound check. A restored selected descriptor `0x03F0` produces tile252
   and an unchecked read. Corrected by `486a364` with a separate 20-byte authored
   test fixture and state-preservation coverage.
4. **Required correction — zero-lap unfinished state.** The decoder admits
   `laps_remaining=0,finished=0`. A later start-line crossing decrements the
   unsigned lap word to65535. Frozen rows establish
   `finished == (laps_remaining == 0)`; malformed restore validation must enforce
   that relation. Corrected in `6faff68`, together with the related finish-delay
   and active-pose implications.
5. **Required correction — jump pending gates before drive.** A fresh
   post-correction lap-two B case first differs at4099. Original retains player
   jump pending1/phase0 while native consumes it to pending0/phase1. Authenticated
   instruction evidence establishes the first return at `$82A8E8` from selected
   high bit `0x80`, and a second return at `$82A8E0` from leading support at4159.
   The earlier surface-mode hypothesis was rejected: common `$818687` clears
   `$0F41` before the jump logic. The uncorrected motion/pose divergence moved
   native finish roughly eleven updates early and hit the result-load guard at
   6713. The frozen case remains a regression and passes `6faff68`.

Corrected candidate `6faff68` authenticates the actual jump gates: selected-high
bit `0x80` at `$82A8E8` causes the first return, and leading support at `$82A8E0`
causes a second related return later in the same retained regression. Before
executing this candidate, the fresh replacement
`zoom-zoo-race-review-mid-neutral.case.json` is preregistered. It replaces
frames3409--3423, the first fifteen updates of a long Right leg, with neutral,
then resumes the exact primary route. This is a material speed/throttle/contact
perturbation in a different lap and input family from every tuned regression;
its timing was selected without candidate output.

The first-finish animation queue branch is acceptable in the declared bounded
domain. The reference reader verifies an empty pending queue from the preceding
WRAM state for both riders on every first animation call; accepted seeds and
restores are those frozen rows, and a new original case with a pending entry
fails before native evaluation. No reached player gameplay writer exists. The
claim does not include arbitrary player announcement-queue restoration.

## Final verification

- Independent app-debug build and focused validation pass: 21/21 CTests and 2/2
  race-audit Python unit tests.
- Independently recaptured primary originals finish6484/6488 through6724. The
  final candidate matches all565 bytes for5,075 updates in two native processes
  and465 fresh restores; row hash `757f629b...`.
- Fresh qualifying one-step-delay originals finish6479/6488 through6719. The
  final candidate matches all565 bytes for5,070 updates and462 restores; row
  hash `2f3c0f47...`.
- Fresh qualifying mid-neutral originals finish6482/6488 through6722. The final
  candidate matches all565 bytes for5,073 updates and455 restores; row hash
  `651cdd23...`.
- All retained regressions pass the final candidate with full restores: delayed
  turns5076 updates/451 restores; first-lap B jump5074/466; lap-two B jump5075/465.
- Original-only nonqualifiers remain tracked: Left+B every Left segment and
  three-update early turns do not finish by11999; two-update delayed turns ties
  6488/6488 instead of retaining the player-win outcome.
- Producer-side independent gates reported for exact upstream `6faff68`: 405
  debug and405 sanitizer checks, the legacy M4-12--14 matrix, denied-ROM/repo
  autonomy, primary, and both fresh cases pass. Those broad runs are not counted
  as reviewer-independent results.

The freeze helper copied the primary-specific phrase “236 updates after opponent
finish” into every review freeze. The row contracts and exact horizons are
correct and were frozen before native evaluation. The actual opponent
continuations are231 updates for one-step-delay and234 for mid-neutral; this
review keeps the immutable freeze files and records the accurate values here.
The helper correction is metadata-only and must compute the value per case. Its
proposed exact delta was reviewed and accepted; final review of its committed
diff remains pending.

Closeout shared weekly usage was52% used, preserving the required20% reserve. No
reset, purchase, provider switch, or child dispatch occurred.

## Disposition

Approve corrected candidate `6faff68`. All five material qualifying variations
and the primary now match the original through their complete race and exact
240-update player-finish display, including restore coverage. The implementation
corrections resolve every review finding. The declared domain ends before
result-screen loading, and arbitrary player announcement-queue restoration is
outside it; both limits are explicit and supported by the frozen entry checks.
