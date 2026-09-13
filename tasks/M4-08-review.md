# M4-08 independent review

- Candidate: `3a3d5ca9b16920d4c79afe1e6f0f0cdd925a1819`
- Assigned comparison base: `684f78a`
- Review branch/worktree: `review/M4-08-zoom-zoo-position`,
  `.worktrees/m4-08-review`
- Reviewer: fresh OpenAI Sol/medium session, 13 September 2026
- Verdict: **approve**. The primary, worker variation, private reviewer
  variation, original arithmetic and integrity cases reproduce without a
  material finding. Production native behavior and prior frozen paths are
  unchanged.

## Private preregistered variation

Before execution I preserved every primary event except Right: it is released
only at frame 1664, restored at 1665 and otherwise held from 1650 through 3299.
I predicted only exact evidence through 1663 and first controller divergence at
1664. Branch timing and reconvergence were expressly not predicted. The
ignored preregistration with zero digest placeholders hashed to
`e131a8276969921c71c242f8ce1c7dea7f36ba7a1f571922efcc6d96753055eb`.

The placeholder-bound two-run replay failed only its four expected sample/final
identity checks. Both fresh processes nevertheless agreed on every declared
field over all 3,300 frames. After binding the observed identities, a second
two-process run passes 24/24: sample digest
`74c88f49399c92aca00d9a640d616f80f3407368838838611fd28face75c0425`,
final state `73ae8954b42270b8dc9417c5fe2af4a59553e059bcb3743dce131be6eecfd933`
and aggregate A/V
`7396706b8a31904402ae57275dfc5f0f32f3b29fa54d4620720103afad86cf79`.
The final ignored manifest hashes to
`5203f4241d83b7ae72cb1865136a95387596b2f17741a52cdff79fdca2bc4374`;
the passing replay report hashes to
`dedd41871f134774aab147c39992d09220cd5110d01ae5d9d1cbc6c82d02272b`.

Two captures with the candidate's complete additive watch-address and watch-PC
sets are byte-identical: access SHA-256
`b8f893f58581ea752294d24e8352fc21fe8d9d7d8d935de566dad6e2a03d9da4`
and work-RAM series SHA-256
`701d5189c7b12065809388cd911aaca772ee5971a263daedb48f69a1f41da763`.
Each contains 953,201 instructions and 471,509 accesses, zero unresolved
stores, zero PCs outside ROM and maximum ring use 18,640 of 262,144.

The authenticated end-1649 row remains
`064dea0e95ffdf1b11fc20d94fe7084a48ede5027ae6e270fd916d617d2be9f4`,
with player `(9200,1561,-1,22)`, opponent `(8248,1452,-24,-1)` and track mask
`0x3fff`. A reviewer implementation written independently of the candidate
module propagates the four residue chains across all 102 player/opponent calls
and agrees at every captured intermediate and final position. Its compact
evaluation hashes to
`ef0d0801c090dedb6ad662ceaa4a01f61eeecb7dc5cbf1e73bc8930529909f6e`;
the candidate's complete canonical rows hash to
`8b0fc030cf5f56382241e803e3ee5f93b06d334a42791ec1169b23c0741a7a5d`.

The reviewer case reaches 68 zero-surface, 19 ordinary `+4`, 14 negative-`vy`
`-1`, and one `unsupported_count_at_least_two` call. Against primary, controller
and player component first differ at frame 1664; only controller frame 1664
differs. The first slope-tail branch difference is frame 1676 and branch
differences occur at 1676 and 1685. The opponent remains exact and the player
does not reconverge by frame 1700. These are observations, not preregistered
claims. The case adds an adjacent branch-timing instance rather than a new
arithmetic class: its only newly selected class relative to primary is the
already worker-exercised unsupported-count guard.

## Original arithmetic and order audit

I decoded the exact 209 supported-PAL bytes at file offset `0x12627`, whose
SHA-256 is
`1b6497ea4306faa243c685f0f23b9ac7d22232db57ce3299f4627bbc22291adc`,
and checked their pre-instruction P/register snapshots rather than inferring
the order from the Python output.

- Accumulator and index widths remain 16 bit throughout the routine. Each axis
  performs wrapped `ADC` of velocity and incoming residue. A negative total is
  converted to two's-complement magnitude, its low five bits are isolated,
  both remainder and quotient signs are restored, and five logical `LSR`s
  implement magnitude division by 32. Position addition/subtraction follows;
  X then applies `AND $0D4F`, while Y remains unmasked.
- The reached tail order is exactly surface, guard, signed
  `unsupported_count-2`, direction high bit, vertical-velocity sign and mode.
  Its instruction forms and snapshots retain 16-bit semantics. The captured
  external position, velocity and contact arguments remain explicit in every
  row; only the four residue chains are recurrent from the authenticated seed.
- On each ordinary `+4` call, the same call stores integrated Y at
  `$82:A6B9` or `$82:A69B`; `$82:A6E5` loads 4, `$82:A6E9` enters with
  accumulator 4 for `ADC $A7`, and `$82:A6EB` enters with wrapped
  `producer+4` for `STA $A7`. Thus the direct-page dependency has same-call
  producer, instruction and register provenance rather than a guessed value.

## Integrity and validation

- Replacing the recurrent residue with the end-1649 seed on every call changes
  or leaves the supported branch domain on 99 of 102 calls; the unchanged
  evaluator therefore cannot pass via per-call oracle replacement. Seed-field,
  rider-chain, call loss/order, source/access/routine/series identity and row
  mutations reject through the focused checks and exact authored manifests.
- Removing an actual reviewer `$82:A6E9` register row rejects as incomplete;
  changing its accumulator rejects the producer/register relation. Synthetic
  signed-division, wrapped-total, signed remainder, wrap-before-mask,
  slope-tail predicate/order and adjustment mutations change or reject the
  result. Missing publications and branch evidence are bound by the complete
  row identity.
- A fresh primary capture reproduces access SHA-256
  `a53e6617baaf476e5d45c13ff60ec7ef2bfb677c5d6dfd0fe169ad919d915c2f`
  and series SHA-256
  `53c03d228999d3c1fbe5ee22be64a3965a77848e9b8f8adbeaba4374cba3d13d`.
  Primary verification reproduces component report
  `e6a787e8cebf9f77cfdf37f3126485974230c06125fbb29904aabeca186d1254`.
  The worker variation reproduces component and comparison hashes
  `33c85f3a3d2186d2e16598b04eee50c093130209d250247af3d5224d63bc4b70`
  and `195c1bb7abb8f68cc5a20d89711ba7f11f4f07b2ccc245db9976a8ba8e6a639a`.
- The published focused M4-05--M4-08 command passes 37/37. Clean `lab-debug`
  and `lab-sanitize` builds pass. Each synthetic report records 350 Python
  tests, all 20 CTest checks and three-process repeatability at
  `0be347c529fadda9`; report SHA-256 values are
  `46896800669dd941a63b207e3c09db88f7ab41155b5e966b096617ba0b7909c0`
  and `21c9a92a45f08d78128e5c98da490b3288a5b921b60d360ab5d6bb51f75b7085`.
- `git diff --check 684f78a..3a3d5ca` passes. The candidate range changes only
  the nine declared additive research/evidence files. No original content,
  captures, reports or build outputs are tracked.

The initial reviewer replay correctly reported the missing local core before I
built the pinned core; it was not counted as a pass. The deliberate zero-digest
run and the later bound run are reported separately above. No candidate
implementation, coordinator-owned registry/state or frozen accepted file was
edited. Private captures, reports, generated builds, ROM locator and toolchain
links remain ignored. The coordinator alone decides acceptance and integration.
