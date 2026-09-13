# M4-08 position-integrator preregistration

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
