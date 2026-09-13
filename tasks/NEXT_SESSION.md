# Coordinator handover — M4-10 accepted, M4-11 claimed

Milestone M3 is accepted on 13 September 2026 and tagged `m3`. M4-00 through
M4-10 are accepted and M4-11 is claimed. Read [M4-11](M4-11.md), [M4-10](M4-10.md),
[R-0028](../docs/research/R-0028-zoom-zoo-response-b.md) and its approved
[review](M4-10-review.md).

The accepted scope is the identified PAL one-player CRAWLER/DRAGSTER slice:
supported-ROM extraction creates a validated local Classic pack, later launches
work with the ROM absent, native gameplay reaches stable result without original
CPU execution, and live macOS controls/presentation plus exact macOS/Linux gates
pass. Audio, unrecovered intermediate rider artwork, other tracks/riders/modes,
menus/progression, local multiplayer and public packaging remain omissions.

M4-03 turns the accepted 50,665-byte ZOOM ZOO decode into a strict
reference-only contract: 24 tile ids plus terminator, 203 tiles, 406 ordered
transfers, 98 independently reconstructed rolling-gather bytes and 40 bounded
collision words across both riders. It directly observes width/stride 256/512,
rejecting blind reuse of DRAGSTER's 1024/2048. Independent review added a
matching frame-2000 collision sample and returned unenforced gather/capture
metadata; correction `029d0df` was approved. Merge `0856621` passes local
contract/replay/coverage/content/native gates and 325/325; hosted run
34727349602 passes macOS/Linux including Linux SDL sanitizers.

M4-05 classifies all 102 calls in frames 1650--1700 and reconstructs only the
first unsupported call, frame 1661 player point 9, as bounded captured-argument
research. Independent review found that per-point preprocessing was not
enforced before lossy reduction; correction `dabb3e5` binds all 30 ordered
tuples and re-review approved. Merge `34d6ea6` passes 321/321 plus all frozen
gates; hosted run 34733976248 is green on macOS/Linux including sanitizers.

M4-06 closes the complete 66-call/660-point vertical-contact episode through
frame 1682; its worker and reviewer onset cases close 72/720 and 74/740 before
their observed direction boundaries. Review returned the capture recipe, not
the equations; correction `814f787` and a doc-derived CLI test were approved.
Integration `3694406` and hosted run 34736840760 are green.

M4-07 closes the observed 36-call `0x4000` reflected/positive-slope suffix and
composes all 102 calls/1,020 points through frame 1700. Review returned semantic
binding and address citations; correction `cfa94e4` was approved, including a
correction to the reviewer's own off-by-one point-x range. Integration
`131df54` and hosted run 34738957270 are green.

M4-08 closes the reached position integrator for all 102 calls from one
end-1649 four-residue seed, including the slope tails and former `$82:A6E9`
gap. Independent review approved its own frame-1664 variation. Integration
`6de3dd5` and hosted run 34741431794 are green.

M4-09 composes recurrent positions/residues, the reached Y helper, authenticated
sampling and contact for all 102 calls/1,020 words through frame 1700. Review
approved its independent frame-1667 variation. Integration `c93de4d` and hosted
run 34744126458 are green.

M4-10 seeds and computes both response-B words across all 102 calls, closes the
opponent 254-to-0 gap with an ordered word clear and preserves the accepted
1,020-sample composition. Worker/reviewer variations both leave response B
unchanged. Integration `a8d9106` and hosted run 34747306845 are green.

Continue M4-11's Astra-defined vertical-velocity producer/recurrence. Its worker
preregisters a frame-1672 one-frame Right release; the independent reviewer owns
frame 1673 or 1674. Horizontal velocity, pose and remaining contact state are
still external; native ZOOM ZOO/pack remain unchanged.
The user authorized an unattended M4 continuation and at most one weekly usage
reset only if an actual provider limit is reached; no money, paid credits,
provider switching, publication or deployment is authorized.
