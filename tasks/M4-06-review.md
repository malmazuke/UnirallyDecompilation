# M4-06 independent review

- Candidate: `f3602158f2ada6a8a2b0a9a0610da21c7c17e2f6`
- Compared with assigned base: `b72b603802853545e6fc017cdecdced98edf33b9`
- Review branch/worktree: `review/M4-06-zoom-zoo-vertical-contact`,
  `.worktrees/m4-06-review`
- Reviewer: fresh OpenAI Sol/medium session
- Verdict: **return with one reproducible evidence-workflow finding**. The
  bounded equations and both authored component cases reproduced; this review
  does not reject their observed behavior.

## Finding

### R1 — the tracked capture reproduction command does not exist

R-0024 line 107 tells a fresh reviewer to invoke
`tools.unirally_lab.native.zoom_zoo_vertical_contact capture`, and the task
handoff refers to the same additive vertical-contact capture surface. The
candidate module registers only `extract-content`, `verify` and
`compare-inputs` at lines 591--615. On the exact clean candidate this command:

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_vertical_contact capture \
  --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json \
  --out artifacts/m4-06-review/should-not-exist \
  --from-frame 1650 --to-frame 1682
```

exits 2 before capture with `invalid choice: 'capture'`; no output directory is
created. This is not a prose-only typo in the evidence trail: the published
end-to-end regeneration sequence cannot produce the access input that the next
verification command requires. I independently recovered the evidence by
using the older M4-05
`tools.unirally_lab.native.zoom_zoo_contact capture` command, whose watch set
does contain the M4-06 landmarks, but that substitute is not the command
recorded in R-0024. Add the bounded capture subcommand or correct and test the
tracked reproduction command. Do not change the frozen capture hashes.

## Independent reference cases

All private artifacts below are ignored. The supported PAL ROM, pinned bsnes
commit and pinned patch matched the candidate identities.

### Authored cases

- A fresh primary capture for frames 1650--1682 is exactly
  `c270cb19d28cab4e07044fcbde8e673f09c3aa79eeb13d3614f9b1e52a080f05`.
  The verifier passes all 66 calls/660 points and emits the claimed component
  SHA-256
  `f4b38eaf709a44679a30279bc9b2c83136e36526fb3e0469481bbd86dc4f52f6`.
- A fresh first-Right-at-1653 capture through frame 1700 is exactly
  `1965151f925d0917c01f400f2cffd2431db5da39fa664a7bae8def2707b4d21e`.
  Its verifier passes all 72 pre-boundary calls/720 points and emits the
  claimed component SHA-256
  `1323187dc98f4aa65b47fad7d595744b1d1e51ee2aa325c94be9f7cfcbd215fb`.

### Reviewer-owned first-Right-at-1654 variation

Before capture I created an ignored manifest that changes only the primary
first Right onset from frame 1650 to 1654 and retains all other events. The
initial deliberately unfrozen two-run replay failed only its placeholder
expected hashes while proving the two fresh processes identical. After binding
those observed identities, the ignored manifest SHA-256 is
`00d14ae3b684323656e7655757268aa3e84cfef964d36fdb8a86a1104c51071c`;
its sample/final/A/V hashes are respectively
`40924e02703d5aa737a180728970545eaa056456591152b796735cfc664982f1`,
`9a2e8971fd8256c769c459fbe84b154c409008cb94a4073c8a5c2006c463b9a5`
and `d31cb53f4840713bf5a1b840910d7d815722f5b7f385acb672ed1b84f7a09318`.

Two independent access captures are byte-identical at
`b1d24d35db74639455b356bb360846cc9850fec5f8505acb26c605b6f8590f78`.
Each covers frames 1650--1700 with 936,887 instructions, 463,961 accesses,
zero unresolved stores, zero PCs outside ROM and maximum ring use 18,647 of
262,144. The actual first direction/special boundary is ordinal 74, frame
1687, player point 8. Every preceding call (74 calls/740 points on frames
1650--1686) reconstructs through `compare_call` without a mismatch. The full
51-frame classification is 72 compatible, 16 non-flat and 14
direction/special; the pre-boundary response split is 46 continuous, 27
unsupported and one recontact.

This case is **irrelevant as a new arithmetic class**, though useful as an
adjacent timing check. Its supported reducer angles are the same signed set
`-5,-4,-3,-2,-1,0` as primary; it contains no positive slope. It repeats
negative incoming `vy` (19 calls, minimum -130), multiple slope coefficients,
reflection (player frames 1670--1686), support loss/reacquisition and the same
opponent recontact. It therefore does not establish behavior beyond the
candidate's stated signed/multiple-angle/upward family. It moves the measured
direction boundary from the worker variation's frame 1686 to frame 1687.

## Original-instruction and ordering audit

I inspected the exact ROM bytes (file offsets equal to the bank-81 addresses
under this LoROM mapping) and the ordered access/PC snapshots, rather than
inferring behavior from the Python result alone.

- Reducer and signed penetration: `$81:90BE` onward iterates the ordered point
  arrays. The byte subtract/`BMI` predicates preserve the 8-bit N-flag test,
  and `$81:90EB` excludes signed-negative penetration from correction after it
  can influence the selected support tuple. The frame-1665 player trace
  includes penetrations 249,251,254,0,2 at points 5--9 and selects correction
  2/angle -3 in the recorded order.
- Slope reduction and signed velocity: `$81:9696` chooses the negative-angle
  coefficient tables at `$00:822B+abs(angle)` and `$00:824B+abs(angle)`.
  `$81:96B6` reads incoming `vx`, the negative branch performs `SEC/ROR` for
  arithmetic shifts, `$81:96CD` publishes the shifted scratch, and the
  multiply/ones-complement sequence through `$81:970B` writes the new `vy`.
  Primary frame 1665 enters with `vx=382`, `vy=-46`, writes shifted velocity
  23 at `$02D4`, then writes `vy=-68`; there is no incoming-`vy` sign guard.
- Reflection/support transition: the review case changes reflection before
  player frame 1670. That call remains continuous on angle -3; frame 1672 is
  unsupported and increments count 0 to 1 while preserving `vx/vy`; frame
  1673 reacquires angle -5, clears the counters and applies the slope response.
  The independently computed values match the captured ordered writes.
- Response and publication: response writes precede the common tail. For
  review frame 1670 player, `$81:970B` writes `vy=-74`, `$81:97CA` writes the
  -1 horizontal contribution, `$81:97E1` writes `vx=404`, `$81:97FD` saves
  incoming y 1554, `$81:980C` publishes corrected y 1554, and `$81:9810`
  saves incoming x 9314. The caller then reads these temporaries at the
  established player/opponent publication sites. The unsupported frame-1672
  trace instead increments `$0FBF/$0F33` before entering the same position
  tail, confirming the branch/common-tail order.

These observations support the candidate's bounded arithmetic. They do not
extend its explicit direction/special, horizontal, positive-slope or
autonomous-recurrence limits.

## Identity and mutation checks

- Changing primary frame 1665 player point 5's nonselected captured
  penetration from 249 to 248 leaves the later reducer summary selected by
  point 9 unchanged, but `compare_call` rejects it exactly as computed
  `(249,253,3080)` versus captured `(248,253,3080)`.
- Incrementing that call's published y by one is rejected as
  `computed response/publication differs at 1665/0: y`.
- Mutating the access core commit is rejected as `core identity differs`;
  mutating the authored manifest core commit is rejected as
  `vertical-contact source identity differs`.
- The inherited M4-05 exact-tuple mutation and the M4-06 reducer, signed
  penetration, coefficient, negative-velocity, support-transition, recontact,
  malformed-comparison and manifest-boundary tests all pass.

## Commands and outcomes

- `python3 -m unittest tests.tooling.test_zoom_zoo_contact
  tests.tooling.test_zoom_zoo_vertical_contact -v` — 18/18 passed.
- Primary capture and `zoom_zoo_vertical_contact verify` — passed with the
  exact hashes above.
- Right-1653 capture and `zoom_zoo_vertical_contact verify` — passed with the
  exact hashes above.
- Two right-1654 captures — passed and byte-identical; all 74 pre-boundary
  calls passed direct independent reconstruction.
- Deliberate nonselected-tuple, response/publication, access-identity and
  manifest-identity mutations — all rejected at their intended dependency.
- Published R-0024 capture command — failed with exit 2 as described in R1.
- `git diff --check` — passed.

No candidate implementation, frozen path or expected output was changed.
Ignored ROM-derived captures, extracted content, reports and local dependency
links are not committed. This review commit records the review only and does
not mark M4-06 accepted.
