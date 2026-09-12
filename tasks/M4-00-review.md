# M4-00 independent review

- Verdict: **returned for correction; not approved**.
- Reviewed immutable candidate: `9e82af4ba89341adc833664a6a327f01c2dd016d`.
- Actual accepted base: `m3`, commit
  `09ce40e9f591ffa828db2e2b54cd13eaa88a0d58`.
- Reviewer: fresh OpenAI Codex `gpt-6-astra`, high reasoning, 13 September 2026.
  This second bounded consultation reviews new evidence after the earlier
  loser-presentation/coupling audit; it performs no implementation or capture.
- Quota supplied at dispatch: weekly 44% used, final 20% reserved; no spending
  or reset redemption. This review did not resample account telemetry.
- Worktree: `.worktrees/m4-00-feature-inventory`; candidate was clean at entry.
  Write ownership is this report only.

## Findings

### F1 — P2: preserve the already recovered SRAM-derived AI state

[R-0018, progression/persistence row](../docs/research/R-0018-m4-feature-inventory.md)
line 32 classifies **original SRAM semantics** as unobserved. That is broader
than the evidence permits. Accepted M2-01A research already identifies the
cartridge-RAM word `$77:0825` as the accumulated feature total:

- [R-0011-motion](../docs/research/R-0011-motion.md), lines 223–243, records
  reward event 1 adding weight 4 to total 0 at frame 1619, then halving the
  weight. The total changes subsequent opponent jump requests; holding it at
  zero produced a demonstrated mismatch from frame 1648.
- The same record, lines 252–260, binds a fresh frame-1533 original SRAM
  capture (`774410886d8e20e123924251c49230fb94a3bfb51438497ea070ba3421b889eb`)
  and confirms total 0/weight 4. Its tested primary/variation domains and the
  absence of RNG reads in their executed AI branch are explicit.
- This is used by accepted native code: `src/core/movement.cpp` lines
  598–599 update total/weight; lines 758–768 consume the total in opponent
  jump control; lines 631/658 serialize and restore it. The M2-01A acceptance
  and its integration into movement are recorded in `docs/STATE.md`.

This is a material inventory error because it discards an established
future-affecting dependency that subsequent AI/track work must retain. Amend
the AI/persistence cells to cite this bounded in-race observation and native
continuation. Keep cross-session save/progression behavior, other SRAM fields
and behavior under other initial persistent states unobserved. Do not infer
user-save persistence from the recovered in-race update. No ROM experiment or
gameplay change is needed to correct the classification.

### F2 — P2: replace the invalid exact base identity

`tasks/M4-00.md` line 20 names
`09ce40e1ca785a7eaff29626835dfdc3140afb2c` as its base commit. It is not the
accepted `m3` commit and does not resolve in this repository:

```text
git cat-file -t 09ce40e1ca785a7eaff29626835dfdc3140afb2c
fatal: git cat-file: could not get object info

git rev-parse 'm3^{commit}'
09ce40e9f591ffa828db2e2b54cd13eaa88a0d58
```

Correct the full hash to the verified value so an agent can reproduce the
task's exact starting state. The abbreviated `09ce40e` and the actual candidate
ancestry are correct; this finding does not question accepted M3.

## Scope checks that hold

- **Presentation classification challenged and confirmed:** the seven frozen
  cases include result frames 3678/3679 from the winner path, with unchanged
  15% whole-frame limits. `build_result_map` at `src/core/presentation.cpp`
  lines 389–391 rejects every outcome other than `PlayerWon`. The accepted
  release case and R-0017 separately establish exact loser gameplay through
  frame 3800. R-0012 and `docs/state/race-finish.md` observe the original loser
  and subsequent complete screen without claiming general ranking semantics.
- **M4-01 is the narrow closure:** it uses that same release path, requires
  original composition/provenance before implementation, freezes its new
  visual case independently, preserves all seven existing counts and gameplay
  identities, and exercises `LivePresentation` without mutating state. The
  conditional pack-extraction allowance requires prior evidence of missing
  entries and does not authorize broader content recovery.
- **M4-02 has an explicit coupling gate:** R-0006 finding 8 supports the four
  alternate names only as displayed labels. The work order observes opponent
  and event/rules before freezing the replay and permits a different candidate
  or prerequisite if they change. It does not assert ZOOM ZOO is reachable as
  an isolated track change. Native source, pack and M3 expectations are frozen.
- **README reconciliation is supported:** accepted M3/tag/date, native CPU
  boundary, 25-entry pack, pack-only relaunch, bounded PAL scheduler, controls,
  integer scaling and art/audio omissions agree with R-0017, R-0016 and current
  manifests. It links the missing loser result and next discovery explicitly;
  it does not advertise unimplemented M4 commands or full-game acceptance.
- **Frozen boundaries and hygiene:** the complete `m3...9e82af4` change is
  eight owned Markdown files (414 additions, 29 deletions). No source,
  manifests, expected values, ROM/core identities, pack extraction rules,
  workflow or ignore rules change. There are no added binary/private payloads.

## Checks and limitations

- Read the assignment, project state/workflow/plan/build specification, all
  changed documents, the exact diff, and the cited M0–M3 evidence/current
  contracts needed for the checks above.
- Reproduced `python3 tools/project.py doctor --report
  artifacts/m4-00-review/doctor.json`: exit 0, required checks passed. Optional
  system Ninja was missing; isolated Ninja was present. Report SHA-256:
  `638f56067bc1db3cd28f9042ba9b6fe9dfc91f3a676b57b8dffde9b55fe54453`.
- `git diff --check m3...9e82af4` passed. `git diff --quiet m3 9e82af4 --
  src tests tools CMakeLists.txt CMakePresets.json .github .gitignore` exited 0.
- No ROM capture, visual fixture regeneration, gameplay execution or complete
  synthetic suite was run by this reviewer. The worker's recorded 314/314
  result remains worker evidence; this report does not relabel it an
  independent test pass. Two exploratory reads used nonexistent guessed
  filenames; their failures yielded no evidence and were replaced by the
  actual tracked paths.

Next action: correct F1 and F2 on a new immutable documentation candidate, then
perform a focused independent re-review before coordinator acceptance. No
implementation or private input is needed for these corrections.
