# Native input and timer component

This is an isolated M2-01 component, not autonomous movement. It uses the PAL
ROM/core identity in R-0010 and the unchanged frozen primary manifest.
The native functions contain no ROM access, reference lookup or frame schedule.

## Original arithmetic and scope

`$80:87E9–87F2` copies `$4218/$4219` into `$0311/$0313` as bytes. The controller
boundary packs the twelve named buttons into these SNES images. The direction
branches `$82:AB1A–AB59` give Up priority over Down and Left priority over Right;
axis values are0,1,2 for negative, neutral, positive. This decodes the input;
race-start or other subsequent overrides belong to the motion/start contract.
The primary exercises Right, neutral vertical and Up; other button packing and
contradictory directions have authored/static-instruction checks, not additional
original gameplay equivalence claims.

The five timer words at `$0E19,$0E1D,$0E21,$0E25,$0E29` are minutes, tens of
seconds, seconds, tenths and subframe. `$81:C6C5–C75B` increments subframe, carries
at5 into tenths, at10 into seconds, at10 into tens of seconds, at6 into minutes,
and at10 minutes restores9:59.9 while retaining subframe0. The immediate operand
file offsets are0xC6E3,0xC703,0xC718,0xC72D,0xC73F; saturation digits are at
0xC744 and0xC750. The source exposes that saturation event to its caller, which
owns auxiliary sound/display flags. Valid digit ranges prevent integer overflow;
invalid component state is rejected. Serialization is ten explicit little-endian
bytes, independent of C++ layout/padding. This does not inventory the full game's
future-affecting state or establish M2-02 restore acceptance.

## Start-gate experiment

Prediction before capture: the timer begins after the first movement update,
when the countdown passes the original threshold, rather than every native step
from seed1533. Focused capture uses the unchanged primary replay with no altered
expectation:

```
python3 tools/project.py access capture --manifest tests/manifests/native/primary.replay.json --out artifacts/m2-01-coordinator/input-timer/start --from-frame 1533 --to-frame 1540 --watch-address 0x11C5 --watch-address 0x0E2D --watch-address 0x0BF9 --watch-address 0x0E29 --watch-address 0x0E25 --watch-pc 0x81C696 --watch-pc 0x81C6A0 --watch-pc 0x81C6B6 --watch-pc 0x81C6C5 --timeout 120 --report artifacts/m2-01-coordinator/input-timer/start-report.json
```

Root coordinator capture at e6f48f2: exit0, unchanged primary sample digest
72f618f2f7e3416e…,142,923 instructions,71,147 accesses,204 unresolved accesses
and zero unresolved stores. Access SHA-256 starts d4eebdee7f582de4; artifacts stay
ignored. `$0E2D` is0 at1533/1534. `$81:C6A0` reads the post-countdown values69
then68; neither ticks. At1535 it reads67, loads `$0BF9=1` into `$0E2D`, loops
through `$81:C694`, and enters `$81:C6C0`. Subsequent calls keep the latched1.
The first subframe carry is1539. The motion worker independently found the
countdown/brake release producing movement one frame earlier, at1534.

## Component comparison

The probe takes the first five frozen timer digits once, then controller
buttons from the replay inputs and an explicit harness-supplied timer enable
(false1534, true from1535). The latter is the observed gate above; **it is not a
native reconstruction of countdown/start state**. No later expected digit is
fed back. On primary1534–2999, all13,194 compared values (nine fields over1,466
updates) agree. The four required movement fields remain untested here.

```
python3 tools/project.py build --preset lab-debug --report artifacts/input-timer/build-probe.json
python3 -m tools.unirally_lab.native.input_timer_check --probe build/lab-debug/tests/native/input_timer_probe --report artifacts/input-timer/primary.json
```

Native output SHA-256 `61fd6b85b7bfe78e55364866aa344531fdb22371d2a92760415e9bc2b9ab7e0f`;
input SHA-256 `69578b17b7961711cc148da556d567d9a044167bc6cd0bda2103c7d0fae9f157`.
The expected primary manifest is bound byte-for-byte by the independently
reviewed comparison loader. Frozen withheld outputs remain unopened. Authored
C++ checks cover opposing directions, packing, paused tick, all carry levels,
saturation, explicit bytes and malformed serialized state. Independent review,
clean-source final checks and integration are recorded in the task handoff.
