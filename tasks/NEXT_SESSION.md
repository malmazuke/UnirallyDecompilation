# Coordinator handover — M4-02 accepted, M4-03 ready

Milestone M3 is accepted on 13 September 2026 and tagged `m3`. M4-00 through
M4-02 are accepted. Read [M4-02](M4-02.md),
[R-0020](../docs/research/R-0020-zoom-zoo-reference.md), its returned
[review](M4-02-review.md) and approved [re-review](M4-02-rereview.md).

The accepted scope is the identified PAL one-player CRAWLER/DRAGSTER slice:
supported-ROM extraction creates a validated local Classic pack, later launches
work with the ROM absent, native gameplay reaches stable result without original
CPU execution, and live macOS controls/presentation plus exact macOS/Linux gates
pass. Audio, unrecovered intermediate rider artwork, other tracks/riders/modes,
menus/progression, local multiplayer and public packaging remain omissions.

M4-02 freezes a deterministic 3,300-frame ZOOM ZOO reference path while
retaining the displayed 1P/MIKE/CRAWLER/BRONSEN/three-lap Race context. Its
scenario-level coverage delta and targeted load/access evidence identify a
6,599-byte packed `0xC3` object that decodes to 50,665 ignored bytes. Review
reproduced the behavior with an adjacent release boundary and returned only a
missing exact regeneration command; correction `6f38439` was approved. Merge
`77885be` passes local replay/coverage/content/native gates and 315/315; hosted
run 34722527701 passes macOS/Linux including Linux SDL sanitizers.

Start ready [M4-03](M4-03.md) with its bounded Astra/high planning consultation,
then return execution to Sol/medium. Recover and validate the ZOOM ZOO decoded
layout, tile-set selection, rolling gather and bounded collision/physics inputs
against runtime reads before any native or Classic-pack expansion. Preserve all
frozen M3/M4 identities. Publishing, deploying, spending money or redeeming
usage credits still requires separate authority.
