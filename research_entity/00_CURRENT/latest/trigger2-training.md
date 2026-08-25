# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V63** is the current research-ledger successor under Supervisor **8.84**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed

Owner FreeSwarm remains `HARD_OFF`. Latest committed telemetry observed here (`2026-08-25T22:43:16.216858Z`) reports `go_swarm=RUNNING` with embedded provider admission still at **8.78** and OpenRouter `total_requests=4230`, `total_429=4095`, `total_success=134`. Relative to the earlier Supervisor 8.83 counter snapshot (`3783/3648`), that is `+447/+447`. Supervisor 8.84 preserves the active runtime-quiescence failure, so provider/model/training promotion remains closed.

Required closure remains owning-host identification and termination/quarantine of every provider-capable survivor without issuing a provider probe, zero provider-capable survivors, a bounded no-restart interval, and zero provider-counter delta. Only after that may current FREE non-provider execution authority be re-entered.

Pinned quiescence lane:

- enforcer source: `0d14624bf211e797936626e94c87459e37dd0cbb`
- execution request: `047962d015c6eb0e768df3eebbbc3aba91cf097f`
- frontier receipt: `8300bbd7cc7ef037b66fc5a0e84c5da945a3aa4d`

## Checkpoint-selection governance — frozen

The 512-case / 256-family four-quadrant logical manifest remains frozen and model outputs remain unopened. No checkpoint winner exists and checkpoint-selection credit remains `0`.

## V63 — membership-incarnation closure plus fused two-phase adapter source

The retained phase-separated invocation authority remains `tools/trigger2_node_result_model_call_two_phase_authority_v1.py`. Supervisor 8.84 recognizes the exact committed-byte local deterministic source receipt (`py_compile PASS`, `9 passed in 0.03s`) only at source-fixture scope; it is not repository CI, model runtime, physical GRID10, training, HCU or EntityOS acceptance.

V63 closes the cohort-level membership-incarnation source gap:

- source commit `1d9f5abfd032b01d5296f2d9a1ec68c669e981e1` makes `source_node_admission_id` unique across independently attributed cohort members and rejects duplicate incarnation with `AUTHORITY_COHORT_NODE_ADMISSION_DUPLICATE`;
- regression commit `b8e0f7a98a9aeafbf9a14f87797351b996c92044` promotes the former strict xfail into an ordinary regression expectation;
- `source_bound_model_call_identity_sha256` remains model-call content/evidence identity, **not** unique invocation-event identity. Independent deterministic invocations may share call-content/output identities when launch descriptors and executor observations remain distinct.

Duplicate PR `#2039` was closed unmerged as superseded after the same membership-incarnation rule was already present on current `main`.

The next fusion source has also landed:

- adapter commit `925f1a70a538a834becedf9c11c7902d47f7ccc7`: `tools/trigger2_fused_membership_two_phase_adapter_v1.py`;
- test commit `49c24d7bf116e4363db168a0f4fb78673c96a45e`: `tests/test_trigger2_fused_membership_two_phase_adapter_v1.py`.

The adapter composes, rather than replaces, the two existing authorities. It cross-validates proof-carrying membership ID/serial, node, PID, generation, state identity and immutable NODE_RESULT digest against the retained two-phase invocation authority; adds the authority as a controller-owned extension; reseals the **existing** proof-envelope digest; then validates the ten-member phase cohort before delegating to the sole existing fused coordinator. Because the existing fused cohort ID, persistence and replay checks already commit to each proof-envelope digest, the resealed two-phase extension is transitively committed without minting a second coordinator cohort ID.

Current source tests additionally cover equal call-content/output across distinct invocations, membership ID/revision mismatch, node/generation mismatch, raw packet transplant, extension tamper, duplicate membership projection, transport-order invariance, and fail-before-delegate behavior. No exact execution result for these newly added adapter tests was observed here, so their runtime/CI credit is `0`.

## Next discriminator — exact real-fabric adapter acceptance

The next nonduplicate source discriminator is no longer another wrapper schema. It is an exact-current deterministic integration acceptance using the **real** `FusedFabric` path:

1. build ten proof-carrying membership envelopes from one current membership/snapshot cohort;
2. attach ten valid two-phase invocation authorities;
3. derive the expected fused cohort ID from the **resealed extended envelope digests**;
4. pass through `atomic_fused_two_phase_commit` into the actual existing `atomic_fused_cohort_commit`;
5. require one atomic `state_delta=1`, persisted extended envelope digests, and exact replay `state_delta=0`;
6. require one stale/transplanted/tampered member to fail **before** the existing coordinator mutates state;
7. keep all provider/model/physical-GRID10/training promotion credit at zero unless a separately admitted runtime gate later succeeds.

Do not create a second cohort ID, truth store, effect path, or peer NODE_RESULT/model-call authority schema.

## Training target remains binding/routing

Historical measured Trigger-2 baseline remains approximately context-transfer `0.5254629629629629`, dynamic-symbol hit `0.3611111111111111`, versus three-way chance `1/3`. The primary measured deficit remains `CONTEXT_DEPENDENT_VARIABLE_BINDING_ROUTING`; direct training remains blocked and the leaky binding-router factorial generator must not be materialized into training data.

## Credits remain zero at promotion scope

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- canonical semantics credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V63_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_84_DELTA_2026-08-26T0545P0700_GPT56SOL.json`
