# COGNITIVE_FABRIC_PREPARE_INPUT/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Scope: the exact causal input boundary required before the retained reference runtime may execute a pre-inference Cognitive Fabric prepare/admission step.

## Temporal authority correction

The pre-inference prepare/admission identity and the final `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` are **different causal objects**.

The final UCF-v1 runtime receipt contains execution/result/authority fields and therefore MUST NOT exist before inference and the deterministic gate/commit-or-no-commit terminal state.

Accordingly:

- `ZERO_WORKSPACE_CAPSULE/v1` and `ZERO_INFERENCE_PACKET/v2` are pre-inference admission material;
- exact packet-v2 downstream-context validation is a pre-inference fence;
- `validate_zero_ucf_capsule_chain_v2.py`, because it composes the final UCF-v1 + boot validator, is post-turn causal evidence/verification and MUST NOT be used to mint a pre-inference final UCF receipt;
- source work that restores `prepare -> inference -> gate/commit -> finalize` is the temporally correct direction.

## Observed current gap

The currently landed source lineage still exposes an older one-phase cognition call shape in `BLOGPOST_ENTITY.clay`, while the current same-MiniUnifiedDB cognition store resolves pre-inference identity with:

- exact live `entity_generation`;
- exact `causal_turn_id`;
- exact task text/hash;
- an already-bound generation-local boot binding;
- exact workspace digest;
- selected workspace slots;
- contradiction state;
- provenance refs;
- required Zero mode.

A real pre-inference handler cannot safely complete that contract from only `previous + compiled + prompt`. It would otherwise have to invent or guess causal/workspace identity.

## Required prepare material

Before inference-bearing prepare/admission succeeds, the single canonical path MUST have exact MiniUnifiedDB-bound material containing at least:

```text
entity_generation
causal_turn_id
task_text_or_exact_task_sha256
turn_binding_digest
boot_binding_digest
workspace_digest
selected_workspace_slots
contradiction_state
provenance_refs
required_zero_mode
zero_identity_digest
grf_digest
hyperposition_digest
bundled_manifest_digest
local_model_digest
tokenizer_digest
jspace_profile_digest
jacobian_lens_digest
workspace_calibration_digest
boot_source_lock_digest
policy_authority_digest
```

The authoritative source for these identities is the current MiniUnifiedDB cognition binding store, not mutable profile fields, model output, chat history, prompt text, guessed defaults or placeholder digests.

## Canonical causal rule

The target sequence is:

```text
MiniUnifiedDB live generation
-> exact pre-existing/bound causal-turn + cognition prepare material
-> pipeline_build_prompt
-> pipeline_cognitive_fabric_prepare
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> packet-v2 exact downstream-context validation
-> exact packet-bound inference/system/user
-> inference_generate
-> deterministic gate
-> MiniUnifiedDB CAS commit OR explicit no-commit terminal state
-> pipeline_cognitive_fabric_finalize
-> final UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1
-> ZERO/UCF/boot/packet-v2 post-turn causal validation
-> post-turn causal binding
```

The exact phase names may only change through a versioned canonical source contract, but the temporal authority above is invariant: final UCF runtime receipt after terminal outcome, never before inference.

A later explicit versioned contract may define deterministic causal-turn derivation. Until then, the prepare handler MUST NOT invent a turn id from `packet_hash`, generation, wall clock, random bytes or profile identity merely to satisfy the schema.

## Fail-closed requirements

A real pre-inference prepare/admission implementation MUST fail before inference on at least:

- missing `causal_turn_id`;
- missing or mismatched task binding;
- missing turn binding;
- stale generation;
- missing or integrity-invalid boot binding;
- missing workspace digest;
- unbound selected workspace slots;
- missing required cognition-object identity;
- placeholder identity;
- profile-sourced replacement of a MiniUnifiedDB cognition identity;
- packet-v2 downstream-context mismatch;
- ABSTAINED capsule presented as executable inference admission.

Finalization MUST fail closed when terminal gate/commit state, final UCF receipt ancestry, or post-turn packet/context binding is malformed or inconsistent.

## Read-integrity prerequisite

The currently landed MiniUnifiedDB cognition store also requires read-time reconstruction/verification of persisted boot and turn binding digests before its resolved prepare material can be trusted by the runtime handler. A stored row must not become admitted merely because an old binding digest remains present beside mutated fields.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`Cognition prepare material = candidate/provenance admission identity only`

`ZERO/J-Space/GWT/model output = candidate or measurement only`

`EffectGate = only real-effect authority`

`Final UCF runtime receipt = post-turn causal evidence, not pre-inference authority`

This contract adds no second state, memory, UCF, recovery, packet or effect path.

## Acceptance boundary

This source contract does not implement the missing prepare/finalize runtime handlers and grants no bundled-0.8B, J-Space, GWT, Claude-adapter, HCU or whole Mini Entity runtime credit.

Next gates:

1. repair read-time cognition binding digest verification in the single MiniUnifiedDB store;
2. converge the canonical source to the two-phase prepare/finalize temporal order without raw inference bypass;
3. implement the retained reference runtime prepare/finalize handlers using exact same-MiniUnifiedDB material and packet-v2 downstream binding;
4. execute exact integrated bytes on an actually-started authorized isolated executor.
