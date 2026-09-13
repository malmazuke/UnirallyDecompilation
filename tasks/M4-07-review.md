# M4-07 independent review

- Candidate: `b842842cfe5556afd21e7c966f9e4e7518134ddd`
- Implementation: `28cafed5768d8970308de92f22f03ade708b4013`
- Assigned comparison base: `d5bf74c`
- Review branch/worktree: `review/M4-07-zoom-zoo-reflected-vertical`,
  `.worktrees/m4-07-review`
- Reviewer: fresh OpenAI Sol/medium session, 13 September 2026
- Verdict: **return with two evidence-integrity findings**. The arithmetic,
  captured primary, complete 66+36 composition and private reviewer case all
  reproduce. Production and prior frozen paths are unchanged.

## Findings

### R1 — two required semantic manifest fields are accepted after contradiction

`validate_manifest` requires the keys `description` and `limits` to exist but
never validates either value. On the exact candidate, independently replacing
the primary reference's `description` with `"contradictory"` and its `limits`
with `"autonomous production support"` each prints `UNEXPECTED_PASS` from
`validate_manifest`. Therefore `verify` can issue a passing component report
for a manifest that contradicts the bounded captured-argument domain. The
report's changed manifest hash records the contradiction but does not turn the
check into a failure.

This is acceptance-relevant because the manifest is the frozen statement of
what its exact calls establish, and M4-07 explicitly requires identity
mutations to fail or affect computation. Bind both semantic fields to the
scenario-specific expected values and add focused mutations for them. Do not
change either authored expected value or regenerate any reference result.

### R2 — the recorded original instruction addresses are not instruction boundaries

Both the preimplementation inventory and R-0025 say the `0x4000` mask is at
`$81:8BE9`. Exact PAL ROM bytes and the captured pre-instruction modes show:

```text
$81:8BE3  29 00 80  AND #$8000   (16-bit A)
$81:8BE6  8D 00 02  STA $0200
$81:8BE9  A5 18     LDA $18
$81:8BEB  29 00 40  AND #$4000   (16-bit A)
$81:8BEE  8D 02 02  STA $0202
```

Thus `$81:8BE9` is the reload and `$81:8BEB` is the second mask. The same two
documents describe the reflected point-x operation as
`$81:8C2C--8C3C`, but `$81:8C2C` is the operand of the preceding `BRA`, the
reflected path begins with `LDA #$03` at `$81:8C2D`, and its column store is
the three-byte `STA $0231,Y` at `$81:8C3D--8C3F`. Correct these evidence links
to instruction boundaries. The implemented equation itself is consistent
with the bytes; this finding is about the project's required precise evidence,
not a rejection of the mirrored-column result.

## Private preregistered case

Before running the case, I kept the accepted first Right at frame 1650,
released Right for exactly frame 1685, restored it at 1686 and retained every
other event. I predicted only exact state through frame 1684 and first
controller divergence at frame 1685; contact timing, class and reconvergence
were not predicted. The deliberately placeholder-bound first replay failed
only the two expected identity checks while its two fresh processes agreed on
all 3,300 frames.

The ignored reviewer manifest after observing the result hashes to
`7ff124c1735ea8564bb21d945d74d55236dfcf6daca85df1482d8145a4e26882`.
Two fresh processes agree at sample digest
`231565381f19f98afd1a5e2968d2a9fd0be92686944bcdf0c61ec5ae4f4cdb50`,
final state
`037fee6dd7e6003ebca34ab45a16d7b70c95ac554d4d48b68658877df697eb00`
and aggregate A/V
`d25c5f4644f59b3419498f64ec61fb9cd99fd3dadb20dc18de8de60396ee46df`.
The unchanged final-state and A/V identities are observations, not
preregistered expectations.

Two contact captures through frame 1700 are byte-identical at
`0545d1d2d8d8f89942d4e5bddb8ba274b62b3ade10dc7ed8912a96a957a0048b`.
Each has 935,319 instructions, 462,794 accesses, zero unresolved stores, zero
PCs outside ROM and maximum ring use 18,640 of 262,144. Direct evaluation of
the candidate equations passes all 102 calls/1,020 points: the unchanged
66-call/660-point prefix comprises 41 continuous, 24 unsupported and one
recontact call; the 36-call/360-point suffix comprises 18 reflected player and
18 flat opponent calls.

