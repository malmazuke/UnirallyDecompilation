# R-0018 — M4 original-game feature coverage inventory

- Task: [M4-00](../../tasks/M4-00.md)
- Baseline: accepted M3 tag `m3`, commit `09ce40e`
- Evidence date: 13 September 2026
- ROM identity: supported PAL SHA-256 `a1105819...fd4e`

This is an inventory of tracked evidence, not a catalogue inferred from outside
knowledge of the game. It deliberately distinguishes four levels:

- **Native accepted:** inside the reviewed M3 domain and its frozen checks.
- **Reference observed:** executed or displayed by a tracked reference capture,
  but not accepted natively beyond any narrower cell stated here.
- **Label only:** text was visible in a captured menu; behavior, count and
  reachability were not exercised.
- **Unobserved:** the repository has no experiment supporting a positive claim.

## Coverage matrix

| Dimension | Original/reference evidence | Native accepted coverage | Remaining M4 boundary |
| --- | --- | --- | --- |
| ROM, region and cadence | The exact headerless 2 MiB PAL ROM is identity-gated; the selected race updates once per PAL frame from reference frame 1329 ([STATE](../STATE.md), [R-0007 finding 9](R-0007-player-state.md)). | Exact same ROM identity is bound into the Classic pack; the desktop scheduler is bounded at 50 Hz for this slice ([R-0014](R-0014-classic-content-pack.md), [R-0016 scheduler](R-0016-minimal-frontend.md)). | Other regions and timing domains are unobserved and are not implied by PAL acceptance. |
| Front-door modes | The main menu visibly lists `1P / 2P / VS / LEAGUE / OPTIONS`; only `1P` was selected ([R-0006 finding 8](R-0006-observed-code-map.md)). | No native menu exists; the app starts at the semantic CRAWLER/DRAGSTER race state ([R-0014](R-0014-classic-content-pack.md), [R-0017](R-0017-m3-acceptance.md)). | `2P`, `VS`, `LEAGUE`, `OPTIONS` are **label only**. Their rules, submenus and player counts are unknown. |
| One-player flow | Reference captures traverse title → `1P` → `PICK YOUR UNI` → `PICK TOUR` → `PICK TRACK` → `NOW PLAYING` → Race; `Exit` is visible but not selected ([R-0006 finding 8](R-0006-observed-code-map.md)). | Only the race and result portion is native; setup screens and Exit behavior are absent. | Menus, cancellation/back navigation, options and post-result continuation need separate evidence. |
| Tour and tracks | `CRAWLER` and `DRAGSTER` were selected. The same Crawler track screen also displayed `ZOOM ZOO`, `BOWL`, `SWITCHER`, `MONSTER` ([R-0006 finding 8](R-0006-observed-code-map.md)). | Only `classic.pal.crawler.dragster.v1`; track sampling, collision, finish and rendering are explicitly Dragster-scoped ([pack manifest](../../tests/manifests/content/classic-crawler-dragster-pack.json), [core guide](../../src/core/README.md)). | The four other displayed names are **label only**. No claim is made that they are the full tour or game-wide track population; other tours are unobserved. |
| Riders and opponent | `MIKE` is selected and `NOW PLAYING` shows `MIKE vs BRONSEN` in the tracked path ([R-0006 finding 8](R-0006-observed-code-map.md)). | The semantic start advances one player rider and one AI rider on the matching frozen path; presentation content is named for MIKE and only the frozen rider-pose pairs are accepted ([pack manifest](../../tests/manifests/content/classic-crawler-dragster-pack.json), [R-0016 presentation](R-0016-minimal-frontend.md)). | Other selectable rider names, opponent selection/rules, palette/identity differences and complete pose sets are unobserved. Do not promote the two displayed names into a roster count. |
| Human player count and input | Every gameplay replay drives controller 1 while controller 2 is silent; reference `2P` and `VS` are menu labels only ([race manifest](../../tests/manifests/replay/race-crawler-dragster-3000.json), [R-0006 finding 8](R-0006-observed-code-map.md)). | Frontend input represents two ports and tests ownership/clearing, but M3 simulation consumes port 0 only ([R-0016 input](R-0016-minimal-frontend.md)). | No two-human gameplay, local multiplayer rules or second-player state agreement is accepted. |
| Movement, collision and gameplay outcome | Controlled reference variants cover acceleration/release, left/right, jump-height response, lean display, collision/contact, both finish orders and result transition within CRAWLER/DRAGSTER ([R-0007](R-0007-player-state.md), [R-0012](R-0012-complete-race-evidence.md), [R-0017](R-0017-m3-acceptance.md)). | Exact finite comparisons cover three full player paths, both winner/loser gameplay outcomes, opponent-first continuation and save/restore boundaries through stable result ([R-0017](R-0017-m3-acceptance.md)). | Generality across another track, rider, opponent or mode is untested. Y/trick meaning and the full trick repertoire remain unresolved; finite paths are not universal mechanics coverage. |
| AI, learned state and randomness | One BRONSEN opponent path and controlled finish continuation are observed. In the tested path, reward event 1 adds weight 4 to cartridge-RAM feature total `$77:0825` at frame 1619; holding the total at zero changes later AI requests from frame 1648. No RNG read was observed in that executed AI branch ([R-0011-motion](R-0011-motion.md), [R-0017 opponent-first](R-0017-m3-acceptance.md)). | The semantic start imports the established initial value, native movement updates/consumes it, and canonical state serializes it across tested continuation boundaries ([core guide](../../src/core/README.md), [R-0011-motion](R-0011-motion.md)). | Other initial learned histories, SRAM fields, AI policies/opponents, difficulty/options and RNG branches remain unobserved. Absence of an RNG read in one branch is not a game-wide no-RNG claim. |
| Presentation | The reference path supplies selected race/finish frames and a winner result at 3679; the slower player-loss path has a captured complete screen at 3800 ([R-0012 experiment](R-0012-complete-race-evidence.md), [presentation manifest](../../tests/manifests/presentation/classic-crawler-dragster-v1.json)). | Seven identity-bound cases pass fixed limits, but both result cases are from the player-win path. Current code explicitly rejects any result outcome other than `PlayerWon` ([R-0017](R-0017-m3-acceptance.md), [presentation source](../../src/core/presentation.cpp)). | Loser gameplay is accepted but loser-result rendering is not. Complete pose artwork, exact whole-frame parity, BG3/fine priority and broader screen/menu presentation also remain outside acceptance. |
| Audio | Reference runs record aggregate audio digests as part of deterministic A/V capture, but no isolated cue/music mapping or cross-backend alignment contract exists ([R-0002](R-0002-reference-adapter-determinism.md), [BUILD_AND_VALIDATION](../BUILD_AND_VALIDATION.md)). | Audio is explicitly not initialized or implemented ([R-0016](R-0016-minimal-frontend.md)). | Music, effects, timing, content provenance, controls and platform tolerance are wholly unimplemented; aggregate A/V repeatability is not audio reconstruction. |
| Game progression and persistence | A result screen is reached; stored-time/ranking/award semantics were left unknown ([R-0012 limits](R-0012-complete-race-evidence.md)). One SRAM-derived learned-feature word has the bounded in-race meaning above; emulator save/restore proves laboratory continuation, not original user-facing persistence. | Canonical in-race state, including the learned-feature value, restores exactly across tested boundaries. The generated content pack persists installation content, not game progress ([R-0011](R-0011-m2-acceptance.md), [D-0005](../decisions/D-0005-classic-content-distribution.md)). | Cross-session league/tour progression, unlocks, records, settings, other original SRAM semantics, native save files and migrations are unobserved. |
| Desktop and release domain | Reference execution is evidenced on the local macOS host; public CI is ROM-free. | M3 builds/tests on macOS 15 and Ubuntu 24.04; visible sustained input/presentation is evidenced on macOS, while Linux has build/test smoke evidence ([R-0017 integration](R-0017-m3-acceptance.md)). | Broader Linux interactive evidence, release packaging/installers, other desktop platforms and public distribution/legal clearance remain outside acceptance. |

