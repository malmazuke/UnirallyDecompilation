# Project plan

Planning baseline v0.1 — 10 September 2026. Milestones are acceptance gates, not completion estimates. The backlog authorizes no implementation or spending by itself; the user's active work assignment controls execution.

## Product goal and accuracy target

Build a portable reconstruction that can eventually support online racing, authored tracks, an editor and replacement artwork. The near-term target is equivalent gameplay for one identified ROM revision. Recovering original source names or producing a byte-identical rebuilt SNES ROM is not required for this target. Annotated disassembly and matching routines remain useful evidence.

Maintain two explicit behavior profiles within one codebase:

| Profile | Contract |
| --- | --- |
| Classic | Preserve measured original rules, arithmetic, input sampling and game-update timing. Match the original within an explicitly recorded test domain. Track original quirks as behavior, not bugs to silently fix. |
| Extended | Allow custom content and deliberate rule changes, with a separate versioned rules identity and its own regression expectations. State the differences from Classic. |

Both profiles use deterministic simulation. Higher-resolution visuals and smoother display refresh must not silently change either profile's game speed or collision. Neither profile promises exhaustive equivalence merely because a finite suite passes.

### Initial scope

The user selected PAL Unirally (European/Australian version). Establish its exact revision and hash in M0. Start with one representative track segment, one rider and a short input recording covering acceleration, airborne movement, a trick and landing. The first native experiment can be headless. A playable version follows once the mechanics can be compared reliably.

Until the playable slice works, defer online services, matchmaking, a general-purpose editor, replacement-art commissioning, multiple ROM revisions and a full rewrite of the sound system. Reserve useful interfaces now; implement features when their milestone needs them.

## Architecture to grow from

Use a small deterministic simulation library with a headless runner. A desktop frontend consumes its state. Research tools run the original in a reference emulator through a separate adapter. Keep the emulator integration replaceable.

```text
ROM + recorded inputs -> reference adapter -> normalized reference state
                                 |                     |
                           trace/snapshots              |
                                                       v
decoded track + same inputs -> native simulation -> state comparator
                                   |
                         render/audio frontend
                                   |
                     later: editor and network session
```

The proposed native stack is C++20, CMake, Python tooling and SDL3. The environment spike may revise it with a written decision. Avoid writing an engine framework before the first experiment.

Design commitments:

- **Explicit updates:** `step(state, inputs, content, rules)` advances one documented simulation update. M1 must determine how this corresponds to frames and input reads in the selected ROM; do not assume 60 updates per second.
- **Complete state:** inventory RNG, timers, previous input, animation state where gameplay depends on it, and all other future-affecting data. Canonical serialization and state hashing must avoid pointers, padding and host byte-order assumptions.
- **Defined arithmetic:** use explicit widths, signedness, overflow and fixed-point behavior where indicated by the original. Avoid C++ undefined overflow and compiler-dependent conversions. Display interpolation can use floats independently.
- **Content separate from code:** extract original content through reproducible tools. Give tracks, sprites and animations stable logical identifiers, independent of source ROM offsets. Preserve offset provenance in the extraction metadata.
- **Visual replacement separate from collision:** record original anchors, logical dimensions and animation timing. A larger texture must not enlarge a rider's collider or alter a trick window.
- **Versioned formats:** record rules, state, replay, track and asset schema versions. Reject incompatible inputs clearly. Add migration support only when a format actually changes.

A temporary emulator-assisted build can accelerate discovery and comparison. Label which systems still execute original code. M3's native gameplay acceptance cannot be satisfied by secretly wrapping the original CPU execution in a modern window. Reusing a documented graphics/audio compatibility component is a separate decision, with its provenance and distribution implications recorded.

## Milestones

| Gate | Deliverable | Evidence required to advance |
| --- | --- | --- |
| M0 — Repeatable laboratory | Reproducible toolchain, identified ROM, automated reference run, durable tasks | Clean build on local macOS and Linux; synthetic checks; identical repeated reference playback; intentionally altered input detected; one task resumed by a fresh agent session |
| M1 — Map the relevant systems | Annotated code/data map, player-state schema, track investigation | Validated addresses and meanings for the selected sequence; state sampling point defined; each critical finding has an experiment; unknowns remain explicit |
| M2 — Native mechanics experiment | Native implementation of the short movement/trick sequence | Exact agreement on defined gameplay fields for the primary trace and at least two withheld input variations; native save/restore continuation agrees; first-divergence reports work |
| M3 — Playable native slice | One complete track, controls, rider animation, collision, tricks, race finish and minimal frontend | Full-track recordings match scoped gameplay fields; real play confirms controls and readability; no original CPU execution for delivered gameplay; declared visual/audio omissions; repeatable build from a clean checkout |
| M4 — Original game coverage | Remaining tracks, opponents, modes, local multiplayer, menus/progression and audio | Feature-by-feature coverage matrix, regression recordings, persistence checks and release testing on selected desktop platforms; remaining mismatches published |
| M5 — Custom-content release | External track packs, high-resolution texture packs and a usable track editor | Create/save/load/race a new track; replace a sprite/animation without altering gameplay; version compatibility and malformed-content checks; Classic regressions still pass |
| M6 — Online release | Network sessions for agreed player count and rules, including custom-content compatibility | Same state across clients, latency/loss/jitter tests, reconnect/disconnect behavior, content/rules checks, desync diagnostics, tested session flow and deployment plan |

