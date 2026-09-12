# M4-01 independent review — DRAGSTER loser result

- Verdict: **returned for correction; not approved**.
- Reviewed immutable remote candidate:
  `33bccb46df3ca25ef160cc04d79e9da1f5bfcdf6` from
  `origin/task/M4-01-loser-result`.
- Task base: `5c3eec786fbbd311236bbb4d80492dfdcb64bd8e`;
  evidence freeze `74112e76a8c9557b7e91bc63f156af32dc751c4c`;
  implementation `f43874160457eeb591130d964a6b0b096435006e`.
- Reviewer: fresh OpenAI Codex Sol/medium session, 13 September 2026.
- Worktree/branch: `.worktrees/m4-01-review`,
  `review/M4-01-loser-result`. Write ownership is this report only; the
  candidate source was not changed.

## Finding

### F1 — P2: impossible loser publication state renders a plausible result

The new result validation does not bind `ResultScreen` to the observed result
loading counter. In `src/core/presentation.cpp`, `observed_phase` accepts every
`ResultScreen` value regardless of `result_loading_updates`. The accepted loss
path has one exact adjacent boundary: frame 3799 is `ResultLoading`/241 and
frame 3800 is `ResultScreen`/242. A state that combines `ResultScreen` with
counter 241 is therefore contradictory in the task's recovered domain.

I copied the exact authenticated 371-byte frame-3800 state, changed only bytes
365–366 from little-endian 242 to 241, and passed it through the candidate's
pack-backed `live_presentation_runner`. Deserialization and rendering both
succeeded (exit 0), and the output was byte-identical to the accepted stable
loser frame:

```text
mutated state: phase=3, outcome=2, delay=240, loading=241
mutated state SHA-256:
53fc2f2085b12b568874c15a8a69a7bb51c0f34948474ba495c3f0170cbc7216
mutated and canonical native PPM SHA-256:
f2a034e3248ba19984cbe61ae75d4235f70bba1c550a7fa021eea952ed23077d
runner exit: 0
```

This is not covered by the candidate tests, which mutate outcome and a time
digit but construct `ResultScreen` states with a default loading counter. It
conflicts with the acceptance requirement that contradictory semantic states
fail before presenting a plausible screen, and with the candidate handoff's
claim that contradictory phase/outcome combinations fail closed.

Correct the result-state predicate to accept only the observed publication
tuples. At minimum, the newly supported loser result must require
`ResultScreen`, `PlayerLost` and loading counter 242 together. Add a regression
that sends the authenticated loser state with counter 241 through
`LivePresentation` and requires rejection. Preserve the accepted winner
boundary and stable winner rendering; its observed tuples should be encoded
explicitly rather than inferred from the loser correction.

## Reference and semantic reproduction

I ran a new wrapped access capture from the exact candidate using the supported
PAL ROM and pinned bsnes core. The command was:

```text
python3 tools/project.py access capture \
  --manifest tests/manifests/replay/race-crawler-dragster-12000-release-3000-3299-fields.json \
  --out artifacts/m4-01-review-reference-wrapped \
  --from-frame 3528 --to-frame 3800 --ring 262144 \
  --watch-address 0x002100 --watch-address 0x802100 \
  --watch-address 0x002101 --watch-address 0x802101 \
  --watch-address 0x002105 --watch-address 0x802105 \
  --watch-address 0x002107 --watch-address 0x802107 \
  --watch-address 0x002108 --watch-address 0x802108 \
  --watch-address 0x00210B --watch-address 0x80210B \
  --watch-address 0x00210D --watch-address 0x80210D \
  --watch-address 0x00210E --watch-address 0x80210E \
  --watch-address 0x00210F --watch-address 0x80210F \
  --watch-address 0x002110 --watch-address 0x802110 \
  --watch-address 0x002115 --watch-address 0x802115 \
  --watch-address 0x002116 --watch-address 0x802116 \
  --watch-address 0x002117 --watch-address 0x802117 \
  --watch-address 0x002118 --watch-address 0x802118 \
  --watch-address 0x002119 --watch-address 0x802119 \
  --watch-address 0x002121 --watch-address 0x802121 \
  --watch-address 0x002122 --watch-address 0x802122 \
  --watch-address 0x00212C --watch-address 0x80212C \
  --watch-address 0x00212D --watch-address 0x80212D \
  --watch-address 0x002130 --watch-address 0x802130 \
  --watch-address 0x002131 --watch-address 0x802131 \
  --watch-pc 0x82B18A --watch-pc 0x82B19D \
  --watch-pc 0x82B1A3 --watch-pc 0x82B1E0 \
  --watch-pc 0x82B296 --watch-pc 0x80C431 \
  --wram-series-range 512 5120 --wram-series-every 1 \
  --frame-image 3558 --frame-image 3559 \
  --frame-image 3798 --frame-image 3799 --frame-image 3800 \
  --timeout 180 \
  --report artifacts/m4-01-review-reference-wrapped/report.json \
  --task M4-01-review
```

