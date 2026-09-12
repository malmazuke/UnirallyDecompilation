# R-0017 — M3 playable-slice acceptance

- Task: [M3-04](../../tasks/M3-04.md)
- Status: checkpoint; acceptance is blocked by the opponent-first live path
- Candidate base: `55fb1d5882f00a0a791a752ec605cc4b5dc6c0e9`
- Tested host: macOS arm64, 13 September 2026
- ROM identity: supported PAL SHA-256 `a1105819...fd4e`
- Classic pack: 25 entries, 154,030 bytes, SHA-256
  `5c1fc5b0...1529`; extraction rules SHA-256 `70712c47...d768`

This record distinguishes accepted component regressions from the incomplete
real-play integration gate. It does not accept M3-04 or M3.

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

## Blocking opponent-first continuation

Both the original bundle-less visible run and the corrected bundled run failed
with `sampling content address is unavailable`. Their frontend reports are
`b069f2d7...28fc` and `cecc061b...2c3`. An independent pack-only
`movement_runner` reproduction supplied neutral masks from semantic frame 1534
onward and binary-searched the first failing prefix:

- frame 3434 is the last completed state; frame 3435 is the first failure;
- player x remains 1088;
- the opponent is already marked finished with stored centiseconds 3358, while
  phase/outcome remain Racing/Pending because the player has not crossed;
- the opponent continues after its finish and has wrapped its 16-bit x to 14;
  the next decoded-track sample is unavailable.

The exact input, output and stderr artifact hashes are respectively
`32070115...cd9`, `6aa5aa8d...2117` and `37b47acd...d01`. This pins the failure
to canonical simulation rather than SDL scheduling or rendering.

It is a verified integration defect in the real-play space but the original
opponent-first behavior is not established. Freezing or skipping the finished
opponent is only a provisional hypothesis and has not been implemented. A
bounded independent consultation/research decision is required before changing
gameplay. Until a correction passes the frozen three-path matrix and fresh live
evidence, the controls, sustained-run, repository-hygiene, independent-review
and hosted exact-candidate gates remain incomplete and M3 acceptance is
blocked.
