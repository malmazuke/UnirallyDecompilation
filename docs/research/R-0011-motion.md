# R-0011 motion — opponent input, pose and integration

Work in progress, M2-01A motion subassignment; no autonomous gameplay claim.
ROM and core identity unchanged from R-0010. Base `ba71142a6d766216772360949dd8c04760fa9ffe`.

## Preregistered experiment (before new captures)

Primary window 1576–1618. Prediction: AI reads the opponent's previous marker
`$0FC7` before motion; its bit 0x2000 causes `$0333=1`. On the opponent's active
phase the copied input `$0F1F` arms `$0F91`, later starts `$0F93`; vertical
velocity then precedes displacement, pose evaluation and collision.
The original reads `$054D` and may change AI continuation once its contact
counter reaches four. This is a hypothesis to test against ordered watches.

Variation: release only player Right at 1576–1584 and resume at 1585; see
`tests/manifests/native/contact-research/motion/release-before-jump.json`.
Prediction: player throttle changes immediately, but the first opponent trigger
at 1578 remains because its previous spatial marker does not directly use player
input. Later opponent speed may change through relative-progress adjustment.
We will compare original-derived trigger timing and inputs, not native outputs.
The two M2-01 withheld movement series remain sealed.

## Checkpoint 1: verified findings

The first primary and variation captures both match 1,548 isolated pose/jump
output values: 86 pose calls and 43 eligible jump calls each. Models in
`motion_research/contracts.py` use captured arguments; they are **not native
movement**. Primary access SHA-256 starts `9ce872c2a9294ca9`, variation
`f4e2910bc2189b89`. The input variation preserves the 1578 jump trigger.

### Ordering and persistent mappings

The frame updates phase `$0302 = u8(1-phase)` and `$0300=(phase+1)&1`, and
`$04C7=(counter+1)&31`, at `$83:CCB8–CCED`. Opponent active motion phase is
`$0302==0`, player active phase is1; gravity/integration/pose still run every
frame. These are persistent counters, not absolute frame-number tests.
AI runs before both riders. Player motion copies its fields into shared scratch,
updates/publishes them; opponent does likewise. The original positions before
collision and the newly selected pose then feed the sampling/contact routines.

`$83:ED77` creates pose `$0FA1`, published to `$0FF3/$0FF5`. Main loop
`$83:CD8B–CD94` copies these to `$0411/$0413` immediately before contact
`$81:8CF4`. Motion's incoming `$0F85` is the previous pose; contact reloads the
new pose. Confusing these phases breaks the causal loop.

| Working field | Player / opponent persistent storage | Contract |
| --- | --- | --- |
| `$0F91` | `$0D39/$0D3B` | u16 pending jump latch |
| `$0F93` | `$04C3/$04C5` | u16 held-jump impulse phase 0..8 |
| `$0F95` | `$0BDB/$0BDD` | u16 baseline added to negative vertical impulse |
| `$0FA5` | `$0BE3/$0BE5` | u16 previous active-phase jump input |
| `$0FA9/$0FAB` | `$04BB/$04BD`, `$04BF/$04C1` | signed horizontal/vertical velocities, 1/32 coordinate units |
| `$0F53` | `$04CB/$04CD` | u16 orientation on a 64-step circle |
| `$0F55/$0F57` | `$0BB3/$0BB5`, `$0BB7/$0BB9` | contact/controlled orientation increments |
| `$0F81` | `$0DE9/$0DEB` | reflected combined orientation modulo64 |
| `$0FAD` | `$0D35/$0D37` | signed transient orientation impulse from contact; arithmetic half added before damping toward zero on even `$04C7` |
| `$0F8D` | `$0B62/$0B64` | animation phase modulo24 |
| `$0F99` | `$0B6A/$0B6C` | signed animation phase increment; decays toward0 every fourth counter step when jump/trick state preserves it |
| `$0F9B/$0F9D` | `$0B5A/$0B5C`, `$0B5E/$0B60` | previous pre-contact x/y, saved by pose update |
| `$0F9F` | `$0B66/$0B68` | signed displacement remainder after division by3 |
| `$0FA3` | `$0B76/$0B78` | cached target orientation from static table |
| `$0F73` | `$0BBB/$0BBD` | absolute displacement magnitude, recomputed from position except held-jump/trick path preserves incoming value |
| `$0F65` | `$0D41/$0D43` | previous brake input used to release stored throttle at GO |

