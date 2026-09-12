# Race-finish state contract v1 (DRAGSTER complete-race scenario)

Validated by [R-0012](../research/R-0012-complete-race-evidence.md) for the
single-player MIKE-versus-opponent DRAGSTER race on the PAL ROM. Addresses are
work RAM offsets in bank `$7E`; values are sampled at the end of each PAL frame.
Names describe only the observed contract. They do not establish a general
race-mode format or the result-screen record layout.

| Field | Address | Encoding and instances | Writer | Observed contract |
| --- | --- | --- | --- | --- |
| `rider_finished[0]` | `$7E0EFF` | u16; player | `$81:823B`, `STA $0EFF,Y` with `Y=0` | One write of 1: continuous frame 3213; release variation frame 3318. It remains 1 through the race/result transition. |
| `rider_finished[1]` | `$7E0F01` | u16; opponent, stride 2 from player | `$81:823B`, `STA $0EFF,Y` with `Y=2` | One write of 1 at frame 3214 in both scenarios. It remains 1 through the transition. |
| `player_finish_delay` | `$7E0F0F` | u16 frame counter | `$83:E81D`, `INC $0F0F` | Starts on the first frame after the player flag is observed by the post-race dispatcher and increments once per PAL frame for exactly 240 updates: 3214–3453 continuous, 3319–3558 variation. The following frame begins the black result load. |
| post-finish horizontal axes | `$7E0319`, `$7E0325` | u8 player/opponent derived horizontal inputs | `$83:E8F8`, `$83:E908` write 1 after the ordinary input/AI writers | Neutral (1) is forced during the player's finish delay. This is an override after `$82:AB52`/`$82:AAFB`, not a change to the controller image. |

## Frame order and visible phases

The rider update and post-race dispatcher do not give both scenarios the same
within-frame boundary:

- Continuous: the player flag is written late in frame 3213. In frame 3214 the
  dispatcher reads it, increments the delay to 1, then overwrites both derived
  horizontal axes with neutral; the opponent flag is written later in that
  frame. The end-of-frame image first says `FINISH` at 3214.
- Release variation: the opponent flag is written at 3214 while the player flag
  remains zero. The player flag is written late in 3318, so ordinary Right is
  still visible to gameplay in that frame. Frame 3319 first increments the
  delay and applies the neutral overrides, and its image first says `FINISH`.
- Delay value 240 is written on frame 3453 continuous / 3558 variation. Those
  images show `WINNER` / `LOSER`, respectively. The next frames are black and
  start the result-screen load. `DRAGSTER COMPLETE` is visible by 3679 in the
  continuous case and by 3800 in the variation.

The shared race-timer digits at `$7E0E19`–`$7E0E29` continue advancing during
the 240-frame finish display. They are not the stored player time printed on
the results screen: continuous results show `0:33.57`, while the shared digits
reach 0:38.3 plus 4/5; the variation results show `0:35.66`, while the shared
digits continue to 0:40.4 plus 4/5. The per-rider stored-time layout is not yet
identified.

## State-format consequence

M2's 333-byte `URMV0001` state ends at frame 2999 and contains neither finish
flags nor this delay. A native complete-race task must revise the format
explicitly and serialize both rider flags, the delay, any future-affecting
stored finish times/result outcome, and the presentation phase. Appending a
hidden global or reusing the emulator's work RAM would violate the M2 boundary.

This record does not establish ranking rules. The variation visibly says
`LOSER`, but its later `DRAGSTER COMPLETE` screen still decorates MIKE's row;
that icon is not interpreted as proof of placement.
