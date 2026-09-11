# M2-01 comparison layer

Coordinator implementation in isolated `.worktrees/m2-01-comparator`, branch
`codex/M2-01-comparator`, base `8f0c7ab`. Owned paths were recorded in M2-01
before implementation. The submission hash is the commit containing this record.

This layer performs no gameplay and supplies no public native command yet.
It validates the frozen projection and exact replay identity, requires complete
native rows including the initial seed and all updates, and reports the first
field divergence with prior values and both controllers' prior/current inputs.
A narrowed reporting window still requires all rows. The report counts only
frames actually compared through the first divergence. Reference/request errors
and malformed native output use distinct exceptions for later exit-code wiring.
Missing files propagate separately. Freeze history supplies provenance; the
loader cannot authenticate edited expected rows and does not claim to do so.

Validation: `python3 -m unittest discover -s tests/tooling -p test_replay.py`
passed 39 existing tests; `python3 -m unittest discover -s tests/tooling -p
 test_native_compare.py` passed nine authored protocol tests. These exercise
signed values, first-divergence ordering, seed/warmup requirements, malformed
rows, immutable projection and exact manifest-byte binding. The real primary
reference is loaded only to validate its format/identity; no native agreement is
claimed. Frozen withheld series remain unopened. No source, frozen expectation,
ROM, extracted content, emulator or local fixture changed.

Next: independent review of this exact submission, then connect the comparator
to the autonomous native runner once contact/motion dependencies are recovered.
Full synthetic integration/CI and native movement acceptance remain pending.
