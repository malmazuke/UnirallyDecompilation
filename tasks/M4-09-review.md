# M4-09 independent review

- Candidate: `c4c85e57862bf40240e5e0fdd67ce56d323663b0`
- Implementation: `201dcc1a5dca3f78d6c039d65f485cc510758d0f`
- Base: `15da58489df4ccce24a678aa3d98382872036ab1`
- Reviewer: fresh OpenAI Sol/medium review in `.worktrees/m4-09-review`
- Status: review complete; approved without a material finding; the coordinator
  alone decides acceptance

## Withheld variation preregistration

Before inspecting the candidate implementation or creating a capture, release
Right for frame 1667 only and restore it at 1668, leaving every other primary
event unchanged. Predict exact primary behavior through frame 1666 and the
first controller image difference at frame 1667 only. Do not preclaim later
composition relevance, branch changes or reconvergence.

## Verdict

**Approve without a material finding.** The candidate reconstructs all 102
ordered calls and all 1,020 track sample words/source offsets from one
authenticated eight-word seed, recurrent coordinates and authenticated static
content. Captured positions, samples and outputs are comparison targets rather
than per-call inputs. The reached helper predicates, integer widths and order,
the sampling/contact phases, contact feedback and declared external boundary
all withstand the independent checks below. The reviewer variation reproduced
twice and behaved exactly as preregistered. No production, frozen expectation,
pack, serialization or frontend path changed.

## Independent source and order audit

The exact candidate and base resolve as stated above, the worktree was clean at
review start, and `git diff --check 15da584..c4c85e5` passes. The candidate
changes nine additive task/research/tooling/manifest files only.

An independent read of the supported PAL ROM reproduces the inclusive 68 bytes
at file `0x01296F` as SHA-256
`5f3d24df4c743df33e24d2febc24522cd2abe68fe5597ee2abf3ebfac413653c`.
The bytes begin `C2 30`, establishing 16-bit accumulator and index widths, then
execute the two zero guards, wrapped `CMP #$0200` sign test, negative/nonnegative
velocity choice, five logical shifts on the nonnegative path, addend plus three,
the `$0FAB` update and one `$A7` increment before `RTS`.

All 102 calls in both worker captures and both reviewer captures reach the
increment. Sequence-number inspection at frames 1650, 1667 and 1683, plus a
complete evaluator pass, confirms player then opponent and the reached order:
Y helper, `$82:A627` integration, point expansion/track sampling, `$81:8F9D`
contact, post-contact caller publication. For example, primary frame 1650
player helper `$82:A971/$82:A9B0` occurs at sequences 1567/1598, integrator
entry `$82:A627` at 1696, point/sample work begins by `$81:8B05` at 4931,
contact entry is 5628 and post-contact x/y publication is 6028/6030. The
earlier pre-contact position publication at 2188/2190 is also retained and
checked rather than confused with the feedback publication.

The primary verifier reproduces:

- 102 calls, 1,020 computed sample words/source offsets, row SHA-256
  `9582292c872f154b917e7973f4b6b2ba8a3a458feaab49d11889f3fe2b9f9c30`;
- sample/source SHA-256s `98e77e32...188dd` and `f24ccd27...fa27`;
- final recurrent player `(9824,1605,12,10)` and opponent
  `(7489,1520,-4,12)`;
- all 100 between-call same-rider transitions carrying the prior contact x/y
  and integrator x/y residues, with no coordinate or residue replacement;
- opponent `response_b` 254 at frame 1661 but externally replaced by zero at
  frame 1662, so it is correctly excluded from recurrent state.

The independently generated primary report hashes to
`7b016b93eea83cc31baafdcec86d9b6c86e9588a1997cc5e2bd0b11c2f7f6295`.
The worker variation report hashes to
`e24c07425bc6260b2170e52d8c203b780329c269398e62c5ba568e5732e7c879`
and its comparison to
`4af2732737127cb31c1edaf833e2a9d4f596e6761473b294b970dc8f9e49b6f8`.

## Reviewer variation

Two fresh cold-start processes produced identical complete records:

- access SHA-256
  `51867f9a181b85933daebe97df8e76e91c778b79fe78b7959735202bdba49483`;
- work-RAM series SHA-256
  `00475d1b11a75063c61e557870511f5f2bee4f063d3df47b095f1c46d1fb89f9`;
