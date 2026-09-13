# M4-11 preregistered vertical-velocity inventory

Preregistered at claim `e21e87b6e1de390f92a77e2c3f00596df90dc627`, before
any new M4-11 capture or replay result. The accepted M4-10 composition and its
captures remain frozen comparison foundations.

## Combined watch set and order hypothesis

The additive capture spans end-of-frame 1649 through frame 1700 and retains the
complete accepted M4-10 watch set. It adds persistent vertical-velocity words
`$04BF/$04C1`, scratch `$0FAB`, their adjacent horizontal and jump-state words,
both riders' jump latch/phase/baseline/input state, vertical-cap/boost state,
rider and active phase, controller words, cap/inhibit/mode guards, and update
counter. Address watches expose every actual reader and writer, including any
writer outside the hypothesized motion ranges.

Every byte in `$82:A81A--A9B2` is a PC watch. This superset covers the declared
vertical cap `$82:A81A--A872`, speed tail and jump dispatch, jump body through
`$82:A96E`, and gravity `$82:A96F--A9B2`, without presuming which instruction
starts or branches are reached. Accepted motion load/publication, integrator,
contact entry, vertical response publication at `$81:8E28/$81:8F7C`, and
contact return landmarks preserve exact same-rider order.

Hypotheses to reject or confirm are:

1. each rider's persistent word loads once to `$0FAB`, is capped before jump,
   consumed/possibly replaced by active-phase jump, then consumed by gravity;
2. the cap uses the original wrapped subtraction predicates and 16-bit word
   stores, with the ordinary mode-0 cap derived from the current speed extra;
3. jump is active-phase-only and follows the latch/held-phase recurrence, with
   reached impulse comparison and word-width semantics; absence of a later jump
   branch must be observed rather than assumed from earlier coverage;
4. gravity tests wrapped `vy - 0x0200`, distinguishes the original velocity's
   negative/nonnegative path, performs five logical right shifts only on the
   nonnegative path, and adds in original order before position integration;
5. contact publication is the sole post-integration velocity feedback before
   the next same-rider cycle, and every reached contact preserve/clear/response
   writer must agree with the accepted M4-05--M4-07 equations.

Reached writers, exact guards, cap inputs, jump branch counts, gravity formula
counts and short-circuited input availability are results to be measured. No
later captured vertical velocity may become an evaluator input: recurrence
seeds `$04BF/$04C1` once from end-1649 and carries computed contact output into
the next same-rider motion cycle.

## Worker variation

Release Right only at frame 1672 and restore it at 1673. The sole prediction is
exact primary evidence through frame 1671 and controller divergence at frame
1672 only. Velocity, contact and composition relevance and reconvergence are
not predicted. Zero replay digests are intentional placeholders, so the first
replay comparison must fail those expectations while still testing two fresh
processes for agreement.

## Boundary

The supported PAL ROM is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
the pinned core is `7d5aa1e656b9171524d01b1b22917197d8121cb4` with patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`.
Horizontal velocity, pose/reflection, controller/jump state and remaining
contact state stay captured external inputs. This bounded twelve-word recurrence
cannot establish native ZOOM ZOO gameplay.
