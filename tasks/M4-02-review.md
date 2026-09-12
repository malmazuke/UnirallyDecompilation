# M4-02 independent review

- Candidate: `c1317eed9ffe4cd476935be627bfa0b4201c4419`
- Candidate parent / claimed worktree start: `1c8657e`
- Review branch/worktree: `review/M4-02-second-track`, `.worktrees/m4-02-review`
- Reviewer: fresh OpenAI `gpt-5.6-sol`, medium reasoning
- Evidence date: 13 September 2026
- Usage: 52% weekly used at review start and 53% after the complete checks;
  the 70% task stop and final 20% reserve were not reached. No reset credit was
  redeemed and no money was spent.
- Verdict: **return one documentation/reproducibility finding**. The behavioral,
  coverage, content and regression claims reproduced, but the exact command
  needed to regenerate the claimed access/provenance record is absent despite
  the candidate saying it is preserved in the task handoff.

## Fresh environment and candidate inspection

The checkout was clean at the exact candidate before review. `local/emulators`
and `local/toolchain` are links to the shared read-only dependencies; all review
outputs and the private system/save directory used for each fresh worker launch
were created under ignored `artifacts/m4-02-review/` and began empty. The native build used this review worktree's
ignored `build/lab-debug`. No shared dependency was modified.

`git diff --check 1c8657e..c1317ee` passed. The candidate commit changes only
the eight paths listed in its handoff. `git ls-files` found no `.sfc`, `.smc`,
`.srm`, `.bin`, `.png`, `.rnc`, `.pack`, trace or WRAM artifact. The regenerated
map is byte-identical to the tracked map, and the ROM-free map test confirms that
tracked maps contain no ROM bytes. The reference-only content manifest holds
offsets, sizes and hashes, not payload bytes.

## Replay identities, clean SRAM and displayed coupling

Commands:

```sh
python3 tools/project.py replay validate --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json
python3 tools/project.py replay validate --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300-release-2500-2599.json
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --runs 2 --artifacts artifacts/m4-02-review/freeze/runs --report artifacts/m4-02-review/freeze/report.json --task M4-02-review --timeout 600
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --against tests/manifests/replay/race-crawler-zoom-zoo-3300-release-2500-2599.json --artifacts artifacts/m4-02-review/tracked-release/runs --report artifacts/m4-02-review/tracked-release/report.json --task M4-02-review --timeout 600 --no-localize
```

Both validations passed. The two-run freeze passed every required identity:
3,300 common frames, sample digest
`791a786370913136e21ed34c841e9a3d892852bf6804e2e0aef21e1df6557b68`,
serialized state
`2a843314d19e60d13dab746541d43ffa9ad84adfe6f95b9cc6d3c45bd9a16aeb`
and A/V
`dc7ca8ff6db1c2bbef17efd639c74f0d238a93f920e3b8f72b1c5ad80b1be22a`.
The report SHA-256 is
`c0e45d3a7332217c82ae5f97ed433f8f4a4dd2ad3dde925fca6a7299d88c0280`.
The workers used distinct PIDs. Both began with no save file, initial WRAM
`fa43239bcee7b97ca62f007cc68487560a39e19f74f3dde7486db3f98df8e471`
and cartridge RAM
`7d2c7ac4888bfd75cd5f56e8d61f69595121183afc81556c876732fd3782c62f`.
Each wrote its own SRAM only after starting. This supports the candidate's
bounded clean-start wording, not a claim about arbitrary learned SRAM.

The tracked release reproduced sample digest
`c253de4bce372be26b0457fa870b72c7a1acddb953a3ecf9ee187006ad55d63e`
and state
`00bf36ed74988b785f96c9e21116b2920915d85a81896b275255961d0330127d`;
its expected behavioral compare exited 1 at frame 2500. Report SHA-256:
`64300570e8fc1d6b446ea7772e99d0663d8d18c3080de90ad7888cecf78fee50`.

A fresh access capture with images at 999, 1003, 1006, 1100 and 1199 shows the
selector moving from DRAGSTER to ZOOM ZOO, then `NOW PLAYING` displaying `1P`,
MIKE versus BRONSEN, `OVER 3 LAPS ON ZOOM ZOO`, and Race/Exit. This verifies the
displayed coupling only; it does not establish independent opponent/event
variables or general AI behavior.

