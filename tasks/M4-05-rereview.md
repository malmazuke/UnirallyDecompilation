# M4-05 focused independent re-review

- Corrected candidate: `050e7f1f1ed09e0535bda2d0ff260a5eac20b891`
- Correction implementation: `dabb3e5a07ce5acde7d47eb35d0425491568ae1b`
- Prior review: [M4-05-review](M4-05-review.md), commit
  `f9a486e753d7e9ce91e9eb8e83b04537af7b9c04`
- Review branch/worktree: `review/M4-05-zoom-zoo-contact-rereview`,
  `.worktrees/m4-05-rereview`
- Reviewer: fresh OpenAI Sol/medium session, 13 September 2026
- Verdict: **approve**. The returned per-point preprocessing enforcement gap is
  resolved; no new finding.

## Correction inspection

`verify_neighbourhood` now calls `compare_preprocessing` immediately after
independently computing each call's ten probes and before reducing them. The
comparison requires exactly ten computed and ten captured tuples, preserves
point order, and exact-compares penetration, angle and descriptor. A mismatch
raises with frame, rider, point and both tuples. A passing report exposes the
computed and captured values plus `match: true` for every point on the
preceding, target and following calls.

The focused regression constructs the formerly hidden contradiction by changing
only target point 9's captured tuple from `(2, 255, 32)` to `(7, 0, 48)` while
leaving the separately captured support summary unchanged. Focused tests pass
8/8, including that exact rejection.

## Returned-defect and adjacent mutation reproduction

I independently loaded the exact-gated primary access record and content,
called `verify_neighbourhood` once without mutation, then deep-copied the calls.
The returned-defect mutation changes the three point-9 captured arrays on
ordinal 22 and leaves `support_summary == 2`. The original independently
reduced summary remains supported, correction 2, angle 255 and selected word
32. Verification rejects exactly:

```text
computed preprocessing differs at 1661/0 point 9: computed (2, 255, 32), captured (7, 0, 48)
```

I also challenged the preceding call, ordinal 21, by changing only point 0's
captured descriptor from 0 to 1 while preserving `support_summary == 255`.
Verification rejects exactly:

```text
computed preprocessing differs at 1660/1 point 0: computed (160, 0, 0), captured (160, 0, 1)
```

Both failures occur at the preprocessing comparison before reduction. The
principal reproducer was:

```sh
PYTHONPATH=tools python3 - <<'PY'
import copy, json
from pathlib import Path
from unirally_lab.native.zoom_zoo_contact import (
    captured_calls, load_content, verify_neighbourhood,
)
access = Path('/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m4-05-zoom-zoo-contact/artifacts/m4-05/final-primary-1650-1700/access.json')
content_path = Path('/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m4-05-zoom-zoo-contact/artifacts/m4-05/content')
calls = captured_calls(json.loads(access.read_text()))
content = load_content(content_path)
original = verify_neighbourhood(calls, content, 22)
mutated = copy.deepcopy(calls)
mutated[22]['observed_penetrations'][9] = 7
mutated[22]['observed_angles'][9] = 0
mutated[22]['observed_descriptors'][9] = 0x0030
assert mutated[22]['support_summary'] == calls[22]['support_summary'] == 2
try:
    verify_neighbourhood(mutated, content, 22)
except ValueError as exc:
    print(exc)
else:
    raise SystemExit('UNEXPECTED PASS: target mutation')
adjacent = copy.deepcopy(calls)
adjacent[21]['observed_descriptors'][0] = 1
assert adjacent[21]['support_summary'] == calls[21]['support_summary'] == 255
try:
    verify_neighbourhood(adjacent, content, 22)
except ValueError as exc:
    print(exc)
else:
    raise SystemExit('UNEXPECTED PASS: adjacent mutation')
PY
```

An initial version of my review script incorrectly looked for an
`observed_summary` key instead of the actual `support_summary` field and exited
with `KeyError`; it did not exercise the candidate and is not counted as a
candidate failure. The corrected command above performed both mutations.

