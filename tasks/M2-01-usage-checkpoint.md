# M2-01 — Usage interruption and routing checkpoint

Recorded 12 September 2026. M2-01 and M2-01A remain unaccepted. This record
supersedes their earlier concurrency/unlimited-session allocations with
[D-0004](../docs/decisions/D-0004-model-and-usage-budget.md), not their scope or
acceptance criteria. The user redirected the active work to usage management.

## Runtime condition

The frontier parent and inherited-model workers consumed substantial usage;
`contact_contract`, `motion_contract` and `sampling_review` ended with provider
usage-limit errors (reported reset: 19 September, 08:22). A usage-tool snapshot
reported zero weekly usage, conflicting with the errors. Actual numerical usage
is unknown; no reset credit was redeemed and no new service was purchased.
No worker was respawned. All prior claims need a stopped-process/ownership check
before reassignment. This continuation is OpenAI-based: resume through a fresh explicit Sol session
when that provider can work. Do not switch to Claude Code automatically; only
the user may move the continuation to another platform.

## Preserved source

Paths below are relative to the repository. The root main was `3865ab1` before
this policy/checkpoint commit; previously accepted native sampling/progress is
on main. All new component branches below remain separate from main.

| Worktree / branch | Head | Evidence/status at interruption |
| --- | --- | --- |
| `.worktrees/m2-01-comparator` / `codex/M2-01-comparator` | `c46ab59` | Strict comparator independently approved; no native CLI registration |
| `.worktrees/m2-01-input-timer` / `codex/M2-01-input-timer` | `a05ce14` | Input/timer independently approved; component tests use captured arguments |
| `.worktrees/m2-01a-contact` / `codex/M2-01A-contact` | `b0556af` | Contact research and C++ component independently approved within recorded flat-track domain |
| `.worktrees/m2-01a-speed` / `codex/M2-01A-speed` | `68fcdd92757ed73971e0ef1e77747507d2479d50` | Research approved; native independent review pending. Recorded final suite 221/221, clean source; debug/sanitizer component comparison 14,660 values |
| `.worktrees/m2-01a-motion` / `codex/M2-01A-motion` | `9b840a8` | Research fixes include negative boost halving and pose-distance cancellation; final independent signoff pending. Uncommitted `tasks/M2-01A-motion-handoff.md` draft preserved |
| `.worktrees/m2-01-native-cli` / `codex/M2-01-native-cli` | `1b599dc` | Protocol and three authored tests only; actual command, preparation and movement runner unfinished |
| `.worktrees/m2-01-integration` / `codex/M2-01-continuation` | `ce92bb22f7fcdf21218137c290cdb703fd61c84a` | Input/timer plus contact assembly checkpoint. Resolved two additive CMake conflicts by retaining both targets. Integration build/suite NOT run on this head; not accepted or merged to main |

Independent review reports are in the separate ignored clone
`.worktrees/m2-01-sampling-review/artifacts/`: `comparator-review/REVIEW.md`,
`input-timer-review/REVIEW.md`, `contact-native-review/REVIEW.md`,
`contact-review/REVIEW.md`, and `speed-review/REVIEW.md`. Read exact task and
research records on each branch for commands, identities and evidence hashes;
this table is navigation, not replacement validation. Retain local artifacts.

## Remaining work and first resumption

1. Read AGENTS, STATE, D-0004 and component handoffs. Inspect branch heads and
   dirty state; check for surviving reference workers before reassigning claims.
   Start with `git -C .worktrees/m2-01a-motion status --short` and inspect its
   preserved draft, then reproduce the last recorded motion check on `9b840a8`.
2. Use one fresh Sol reviewer for final motion research fixes and then the speed
   native component. Preserve independent reproduction and boundary cases.
3. Assemble reviewed components on the continuation branch, resolving interfaces
   and running affected checks on the exact candidate. Its immediate build
   command is `python3 tools/project.py build --preset lab-debug` from that
   worktree, followed by `python3 tools/project.py test --suite synthetic`.
4. Implement the semantic native state/update, seed/content preparation and
   `movement_runner`, then wire native comparison using the agreed protocol in
   the CLI handoff. These are unfinished implementation, not missing user input.
5. Freeze the full implementation before opening M2-01's withheld movement
   outputs. Validate all 13 required fields, primary frames 1534–2999 from an
   end-of-frame1533 seed, then both frozen withheld cases and independent review.

The coupled state includes opponent motion/contact/pose, quarter-turn rewards,
boosts and cartridge-RAM feature totals affecting later AI. Component probes
receive captured arguments; they cannot establish autonomous gameplay. No
emulator fallback, fitted per-frame oracle or relaxed expected output is allowed.
Withheld-release2347 and cadence17 outputs remain unopened at this checkpoint.

## This checkpoint's verification

Inspected branch/dirty state and staged merge changes; `git diff --cached --check`
passed before the assembly checkpoint commit. No new gameplay test result is
claimed. The policy/configuration change is checked by TOML parsing, local link
resolution and Git whitespace checks; runtime default selection still needs to
be observed in a fresh session. Existing live sessions are not switched by a
repository configuration edit.

## Subsequent user routing adjustment

Keep the current continuation's coordinator on Astra. Sol/medium is the default
for future OpenAI sessions and bounded workers, not a requirement to replace
this live coordinator. Future Anthropic sessions start with Opus provisionally.
Provider boundaries and quota guardrails above still apply.
