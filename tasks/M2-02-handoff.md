# M2-02 native save/restore handoff

## Candidate outcome

`native restore-check` uses the accepted M2-01 runner and canonical encoding
without adding a second snapshot path. It runs an uninterrupted baseline, a
fresh prefix and a fresh restored suffix for each requested interior frame. The
baseline must still match the frozen reference; every prefix state and every
restored suffix projection/canonical state must equal the uninterrupted series.
The command requires a distinct interior boundary list, the exact333-byte state,
fresh artifacts and a positive bounded timeout. It rehashes the binary, original
seed, content, case/reference/replay/runtime and each generated restore seed
between native processes.

Authored command tests cover the successful three-process case, duplicate and
endpoint boundaries, changed prefix and suffix state, wrong embedded frame,
changed width, input mutation between processes, crash, timeout, missing build
and invalid report location. `movement_state_tests` now explicitly rejects bad
magic, truncation, invalid input axes, queue cursors, phases and animation
counter in addition to its existing flag/idle/timer/trailing validation.

The ROM-free `movement_restore_continuation` test runs32 authored updates, saves
and restores at updates1,13 and25, and compares every subsequent333-byte state.
Its fixed platform-independent FNV-1a series hash is `7c799b4393d171f2`.
An initial180-update version left the deliberately tiny zero-filled authored
sampling domain and correctly raised `sampling content address is unavailable`;
the test was bounded to32 updates rather than weakening production guards.

## State inventory audit

The canonical writer and reader are symmetric and cover every member of
`MovementState`: frame/input; both riders' motion, contact, speed, progress,
jump, pose and history, idle oscillator, quarter-turns, residues, throttle,
brake/launch and small-motion state; timer; opponent AI; reward entries/cursors,
cooldown, learned total and weight; countdown; contact/progress phases and
animation/update counters. Content tables and future controller masks are
immutable identity-checked inputs, not state. No native gameplay global or
hidden runner state exists. Exact suffix equality across the real boundaries
below is the operational check that the inventory is sufficient in the tested
domain; other modes remain outside the claim.

## Exact local evidence

Primary restore frames1631 and2200 pass through frame2999 with five fresh
processes; final exact-candidate report
`artifacts/m2-02-final-primary/report.json`, SHA-256
`7c0169cbbf072b4bd3ce811aed77edccb848b7211e25156a2c1c84fc9a448344`.
Saved-state hashes are `61b35389...9da9` and `336136d4...3eb1`; both restored
suffixes end at `aecc6f2b...c605` exactly like the uninterrupted process.

Release-2347 restore frames2761 and2787 bracket the idle/contact displacement
boundary and pass through2999 with five fresh processes; final exact-candidate
report `artifacts/m2-02-final-release/report.json`, SHA-256
`c9b5d703d0e193b9365fc2db68a801d32e9e2a5534c998eae9f43ba644b6fd33`.
Both baselines also remain identical to all13 frozen reference projections.
Runtime metadata remains `a38d58f2...37da`; seed remains `7cd034fc...b4ab`.

## Clean candidate validation

Implementation commit `f7a3386edd4806a9ef97bcbc404af763dca1181b`
passes the complete ROM-free suite **281/281** on clean source; report
`artifacts/m2-02-final-synthetic.json`, SHA-256
`da2b8a5786825f94b540b7a7775304749d2b89bc3f254ba4c23a709e4e9b824c`.
The three movement CTests pass under sanitizers with no diagnostics; sanitizer
build report SHA-256 is
`c668cea682dd18906666a94989d81440078808906347a146edb55b3767f1bd3d`.
Focused command tests pass19/19. No gameplay source or frozen expectation changed.

## Review and acceptance

Independent review approved behavioral commit `f7a3386`: **281/281** synthetic
checks, all three sanitizer movement tests, both required exact cases, and the
portable `7c799b4393d171f2` hash were reproduced in a clean detached checkout.
Reviewer-owned boundaries1534 and2998 passed in five fresh processes (report
SHA-256 `7881f4c5a5ccb90a20dada0b59cd82d71ff0e9043f3a48ffb748ea216a5bd3ab`),
and a deliberate suffix-stream mutation was rejected after two producer calls
with exit1. The reviewer found no hidden runtime state or remaining finding.

Coordinator merge candidate `5c065db4ff261e69ef29516f41651e63c2892ade`
passes **281/281** synthetic checks (report SHA-256
`7cb940df41f6ccf572fa8814bbdc57805c079e193037e4f8dc80f1352bc1f838`),
all three sanitizer movement tests (build-report SHA-256
`ab2b7b43211a08fcb388e6571b28522928fae516092f6d0374251b63fffdb854`),
primary1631/2200 (report SHA-256
`91051b76ee5cbb72a1b3242e7be0be00d2995e3ddd926b25eebf314437cc1a97`)
and release2761/2787 (report SHA-256
`998d188bdec6dbe6a7c59b5ab805c95d594ac4cc1134c127aebee4faf074c4ca`).
All reports record clean source and no source change during execution. One
initial coordinator release invocation misspelled the manifest filename and
correctly exited2 as a missing prerequisite; the corrected command above passed.

PR5 ran twice because both its push and pull-request events matched the workflow.
Runs34675475186 and34675476818 each passed on macOS15 and Ubuntu24.04; the
portable continuation test and Linux sanitizer run were included. PR5 merged as
`144fd4839d540654b255f81d199f30acb866a55d`. M2-02 and milestone M2 are
accepted; the milestone audit is [R-0011](../docs/research/R-0011-m2-acceptance.md).
