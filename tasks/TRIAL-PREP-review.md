# Trial process preparation — independent documentation review

- Candidate: `bc638f6991c149a302a85d5cd69af9874bed4368`
- Reviewed range: `15237954fe636ecf83cf105186570207593c900b..bc638f6991c149a302a85d5cd69af9874bed4368`
- Review branch/worktree: `review/trial-process-prep`,
  `.worktrees/trial-process-prep-review`
- Reviewer: fresh OpenAI `gpt-5.6-sol`/medium documentation reviewer
- Verdict: **approved without a material finding**

## Assessment

The candidate consistently assigns M4-12 recovery and native implementation to
one Astra/medium primary and requires that primary to launch a fresh, explicit
Sol/medium reviewer in an isolated checkout of an immutable candidate. The
reviewer owns its report and independent cases, cannot silently edit or approve
the implementation, and the primary owns corrections, re-review, exact-candidate
integration checks and verified private-origin synchronization. This is a
workable non-circular ownership path.

The M4-12 exception is narrow and consistent across AGENTS.md, D-0004, D-0006,
the workflow, state, registry and handoff. It waives the 20-percentage-point task
cap only for M4-12 while preserving usage sampling and the final 20% weekly
review/recovery reserve. The preparation-time 98%-used observation is explicitly
stale, one available reset is not treated as authorization, and startup below
the reserve permits recovery work only. No purchase, provider fallback or reset
redemption is implied.

Acceptance remains materially demanding: the primary must freeze the expanded
reference contract before tuning, preserve the accepted short-window evidence,
close every future-affecting dynamic input, match both riders through the
predeclared 200-update interval, exercise a new relevant transition, pass two
reviewer-owned relevant variations and fresh-process restores, and retain broad
DRAGSTER/content/presentation regressions. A withheld failure used for tuning
loses withheld status and must be replaced. Partial research and the old
51-frame match cannot be relabelled as native acceptance.

The documented startup commands are real: `rom inspect --expect` accepts an
omitted `--path` through the ignored ROM locator, and all seven named focused
test modules and linked manifest/evidence/source-guide files exist. The new
ZOOM ZOO native compare/restore commands are explicitly identified as
unimplemented work that M4-12 must add before review, rather than advertised as
current capability.

## Checks

- `git rev-parse HEAD` reproduced the exact candidate above; the accepted base is
  its parent and current `origin/main`.
- `git diff --check 15237954fe636ecf83cf105186570207593c900b..bc638f6`
  passed.
- Static path and CLI-help inspection confirmed the startup recipe and focused
  module inventory.
- The candidate changes documentation and Codex configuration comments only;
  no gameplay source, frozen manifest, fixture or research-evidence file changed.
- Game, build and test suites were deliberately not run for this documentation-
  only review. Their historical results were not counted as candidate gameplay
  validation.

No candidate file was changed by this review.
