# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V63** is the current research-ledger successor under Supervisor **8.83**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed

Owner FreeSwarm remains `HARD_OFF`. Latest retained committed telemetry reports OpenRouter `total_requests=4140`, `total_429=4005`, `total_success=134` and `go_swarm=RUNNING`, i.e. `+357/+357` request/429 drift relative to the already-failing Supervisor 8.83 snapshot. Provider/model/training execution remains closed.

Required closure remains owning-host identification and termination/quarantine of every provider-capable survivor without issuing a provider probe, zero provider-capable survivors, a bounded no-restart interval, and zero provider-counter delta. Only after that may current FREE non-provider execution authority be re-entered.

Pinned quiescence lane:

- enforcer source: `0d14624bf211e797936626e94c87459e37dd0cbb`
- execution request: `047962d015c6eb0e768df3eebbbc3aba91cf097f`
- frontier receipt: `8300bbd7cc7ef037b66fc5a0e84c5da945a3aa4d`

## Checkpoint-selection governance — frozen

The 512-case / 256-family four-quadrant logical manifest remains frozen and model outputs remain unopened. No checkpoint winner exists and checkpoint-selection credit remains `0`.

## V63 — membership incarnation gap closed at source structure

The retained two-phase invocation-authority source remains `tools/trigger2_node_result_model_call_two_phase_authority_v1.py`. Exact committed source-fixture validation from the prior stage remains bounded to `py_compile PASS` plus `9 passed in 0.03s`; it is not repository CI, provider/model runtime, physical GRID10, training, HCU or EntityOS acceptance.

V63 closes the remaining V62 cohort-level membership-incarnation source gap:

- source commit `1d9f5abfd032b01d5296f2d9a1ec68c669e981e1` adds `source_node_admission_id` to cohort-level uniqueness and rejects duplicate incarnation with `AUTHORITY_COHORT_NODE_ADMISSION_DUPLICATE`;
- regression commit `b8e0f7a98a9aeafbf9a14f87797351b996c92044` promotes the former strict xfail `test_one_node_admission_identity_cannot_be_projected_onto_two_nodes` into an ordinary regression expectation;
- no exact CI execution/status was observed for those new commits here, so runtime and repository-CI credit remain `0`.

The V61/V62 semantic correction is preserved: `source_bound_model_call_identity_sha256` is model-call **content/evidence identity**, not guaranteed unique invocation-event identity. Independent deterministic invocations may share equal call-content and output identities; invocation multiplicity is carried by distinct pre-call launch descriptors plus post-call executor observations. Reusing one launch or one executor observation across cells remains fail-closed. Intentional one-invocation fan-out requires explicit consumer identities and must not mint duplicate execution credit.

Duplicate PR `#2039` was closed unmerged as superseded after the same minimal membership-incarnation rule and regression were already present on current `main`; this preserves a single implementation lane.

## Next source discriminator — proof-carrying membership ↔ two-phase invocation fusion

The next source target is now:

`proof-carrying membership/admission incarnation -> pre-call launch -> call evidence -> post-call executor observation -> immutable NODE_RESULT -> two-phase authority envelope -> cohort reducer -> fused GRID10 coordinator persistence`

Before fused persistence, cross-validate all of the following against existing `PROOF_CARRYING_NODE_RESULT/v1` membership evidence rather than trusting wrapper fields alone:

- `source_node_admission_id` ↔ proof `source_membership_id`;
- admission revision/incarnation ↔ admitted membership revision/serial;
- controller node ↔ membership node ↔ raw `NODE_RESULT.source_node_id`;
- controller PID ↔ proof producer PID ↔ raw result process PID;
- runtime generation ↔ admitted membership/current generation;
- raw node-result packet digest ↔ proof node-result digest;
- whole cohort fails closed when any one member is stale, transplanted, duplicated or inconsistent.

Do **not** introduce another peer NODE_RESULT/model-call authority schema; compose the retained two-phase invocation authority with the existing proof-carrying membership authority and then bind the composed digest into fused cohort identity, persistence and replay checks.

## Training target remains binding/routing

Historical measured Trigger-2 baseline remains approximately context-transfer `0.5254629629629629`, dynamic-symbol hit `0.3611111111111111`, versus three-way chance `1/3`. The primary measured deficit remains `CONTEXT_DEPENDENT_VARIABLE_BINDING_ROUTING`; direct training remains blocked and the leaky binding-router factorial generator must not be materialized into training data.

## Credits remain zero at promotion scope

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V63_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_83_DELTA_2026-08-26T0435P0700_GPT56SOL.json`