## Inventory consequences

The inventory exposed a narrower failure than a new-track experiment. The
release-3000 path already has exact native loser gameplay through stable result
and an original complete-screen observation at frame 3800, but
`build_result_map` rejects `RaceOutcome::PlayerLost`. [M4-01](../../tasks/M4-01.md)
therefore closes loser-result presentation first. It changes no track, rider,
opponent, mode, input schema or gameplay arithmetic and can reuse the frozen
release path. This is the smallest evidenced native coverage gain, not a claim
that result ranking/award semantics are generally understood.

The matrix also does not support immediately generalizing the native engine.
Track, mode, rider/opponent, player count, progression and audio may be entangled
in uncaptured paths, while the only alternate-track evidence is four menu
labels. The following breadth experiment is [M4-02](../../tasks/M4-02.md):

1. retain the exact PAL ROM and pinned core;
2. retain `1P`, MIKE, CRAWLER, Race and silent controller 2;
3. move from default DRAGSTER to the next displayed selection, provisionally
   ZOOM ZOO, using a controlled menu input whose effect is confirmed by frames;
4. first confirm the opponent and event type; if either changes, record that
   coupling and narrow or amend the prerequisite rather than calling it a
   one-variable comparison;
5. freeze a deterministic reference replay and derive its coverage delta before
   deciding what native/content work it requires.

This ordering tests whether the existing state fields and code/content seams
survive a track change without silently introducing a new tour, rider,
opponent, human player, event rule or persistence rule. A failed navigation,
coupled selection or track-specific schema gap is
a useful result: it narrows the next prerequisite instead of authorizing a
plausible substitute.

## Verification limits

This inventory was produced without opening the ROM or generating new traces.
Claims derive only from tracked evidence at `m3`; exact path links are the audit
trail. The next reviewer must challenge at least one classification and confirm
that M4-01 is a genuine outcome-presentation closure and M4-02 does not assume
the menu label isolates a track dimension. The bounded Astra/high audit was
explicitly requested by the user; it identified the loser-result distinction
and second-track coupling risk incorporated above. Independent review is still
required before the coordinator accepts this task.
