# M3-04 independent review — playable-slice acceptance

- Candidate reviewed: `c2c890993bd5773098b5d8a30221261881d67cef`
- Diff reviewed: task start `36f742f295ac109c1b63a3d82baf266db5595950`
  and candidate base `55fb1d5882f00a0a791a752ec605cc4b5dc6c0e9`
  through `c2c8909`
- Reviewer: fresh OpenAI Codex Sol/medium session
- Worktree/branch: `.worktrees/m3-04-review`,
  `review/M3-04-playable-acceptance`
- Date: 13 September 2026 AEST
- Verdict: **approved with no material findings**

## Findings

No material correctness, compatibility, packaging, presentation, diagnostic or
evidence-honesty defect was found in the reviewed diff.

The recovered opponent-first path is narrowly bounded and source-backed rather
than presented as a general AI implementation. The native contract compares
the opponent's x/y/velocity/pose and the unfinished player's timer/finish state
against a pre-implementation frozen original projection on every frame through
3999. The additive 371-byte `URMV0003` state carries the finish-pose selector;
333-byte V1 and 369-byte V2 remain readable, V2 offsets are unchanged, and the
reviewed save/restore checks cover both sides of the opponent finish and speed
settling boundaries. The diagnostic counters observe SDL events and sampled
inputs without changing their ordering or the one-snapshot-per-update path.
The macOS bundle change is platform-conditional and the established Linux
executable path remains covered by the tooling regression.

## Clean extraction and pack-only launch

The review checkout began without `build/`, a generated pack or a ROM locator.
It reused only symlinked checksum-pinned cache/toolchain directories. The
following tracked commands passed from that state:

```text
python3 tools/project.py bootstrap --report artifacts/m3-04-review/bootstrap.json
python3 tools/project.py build --preset app-debug --report artifacts/m3-04-review/build-app-debug.json
python3 tools/project.py rom inspect --path local/m3-04-review-pal.sfc --expect tests/manifests/rom/unirally-pal.json --report artifacts/m3-04-review/rom-inspect.json
python3 tools/project.py content pack --rom local/m3-04-review-pal.sfc --out local/classic-crawler-dragster.pack --report artifacts/m3-04-review/pack-create.json
python3 tools/project.py content pack-inspect --pack local/classic-crawler-dragster.pack --report artifacts/m3-04-review/pack-inspect.json
python3 tools/project.py frontend run --pack local/frontend-first-launch.pack --rom /tmp/m3-04-review-pal.sfc --updates 5 --hidden --report artifacts/m3-04-review/frontend-first-launch.json
python3 tools/project.py frontend run --pack local/frontend-first-launch.pack --updates 5 --hidden --report artifacts/m3-04-review/frontend-first-launch-pack-only.json
```

The supplied ROM matched all ten tracked identity fields and the supported PAL
SHA-256. Both extraction routes produced byte-identical 25-entry packs. Before
the second frontend command, the external ROM was renamed out of reach and the
checkout had no locator. The second report states `ROM was not opened`.
An existing 100-byte truncated pack was rejected and left at 100 bytes even
with a valid ROM argument; a tracked JSON used as a ROM was rejected before an
output pack appeared. These negative commands exited 3 as required.

Key ignored report SHA-256 values are:

| Evidence | SHA-256 |
| --- | --- |
| bootstrap | `ed93d726e78b45560c3495705add4848ffbca00753d8285ba81d1acc65712a87` |
| app-debug build | `e74b6715bb34bc14bc0b37a3fc060446d955d3e6e7da7a6f26ab2bb11c1cfadb` |
| ROM inspection | `3faf7204642866e7b3391b86c59ae7bfa4a22b921758908d6f259748a13e9c04` |
| direct pack creation / inspection | `8923a313c8440ba0cd3ce28bd0aa6f7e305f24eaa329c108bb73bde3072a9750` / `6778cee565f270f3c73694efc33a7be435023924bebbeb5c7734ae2f164eeb53` |
| frontend first launch / pack-only relaunch | `d6b952bba359d99e53e8f37545efb306061f3d35fc7eaba95bdd7b56ad690b3a` / `3894d8db7bb384b0801e332148bd7de6b4eac8cbd8eed9e52d67cf03d393e796` |
| corrupt pack / wrong ROM | `a4e3604a60f8341fddac03e1ecf4678de9391ecd7c02a2ce4be4b590210731e0` / `29cf132c91577c03955152633b4544511e486ed1e7e1eff32bbaebe36ada2fc9` |

