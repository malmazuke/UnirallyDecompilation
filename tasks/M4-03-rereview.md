# M4-03 focused independent re-review

- Corrected candidate: `cd6938f16dd46058dc6072f823ad3c00bdf7f143`
- Correction implementation: `029d0dfec0c17ce069bb6a33771f904b73a6eea7`
- Prior review: [M4-03-review](M4-03-review.md), commit
  `9a0e029f0738fb44ee7a0946ebd90d9d972c01bb`
- Review branch/worktree: `review/M4-03-zoom-zoo-contract-rereview`,
  `.worktrees/m4-03-rereview`
- Reviewer: fresh OpenAI Sol/medium session, 13 September 2026
- Verdict: **approve**. Both returned contract-boundary findings are resolved;
  no new finding.

## Correction and boundary inspection

The correction exact-gates the accepted replay sample digest, final-state hash
and complete five-entry capture-hash inventory. It parses each gather
destination as an inclusive ascending 16-bit range, requires the observed
staging start `$0437`, derives the required byte count as twice the sum of the
declared word counts and repeats that check against the bytes actually
reconstructed from the immutable decode.

I independently exercised adjacent and malformed ranges. For the 66-byte frame
1700 gather, `$0437-$0477` and `$0437-$0479` reject the one-byte-short and
one-byte-long bounds; `$0436-$0477` rejects an equal-length range with the wrong
start. `$0437-$10000`, uppercase-prefix and double-separator forms also reject.
Missing, additional and pairwise-swapped capture entries all reject through the
exact inventory comparison. Thus neither an inclusive-length off-by-one nor a
same-cardinality identity substitution bypasses the corrected gate.

`git diff 9a0e029..cd6938f` contains only 54 task-record additions, 41 test
additions/one deletion and 48 validator additions. `git diff --check
9a0e029..cd6938f` passes. The `tests/manifests/replay`, `docs/map`,
`tests/manifests/native` and `src` tree objects are unchanged, as are the
DRAGSTER content manifest, Classic-pack manifest, ZOOM ZOO inventory and PAL
ROM manifest. No baseline, expected digest, ROM, decoded payload, capture or
trace changed.

## Returned mutation reproduction

I copied the tracked contract into ignored artifact paths and changed only the
specified field. Each command deliberately names a nonexistent `--rom`; exit 3
rather than a missing-ROM result proves rejection occurs at manifest/command
validation before ROM lookup.

```sh
python3 tools/project.py content zoom-zoo-contract \
  --contract artifacts/m4-03-rereview/mutations/wrong-gather-destination.json \
  --rom artifacts/m4-03-rereview/does-not-exist.sfc \
  --report artifacts/m4-03-rereview/mutations/wrong-gather-destination-report.json \
  --task M4-03-rereview
# exit 3: gather destination must begin at 0x0437 and contain exactly 66 reconstructed bytes

python3 tools/project.py content zoom-zoo-contract \
  --contract artifacts/m4-03-rereview/mutations/wrong-sample-digest.json \
  --rom artifacts/m4-03-rereview/does-not-exist.sfc \
  --report artifacts/m4-03-rereview/mutations/wrong-sample-digest-report.json \
  --task M4-03-rereview
# exit 3: replay sample or final-state identity differs

python3 tools/project.py content zoom-zoo-contract \
  --contract artifacts/m4-03-rereview/mutations/wrong-capture-hash.json \
  --rom artifacts/m4-03-rereview/does-not-exist.sfc \
  --report artifacts/m4-03-rereview/mutations/wrong-capture-hash-report.json \
  --task M4-03-rereview
# exit 3: capture identity inventory differs
```

The mutation/report SHA-256 pairs are:

| Mutation | Manifest SHA-256 | Report SHA-256 |
| --- | --- | --- |
| gather destination `$0000-$0001` | `02fd5638dbabd1b21cc2d5201e48c2c142f97594bfb3a9c40103f7f5b8e618e8` | `1064be57141b60ef298aebfb449c78484c00f61c1c051c547872fa1f288b0cc4` |
| replay sample digest all zeroes | `3c2bb2000739751d3ca39056be0976055817e65f4e5184777340795d8dc1177b` | `9462687389d7648d60ea267d541681bcc5d49b545b3bf60596efb622f1c08999` |
| load-capture hash all zeroes | `5d89a2dba5deb59fae90ec01707c5777ace7cb49b8c1bbf7d68644a627d28bfd` | `f30b34b9aa590c2f3034d055fefadc18b981fdc5ae5a9a620633d0c32f7f5610` |

The first attempt to construct the capture mutation used an erroneous Perl
replacement that inserted a control byte. It correctly exited 3 for invalid
JSON, but that is not counted as identity-gate evidence. I recreated the file
from the tracked contract with an exact digest replacement, confirmed it with
`python3 -m json.tool`, and obtained the valid-JSON capture-inventory rejection
recorded above.

## Focused validation

The focused ROM-free suite passes all 10 tests, including CLI rejection before
ROM lookup and mutations of both replay identities and every capture entry:

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_contract -v
# Ran 10 tests in 0.079s — OK
```

The tracked supported-ROM contract passes from the immutable candidate:

```sh
python3 tools/project.py content zoom-zoo-contract \
  --contract tests/manifests/content/zoom-zoo-reference-contract.json \
  --report artifacts/m4-03-rereview/contract-report.json \
  --task M4-03-rereview
```

It passes 3/3 required checks and independently reconstructs 50,665 decoded
bytes, 24 ordered loader entries, 203 tiles, 406 transfers, 98 gather bytes and
40 collision words. Report SHA-256:
`afa6607acf46e333b5ad37e5e6e6273b45da1812c96256b9cba14271f4358f9a`.
The report records candidate `cd6938f16dd46058dc6072f823ad3c00bdf7f143`,
`dirty: false` and no untracked files (ignored runtime artifacts are excluded by
the reporting contract).

The coordinator may integrate this exact candidate and perform the required
integration/remote checks. This review does not mark M4-03 accepted and does
not edit coordinator-owned state or the task registry.
