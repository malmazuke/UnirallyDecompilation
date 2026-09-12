# R-0017 — M3 playable-slice acceptance

- Task: [M3-04](../../tasks/M3-04.md)
- Status: evidence candidate; independent review/hosted gates remain pending
- Candidate base: `55fb1d5882f00a0a791a752ec605cc4b5dc6c0e9`;
  correction candidate `0803735`
- Tested host: macOS arm64, 13 September 2026
- ROM identity: supported PAL SHA-256 `a1105819...fd4e`
- Classic pack: 25 entries, 154,030 bytes, SHA-256
  `5c1fc5b0...1529`; extraction rules SHA-256 `70712c47...d768`

This record maps the component regressions and completed local real-play
integration evidence. It does not accept M3-04 or M3.

## Clean installation and archive-only launch

Before bootstrap, `git status --short --branch`, `find build` and `find local`
showed a clean task worktree with no `build/` and no generated pack. The only
ignored local entries were the shared download cache, pinned toolchain cache and
the pre-existing ROM locator. No prior build or pack was copied in.

`python3 tools/project.py bootstrap` reused only the checksum-pinned cache, and
`python3 tools/project.py build --preset app-debug` configured and built from
that baseline. Their ignored report SHA-256 values are `9dbf17ba...bb3c` and
`e03cff76...2727`.

An ignored disposable copy of the ROM passed the tracked identity manifest
10/10, including size, mapping, region, internal checksum and SHA-256 (report
`22813155...e4eb`). The first `frontend run --rom ... --updates 5 --hidden`
exact-gated those bytes, atomically created the 25-entry pack and revalidated it
before launch (report `eba80536...dcec`). Independent `pack-inspect` passed the
schema, complete inventory and every entry digest (`bbdf663c...851bf`).

The disposable ROM and `local/rom-location.txt` were then moved outside the
checkout. Their absence was asserted before `frontend run --updates 5
--hidden`. That launch passed from the existing pack and its report explicitly
states `ROM was not opened` (`269c68ad...f8ff`); a second pack inspection passed
(`3abd92e5...b30`). No ROM, WRAM/SRAM seed or loose extracted content appears in
the pack-only frontend or native command inputs.

The following negative cases were then run deliberately:

- a non-ROM tracked JSON input returned invalid input before creating a pack
  (`3e29a768...dad4`);
- `content pack --simulate-interruption-before-commit` with the supported
  external disposable copy returned failure, leaving neither output nor a
  temporary pack (`2dca5526...3bd`);
- a truncated copy of the valid pack was rejected as an existing corrupt pack
  and was not replaced even when an explicit valid ROM path was also supplied
  (`aa83e850...77e8e`).

These results satisfy the extraction, identity, atomicity, failure-path and
archive-only portions of the M3 project-plan and build-validation gates on this
candidate state.

## Accepted gameplay and presentation regressions

All commands below used only the validated pack and fresh native processes.
Each exact gameplay/finish comparison and every requested continuation passed:

| Path | Restore frames spanning phases | Outcome | Report SHA-256 |
| --- | --- | --- | --- |
| continuous Right | 1600, 3213, 3453, 3678 | exact through stable result | `b3a36b6c...90d2` |
| release 3000–3299 | 1600, 3318, 3558, 3799 | exact through stable result | `4fddb368...e3a3` |
| reviewer release 3213 | 1600, 3213, 3226, 3453, 3678 | exact through stable result | `2de572af...425` |

`native presentation-check` revalidated all seven private, identity-bound cases
at their unchanged limits. Exact mismatches were 36/26,656, 697/50,176,
279/50,176, 445/50,176, 653/50,176, 962/57,344 and 961/57,344 (report
`deca6709...1b07`). This retains the declared omissions: intermediate rider
poses reuse only the last recovered rider art, while current scene/camera/HUD
and effects are redrawn; audio is not implemented.

The dirty candidate with the macOS-launch diagnostic passed both complete
ROM-free suites: app-debug 311 records (288 Python, 20 CTest, three fresh
processes), report `99ca04a5...fd1`; app-sanitize the same 311 records, report
`455efaa8...caaf`. These are checkpoint results, not final exact-commit suite
evidence.

## Real-window integration findings

The initial macOS executable had no application bundle identity. Desktop
automation could enumerate PID 36338 and window 36052, but could not target the
process. The task-scoped correction makes only the macOS target a CMake app
bundle with identifier `org.unirally.classic`; non-Apple platforms retain the
same executable target and path. `frontend run` now resolves the bundle's inner
executable on Darwin and the existing path elsewhere. A focused Python
regression covers both paths. The built Info.plist reports the intended bundle
identifier, the pack-only hidden smoke passes (`a03a06cc...1cd`), and computer
use then identified PID 38584 by bundle identifier and captured its real
768x700 window.

A small final-state/input diagnostic was added to report mapped key down/up
events, sampled nonzero/simultaneous/neutral updates, focus clearing and the
final native state. It is observational only and does not alter input sampling
or gameplay.

The coordinator sent 30 real Right key presses to the bundled window. The
native scene stayed current and the visible start-line/HUD moved slightly, but
the process failed before a normal diagnostic summary could establish how many
short presses overlapped a PAL update. Therefore this is **not yet** claimed as
live-input acceptance evidence.

## Corrected opponent-first continuation