- 953,432 instructions, 471,805 accesses, maximum ring delta
  18,640/262,144, zero unresolved stores and zero non-ROM PCs.

The controller differs only at frame 1667. Composition is exact through 1666
and first differs for the player at 1667, satisfying the preregistration.
Samples first differ at 1671; nine player contact branch choices differ through
1685, including a mixed direct/reflected call at 1683. All 51 opponent calls
remain exact and player state does not reconverge by 1700. Reviewer final
recurrent state is player `(9821,1603,18,29)`, opponent
`(7489,1520,-4,12)`. Reviewer row/sample/source SHA-256s are respectively
`63996694...5bf`, `0c478c81...fc33` and `31a2058c...026`.

## Adversarial checks

For each primary and worker-variation authored manifest, independent mutations
of the seed, call count, rider/final chain, sample digest, source-offset digest,
helper counts, `response_b` inventory, phase order, core identity and row/tuple
digest reject. A changed player seed changes the first integrated result.

Additional calculation-level challenges show:

- changing frame-1661 opponent `response_b` rejects at its response
  publication;
- changing frame-1661 player point 9 from the exact preprocessing tuple rejects
  even though the later reducer path is unchanged;
- a 64-unit coordinate perturbation changes all ten source offsets and eight of
  ten words in the sampled call;
- omitting the helper's Y increment changes the tested integrated Y from 1542
  to 1541;
- feeding the pre-contact Y rather than contact-corrected Y changes frame-1661
  player feedback from 1560 to 1562, while frame 1662 consumes 1560;
- changing authenticated direct or reflected coefficient bytes changes and
  rejects response output at frame 1669 or 1699 respectively;
- missing helper events, altered call/rider order, captured-sample
  contradiction and identity changes all reject through the focused tests or
  exact capture binding.

The external inventory agrees with the actual computation boundary: three
pre-helper inputs, seven position inputs, pose/reflection for sampling, fifteen
captured contact fields, and the two live contact dependencies. The recurrent
set is exactly both riders' x/y/x-residue/y-residue.

## Commands and results

```sh
python3 -m unittest tests.tooling.test_zoom_zoo_position tests.tooling.test_zoom_zoo_contact tests.tooling.test_zoom_zoo_vertical_contact tests.tooling.test_zoom_zoo_reflected_vertical_contact tests.tooling.test_zoom_zoo_composition -v
# 46/46 passed

python3 -m tools.unirally_lab.native.zoom_zoo_composition verify --access <primary-access> --content <content> --manifest tests/manifests/native/zoom-zoo-composition-primary.reference.json --report <report>
python3 -m tools.unirally_lab.native.zoom_zoo_composition verify --access <worker-variation-access> --content <content> --manifest tests/manifests/native/zoom-zoo-composition-right-release-1666.reference.json --report <report>
python3 -m tools.unirally_lab.native.zoom_zoo_composition compare-inputs --primary-access <primary-access> --variation-access <worker-variation-access> --content <content> --report <report>
# all passed

python3 -m unittest discover -s tests/tooling -p 'test_*.py' -v
# 359/359 passed

ctest --test-dir ../m4-09-zoom-zoo-composition/build/lab-debug --output-on-failure
ctest --test-dir ../m4-09-zoom-zoo-composition/build/lab-sanitize --output-on-failure
# 20/20 passed in each exact-candidate build

python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-right-release-1666.json --runs 2 --report <report> --artifacts <dir>
# 24/24 required replay checks passed; fresh PIDs and exact A/V

python3 tools/project.py content pack-inspect --pack local/classic-crawler-dragster.pack --report <report>
# 3/3 passed
```

The reviewer variation used the candidate's union watch set with direct
`tools/project.py access capture` because the task command intentionally admits
only the two worker-preregistered manifests. Its zero digest placeholders
therefore produced the expected two digest failures while capture completeness,
identity, region and determinism checks passed; the two raw captures were then
compared byte for byte. An initial broad `unittest discover -s tests` invocation
found zero tests because this repository's Python suite lives in
`tests/tooling`; the corrected command above passed all 359. A first direct
CTest invocation used a nonexistent convenience path and did not run; the
pinned `local/toolchain/cmake-3.31.10-darwin-arm64/bin/ctest` path then passed
both exact-candidate build trees. These were invocation/setup errors, not
passes or candidate defects.

Private ROM, captures, derived content and generated reports remain ignored.
The review changes only this record.
