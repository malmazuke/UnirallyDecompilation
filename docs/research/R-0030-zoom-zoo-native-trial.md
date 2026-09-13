# R-0030 — M4-12 native capability trial (in progress)

No autonomous capability is accepted. The playable product remains DRAGSTER.

## Reference contract before whole-update tuning

The additive `tests/manifests/native/zoom-zoo-trial-primary.reference.json`
freezes end-1649 and all 200 updates through 1849. Its 394-byte projection
contains the established semantic movement layout (including actual original
transition rejection words projected to their binary fields), fifteen additional
words per rider and the opponent horizontal input byte. The added fields cover
reflection step/end/table base/pose override/completion/hold, drive-pose enable,
reflection air turns, direction latch, base velocity cap, synthesized brake,
rotation and jump inputs, and the wrong-direction counter. The controller is
Right on port zero through the full horizon; port one is neutral.

The first 333 bytes follow `prepare.py:canonical_seed` and
`movement.cpp:serialize_movement_state`, with the new `URZZ0001` identity and
actual frame number. This is a reference projection, not permission to accept
unvalidated native input. Runtime validation, serialization and restores are
still to be implemented. The native-only transient rejection placeholder in the
old seed writer is replaced by reads from `$0FD1/$0FD3` in the reference tool;
no expected byte is supplied by a native result or missing-input default.

`zoom_zoo_trial_reference.py` captures WRAM and cartridge RAM directly from two
fresh original processes. Every observed frame's whole-WRAM hash must match the
unchanged accepted primary replay. Both processes produce identical projections
with row digest `0588e60a73b79948567e1e5ec692e4cdf95cf9ee5a315905a9f556652e931568`.
The seed matches the complete original M4-04 WRAM and cartridge identities.
Original bytes, projected rows and traces remain ignored under `artifacts/m4-12`.
The tracked contract stores hashes and field/source metadata only.

## Dependency audit and pending closure

The two expanded access captures agree exactly. They cover every original
instruction from 1649 through 1849, including 3,679,052 instructions and
1,821,598 accesses. The ordered watches cover the accepted M4-11 surface plus
persistent-state neighborhoods and both displacement histories. No store is
unresolved, no watch is truncated and no memory resolution conflicts occur;
4,400 unresolved **reads** remain in the aggregate and require classification
before dependency closure can be claimed.

Dispatcher loads at `$82:89xx--8C2D` identify the prior-frame semantic fields.
Matched scratch stores and subsequent routine accesses distinguish persistence
from overwritten temporaries. `$0BC3`, for example, supplies a per-update
animation override that `$81:8681` clears before use; `$0E03`, conversely,
feeds the ongoing reflection counter at `$82:A3B3` and must persist. The
additional scoped mode/input guards in the reference tool are read directly
from the seed and remain unchanged over all 201 observed states. This is an
inventory and tested-domain observation, not yet proof of autonomous closure.

Static content uses the accepted ZOOM ZOO track/columns/flags/pose extraction,
identity-verified common DRAGSTER motion tables, and the 128-byte reflection
pose table at PAL `$82:A2DB` used by `$82:A447`. All seventeen files are bound
by byte length and SHA-256 in the additive contract. Future missing static
inputs require an explicit additive contract supplement before their tuning;
accepted identities must not be replaced.

The longer interval reaches opponent reflection and new recontacts at 1778
and 1823. The latter reaches a special tile/landing velocity transform absent
from the accepted short component. Full reference coverage is frozen at 1849;
it must not be shortened to avoid these branches.

## Early native component

`vertical_contact.*` ports the accepted direct/mirrored vertical preprocessing,
ordered signed-byte reduction and bounded continuous/sentinel response into
C++. It is separate from the accepted flat contact implementation. The probe
matches all eighteen motion/contact outputs on the 102 calls from 1650--1700.
This component uses captured incoming arguments in its research probe; it does
not demonstrate autonomous movement. The C++ port preceded the expanded whole-
update freeze but was compared only to the already-frozen short component.
No whole-update implementation or expanded native tuning preceded the freeze.

A first diagnostic compared a stale scratch duration after an unknown RMW and
reported a one-unit mismatch at 1650/opponent. Using the caller's publication
(the accepted evidence method) resolves it without native arithmetic changes.
Preserve that distinction when inspecting traces: unknown RMW values are not
observed output values.

## Reproduction at this checkpoint

- Expanded capture: exact argument arrays are in
  `artifacts/m4-12/expanded-primary-{a,b}/command.json`; these invoke the
  existing bounded `tools/project.py access capture` surface and preserve its
  original replay expectations. The source/watch recipe will be promoted into
  the trial tooling before review.
- Projection: `python3 -m tools.unirally_lab.native.zoom_zoo_trial_reference
  --access-dir artifacts/m4-12/expanded-primary-a
  --out artifacts/m4-12/reference-final-a.json` (fresh output required);
  repeat with the independent capture and output `b`, with a 90-second bound.
- Startup and early component commands/results are recorded in M4-12.

Independent variations, native autonomy, restore, full regressions, independent
Sol review, hosted CI and integration are outstanding.