## Full ordered preprocessing reports

Each item below is `(penetration, angle, descriptor)` in point order 0 through
9. Every item has identical `computed` and `captured` objects and
`match: true`; each report contains exactly three calls and 30 items.

Primary, access SHA-256
`267ecfbf7223a3c2a9e6844d620feda0c41adb98fd9a5280d10320d3682fab67`:

```text
1660/rider 1: [(160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0)]
1661/rider 0: [(160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (2,255,32)]
1661/rider 1: [(160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0)]
```

Worker variation, access SHA-256
`0f04150363bdfbf41f53ca192ee091529c36933950bfb74daa6eea8001178dec`:

```text
1662/rider 1: [(160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0)]
1663/rider 0: [(160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (3,255,32)]
1663/rider 1: [(160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0), (160,0,0)]
```

The primary order is preceding opponent, target player, following opponent at
frames 1660/1661. The variation order is the corresponding 1662/1663 window.
The target point alone changes from penetration 2 to 3, as already frozen by
the unchanged captures; descriptor and angle remain 32 and 255.

## Focused validation

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_contact -v
# Ran 8 tests in 0.001s -- OK

python3 -m tools.unirally_lab.native.zoom_zoo_contact verify \
  --access '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m4-05-zoom-zoo-contact/artifacts/m4-05/final-primary-1650-1700/access.json' \
  --content '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m4-05-zoom-zoo-contact/artifacts/m4-05/content' \
  --manifest tests/manifests/native/zoom-zoo-contact-reference.json \
  --report artifacts/m4-05-rereview/primary-component-report.json

python3 -m tools.unirally_lab.native.zoom_zoo_contact verify \
  --access '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m4-05-zoom-zoo-contact/artifacts/m4-05/variation-contact-1650-1700/access.json' \
  --content '/Users/markfeaver/Projects/Unirally Decompilation/.worktrees/m4-05-zoom-zoo-contact/artifacts/m4-05/content' \
  --manifest tests/manifests/native/zoom-zoo-contact-right-1652.reference.json \
  --report artifacts/m4-05-rereview/variation-component-report.json
```

Both verifies pass. The primary report has SHA-256
`01cc1b5cc27c7c03b20825f4f1daa4eddf86c7514a5c5e3b258548812fadac70`
and retains classification SHA-256
`4f4c7fc0e0e6bf4fe89bfdaafe0d8fcc4824eb9214930507a17e42c97ec15dc4`
and first incompatibility ordinal 22, frame 1661, rider 0, point 9. The
variation report has SHA-256
`89f46dd8406453b06eec24258215d61ac43e77b2622485e940f92745d014f0fc`
and retains classification SHA-256
`bb5aa59d1bc6a6e6ac0084b44767a194df37bf91c9af929350a4da8bcaca3c2d`
and first incompatibility ordinal 26, frame 1663, rider 0, point 9.

## Scope and hygiene

`git diff --check f9a486e..050e7f1` passes. The correction range changes only
four text files: 31 additions/one deletion in the research verifier, 17 test
additions, 15 additions/10 deletions in R-0023 and 48 additions/two deletions in
the task handoff. The `src` and complete `tests/manifests` tree objects are
unchanged, as are `docs/STATE.md` and `tasks/README.md`; this fixed-scope check
exits 0:

```sh
git diff --quiet f9a486e..050e7f1 -- \
  src tests/manifests docs/STATE.md tasks/README.md
```

No production native code, serialization, Classic pack/profile/start, accepted
projection/replay/content manifest, core, lock, coordinator state or registry
changed. No ROM, decoded content, capture, report or generated artifact is
tracked by the correction or this review.

The coordinator may integrate this exact candidate and perform the required
integration and private-remote checks. This re-review does not mark M4-05
accepted and does not edit coordinator-owned state or the task registry.