M0–M3 form the first investment decision. Measure progress before estimating M4–M6. M5 format prototypes can run beside M4 after M3 stabilizes. An M6 two-client networking spike can start after M3 if serialization is reliable, but production online work depends on the chosen content/rules contracts. Completing every original menu is not a prerequisite to learning whether rollback is practical.

For M4, inventory actual game features from evidence; the table does not assert that every named system has already been confirmed in this ROM. For M3, maintain a scoped inventory so a polished demo cannot be mistaken for the full game.

### Next-stage estimate, revised from observed effort

Revised 11 September 2026 from the M0-01 to M0-05 handoffs; the figures and their derivation are in [R-0005](research/R-0005-m0-acceptance.md). Observed: about **9 h 55 min of worker sessions** across five accepted tasks, plus **11 review rounds** (at least 1 h; five of the sessions recorded no duration), of which **6 returned a material finding**. Two patterns, both from this small sample:

- Fix rounds after the first candidate cost roughly as much as the first candidate (M0-03: 1 h 45 min, then 2 h 35 min of fixes; M0-04: 1 h 30 min, then 30 min).
- The tasks that touched a real unknown needed the most review rounds. M0-03 took five, and each one found a defect in how a *check* was defined rather than in the emulator. Pure tooling tasks (M0-02, M0-04) settled in two.

M1's three tasks each face a real unknown (what the ROM executes, where player state lives, how a track is encoded), so M0-03 is the closer analogue than M0-02. Taking about 2 h for a first candidate plus a comparable amount of fixes, M1-01 to M1-03 are estimated at roughly **12 h of worker sessions and 6 to 15 review rounds** — with the spread, not the midpoint, as the honest figure: a single task that turns out to need a different capture method can absorb the whole estimate on its own, as M0-03 did.

These are effort figures for planning task order and concurrency. They are not a calendar date, a delivery promise or a cost: sessions are not metered here, no spend is authorized by this plan, and five tasks on one host by two models is too small a sample to extrapolate to M2 and beyond. Re-estimate M2 from M1's observed figures rather than from this one.

## Future features without premature implementation

### Online play

Start with two players as a planning default, subject to product choice. Early replay and save/restore work prepares for network synchronization, but does not prove network viability. Benchmark state size, restore cost and simulation speed before choosing input delay, rollback, or an authoritative server approach.

A networking spike must model input sequencing, prediction/correction, random seed, session start, version/content hashes, and desync recovery. Rollback must reconcile presentation events so audio or effects are not duplicated. Test mismatched builds, jitter, packet loss, prolonged stalls and disconnects. Competitive ranking, anti-cheat, accounts, public servers and matchmaking are separate scope decisions with operating costs; do not assume them into the first online milestone.

### Tracks and editor

Use the original track decoder to learn which geometry and gameplay properties are necessary. Build one validated external track format before choosing a full editor framework. Keep editable source data separate from compiled runtime data. The first editor needs geometry placement, starts/checkpoints/finish, undo, validation, save/load and playtest. Sharing, discovery and collaborative editing can follow.

### High-resolution assets

Use an asset manifest mapping logical identities to replacement images, pivots, frame order and timing. Specify fallback to original extracted art and texture-size/memory limits. Check that a visual-only pack leaves simulation hashes unchanged. A public pack gallery or hosting service is later scope.

## Risks and decision rules

| Uncertainty | Early experiment | Response if it fails |
| --- | --- | --- |
| Emulator cannot be automated reliably | M0 cold-start replay and capture | Try one alternate adapter or a small pinned-core modification; keep gameplay work dependent on a working reference |
| State is incomplete or misidentified | M1 perturbations and independent traces | Narrow the task to the first changing field and its writers; revise the schema |
| Custom compression or track representation is difficult | Decode a small region and validate against runtime use | Preserve raw provenance; defer a general extractor until the small case is explained |
| Native physics appears plausible but diverges | M2 field-level differential comparison | Find the first divergence; investigate arithmetic and update order before tuning constants |
| Agents consume time without learning | Per-task hypothesis and experiment log | After repeated unproductive attempts, checkpoint and narrow or reassign the task |
| Parallel work causes integration drift | Small tasks, isolated worktrees and a single integration owner | Reduce concurrency around shared interfaces; merge prerequisites first |
| Cross-platform determinism breaks | Native replay on two hosts | Investigate serialization, arithmetic, iteration order and compiler behavior before networking |

Track accepted tasks, validated mechanics, replay coverage and resolved divergences. Do not use lines of code, tool-call count, or a guessed percent of ROM bytes as the headline progress metric. Report observed cost/time per accepted task when available, and revise the next milestone estimate from those measurements.
