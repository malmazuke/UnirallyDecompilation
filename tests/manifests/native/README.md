# M2-01 reference freeze

These are reference observations, not native results. Each `*.replay.json`
is executable with the existing `replay compare` command and preserves all
eleven original ranges. Each `*.expected.json` contains the explicit movement
projection for frame 1533 (initial observation) and updates 1534–2999. The
`projection` array declares byte offsets, widths and signed interpretation;
the diagnostic-only bytes cannot count as native agreement.

The release at 2347 and the 17-frame cadence from 1700 are withheld from
implementation. Their replay inputs and expected series were generated before
native computation, using two fresh reference processes per case. Do not inspect
their series while developing the routine. Input choices are preregistered in
M2-01. Controller 2 is silent in all cases.

Regenerate reference samples using each replay manifest's `regeneration_command`,
then freeze into a **new** output path (the utility refuses overwrite):

```sh
python3 -m tools.unirally_lab.native.freeze_reference \
  --manifest tests/manifests/native/primary.replay.json \
  --samples artifacts/m2-01/freeze/primary/run1-samples.json artifacts/m2-01/freeze/primary/run2-samples.json \
  --out artifacts/m2-01/freeze/primary/check.expected.json
cmp tests/manifests/native/primary.expected.json artifacts/m2-01/freeze/primary/check.expected.json
```

Replace `primary` with a withheld name only for reference regeneration or final
withheld validation. Frozen reference values do not eliminate native content
prerequisites. The utility only projects reference samples; there is no native
simulation or `native compare` command yet. Source identities, detailed capture
commands and the current prerequisite investigation are in R-0010.

M3-01 adds two `native_full_race_case` manifests. Each binds the original replay,
the pre-implementation frozen gameplay projection, the finish-state reference
contract, and the accepted ignored M2 runtime. `native finish-check` consumes
those bindings without loading a ROM or invoking the reference emulator.
