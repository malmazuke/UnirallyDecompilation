# Coordinator handover — M4-00 inventory candidate

Milestone M3 is accepted on 13 September 2026 and tagged `m3`. M4-00 now has a
documentation candidate on `task/M4-00-feature-inventory`; read
[the task](M4-00.md) and [R-0018](../docs/research/R-0018-m4-feature-inventory.md).
It reconciles the root README, separates accepted native/reference-observed/menu-
label/unobserved coverage and writes two bounded next work orders. Independent
review is still required before M4-00 acceptance.

The accepted scope is the identified PAL one-player CRAWLER/DRAGSTER slice:
supported-ROM extraction creates a validated local Classic pack, later launches
work with the ROM absent, native gameplay reaches stable result without original
CPU execution, and live macOS controls/presentation plus exact macOS/Linux gates
pass. Audio, unrecovered intermediate rider artwork, other tracks/riders/modes,
menus/progression, local multiplayer and public packaging remain omissions.

The bounded user-requested Astra/high audit found one material sequencing issue:
the release-3000 loser gameplay is exact through stable result, but the visual
contract has winner results only and `src/core/presentation.cpp` rejects
`PlayerLost`. [M4-01](M4-01.md) therefore closes the existing DRAGSTER loser
result first. [M4-02](M4-02.md) performs second-track reference discovery next;
ZOOM ZOO is currently a menu label only, so it must observe opponent/event
coupling before claiming track-only isolation.

Review the candidate, including at least one challenged matrix classification,
README accuracy and the work-order boundaries. After approval, the coordinator
may integrate/accept M4-00 and claim M4-01. Preserve every frozen M3 identity and
regression. Publishing, deploying, spending money or redeeming usage credits
still requires separate authority.