This case is **not a new contact class**. The reflected player calls remain on
frames 1683--1700, use only descriptor family `0x4000`, remain continuously
supported, and select the same angle/coefficient progression 0 through 8.
Compared with primary it changes arguments: player `vx` is 482 rather than 483
at frame 1685 (published `vx` 483 rather than 484), and later pose/position
arguments differ at frames 1696--1700. It does not change the family or its
timing through the cap. Because the candidate is returned, no tracked reviewer
manifest or expectation was frozen; all private files remain ignored.

## Original arithmetic and order audit

I inspected the exact PAL ROM bytes and captured pre-instruction P flags/access
order independently of the Python result.

- The masks above execute with 16-bit A. The reached preprocessing later uses
  8-bit A: the reflected table column runs from `$81:8C9E` through the
  `STA $0230,Y` at `$81:8CA9`; height is read at `$81:8CBB`, decremented and
  subtracted from local y through `$81:8CD3`; angle is read at `$81:8CDD` and
  byte-negated by `EOR #$FF; INC` at `$81:8CE6/$81:8CE8`.
- The accepted reducer at `$81:90BE` preserves 8-bit sign tests, ordered tie
  updates and the `$81:90EB` signed-negative penetration exclusion from the
  correction axis. Exact comparison still binds every nonselected tuple.
- `$81:973D--9747` selects the reached shift/multiplier tables. The extracted
  indices 6--8 are shifts `04 04 01` and multipliers `06 07 01`; the complete
  18-byte index-0--8 payload independently hashes to
  `f5016c76c1f4e60c988c67672b12da1d3b10948934f5f1e8b29135274203e7a1`.
  `$81:9749--9760` uses signed arithmetic shift, the repeated-add loop is
  `$81:9763--9770`, and the sign-dependent product sequence through
  `$81:977E` implements the documented positive product / `-product+1` split.
- `$81:97B7--97CA` derives and stores the signed half-angle contribution;
  `$81:97DB--97E3` loads/adds/stores vx. The response precedes the common
  position tail: `$81:97FD` stores incoming y and `$81:980C` publishes corrected
  y before caller publication. Captured scratch and every response/publication
  field agree for angles 0--8.

## Mutation and focused-check results

- An actual frame-1684 nonselected preprocessing tuple mutation that preserves
  the independently computed reducer summary is rejected at its exact point.
- Reflected descriptor, mirrored table angle, coefficient, incoming vx and
  published-vx mutations fail or change the reconstructed result as intended.
- Source identity and call count mutations reject. Call order/count hashing,
  signed shift, tie order, signed penetration, prior M4-05/M4-06 response paths
  and unobserved descriptor/horizontal rejection remain covered by the focused
  suite.
- The contradictory `description` and `limits` mutations unexpectedly pass as
  described in R1.
- A fresh primary capture reproduces access SHA-256
  `267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67`;
  the verifier reproduces component report SHA-256
  `aff5212c7e5e523abcc6664ec51d2869be0b330fcdd55fea39b8a6e900eb4aed`.
- `python3 -m unittest tests.tooling.test_zoom_zoo_contact
  tests.tooling.test_zoom_zoo_vertical_contact
  tests.tooling.test_zoom_zoo_reflected_vertical_contact -v` passes 29/29.
- Clean `lab-debug` build passes. The synthetic suite passes 342/342 Python
  records, all 20 CTest checks and three-process determinism at
  `0be347c529fadda9`; report SHA-256 is
  `462d5070f0e5445ad82fe2400997e8c5d1581d608cc026d5e05c5ac2024500f7`.
- `git diff --check d5bf74c..b842842` passes. The candidate range changes only
  its eight declared additive research/evidence files.

No candidate implementation, coordinator-owned registry/state, production or
prior frozen path was edited. ROM-derived captures, content, reports, build
outputs and the reviewer manifest are ignored and are not part of this review
commit. The coordinator alone decides acceptance after correction and fresh
focused re-review.
