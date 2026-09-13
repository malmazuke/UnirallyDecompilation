# M4-05 independent review

- Candidate: `1ba60cea29a5b2733eb92fe4e2ea6d6656e4e37c`
- Implementation: `4c07f99b8da040f629d73f1442b9808b8057e007`
- Base: `93a9efe6c40248d9dcd28137e54861d3c38aa3b7`
- Reviewer: fresh OpenAI Sol/medium review in
  `.worktrees/m4-05-review`
- Status: review complete; returned with one blocking finding; the coordinator
  alone decides acceptance

## Withheld variation preregistration

Before creating or executing the reviewer replay, choose first Right at frame
1651, one update later than the accepted primary onset and distinct from the
worker's frame-1652 (+2) case. Retain the frame-3299 release boundary and every
other event. Predict exact whole-state and declared-field agreement through
end-frame 1649, with the first controller/state difference at frame 1650. Do
not predict the first incompatible-contact frame or player-contact
reconvergence. Expect the opponent's captured contact path to remain unchanged
if it is independent of this one-frame player-input shift; report the observed
result rather than treating that expectation as a required pass.

## Review result

**Verdict: return for one acceptance-blocking verification gap.** The original
capture, classification, first branch equations and reviewer variation all
reproduce, and no production or frozen-data regression was found. However,
`verify_neighbourhood` independently computes each point's preprocessing tuple
and then reduces it without ever comparing those tuples to the captured
`observed_penetrations`, `observed_angles` and `observed_descriptors`. Thus the
component does not enforce its claim that preprocessing itself matches exactly,
and its focused tests do not reject that contradiction. The coordinator alone
decides acceptance; this review does not mark M4-05 accepted.

## Primary reproduction and code inspection

The review used the exact candidate above. The worktree initially had no
`local/` runtime. The first capture therefore exited 2 with a required
`core_available` missing result. After retaining that failed report, I supplied
only ignored narrow links to the existing `emulators`, `toolchain` and
`rom-location.txt`; no tracked private/generated input was added.

Fresh extraction and capture reproduced:

| Item | SHA-256 / result |
| --- | --- |
| primary access, frames 1650--1700 | `267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67` |
| extracted content metadata | `7352761224b68a5e5e22f60992d1462f9d29e721d6d862e29783371471bcbb2b` |
| primary component report | `6e8a6d5aaedbbc7190b0a336b70913ec815ac4c69ca58b0256b5c2035123fea2` |
| compact classification | `4f4c7fc0e0e6bf4fe89bfdaafe0d8fcc4824eb9214930507a17e42c97ec15dc4` |

The access record is complete and nontruncated, with no ring overflow,
unresolved store, PC outside ROM or resolution conflict. It contains ordinals
0--101 exactly as player/opponent pairs for every frame 1650--1700. Independent
enumeration gives 67 compatible calls, 17 first-failing `non_flat_angle` calls
and 18 first-failing `direction_or_special` calls. The first incompatibility is
ordinal 22, frame 1661 player, point 9, non-flat angle.

The reconstructed target has incoming x/y 9258/1562 and vx/vy 287/19. Static
content produces descriptor `0x0020`, tile 8, height/angle `0xff/0xff`,
penetration and correction 2. The unchanged candidate equations produce
x/y 9258/1560, vx 287 and vy `0xfff0` (-16), with the reported surface,
selection, saved coordinates, counters and adjacent opponent outputs all exact.
I separately compared all 30 recomputed preprocessing tuples in the three-call
neighbourhood with the capture; all 30 happen to agree despite the enforcement
gap below.

Frame 1650 independently contains player descriptors nine `0x5800` plus one
`0x1ae6`, and ten opponent `0x7800`. R-0011 records the original marker-first
order; unchanged production `src/core/flat_contact.cpp` SHA-256
`b0601e494d0b03f052b8b7f265dcf0e6c6fac066f40ee8ba0831d8ccda68a0a3`
tests `(descriptor & 0x03ff) == 0` before `(descriptor & 0xc001) == 0` at
lines 38--39. Therefore all `0x5800`/`0x7800` words are marker-only and
`0x1ae6` passes the direction mask. The R-0022 correction is accurate and
changes prose only; no accepted projection or expected byte changed.

