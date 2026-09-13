# M4-09 preregistered composition inventory

Preregistered at claim `15da58489df4ccce24a678aa3d98382872036ab1`, before
any new M4-09 capture or replay result. The accepted M4-08 and M4-07 captures
remain comparison foundations and are not edited.

## Combined watch and order hypothesis

The additive capture is end-of-frame 1649 through frame 1700 with the union of
the accepted M4-08 position and M4-05--M4-07 contact watch sets. It adds every
decoded instruction of `$82:A96F--A9B2`, its `$0F4B`, `$0FF9`, indexed
`$0547/$0549`, `$0FAB`, `$00/$02` and `$A7` dependencies, and the two callers'
helper/integrator/sampling/contact boundaries.

Instruction decoding predicts a 16-bit predicate chain: `$0F4B == 0`, indexed
`$0547,Y == 0`, and signed `$0FAB < 0x0200`. Only then the helper updates
vertical velocity using the reached sign-sensitive shift path and increments
the transient Y word `$A7` once at `$82:A9AD--A9B0`. Exact predicate counts,
the computed velocity relation and whether either early exit is reached are
observations, not preregistered results.

The order hypothesis is that each player/opponent update executes the helper,
then `$82:A61F` enters the accepted position integrator, then collision-point
expansion and width-256 track sampling, then contact, and finally caller
publication. Across frames, the next position integrator consumes the previous
contact publication. Captured pose, reflection, velocity and all contact inputs
other than the eight recurrent position/residue words remain explicit external
fields until evidence proves a producer; `response_b` is specifically not
recurred because accepted evidence shows it can change before contact.

## Worker variation

The only primary-event change is releasing Right at frame 1666 and restoring it
at 1667. Predicted before execution: exact primary evidence through frame 1665,
and the controller differs at frame 1666 only. Position/contact branch relevance
and any reconvergence are deliberately not predicted. The initial replay digest
fields are zero placeholders so the first run must fail those authored checks
while two fresh processes can still demonstrate mutual determinism.

## Decoded helper identity

The inclusive 68 bytes at ROM `$82:A96F--A9B2` (file offset `0x01296F`) hash to
`5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c`.
The supported PAL ROM identity is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
