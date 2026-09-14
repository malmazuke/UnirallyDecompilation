# Next session — resume incomplete M4-16

**M4-16 is incomplete and unaccepted.** The user requested a committed handover
because usage was nearly exhausted. This is a user-requested pause, not task
acceptance; do not continue automatically or dispatch M4-17.

## Resume location and identity

Use `.worktrees/m4-16-playable-zoom-zoo`, branch
`codex/m4-16-playable-zoom-zoo`, not main for implementation. Main retains accepted
M4-15 gameplay and a documentation pointer. Latest behavior commit:
`ca4602597960426629ad743f92f788e84c01a175`. Later review/handover commits do not
change that behavior; inspect actual `git status`/`git log` before resuming.
Independent review `d8ec276db17640054831062e04b8e6d9f7f041c7` is integrated as
`60a1544`. Read [M4-16](M4-16.md), [review](M4-16-review.md),
[STATE](../docs/STATE.md), AGENTS, AGENT_WORKFLOW, D-0004/D-0006 and
[R-0035](../docs/research/R-0035-zoom-zoo-playable-recovery.md).

Ignored `artifacts/m4-16/handover-closeout-2026-09-14.json` records final task/main
SHAs, remote verification, CI, commands, hashes and resource measurements. If
absent, recover refs with `git log`, `git ls-remote origin`, and `gh run list`.
The older `recovery-closeout.json` describes the previous 82% checkpoint only.

Primary is OpenAI Astra/medium; reviewer is Sol/medium in separate checkout
`.worktrees/m4-16-review`. Preserve independent review and isolated ownership.
Starting weekly usage was57%; the latest handover sample is94% used. The user
previously overrode percentage limits to continue, then explicitly requested
this handover. No reset, credit purchase, paid fallback or provider switch is
authorized. Sample fresh usage on a user-requested resumption.

## Current implementation and evidence

Experimental state is **URZZ000B / 742 bytes**. Historical accepted URZZ0001/2/3
remain readable. Current static pack is **v5 / 50 entries**:
`local/classic-crawler-two-tracks-v5.pack`. Do not overwrite frozen v2/v3/v4 packs.
The old default `local/classic-crawler-two-tracks.pack` is incompatible v2.
Private ROM locator: `local/rom-location.txt`; audited core:
`local/emulators/bsnes/bsnes/out/bsnes_libretro.dylib`. Identities are in R-0035.

Native fresh initialization, countdown, ordinary reflection/roll/held-roll,
player rewards and combination voices, pause/resume, result and fresh restart
are implemented in the experimental branch. Latest bounce recovery reaches
charge160 at5345 and completes6468/6488, stable6823; its original pair was frozen
before tuning in57f1b27. Native diagnostic matches every742-byte state across
6225 observations. Full app-debug and app-sanitize builds plus focused
`tests/native/zoom_zoo_trial_tests` pass at the latest behavior. Five final
complete-case diagnostics (primary, loss, late bounce, held X, shifted countdown
pause) also match6225 states; logs are `artifacts/m4-16/handover-diagnostics-retry`.
These are not full latest restore gates or playable acceptance.

Full gates on earlier immutable candidates:

- 7c3e3b6 compound X+R:742 bytes,6225 observations,751 fresh-process restores,
  repeat initialization and full restart (`compound-reverse-v11-full-7c3e3b6.json`).
- Independent239ae83 early compound X+R:742 bytes,6225 observations,739 restores,
  repeat initialization/full restart. Exact full app-debug build and focused
  tests pass. See review report and reviewer-owned ignored artifacts.
- Older broad debug/sanitize each405 no skips at9f7f3b4, and all28 historical
  M4-12–14 commands plus DRAGSTER gates at4f8aaad are historical evidence only.
  Latest full historical M4-15 and final merge/CI matrices remain due.

A chained build/test invocation masked an app -Wshadow failure atdb89d58. Review
caught it;239ae83 fixed the name, and explicit checked full builds pass. Always
check each command's return code. An initial handover diagnostic omitted
PYTHONPATH and failed import; the separately preserved retry passes. No failed
invocation is counted as passing.

