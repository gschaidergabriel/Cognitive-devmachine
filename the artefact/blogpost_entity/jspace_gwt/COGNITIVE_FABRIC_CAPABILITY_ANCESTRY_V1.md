# MINI_COGNITIVE_FABRIC_CAPABILITY_ANCESTRY/v1

Status: **CURRENT PRE-INFERENCE FUSION CONTRACT CANDIDATE**  
Scope: exact provenance binding between the admitted `MINI_INFERENCE_CAPABILITY_BINDING/v1` route and `mini-entity-cognitive-fabric-admission/v1`.

## Problem

`target_engine_class + jspace_mode` are not sufficient provenance identities. Two different capability evidence receipts can legitimately resolve to the same route tuple. If the pre-inference admission carries only that tuple, capability evidence can be replaced or laundered without changing the admission ancestry.

The merged capability binder prevents provider/model names from minting J-Space capability. This contract preserves that evidence identity through the next boundary.

## Required causal chain

```text
MiniUnifiedDB DB-resident profile snapshot
-> MINI_INFERENCE_CAPABILITY_BINDING/v1 validation
-> exact capability binding digest + capability receipt digest
-> active MiniUnifiedDB cognition prepare material
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> mini-entity-cognitive-fabric-admission/v1
-> inference_generate
```

No second state, truth, inference, turn, recovery or effect authority is created.

## Required admission ancestry

A successful pre-inference admission MUST carry, both in its returned envelope and inside the exact receipt bytes hashed by `cognitive_fabric_receipt_digest`:

- `generation`;
- `profile_id`;
- exact verified `profile_hash`;
- `capability_binding_digest` = exact `MINI_INFERENCE_CAPABILITY_BINDING/v1` binding digest;
- `capability_receipt_digest` = exact evidence receipt digest validated by that binding;
- `target_engine_class` exactly equal to the validated capability result;
- `jspace_mode` exactly equal to the validated capability result;
- exact `inference_packet_digest`;
- the remaining current MiniUnifiedDB turn/boot/workspace/model/J-Space provenance required by the parent admission contract.

If a separate generation/turn/cognition-bound route digest is materialized, the admission MUST bind that exact digest too; such a route digest may strengthen but may not replace capability evidence identity.

## Anti-laundering invariant

```text
SAME(target_engine_class, jspace_mode)
AND DIFFERENT(capability_binding_digest OR capability_receipt_digest)
=> DIFFERENT admission ancestry
```

Swapping capability evidence after admission, even when the route tuple is unchanged, MUST fail closed.

## Profile and route fence

- the profile snapshot must come from the canonical MiniUnifiedDB profile read boundary, which re-hashes stored profile bytes;
- admission profile identity/hash must equal the validated capability profile identity/hash;
- provider/model/kind strings remain non-authorizing metadata;
- Claude Code remains `COMPILED_EXTERNAL` under the current capability contract;
- local latent/observe routing remains conditional on the exact capability evidence accepted by `MINI_INFERENCE_CAPABILITY_BINDING/v1`;
- no inference engine receives direct truth/state/effect authority.

## Validation helper

`tools/validate_cognitive_fabric_capability_ancestry_v1.py` is a composition-only fail-closed validator. It does not select a route and does not create canonical state. It checks exact profile, capability, route, packet and admission-receipt identity and re-derives the admission receipt digest.

The helper is intended to be composed into the single retained pre-inference materializer/runtime handler. It is not a second Cognitive Fabric implementation.

## Failure obligations

At minimum, fail closed on:

- missing/malformed/placeholder capability binding digest;
- missing/malformed/placeholder capability receipt digest;
- profile id/hash drift;
- target engine drift;
- J-Space mode drift;
- admission receipt not carrying the same capability identities;
- post-hoc mutation of admission receipt bytes;
- InferencePacket digest mismatch.

## Evidence boundary

Source presence and focused validator tests are component/mechanism evidence only. They grant zero reference-runtime, model, bundled-0.8B, J-Space, Whole-GWT, Claude-adapter, HCU-capacity or whole Mini Entity runtime credit.

Promotion requires the single retained `pipeline_cognitive_fabric_admit` runtime path to consume the merged capability binder, preserve these identities inside the exact pre-inference receipt, and execute on exact source bytes in an actually-started authorized isolated executor.
