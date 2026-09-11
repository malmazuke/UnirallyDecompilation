# D-0003 — Human-readable native code from the first implementation

- Status: accepted project policy (not a gameplay finding)
- Date and owner: 12 September 2026, Codex coordinator, following the user's maintainability/community question
- Related milestone/tasks: M2-01 and later native implementations
- Evidence records: existing architecture in PROJECT_PLAN.md; no new gameplay claim

## Problem

M2-01 introduces the first recovered game source. A mechanically translated routine can preserve behavior yet become difficult for humans to understand or extend. A later wholesale readability rewrite would mix structural changes with newly discovered mechanics.

## Options and experiment

Defer all readability work, build an extensible framework now, or require readable small implementations now and grow abstractions from measured needs. Choose the third: it supports review immediately without designing a mod API around unknown mechanics. This is an implementation policy decision, not an experimentally verified game property.

## Decision and consequences

Use descriptive names for established concepts; label unknowns by neutral names and provenance. Document units, fixed-point scales, widths, wrapping, input phase and update order. Prefer small functions with explicit state, input and content dependencies, with research links and relevant source addresses for unusual behavior. Keep a compact guide beside the first native implementation explaining its flow, supported domain, evidence and commands.

Keep exact Classic behavior as the constraint on every readability change. Isolate processor-shaped helpers when needed for exact arithmetic; a research translation is permitted but must not silently become the public architecture. Avoid per-instruction comments that merely repeat C++ operations. Review both semantic correctness and whether a human can trace the implementation to its evidence.

Use frozen differential cases to support incremental refactoring. Defer mod APIs, plugin frameworks and speculative abstractions until real requirements exist; preserve the current simulation/content/frontend and Classic/Extended boundaries. No change to publication, licensing or service authority.

## Revisit trigger

Repeated native routines reveal common structure, a measured dependency makes the current boundary misleading, or M3/M5 supplies a concrete extension use case. Revisit those boundaries with tests, without removing the readability requirement.