## Reviewer-owned visible boundary

I launched the real review-built `org.unirally.classic` app from the validated
pack without a ROM and used computer use to inspect its 768x700 SDL window. It
remained visibly current through a bounded 2,500-update run, reached semantic
frame 4033 (past the former frame-3435 failure), and exited normally after
50.353 seconds. The final report records 2,498 presentation frames, maximum
identical run four frames, zero focus losses, final neutral mask and no ROM
open. Report SHA-256:
`f35f7e43ae5807759bc44c47637aa1f06e1e11f28f403aee3bb4b53d88d42063`.

I also delivered 40 Right and 10 Z key taps to the focused SDL window. All 50
down/up pairs were mapped, but none overlapped a PAL sampling update, so this
review does **not** claim independent live-input acceptance. The reviewer-owned
M3-04 boundary is sustained visible presentation, as permitted by the task.
The worker/coordinator live-input evidence remains separately identified in
R-0017. Audio and unrecovered intermediate rider art remain declared omissions.

## Exact gameplay, restore and presentation checks

These candidate-bound checks passed with the independently generated pack:

```text
python3 tools/project.py native opponent-first-check --manifest tests/manifests/native/m3-04-opponent-first.case.json --content-pack local/classic-crawler-dragster.pack --save-frame 3214 --save-frame 3215 --save-frame 3231 --save-frame 3234 --save-frame 3435 --artifacts artifacts/m3-04-review/opponent-first --report artifacts/m3-04-review/opponent-first/report.json --timeout 120
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-continuous.case.json --content-pack local/classic-crawler-dragster.pack --save-frame 1600 --save-frame 3213 --save-frame 3453 --save-frame 3678 --artifacts artifacts/m3-04-review/full-continuous --report artifacts/m3-04-review/full-continuous/report.json --timeout 120
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-release.case.json --content-pack local/classic-crawler-dragster.pack --save-frame 1600 --save-frame 3318 --save-frame 3558 --save-frame 3799 --artifacts artifacts/m3-04-review/full-release --report artifacts/m3-04-review/full-release/report.json --timeout 120
python3 tools/project.py native finish-check --manifest tests/manifests/native/full-race-review-release-3213.case.json --content-pack local/classic-crawler-dragster.pack --save-frame 1600 --save-frame 3213 --save-frame 3226 --save-frame 3453 --save-frame 3678 --artifacts artifacts/m3-04-review/full-review --report artifacts/m3-04-review/full-review/report.json --timeout 120
python3 tools/project.py native presentation-check --manifest tests/manifests/presentation/classic-crawler-dragster-v1.json --fixtures artifacts/m3-04-review/presentation-fixtures --content-pack local/classic-crawler-dragster.pack --preset lab-debug --artifacts artifacts/m3-04-review/presentation --report artifacts/m3-04-review/presentation/report.json --timeout 120 --task M3-04
```

Opponent-first passed two fresh processes and all five continuations. The three
full-race paths passed exact gameplay/finish comparison, fresh-process
repeatability and every requested cross-phase continuation. All seven visual
mismatches were unchanged: 36/26,656; 697/50,176; 279/50,176; 445/50,176;
653/50,176; 962/57,344; and 961/57,344.

Report SHA-256 values are opponent-first
`a443eba680382f2a6c6379038fb6b412182619071ff4fb0003ce7f5f5b31177d`,
continuous `3ced84776c54145bccd6ddc6a432c77186340cfcaf4b9ed6bcc8ce74337c6b53`,
release `1c3d171d07d7b63430b0a1dfb1fe7fc5dbb0a6f49305c6aa1dc5de6cf62b1fe1`,
reviewer release `b4f7b60b12c9d84488f5fa6a59f6777c1010f606b522dd892bcc2d5c6b099301`,
and presentation
`209f46033a8600e46bc6ab69c0979fcb84272d5e7e003abe885345410cc9d641`.

The original-side replay was also run in a fresh process with the pinned bsnes
core and the supplied PAL ROM. It reported PAL and reproduced sample digest
`6ef702112e824ad6...` and final state `2d3d727a1ff8069e...` exactly. Report
SHA-256:
`7ff666457342c7868d037f63dd0dcce8be4a657f17d29a16beeb88a67481338c`.

## Broad suites and hygiene

