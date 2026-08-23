# MINI_ENTITY_EXECUTION_IDENTITY/v1

## Purpose

`MINI_ENTITY_EXECUTION_IDENTITY/v1` is the immutable build/launcher evidence boundary required before a post-turn `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` may truthfully claim exact source/runtime/artifact identity.

It is evidence only. It is not MiniUnifiedDB truth authority, model authority, J-Space/GWT authority, capability authority, or EffectGate authority.

## Authority law

The identity MUST be produced from trusted build/launcher facts outside mutable application profile data.

It MUST NOT be sourced from or overridden by:

- a MiniUnifiedDB application profile;
- model output or model self-report;
- J-Space/GWT state or observation;
- an effect result;
- arbitrary environment metadata not bound by the admitted launcher/build contract.

MiniUnifiedDB remains the sole canonical durable cognition/state authority. EffectGate remains the sole real-effect authority.

## Exact identity fields

The v1 object contains exactly:

- `schema = MINI_ENTITY_EXECUTION_IDENTITY/v1`;
- `source_commit` — exact clean source Git commit OID;
- `source_tree` — exact source Git tree OID;
- `source_dirty = false`;
- `runtime_module_digest` — SHA-256 of the admitted runtime module bytes;
- `artifact_sha256` — SHA-256 of the admitted packaged/runtime artifact;
- `mini_entity_version`;
- `entityos_version`;
- `source_lock_digest` — SHA-256 of the admitted boot source-lock material;
- non-empty unique `provenance_refs`;
- `authority = EXECUTION_EVIDENCE_ONLY_NO_TRUTH_STATE_EFFECT_AUTHORITY`;
- deterministic `identity_digest` over all preceding fields.

Unknown fields fail closed. Placeholder digests/OIDs fail closed. Dirty/unknown source fails closed.

## Canonical cognition ancestry binding

Before this identity can support a cognition-turn runtime receipt it MUST be cross-bound to the exact current MiniUnifiedDB prepare ancestry:

`MINI_ENTITY_EXECUTION_IDENTITY/v1`
`+ MiniUnifiedDB prepare(entity_generation, causal_turn_id, turn_binding_digest, boot_source_lock_digest)`
`-> MINI_ENTITY_BOUND_EXECUTION_IDENTITY/v1`

Required fences:

1. exact current `entity_generation`;
2. exact `causal_turn_id`;
3. exact `turn_binding_digest`;
4. execution `source_lock_digest == prepare.boot_source_lock_digest`.

The bound identity remains evidence-only and receives no truth/state/effect authority.

## Finalizer law

A post-commit Cognitive Fabric finalizer may consume a valid bound execution identity. It MUST NOT manufacture missing commit/tree/runtime/artifact/source-lock identities from profile fields, timestamps, model names, hashes of unrelated state, or plausible defaults.

If execution identity is absent, stale, dirty, malformed, or not bound to the same cognition prepare ancestry, final UCF evidence remains unavailable/failed. An already-successful MiniUnifiedDB commit is not rolled back or retried merely because terminal evidence finalization is incomplete.

## Build/launcher integration obligation

The admitted build/launcher path must eventually supply and persist the exact clean source commit/tree plus runtime/artifact/source-lock digests used for that process invocation. Package metadata from an older source head is not sufficient runtime attestation.

No runtime/model/J-Space/GWT/Claude/HCU or whole-product acceptance is implied by validation of this identity object alone.
