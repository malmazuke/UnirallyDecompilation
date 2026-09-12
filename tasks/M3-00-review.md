# M3-00 independent review — complete-race evidence

- Review status: **returned for one required evidence-verifier change**
- Reviewed behavioral/evidence candidate: `922ea576dd99e1c4715d16c53fb503be43f47321`
- Input freeze: `135ae38`
- Handoff head inspected: `ad068e5a8731ac29d64a414f64a55e3f41b52ffa`
- Review checkout: `review/M3-00-finish-evidence` in `.worktrees/m3-00-review`
- Reviewer/runtime: fresh OpenAI Codex `gpt-5.6-sol`, medium; no child agent
- Quota: coordinator checkpoint was 41% used / 59% remaining at 2026-09-12
  16:08 AEST. Review sample was 43% used / 57% remaining in the same seven-day
  window, below the 50% checkpoint and retaining the final 20%. No purchase or
  reset was made.

## Decision

The reference observations, replay identities, counter boundary, within-frame
order, coverage delta and decoded-track sufficiency reproduced. The candidate
is not approved yet because the compact analyzer reports success after its
provenance totals are changed to false values. This leaves the numeric content
delta in R-0012 outside the claimed machine-checked contract. The candidate was
not edited.

Required change:

1. Add the expected provenance/content totals to the finish contract and make
   `tools.unirally_lab.finish.analyze` fail when at least
   `channel_transfers`, `block_moves`, `block_move_bytes`,
   `destinations_pairable`, or `destinations_paired` differs. Add a focused
   mutation test. The existing true values are 9,817, 5, 80, 9,817 and 9,814.
   Re-run the compact analyzer and synthetic suite on the corrected candidate.

Severity is moderate and limited to evidence validation: the underlying
content-addressed provenance artifact contains the stated values and the
reference/gameplay observation itself reproduced, but the analyzer's passing
status currently does not protect those claims.

Advisory, not a separate blocker: regenerating the tracked coverage summary
from the exact coverage artifact reproduced the JSON map byte-for-byte but
changed only the displayed `Regenerate:` line by omitting `--baseline`. The
tracked line is the more complete command; the observation tables did not
change.

## Source and input audit

`git diff --name-status a2e6afb..922ea57` contains only the two new replay
manifests, finish contract/analyzer/tests, new map/summary, R-0012,
`docs/state/race-finish.md`, and `tasks/M3-00.md`. In particular, the existing
3000-frame replay baseline, emulator lock/patch, reference adapter and
`src/core/` have no diff. `git diff --check` passed.

The two manifests already existed at freeze commit `135ae38`, before expected
results were added. Re-reading that commit produced SHA-256:

- continuous: `d03102fc33c22738466bfc9ae81fb55107ced9d693904ebd3132fa1f76afced2`
- release variation: `8f449cd1a59a50904a9d208176a1bb015ebcd4ad128978942e8294d72f294cd1`

Only ignored `artifacts/`, `build/`, `local/` and Python caches were present
after review. No tracked `.sfc`, `.smc`, `.rom`, `.sav`, state, PNG, binary or
archive was introduced.

## Exact-candidate reproduction

All commands in this section ran detached at exact commit `922ea57`.

```sh
python3 tools/project.py doctor --report artifacts/m3-00-review/doctor.json
python3 tools/project.py bootstrap --report artifacts/m3-00-review/bootstrap.json
python3 tools/project.py build --preset lab-debug --report artifacts/m3-00-review/build-debug.json
python3 tools/project.py test --suite synthetic --report artifacts/m3-00-review/synthetic.json
python3 tools/project.py reference build --report artifacts/m3-00-review/reference-build.json
```

Doctor, bootstrap, debug build and pinned-core build passed. Synthetic passed
286/286 with `source.commit=922ea57`, `dirty=false`, no failure or skip. Report
SHA-256 values in command order were:

- `1a1fa762b3edd9ef3e4a2a9044dec486a6fc8f7d6b4f8aecc7a0e1244ad74924`
- `39738337003db7ab69278675f0d03438038d5f2cc632e493a7aa9da1cabc10d4`
- `1e23233371640e5d089ead34ad9450ecf6a6a39d2b1f0740613a1871c0e11b73`
- `d6546677247da30fa8960d5638ceaea5078860ac757b11c88b742fad79beff3c`
- `bbf78e46181728c8ee15da2bef67da974a8e04d85655adf2a6e7887e1fc1728c`

The complete replay was reproduced with:

```sh
python3 tools/project.py replay compare \
  --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json \
  --runs 2 --task M3-00-review \
  --artifacts artifacts/m3-00-review/continuous \
  --report artifacts/m3-00-review/continuous-compare.json
```

It passed 24/24 required checks in fresh worker PIDs 4373 and 4624. Both runs
had sample digest `22e9babdcb867936245e7c4a52fdf53a1bf8dc9433e91b77066818a4fc3484d6`
and final-state digest
`6606f9411e05d00feab16b57183b8133de322e4e324c28f7aac710a345bb9ba0`.
Report SHA-256: `8cde341e26d43d0132fceee728b1c08b86aa938f71e98c687220d55d7cf7ffc4`.

The preregistered cross comparison was:

