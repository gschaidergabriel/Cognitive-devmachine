# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V66** is the current research-ledger successor under Supervisor **8.84**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed

Owner FreeSwarm remains `HARD_OFF`. Latest committed telemetry carried forward from V65 reports `supervisor=STOPPED/QUARANTINED`, `go_swarm=RUNNING`, embedded provider admission still at **8.78**, and OpenRouter counters still advancing after stop. Supervisor 8.84 therefore preserves `ACTIVE_FAIL_POST_STOP_PROVIDER_ATTEMPT_COUNTERS_INCREASING`; provider/model/physical-GRID10/training promotion remains closed.

Required closure remains owning-host identification and termination/quarantine of every provider-capable survivor **without issuing a provider probe**, zero provider-capable survivors, a bounded no-restart interval, and zero provider-counter delta. Only after that may current FREE non-provider execution authority be re-entered.

## Retained V65 source chain

Retained invocation/fusion authority remains:

- `tools/trigger2_node_result_model_call_two_phase_authority_v1.py`
- `tools/trigger2_fused_membership_two_phase_adapter_v1.py`
- call-content identity may repeat across independent deterministic invocations;
- invocation-event authority is distinct pre-call `launch_descriptor_sha256` plus post-call `executor_observation_sha256`;
- membership ID/revision, node, PID, generation, state and immutable NODE_RESULT identity are cross-bound before fusion;
- the adapter embeds authority into `authority_extensions`, reseals the existing proof envelope, and delegates only to the sole `FusedFabric.atomic_fused_cohort_commit` path.

Exact committed-byte adapter regression receipt remains **24 passed in 0.06s**, source-fixture scope only. No provider/model/physical-GRID10/VPS/training execution was performed and all promotion credits remain `0`.

## V66 — caller-forgeable physical proof boundary

A stronger source blocker was found while re-entering the newly landed real-`FusedFabric` source-path integration test.

`FusedFabric.atomic_fused_cohort_commit` currently receives an ordinary caller-supplied `proof` dictionary and accepts the physical-cohort gate by checking boolean/value fields such as:

- `all_alive_at_barrier`
- `distinct_os_pids == 10`
- `parent_child_pid_binding`
- `same_snapshot_identity`
- `all_transactions_open_at_barrier`
- `all_hold_readonly_s1_fd_at_barrier`
- `writer_free_identity_stable`
- `process_intervals_overlap_release`
- `ready_by_node` PID/read-receipt/snapshot markers

The current source-path integration fixture `tests/test_trigger2_fused_membership_two_phase_real_fabric_source_v1.py` deliberately constructs `_synthetic_source_proof(...)`, sets those physical predicates to `True`, and uses deterministic packet PIDs `9001..9010`. This is acceptable only as a deterministic composition test of the real persistence code. It also demonstrates that the physical evidence boundary itself is not source-enforced: correctly shaped caller data is currently treated as equivalent to an observed physical witness.

Blocker ID: `CALLER_FORGEABLE_PHYSICAL_COHORT_PROOF_DICTIONARY`.

Counterhypothesis: the dict is intended to be internal/trusted output of `spawn_held_cohort`. Current adjudication: that convention is insufficient for Clay's fail-closed evidence authority because the public source boundary does not verify trusted construction/provenance, and the source test itself traverses it with synthetic evidence.

Therefore:

- the real-`FusedFabric` source-path test may establish persistence/composition semantics only after exact execution;
- it cannot establish physical GRID10 evidence;
- physical GRID10 promotion credit remains `0`;
- no model/J-Space/training/HCU/EntityOS runtime credit changes.

## Next discriminator

Split source-fixture composition from physical witness admission.

1. Physical commit path must reject raw or explicitly synthetic proof data as physical evidence.
2. Introduce an explicit typed/opaque physical witness provenance boundary minted by the retained physical observation path.
3. Bind that witness to exact node/PID/read-receipt/snapshot/barrier observations.
4. Preserve a separate source-fixture-only path for deterministic adapter persistence/replay testing whose receipts are structurally incapable of claiming physical runtime credit.
5. Add a regression proving an all-true synthetic proof cannot mutate physical-cohort state.
6. Only with an exact-current dependency tree execute the retained adapter through the actual physical witness path and require commit `state_delta=1`, identical replay `state_delta=0`, persisted resealed envelope-digest equality, fail-before-mutation on tamper, and transport-order invariance.

## Checkpoint/training governance remains frozen

The 512-case / 256-family four-quadrant logical checkpoint manifest remains frozen and outputs remain unopened. No checkpoint winner exists. Direct training remains blocked; accepted dataset tokens remain `0`.

## Credits

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- canonical semantics credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V66_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_84_DELTA_2026-08-26T0545P0700_GPT56SOL.json`
