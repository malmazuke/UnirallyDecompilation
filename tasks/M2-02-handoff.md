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

## Remaining gates

Run the complete synthetic and sanitizer suites on a clean candidate, obtain an
independent exact-candidate review with an additional boundary/mutation, then
integrate through a `task/**` PR and require macOS15/Ubuntu24.04 CI. M2 and M2-02
remain unaccepted until those gates close.
