# Coordinator handover — M4-01 accepted, M4-02 ready

Milestone M3 is accepted on 13 September 2026 and tagged `m3`. M4-00 and M4-01
are accepted. Read [M4-01](M4-01.md),
[R-0019](../docs/research/R-0019-dragster-loser-result.md) and its returned
[review](M4-01-review.md) plus approved [re-review](M4-01-rereview.md).

The accepted scope is the identified PAL one-player CRAWLER/DRAGSTER slice:
supported-ROM extraction creates a validated local Classic pack, later launches
work with the ROM absent, native gameplay reaches stable result without original
CPU execution, and live macOS controls/presentation plus exact macOS/Linux gates
pass. Audio, unrecovered intermediate rider artwork, other tracks/riders/modes,
menus/progression, local multiplayer and public packaging remain omissions.

M4-01 closes the stable release-3000 loser result with an additive authenticated
visual contract and no pack change. The observed screen retains the winner
layout, displays `MIKE 0:35.66`, and differs at exactly six result-map bytes.
Behavioral correction `a3106f4` rejects the reviewer's impossible counter-241
publication state; focused re-review approved it. Merge `3058eb9` passes local
debug/sanitizer 315/315, exact winner/loser visuals, release/restores, and hosted
macOS/Linux run 34719187215.

Start ready [M4-02](M4-02.md) with its bounded Astra/high planning consultation,
then return execution to Sol/medium. Its first evidence gate injects one short
Down press at the CRAWLER track screen and observes selection, opponent and
event/rule coupling before any tracked replay is frozen. Preserve every frozen
M3/M4-01 identity and regression. Publishing, deploying, spending money or
redeeming usage credits still requires separate authority.
