# M4-16 fixed-scenario persistent input ledger

Status: **independent review evidence for an incomplete, unaccepted M4-16
experiment**. This ledger is limited to a fresh one-player MIKE/BRONSEN
CRAWLER/ZOOM ZOO three-lap scenario and the standalone **Race Again** action.
It does not establish alternate persistent profiles or original tour
continuation.

ROM SHA-256:
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
Audited bsnes core SHA-256:
`e59bf88d4fc922c9fe3b5438e65ff3a6909d24e1628f0f87141c8de17699a91b`.
The underlying private captures are `artifacts/m4-16/initialization-audit`,
`artifacts/m4-16/result-audit` and `artifacts/m4-16/boundary-a/b` in the M4-16
task worktree.

## Fresh scenario inputs

| Original input | Fresh value | Reached use and native boundary |
| --- | ---: | --- |
| `$770748` | `0` | Player identity. It selects MIKE in setup/result presentation and the player voice bank in landing rewards (`$829D21`, `$829D47`). Native supports MIKE only. |
| `$770749` | `17` | Opponent identity. It selects BRONSEN and the opponent voice bank. Native supports BRONSEN only. |
| `$77074A` | `1` | Selected event/track input used by setup and race dispatch, including `$82D97E/$82D98F`, `$83CC2B` and `$82A81A`. Native supports the resulting ZOOM ZOO scenario only. |
| `$77074B` | `1` | Lap-setting/layout selector. `$82DB96` uses it before `$82DBAF/$82DBB2` publish four start-line crossings, meaning three timed laps. It remains a reached runtime and result-layout input. Native fixes this result to three laps. |
| `$770744` | `3` | Speed-cap setting read at `$82DBA6`; `$82DBBA/$82DBBD` publish cap `448`. Native fixes the derived cap. |
| `$770750` | `0` | Mode/player configuration byte reached in setup and ordinary race branches (`$82D781`, `$82D5BE`, `$83CBF4`, `$82B156`, among others). Its broader menu meaning is not claimed; native admits only the observed one-player configuration. |
| `$771116` | `0` | Persistent tutorial/configuration input at `$82D951`, then reached during the race at `$83CEB7`. Native fixes the fresh value and implements the resulting tutorial state. |
| `$77111A` | `0` | Persistent setup input reached at `$83FB8C/$83FB9B` and `$82D978`. Native fixes the fresh value; other profiles remain unsupported. |

These bytes are authenticated inputs, not state produced by the native race
initializer. The initializer hard-codes the declared scenario and reconstructs
their reached consequences. In addition, `$82D89D-D904` consumes the fixed
decompressed track header and publishes player/opponent positions and camera
origins; `$82DB25-DB7F` fills lap slots/totals with `60000`; `$82D844` publishes
countdown `270`; `$82D897/$82D89A` publish boost `384`; `$82DB8B/$82DB8F`
copy static reward weights; and `$82D95C/$82D975` publish tutorial active `1`
and update count `30`.

## Result inputs and publications

The supported native result is derived from the just-completed race archive
plus one fresh-record default:

| Original producer/input | Observed value | Supported meaning |
| --- | ---: | --- |
| Current-race lap arrays `$770755-0768`, `$7707BF-07D2` | three completed lap slots per rider, remaining sentinels | `$83904A-90F0` derives graph bounds; native also derives each current-race best lap from these serialized slots. |
| Prior-record `$770424` | `60000` | Fresh no-record sentinel read by `$839051/$839094`. Native uses this declared fresh default while deriving the graph. Persisted prior records are outside the supported profile. |
| Graph maximum `$771071` | `3288` | Original result publication at frame 6830 (`$83908C`); projected native result byte pair. |
| Graph minimum `$77106F` | `3088` | Original result publication at frame 6830 (`$8390E9`); projected native result byte pair. |
| Totals `$770618/$77061A` | `9802/9810` | `$80F88D-F8AF` publishes the two current-race totals at frame 6831; projected native result byte pairs and winner inputs. |

The eight projected result bytes are therefore graph maximum/minimum and both
published totals. Winner, current-race best laps and the graph presentation do
not require an additional hidden future-state input in this fixed scenario:
they are derived from those publications and the serialized lap archive.

The result loader also reads fixed presentation data. `$770748=0`,
`$770749=17` and `$77074B=1` select MIKE, BRONSEN and the three-lap layout.
Generated code at `$000199` performs three authenticated 16-byte `MVN` copies:
the ROM label block `$83A003-A012`, SRAM MIKE block `$77000C-001B`, and SRAM
BRONSEN block `$77011C-012B`, each to scratch `$00DE-00ED`. Other reached
presentation inputs include `$770551=4112`, `$77106B=1026` and `$7710AD=1`.
Native uses fixed semantic labels/layout rather than claiming original result
graphics equivalence.

## Deliberately discarded persistent output

Original result loading updates `$77082B` from fresh sentinel `59999` to best
lap `3250` at frame 6831. `$771118` also changes during the original transition,
and `$770742` remains original screen/transition control after result loading.
These values belong to persistent record/tour or original presentation flow.
The standalone **Race Again** action deliberately discards them and invokes the
same fixed fresh initializer. Original Start instead advances tour progression
to STUNT and is outside this product action.

For that explicit restart decision, the audit identifies no missing reached
future-state input: fresh-process restart comparisons already require every
represented field to equal a direct fixed-scenario initialization and continue
through a complete second race. This conclusion does not extend to persisted
records, different riders/tracks/lap settings, tutorial profiles, menu state or
tour continuation.

## Remaining evidence limits

The result access capture retains 11,738 unresolved reads before frame 6795,
although none remain from fully visible frame 6839 through 7200 and there are
zero unresolved stores. The inspected reached inputs above close the declared
eight result publications and standalone restart dependency; they do not turn
the aggregate unresolved count into a global producer-closure result. The
remaining reached loading reads would need individual presentation,
persistent-tour or future-state classification before a global closure claim,
and representative frozen visual checks are still required. Exact original
result rendering and alternate persistent defaults remain unsupported.
