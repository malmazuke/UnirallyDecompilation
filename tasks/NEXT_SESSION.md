# Next session — resume incomplete M4-16

M4-16 was executed from dispatch `ede4c0b3b17269cd6984b21765efd98f11fe1085`
and remains **in progress, unaccepted**. Weekly usage reached80% on14 September
2026; D-0004 requires stopping new implementation and preserving final20% for
review/recovery. No reset, purchase or provider switch was authorized. Sample
fresh quota before resuming; below20% remaining do recovery only until restored.

The existing task branch is `codex/m4-16-playable-zoom-zoo`, with checkout
`.worktrees/m4-16-playable-zoom-zoo`. **Resume that checkout**, not a replacement
branch. Read its `tasks/NEXT_SESSION.md`, `tasks/M4-16.md`, `docs/STATE.md` and
`docs/research/R-0035-zoom-zoo-playable-recovery.md`, then AGENTS and workflow.
Use `git status` and `git log -5` there for the actual tip. Its private evidence
is under `artifacts/m4-16`; `recovery-closeout.json` records final refs, review,
commands/results, quota and time. Private originals/packs remain ignored.

If the checkout is unavailable, fetch the existing private origin and recover
`origin/codex/m4-16-playable-zoom-zoo`; do not use a captured dynamic seed as a
native initialization replacement. Final backup/pointer synchronization is
conditional until verified in the recovery closeout; recover missing status
with `git ls-remote origin refs/heads/main refs/heads/codex/m4-16-playable-zoom-zoo`
and `gh run list --branch main` / `gh run view <id>`.

Provisional work includes native initialization/countdown, a49-entry static
pack, frontend/result/restart, manual turns, announcement rewards and X/held
roll recovery. At candidate9f7f3b4, primary730-byte6225-observation comparison,
757 restores/full restart, independent held-X768 restores/full restart, and
405 debug plus405 sanitizer checks pass. Later review correction fe02cd8 adds
held-counter restore consistency; its actual validation belongs in the task
handoff/review. These are bounded experimental passes, not playable acceptance.

Remaining: ordinary control/producer closure, live complete race/result/restart,
independent live exercise, frozen visuals, clean bootstrap/denied access and
full latest regressions/merged CI. A CGEvent key-hold fallback authorization
request is pending in the execution conversation; do not assume approval.
No M4-17 dispatch, M4 tag or unaccepted gameplay merge. Main retains accepted
M4-15 gameplay (`8bc2e71`); this update only preserves the resume pointer.
