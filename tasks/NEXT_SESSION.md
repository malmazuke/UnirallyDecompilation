# Next session — resume incomplete M4-16

**M4-16 is incomplete and unaccepted.** The open high-priority opponent reward
finding is closed and independently approved, but the product acceptance items
below are still open. Nothing is merged to `main` and no milestone tag is due.

## Resume location and identity

Use `.worktrees/m4-16-playable-zoom-zoo`, branch
`codex/m4-16-playable-zoom-zoo`, not main. Main retains accepted M4-15 gameplay
and a documentation pointer at `80cd742`. Inspect actual `git status`/`git log`
before resuming. Read [M4-16](M4-16.md), [review](M4-16-review.md),
[STATE](../docs/STATE.md), AGENTS, AGENT_WORKFLOW, D-0004/D-0006 and
[R-0035](../docs/research/R-0035-zoom-zoo-playable-recovery.md).

Primary is now **Claude Opus 5** by explicit user instruction after GPT Astra
and Fable 5.1 credits were exhausted; D-0004 records the authorized move and its
two consequences. The independent reviewer is a fresh Claude Opus 5 subagent in
`.worktrees/m4-16-review`, which holds four review commits ending at `0945ef2`.
No reset, purchase, paid fallback or further provider change is authorized.
Weekly percentage telemetry does not exist under this provider; record UTC wall
clock instead of inventing a figure.

## What is done and approved

Experimental state is **URZZ000B / 742 bytes**; static pack is
**v5 / 50 entries**, and fresh extraction from the user's ROM reproduces it
byte for byte. The generic opponent reward consumer `$81C219-C2C9` is recovered
and independently approved across three review rounds. Evidence and the exact
commands are in [M4-16](M4-16.md); do not re-derive them.

Passing on the current tip: 21/21 focused tests; six complete cases at 6225
states each covering both outcomes; the primary gate at 6225 observations, 757
fresh-process restores and a full fresh restart; seven reward probes plus the
150 control; 405 synthetic checks on both app presets with no skips; 20
historical M4-12-M4-14 and DRAGSTER commands on both lab presets; bootstrap,
pack-only, wrong-ROM, truncated and corrupt-pack gates; and denied-execution
autonomy with controls proving the denial was in force.

`local/native/dragster-idle` was missing here and was restored from the main
checkout; without it every historical command exits 2, missing prerequisite.

## Remaining work, in order

1. **Live controls — blocked on the user, not on code.** A visible window driven
   by real key events through a complete race, result and restart is the main
   acceptance gap. Synthesized events are dropped: macOS discards them from a
   process without Accessibility permission and reports no error, so the
   PID-restricted `artifacts/m4-16/live-key` helper returns 0 while the app
   records `mapped key down/up 0/0` over 900 updates; activating the window via
   System Events hangs on the Automation consent prompt. Either the user grants
   Accessibility to the driving process, or the user exercises the app directly.
   Do not retry this blindly and do not substitute a fixed mask, a replay or a
   terminal runner. The app itself launches, validates, renders and runs 50 Hz
   native updates correctly.
2. **M4-15 race matrix and the ZOOM ZOO trial differentials.** Not run: their
   original reference pairs are absent from this checkout. Re-capturing the
   M4-15 primary pair is roughly 1.3 GB against about 24 GB free. The legacy
   empty-bank path is provably unchanged, which is a reason to expect a pass,
   not evidence of one.
3. **Visual acceptance.** Original scene identities are frozen in
   `tests/manifests/presentation/zoom-zoo-playable-v2.json`; private originals
   are `visual-original-a/b`, comparison `visual-7c3e3b6/comparison.png`. The
   recorded limitations are a missing direction arrow and coaching cue, rider
   anchors off by roughly 8-14 pixels, and low-salience result graph points.
   Independent readability review is still due.
4. **Result-loading read classification** against the durable
   [persistent-input ledger](../docs/research/M4-16-persistent-input-ledger.md).
   Zero unresolved stores is not zero unresolved reads.
5. **Final integration**: reviewed exact merge, hosted macOS/Linux CI on the
   exact tip, and synchronized private main. Hosted Linux is synthetic coverage,
   not private Linux differential execution. No M4-17 and no milestone tag.

## Launch recipe

```sh
python3 tools/project.py frontend run --track zoom-zoo --pack local/classic-crawler-two-tracks-v5.pack --preset app-debug --report artifacts/m4-16/FRESH-live.json
```

Add `--rom` with the private locator's ROM and a fresh pack path for a first
extraction. This remains a prototype.
