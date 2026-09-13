# M4-15 preparation

- User authorized next-task preparation after the M4-14 retrospective: aim for
  race completion, reference feasibility inside the task, evidence-justified
  downstream fallback only, audit preflight and lightweight validation ledger.
- Base: `38c72e889d59b62270be6e26fca713b3fb3aa153`; branch
  `codex/m4-15-preparation`. Base remote ref and CI `34761303975` verified.
- Scope: documentation and config comment only; no gameplay capture, implementation,
  frozen evidence changes or new tooling in this preparation.
- Starting shared weekly usage 37%; no credits/reset/purchase used.
- Acceptance: inspect staged diff, Markdown links, TOML, fresh isolated Sol/medium
  documentation review, private main push/ref verification and exact-tip CI.
  Native local suites are unnecessary for this documentation-only change.
- Local validation: 124 local Markdown link targets resolve; TOML parses and
  actual model defaults are unchanged. `git diff --check` passed.
- Final delivery is conditional on review/local checks, private sync and final-tip
  CI. Record final identities/results/time/usage in ignored
  `artifacts/m4-15-preparation/closeout.json`; if unavailable, recover main history,
  `git ls-remote origin refs/heads/main` and `gh run list --commit <sha>` /
  `gh run view <id> --json headSha,status,conclusion`.
- M4-15 remains ready/unclaimed. Implementation starts in a new user-started
  Astra/medium session; no M4-16 dispatch.
