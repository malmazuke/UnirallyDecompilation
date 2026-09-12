# <Task ID> — <reviewable outcome>

## Assignment

- Status: planned / ready / claimed / in_progress / review / accepted / blocked / abandoned
- Milestone:
- Coordinator:
- Task provider (fixed for all children; record any user-initiated platform change):
- Worker/session/runtime/model:
- Actual model/reasoning effort, routing rationale and frontier escalation question (if any):
- Provider quota window/baseline timestamp, used/remaining or unknown, reserve and session allowance (D-0004):
- Reviewer:
- Dependencies and evidence of acceptance:
- Base commit:
- Branch and isolated worktree:
- Owned paths and shared interfaces:
- Claim/lease/heartbeat/checkpoint location:
- Session time limit, concurrency allocation and actual spend authorization if relevant:

## Outcome and boundaries

Describe a concrete deliverable. Name the behavior/domain covered and the work deliberately outside this task. Link relevant decisions. A research task may deliver a validated finding without production code.

## Inputs and prerequisites

List ROM/tool/fixture hashes, schema versions, local-only artifact locations and required capabilities. Explain how a fresh host obtains or regenerates them. List known baseline failures separately.

## Acceptance

| Criterion | Command or experiment | Expected result | Required artifact |
| --- | --- | --- | --- |
| <criterion> | <reproducible invocation> | <predefined expectation> | <report/manifest/hash> |

For a task creating a tool, state the intended interface and how that tool will itself be verified. Don't claim a not-yet-implemented command can currently run.

## Evidence and attempts

| Attempt | Hypothesis | Experiment | Observation | Next decision |
| --- | --- | --- | --- | --- |

Link concise evidence records and full local artifacts. Do not paste an entire transcript.

## Handoff

- Current base/head commit and uncommitted state:
- Verified findings:
- Current hypothesis and failed approaches:
- Commands executed, outcomes and report hashes:
- Unavailable/skipped checks:
- Exact next experiment/command:
- Remaining dependencies:
- Runtime needs (network, build time, fixtures, memory):
- Aggregate parent/child time, provider usage before/after (or unknown), other-account-work caveat:
- Accepted outcome, review/fix rounds and next routing decision:

## Review and integration

- Reviewer and independent reproduction/withheld-case results:
- Required changes or acceptance rationale:
- Exact merge candidate and required-check results:
- Integrated commit and evidence location:
- Remote synchronization: pushed ref(s), verified local/remote commit IDs, or
  exact push failure:
- Scope still unverified:

Only the coordinator marks accepted after integration and evidence checks. When
the existing private `origin` is configured, completion also requires pushing
the accepted integration to `origin/main` (and any accepted milestone tag) and
verifying the remote ref. A local `main` that is still ahead is not complete.
