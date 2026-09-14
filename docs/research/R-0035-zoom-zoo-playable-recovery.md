# R-0035 — Native ZOOM ZOO initialization and playable recovery

Status: **incomplete, unaccepted M4-16 experiment**. The accepted product remains
DRAGSTER; accepted ZOOM ZOO evidence remains M4-15's seeded laboratory domain.
This record consolidates source observations and implementation decisions, not
complete gameplay or presentation acceptance. See [task](../../tasks/M4-16.md)
and [independent review](../../tasks/M4-16-review.md).

## Identity and tested domain

PAL ROM SHA256 `a1105819d48c04d680c8292bbfa9abbce05224f1bc231afd66af43b7e0a1fd4e`;
private audited bsnes core SHA256
`e59bf88d4fc922c9fe3b5438e65ff3a6909d24e1628f0f87141c8de17699a91b`.
One-player MIKE/BRONSEN CRAWLER/ZOOM ZOO, three laps, fresh scenario defaults.
Original pairs cold-start through frame7600; all WRAM/SRAM images and controller
timeline are authenticated before native evaluation. Native starts at end1376
with static content and controllers only. Primary input is inherited from the
M4-15 manifest through6724, then neutral. Experimental overlays are retained in
tracked `tests/manifests/native/zoom-zoo-playable-*.case.json` and freeze files.

`URZZ000A` is730 bytes: historical565 race bytes, fade/start boost/result clock,
eight separately projected original result publication bytes, charge latches,
player announcement/tutorial state, twelve roll words per rider, and25 additional
learned reward weights per rider. Historical accepted URZZ0001/2/3 remain readable;
unaccepted V4–V9 experiments are preserved as evidence, not compatibility promises.
Frame1376–7600 comprises6225 observations and6224 updates.

## Recovered producers and decisions

| Domain | Original source and verified observation | Native decision / remaining limit |
| --- | --- | --- |
| Clean scenario | $82D7C6–D7FA clears runtime; $82D89D–D904 derives positions/cameras from track header; $82DB25–DB7F fills lap/total sentinels; $82DB96–DBBD sets laps and cap448 | Derive from static header and explicit fresh scenario. No end1649 seed. Initial OAM X101 is explicit $82D76D–D76F. |
| Countdown | Fade $0FF1 grows to30; countdown waits until fade5. Start boosts $1261/1263 initialize384; countdown/control ordering clears or consumes them | Preserve original integer ordering at130/100/70 and timer below68. Initial fade draws prior update's value ($80883F–8849). |
| Manual turn | $82A35B–A49E controls A reflection; $82A49F–A5F9 changes L/R rate under A | Tested A, Up, Down and Select overlays complete. Up/Down/Select have no extra gameplay effect in these tested sequences; not a universal inertness claim. |
| Announcements | $829995–9A49 charge latches; $81C598–C5C8 enqueues; $81BEA8–BEF1 idle display; $81C0CE–C18A consumes weights/boost; $81C02A–C054 cooldown; $83CDBC–CE43 tutorial | Native player queue, hints and reached event1/17 reward feedback. Event/class arrays are static. Other compound reward producers remain incomplete. |
| Roll | $829398–9714 X entry, signed step, held/return poses and reflection; $829C98–9CA7 held landing reward | Full X, release/landing and re-press sequences recovered. Bounce charge/active/prior-step continuations remain unsupported and rejected at restore. |
| Roll content | $0080E8 pose table128 bytes; $008168 direction64; $82D7A4 learned weights26; $82DB87–DB94 copies weights | Authenticated static pack entries, never runtime state. $054B/054D mirrors support count ($818E06/$818F5A), not a bounce phase. |
| Camera | Original HDMA frame1382–6724 uses prior camera minus initial origin8944/1232; BG2 shifts wrapped word right once | Match all5343 observed mappings. Initial black frames do not prove visible alignment. |
| Result | $83904A–90F0 publishes graph extrema; $80F88D publishes totals. Primary load6725, visible6833, stable6839 | Archive final race when original WRAM becomes graphics; independently project graph min/max and totals from SRAM. Semantic load counter1–115 is explicitly an abstraction. |
| Restart | Original Start after result advances tour to STUNT, not ZOOM ZOO | Standalone Race Again resets the same clean scenario, including fresh persistent defaults. Full fresh-process restart comparison; no tour-continuation claim. |

