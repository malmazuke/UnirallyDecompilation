# M4-02 focused re-review

- Corrected candidate: `6f38439a5703223a48929dcea6875b608416e11a`
- First candidate: `c1317eed9ffe4cd476935be627bfa0b4201c4419`
- Prior review: [M4-02-review](M4-02-review.md), commit
  `258e5caa9d6ddcda1ed7411f8aa21bba018a6b83`
- Review branch/worktree: `review/M4-02-second-track-rereview`,
  `.worktrees/m4-02-rereview`
- Reviewer: fresh OpenAI `gpt-5.6-sol`, medium reasoning
- Evidence date: 13 September 2026
- Usage: 53% weekly used at focused re-review start and 54% afterward. The
  70% task stop and final 20% reserve were not reached. No reset credit was
  redeemed and no money was spent.
- Verdict: **approve**. R1 is resolved; no new finding.

## Scope and correction inspection

This re-review was limited to R1. `git show --stat 6f38439` and
`git diff --check c1317ee..6f38439` pass. Correction commit `6f38439` modifies
only `docs/research/R-0020-zoom-zoo-reference.md` and `tasks/M4-02.md`. The
prior review record is its parent, not part of the correction commit. No replay,
map, content manifest, tool, native source, frozen expectation or dependency
changed.

R-0020 now records the complete canonical access invocation: frames 1150-1750,
all 21 watched addresses, all 10 watched PCs and the implicit default ring of
262,144. It also records both successful provenance invocations with their
access paths, output/report paths, frame bounds and task value. The M4-02
handoff links those commands and records the full expected access and provenance
SHA-256 values.

## Mechanical reproduction

I executed the exact tracked access arguments in a fresh ignored directory,
changing only output/report paths as permitted by the focused re-review handoff:

```sh
python3 tools/project.py access capture --manifest tests/manifests/replay/race-crawler-zoom-zoo-3300.json --out artifacts/m4-02-rereview/access --from-frame 1150 --to-frame 1750 --watch-address 0x002115 --watch-address 0x002116 --watch-address 0x002117 --watch-address 0x002118 --watch-address 0x002119 --watch-address 0x002121 --watch-address 0x002122 --watch-address 0x002102 --watch-address 0x002103 --watch-address 0x002104 --watch-address 0x00420B --watch-address 0x00420C --watch-address 0x770825 --watch-address 0x7E0415 --watch-address 0x7E04BB --watch-address 0x7E0BEB --watch-address 0x7E0E19 --watch-address 0x7E0E1D --watch-address 0x7E0E21 --watch-address 0x7E0E25 --watch-address 0x7E0E29 --watch-pc 0x82B2DD --watch-pc 0x81B8E2 --watch-pc 0x82E12B --watch-pc 0x82E1A7 --watch-pc 0x828DB9 --watch-pc 0x828E9A --watch-pc 0x82AAA4 --watch-pc 0x82AADF --watch-pc 0x81C6C9 --watch-pc 0x81C6ED --task M4-02-rereview --report artifacts/m4-02-rereview/access-report.json --timeout 600
```

All required checks passed. The capture reproduces access SHA-256
`25c47f266e393ad7071727e88475cf890974ce35b0750969c86ee07fcb51f85f`,
frames 1150-1750, 10,270,015 instructions, 5,000,173 derived accesses,
25,650 unresolved accesses, no unresolved stores, no PCs outside ROM, 10,664
DMA triggers and 369 HDMA enables. Its sample and final-state identities remain
the frozen `791a786370913136...` and `2a843314d19e60d1...`.

I first ran the two provenance commands against that independent path. Both
passed and reproduced all counts, but their JSON hashes differed because the
provenance format records its access path. I therefore repeated the same access
command with only `--out` changed to the provenance lines' documented input
path, then ran both tracked provenance lines literally:

```sh
python3 tools/project.py content provenance --access artifacts/m4-02/access/load-riding/access.json --out artifacts/m4-02/provenance/load --from-frame 1200 --to-frame 1426 --task M4-02 --report artifacts/m4-02/provenance/load-report.json
python3 tools/project.py content provenance --access artifacts/m4-02/access/load-riding/access.json --out artifacts/m4-02/provenance/riding --from-frame 1645 --to-frame 1700 --task M4-02 --report artifacts/m4-02/provenance/riding-report.json
```

The access file again hashes exactly to `25c47f266e393ad7...`. Load provenance
passes with SHA-256
`f968585d7736986bb53a8fbd22ce2e35e2da7be410f4053eec48c86aab928658`:
1,697 transfers, 1,695 paired, 66,464 ROM-to-VRAM bytes, 532 WRAM-to-VRAM
bytes and 5,440 WRAM-to-OAM bytes. The two unpaired OAM destinations remain the
explicitly recorded optional limitation.

Riding provenance passes with SHA-256
`ad78116903821d9f2fcfb97b12e4f1642e0885365dd32ec7a987a42f22b8ce31`:
1,523/1,523 paired transfers, 46,304 ROM-to-VRAM bytes and 2,058
WRAM-to-VRAM bytes. Thus the tracked watch lists and both provenance commands
are complete and mechanically usable, and reproduce the exact accepted
identities when their ignored paths are kept consistent.

The earlier independent review already reproduced the replay, withheld case,
coverage, content, DRAGSTER/native regressions and hygiene. Those checks were
not rerun or broadened for this record-only correction.
