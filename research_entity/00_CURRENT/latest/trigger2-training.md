# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V61** is the current research-ledger successor under Supervisor **8.83**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed

Owner FreeSwarm remains `HARD_OFF`. V59 recorded OpenRouter `total_requests=4140`, `total_429=4005`, `total_success=134` and `go_swarm=RUNNING`, i.e. +357 requests and +357 429s relative to the Supervisor 8.83 snapshot. Provider/model/training execution remains closed.

Required closure remains owning-host identification and termination/quarantine of every provider-capable survivor, zero survivors, a bounded no-restart interval, and zero provider-counter delta without issuing a provider probe.

Pinned quiescence lane:

- enforcer source: `0d14624bf211e797936626e94c87459e37dd0cbb`
- execution request: `047962d015c6eb0e768df3eebbbc3aba91cf097f`
- frontier receipt: `8300bbd7cc7ef037b66fc5a0e84c5da945a3aa4d`

## Checkpoint-selection governance — frozen source-only

The 512-case / 256-family four-quadrant logical manifest remains frozen and model outputs remain unopened. No checkpoint winner exists and checkpoint-selection credit remains `0`.

## Model-call → NODE_RESULT lineage — V61 semantic correction

Retained source direction:

- `tools/trigger2_node_result_model_call_two_phase_authority_v1.py` — introducing commit `56e8cc09f0c1b8e1fd99ab091154c3f3a6382b17`
- exact committed fixture bytes aligned at `8f9789e49d6806d8d508233712fec3aa85d4e620`
- exact-byte deterministic source validation receipt: `research_entity/continuity/receipts/2026-08-26_TRIGGER2_TWO_PHASE_SOURCE_VALIDATION_GPT56SOL.json` — commit `e9292ea7857877ec1da972d43ee21e745a00fc66`

The receipt binds exact source/test bytes and records `py_compile PASS` plus `9 passed in 0.03s` on a local deterministic source fixture. It is not repository CI, model runtime, physical GRID10 runtime, training, or EntityOS/HCU acceptance.

The retained two-phase pattern separates:

1. **pre-call invocation precommit** — `launch_descriptor_sha256` binds cohort plan, GRID cell, node, membership incarnation, runtime generation, PID, candidate, rendered input and source identity;
2. **post-call invocation observation** — `executor_observation_sha256` binds that launch to the existing source-bound model-call content/evidence identity, model-output identity and ABI-v2 receipt;
3. **derived invocation provenance** — authority envelope over exact launch + post-call observation + immutable authority-free NODE_RESULT evidence.

### Critical V61 correction: call content is not invocation identity

Direct ABI/source inspection falsified V60's blind call-digest injectivity hypothesis. `source_bound_model_call_identity_sha256` commits model/input/runtime/output/source evidence, but the current schema does **not** contain HCU causal-event, GRID-cell, membership-incarnation, process-instance or launch identity. Therefore it is best treated as **model-call content/evidence identity**, not as a guaranteed unique invocation-event identifier.

Two independently launched deterministic invocations may validly have equal call-content and equal output identities while remaining distinct causal invocations through distinct launch and executor-observation identities. Conversely, reusing one launch or one executor observation across cells must fail closed. Intentional one-invocation fan-out requires explicit consumer/fanout identities and must not mint multiple execution credit.

Audit:

- `research_entity/global/j-space/research/2026-08-26_TRIGGER2_MODEL_CALL_CONTENT_VS_INVOCATION_IDENTITY_AUDIT_V1_GPT56SOL.json` — commit `71b7b10dafc715930948cc12cbc5f39277fdc322`

The falsified V60 regression was removed at commit `9b97e703397044bc9b7dcf9033ac9df8b76494f4`. Its corrected semantic successor is:

- `tests/test_trigger2_two_phase_call_content_vs_invocation_semantics_v1.py` — commit `4b705e086d65fe5b9cf4a7d1119b517deabf8cb3`

This successor encodes equal call-content across independent invocation authorities as allowed, while preserving replay/alias rejection for reused launch or executor-observation identity. A remaining membership-provenance discriminator is whether one `source_node_admission_id` can be projected onto two distinct nodes without an explicit multiplexing contract.

No execution claim is made for this new semantic test file yet.

## Training target remains binding/routing

Historical measured Trigger-2 baseline remains approximately:

- context-transfer: `0.5254629629629629`
- dynamic-symbol hit: `0.3611111111111111`
- three-way chance: `1/3`

The primary measured trainable deficit remains `CONTEXT_DEPENDENT_VARIABLE_BINDING_ROUTING`. Semantic readout, symbol writeout and carrier binding were not the primary measured bottleneck in the retained evidence scope.

`trigger2_binding_router_factorial_generator_v3.py` remains blocked from direct training for conditional nuisance leakage in codebook-order serialization. Do not materialize training from the leaky generator.

## Next source-only gate

Freeze the call-content-versus-invocation semantic contract in the fused path, then integrate the retained two-phase invocation authority with `PROOF_CARRYING_NODE_RESULT/v1` and the fused GRID10 membership/cohort source. Cross-validate node-admission identity/revision, node, process and generation against the proof-carrying membership envelope instead of relying on wrapper fields alone. Do not add artificial nonces to the call-content digest merely to force uniqueness.

P0 runtime quiescence still outranks all source work for any execution promotion.

## Credits remain zero at promotion scope

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V61_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_83_DELTA_2026-08-26T0435P0700_GPT56SOL.json`