All required checks passed. It reproduced sample digest
`d24a12347bcda335...`, final serialized-state digest `628878bd41e4edec...`,
and the exact access SHA-256
`afa7abedf63e0bfb5897b54c6624f80a17afb132108f4ec444d0feb6d8485482`.
The stable PNG also reproduced exactly as
`2441b84cec5c047fcfac286389314843e8fb0690531e5bbef0d0c249b7701afb`.
The capture report SHA-256 is
`a48901016d4b821bc818356b070fdbd40900aa75533dbc6ee8bb425f5917b78c`.

Independent image inspection confirmed the semantic layout: yellow two-row
`DRAGSTER` / `COMPLETE` title, `PLAYER     TIME` header, `MIKE      0:35.66`,
then three `SOMEONE   NO TIME` rows. Frames 3798 and 3799 were pixel-identical;
frame 3800 differed from them at 731/57,344 pixels and was the first complete
result. This agrees with R-0019 and does not support a loser-specific title,
ranking or award.

The new visual command passed at exactly 1,073/57,344 mismatches
(1.871164%, 15% limit). The original seven winner cases retained exact counts
`36, 697, 279, 445, 653, 962, 961`. Report SHA-256 values are respectively
`a225fb9e25fdd85ee9d931a8dfcdf454ba6b430b32b0036aec67c958e32f4f8d`
and `753195423083d80582cea58f01042f82d1ecc1d64de037064ad94594c0e0274f`.

## Gameplay, suites and hygiene

The exact release path and all requested restore boundaries passed:

```text
python3 tools/project.py native finish-check \
  --manifest tests/manifests/native/full-race-release.case.json \
  --content-pack local/classic-crawler-dragster.pack \
  --save-frame 1600 --save-frame 3318 --save-frame 3558 \
  --save-frame 3799 --preset lab-debug \
  --artifacts artifacts/m4-01-review-release-debug \
  --report artifacts/m4-01-review-release-debug/report.json \
  --task M4-01-review --timeout 180
```

It passed 18/18 required checks through frame 3800; report SHA-256
`fb1b0c404d05d7baf40dabe8b1aca601b3f8b7a76ca9ac5a5e1433e457497a8d`.

Both broad suites passed 315/315 required records (292 Python tests, 20
CTest cases and three fresh-process repetitions):

```text
python3 tools/project.py test --suite synthetic --preset app-debug \
  --artifacts artifacts/m4-01-review-app-debug \
  --report artifacts/m4-01-review-app-debug/report.json \
  --task M4-01-review --timeout 180 --test-timeout 60
python3 tools/project.py build --preset app-sanitize \
  --report artifacts/m4-01-review-build-sanitize.json
python3 tools/project.py test --suite synthetic --preset app-sanitize \
  --artifacts artifacts/m4-01-review-app-sanitize \
  --report artifacts/m4-01-review-app-sanitize/report.json \
  --task M4-01-review --timeout 180 --test-timeout 60
```

Debug/sanitizer suite report SHA-256 values are
`fcf70072dcf64a1365d6e512af8de25c1324f0362fd9079b59896ef7610e3c07`
and `7c978945256daf1594646d8d6d9e01321626dc46cea7ef26c5e9fd85782546f3`.

`git diff --check 5c3eec7..33bccb4` passed. The evidence contract was committed
before implementation, and the original seven-case manifest, gameplay
expectations, pack rules and pack payload inventory did not change. The diff
contains no tracked ROM, pack, state, PNG, access trace or report. The review
worktree had no tracked change before this reviewer-owned record; all private
inputs and outputs remain ignored.

Next action: make the narrow semantic counter validation and regression on a
new immutable candidate, then request focused independent re-review of F1.
The coordinator still owns integration, accepted status, CI, main and remote
synchronization.
