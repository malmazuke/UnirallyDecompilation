# Next session — resume incomplete M4-16

**M4-16 is in progress and unaccepted. Do not start a replacement task.**
Work in `.worktrees/m4-16-playable-zoom-zoo` on
`codex/m4-16-playable-zoom-zoo`, dispatched from synchronized
`ede4c0b3b17269cd6984b21765efd98f11fe1085`. Main retains accepted M4-15 gameplay.
Read [M4-16](M4-16.md), [STATE](../docs/STATE.md), AGENTS, AGENT_WORKFLOW,
D-0004/D-0006 and [R-0035](../docs/research/R-0035-zoom-zoo-playable-recovery.md).
Resume the existing checkout; `git status`, `git log -5` and the ignored recovery
record identify its actual tip. Do not overwrite private fixtures or old packs.

## Resource and review boundary

Session started2026-09-13 22:55:27 UTC, OpenAI Astra/medium, weekly57% used.
Latest sampling and the stopping reason are recorded in `recovery-closeout.json`
under ignored `artifacts/m4-16` in the task checkout. Preserve final20% weekly
review/recovery reserve. At80% used stop scope expansion; below20% remaining
perform recovery only until allowance is restored. No reset, purchase or provider
switch is authorized. No M4-17 or M4 milestone acceptance.

Fresh independent Sol/medium reviewer owns `.worktrees/m4-16-review`.
Review history and exact candidate results are in [M4-16-review](M4-16-review.md).
Code9f7f3b4 implements experimental V10/730-byte native start-to-result state,
49-entry static pack and held-roll feedback. This is not a playable acceptance.
Follow-up commits contain review/corrections and recovery docs; inspect them.

## Evidence and commands

Private ROM locator `local/rom-location.txt`; core
`local/emulators/bsnes/bsnes/out/bsnes_libretro.dylib`. Identities in R-0035.
Current pack: `local/classic-crawler-two-tracks-v4.pack`. Older default
`local/classic-crawler-two-tracks.pack` is a frozen incompatible v2 experiment.
Do not overwrite it. Warm first-extraction and pack-only launch reports are in
`artifacts/m4-16/launch-9f7f3b4`; these do not prove clean bootstrap or live play.

Prototype launch from this checkout, after a matching build:

```sh
python3 tools/project.py frontend run --track zoom-zoo --pack local/classic-crawler-two-tracks-v4.pack --preset app-debug --report artifacts/m4-16/FRESH-live.json
```

For a new pack, pass the supported ROM with `--rom` and a fresh `--pack` path.
The standalone `content pack` command still targets accepted DRAGSTER rules.
Current frontend exposes keyboard controls and Enter Race Again after stable
result. Start and other remaining native guards can abort ordinary play; do not
present this as a tested usable release. No automated fixed input is live proof.

At code9f7f3b4 debug and sanitizer each405 synthetic checks pass with no skips.
Primary V10 gate, reviewer held-X restore and launch results are recorded in the
final checkpoint below. Earlier clean4f8aaad passed primary V8/479 restores and
28 historical M4-12–14 commands; independent edec610 X V9/1782 restores passed.
These older results do not replace latest candidate/merge evidence.

## Resume order

1. Read fresh quota and review findings. Finish any outstanding review fixes
   under frozen original comparisons. Never tune after a gate starts.
2. Recover ordinary Start, bounce/compound rewards and wrong-direction boundary
   as internal M4-16 experiments. Expand original state/producer inventory before
   native tuning; preserve the original-only freeze ordering.
3. Complete initialization/result/restart producer closure. Standalone Race Again
   resets a fresh scenario; original result Start advances to STUNT and is not
   the same restart. The re-press-X case never finishes by7600 and cannot count
   as an acceptance case.
4. Complete frozen representative visual checks and actual live full race,
   stable result, restart, focus loss and independent reviewer live exercise.
5. Clean isolated bootstrap/extraction, denied ROM/reference/repository execution,
   wrong/incomplete-pack checks, full latest M4-12–15 and DRAGSTER regressions,
   fresh untuned cases/outcomes, independent review, exact merged checks and CI.
   Only accepted integration is pushed to main; verify exact remote refs/CI.

Desktop built-in CUA key taps yielded no nonzero50Hz input updates. A private
PID-restricted helper at `artifacts/m4-16/live-key.swift` is compiled but unused.
An explicit CGEvent permission request is pending because the desktop tool
prohibits this fallback without authorization. Check current conversation for
an actual answer; never infer it. The helper is not a replay/autopilot and only
posts one actual key transition to the validated Unirally PID. Gamepad untested.

## Frozen candidate checkpoint

Code9f7f3b46c7d49916bc3dc96547979cd6b10874ae: primary730 bytes6225 observations,757 restores and full fresh restart passed (`artifacts/m4-16/primary-start-result-v10.json`). Independent held-X gate passed6225 observations,768 restores and full restart with independently rebuilt matching pack. Debug/sanitize each405 passed, no skipped tests. Both sides used immutable candidate sources. V9 review actual commit d0c2c785c471f3696aacb33760ddb5716d57f790 is integrated as a7070ac; its initially reported expanded SHA was erroneous and recovered from the review checkout reflog.

Warm fresh extraction and pack-only hidden20-update launches pass. Wrong-ROM and truncated-pack commands exit3 with explicit identity/truncated-entry errors and do not replace the invalid pack. No new live/visual/clean-bootstrap/full historical matrix/merge/CI acceptance claim.

## Final review correction checkpoint

Behavior candidate fe02cd86d3a7fb0d16ccae89876328812d1a1594 passes primary730/6225/757 restores/full restart (`primary-start-result-v10-corrected.json`) and independent held-X730/6225/768 restores/full restart. Focused debug/sanitizer tests pass. Sol review438b3aef10f0f6f56639a7d2f43593194bf60c70, integrated415e460, closes the reported pose/held-counter restore findings; retained-rotation6/7 is valid, impossible7/6 rejects. The subsequent source edit corrects only a provenance comment to `$8295D5-95F6`; no behavior changed after the tested candidate.

New implementation stopped at80% weekly usage. Review/fix/recovery reached81% in the latest sample; final measurement is in `artifacts/m4-16/recovery-closeout.json`. Main documentation pointer7c62de5d6d2957b12096d6e6b9730f7d086ec036 was independently reviewed and its private remote ref verified. CI34795065815 and final task-branch backup refs are recorded in the closeout after verification. No gameplay acceptance, no milestone tag, no automatic continuation into reserve-funded feature work.