The source map is not a complete reached-producer closure. Result audit includes
non-ROM PCs and unresolved reads; zero unresolved stores must not be described
as zero residual accesses. Finish camera/lap/AI domains inherit R-0034 evidence.
Uncertain fields keep provisional names. Native arithmetic retains wrapped words,
signed steps, arithmetic shifts and original per-rider scheduling.

## Reproducible evidence

Private root: `.worktrees/m4-16-playable-zoom-zoo/artifacts/m4-16` relative to
main. `boundary-a/b`, `brake-a/b`, `start-brake-a/b`, `stop-brake-a/b`,
`trick-left-a/b`, `trick-long-a/b`, `ordinary-controls/{a,up,down,x}-a/b`,
`held-controls/{held-x,select,resume-x}-a/b` retain independent fresh originals.
Each reference has its timeline, memory hashes and video identity. Do not commit
these memory files, screenshots, packs or ROMs.

`initialization-audit` covers1207–1650, `result-audit`6725–7200,
`trick-long-audit`1718–1785, `ordinary-controls/a-audit`1681–1740,
`ordinary-controls/x-audit`1690–1760 and both `held-controls/*-audit`1700–1760.
Their `authentication.json` records exact capture commands and6394 authenticated
WRAM frames. Access reports retain residual reads and original hashes.

From the task checkout, repeat the immutable primary candidate gate:

```sh
python3 -m tools.unirally_lab.native.zoom_zoo_playable compare --reference artifacts/m4-16/boundary-a --repeat artifacts/m4-16/boundary-b --contract tests/manifests/native/zoom-zoo-playable-primary-v10.freeze.json --binary build/app-debug/src/core/zoom_zoo_runner --pack local/classic-crawler-two-tracks-v4.pack --out artifacts/m4-16/FRESH-primary-v10.json
```

Use fresh output names and a clean source/binary for the entire gate. Original
recovery uses `zoom_zoo_playable_reference --core ... --case ... --out FRESH`.
The ordinary `freeze` and `compare` commands require both finishes and200 stable
result updates. The re-press original fails that requirement (no player finish
by7600); its separate incomplete inventory is recovery evidence only.

At clean4f8aaad the632-byte primary passed479 restores and full restart;
debug/sanitize each405 checks, all28 historical M4-12–14 differential/restores,
DRAGSTER win/loss/restores/presentation, content and original replay passed.
At cleanedec610 independent full X680-byte gate passed1782 restores/restart.
These are historical candidate-specific passes, not final V10 or M4-16 acceptance.
Candidate9f7f3b4 and later review results are recorded in NEXT_SESSION.
Independent V10 review found a held duration7/rotations6 forged restore that
changed event17 weight after re-press. Correction uses positive duration <=
accumulated rotations before16-bit wrap, not equality: return/new roll retains
prior rotation counts. Elapsed-update bounds reject counters that could not yet
have accumulated. Negative return-phase relationships remain less constrained;
finite restore checks are not a complete reachability proof.

## Product gaps and next experiments

Still required: bounce and compound rewards, Start behavior, wrong-direction
counter boundary, complete producer closure, clean isolated bootstrap/extraction,
wrong-ROM/incomplete-pack/denied-access gates, latest historical M4-15 matrix,
untuned latest variations, representative frozen visual checks, and actual live
complete race/result/restart with independent reviewer input exercise.

Prototype rendering uses original track/background, prior camera, native HUD and
result values. Rider art retains the last recovered pair as in DRAGSTER, but
ZOOM ZOO fallback/anchor/readability still needs quantitative and independent
visual acceptance. Audio is excluded by task scope. Current app exit diagnostics
still print generic movement race status for ZOOM ZOO; its separate result line
is more informative, but diagnostics need correction. Gamepad is untested.

Earlier actual-window CUA taps produced2 down/up pairs but zero nonzero50Hz
updates. The inspected app stayed neutral, never finished/restarted, and its
source changed during that run. `live-inspection.json` says launch passed;
that is not live acceptance. No frozen-mask demonstration may replace live input.
The built-in desktop API cannot hold a key. A private PID-restricted CGEvent
helper is prepared but has never run; explicit permission was requested because
the desktop tool prohibits that fallback without user authorization. No answer
was received at this checkpoint. Do not infer authorization from elapsed time.

Pack v4 has49 entries and is experimental. Existing v2/v3 files at older local
paths are intentionally not overwritten and will be rejected by current code.
The landing-matrix extraction helper is tied to the audited macOS core identity;
clean Linux private extraction has not been established. Hosted synthetic CI
cannot substitute for it. M4 remains incomplete; no milestone tag is due.
