# M2-01A contact worker handoff

Checkpoint 1: 12 September 2026. Base/head `ba71142a6d766216772360949dd8c04760fa9ffe`,
branch `codex/M2-01A-contact`, isolated `.worktrees/m2-01a-contact`.
Dirty authored research/capture and variation manifest; no existing files changed.

Doctor/bootstrap/debug build passed; synthetic 211 checks passed. Sampling probe
reproduced 29,320 words using prior primary capture and static local content;
report `artifacts/m2-01a-contact/sampling-baseline.json`. Primary focused capture
command: `python3 -m tools.unirally_lab.native.contact_research.capture --out artifacts/m2-01a-contact/primary`.
Passed, unchanged sample/final digest; access SHA starts `6e5144706276c3a3`,
778,312 instructions / 388,664 accesses, zero unresolved stores. ROM/core unchanged.

Verified: primary has negative-support summary => saturating unsupported count,
continued-contact branch for incoming count <9, and distinct recontact for >=9.
Caller copies prior pre-correction positions from persistent `$04D7/$04DB`
(player) and `$04D9/$04DD` (opponent); contact writes them before correction.
The separate unsupported-duration word persists at `$0FC1/$0FC3`.

Next: finish already-running preregistered release-1570 capture, derive ordered
per-call summaries, widen primary to 1534–2999 with only needed state watches,
validate narrow formula contracts, document preprocessing and recontact coefficients.
No withheld movement outputs opened. No failed behavioral hypothesis so far.

## Checkpoint 2 / review preparation

The contract is now implementable for the post-seed primary domain. Full capture
proves 2,889 continuous /42 unsupported /one recontact. Research variation
retains predicted counter/contact behavior. Isolated arithmetic checks pass
37,989 primary relations,1,006 variation relations and17,592 primary preprocessing
values; seven authored tooling tests pass. R-0011-contact records exact commands,
hashes, publication mapping, context guards and the two tooling failures fixed
without altering any expectation. Contact's landing impulse4 reaches opponent
`$0D37` for subsequent pose/orientation damping. Coordinator and motion worker
have the interface and concrete1617 inputs/outputs.

Next command: clean-source full synthetic suite after scoped candidate commit;
then send exact candidate and handoff for independent review. Broader geometry,
upward support and other landing buckets remain unsupported, explicitly bounded
out rather than invented. No native gameplay implementation or withheld run.

Final-suite attempt at7271b3d failed: the new test module imported`tools.unirally_lab`,
which direct unittest discovery permits but the project's subprocess runner does
not put on its path. Existing tests explicitly prepend the tools directory and
import`unirally_lab`; the new test now follows that convention. The failure was
reported as a failure (200 tests including one failed import), not a pass.
No gameplay/model/evidence change. Re-running after the import-only fix.

## Submitted research result

Implementation/tooling candidate: `f979f0e0bd13c2c4ba709cd3a69879f9ecbf2160`;
base `ba71142a6d766216772360949dd8c04760fa9ffe`. Clean-source full suite at that
candidate passes218/218 checks (206 Python tests); report SHA-256
`2a0fb2f5b293b41a66840f61b2847b0786e0358b56a2f62292b21c8738a47f14`.
This documentation follow-up records the result and corrects the response-B
inventory: B is2 on24 unsupported opponent calls1590–1613, preserved by contact,
then motion clears it before recontact. Update formula/evidence unchanged.
R-0011-contact now includes a native interface proposal reusing the sampler
structures and preserving contact-specific state inside future RiderState.

All requested scoped research/tools/manifests/tests are committed; obtain the
final documentation submission hash with`git rev-parse HEAD`. No frozen expected
file, existing source/interface, ROM, extracted byte file or native gameplay
simulation changed. Independent reviewer acceptance remains pending. Coordinator
will authorize native port separately after review; this task does not accept
M2-01A or M2-01. Stay available for review fixes/interface decisions. Exact next
independent command is the full primary capture in R-0011-contact; existing local
captures may accelerate an inspection but must not substitute for reproduction.

## Native continuation checkpoint 1

Coordinator amendment090e758 authorizes new flat_contact source, contact native
tests/probe and CMake registration. Branch starts from280e282 research head.
New C++ component and typed interface are implemented. First valid debug probe
matches70,368 outputs across2,932 primary calls, composing native pose expansion,
track sampling, preprocessing and response from captured incoming motion/state.
Focused release variation matches2,064 outputs across86 calls. Three authored
C++ test groups pass (sampling, response, boundaries). Fresh native-input captures
add explicit phase0300, auxiliary flag and cartridge-option watches; original
primary sample/final hashes unchanged. Paths`artifacts/m2-01a-contact/native-*`.

Reviewer fixes: calls() now rejects reversed/empty/noninteger/inconsistent frame
ranges before a comparison can pass without calls; authored regression passes.
ContactContext has explicit`cartridge_options & 8 == 0` plus opponent guard for
recontact, corresponding to94A8/94AF/94B4. Source rejects unsupported algorithm
branches before committing any state mutation. No frame or coordinate-tuple
lookup exists. Motion worker/coordinator have concrete header/field mapping.

Current commands running: sanitizer build, contact CTest groups and both native
probes. Next: finish results, document new interface/probe commands, inspect diff,
commit scoped candidate and run clean-source full suite. No native gameplay or
withheld series comparison has run. This remains a captured-input component.

## Native component submitted

Exact implementation candidate: `d031a0eed7f0cb8895ae9b78052fcaac0c29c05c`,
clean during all final checks. The documentation submission following it changes
only this handoff and R-0011-contact. Clean suite222/222 (207 Python tests); clean
debug and sanitizer probes match70,368 primary and2,064 variation outputs each;
three sanitizer contact CTest groups pass without diagnostics. All hashes and
commands are in R-0011-contact's final sections. Debug/sanitizer output files are
byte-identical for each case. Native captures use explicit phase/auxiliary/option
watches and preserve original identity and primary expected digests.

New library`unirally_contact` links the existing`unirally_sampling`; CMake adds
contact_probe/contact_tests and three test groups. No existing sampler interface
changed. No complete RiderState or serialization has been introduced: contact
persistence is a small member ready for composition with shared motion fields.
Guard failure is transactional; no coordinates/frame tuple drives dispatch.
Reviewer research findings are fixed (nonempty-range validation and explicit
cartridge-option context guard). Native review is still required. No hidden
movement case or reference expectation was read/altered. No new failed native
comparison arose; first valid native executions matched both cases.

Next independent action: build this candidate in the reviewer worktree and run
the documented capture/probe pair with its own research variation, plus contact
CTest under sanitizer. Coordinator owns integration and final acceptance;
worker remains available for specific review fixes.