## Withheld adjacent boundary

Before any review execution I created ignored
`artifacts/m4-02-review/withheld-release-2501.json`, changing only the Right
release boundary: Right remains held through frame 2500 and is absent on
2501-2599. The recorded prediction was exact agreement through frame 2500,
first divergence at 2501 in the horizontal joypad image and throttle, followed
by a speed or position response in that update or later.

The first discovery run intentionally retained the tracked 2500 variant's
expected identities and failed those two identity checks while preserving the
new samples. After recording the observed reviewer-only identities in the
ignored manifest, a fresh repeat reproduced sample digest
`46410fda33076403c375eca4af1a39e0c98273518396f541f7294681bebb42d7`
and serialized state
`af1bb336957fdb8ffd3f2423333361e1b34cab95d76181673083adbd7facebde`.
The expected behavioral compare exited 1 with exact agreement through 2500 and
first divergence at 2501. Its report and divergence SHA-256 values are
`ab23af58a1ac155593ee35c0ad8498efbea25622e6ddd10e9a1e46fc9f3c9e35`
and `fae616854e61156e3691555e1886e6a5d337c59304012f4f2427963740177752`.

Two fresh access captures over 2499-2503 have SHA-256
`5136ca4a48c500f46c3c927016cdaa335a5db837045d15f85f4c8d974d626095`
and `2660d874744ef8dc92cfa8486907b797f0ce9b7d1c9eba83211e331ed43718bb`.
At 2501 `$80:87F2` stores `$7E:0313` as 1/0 and `$82:8DBF` stores
`$7E:0BEB` as 432/0. `$82:8E9A` already differs in that update (462/437 before
the accepted copy writers); `$82:8DB9` writes equal position 14011 at 2501 and
different positions 14026/14024 at 2502. Thus input delivery and subsequent
motion-writer response agree exactly with the predeclared prediction.

## Timing, fields and learned-state boundary

The fresh 990-1590 capture (`access.json` SHA-256
`3c6f81e35d089d55c245007a8b3645233debdbc239030233368c16bb1807e2f0`)
shows `$81:C6C9` first writing `$7E:0E29` at 1583, then once per frame; the
counter reaches 5 and `$81:C6ED` resets it at 1587. Frames 1583-3299 inclusive
are exactly 1,717 timer-active frames (34.34 PAL seconds). Coverage independently
places the NMI gap at 1208-1376 and the once-per-frame continuation at 1377.
The wording is appropriately timer-active rather than a claim that the black
load presentation itself is riding.

A fresh 1200-1750 access record confirms the candidate's field safety table:
the primary player/opponent position writers and player displacement, throttle
and speed writer each execute 374 times over frames 1377-1750; joypad image
delivery begins at 1382; timer cadence begins at 1583. `$77:0825` is zeroed at
1291, read at 1628-1634 and written to 4 at 1672. These observations support
only this clean-start BRONSEN path. The candidate correctly leaves camera,
collision, finish and presentation meanings unsafe to reuse.

## Coverage and content

Two complete fresh captures and two maps were generated into ignored paths.
Both coverage files have SHA-256
`476de96fa13b2cff31166037d654c5724634d280de0945ae4baf10e1d9ccd41d`;
both regenerated maps have SHA-256
`b1e17356f656be5d225753ceb7e3d094b5839a33c98655b48b3e6b1b842f4903`,
and both summaries have SHA-256
`84c7dd6efcd929558e1381985ce4007eeb0b00b769bb7cb6990413bab5cd982c`.
They are byte-identical to the tracked files. The DRAGSTER baseline delta is
4,014 bytes / 268 entry points only here, 1,185 bytes / 45 entry points only in
the baseline, and 33,715 shared bytes. The research record explicitly treats
menu input, load duration, movement timing/path and total duration as
confounders, so it does not overstate this as a pure track-causal delta.

Commands included two `coverage capture` invocations followed by two identical
`coverage map --baseline docs/map/race-crawler-dragster-3000.map.json`
invocations, with outputs under `artifacts/m4-02-review/coverage-{1,2}` and
`map-{1,2}`.

```sh
python3 tools/project.py content decode --manifest tests/manifests/content/zoom-zoo-reference-inventory.json --out artifacts/m4-02-review/content-zoom-zoo --report artifacts/m4-02-review/content-zoom-zoo-report.json --task M4-02-review
```