## Withheld frame-1651 onset

The ignored reviewer manifest SHA-256 is
`1921f07a12f22915c1e3cb92158fdd38dc1fd885cdead2695d7d0f5f6ce34004`.
The initial discovery run deliberately retained primary expectations and
failed only the two stale identity checks; its report hashes to
`7f46276c82a7d5476e6ca6ed520de11ecb8776eb237d081f9b470257cdf3a5ac`.
After binding the observed identities, two new processes reproduced sample
digest `f488e5dfedf49f164b0d72ebc8cb7cfb3498b7ca54bf2ba6d515bdc367cfa329`,
final state `8c0a7181ba45423b72805705c7057c90559e8b2c11c25e52a1102746b1a36040`
and A/V `8c49b468ff01f80b74c99d03cd7ae1e0a491df73f60adb51f4fc968338c44a44`.
The passing repeat report hashes to
`c2b4bf3aa113f5133e89e860634b4ea39c8de2c37f950df34a7c5001ee3b5363`.

Primary and reviewer runs agree through end-frame 1649 and first differ at
1650 in the declared fields, exactly as preregistered. The expected behavioral
comparison exits 1 and its report hashes to
`3c7d2d8db44535fb94db62b9d24e79507c9cd05b50ffd110cc199d06777f990d`.

The reviewer access SHA-256 is
`0454d2abb27fbb406b423883bd65ee3eede9c7dcee1b9b90e4dce958b906f130`;
it again contains all 102 ordered calls. Without editing the candidate
equations, classification gives 69 compatible, 16 non-flat and 17
direction/special calls, digest
`f8b271122cbcb1b303f02ebdbc67d6895d42a879152456b6d7cee9f221af03c3`.
The first incompatibility shifts to ordinal 24, frame 1662 player point 9.
Incoming y 1563 yields penetration/correction 3 and final y 1560; x 9258,
vx 287 and predicted vy -16 all match. The reviewer equation report hashes to
`675f9f2ca3e481272ecf304b55856c961f2771ac426b7b5e1c954d67f60b7723`.

The player call record does not fully reconverge on any frame through 1700.
Opponent raw samples, penetration, angles, descriptors, reduction, response and
publication are exact on all 51 frames. Some opponent snapshots of irrelevant
shared scratch (notably unwritten marker-axis slots) differ after the player
call, so it would be inaccurate to call every captured opponent argument byte
identical. Across the primary record, 633 axis slots are absent only on samples
already classified marker-only; every non-marker axis dependency is present.

## Blocking finding

`tools/unirally_lab/native/zoom_zoo_contact.py:385-400` computes `probes`, then
compares only the lossy reduced summary. It never compares the computed point
tuples with the capture arrays used by `classify_calls`. This reproducer changes
all three captured target preprocessing results while leaving the independent
calculation and later captured summary/output untouched:

```sh
PYTHONPATH=tools python3 - <<'PY'
import copy, json
from pathlib import Path
from unirally_lab.native.zoom_zoo_contact import (
    captured_calls, load_content, verify_neighbourhood,
)
calls = captured_calls(json.loads(Path(
    'artifacts/m4-05-review/primary-1650-1700/access.json').read_text()))
mutated = copy.deepcopy(calls)
mutated[22]['observed_penetrations'][9] = 7
mutated[22]['observed_angles'][9] = 0
mutated[22]['observed_descriptors'][9] = 0x0030
rows = verify_neighbourhood(
    mutated, load_content(Path('artifacts/m4-05-review/content')), 22)
print('UNEXPECTED_PASS', rows[1]['summary'])
PY
```

It prints `UNEXPECTED_PASS` with the original `(2, 0xff, 0x0020)`-derived
summary. The outer access SHA check proves that a known capture was supplied;
it does not test whether the component's independently computed preprocessing
matches that capture. This is directly within the acceptance requirements for
independent preprocessing and captured-result mutations.

