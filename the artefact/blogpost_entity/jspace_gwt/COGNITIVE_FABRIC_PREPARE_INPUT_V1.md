# COGNITIVE_FABRIC_PREPARE_INPUT/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Scope: the causal input boundary required before the retained reference runtime may implement a real `pipeline_cognitive_fabric_admit` handler.

## Observed current gap

At current Mini Entity source, `BLOGPOST_ENTITY.clay` calls `pipeline_cognitive_fabric_admit` with the ordinary phase envelope and a `data` map containing only the current `compiled` and `prompt` objects.

The current same-MiniUnifiedDB cognition store resolves pre-inference cognition identity with:

- exact live `entity_generation`;
- exact `causal_turn_id`;
- exact task text/hash;
- an already-bound generation-local boot binding;
- exact workspace digest;
- selected workspace slots;
- contradiction state;
- provenance refs;
- required Zero mode.

Therefore a runtime handler cannot safely complete the current contract merely by receiving `previous + compiled + prompt`. It would otherwise have to invent or guess causal/workspace identity after the admission boundary.

## Required pre-admission material

Before a real inference-bearing admission succeeds, the single canonical path MUST have an exact MiniUnifiedDB-bound prepare input containing at least:

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

## Causal rule

The preferred shape is:

```text
MiniUnifiedDB live generation
-> exact pre-existing/bound causal-turn + cognition prepare material
-> pipeline_build_prompt
-> pipeline_cognitive_fabric_admit
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> canonical UCF + boot ancestry validation
-> exact packet-bound inference/system/user
-> inference_generate
-> deterministic gate/CAS
-> final UCF runtime receipt
-> post-turn causal binding
```

The implementation MAY change the exact mechanical location at which the prepare material is fetched, but it MUST preserve one authority and one causal identity. A later explicit versioned contract may define a deterministic causal-turn derivation. Until then, the admission handler MUST NOT invent a turn id from `packet_hash`, generation, wall clock, random bytes or profile identity merely to satisfy the schema.

## Fail-closed requirements

A real `pipeline_cognitive_fabric_admit` implementation MUST fail before inference on at least:

- missing `causal_turn_id`;
- missing or mismatched task binding;
- missing turn binding;
- stale generation;
- missing boot binding;
- missing workspace digest;
- unbound selected workspace slots;
- missing required cognition-object identity;
- placeholder identity;
- profile-sourced replacement of a MiniUnifiedDB cognition identity;
- packet-v2 downstream-context mismatch;
- ABSTAINED capsule presented as executable inference admission.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`Cognition prepare material = candidate/provenance admission identity only`

`ZERO/J-Space/GWT/model output = candidate or measurement only`

`EffectGate = only real-effect authority`

This contract adds no second state, memory, UCF, recovery, packet or effect path.

## Acceptance boundary

This source contract does not implement the missing runtime handler and grants no bundled-0.8B, J-Space, GWT, Claude-adapter, HCU or whole Mini Entity runtime credit.

The next implementation gate is to make the canonical runtime receive/resolve this exact same-MiniUnifiedDB material, compile the existing ZERO capsule + packet-v2 ancestry, bind the exact downstream context, and then execute the integrated path on an actually-started authorized isolated executor.