## First recovery experiment

**Open high-priority review finding: generic opponent reward consumption.**
`update_zoom_landing_rewards` can queue events1–21 for the opponent, but legacy
`update_reward_queue` only consumes event1 or class255. An authentic-derived
pending event2 restore is accepted and then aborts at1722. Player100/opponent199
forged voice events now reject correctly; do not reject legitimate low trick
producers merely to hide the missing consumer.

Recover `$81C219-C2C9`: opponent uses `learned_weights[1]`, feature total,
weight halving with minimum1, horizontal reward and **full** vertical reward
(player uses half). Voice events>=72 bypass scoring; valid fixed producer ranges
are player72–87/opponent200–215. Plan a clearly labelled artificial original-only
queued-event2 probe twice before tuning, following the counter probe pattern;
reviewer did **not** start that probe after the user's stop request. This is an
internal mechanics experiment, never a seed-based playable acceptance fallback.
Then independently re-review the new consumer and latest bounce restore domain.

`zoom_zoo_wrong_way_probe` is an explicitly artificial original counter179
intervention at1997: both originals return120 and queue22. Its native one-update
742-byte check passes. Constant-direction and long-roll cases never finish by
7600; their inventories are labelled non-acceptance even though diagnostics match.

## Remaining product and acceptance work

1. Resolve opponent consumer and any further ordinary reached guards, then freeze
   an immutable candidate for fresh independent complete variations and restores.
   Latest bounce source/restore change has not had independent final review.
2. Finish result-loading/read classification against the durable
   [persistent-input ledger](../docs/research/M4-16-persistent-input-ledger.md).
   Zero unresolved stores is not zero unresolved reads. Fresh standalone restart
   intentionally discards tour progression/persistent best-record carryover.
3. Complete representative visual comparison and independent readability checks.
   Original scene identities are frozen in
   `tests/manifests/presentation/zoom-zoo-playable-v2.json`; private originals are
   `visual-original-a/b`, comparison `visual-7c3e3b6/comparison.png`. Extra original
   captures use the ignored `capture-visual-scenes.py`; authenticate ROM/core,
   timeline, whole memories and repeat PNG hashes when recreating.
4. Actual visible live controls through a complete race/result/restart, focus-loss
   clearing and independent reviewer live exercise remain missing. Gamepad hardware
   is untested. No fixed-mask/replay/terminal demonstration substitutes for this.
5. Clean isolated bootstrap/extraction, pack-only denied-ROM/reference/repository
   execution, negative controls, latest complete DRAGSTER/M4-12–15 regressions,
   debug/sanitizer, reviewed exact integration and hosted CI remain required.
   Do not merge experimental gameplay or create a milestone tag before acceptance.

The authored pause menu is RESUME / RESTART RACE. Down/Start deliberately invokes
shared fresh initialization; original Retire/tour flow is excluded, not emulated.
Input and retained art clear on restart. Resume remains original-comparable.
Core restart equality is tested; actual live paused restart still needs evidence.

## Launch and tool access

From the task checkout after a successful current build:

```sh
python3 tools/project.py frontend run --track zoom-zoo --pack local/classic-crawler-two-tracks-v5.pack --preset app-debug --report artifacts/m4-16/FRESH-live.json
```

For first extraction, add `--rom` with the private locator's ROM and a fresh pack
path. This remains a prototype with the open opponent reward bug.

Built-in CUA taps produced no sustained50Hz input in earlier live attempts.
A PID-restricted CGEvent helper (`artifacts/m4-16/live-key.swift`, compiled
`live-key`) is prepared but has **never been executed**. The desktop tool requires
explicit permission for this fallback; the question remains unanswered. The
usage override did not authorize CGEvent. Check for an actual subsequent answer
before using it. CUA documentation must be refreshed after compaction; Orca
runtime was unavailable in prior attempts. Do not ask again for routine git,
local tests or task-scoped source synchronization already authorized by AGENTS.
