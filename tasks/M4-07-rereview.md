# M4-07 focused independent re-review

- Corrected candidate: `3bca69873b3604885e9a6d4b208f6310dd8f7cb1`
- Correction implementation: `cfa94e41873b21583cbe5afdf2f4c15d44ce1bdd`
- Imported review: `e340b1414e88b5fc100aeaebed6c58e6d3bbc98e`
- Review branch/worktree: `review/M4-07-zoom-zoo-reflected-vertical`,
  `.worktrees/m4-07-review`
- Reviewer: fresh OpenAI Sol/medium focused re-review, 13 September 2026
- Verdict: **approve**. Both returned evidence-integrity defects are closed;
  no new material finding.

## R1 — semantic manifest binding

`validate_manifest` now selects exact expected `description` and `limits`
values by scenario and rejects any difference before validating the remaining
source/inventory fields. I independently repeated the exact former
unexpected-pass mutations against the primary manifest:

```text
description = "contradictory"
  -> REJECTED: reflected vertical description differs
limits = "autonomous production support"
  -> REJECTED: reflected vertical limits differs
```

The focused test applies both mutations to both authored manifests. It does
not weaken or change either expected value. This closes R1 at the same public
validation boundary that formerly accepted the contradictions.

## R2 — exact ROM instruction boundaries

I independently read the exact supported PAL ROM bytes. The corrected mask
address is exact:

```text
$81:8BE3  29 00 80  AND #$8000
$81:8BE6  8D 00 02  STA $0200
$81:8BE9  A5 18     LDA $18
$81:8BEB  29 00 40  AND #$4000
$81:8BEE  8D 02 02  STA $0202
```

The point-x bytes are:

```text
$81:8C2A  80 13     BRA $8C3F
$81:8C2C  A9 03     LDA #$03       (8-bit accumulator)
$81:8C2E  99 90 02  STA $0290,Y
$81:8C31  B9 00 00  LDA $0000,Y
$81:8C34  18        CLC
$81:8C35  6D A6 02  ADC $02A6
$81:8C38  49 FF     EOR #$FF
$81:8C3A  29 0F     AND #$0F
$81:8C3C  99 31 02  STA $0231,Y
$81:8C3F  AD 01 02  LDA $0201      (next instruction)
```

Therefore the instruction-complete reflected point-x range is exactly
`$81:8C2C--$81:8C3E`. The original review correctly found the old citation
wrong but proposed `$81:8C2D--$81:8C3F`, which cuts the `LDA` immediate and
includes the next opcode. The corrected inventory and R-0025 now cite the
independently confirmed range. The corrected-to-review explanation is precise
and does not alter the recovered equation.

## Focused validation and scope

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_contact \
  tests.tooling.test_zoom_zoo_vertical_contact \
  tests.tooling.test_zoom_zoo_reflected_vertical_contact -v
# Ran 29 tests in 0.123s -- OK

python3 -m tools.unirally_lab.native.zoom_zoo_reflected_vertical_contact verify \
  --access artifacts/m4-07-review/primary/access.json \
  --content artifacts/m4-07-review/content \
  --manifest tests/manifests/native/zoom-zoo-reflected-vertical-primary.reference.json \
  --report artifacts/m4-07-review/rereview-primary-component.json
# passed; SHA-256 aff5212c7e5e523abcc6664ec51d2869be0b330fcdd55fea39b8a6e900eb4aed

git diff --check e340b1414e88b5fc100aeaebed6c58e6d3bbc98e..3bca69873b3604885e9a6d4b208f6310dd8f7cb1
# passed
```

The correction range changes only the reflected research verifier and focused
test, the two M4-07 evidence documents, and the task handoff. Production
native code, prior frozen manifests/expectations, serialization, Classic pack,
frontend, core, locks and coordinator-owned registry/state are unchanged. The
primary component hash is unchanged. Private captures, extracted content,
reports, build outputs and local dependency links remain ignored.

The coordinator may integrate the exact corrected candidate and run the full
integration/private-remote gates. This focused re-review does not itself mark
M4-07 accepted.
