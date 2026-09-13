# Trial process preparation — 13 September 2026

- User assignment: prepare repository policy/tasks so the next Astra session can
  execute the agreed process trial. No gameplay implementation or reset redemption.
- Base: `15237954fe636ecf83cf105186570207593c900b`; branch `task/trial-process-prep`.
- Scope: AGENTS/README, workflow/plan/validation/model decision, D-0006, task
  template/registry, compact state/handoff, M4-12 and config comments. Historical
  evidence and gameplay source/fixtures remain unchanged.
- Preparation usage: OpenAI weekly 98% used; one reset available. Concise
  documentation review/preparation only; do not redeem the reset.
- Acceptance: internally consistent trial ownership, startup, scope, resource
  policy, automatic explicit-model review, immutable evidence and staged gates;
  Markdown local links and TOML parse; independent Sol review; inspected diff,
  synchronized private main and final hosted CI status.
- No new tests needed for documentation/config comments. Native suites are not
  rerun locally because executable code/inputs are unchanged; this is not a claim
  that new gameplay was tested. Hosted configured CI still runs on source sync.
- Reviewed candidate: `bc638f6991c149a302a85d5cd69af9874bed4368`.
- Independent Sol/medium review approved without material findings; report commit
  `34e854f3e4cd8968c82e239e5dfc04b40b2fea67`,
  [review record](TRIAL-PREP-review.md). No implementation files were changed by review.
- Local validation: `git diff --check` passes; all 119 local Markdown links in
  the candidate resolve, including heading anchors; `.codex/config.toml` parses
  with unchanged Sol/medium defaults. CLI help confirms `rom inspect --expect`
  and build/test `--preset` options. No gameplay/build suites ran locally.
- Accepted gameplay ancestor remains `15237954fe636ecf83cf105186570207593c900b`.
  Integration consists of the reviewed candidate, independent review record and
  this documentation-only validation handoff. Inspect `git log` for the final
  bookkeeping commit rather than inventing a self-referential hash here.
- Delivery verification: push private `main`, verify `git rev-parse HEAD` equals
  `git ls-remote origin refs/heads/main`, then check the `synthetic` hosted run
  whose `headSha` equals that final tip. This session's completion report records
  the exact pushed commit and hosted result. No milestone tag is appropriate.
- Next action: user starts Astra/medium with tasks/NEXT_SESSION.md. M4-12 remains
  unclaimed; fresh usage/reset readiness is required before implementation.
  Reset consumed by preparation: none.
