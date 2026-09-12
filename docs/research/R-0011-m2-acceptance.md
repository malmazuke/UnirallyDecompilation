# R-0011 — M2 acceptance

- Status: accepted 12 September 2026
- Tasks: [M2-01](../../tasks/M2-01.md),
  [M2-01A](../../tasks/M2-01A.md), [M2-02](../../tasks/M2-02.md)
- Integration: PR5, merge `144fd4839d540654b255f81d199f30acb866a55d`
- Baseline: PAL Unirally SHA-256
  `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`

## Gate audit

| M2 gate | Accepted evidence |
| --- | --- |
| Native short movement sequence | M2-01 matches all13 frozen projections for every update from frames1534–2999 in the primary, cadence-17 and release-2347 cases. No original CPU executes in the native runner and no per-frame reference state is an input. |
| At least two withheld inputs | Cadence-17 and release-2347 were frozen before the completed implementation and both match exactly through frame2999. |
| Save/restore continuation | M2-02 resumes the exact333-byte canonical state in a fresh process. Primary boundaries1631/2200 and release boundaries2761/2787 match every later canonical state and projection; independent boundaries1534/2998 also pass. |
| First divergence | Native comparison and restore tooling report the first divergent frame, prior frame, projection differences, canonical byte offsets and state hashes. Authored mutations exercise the failure paths; a reviewer-owned changed suffix stream was rejected with exit1. |
| Portability and regressions | The ROM-free continuation series pins FNV-1a `7c799b4393d171f2`. PR5 CI runs34675475186 and34675476818 each passed macOS15 and Ubuntu24.04, including Linux sanitizers and **281/281** required checks. |
| Independent review and integration | M2-01's review found and verified the idle-pose zero-crossing correction and later GCC conversion correction. A fresh M2-02 reviewer approved exact behavioral commit `f7a3386`, reproduced all required evidence, and added the boundary/mutation cases above. Coordinator candidate `5c065db` passed the full local matrix before PR5 merged. |

The canonical writer/reader audit covers every `MovementState` member. Static
content and future controller masks remain identity-checked inputs rather than
serialized state. No second snapshot path, emulator fallback, hidden gameplay
global, frozen expectation change, required skip or missing check was accepted.

## Scope boundary

M2 proves the recovered short DRAGSTER movement domain only. It does not prove a
complete race, finish logic, all tricks, menus, rendering, audio, other tracks,
local multiplayer or a playable frontend. Those remain M3 and later work. The
state format is validated for this domain; future fields must be added through
an explicit format revision, not hidden alongside the333-byte schema.

## Next decision

M3 will continue on the existing Crawler/DRAGSTER scenario because its native
mechanics, state, track content and reference identities are already reviewed.
First extend the reference recording through an actual finish and inventory the
missing gameplay/render/control dependencies; then divide the playable slice
along evidence-backed interfaces. This avoids selecting a new track before the
first complete native path is understood.
