# Next session — resume incomplete M4-16

**M4-16 is incomplete and unaccepted.** After explicitly allowing continuation
past earlier usage boundaries, the user requested a committed handover because
usage was nearly exhausted. Final synchronization sample: 96% weekly used. Stop automatic
continuation; no reset, purchase, paid fallback or provider change is authorized.

Resume the existing checkout `.worktrees/m4-16-playable-zoom-zoo`, branch
`codex/m4-16-playable-zoom-zoo`. Latest behavior commit is
`ca4602597960426629ad743f92f788e84c01a175`; its detailed handover is committed at
`9f4c4239865681b7ecdb98d009ae50408c21c5ec` (later review-only corrections may follow).
Read that checkout's `tasks/NEXT_SESSION.md`, `tasks/M4-16.md`, review, STATE,
R-0035 and persistent-input ledger, then AGENTS/AGENT_WORKFLOW/D-0004/D-0006.
Inspect actual git status/tip; do not create a replacement task or use a captured
seed as native initialization. If the checkout is absent, fetch the existing
private `origin/codex/m4-16-playable-zoom-zoo` and restore ignored inputs privately.

Main retains accepted M4-15 gameplay. Experimental M4-16 now has742-byte state,
50-entry v5 static pack, native initialization/result, pause/restart and bounce
recovery. Latest debug/sanitizer builds and focused checks pass; five complete
case diagnostics match6225 states. Independent earlier candidate239ae83 passed
742-byte6225-observation comparison,739 restores and full restart. Latest bounce
changes still need full restores and independent review. Historical broad passes
are not latest-candidate acceptance evidence.

First open recovery is **generic opponent reward consumption**: landing can
queue events1–21, but the consumer only handles event1/class255. A legitimate
low-event restore can therefore fail on continuation. Do not reject reachable
producers to conceal this gap. The task handover specifies the original source
and next experiment. Live full race/result/restart, independent visual review,
clean bootstrap/denied-access and final regression/merge/CI gates also remain due.
The pending CGEvent fallback permission has no user answer; usage authorization
did not authorize that desktop fallback. No M4-17 or milestone tag.

Final refs, source/binary/pack hashes, checks, usage and synchronization are in
ignored task-checkout `artifacts/m4-16/handover-closeout-2026-09-14.json` and main
`artifacts/m4-16-handover-closeout.json`. The previous recovery-closeout.json is
historical82% evidence. Synchronization of this pointer is conditional until
those records verify the private remote refs and exact-main-tip CI. If missing,
use `git ls-remote origin refs/heads/main refs/heads/codex/m4-16-playable-zoom-zoo`,
`gh run list --branch main`, and `gh run view <id>`. No experimental gameplay is
accepted or merged by this documentation pointer.