All table/index arithmetic is integer. Pose target table is ROM `$00:8008`
(file offset8). Displacement helper `$81:B764` uses the two words indexed by
`2*(abs(dx)&255)` and `2*(abs(dy)&255)` in `$17:DD74`; abs(dy)<3 is treated0
before lookup. It computes floor sqrt of their u16 sum. The first128 entries
are squares, but the rest are reflected; a naive universal `dx*dx+dy*dy` is
not the recovered contract. The ignored original table is read only after ROM
identity verification. Signed distance is negative when oldX-newX<0. The
accumulator adds it modulo65536, divides abs(sum) by3, applies the sum's sign
to quotient and **dx's sign** to remainder. The remainder is future-affecting.

### First jump and contact-dependent rotation

AI reads previous opponent marker `$0FC7` bit0x2000 at `$83:E114`; this asserts
`$0333=1` atE122. Without that bit it copies `$0300` atE21F. The phase copy is
zero on the opponent's active phase, so it does not create repeated jumps.
When the asserted input reaches `$0F1F`, the first active update arms latch1
at1578. At1580 it clears that latch and starts held-impulse phase1; it increments
on1582,...,1596. Phases1..4 cap signed vertical velocity at baseline-144;
phases5..8 cap at baseline-192. Phase9 clears to0 without applying an impulse.
Contact counter is separate: it first increments at1580, reaches9 at1588,
and clears on recontact1617 (contact worker's contract).

At1584 AI sees prior contact counter4. It initializes `$0C6F=abs(vy)>>1=53`,
sets `$0C75=1`, and asserts `$032F`. While marker bit persists and `$0C6F!=0`,
`$0C75` selects repeated synthesized trick inputs. `$82:A49F` allows the
orientation increment only when contact counter>=9 or abs(track angle)>=30,
with other mode gates. At1590 `$82:A50D` stores 2 in `$0F57`; the active-phase
updates retain this through1612. These inputs therefore affect collision pose;
an always-accelerating/no-trick opponent is insufficient.

### GO transition and exact seed boundary

End1533 has countdown `$11C5=69`, prior brake `$0D41/$0D43=1`, throttle432,
speed0, x1088 and signed horizontal residues `$0401=-1/$0403=0`.
The countdown handler entered frame1533 at70; `$83:E6ED` compares70 and the
E759 path forces brake `$0325/$0327=1`, before decrementing countdown to69.
Frame1534 enters69, takes the below70 path and no longer forces the brakes.
`$82:99F1` sees the prior brake1 and current brake0. The ordinary acceleration
already added24 to speed; `$82:99FC` adds stored throttle432, yielding456,
then clears throttle and sets `$11F1=256`. `$82:9A4F` saves current brake0.
This is a recovered transition from1533, not a special frame1534 constant.
The x integrator adds speed to signed residual (-1+456=455), produces quotient14
and residual7 (opponent starts residue0, quotient14/residue8). Contact may
correct y after gravity and velocity integration; this is documented separately.

### Failed checks and next experiment

The first all-primary pose probe reports eight orientation mismatches at1535
because the capture omitted the in-frame producer of `$0E7B`, and later
`$0FE3` comparisons used stale seed values because that scratch address was
also unwatched. No formula or expected result was changed to hide them.
A new capture adds these and integration residual/control watches, covering
1533–2999. It will test whether the missing call inputs alone explain them.
AI, throttle/speed and other active-phase producers remain to be independently
contract-tested. This checkpoint does not claim full state closure.

## Final recovered domain and implementation contract

All motion/pose functions in `motion_research/contracts.py` are small isolated
arithmetic models. Their address dictionaries are deliberately confined to
research call arguments; they are not the proposed native state representation,
a CPU interpreter, or an autonomous runner. Unsupported AI modes, failed or
combined stunts, wall rotation tracking, moving-brake behavior and leftward
throttle reject explicitly. The primary and preregistered release variation
stay inside these guards. No RNG read occurs in their executed AI branch.

The final primary probe matches **231,780 values**, covering frames1533–2999:
2,934 calls each to common reset, throttle, pose, gravity, integration and
rolling-mode selection; 1,467 each to active-phase wheel override, jump,
rotation input and quarter tracking; 1,466 AI calls (1533 still has countdown
input overrides), plus1,467 queue updates. The variation matches **26,538 values**
over1533–1700 and preserves the original first jump at1578. The expanded
variation window includes the reward and later AI suppression. Both derive
expectations solely from their original executions, never native output.
The first full probe's missing-watch failures disappeared when the newly
captured inputs were supplied; no pose arithmetic or expectation was changed.

### Ordinary update functions and units

- `$81:8592–8704`: common reset clears transient controls before each rider.
  In this domain all alternate mode/timer predicates are zero; the model rejects
  nonzero unsupported predicates. Its retained mutable inputs are the rider's
  phase-independent state, not the previous rider's scratch. `$81870F/$818718`
  additionally decrement both global reward-message cooldowns if nonzero.
  Because common reset runs for each rider, each global cooldown gets **two
  decrements per game frame**, a causally relevant original behavior.
- `$82:A069–A0B6`: on active phases, if unsupported count>=2 or all four current/
  previous displacement samples are<2, nonneutral horizontal input supplies an
  animation increment: -2 for Right, +2 for Left, negated when reflected.
  The common reset clears this override before every frame.
- `$82:98CF–9A52`: with unsupported count>=2, extreme surface angles±31 or the
  excluded mode `$0F5D`, throttle clears and no acceleration is applied. On
  ordinary Right, horizontal velocity adds24 (or the established override
  `$0F3B`), throttle adds16 only if the candidate is strictly less than
  `max(boost,0)+base+launch_override`. Neutral clears throttle. The launch branch
  and prior-brake publication are described above. Before moving, a persistent
  small-motion counter `$0C77/$0C79` saturates at4 and overrides animation rate;
  it is already4 in the1533 seed.
- `$82:A96F–A9B2`: unless an observed zero inhibit is set or signed vy>=512,
  gravity adds19 when vy<0, otherwise `19-(vy>>5)`, wrapping16bits. It separately
  adds1 to y. `$82:A627–A6F7` then integrates **after** the speed clamp: add each
  velocity to its signed /32 residue, divide absolute magnitude by32, restore
  the total's sign to quotient/remainder, update position and save residue.
  X is then ANDed with the track wrap mask `$0D4F`; y wraps16bits. The extra
  sloped-contact y adjustment has a zero surface-angle predicate in this domain.
- `$82:A288–A2DA`: rolling animation selection uses orientation>=45 and
  displacement thresholds16 for entering and14 for remaining, reflection and
  horizontal-velocity sign; unsupported count9 or active excluded mode clears
  it. The exact branch preserves an existing zero when the enter threshold is
  missed. Its persistent flag is `$0EA3/$0EA5`, the level counter is
  `$0B9F/$0BA1`, and alternate animation phase is `$0FE5/$0FE7`.
- `$83:EF54–F0FA`: target orientation comes from signed speed>>5 (or the bounded
  rolling-mode branch), clamped[-31,31], mapped through `$00:8008`. Contact
  increments and the 64-step shortest-path rule update persistent orientation;
  high displacement>=16 allows up to three steps. Contact's transient impulse
  contributes arithmetic-half **before** its even-counter decay and reflection.
  `$83:ED7B–EF53` then updates the modulo24 wheel phase, displacement history,
  signed remainder, cached pre-contact x/y, and final pose index.
- `$82:A237` only clears `$0F97` in this domain; `$82:A027` sees the unchanged
  positive field `$11F7=48` and returns. `$82:A35B` takes no state-changing
  turnaround branch. `$82:A0B7` clears dormant idle-animation fields
  `$0F75/$0F77/$0F79/$0F7B/$0F35/$0F7D/$0F7F`, all alreadyzero here. These
  observations support explicit native zero-domain guards, not a universal
  claim that the routines are unnecessary. The speed clamp/decay is independently
  recovered by the coordinator's speed research, not duplicated here.

### Quarter tracking, queue latency and reward feedback

`$82:9A53` runs on the rider's active phase before the new rotation input. At
unsupported count2, it saves the quadrant of `(orientation - signed8(rotation))
&63`, remembers reflection, initializes the tracker and clears both directions'
quarter/full-turn counts. Subsequent quadrant changes advance the corresponding
quarter count, clear the opposite partial count, and promote four quarters to
one full turn. Landing finalizes: **three partial quarters round up to a turn**.
The first opponent jump reaches three forward quarters by1616; on the first
active update after contact,1618, the reflected orientation classifies it as
reward event1. The model obtains that event from quarter state, not from frame
number or a replayed event list.

| Persistent tracker field | Player / opponent | Width |
| --- | --- | --- |
| previous quadrant (`$0F67`) | `$0D25/$0D27` | u16 |
| initialized | `$136B/$136D` | u16 |
| reflection at start | `$033F/$0341` | u16 |
| forward turns / quarters | `$1203/$1205`, `$120B/$120D` | u16 |
| reverse turns / quarters | `$1207/$1209`, `$120F/$1211` | u16 |
| opponent queue contents | `$0CEB–0D0A` | 32 bytes |
| opponent queue read / write cursor | `$0D11/$0D13` | u8 (accessed as zero-extended words in enqueue) |
| opponent cooldown | `$0CA7` | u16 |
| horizontal / vertical reward boost | `$11DB/$11E1` | u16 |
| learned event1 weight | `$7E:2102` | u8 |
| accumulated feature total | `$77:0825` cartridge RAM | u16 |

At1618 `$82:9CF8` enqueues event1 into slot1, advancing write cursor1→2.
Read cursor is0, cooldown2 after the common ticks. At1619 the two ticks clear
cooldown and `$81:C219` advances read cursor0→1. Its classification byte at
ROM`$81:C50A` is0 and the reward word at`$81:C493` is128; the consumer adds
that word to both boosts atC2A2/C2AD. The value128 is a static table read, not a
fitted velocity increment. Event1 weight4 is added to cartridge total0→4 and
halved to2. Cooldown is set to `max(5,40-4*remaining_queue_entries)`, here40.
When no event exists, the opponent path resets cooldown10. The queue probe
persists its contents, cursors, cooldown, weight and feature total from **one
seed**, while boost values at the consumer boundary are isolated captured
arguments because speed decay belongs to the separate contract.

The nonzero feature total matters again: at subsequent0x2000 markers, AI checks
player-progress minus opponent-progress against3. Below3 it replaces asserted
jump with `$0300`, zero on the opponent's active phase. The first AI-only model
that incorrectly held this cartridge total at0 failed from1648. Propagating the
observed reward transition yields full-primary AI agreement. Thus SRAM-derived
future state cannot be omitted as mere saved progress.

Only reward event1 occurs in this gameplay window. The single reflected turn
selects combination score25; ROM`$82:9DB6+25` is0xFE, so no extra combination
message is enqueued. Other event combinations remain unsupported in native
scope; the queue model does not establish their gameplay behavior.

### Seed provenance and state design

A separate fresh original process, using an empty private save directory,
reproduces all1533 seed WRAM bytes against the primary reference hash
`f87f42ddfcdae3010bef8da6823216664f655cb5fcdb54af8b7bbd7876605fdf`.
Existing adapter methods `wram()` and `cartridge_ram()` capture the actual
128KiB WRAM and8KiB SRAM; no adapter patch is needed. Cartridge SHA-256 is
`774410886d8e20e123924251c49230fb94a3bfb51438497ea070ba3421b889eb`.
It directly confirms feature total0 and event1 weight4 at1533. Queue seed is
read0/write1/cooldown2, with no pending event. Prior inference from the later
first read is superseded by this direct seed capture.

The proposed native state has one `ContactMotion` record holding x/y, velocities,
displacement, response A/B and orientation impulse, shared with the contact
component, and embeds `RiderContactState`. Add named jump state, fractional
residues, throttle/prior brake, pose/animation state, displacement history,
quarter-turn progress and speed modifiers. Do not duplicate these as a second
contact or speed shadow state. Shared state holds both phase bytes, modulo32
animation counter, modulo256 boost-decay counter, countdown and timer gate,
timer digits, opponent AI continuation/feature state and its queue/cooldown.
Static tables are content, excluded-mode fields are checked seed/domain guards,
and overwritten work registers remain local temporaries. This separates the
future-affecting inventory from an indiscriminate WRAM dump.

The native frame ordering must be: global counters/decoded input → AI/countdown
input gates → player common/active/every-frame motion and publication → opponent
common/active/every-frame motion and publication → timer and reward queue → new
pose publication → both collision/sample/contact updates. Marker progress uses
its previously recovered active-phase ordering. Dynamic outputs from contact
feed the next frame; captured function arguments in these probes must never
become runtime per-frame inputs.