```text
python3 tools/project.py build --preset app-sanitize --report artifacts/m3-04-review/build-app-sanitize.json
python3 tools/project.py test --suite synthetic --preset app-debug --artifacts artifacts/m3-04-review/suite-debug --report artifacts/m3-04-review/suite-debug.json --timeout 120 --test-timeout 30
python3 tools/project.py test --suite synthetic --preset app-sanitize --artifacts artifacts/m3-04-review/suite-sanitize --report artifacts/m3-04-review/suite-sanitize.json --timeout 120 --test-timeout 30
git diff --check 55fb1d5..c2c8909
```

Both suites passed 314/314 required records: 291 Python tests, 20 CTests and
three fresh-process runs. Debug report SHA-256 is
`de4d095f03b00e0e697902c1b4ce0a4c3e3eebc4b75e027c22a5855750cd75a0`;
sanitizer report SHA-256 is
`a4d220491f563803429eb9a63c1fa4d323ab05cf795ef0bc4c6bd41d07379b52`.
`git diff --check` passed. No ROM, generated pack, state, capture, screenshot,
report, locator or other private binary is tracked; the review worktree had no
tracked change before this record.

## Limitations and coordinator gates

This approval applies to the supported PAL one-player CRAWLER/DRAGSTER slice
and the explicit M3 omissions only. It does not establish other tracks, riders,
modes, multiplayer, audio, complete pose art, packaging or public release.

Hosted macOS/Linux CI for the exact integration candidate was not available to
this review session and remains a coordinator gate. This review does not accept
M3-04 or M3, update the registry/state, create the `m3` tag, push, publish or
deploy. Those actions remain with the coordinator after exact-candidate hosted
evidence is green.

## Focused CI path re-review — `2be0aa6`

- Main commit reviewed:
  `2be0aa6e2f3bd4a8ed3d4f1fe0127caa2c6f1a64`
- Parent: `4cd9d66`; exact diff is one workflow hunk in
  `.github/workflows/synthetic.yml`
- Verdict: **approved with no findings**

The M3-04 merge exposed a CI-only macOS failure: `MACOSX_BUNDLE` places the
clean-build executable at
`build/app-debug/src/app/unirally.app/Contents/MacOS/unirally`, while the
workflow still invoked the former unbundled path. The correction selects that
bundle path when GitHub's `RUNNER_OS` is `macOS` and retains
`build/app-debug/src/app/unirally` otherwise.

This matches all three relevant boundaries. `src/app/CMakeLists.txt` uses
`MACOSX_BUNDLE` only under `APPLE`; `_default_executable` in the frontend
resolver selects the same bundle inner executable only when `sys.platform` is
`darwin`; and the existing focused test requires precisely that Darwin path
and the unchanged Linux path. A path-limited diff proved those production and
test files are byte-identical between the already-reviewed `c2c8909` and
`2be0aa6`.

Exact focused commands and outcomes:

```text
git show --format=fuller --find-renames 2be0aa6 -- .github/workflows/synthetic.yml src/app/CMakeLists.txt tools/unirally_lab/frontend/commands.py tests/tooling/test_frontend.py
# one workflow file changed, 6 insertions and 1 deletion

git diff --exit-code c2c8909 2be0aa6 -- src/app/CMakeLists.txt src/app/sdl_main.cpp tools/unirally_lab/frontend/commands.py tests/tooling/test_frontend.py
# exit 0; no production/test difference

git diff --check 2be0aa6^..2be0aa6
# exit 0

git show 2be0aa6:.github/workflows/synthetic.yml | ruby -e 'require "yaml"; YAML.safe_load(STDIN.read, aliases: true); puts "yaml-parse=passed"'
# yaml-parse=passed

test -x build/app-debug/src/app/unirally.app/Contents/MacOS/unirally
# exit 0

RUNNER_OS=macOS bash -c 'if [[ "$RUNNER_OS" == "macOS" ]]; then build/app-debug/src/app/unirally.app/Contents/MacOS/unirally --help; else build/app-debug/src/app/unirally --help; fi'
# exit 0; printed the expected Unirally usage, controls and audio omission

PYTHONPATH=tools python3 -m unittest discover -s tests/tooling -p 'test_frontend.py' -v
# 10 tests run in 2.561s; OK
```

The local host is macOS arm64, so the bundle existence and runtime-link/help
boundary were executed directly. Linux was verified structurally through the
unchanged non-Apple CMake branch, workflow `else` branch and the focused
platform-mocked resolver test; no Linux host was available in this review
session. A hosted rerun remains the coordinator's evidence gate. This focused
approval does not alter coordinator acceptance records or authorize another
acceptance, tag, push, publication or deployment.
