# COGNITIVE_FABRIC_INVOCATION_SELECTOR/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Purpose: close the last caller-to-MiniUnifiedDB selection gap before a real `pipeline_cognitive_fabric_admit` implementation. This contract does not create a second turn ledger, workspace, identity authority, inference path or effect path.

## Observed exact gap

Current `BLOGPOST_ENTITY.clay::run(entity_db, source_db, secret_file)` reaches `pipeline_cognitive_fabric_admit` with `previous + compiled + prompt`, but no exact causal-turn selector or task text.

Current `tools/miniunifieddb_cognition_store_v1.py::resolve_prepare_binding(...)` requires:

- live `entity_generation`;
- exact `causal_turn_id`;
- exact `task_text` whose SHA-256 matches the stored turn binding.

The turn binding stores `task_sha256`, not the original task text. `ZERO_WORKSPACE_CAPSULE/v1` in turn requires the exact task text in its bounded task field. Therefore the admission handler cannot currently build the exact capsule by using only `previous + compiled + prompt` without sourcing or inventing material outside the canonical turn binding.

The runtime MUST NOT derive `causal_turn_id` from packet hash, generation, profile id, wall clock or random bytes merely to make the schema pass. It also MUST NOT replace exact MiniUnifiedDB cognition identities with mutable profile/chat values.

## Minimal invocation selector

A pipeline invocation may carry only this bounded selector:

```text
MINI_COGNITIVE_INVOCATION/v1 {
    expected_generation
    causal_turn_id
    task_text
    turn_binding_digest
}
```

This selector is **not authority**. It may select only material that is already bound in MiniUnifiedDB.

Admission procedure:

1. read the live generation from canonical MiniUnifiedDB;
2. require `expected_generation == live_generation`;
3. call the same-store cognition resolver using `live_generation + causal_turn_id + task_text`;
4. require the returned `turn_binding_digest` equals the selector digest;
5. reconstruct/verify the persisted turn and boot binding digests before using any returned field;
6. obtain all Zero/GRF/Hyperposition/model/tokenizer/J-Space/lens/workspace/policy identities only from the verified MiniUnifiedDB binding;
7. compile `ZERO_WORKSPACE_CAPSULE/v1` from that exact material and the verified task text;
8. compile `ZERO_INFERENCE_PACKET/v2` against the exact downstream inference/system/user context;
9. only then return a pre-inference candidate admission envelope.

A caller therefore chooses an already-admitted causal turn but cannot mint or mutate its cognition/workspace authority.

## Upstream binding requirement

Before an inference-bearing invocation is allowed, a canonical Zero/workspace scheduler must already have created the exact boot and turn bindings in MiniUnifiedDB. The invocation selector does not create them.

If no exact bound turn exists, admission fails closed or returns a typed abstention where the existing capsule/packet contracts permit it. It does not fabricate a turn.

## Engine / J-Space selection

The selector MUST NOT carry engine capability, J-Space mode, model digest, lens identity, policy authority or workspace fields.

Engine routing may use the canonical DB profile together with an admitted capability/J-Space object, but the real handler must fail closed until those versioned payload semantics are explicitly resolved. It must not infer latent-access capability from provider/model names.

## Required fail-closed cases

- missing/malformed selector;
- stale `expected_generation`;
- missing causal turn;
- task hash mismatch;
- turn binding digest mismatch;
- persisted turn/boot digest reconstruction mismatch;
- missing boot binding;
- missing/admission-invalid cognition object;
- missing workspace digest or selected slots;
- placeholder digest;
- profile/chat replacement of cognition identity;
- unbound/unsupported engine capability or J-Space mode;
- packet-v2 downstream-context mismatch;
- ABSTAINED capsule presented as executable inference;
- final UCF runtime receipt attempted before inference + deterministic gate + commit-or-explicit-no-commit.

## Causal shape

```text
MiniUnifiedDB live generation
-> pre-existing boot + turn/workspace binding
-> bounded invocation selector
-> build_prompt
-> pipeline_cognitive_fabric_admit
-> verified binding resolver
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> exact context-bound inference
-> deterministic gate/CAS
-> commit or explicit no-commit
-> final UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1
-> post-turn causal binding
```

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`Invocation selector = routing key into already-bound canonical material only`

`Zero/J-Space/GWT/model output = candidate or measurement only`

`EffectGate = only real-effect authority`

## Acceptance boundary

This contract is a source-level integration discriminator only. It grants zero runtime/model/bundled-0.8B/J-Space/GWT/Claude/HCU/whole-product credit until exact integrated bytes execute in an actually-started authorized isolated executor.
