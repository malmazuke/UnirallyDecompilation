# M4-16 preparation documentation review

- Reviewer: fresh independent `gpt-5.6-sol`/medium session.
- Candidate: `f5a4f34afd2d50c2966b7a76f071ed204bd7ff85`.
- Base: `8bc2e71997bd9dd0a513326fce21ab92c076140d`.
- Review branch/worktree: `codex/review-m416-prep`,
  `.worktrees/m4-16-preparation-review`.
- Scope: documentation/configuration preparation only; candidate files were
  treated as immutable. No gameplay implementation, reference capture or native
  validation was performed.

## Decision

**Approved. No material findings.**

The task, handoff, state, plan, registry and policy records consistently define
one product-sized M4-16 outcome: native ZOOM ZOO initialization, an interactive
complete race in the existing desktop frontend, an authenticated winner/loser
result, restart without stale state and later pack-only relaunch. Coupled
initialization, gameplay, presentation and result dependencies remain inside the
task. M4-16 does not accept all of M4, authorize a milestone tag or dispatch
M4-17.

The acceptance contract closes the seed and headless shortcuts. Production must
construct the initial state from authenticated static content and explicit
scenario parameters by recovered native algorithms; the M4-15 end-1649 seed,
dumped runtime state, later captured repairs, original CPU and emulator execution
are forbidden. Scripted controller streams remain validation inputs only. A
visible app race must use real press/release, direction, jump and focus-loss
events through result and restart, and the reviewer must independently exercise
live controls and the result/restart boundary. A terminal run, replay, autopilot
or recorded demonstration alone cannot satisfy the outcome.

The exact evidence remains bounded and independently testable. The primary must
match every declared future-relevant byte for both riders from the authenticated
initialization boundary through finish, result transition and stable result,
with a complete reached-producer inventory and zero captured dynamic native
inputs. Fresh-process restores span initialization, start, escape, lap, finish,
result and restart. The reviewer chooses at least two material untuned
start-to-result variations after candidate freeze, freezes each original twice
before native evaluation and retains both player-win and player-loss coverage.
Any case used for correction becomes a regression and needs a new untuned
replacement. These requirements prevent a narrowed state declaration or one
fixture-specific trace from substituting for the product claim.

Frontend acceptance preserves the established product boundary. Fresh isolated
extraction/build, wrong-ROM and corrupt-pack failures, ROM-absent ZOOM ZOO
relaunch, and selectable/playable DRAGSTER are explicit. Visual evidence covers
start, reversal, steep contact, lap, finish and both result outcomes. Audio stays
out of scope, and the existing rider-art fallback may remain only when documented,
no worse than the accepted DRAGSTER standard and independently shown not to
obscure gameplay state. The task does not imply pixel, complete-art or audio
fidelity.

The command inventory distinguishes implemented tools from M4-16 work. The
accepted M4-15 audit preflight and identity ledger are available for reuse;
M4-16 initialization and frontend/result interfaces are explicitly described as
unimplemented by this preparation and must extend existing tools deliberately.
The ledger cannot replace fresh references, reviewer cases, sanitizers, merge
checks or final-tip CI.

D-0004, D-0006, AGENTS and the workflow consistently assign direct
Astra/medium ownership and automatic fresh Sol/medium review in an isolated
exact-candidate checkout, with correction and re-review handled without user
relay. The M4-16 exception waives the 20-point cap while preserving the final
20% weekly reserve. It requires fresh usage sampling and authorizes no reset,
purchase, provider switch or M4-17 continuation.

## Checks

- Inspected all 13 changed paths and the complete diff against the accepted
  base, including M3-04/R-0017 product limits and M4-15/R-0034 review boundaries.
- `git diff --check 8bc2e71..f5a4f34` passed.
- The candidate's 130 local Markdown link-target and nine fragment-anchor checks
  were reviewed as preparation evidence; changed cross-document references were
  inspected and no broken target or contradictory task boundary was found.
- `.codex/config.toml` parses; its only change is a comment and the model defaults
  remain unchanged.
- The changed range contains no source, tests, fixtures, captured content or
  frozen gameplay expectations.
- `origin/main` independently resolved to the accepted base, and GitHub Actions
  run `34785933369` completed successfully for that exact SHA on macOS and Linux.
- Gameplay/build suites were not run for this documentation-only candidate.
  Historical M4-15 results were not counted as M4-16 gameplay validation.

No candidate file was changed by this review.