```sh
python3 tools/project.py replay compare \
  --manifest tests/manifests/replay/race-crawler-dragster-12000-continuous-right-fields.json \
  --against tests/manifests/replay/race-crawler-dragster-12000-release-3000-3299-fields.json \
  --task M3-00-review --artifacts artifacts/m3-00-review/cross \
  --report artifacts/m3-00-review/cross-compare.json
```

It returned the expected exit 1, not a repeatability pass: first divergence at
frame 3000 in WRAM/registers, `joy1h_image`, `axis_h`, `throttle` and `speed`.
Localization found six WRAM bytes beginning `$7E0313` and two registers. The
variation sample/final digests were
`d24a12347bcda3352244ecdb1d5e1ffc88985827a7725ac00da5a9f8ec866c74`
and `628878bd41e4edecf2ca3efd5b8cedb7b3144385f1edb726c0f198727c4e5dcd`.
Report SHA-256: `0c38ae6748c3e17b5993bbcc5177a0167bfd1c9d4c2c011b90d42e6d8e3eb3cd`.

## Artifact and boundary checks

The worker's ignored artifacts matched every recorded hash:

- continuous access `06bf2769df2f6af21f9c78c0ccb9ec3820baf33f019eefcd071efab8bafa7f65`
- focused order access `17fbd19656d3ff796c4b5dbab88290113d85a1463963e033225c1e47e9c61d25`
- variation access `6fda1f7f1f47cf9e23324158e7a931cdb52fb4a22664b378ee046b90de251567`
- whole-run coverage `7654ac204a7a130f66a0dfe8228cf367dd88a35ffc7b2eec5a16ac3f3839337e`
- tracked map `3333f8a96a4c256abe669ea7f376533783722e3fe152cdff8aae6ccb241d09ce`
- complete provenance `9f50dbb7369c3b42b5c4abdbb756202468233b375ff4f30d094143e01eb6fdbc`

Regenerating the map from that coverage artifact with the accepted 3000-frame
map as baseline produced the same map hash and the same 3,467/0 byte delta, 92
new ranges and 180 new entry points. The map report SHA-256 was
`bdde1c7b3b16c47dd1f2eaeb5adf48c97802b3f0f19b495997bf3b289d0912de`.

The compact analyzer used the fresh replay samples and the hashed access,
coverage and provenance artifacts. It passed 20/20 and reproduced output hash
`2c1467d062ba5c6f6dc6b07199b60bad5edd97b377b95bb23623e196dfbb31bc`.
It counted 16,849 continuous bank-$7F reads on frames 3000–3453 and 12,103
variation reads on frames 3180–3558, with zero outside `$7F0000`–`$7F8416`.
Together with R-0008's accepted through-2999 observation, this supports the
stated single-track continuous-finish sufficiency and no broader claim.

Reviewer-owned raw checks, independent of the analyzer's aggregate range
test, established:

- variation counter 239 is written on frame 3557, 240 on 3558, then frame 3559
  reads 240 and performs no counter write;
- ImageMagick reports the frame-3559 PNG as 256x224, one colour, mean zero,
  with all 57,344 pixels `#000000`; frame 3558 visibly contains the LOSER
  finish display;
- continuous frame 3214 sequence numbers are ordinary axes 757/777, counter
  increment 909, neutral overrides 928/934, and opponent finish flag 2866.
  Thus the dispatcher reacts to the player before the later opponent write.

Changing only `finish.variation.counter_last` from 3558 to 3559 returned exit
1 and the exact `variation_counter_range` failed check, with observed
`[3319,3558,240]` versus expected `[3319,3559,240]`. Missing-contract and
malformed-JSON CLI cases returned 2 and 3 respectively.

## Reproducible required finding

This command constructs a false provenance summary from the exact hashed input:

```sh
jq '.summary.channel_transfers = 0 | .summary.destinations_paired = 0' \
  ../m3-00-finish-evidence/artifacts/m3-00-content/complete-provenance/provenance.json \
  > artifacts/m3-00-review/mutated-provenance.json

python3 -m tools.unirally_lab.finish.analyze \
  --contract tests/manifests/finish/dragster-complete-race.json \
  --continuous-samples artifacts/m3-00-review/continuous/run1-samples.json \
  --variation-samples artifacts/m3-00-review/cross/right-samples.json \
  --continuous-access ../m3-00-finish-evidence/artifacts/m3-00-complete-access/capture/access.json \
  --variation-access ../m3-00-finish-evidence/artifacts/m3-00-variation-access/capture/access.json \
  --coverage-map docs/map/race-crawler-dragster-12000-continuous-right-fields.map.json \
  --content-manifest tests/manifests/content/dragster-segment.json \
  --provenance artifacts/m3-00-review/mutated-provenance.json \
  --out artifacts/m3-00-review/mutated-provenance-analysis.json
```

Observed exit was 0 with `status=passed checks=20`, even though the emitted
`content_delta` said `channel_transfers: 0` and `destinations_paired: 0`.
Output SHA-256 was
`4117f3b6316db998e8fd17d1b64c67accbe5e8ee639e1fb5418eaed180053c57`.
This mutation is not covered by the five added tests. Review should resume on
the corrected exact candidate; the expensive reference runs need not be
repeated if the fix is confined to the contract/analyzer/tests and preserves
the frozen manifests and artifact identities.
