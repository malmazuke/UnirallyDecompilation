# M2-01 input/timer component handoff

Coordinator isolated worktree `.worktrees/m2-01-input-timer`, branch
`codex/M2-01-input-timer`, claim base e6f48f2. Independently reviewed comparator
c46ab59 was merged as a dependency at f1e0078; reviewer report lives in the
separate review clone at `artifacts/comparator-review/REVIEW.md`. Metadata type
strictness was corrected after review; no outstanding comparator finding.

Component submission is the commit containing this record. Owned source, probe,
check and evidence files are new; CMake registration is the only change to
existing code. No reference output, ROM/content fixture, field schema or core
changed. Read R-0010-input-timer for precise original arithmetic, observed gate
and the narrower comparison claim. Runtime receives timer enable explicitly;
it does not infer native startup from a frame constant. The research harness
supplies the observed gate, so its agreement cannot accept M2-01.

Checks before submission: doctor/bootstrap/debug build passed; synthetic suite
passed (209 Python tests plus native/repeatability checks; source dirty during
this development check). Debug and sanitizer component probes each match all
13,194 values; output SHA-256
61fd6b85b7bfe78e55364866aa344531fdb22371d2a92760415e9bc2b9ab7e0f.
Sanitizer CTest `input_timer_boundaries` passes with no diagnostic. Reports live
under ignored `artifacts/input-timer/`. Post-commit checks follow on clean source.

Next: independent review including a crafted carry/precedence boundary, then
coordinator integration with reviewed contact/motion evidence. Autonomous native
movement, withheld runs and full-state serialization remain pending. The two
frozen withheld outputs remain unopened. No user intervention is required.
