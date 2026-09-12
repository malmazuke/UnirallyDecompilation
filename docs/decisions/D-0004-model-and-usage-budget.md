# D-0004 — Model routing and usage conservation

Status: adopted, 12 September 2026. Reassess from measured accepted work.

## Context

The user reports exhausting a weekly Codex allowance in about one hour with
Astra, compared with about 24 hours of work with Fable 5.1 in Claude Code.
These are observations across different providers and workloads, not a
controlled model-cost benchmark. The M2 continuation used a frontier parent
and several children inheriting that model. Parallelism shortened elapsed time
while increasing aggregate usage. Three child sessions subsequently returned
usage-limit errors. The usage snapshot conflicted with those errors; it cannot
support a numerical burn-rate estimate.

## Routing decision

**Keep each task within the provider the user started it with.** An OpenAI
task uses only OpenAI models for coordination, implementation, subagents and
review; an Anthropic task uses only Anthropic models. Model/effort changes within
that provider remain autonomous. This applies to prerequisite tasks and fresh
worker sessions too: creating a child does not authorize crossing providers.
Only the user may move work between platforms. A user-initiated continuation
on another platform establishes the provider for that continuation; historical
commits from another provider do not force a switch back.

The user manages the two subscription allowances separately and reports no
Anthropic weekly allowance remaining at this adjustment. Never assume the other
provider has spare capacity. If the task's provider runs out, checkpoint and
report the resource condition; do not fall back to another provider or ask the
user to make a routine routing decision.

The following defaults apply to OpenAI tasks. For Anthropic tasks, keep routine
work in the selected Anthropic runtime (Opus is the proposed worker candidate),
with bounded Fable consultation/review where justified; never dispatch Sol or
Astra from that task. Record actual supported model settings in either runtime.

| Work | Default | Escalation |
| --- | --- | --- |
| Coordination, task selection, routine planning | Sol, medium reasoning | One bounded frontier consultation for a consequential unresolved design question |
| Implementation and ordinary research | Sol, medium reasoning | Narrow the experiment after two unsuccessful bounded attempts; use high reasoning or a frontier consultation when the record explains why |
| Independent component review | Fresh Sol reviewer; medium normally, high for difficult arithmetic | Frontier review for unresolved reviewer disagreement or critical uncertainty |
| Milestone architecture/accuracy audit | Bounded Astra review | Produce findings and a decision, then return execution to the default model |
| Mechanical, low-risk chores | Sol initially; Terra/Luna optional | Adopt only when measured results justify the change |

Use explicit provider model IDs and reasoning settings in each dispatch. Codex
IDs currently used here are `gpt-5.6-sol` and `gpt-6-astra`; do not infer IDs from
marketing names. Fable and Opus run through an available Claude Code runtime,
not as fictional native Codex subagent IDs. Opus is a candidate implementation
or review worker, but its name alone establishes neither cost nor suitability.
Use the user's observed Fable throughput as a reason to compare it, not a
promise of future hours. Never create a paid provider account to switch models.

A frontier consultation receives one question, exact evidence paths and a
required output. Reassess within ten minutes and checkpoint if unresolved;
do not turn it into continuous frontier coordination, routine coding or polling.
A second consultation needs a recorded new question or new evidence. Routine
model selection and reversible adjustments need no user confirmation.

## Starting future sessions

Start new OpenAI work sessions with Sol/medium; start Anthropic sessions with
Opus as the provisional routine coordinator/worker choice. Keep the coordinator
stable and use compact, same-provider frontier consultations when justified.
Do not start every task on a frontier model merely to plan it before switching.

User adjustment: the completed OpenAI run kept Astra as coordinator. At its
clean checkpoint, the user requested preparation for a cheaper coordinator; the
next continuation starts on Sol using tasks/NEXT_SESSION.md.
The new-session default does not require a mid-task coordinator switch. Bounded
Sol workers remain available under the existing scope and quota rules. This is
a continuity preference, not a measured claim that switching models would cost
more: the actual context sent, compaction and caching determine input overhead,
and this session's cross-model cache behavior has not been established.

## Execution and usage guardrails

- Default to the primary plus at most one active child. Sequence implementation
  and independent review. A second child requires a recorded independent scope,
  expected benefit and usable quota; a frontier swarm is not the default.
- Start children with a compact task handoff: exact base, owned paths, relevant
  evidence and acceptance checks. Avoid copying full conversation history. For
  Codex collaboration calls with a model override, use `fork_turns: "none"` and
  supply that self-contained prompt. Explicitly set model and reasoning effort;
  an inherited frontier model is not an acceptable accidental default.
- Sample available account usage before dispatch and at checkpoints. Record the
  provider/window, timestamp, used/remaining percentages and reset, or `unknown`.
  Compare aggregate work across parent and children; account-wide deltas may
  include unrelated work and cannot be attributed precisely to this project.
- Updated policy for tasks started after 12 September 2026: reserve the final
  20% of a weekly allowance for review/recovery; limit discretionary
  implementation to a 20 percentage-point increase from a recorded
  work-session start. This doubles the former 10-point task quota and its
  enforcement guardrail; the recovery reserve is unchanged. Do not reset that
  baseline by spawning a child, rotating tasks or starting another automatic session. At
  either threshold, checkpoint and end discretionary implementation with the
  resource condition recorded. Do not switch providers to bypass the limit.
  These are project defaults chosen in response to the user's request, not
  provider guarantees or newly authorized purchases.
- Unknown or contradictory telemetry is not free capacity: avoid new frontier
  dispatch, use at most one default-model child if the runtime permits, and
  reassess at each checkpoint. An actual usage-limit error stops new dispatches
  to that provider; do not repeatedly retry or respawn. Preserve partial work.
- Never automatically redeem reset credits, buy credits, enable paid API usage
  or upgrade a plan. Existing authority to work is not authority to spend.
- Keep 45-minute reassessment sessions and ten-minute durable checkpoints.
  Use focused checks during edits and the required complete checks on the exact
  review/integration candidate. Do not rerun unchanged broad suites simply to
  keep agents occupied. Preserve independent reproduction, withheld cases and
  frozen expectations; cheaper execution does not weaken acceptance.

The percentage guardrails are sampled, agent-enforced policy. No hard token or
spend limiter, quota monitor, automatic model router or scheduler is implemented.
If a provider exposes an actual spend cap, use it within existing authorization.
Time limits alone cannot guarantee token limits.

## Configuration and measurement

[Project Codex configuration](../../.codex/config.toml) defaults new sessions to
Sol/medium and one Sol/medium child. Explicit session, spawn or custom-agent
settings can override those defaults. It does not switch an already running
frontier session. Other runtimes follow this decision through AGENTS.md and the
portable dispatch record; game code and evidence remain provider-independent.
Use standard service mode; do not opt into Fast mode for routine project work.

Record model, effort, reason, accepted outcome, review/fix rounds, aggregate
agent time and observed quota delta in the task. After three comparable bounded
tasks, compare accepted outcomes per allowance consumed and adjust the defaults.
Do not benchmark with extra artificial workloads or infer efficiency from wall
clock time alone.

User adjustment, 12 September 2026: double the quota for all future tasks,
including the guardrail. This changes the per-task discretionary allowance from
10 to 20 percentage points. It does not authorize reset redemption, purchases,
provider switching or use of the final 20% review/recovery reserve.

Official references checked on 12 September 2026:
[Codex subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Codex pricing and usage](https://learn.chatgpt.com/docs/pricing).
The published credit rates imply 2.5 times the credits for Astra versus Sol for
the same input/cache/output token mix. That is not a prediction of subscription
runtime, and does not explain the user's entire observed difference.
