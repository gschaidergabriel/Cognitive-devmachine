# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V62** is the current research-ledger successor under Supervisor **8.83**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed

Owner FreeSwarm remains `HARD_OFF`. Latest retained V59 telemetry recorded OpenRouter `total_requests=4140`, `total_429=4005`, `total_success=134` and `go_swarm=RUNNING`, i.e. +357 requests and +357 429s relative to the Supervisor 8.83 snapshot. Provider/model/training execution remains closed.

Required closure remains owning-host identification and termination/quarantine of every provider-capable survivor, zero survivors, a bounded no-restart interval, and zero provider-counter delta without issuing a provider probe.

Pinned quiescence lane:

- enforcer source: `0d14624bf211e797936626e94c87459e37dd0cbb`
- execution request: `047962d015c6eb0e768df3eebbbc3aba91cf097f`
- frontier receipt: `8300bbd7cc7ef037b66fc5a0e84c5da945a3aa4d`

## Checkpoint-selection governance — frozen

The 512-case / 256-family four-quadrant logical manifest remains frozen and model outputs remain unopened. No checkpoint winner exists and checkpoint-selection credit remains `0`.

## V62 — two-phase invocation authority validated at source-fixture scope

Retained source direction:

- `tools/trigger2_node_result_model_call_two_phase_authority_v1.py` — commit `56e8cc09f0c1b8e1fd99ab091154c3f3a6382b17`
- exact fixture bytes aligned at `8f9789e49d6806d8d508233712fec3aa85d4e620`
- source validation receipt `research_entity/continuity/receipts/2026-08-26_TRIGGER2_TWO_PHASE_SOURCE_VALIDATION_GPT56SOL.json` — commit `e9292ea7857877ec1da972d43ee21e745a00fc66`

The receipt binds exact committed source/test bytes and records `py_compile PASS` plus `9 passed in 0.03s` on a local deterministic source fixture. Scope remains source/component only: no repository CI, provider/model runtime, actual pre-call freeze attestation, physical GRID10, training, HCU or EntityOS promotion.

The architecture is now explicitly phase-separated:

1. **pre-call launch authority** — `launch_descriptor_sha256` binds plan/cell/node/membership generation/process/candidate/input/source facts available before execution;
2. **post-call executor observation** — `executor_observation_sha256` binds that exact launch to model-call content/evidence, output and ABI receipt after execution;
3. **derived invocation provenance** — deterministic authority envelope around the immutable, authority-free `NODE_RESULT` packet.

## V62 semantic result — call content != invocation identity

The V60 hypothesis that `source_bound_model_call_identity_sha256` must be unique across independent invocations was falsified at the schema level and its regression was retired at `9b97e703397044bc9b7dcf9033ac9df8b76494f4`.

Corrected test source:

- `tests/test_trigger2_two_phase_call_content_vs_invocation_semantics_v1.py` — commit `4b705e086d65fe5b9cf4a7d1119b517deabf8cb3`

Current semantics:

- two independently attributed invocations may share equal call-content and output identities;
- reusing one launch descriptor across cells fails closed;
- reusing one executor observation across cells fails closed;
- equal model output does not collapse distinct invocation authority;
- intentional one-invocation fan-out must use explicit consumer identities and must not mint multiple execution credit.

## Remaining source discriminator

The remaining strict xfail is membership provenance: one `source_node_admission_id` must not silently represent two independent node memberships in one cohort unless an explicit multiplexing/fanout contract exists.

Next source target is therefore:

`membership/admission incarnation -> pre-call launch -> call evidence -> post-call executor observation -> immutable NODE_RESULT -> two-phase authority envelope -> cohort reducer -> fused GRID10 coordinator`

Cross-validate admission identity/revision, node, process and generation against the existing proof-carrying membership evidence rather than relying on wrapper fields alone.

## Training target remains binding/routing

Historical measured Trigger-2 baseline remains approximately context-transfer `0.5254629629629629`, dynamic-symbol hit `0.3611111111111111`, versus three-way chance `1/3`. The primary measured deficit remains `CONTEXT_DEPENDENT_VARIABLE_BINDING_ROUTING`; direct training remains blocked, and the leaky binding-router factorial generator must not be materialized into training data.

## Credits remain zero at promotion scope

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V62_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_83_DELTA_2026-08-26T0435P0700_GPT56SOL.json`
