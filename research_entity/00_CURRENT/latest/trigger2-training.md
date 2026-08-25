# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V60** is the current research-ledger successor under Supervisor **8.83**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed

Owner FreeSwarm remains `HARD_OFF`. V59 recorded OpenRouter `total_requests=4140`, `total_429=4005`, `total_success=134` and `go_swarm=RUNNING`, i.e. +357 requests and +357 429s relative to the Supervisor 8.83 snapshot. Provider/model/training execution remains closed.

Required closure remains owning-host identification and termination/quarantine of every provider-capable survivor, zero survivors, a bounded no-restart interval, and zero provider-counter delta without issuing a provider probe.

Pinned quiescence lane:

- enforcer source: `0d14624bf211e797936626e94c87459e37dd0cbb`
- execution request: `047962d015c6eb0e768df3eebbbc3aba91cf097f`
- frontier receipt: `8300bbd7cc7ef037b66fc5a0e84c5da945a3aa4d`

## Checkpoint-selection governance — frozen source-only

The 512-case / 256-family four-quadrant logical manifest remains frozen and model outputs remain unopened. No checkpoint winner exists and checkpoint-selection credit remains `0`.

## Model-call → NODE_RESULT lineage — V60 exact-call cohort discriminator

The retained temporal-causality direction remains:

- `tools/trigger2_node_result_model_call_two_phase_authority_v1.py` — commit `56e8cc09f0c1b8e1fd99ab091154c3f3a6382b17`
- `tests/test_trigger2_node_result_model_call_two_phase_authority_v1.py` — commit `e287fcc5e73277dd8bc5119c11f2b97b5dde9616`

The two-phase pattern correctly separates:

1. **pre-call launch descriptor** — cohort plan, GRID cell, node, node-admission identity/revision, runtime generation, controller-observed PID, candidate, rendered-input identity and source identity;
2. **post-call executor observation** — exact launch descriptor plus the existing source-bound model-call identity, model-output identity, ABI-v2 receipt identity and executor-observed PID;
3. **derived authority envelope** — immutable authority-free NODE_RESULT plus those phase-separated deterministic commitments.

V60 adds a narrower cohort-level finding. `derive_authority_cohort_id` currently enforces uniqueness for cell, node, PID, launch descriptor, executor observation and raw NODE_RESULT packet, but not for the exact `source_bound_model_call_identity_sha256` or `source_node_admission_id`.

That means two distinct cells can theoretically carry two distinct launch descriptors and two distinct post-call observations while both reference the **same exact model call**. Distinct observation wrappers do not prove distinct model invocations. If a cohort member claims an independently attributed model invocation, exact call identity must be injective across those members. Intentional one-call fan-out would need an explicit one-call/many-consumer representation instead of being counted as multiple independent calls.

Source-only audit:

- `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TWO_PHASE_COHORT_EXACT_CALL_UNIQUENESS_AUDIT_V1_GPT56SOL.json` — commit `2c3881c17d68d1dcbc35fd4fefa79ce3b233c71f`

Pinned regression:

- `tests/test_trigger2_two_phase_cohort_exact_call_uniqueness_regression_v1.py` — commit `c3c8b8b714edfd605ac60e1b57df84a4cba1f635`

The regression preserves these distinctions:

- two distinct exact calls form a valid cohort;
- identical `model_output_identity_sha256` remains allowed for distinct exact calls;
- strict xfail: one exact `source_bound_model_call_identity_sha256` projected into two distinct cells must eventually reject with `AUTHORITY_COHORT_MODEL_CALL_DUPLICATE`;
- strict xfail: one `source_node_admission_id` projected onto two distinct nodes must eventually reject or be independently cross-validated against node identity.

No repository CI execution is claimed for this new regression yet. No model/provider/runtime/training promotion follows from source structure.

## Training target remains binding/routing, not generic language tuning

Historical measured Trigger-2 baseline remains approximately:

- context-transfer: `0.5254629629629629`
- dynamic-symbol hit: `0.3611111111111111`
- three-way chance: `1/3`

The primary measured trainable deficit remains `CONTEXT_DEPENDENT_VARIABLE_BINDING_ROUTING`. Semantic readout, symbol writeout and carrier binding were not the primary measured bottleneck in the retained evidence scope.

`trigger2_binding_router_factorial_generator_v3.py` remains blocked from direct training for conditional nuisance leakage in codebook-order serialization. Do not materialize training from the leaky generator.

## Next source-only gate

Patch only the retained two-phase cohort reducer so `source_bound_model_call_identity_sha256` and `source_node_admission_id` are one-to-one across independently attributed cohort members, then convert the two strict xfails into passing regressions. After that, integrate the retained two-phase authority envelope with `PROOF_CARRYING_NODE_RESULT/v1` and the fused GRID10 membership/cohort path without changing raw model cognition or creating a second authority schema.

P0 runtime quiescence still outranks this source work for any execution promotion.

## Credits remain zero at promotion scope

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V60_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_83_DELTA_2026-08-26T0435P0700_GPT56SOL.json`
