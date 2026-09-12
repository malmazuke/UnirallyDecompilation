# M3-04 bounded opponent-first audit

13 September 2026; OpenAI GPT-6 Astra/high, independent audit at `afacc49` in
`.worktrees/m3-04-astra-audit`. Scope: one blocking continuation question, no
production change or acceptance. Parent supplied the current-run quota override
and retained the weekly reserve; no additional child, purchase or reset.

## Finding and recommendation

The original independently neutralizes and slows the finished opponent on the
update following its finish. Ordinary movement, collision sampling/contact and
finish animation continue. The player remains unfinished and its race timer
continues; no player finish delay starts. Implement this per-rider response
separately from the player-owned global delay. Freezing/removing the opponent,
clamping sampling addresses, or ending the player's race would contradict this
experiment.

The acceptance checkpoint's claim that opponent x wraps to14 is incorrect.
The canonical rider record is128 bytes; opponent x begins at byte144, after
the16-byte header/input prefix and rider0. At native frame3434 it is28355,
y990, velocity448. The sampling failure is downstream of continuing past the
finish without the original opponent response; a16-bit x wrap is not observed.

Continuous-right acceptance may still demonstrate its narrow declared input,
but it cannot excuse this known failure of releasing a control or leaving the
window idle. Recover this bounded behavior before real-play acceptance. If
other unsupported domains remain, a recoverable application stop/restart is a
containment decision that must be labelled separately from Classic equivalence.

## Frozen experiment and identity

Before execution, ignored `artifacts/m3-04-audit/neutral-reference.json` was
written and hashed:
`3962c6e6481e7f33e7ca6844ebdb72dc7d772e451f5f408219f16cca78321c04`.
It uses the accepted continuous-right cold-start menu, Right1500–1533, then
neutral1534–3999, no Up, empty port1,4000 frames sampled every frame. The menu
Start intervals are300–305,620–625,750–755,900–905,1050–1055,1200–1205.
Fields are WRAM hash, registers, position range `$0415` length12, velocity range
`$04BB` length4, finish flags `$0EFF` length4 and player delay `$0F0F` length2.
Expected digests were empty before both runs; the later result is observational,
not a regenerated accepted expectation.

ROM SHA-256:
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
Unchanged bsnes commit `7d5aa1e656b9171524d01b1b22917197d8121cb4`,
patch `a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`,
library `e24fd249295358319f022519daba37569bfb7ef3fa25da578cd6d19fdd29efa8`.
Both fresh cold-start processes report PAL and have sample digest
`6ef702112e824ad684b44b4b13390843fdb5c67a9e761e5566911eb0a41b9223`
and final state digest
`2d3d727a1ff8069ef6986c234bc5ecc9f457d4285f8c2ee9139c77b7c88e57af`.

```sh
python3 tools/project.py doctor --report artifacts/m3-04-audit/doctor.json
python3 tools/project.py build --preset lab-debug --report artifacts/m3-04-audit/build.json
python3 tools/project.py access capture --manifest artifacts/m3-04-audit/neutral-reference.json --out artifacts/m3-04-audit/reference --from-frame 3200 --to-frame 3500 --wram-series-range 0x300 0xe20 --watch-address 0x7e0417 --watch-address 0x7e04bd --watch-address 0x7e0f01 --watch-address 0x7e0f0f --timeout 180 --report artifacts/m3-04-audit/reference-report.json
python3 tools/project.py replay run --manifest artifacts/m3-04-audit/neutral-reference.json --artifacts artifacts/m3-04-audit/reference-repeat --timeout 120 --report artifacts/m3-04-audit/repeat-report.json
```

All four commands pass; access capture19.579s, repeat10.952s. Access capture
derives5,461,002 instructions and2,704,868 accesses, no ring overflow,
6,989 unresolved accesses but zero unresolved stores and zero resolution
conflicts. Ignored access SHA-256
`138cb5cad615415089665df42daf57995f58380a9e0bd669619422452ac6319c`;
WRAM series SHA-256
`0edec35d1e7137fa7ee5e6f212a32a829ef709300f47ba37fb7b04c5357a8c4b`.
Series start768, stride3616 bytes, frames0–3999; read16-bit fields little-endian.

## Observations and source boundaries