Both the original bundle-less visible run and the corrected bundled run failed
with `sampling content address is unavailable`. Their frontend reports are
`b069f2d7...28fc` and `cecc061b...2c3`. An independent pack-only
`movement_runner` reproduction supplied neutral masks from semantic frame 1534
onward and binary-searched the first failing prefix:

- frame 3434 is the last completed state; frame 3435 is the first failure;
- player x remains 1088;
- the opponent is already marked finished with stored centiseconds 3358, while
  phase/outcome remain Racing/Pending because the player has not crossed;
- the earlier parsing used byte 152. The canonical opponent begins at byte 144,
  so its actual native frame-3434 state was x=28355, y=990, vx=448. No x wrap
  occurred; the unavailable sample was downstream of missing finish handling.

The exact input, output and stderr artifact hashes are respectively
`32070115...cd9`, `6aa5aa8d...2117` and `37b47acd...d01`. This pins the failure
to canonical simulation rather than SDL scheduling or rendering.

The bounded independent audit is recorded in
[R-0017-opponent-first-audit](R-0017-opponent-first-audit.md), audit commit
`b183486` (integrated task head `29ccf8a`). It established the original
continuation: `$83:EA72-$83:EAC3` neutralizes the finished opponent from frame
3215 and applies signed ten-unit pre-slowdown on the two nonzero phases, while
ordinary horizontal limiting, integration, collision/contact and the player's
timer continue. Freezing, clamping or skipping the rider would be incorrect.

The finish pose is separately source-backed. `$82:8953-$82:89C2` advances
per-rider selector `$11E7` on those same two phases through `$17:C7D6`: entries
0..47 are poses `$0A45-$0A5C`, each duplicated; negative sentinel entry 48
resets the selector and republishes `$0A45`. Persistent `$0DF1` is copied via
`$0F59` before collision. Native serializes this selector in additive
371-byte `URMV0003`; older 333-byte V1 and 369-byte V2 remain readable and V2
offsets are unchanged.

The tracked replay and projection bind the PAL ROM, unchanged bsnes/core
identity, cold-start inputs, original sample/final/WRAM-series identities and a
74,010-byte full projection for frames 1533-3999. Projection SHA-256 is
`77ed349e...febe`. `native opponent-first-check` passes it in two fresh
pack-only native processes and restores at 3214, 3215, 3231, 3234 and 3435
(report
`ee81b5ac46710c61076a926998e523b8fa9195747d95283a099c2d480efca00d`).
Exact boundaries include frame 3215
x/y/vx=`25278/857/415`, x=`25359` from 3231, velocity zero at 3234, pose
`$0A45` at 3435 and `$0A55` at 3999. Player x stays1088, unfinished, and its
timer advances through frame3999.

After correction, all three accepted full-race paths and restores remain exact:
continuous `5dfdf196a44ec47355b621cccce23a4006d3d6d1a8f96005a4f0890b86796179`,
release `9fdd1a4a196b5c4f497a04bdded7bd6fc9d75f0693d3ff525fc35ab8c0d18326`,
reviewer release `070cb4940ebb5f99954cbc18927b059eb3224887964fe5f4b49fa7214a4c783b`.
All seven visual mismatches remain exactly unchanged
(`484df63557974c0190e6507b3b0e61f59d26446d4340982e709f87856c28aca0`).
Serial final app-debug and app-sanitize suites each pass 314/314 (291 Python,
20 CTest, three fresh processes;
`956fb0ab00b3c2c23f47952334b077f3b1785c639fefb87933075e04736e34ee`,
`16b777ada9842590582306ee381df84414c7158e052dfd080715a855acdf7bc9`).
A deliberately concurrent first debug/sanitize invocation caused two debug
tooling failures because both suites mutated the shared `lab-failure-probe`
build; the serial debug rerun is the applicable evidence.

The ROM locator used for the targeted audit was removed again after capture.

## Corrected sustained real-window run

The rebuilt pack-only bundle (`org.unirally.classic`) ran visibly for 4,000 PAL
updates/80.298 seconds and ended normally at semantic frame5533, far beyond the
former 3435 failure. Coordinator computer use captured the current finish-line
scene twice and delivered 120 mapped key-down plus 120 key-up events: 50 Right,
then 30 Right, 20 Z and 20 Up taps. The diagnostic proved one nonzero controller
update, 1,675 subsequent neutral updates, final mask zero and player x1094
(report
`6cf5621cb7ef1c8a276112dc4d06e163949dfd423d2b424b6030bd24317cca5d`).
Thus real keyboard press, mapped sampling, visible response and
release-to-neutral are observed; `--fixed-controller-mask` was not used.

The automation API explicitly rejected a multi-nonmodifier `Right+Z` chord, so
simultaneous input was not practical and is unavailable rather than passed.
Simple Finder/game app switching did not surface an SDL event, so the
coordinator clicked the real window minimize control, observed Finder in the
foreground, then raised the game and captured a current screenshot. That
second finite pack-only run reports one focus loss and zero active clears—as
expected because it carried no active input—and completed 2,000 updates at
frame3533
(`f0fa6ed60bc509e9cb869359ba4ea536eda7d86f8a680660ba251585cd917bc3`).
Active-mask clearing remains covered by the authored input-state regression,
not a live claim. Final hygiene found no tracked ROM, pack, binary image or
locator and `git diff --check` passed. Fresh review and hosted exact-candidate
CI remain pending. This record does not accept M3-04 or M3.
