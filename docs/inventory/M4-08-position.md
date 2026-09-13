# M4-08 position-integrator inventory

This checkpoint freezes the producer watch set and worker variation before any
new M4-08 result is observed. The research capture covers end-of-frame 1649 for
the one four-residue seed and all 102 ordered rider calls on frames 1650--1700.
It watches every instruction of `$82:A627--A6F7`, persistent positions,
velocities and residues, direct-page position/scratch words, the `$0D4F` mask,
all reached slope-tail guards and caller publications.

In particular `$82:A6E9` (`ADC $A7`) and `$82:A6EB` (`STA $A7`) are explicit
watch PCs and direct-page `$A7` is an explicit watched address. The later
implementation must bind its operand to an ordered last write or register
provenance in each call. A missing producer is an incomplete capture, not a
zero/default value.

The worker variation preserves every primary event except Right: it releases
Right only at frame 1662 and restores it at 1663. Before execution the only
prediction is exact primary evidence through frame 1661 and first controller
divergence at frame 1662. Contact branch, timing and reconvergence are not
preclaimed.

The capture and variation remain reference-only research inputs. They do not
change the native core, Classic pack/profile/start, frontend or serialization.

## Recovered instruction boundary

The exact `$82:A627--A6F7` payload is 209 bytes from ROM offset `0x12627`,
SHA-256 `1b6497ea4306faa243c685f0f23b9ac7d22232db57ce3299f4627bbc22291adc`.
The routine enters in 16-bit accumulator/index mode. Both axes add the signed
residue with 16-bit wrap, take two's-complement magnitude on a negative total,
divide the magnitude by 32 with logical shifts, restore quotient/remainder
sign, and add the quotient to position with 16-bit wrap. X masks the completed
position addition with `$0D4F=0x3fff`; Y remains unmasked.

The slope tail after Y integration tests, in order: surface, guard, signed
`unsupported_count-2`, direction high bit, vertical-velocity sign and mode.
Its reached adjustments are zero, -1, +1 or +4. Primary reaches only zero,
-1 and +4; the worker variation additionally reaches the no-adjustment
unsupported-count guard.

`$82:A6E9` is no longer an unresolved semantic dependency. Same-call register
snapshots bind the Y producer at `$82:A6B9`/`$82:A69B`, accumulator 4 before
`ADC $A7`, and producer+4 before `$82:A6EB`. Missing or reordered evidence
rejects.

## Result inventory

- End-1649 seed: player `(9200,1561,-1,22)`, opponent
  `(8248,1452,-24,-1)`; row SHA `064dea0e...e9f4`.
- Primary: 102 exact recurrent calls, rows SHA `aaf2eb99...1bfe`;
  68 zero-surface, 20 +4 and 14 -1 tails.
- Frame-1662 variation: 102 exact recurrent calls from the same seed, rows SHA
  `5ace936f...3028`; first component divergence 1662, first branch divergence
  1678, opponent exact and player not reconverged through 1700.
- No position wrap crossing occurs in either bounded capture. Wrap and mask
  order are instruction-derived and synthetic-mutation checked only.

The tracked output is an identity-bound research component. Positions,
velocities and contact state remain captured external inputs; no autonomous
movement or production support is claimed.
