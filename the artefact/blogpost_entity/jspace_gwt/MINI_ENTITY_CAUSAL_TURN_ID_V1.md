# MINI_ENTITY_CAUSAL_TURN_ID/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

## Purpose

The retained Mini Entity reference runtime needs an exact pre-inference `causal_turn_id` before Cognitive Fabric admission can resolve the already-landed MiniUnifiedDB cognition turn binding. The current runtime does not receive such an id, and the canonical prepare-input contract correctly forbids inventing one from only `packet_hash`, generation, wall clock, random bytes, output id or profile identity.

This contract defines one deterministic identity rule from the **complete already-bound pre-inference turn material**. It adds no database, truth authority, effect authority, workspace producer or model authority.

Implementation:

`tools/mini_causal_turn_id_v1.py`

## Identity material

One v1 turn id binds exactly:

- schema `MINI_ENTITY_CAUSAL_TURN_ID/v1`;
- live `entity_generation`;
- exact admitted `boot_binding_digest`;
- SHA-256 of exact task text;
- exact `workspace_digest`;
- ordered `selected_workspace_slots`;
- `contradiction_state`;
- exact provenance refs;
- `required_zero_mode`;
- fixed candidate-only / no-direct-truth / no-direct-effect authority statement.

The canonical id is:

```text
ct1:<sha256(canonical_json(identity_material))>
```

This is a causal identity, not a truth score and not an effect capability.

## Retry / concurrency semantics

At one entity generation, byte-equivalent complete identity material denotes the same logical turn/retry and therefore derives the same id. This supports idempotent rebinding through the existing `mini_cognition_turn_bindings` table.

A change in task, boot identity, workspace identity/selection, contradiction state, provenance or required Zero mode derives a different id. Changed material may never be laundered through an old causal-turn identity.

Two intentionally distinct turns with exactly identical complete v1 material at the same generation are intentionally collapsed by this v1 rule. If product evidence later requires distinguishing them, that requires a **new versioned canonical nonce/allocation contract inside MiniUnifiedDB**; random or wall-clock entropy may not be silently added to v1.

## Same-store law

`bind_derived_turn()` computes the id and delegates persistence to the existing `miniunifieddb_cognition_store_v1.bind_turn()` API.

`resolve_derived_prepare_binding()` recomputes the id, resolves through the existing MiniUnifiedDB store and cross-checks the supplied boot/workspace/provenance/Zero-mode material against the resolved row.

No second table, state store, memory, UCF, recovery ledger or effect path is created.

## Fail-closed rules

The v1 identity path must fail before inference on:

- invalid generation type/range;
- malformed or placeholder boot/workspace digests;
- missing task text;
- malformed/duplicate workspace slot or provenance lists;
- empty contradiction state or required Zero mode;
- stale generation rejected by MiniUnifiedDB;
- missing already-bound turn;
- any resolved field that differs from the identity material.

## What this does **not** solve

This contract does **not** fabricate a workspace or select GWT slots. A real `pipeline_cognitive_fabric_admit/prepare` implementation still requires an admitted upstream workspace/turn producer that supplies the exact boot/workspace/provenance/Zero-mode material. Until that exists and exact source executes in an authorized isolated executor, the runtime handler must remain fail-closed and runtime credit remains zero.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`MINI_ENTITY_CAUSAL_TURN_ID/v1 = deterministic identity only`

`ZERO / bundled model / J-Space / GWT / HCU output = candidate or measurement only`

`EffectGate = only real-effect authority`

## Acceptance obligations

Before promotion into the real runtime path:

1. execute the exact helper + regressions in an actually-started authorized isolated executor;
2. integrate only with the single retained MiniUnifiedDB cognition store;
3. demonstrate idempotent exact retry and changed-material non-reuse;
4. bind the id through `ZERO_WORKSPACE_CAPSULE/v1 -> ZERO_INFERENCE_PACKET/v2`;
5. preserve deterministic gate/CAS and post-terminal final UCF-v1 receipt;
6. keep missing workspace/boot/turn material fail-closed rather than generating defaults.
