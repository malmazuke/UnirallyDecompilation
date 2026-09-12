# M4-01 focused independent re-review

- Verdict: **approved with no findings**.
- Reviewed immutable remote candidate:
  `7298c9798da7d7749dfd21f96a10cc7c97f15efd` from
  `origin/task/M4-01-loser-result`.
- Behavioral correction:
  `a3106f47c014cecdd2b236cd04405f96f710fc55`; original returned candidate
  `33bccb46df3ca25ef160cc04d79e9da1f5bfcdf6`.
- Reviewer: OpenAI Codex Sol/medium, 13 September 2026.
- Worktree/branch: `.worktrees/m4-01-rereview`,
  `review/M4-01-loser-result-rereview`. The candidate source was not changed;
  this report is the only tracked reviewer-owned change.

## F1 resolution

F1 is resolved. The result compositor now admits only the three observed
publication tuples:

- winner `ResultLoading`/225;
- winner `ResultScreen`/226;
- loser `ResultScreen`/242.

The predicate retains the existing finish ordering and digit/centisecond
checks. The correction is narrow: behavioral commit `a3106f4` changes only
`src/core/presentation.cpp`, the pack-backed test runner and the focused native
presentation test (40 additions, five deletions). It does not change movement
state layout/serialization, native manifests, frozen presentation contracts,
pack rules or gameplay expected values.

I recreated the original review mutation from the authenticated 371-byte
frame-3800 loser state by changing only little-endian bytes 365–366 from 242 to
241. The mutated state retained `ResultScreen`, `PlayerLost`, both finish times
and all digits; its SHA-256 remained the original review identity
`53fc2f2085b12b568874c15a8a69a7bb51c0f34948474ba495c3f0170cbc7216`.
Running it through the actual pack-backed `LivePresentation` executable now
exited 1 with `unsupported Classic result composition` and created no PPM:

```text
build/app-debug/src/app/live_presentation_runner \
  --content-pack local/classic-crawler-dragster.pack \
  --state artifacts/m4-01-rereview-boundaries/loser-result-screen-241.bin \
  --out artifacts/m4-01-rereview-boundaries/loser-rs241.ppm \
  --camera-x 0 --bg1-scroll-x 0 --bg1-scroll-y 0 \
  --bg2-scroll-x 0 --bg2-scroll-y 0
```

The exact authenticated counter-242 state passed the same runner, whose new
pack-backed check also derives counter 241 internally and requires rejection.
Its native PPM retained SHA-256
`f2a034e3248ba19984cbe61ae75d4235f70bba1c550a7fa021eea952ed23077d`.

## Winner and adjacent tuple checks

I exercised the existing winner states and four one-field adjacent mutations
through the same pack-backed executable. Results were:

| Tuple | Result |
| --- | --- |
| `ResultLoading`/225, `PlayerWon` | exit 0; accepted observed publication |
| `ResultScreen`/226, `PlayerWon` | exit 0; accepted observed stable state |
| `ResultLoading`/224, `PlayerWon` | exit 0; remains non-visible |
| `ResultLoading`/226, `PlayerWon` | exit 1; contradictory tuple rejected before output |
| `ResultScreen`/225, `PlayerWon` | exit 1; contradictory tuple rejected before output |
| `ResultScreen`/227, `PlayerWon` | exit 1; unsupported tuple rejected before output |

The two accepted publication outputs were byte-identical, SHA-256
`b5cf1100f278a74c7690662bfd4600e458e2693547b9a92b84133715ff75fbbb`.
The loading-224 output differed from the published result at 57,280/57,344
pixels, confirming it did not cross the frozen visibility boundary. Each
rejected tuple created no PPM. These cases independently cover the explicit
winner preservation requested by F1; the candidate test itself covers the
loser counter mutation.

## Visual and focused validation

The exact loser visual passed at the unchanged 1,073/57,344 mismatches
(1.871164%, limit 15%):

```text
python3 tools/project.py native presentation-check \
  --manifest tests/manifests/presentation/classic-crawler-dragster-loser-v1.json \
  --fixtures artifacts/m4-01-loser-fixtures \
  --content-pack local/classic-crawler-dragster.pack \
  --preset lab-debug --artifacts artifacts/m4-01-rereview-loser-visual \
  --report artifacts/m4-01-rereview-loser-visual/report.json \
  --task M4-01-rereview --timeout 120
```

Report SHA-256:
`87a91bbb7cbd57d9697e5fd12ca4145e387c93f324dcc539541b3c6ee67f6737`.
This command also exercised the new internal pack-backed prior-counter
rejection.

The original winner contract passed all eight required checks and retained the
seven exact mismatch counts `36, 697, 279, 445, 653, 962, 961`:

```text
python3 tools/project.py native presentation-check \
  --manifest tests/manifests/presentation/classic-crawler-dragster-v1.json \
  --fixtures artifacts/m3-02-integration-fixtures \
  --content-pack local/classic-crawler-dragster.pack \
  --preset lab-debug --artifacts artifacts/m4-01-rereview-winner-visual \
  --report artifacts/m4-01-rereview-winner-visual/report.json \
  --task M4-01-rereview --timeout 120
```

Report SHA-256:
`c31663cf0693cdbdc575a2a43e3539746b8c764fe896e2fd70a7b48a3e79c959`.

Focused native and tooling checks passed:

```text
local/toolchain/cmake-3.31.10-darwin-arm64/bin/ctest \
  --test-dir build/app-debug \
  -R 'presentation_gather_mapping_and_determinism|frontend_scheduler_input_display_contract' \
  --output-on-failure
# 2/2 passed

PYTHONPATH=tools python3 -m unittest discover \
  -s tests/tooling -p 'test_native_presentation.py' -v
# 4/4 passed

local/toolchain/cmake-3.31.10-darwin-arm64/bin/ctest \
  --test-dir build/app-debug -R movement_state_roundtrip --output-on-failure
# 1/1 passed
```

The exact build command passed from a fresh build directory; report SHA-256
`0ed004e77c383c8516098f75b3d2f094e3ae2af8c7c76f969248db69a7a9fe54`:

```text
python3 tools/project.py build --preset app-debug \
  --report artifacts/m4-01-rereview-build-debug.json
```

`git diff --exit-code 33bccb4..a3106f4 --` over movement source/header,
movement-state tests, finish parsing, native manifests and presentation
manifests exited 0. `git diff --check 33bccb4..7298c97` passed. Private pack,
states, frames, generated outputs and build reports remained ignored; no
baseline or generated content was tracked.

The coordinator may proceed with exact-candidate integration and its required
CI/remote synchronization. This review does not itself mark M4-01 accepted,
integrate, push, publish or deploy.
