# M4-04 focused independent re-review

- Corrected candidate: `ac2bee7a4f51a864425e79efc2c7aeb6f44c9337`
- Correction implementation: `970dcb83956750cb93d5427d6b912bc8bad0675b`
- Prior review: [M4-04-review](M4-04-review.md), commit
  `c5ee5fd6dc1ec7add5fc7b54226b0e1dd0f4a25b`
- Review branch/worktree: `review/M4-04-zoom-zoo-riding-freeze-rereview`,
  `.worktrees/m4-04-rereview`
- Reviewer: fresh OpenAI Sol/medium session, 13 September 2026
- Verdict: **approve**. The returned complete-seed binding defect is resolved;
  no new finding.

## Correction inspection

The correction canonicalizes the complete tracked `seed` object with sorted
JSON keys and compact separators, then exact-binds SHA-256
`d16d7576d556ac09adf842a890d68498db858c3f1c771fcfa499d181a398bc45`
whenever a real frozen projection is verified. Both tracked projections
independently reproduce that digest and contain exactly 124 inventory records
and 124 values. The public standalone command calls
`verify_projection(..., require_frozen=True)` and `verify-pair` retains its
default `require_frozen=True`, so both command boundaries exercise the new
gate before accepting the pair.

The correction leaves the projection files and their rows unchanged. Their
file SHA-256 values remain:

| Projection | SHA-256 |
| --- | --- |
| primary | `130e4631a7785b3839a3ba9a8b3d59d15a0773711450fdc769632c57a3d92766` |
| release 2500--2599 | `90adf082f2410251dff4ec50431dfe557a2552fb94d0f6b9737a0d0285fba247` |

## Returned-defect and adjacent mutation reproduction

I loaded each tracked projection, deep-copied it, applied the named mutation to
both copies for paired verification, serialized each mutation with Python's
default `json.dumps`, and invoked the public module twice:

```sh
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify \
  --projection <mutated-primary.json>
python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify-pair \
  --primary <mutated-primary.json> --release <mutated-release.json>
```

Every standalone and synchronous-pair attempt exited 2. The first three emit
`projection complete frozen seed object differs`; the last two emit
`projection seed inventory differs`.

| Mutation | Primary SHA-256 | Release SHA-256 |
| --- | --- | --- |
| `seed.values.player_x = 65535` | `9e43d9907b179afe9f7ef65b9aba337442670e560212f1299e78ed2b1321e4fd` | `b729d1ed67ef759a0532b63511d3373f34cffd3d1b87d522bc9faf9479f7ccb1` |
| `seed.queue_sha256 = "0" * 64` | `600f68ead683c86a581b11af502d4e190c46a7b44c89c88c60c6a3d2c1fad718` | `092a79e4a7b1c6a32f810b60830a704e2cb7215c121f6c95cd45b88ae933c358` |
| `seed.manifest_identity = "0" * 64` | `bf10ae832ee2b8d6e6495f2da0b425d672ffc3fde8c8dec39f76a111d27ae2a7` | `d3733a73dc7a1cdbacbff44dd8db67ad835beaa506ca67144239424c5182d4b5` |
| extra `seed.values.extra_key = 1` | `ee928d692f05dd374aacbed182da0b4323825c33474cbc82ae4f342ba7dd30b2` | `ee5625b747bcc5f9a8239b9d21b7b4a4cf30373ca99557bc61e46417c20ae08c` |
| remove final inventory record | `a42acc3a02f77ef746610c76ced8d839bb2de43358269735f654e3774f544755` | `3fac7bb6b8bf2528610b34d1d270ad5ce52508eece6e9f1d82bdb4bfc0c6d7d1` |

This reproduces all three returned defect targets independently and also
challenges both an additional values key and a missing inventory record. A
synchronous contradictory pair can no longer escape merely because both bad
seed copies agree.

## Focused validation

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_freeze \
  tests.tooling.test_zoom_zoo_windows -v
# Ran 11 tests in 0.934s -- OK

python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify \
  --projection tests/manifests/native/zoom-zoo-primary.reference.json
# verified tests/manifests/native/zoom-zoo-primary.reference.json

python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify \
  --projection tests/manifests/native/zoom-zoo-release-2500-2599.reference.json
# verified tests/manifests/native/zoom-zoo-release-2500-2599.reference.json

python3 -m tools.unirally_lab.native.freeze_zoom_zoo verify-pair \
  --primary tests/manifests/native/zoom-zoo-primary.reference.json \
  --release tests/manifests/native/zoom-zoo-release-2500-2599.reference.json
# first_divergence 2500; joy1h_image, axis_h, player_x,
# player_x_residue, player_vx, player_vy and player_throttle differ;
# finish_transition false
```

The focused suite includes the public-command regression for independent seed
value, queue hash and provenance mutations through both standalone and paired
verification. The unchanged real projections still accept only their expected
frame-2500 seven-field response and have no bounded finish transition.

## Scope and hygiene

`git diff --check c5ee5fd..ac2bee7` passes. The correction range changes only
four UTF-8/ASCII text files: seven verifier lines, 36 focused-test lines, eight
research-record lines and 49 task-record lines. It changes no projection or
replay manifest, source gameplay tree, content manifest, coordinator state or
task registry. No ROM, SRAM, save state, capture, decoded payload, generated
pack or other binary is tracked by the correction. The fixed-scope tree check
below exits 0:

```sh
git diff --quiet c5ee5fd..ac2bee7 -- src tests/manifests/native \
  tests/manifests/replay tests/manifests/content docs/STATE.md tasks/README.md
```

The coordinator may integrate this exact candidate and perform the required
integration and private-remote checks. This re-review does not mark M4-04
accepted and does not edit coordinator-owned state or the task registry.
