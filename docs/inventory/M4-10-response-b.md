# M4-10 preregistered response-B inventory

Preregistered at claim `087660809f66c4c8d5a2468421ef306b0ff3a7f0`, before
any new M4-10 capture or replay result. The accepted M4-09 composition and its
captures remain frozen comparison foundations.

## Combined watch and writer hypothesis

The additive capture spans end-of-frame 1649 through frame 1700 and retains the
entire accepted M4-09 position/contact watch set. It adds both persistent
response-B words `$0BB7/$0BB9`, their adjacent response-A words
`$0BB3/$0BB5`, scratch `$0F55/$0F57`, rider selectors `$0FF9/$0F51`, phase
words `$0300/$0302`, modulo-32 counter `$04C7`, contact counter words
`$0DE7/$0DE9`, and the orientation/pose scratch and persistent words reached by
the suspected producer and consumer. Address watches record every actual writer
PC, including writers outside the suspected routine.

Every byte address in the inclusive producer range `$82:A49F--A5F9` is supplied
as a PC watch, so every reached instruction start is retained without assuming
an instruction boundary before decoding the authenticated ROM. Every byte in
the pose range `$83:EF54--F0FA` is watched likewise. Caller landmarks retain the
motion load/publication, pose consumption, sampling/contact entry, contact
response output and caller publication order for both riders.

Instruction-derived hypotheses to reject or confirm are:

1. rider scratch is loaded from `$0BB7,Y`, with `Y=0/2`, before the producer;
2. inactive phases preserve the persistent word, while reached active paths can
   clear it with a 16-bit store or replace only its low byte while preserving
   the previous high byte;
3. `$0F57` is consumed during pose processing before the same rider's contact;
4. contact output publication is not blindly the next contact input because an
   intervening motion producer may clear or replace the persistent value; and
5. the observed opponent `254` output at frame 1661 to zero input at frame 1662
   is explained by an ordered, watched writer rather than an inferred zero.

Exact reached branches, widths, guards, input inventory, writer counts and the
meaning of active/inactive phase are new observations, not preregistered
results. Later captured response-B values will be comparison targets only; the
recurrence must seed each rider once at end-1649 and execute every reached
producer in order.

## Worker variation

The only primary-event change is releasing Right at frame 1668 and restoring it
at 1669. Predicted before execution: exact primary evidence through frame 1667,
and the controller differs at frame 1668 only. Producer/contact relevance and
any reconvergence are deliberately not predicted. The initial replay digest
fields are zero placeholders, so the first replay comparison must report those
expectations as failures while two fresh runs can still establish mutual
determinism.

## Identity and boundary

The supported PAL ROM SHA-256 is
`a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`.
The pinned core is `7d5aa1e656b9171524d01b1b22917197d8121cb4` with patch
`a719f5ffe2222dad4c1ab04336633319ad85004f74e32fc14893a058be333885`.
Velocity, pose and contact fields other than response B remain captured external
inputs. This experiment cannot establish autonomous ZOOM ZOO gameplay.
