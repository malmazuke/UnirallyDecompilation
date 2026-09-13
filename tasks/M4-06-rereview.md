# M4-06 focused independent re-review

- Corrected candidate: `1421787d1b3f6c5a5099ae0cb3a3402b9e7f0d20`
- Correction implementation: `814f7871774662cb93905db426118cec33f96677`
- Prior review: [M4-06-review](M4-06-review.md), commit
  `dd3d819c0fb2826c285ad72dc46ac17b262839b1`
- Review branch/worktree: `review-grade/M4-06-rereview`,
  `.worktrees/m4-06-rereview`
- Reviewer: fresh OpenAI Sol/medium session, 13 September 2026
- Verdict: **approve**. The returned evidence-workflow defect is closed; no
  new material finding.

## Correction inspection

R-0024 now invokes the implemented
`tools.unirally_lab.native.zoom_zoo_contact capture` command before passing its
`access.json` to the M4-06 verifier. The accompanying text explicitly says that
M4-06 reuses the complete M4-05 watch set and does not claim a separate capture
surface. `docs/BUILD_AND_VALIDATION.md` agrees: it inventories
`zoom_zoo_vertical_contact` as a consumer with exactly `extract-content`,
`verify` and `compare-inputs`, and records the reused M4-05 capture command.

The new ROM-free test derives the capture module from the command published in
R-0024 rather than hard-coding the intended replacement. It requires that
`capture --help` succeed and expose `--manifest`, `--out`, `--from-frame` and
`--to-frame`; it then dispatches the derived command with a missing manifest,
requires exit 2 and requires that no output directory was created. Directly
invoking the former documented M4-06 command on this candidate still exits 2
at argument parsing with:

```text
invalid choice: 'capture' (choose from extract-content, verify, compare-inputs)
```

Therefore substituting the former erroneous module name back into R-0024 makes
the new test fail at its required successful-help assertion. The test exercises
the public command boundary and catches the exact returned defect.

## Independent clean reproduction

I supplied the existing private PAL ROM and pinned core to the isolated
worktree through ignored `local/` entries, then ran the complete corrected
R-0024 sequence:

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_contact extract-content --contract tests/manifests/content/zoom-zoo-reference-contract.json --rom "$(cat local/rom-location.txt)" --out artifacts/m4-06/content
python3 -m tools.unirally_lab.native.zoom_zoo_contact capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-06/primary-1650-1682-a --from-frame 1650 --to-frame 1682
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_contact verify --access artifacts/m4-06/primary-1650-1682-a/access.json --content artifacts/m4-06/content --manifest tests/manifests/native/zoom-zoo-vertical-contact-primary.reference.json --report artifacts/m4-06/final-primary-component.json
```

The capture report binds clean source `1421787d1b3f6c5a5099ae0cb3a3402b9e7f0d20`,
records `dirty: false`, `source_changed_during_run: false`, and 18 passed
checks with no other outcomes. Its SHA-256 is
`daefdbb608a13df9e72d0dac1f4f7ae40ba53aa627c20d2715fa3e1a543cc1b2`;
the difference from the correction handoff's clean report hash is the recorded
source commit (`1421787` here versus `814f787` there). The behavior-bearing
identities are unchanged:

- Access SHA-256:
  `c270cb19d28cab4e07044fcbde8e673f09c3aa79eeb13d3614f9b1e52a080f05`
- Component report SHA-256:
  `f4b38eaf709a44679a30279bc9b2c83136e36526fb3e0469481bbd86dc4f52f6`
- Classification SHA-256:
  `f480ef6841d9c52de16dfb3203ac1ea1eda0648b55b6478e874472627bae574c`
- Verified domain: 66 ordered calls and 660 points on frames 1650--1682

An independent command-boundary dispatch with a nonexistent manifest returned
exit 2, emitted the expected `No such file or directory`, and did not create
the requested output directory.

## Focused validation and scope hygiene

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_contact \
  tests.tooling.test_zoom_zoo_vertical_contact -v
# Ran 19 tests in 0.120s -- OK

git diff --check dd3d819c0fb2826c285ad72dc46ac17b262839b1..1421787d1b3f6c5a5099ae0cb3a3402b9e7f0d20
# passed
```

The correction range changes only R-0024, the build/validation inventory, the
focused ROM-free test and the M4-06 handoff. A fixed-scope tree comparison
confirms no changes to `src/`, `tools/`, `tests/manifests/`, `docs/STATE.md` or
`tasks/README.md`. No implementation, reference manifest, frozen output,
serialization, Classic pack/profile/start, frontend, core, lock, coordinator
state or registry changed. Private ROM-derived captures, extracted content and
reports remain ignored and are not included in this review commit.

The coordinator may integrate this exact candidate and perform the required
integration and private-remote checks. This re-review does not mark M4-06
accepted and does not edit coordinator-owned state or the task registry.
