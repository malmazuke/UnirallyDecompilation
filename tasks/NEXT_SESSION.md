# Coordinator handover — M4-03 accepted, M4-04 planning next

Milestone M3 is accepted on 13 September 2026 and tagged `m3`. M4-00 through
M4-03 are accepted. Read [M4-03](M4-03.md),
[R-0021](../docs/research/R-0021-zoom-zoo-content-contract.md), its returned
[review](M4-03-review.md) and approved [re-review](M4-03-rereview.md).

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

Use a bounded Astra/high planning consultation to select and write one narrow
M4-04 work order from the accepted M4-03 evidence before claim. Native ZOOM ZOO
is still unsupported: full autonomous movement/contact, finish/result and
presentation are not established, and the Classic pack is unchanged. Preserve
all frozen M3/M4 identities. The user authorized an unattended M4 continuation
and at most one weekly usage reset only if an actual provider limit is reached;
no money, paid credits, provider switching, publication or deployment is
authorized.
