# M3-02A independent review

- Candidate reviewed: `e5b0ddf`
- Corrected behavioral candidate: `c86874d` (integrated on `main` as `70fceec`)
- Reviewer: fresh OpenAI Codex `gpt-5.6-sol`/medium session
- Outcome: accepted after one returned finding and exact-candidate integrator recheck

The reviewer independently generated the 86,485-byte pack twice from the PAL
ROM and obtained SHA-256 `0b9a0557...343f`, ran the reviewer-owned full-race
case with a withheld restore boundary at frame 3212, and ran both debug and
sanitizer suites at 295/295. No reference baseline or private asset was changed
or tracked.

The first candidate was returned because direct `movement_runner` use accepted
a pack whose source-ROM identity byte at offset 12 was changed. The stable
Python command rejected it, but `ClassicContentPack` skipped the source/rules
hashes and trusted table-provided entry hashes. The mutated and valid packs
therefore produced identical 2,148-line native output.

Correction `c86874d` binds the native reader to the exact PAL source hash,
frozen extraction-rules hash and all thirteen expected logical-ID/size/hash
tuples before exposing a payload. The worker added the ROM-free
`classic_content_pack_identity_rejection` test and demonstrated direct source,
rules, row-digest and payload rejection. Debug and sanitizer suites increased
to 296/296 and both pack-backed full-race/restore cases remained exact.

The collaboration runtime would not reopen the completed reviewer after the
fix. The integrator therefore rechecked the exact correction without editing
it: independently rebuilt it, generated the exact pack, repeated direct source
and rules mutations, observed exit 1 with zero output lines and the responsible
errors, ran the focused CTest, and ran the complete debug suite at 296/296
(report SHA-256 `2795519a...d7a`). The integration candidate `cd37469` then
passed local debug and sanitizer suites at 296/296 (report hashes
`09294505...21f9` and `0f878cda...c9ad`) and hosted run 34685007265 passed on
macOS 15 and Ubuntu 24.04, including Linux sanitizers.

Approval is limited to one exact PAL ROM and the CRAWLER/DRAGSTER gameplay
content/start boundary. Presentation extraction, SDL, audio, other modes and
distribution/legal clearance remain outside M3-02A.