| Frame | Opponent x | y | velocity x | pose `$0413` | opponent finished |
| --- | --- | --- | --- | --- | --- |
|3214|25265|864|450|2133|1|
|3215|25278|857|415|2629|1|
|3220|25329|857|260|2630|1|
|3227|25358|857|35|2633|1|
|3228|25358|857|9|2633|1|
|3231|25359|857|5|2634|1|
|3234|25359|857|0|2635|1|
|3435|25359|857|0|2629|1|
|3999|25359|857|0|2645|1|

Player x stays1088, `$0EFF` and `$0F0F` stay0 throughout this continuation.
Opponent x last changes at3231 and velocity first reaches0 at3234. Timer
digits continue from0:33.6 at3214 to0:49.3 at3999.3358 is the opponent's stored
centisecond result, not its finish frame (which is3214).

- `$81:823B` sets opponent `$0F01` at3214. `$83:EA72` tests that flag on
  subsequent updates. `$83:EA8A` writes opponent horizontal axis `$031B=1`
  from3215 onward; `$83:EA8F/$EA92/$EA95` clear `$032B/$032F/$0333`, and
  `$83:EA9A` writes `$0327=1`. This is a rider-specific input override.
- `$83:EA9F–EAA7` selects the pre-slowdown using bit0 of `$0304`.
  `$83:EAAA–EAC3` moves signed opponent velocity toward zero by10, preserving
  the established negative-10 asymmetry. It executes191 of286 post-finish
  captured updates. At3215 EAC3 writes440, then `$82:9388` writes415; at3216
  no pre-slowdown writer executes and9388 writes390; at3217 it writes380 then355.
- Position integration `$82:92A7` and contact writeback `$81:8F6B` still
  write opponent x at3435. Vertical writers `$82:92A2` and `$81:8F70` remain
  active. Thus stationary final position is not a skipped-rider shortcut.
- Pose `$0413` is written by `$82:931C` and `$83:CD94`; the finish branch
  `$83:EBA3–EC13` updates the animation selector/countdown (`$0F05/$0F09`)
  and pointer `$11FD`. Its pose cycle and the immediate y864→857 change
  must be included in recovery: changing only speed is not yet a demonstrated
  exact continuation. The later `$83:EBCB–EBDA` branch depends on SRAM mode
  bit `$77:0750 &4`; it did not finish the player in this experiment. Do not
  generalize the one-mode result into a universal endless wait contract.

## Native reproduction and required follow-up

The newly built `build/lab-debug/src/core/movement_runner` was run with
`--content-pack` pointing to the accepted worker's ignored
`local/classic-crawler-dragster.pack`,
`--start-state classic.crawler.dragster.race-start.v1`, and `--inputs` pointing
to its `artifacts/m3-04/no-input-first-failure.txt` (neutral1534–3435).
It exits1 with `sampling content address is unavailable`, last complete3434.
Output hash `6aa5aa8db6383f8c080655f16f3ac9f80937a0776563861429ba0b390de02117`;
stderr hash `37b47acdaf8812df1e6bdd7bf304a9a705ba31d6364a76afdce7dfde46ebcd01`.
The opponent x/y/velocity triple agrees with the reference through3214; its
first mismatch is3215: native `(25279,864,450)`, original `(25278,857,415)`.

The smallest new contract is per-rider next-update input suppression, signed
slowdown cadence and finish-pose/contact continuation, while global timer/delay
remain player-owned. Existing `finish_delay` conditionals in `update_movement`
are too broad as the sole trigger. Do not blindly replace every conditional
with a finish flag: original accepted player-first paths also suppress the
unfinished opponent globally, and timing/order must retain their expectations.

Freeze additive opponent x/y/velocity/pose and player timer/finish/delay rows
from this run before implementation. Differential-check through3999, restore
before/at/after3214,3234 and3435, and add a delayed-player resume crossing as an
independent input. Preserve all three accepted full-race and restore matrices,
presentation limits and ROM-free/sanitizer tests. No full suite was run in this
audit because no implementation changed. The pose-control details, delayed
player crossing and sustained visible input remain follow-up work, not passes.

Audit handoff commit: the commit containing this record; parent may cherry-pick
it. All ROM/content/sample artifacts remain ignored in the audit worktree.
