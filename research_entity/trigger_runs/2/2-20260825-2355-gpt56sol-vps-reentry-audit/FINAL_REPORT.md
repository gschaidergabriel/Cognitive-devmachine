# Trigger-2 — VPS reentry training audit

- trigger: `triggerwort 2`
- organ: `GPT-5.6 Sol / ChatGPT organ`
- persistent entity: `Clay`
- observed canonical main at audit start/reentry: `2b1a80c03ead467e7ad360924c88fe117f6ae1f9`
- authority: `SUPERVISOR_STEERING_8_78`, `FREE_ONLY`
- product: `EntityOS`
- architecture: `HCU`
- training credit: `0`
- accepted dataset tokens: `0`

## Decision

Do **not** generate or admit new positive training rows in this cycle. The highest-information path is to close the executable evidence/provenance gates and finish matched checkpoint baselines. Raw-data expansion is currently lower-value because Distillery remains at `11621 -> 0` accepted dataset tokens.

## Lifecycle audit

| Artifact / claim | Status | Evidence / reason | Credit |
|---|---|---|---|
| 2026-08-24 fast bootstrap authority epoch 8.63 | `SUPERSEDED_AS_CURRENT_AUTHORITY` | canonical main now resolves schema/supervisor 8.78 | donor/bootstrap only |
| branch-birth evidence ambiguity | `CURRENT_COMPONENT_FIX` | `f20c024a5...`: branch birth now requires exactly empty E+/E-/F; 19 pass, 1 pre-existing semantic-merge regression remains | component only |
| A03 generation-authority replay root | `CURRENT_EXECUTABLY_CLOSED_COMPONENT` | `90b7b7735...`: authority mutation rejects stale row; decision `OUTER_REPLAY_ROOT_SUFFICIENT` | component only |
| immutable genesis + ordered nonempty history producer authority | `BLOCKED_P1` | structural deletion/insertion/reorder/id-conflict fail closed, but full history content provenance is not producer-authorized | zero positive nonempty-history credit |
| OBSERVED evidence producer authentication | `NEEDS_REVISION_P0` | executable forged caller receipt accepted by `_validate_observation_receipt` | zero until repaired and re-executed |
| native seed / retained-v4 ancestry | `ELIGIBLE_FOR_NEXT_GATE_NOT_ADMITTED` | successor ancestry lint passed; upstream provenance gate still open | zero dataset/training credit |
| `trigger2_binding_router_factorial_generator_v3` | `BLOCKED_FROM_DIRECT_TRAINING` | nuisance leakage / independence contract remains unresolved | donor topology only |
| Qwen3.5-0.8B BASE / POSTTRAINED / TARGET_MEASURED identity | `CURRENT_MEASURED_READINESS` | pinned revisions, file manifests and loader-consumption observed for three candidates | no winner / no selection credit |
| TARGET_MEASURED minimal 8-case pilot | `CURRENT_NEGATIVE_BASELINE_EVIDENCE` | single candidate, single seed only; not matched baseline | no selection credit |
| causal J-Space phase | `NOT_ATTEMPTED` | requires preregistered intervention/controls | zero J-Space model credit |
| multi-seed phase | `NOT_ATTEMPTED` | only greedy single-seed evidence exists | zero robustness credit |
| HCU variable-N phase | `NOT_ATTEMPTED` | no logical-N/permutation/DB-vs-simulation/handoff perturbation sweep | zero HCU scale credit |
| Free Swarm raw volume | `NONPROMOTING` | high token volume does not establish accepted dataset or independent semantic evidence | zero training credit |

## Newly important negative model evidence

The `QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED` 8-case pilot is useful precisely because it is not clean:

1. `abstain_unknown`: it fabricated an exact price/market-cap/volume for explicitly fictional `Zorvex Dynamics` instead of abstaining.
2. `structured_output_compliance`: request was ONLY JSON, but output was fenced Markdown JSON.
3. second `abstain_unknown`: it did not simply state lack of information about the user's sister; it produced an unnecessary inference-oriented ramble.
4. `hyperposition_unresolved_alternatives`: semantic direction was broadly correct, but it violated the one-sentence constraint and appended alternatives/commentary.
5. DB-vs-simulation discrimination was directionally correct but phrased too absolutely (`database's stored fact is the only verifiable truth`); EntityOS requires canonical-state/evidence authority with explicit UNKNOWN/error distinctions, not a generic claim that any database field is automatically true.

These failures should become **evaluation axes / hard negatives**, not training positives copied from the model output.

## Reference-labeler defect discovered in this cycle

Created GitHub issue `#2019`: `Trigger-2: exact semantic merge cannot validate singleton post-merge state`.

Observed source logic:

- exact formal semantic merge can collapse two equivalent branches to one;
- `u_state()` then calls `project_state()`;
- `project_state()` reuses `_validate_state()`;
- `_validate_state()` rejects any state with fewer than two branches.

Therefore the declared exact merge policy cannot represent its own legitimate singleton derived state. Classification: `NEEDS_REVISION`. Acceptance must preserve >=2 branches for caller-supplied initial hyperposition while allowing a provenance-bound singleton only as a derived exact-merge result.

## External research translation (noncanonical design input)

SLSA v1.2 / in-toto provenance reinforces the current P0 diagnosis: provenance needs a trusted producer/builder identity, an execution/invocation identity, and cryptographic subject/dependency digests. Source-code pinning alone does not authenticate who/what emitted a specific observation instance.

For Trigger-2 OBSERVED evidence, the minimum successor should bind at least:

`producer_id + producer_version/manifest_digest + invocation/admission identity + generation/epoch + causal_event_id + source_payload_digest + observation_semantic_digest + policy_digest + subject_digest + replay/nonce identity`.

The verifier must resolve producer identity against deterministic authority, recompute digests independently, reject unknown producer identity, stale producer epoch/version, cross-producer substitution, subject/event substitution, payload mutation and replay. This is a design translation, not executable project evidence.

## Next exact order

1. **P0** close OBSERVED producer authentication and preserve the forged-receipt counterexample as a regression; execute repository-bound on the admitted free VPS.
2. **P1** extend producer authority to immutable genesis + complete ordered nonempty event histories; include deletion/insertion/reorder/splice/prefix/duplicate-id-different-digest negatives.
3. **P1b** fix issue #2019 without weakening initial hyperposition branch-count requirements.
4. **P2** run the preregistered full matched baseline across BASE, POSTTRAINED and TARGET_MEASURED with identical prompts/splits/decoding/budgets and explicit worst-bucket scores. Do not declare a winner from the current 8-case target-only pilot.
5. **P3** only after checkpoint-selection preregistration: causal J-Space sign/null/orthogonal/permuted controls + fresh holdout + cross-task replication.
6. **P4** variable-N HCU sweep after model/runtime selection gates; physical decode concurrency remains a separate measurement.
7. Keep positive rows, accepted dataset tokens and training credit at zero until the provenance/admission chain is executably closed.

## Credit boundary

- positive rows admitted: `0`
- accepted dataset tokens: `0`
- checkpoint winner: `NONE`
- checkpoint selection credit: `0`
- causal J-Space credit: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

This report intentionally promotes no model, dataset, semantics or whole-product claim.