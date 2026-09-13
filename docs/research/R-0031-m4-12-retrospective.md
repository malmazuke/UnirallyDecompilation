# M4-12 retrospective

M4-12 delivered a bounded native capability: both riders matched all 395 canonical bytes for 200 updates, with independent variations and restores. It was a substantial integration step built on extensive prior research—not a reconstruction from scratch.

**Reused versus newly recovered.** M4-02–M4-04 supplied the reproducible ZOOM ZOO replay, static-content contract and authentic end-1649 seed. M4-05–M4-11 supplied contact, position/residue, response-B and vertical-velocity evidence. Existing DRAGSTER code supplied controller sampling, timer, progress, pose, jump, gravity, speed-limit and reward helpers; the pinned emulator, capture tools and validation infrastructure were already available.

New work connected those pieces into an autonomous update: horizontal control/AI ordering, reflection transitions and pose overrides, additional vertical-contact cases, auxiliary-contact byte-width semantics, later landing transforms and boost-tile ordering. The landing required recovering immutable pre-race coefficient matrices. The screen-dependent speed predicate was bounded using an explicit retained opponent seed byte and rejection of unsupported player-boost cases. [Source and dependency inventory](R-0030-zoom-zoo-native-trial.md)

**Workflow changes that helped.** Keeping coupled dependencies inside one capability task avoided a separate dispatch/review/integration cycle for each producer. Early native execution made the next investigation concrete: fix the first divergence, then extend exact coverage. Freezing the longer reference before tuning forced progress beyond the familiar 51-frame window and exposed the later landing/boost sequence. Reusing semantic helpers avoided building another complete Python simulation.

Independent review materially improved correctness. Delayed acceleration exposed the missing low-speed gate on the wrong-direction counter at frame 1661. After correction, that case became a disclosed regression; a newly preregistered case supplied fresh withheld evidence. Review also overlapped useful validation work. [Review and correction](../../tasks/M4-12-review.md)

**Where time went.** Only checkpoint times were recorded; these activity estimates overlap and should not be summed.

| Activity | Approximate time |
| --- | ---: |
| Investigation: traces, dependency audit, arithmetic and ordering | 20–25 minutes |
| Native implementation, serialization, extraction/comparison tooling | 15–20 minutes |
| Environment/setup and avoidable path corrections | 3–5 minutes |
| Independent review and correction | About 12 elapsed minutes, overlapping validation |
| Local validation and repeated corrected-source gates | 6–10 minutes, overlapping review |
| Post-approval integration, documentation, autonomy check and final CI | About 11 elapsed minutes |

The records are consistent: **10:24–11:24 UTC was approximately 60 minutes to review approval**, with weekly usage rising from 0% to 11%. **11:35 UTC was final closeout**, after integration, remote verification, the OS-denied-reference experiment and final CI: approximately **71 minutes and 12 percentage points**. Usage was account-wide, may include unrelated work, and is not a task-cost measurement. No reset was used. [Checkpoints](../../tasks/M4-12.md) · [Final closeout (private local artifact)](../../artifacts/m4-12/closeout.json)

**Remaining waste.** Top-level cache symlinks caused 12 Python failures and a rerun; an incorrectly placed report caused another rejected invocation. Several projection captures and temporary scripts accumulated while the state inventory evolved. Starting with the correct directory layout and promoting the harness earlier would reduce this churn. The full matrix was repeated after the review fix, and preliminary CI was cancelled. Those corrected-source checks were justified, but broad validation could have waited for the first review result.

**Limits and shortcuts.** “Exact” means four seconds from one seed on one PAL ROM, covering the declared gameplay projection—not all machine state or arbitrary Right/neutral sequences. Unknown branches fail closed. Pre-race extraction still uses the original emulator; native gameplay does not. Camera-dependent boost behavior was bounded rather than generally recovered. Hosted Linux CI passed synthetic checks, not a Linux run of the private ZOOM ZOO references. There is no full-track finish or ZOOM ZOO frontend/presentation support. This was not a controlled model benchmark.

**Recommended next capability:** autonomous two-rider ZOOM ZOO continuation through a controlled **player support-loss, landing and recovery** sequence. Before implementation, freeze a horizon that includes that event and at least 100 subsequent updates. Require the same-seed native run, complete future-affecting state, two reviewer-owned timing variations, restores before/after landing, and zero captured runtime inputs. Recover any newly reached control or camera dependency within that capability; keep finish and presentation excluded. This is a recommendation only—no further implementation or tests were started.


Assessment decision: this recommendation was adopted for the next prepared
[M4-13](../../tasks/M4-13.md) task under [D-0006](../decisions/D-0006-capability-driven-work.md).
The usage/time figures remain observations with the limitations above.