Decode passed at 50,665 bytes with SHA-256
`db6770152e399f9d16fc6937b5d56588a8f67e825ae70d6578b77d36053fdd28`.
The exact 6,599-byte ROM slice at offset `0x0C0183` independently hashes to
`3a8b470c673d0db36bc842f16b61b5a72575fac002c09e795112d747ea940646`.

I also reconstructed a fresh port-watch access capture over 1200-1750 and ran
provenance for 1200-1426 and 1645-1700. The load result exactly reports 1,697
transfers, 66,464 ROM-to-VRAM bytes, 532 WRAM-to-VRAM bytes, 5,440 WRAM-to-OAM
bytes and 1,695/1,697 paired destinations; its VRAM/CGRAM images hash to the
claimed `970b3988...` / `c47e9fe5...`. The riding result exactly reports 1,523
paired transfers, 46,304 ROM-to-VRAM bytes and 2,058 WRAM-to-VRAM bytes; its
images hash to `691c3d75...` / `61876568...`. The ROM source envelope is
`$27:8000-$34:E2BF` (file offsets `0x138000-0x1A62BF`) and the WRAM source
envelope is `$00:0437-$00:0478`. The record correctly says these are envelopes,
not claims that every intervening byte was read.

## Frozen regressions

```sh
python3 tools/project.py replay compare --manifest tests/manifests/replay/race-crawler-dragster-3000.json --runs 2 --artifacts artifacts/m4-02-review/dragster-freeze/runs --report artifacts/m4-02-review/dragster-freeze/report.json --task M4-02-review --timeout 600
python3 tools/project.py content decode --manifest tests/manifests/content/dragster-segment.json --out artifacts/m4-02-review/content-dragster --report artifacts/m4-02-review/content-dragster-report.json --task M4-02-review
python3 tools/project.py content pack-inspect --pack local/classic-crawler-dragster.pack --report artifacts/m4-02-review/pack-inspect-report.json --task M4-02-review
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack local/classic-crawler-dragster.pack --save-frame 1600 --save-frame 3213 --save-frame 3453 --save-frame 3678 --artifacts artifacts/m4-02-review/native-finish --report artifacts/m4-02-review/native-finish/report.json --timeout 120 --task M4-02-review
python3 tools/project.py test --suite synthetic --preset lab-debug --artifacts artifacts/m4-02-review/synthetic --timeout 180 --test-timeout 30
```

DRAGSTER passed two fresh processes at sample digest `72f618f2f7e3416e...`
and state `0f3cc38bd5d64401...` (report
`1cc351c1db221400a23889fd73aab91443751201b7f867a3de47c691cb793751`).
All ten DRAGSTER content entries passed. The existing pack passed structure,
25-entry inventory and all payload hashes. Native finish/restores passed all
18 checks (report
`5ecc0952971a96671bd71874e79632305538f574d6336e25cc55bad4f0d04c5a`).
The ROM-free suite passed 315/315; its CTest XML SHA-256 is
`12f868442d5943cf3f48dc11cc78f629c485db5fdf1827d181cc0e447c616cd2`.

## Return finding

### R1 — Restore the missing exact access/provenance regeneration commands

`docs/research/R-0020-zoom-zoo-reference.md` says the exact access command is
both in the ignored access record and preserved in the M4-02 handoff. It is not
in `tasks/M4-02.md`: the handoff gives only the frame window, record hash and a
summary. The research reproduction block likewise omits `access capture` and
both `content provenance` commands. A fresh checkout cannot regenerate the
claimed `25c47f266e393ad7...` record or determine its complete address/PC watch
set, and the ignored worker record named as the other source is intentionally
unavailable. My independently reconstructed port-watch record has a different
hash (`a2da880d1903513b...`) even though it reproduces the reported provenance
aggregates, which demonstrates why a summary is not the promised exact command.

This is a bounded record-only correction: add the exact successful `access
capture` command and the two successful `content provenance` commands (including
all watch arguments, frame bounds and ring) to a tracked task or research
record, correct the sentence claiming they are already present, and confirm
that the access command regenerates `25c47f266e393ad7...`. No candidate evidence
or implementation should be silently changed by the reviewer.
