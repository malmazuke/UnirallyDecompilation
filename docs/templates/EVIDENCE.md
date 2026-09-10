# <Finding ID> — <specific behavior or format>

- Status: hypothesis / observed / independently verified / contradicted / superseded
- Related task/decision:
- Tested domain and excluded cases:
- ROM hash, emulator revision/configuration and adapter version:
- Addresses: distinguish file offsets from CPU/bus addresses; record bank/mapping and processor-mode assumptions:
- Input/reset/snapshot identity and hashes:
- Experiment source commit and exact command:
- Artifact location, hashes and regeneration procedure:

## Observation

What was measured, including values, units, signedness and sampling phase. Explain how the observation can be repeated.

## Interpretation

What the observation supports; plausible alternatives; what would falsify the interpretation. Confidence is tied to evidence, not a model's certainty.

## Independent check

Different inputs, boundary cases, a traced writer/reader or another observer's reproduction. State who/what performed it and the outcome. Lack of a check is explicit.

## Implementation consequence

Exact arithmetic, data layout/format, state fields or ordering required by the finding. Link affected code and regression cases once they exist.

## Supersession

If corrected, preserve the old claim and link the newer evidence with the reason. Never silently rewrite history to match the current implementation.
