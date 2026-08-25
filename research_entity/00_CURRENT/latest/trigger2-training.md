# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V70** is the current research-ledger successor under Supervisor **8.84**. This is a cache pointer only; newest explicit owner/supervisor authority and exact executable evidence outrank it.

## P0 — runtime quiescence actively failed with direct counter movement

Owner FreeSwarm remains `HARD_OFF`, but committed shared provider-budget telemetry still advanced. Over the latest observed committed window, OpenRouter changed:

- `total_requests`: **4230 → 4317** (`+87`)
- `total_429`: **4095 → 4182** (`+87`)
- `total_success`: **134 → 134**

Classification remains `ACTIVE_FAIL_POST_STOP_PROVIDER_ATTEMPT_COUNTERS_INCREASING`. This is evidence of continued provider-attempt activity, not a scientific negative about model/EntityOS behavior and not authorization to issue a provider probe.

Provider/model/physical-GRID10/training promotion remains closed. Required closure: zero provider-capable survivors, zero unexpired provider-budget leases and a bounded zero provider-counter delta without probing a provider; only then re-enter explicit FREE non-provider execution authority.

## Retained invocation/fusion source chain

- `tools/trigger2_node_result_model_call_two_phase_authority_v1.py`
- `tools/trigger2_fused_membership_two_phase_adapter_v1.py`
- content identity may repeat across deterministic invocations;
- invocation-event authority is separate pre-call launch plus post-call executor observation;
- membership/node/PID/generation/state/NODE_RESULT provenance is cross-bound before fusion;
- current main freezes one deep-copied envelope cohort before validation and delegates that same snapshot, closing mutable validation/use drift at source level.

All remains source/component evidence only.

## V67 — physical proof-origin gap pinned

Retained fail-closed regression:

- `tests/test_trigger2_physical_cohort_proof_origin_boundary_v1.py`

Blocker: `CALLER_FORGEABLE_PHYSICAL_COHORT_PROOF_DICTIONARY`.

A synthetic all-true proof must fail before `fused_cohort_admissions`, `admitted_results` or epoch mutation. Physical GRID10 credit remains `0`.

## V68–V70 — pidfd witness frontier

Committed donor candidate:

- `tools/trigger2_physical_witness_capability_v1.py`
- `tests/test_trigger2_physical_witness_capability_v1.py`

Useful retained primitive: `pidfd` as a nonserializable process-incarnation/liveness handle plus explicit `SOURCE_FIXTURE_ONLY` zero-credit receipt typing.

The candidate is **not** physical authority. It still accepts caller-supplied marker/FD/S1/predicate mappings and is not integrated into the sole retained `FusedFabric.atomic_fused_cohort_commit` physical mutation entry.

A temporal audit found an additional blocker: `spawn_held_cohort` currently returns only after barrier release plus `communicate`/wait/reap. Therefore minting pidfds from the returned proof is too late to establish the intended barrier-time process provenance.

### Higher-information Linux discriminator

During the live barrier, acquire one pidfd per child and use `pidfd_getfd` on the observed target S1 descriptor. Inside the same observer-owned authority boundary:

1. stat the canonical S1 path;
2. duplicate each child's actual target fd via the pidfd-referenced process;
3. locally `fstat` and `F_GETFL` the duplicate;
4. require device+inode equality and read-only access mode;
5. bind process incarnation, actual S1 descriptor identity, ready marker, generation/epoch/state identity and a pre-release exact NODE_RESULT/packet commitment;
6. after release, require exact packet/read-receipt equality before the sole physical mutation path is reachable;
7. fail closed on unavailable kernel/permission support instead of falling back to caller-supplied evidence.

This remains source/research direction only. Physical-proof-boundary closure remains `0`.

## Training — Qwen3.5-0.8B binding/remap discriminator

Current training hypothesis: the highest-value trainable deficit is episode-local **BIND / ROUTE / REMAP**, not semantic readout alone.

Gated curriculum retained:

- B0: separate semantic READ and symbol WRITE baselines;
- B1: arbitrary episode-local binding with full S3/counterbalanced nuisance crossing;
- B2: semantic-prior override plus mid-episode remapping and stale-binding rejection;
- B3: multi-hop dereference;
- B4: delay/interference capacity curves;
- B5: variable-N and cell-permutation equivariance;
- B6: DB-vs-simulation, Claude Code handoff/re-entry, Hyperposition/evidence authority.

No aggregate checkpoint score may hide a mandatory-axis failure. Exact rendered-byte leakage/nuisance/equivariance gates, family-disjoint frozen holdouts and retention floors remain prerequisites.

Training materialization remains closed: admitted rows `0`, accepted dataset tokens `0`, checkpoint outputs unopened, checkpoint winner `null`, training credit `0`.

## Next exact gate

P0: close owning-host runtime quiescence without a provider probe.

P1 source: restructure the retained held-cohort lifecycle so pidfds, actual S1 descriptor binding and a complete packet commitment are sealed **before release/reap**; then require that observation-bound capability at the sole physical FusedFabric mutation entry and keep `SOURCE_FIXTURE_ONLY` structurally disjoint from `PHYSICAL_OBSERVED`.

P2 training: retain B1+B2 as the first small family-disjoint pilot only after runtime authority and exact ABI/tokenizer/rendered-byte gates permit deterministic materialization.

## Credits

- accepted dataset tokens: `0`
- checkpoint winner: `null`
- checkpoint/model-call runtime credit: `0`
- physical GRID10 promotion credit: `0`
- physical proof boundary closed: `0`
- runtime quiescence credit: `0`
- J-Space model credit: `0`
- training credit: `0`
- canonical semantics credit: `0`
- whole HCU runtime credit: `0`
- whole EntityOS runtime credit: `0`

Current ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V70_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_84_DELTA_2026-08-26T0545P0700_GPT56SOL.json`