Required correction: for the preceding, target and following calls, compare
each computed `(penetration, angle, descriptor)` tuple to the corresponding
captured arrays before reduction, report the exact comparisons, and add a
focused test showing a contradictory captured tuple fails. Keep the existing
reference data and equations unchanged. A focused re-review can then repeat the
mutation and component commands.

## Regression, mutation and hygiene results

- `python3 -m unittest tests.tooling.test_zoom_zoo_contact -v`: 7/7 pass. It
  covers call loss/duplication/swap/rider/ordinal, source/guard/content identity,
  marker precedence, classification, slope response, state/coefficient changes
  and one incomplete-access case, but not the contradiction above.
- Debug synthetic report
  `56659111a67e65120f55f8616d3dbe8b6a90550bf32db56a1b4de309e247dec2`:
  320/320 Python records, 20/20 CTest checks and three-process determinism pass.
- Sanitizer serial report
  `c07fe44676929c0d689e380f83272b9e7d74107d8d51d47afb22d899d4007f50`:
  the same 320/320, 20/20 and determinism checks pass. An earlier concurrent
  debug/sanitizer attempt caused the suites' shared `lab-failure-probe` build
  to collide and accurately failed two harness tests; retained failed report
  `05e20b40247912853cd23ae176b165d46c7ebe5c29535e3d3cc5c8d229ccb061`.
  The serial rerun establishes this was review orchestration, not a candidate
  regression.
- M4-03 content contract passes 3/3, report
  `04b0c4259d6ff2a6a4cf1fc040298977effddc7f099b8034012194e2e951b08b`.
  M4-04 pair verification remains first divergence 2500 in exactly its seven
  fields with no finish transition.
- Classic pack inspection passes 3/3, report
  `7e939c10133065bdb983ffefd49247cbf98694925c58b39867666281a13680f6`.
  The unchanged DRAGSTER full-race and four restore boundaries pass 18/18,
  report
  `0f995488f0f16b2cb65cb027196b901638adf45115439ddd9fa024620e051fee`.
- `git diff --check 93a9efe..1ba60ce` passes. Candidate changes are confined to
  the declared additive research tool/tests/manifests, documentation and task
  record. Production native, serialization, pack/profile/start, accepted
  projections, core and locks are unchanged. Generated captures, ROM-derived
  content, build products and narrow local links remain ignored. The candidate
  handoff says 19 CTest checks, but both its own reports and this review contain
  20; correct that minor count when addressing the blocking finding.

Principal reproduction commands:

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_contact extract-content --contract tests/manifests/content/zoom-zoo-reference-contract.json --rom "$(sed -n '1p' local/rom-location.txt)" --out artifacts/m4-05-review/content
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-05-review/primary-1650-1700 --from-frame 1650 --to-frame 1700
python3 -m tools.unirally_lab.native.zoom_zoo_contact verify --access artifacts/m4-05-review/primary-1650-1700/access.json --content artifacts/m4-05-review/content --manifest tests/manifests/native/zoom-zoo-contact-reference.json --report artifacts/m4-05-review/primary-component-report.json
python3 tools/project.py replay compare --manifest artifacts/m4-05-review/withheld/right-1651.json --runs 2 --artifacts artifacts/m4-05-review/withheld/repeat --report artifacts/m4-05-review/withheld/repeat-report.json --task M4-05-review
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest artifacts/m4-05-review/withheld/right-1651.json --out artifacts/m4-05-review/withheld/contact-1650-1700 --from-frame 1650 --to-frame 1700
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --against artifacts/m4-05-review/withheld/right-1651.json --artifacts artifacts/m4-05-review/withheld/against-primary --report artifacts/m4-05-review/withheld/against-primary-report.json --task M4-05-review
python3 tools/project.py test --suite synthetic --preset lab-debug --artifacts artifacts/m4-05-review/synthetic-debug/artifacts --report artifacts/m4-05-review/synthetic-debug/report.json --task M4-05-review
python3 tools/project.py test --suite synthetic --preset lab-sanitize --artifacts artifacts/m4-05-review/synthetic-sanitize-serial/artifacts --report artifacts/m4-05-review/synthetic-sanitize-serial/report.json --task M4-05-review
```
