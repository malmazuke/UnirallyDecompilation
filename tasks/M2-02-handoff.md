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
processes; report `artifacts/m2-02-primary-verified/report.json`, SHA-256
`be9e34df71bfddda980fcc6ed55846955da6e76dca64ae7ff55c14c90e611d3f`.
Saved-state hashes are `61b35389...9da9` and `336136d4...3eb1`; both restored
suffixes end at `aecc6f2b...c605` exactly like the uninterrupted process.

Release-2347 restore frames2761 and2787 bracket the idle/contact displacement
boundary and pass through2999 with five fresh processes; report
`artifacts/m2-02-release-verified/report.json`, SHA-256
`5c941f58a29eaf0d04b6e6f56ce577508a4819887f3c1ca10991e6233d55a90b`.
Both baselines also remain identical to all13 frozen reference projections.
Runtime metadata remains `a38d58f2...37da`; seed remains `7cd034fc...b4ab`.

## Clean candidate validation

Implementation commit `c4c88a4efb2afe3f3bc88662dcb27d7f732f79d9`
passes the complete ROM-free suite **281/281** on clean source; report
`artifacts/m2-02-clean-synthetic.json`, SHA-256
`c13f6af3340214462dc285bcd491147d53feebf8f34b6ce39af0f8051c5851f6`.
The three movement CTests pass under sanitizers with no diagnostics; sanitizer
build report SHA-256 is
`baf065e4bd8758ac0b6f53d5f443d261ef512563bedf3b6e01ba85677569b312`.
Focused command tests pass19/19. No gameplay source or frozen expectation changed.

## Remaining gates

Run the complete synthetic and sanitizer suites on a clean candidate, obtain an
independent exact-candidate review with an additional boundary/mutation, then
integrate through a `task/**` PR and require macOS15/Ubuntu24.04 CI. M2 and M2-02
remain unaccepted until those gates close.
