# Speed clamp and boost decay

Coordinator research, work in progress; no native movement claim. Assigned
`$82:A6F8–A8C8`, base2d26b1e, separate from motion's reward/AI investigation.

Before capture: predict that a per-rider boost and progress-derived adjustment
combine before clamping horizontal speed; the boost then decays according to a
counter mask, so evaluating its decay before the cap would give a different
result. The GO override bypasses the progress adjustment but does not skip all
boost processing. Recover predicate/width/order from original instructions,
then compare isolated calculations using captured arguments. No frozen withheld
series may be read, no per-frame oracle may enter the eventual native runtime.

Regenerate primary evidence with `python3 -m tools.unirally_lab.native.speed_research.capture`.

## Reproduced result and precise domain

ROM SHA-256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`,
bsnes `7d5aa1e656b9171524d01b1b22917197d8121cb4`, patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`; unchanged primary
sample/final-state digests. Fresh capture:27,090,754 instructions,13,466,478
accesses,28,223 unresolved accesses, zero unresolved stores. Access SHA-256
`960c62cb6058694e27021ebd4ea1b409af2138ee1fbc09cff6c38e2a21c3f111`; WRAM series
`c4bc26d6a166cb1e23195f4cf9059a76f2e82667025e172c6a7b6e4002763c46`.

`python3 -m tools.unirally_lab.native.speed_research.probe` reproduces all14,660
outputs (five state words,2,932 calls over1534–2999) and1,466 counter recurrences.
The model matched on its first comparison; no fitting or expected-output change.
All calls use skip/drag flags0, cartridge mode0, friction flag2, base cap448,
adjustment limit96, AI mode1 and AI adjustment0. GO override256 occurs in the
first player and opponent calls only. Direction/pose byte ranges43–104. The
model's other arithmetic branches have authored checks only; alternate cartridge
vertical-cap modes2/42 are explicitly unsupported. These are isolated calls
using captured inputs, not independent game evolution.

## State and order for native implementation

| Concept | Original location / caller mapping | Contract |
| --- | --- | --- |
| Horizontal/vertical velocity | scratch`$0FA9/$0FAB`; persistent player`$04BB/$04BF`, opponent`$04BD/$04C1` | Signed16-bit bit patterns, clamped here before position integration |
| Speed boost | scratch`$11D7`, loaded from`$11D9`/`$11DB` at`$82:8BB5/8EC4`; published`$82:8D07/91EF` | u16 state; reward generation is motion's separate contract |
| Vertical boost | scratch`$11DD`, loaded`$11DF`/`$11E1`, published`$82:8D0D/91F5` | Decrements if wrapped result is nonnegative; ordinary-mode vertical cap does not read it |
| Progress adjustment | `$0343`/`$0345` | Persistent u16; player increments while behind, decrements while ahead; opponent's AI-mode branch bypasses it |
| Start override | scratch`$11F1` from`$11F3`/`$11F5` | Nonzero selects fixed extra80, bypassing progress update and boost contribution to that extra |
| Base cap | **`$11D3` for both riders** | Do not substitute opponent scratch`$11D1`; primary value448 |
| Progress | `$0FCD/$0FCF` | Published transition counts from the existing progress contract |
| Update counter | `$127F` low byte | `$83:CCDE–CCE4` increments modulo256 once before both calls; seed1533 value205, first update206 |
| Contact phase | `$0300` low byte | Adjacent`$83:CCE7–CCED` increments and AND1; separate from progress phase`$0302` |

The capture checks every counter old/read/new relation and both consumers'
identical current value. High byte is untouched by the8-bit store and zero in
this domain. Native state should use an explicit byte and document that bound.

## Arithmetic, directly from instructions

Use unsigned16-bit words, `u16(x)=x&65535`, and test bit15 for original BMI/BPL.
Do not replace subtraction-sign branches with unbounded integer comparisons.

1. `$82:A6FD–A76F`: skip flag returns immediately. Drag flag moves horizontal
   word toward zero by3 (wrapped), then attempts boost−16. Otherwise the selected
   pose byte only decides whether to attempt boost−16; **it does not change
   horizontal velocity**. Its DEC/INC of accumulator is discarded by the next
   LDA11D7. Store a boost subtraction only if its wrapped result is nonnegative.
2. `$82:A772–A7F5`: nonzero start override chooses extra80. Otherwise, opponent
   in AI mode uses twice`$1283` only when player−opponent progress is positive;
   its primary `$1283=0` contributes zero. Other calls compute other−self modulo
   65536. When positive, increment adjustment only while candidate−limit has
   its sign bit set (limit96 therefore permits95); when zero, keep it. When
   negative, decrement only if candidate is nonnegative, otherwise contribute0.
   Add boost and contribution modulo65536, turn negative into0, cap positive384.
3. `$82:A7F8–A81A`: horizontal cap is `u16((extra>>1)+base_cap)`. Positive and
   negative velocities use the original subtraction-sign predicates against
   positive or two's-complement negative cap. In this tested range this is a
   symmetric clamp; the model retains the precise wrapped expressions.
4. `$82:A81A–A872`: cartridge mode0 uses vertical cap `(extra>>1)+768` with the
   same signed-word predicates. Then vertical boost decrements if its wrapped
   candidate is nonnegative. Modes2/42 take another original branch not validated
   here and must not silently fall through to the ordinary formula.
5. `$82:A875–A8A4`: bucket=`min(extra>>4,8)`; read a byte mask from ROM file
   `0x051B+bucket` and a word decrement from `0x0524+2*bucket`. Only when
   `counter&mask==mask`, subtract decrement from boost if the wrapped result is
   nonnegative. This happens **after** this call's speed cap, so changing the
   order affects the velocity at a boost decay boundary.
6. `$82:A8A7–A8C8`: friction flag1 moves velocity by1 but rejects crossing the
   original sign boundary. Notably, negative−1 remains−1; positive1 becomes0.
   Primary flag2 bypasses this. Authored tests preserve that instruction-derived
   asymmetry without claiming it occurs in the primary run.

The9 mask bytes hash to
`0ca19a78da56137e0926c4ba602d8041648a422b9cf5d0a7c3de4a30998cf58b`, the18 decrement
bytes to `c1fab1d9aa1e691d34c1a78e8658cfd52b8334cc5bdec8efb23bedc672988068`.
These are static original content, read from the identified ROM in the research
probe and kept out of tracked files. A native runner must extract/validate them
once through its content boundary; it must not replay per-call observed reads.

Immediate constants80/384/768/16/8 are derived from operands at file offsets
0x1277A/0x127F1/0x12830/0x1276B/0x1287C respectively. The model is a small semantic
state/context transform, not a register interpreter. The captured-argument
snapshot helper belongs only to research and must not be linked into native
movement.

Eight authored tests cover cap-before-decay, counter masks and underflow,
progress-before-cap, exclusive limit, wrapped progress differences, GO override,
fast decay, negative friction boundary, skip and unsupported cartridge modes.
No frozen withheld movement output was opened. Independent review and clean
suite results are recorded in the task handoff.
