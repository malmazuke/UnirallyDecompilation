# Coordinator handover — M4-05 accepted, M4-06 claimed

Milestone M3 is accepted on 13 September 2026 and tagged `m3`. M4-00 through
M4-05 are accepted. Read [M4-05](M4-05.md),
[R-0023](../docs/research/R-0023-zoom-zoo-contact.md), its returned
[review](M4-05-review.md) and approved [re-review](M4-05-rereview.md).

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

Continue [M4-06](M4-06.md) in its isolated Sol/medium worktree. Its bounded
Astra/high audit found the continuous prefix fails earlier than frame 1683:
frame 1662 hides angle -2 and negative penetrations behind the lossy selected
summary, frame 1665 enters with negative vertical velocity, and support is lost
then reacquired before another response guard at 1677. Reconstruct all 66 calls
on frames 1650--1682, not the direction branch. Native ZOOM ZOO,
finish/result/presentation and the Classic pack remain unchanged.
The user authorized an unattended M4 continuation and at most one weekly usage
reset only if an actual provider limit is reached; no money, paid credits,
provider switching, publication or deployment is authorized.
