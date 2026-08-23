# MINI_COGNITIVE_FABRIC_CAPABILITY_ANCESTRY/v1

Status: **CURRENT PRE-INFERENCE FUSION CONTRACT CANDIDATE**  
Scope: exact provenance binding from the canonical `MINI_INFERENCE_BOUND_ROUTE/v1` into `mini-entity-cognitive-fabric-admission/v1`.

## Problem

Current `main` now has one cognition-bound capability route: `mini_inference_capability_binding_v1.resolve_bound_route()` combines the verified MiniUnifiedDB profile capability with current generation, causal turn, turn/boot/workspace identity and admitted cognition-object identities into one exact `route_digest`.

The remaining laundering risk is downstream: a pre-inference compositor can still reduce that bound route to only `target_engine_class + jspace_mode`. If so, two different capability receipts or cognition ancestries that happen to choose the same route tuple can collapse to the same admission ancestry.

## Required causal chain

```text
MiniUnifiedDB DB-resident profile snapshot
-> MINI_INFERENCE_CAPABILITY_BINDING/v1 validation
-> active MiniUnifiedDB cognition prepare material
-> MINI_INFERENCE_BOUND_ROUTE/v1
   [generation + causal turn + turn/boot/workspace
    + profile + capability binding/receipt
    + cognition artifact ancestry + route_digest]
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> mini-entity-cognitive-fabric-admission/v1
-> inference_generate
```

No second state, truth, inference, turn, recovery or effect authority is created.

## Required admission ancestry

A successful pre-inference admission MUST carry, both in its returned envelope and inside the exact receipt bytes hashed by `cognitive_fabric_receipt_digest`:

- `generation` exactly equal to bound-route generation;
- `profile_id` and exact verified `profile_hash`;
- `inference_route_digest` exactly equal to `MINI_INFERENCE_BOUND_ROUTE/v1.route_digest`;
- `capability_binding_digest` from the bound route;
- `capability_receipt_digest` from the bound route;
- `target_engine_class` exactly equal to the bound route;
- `jspace_mode` exactly equal to the bound route;
- exact `inference_packet_digest`;
- the remaining current MiniUnifiedDB turn/boot/workspace/model/J-Space provenance required by the parent admission contract.

The full bound route is the pre-inference routing identity. Engine/J-Space labels are descriptive route outputs and MUST NOT replace the route digest or capability evidence identities.

## Anti-laundering invariants

```text
DIFFERENT(MINI_INFERENCE_BOUND_ROUTE/v1.route_digest)
=> DIFFERENT admission ancestry
```

and specifically:

```text
SAME(target_engine_class, jspace_mode)
AND DIFFERENT(capability binding/receipt OR cognition ancestry)
=> DIFFERENT route_digest
=> DIFFERENT admission ancestry
```

Swapping capability evidence, generation/turn ancestry, model/J-Space cognition identity or any other route-bound material after route resolution MUST fail closed even when engine and J-Space mode remain unchanged.

## Profile, cognition and route fence

- the profile snapshot must come from the canonical MiniUnifiedDB profile-read boundary that re-hashes stored profile bytes;
- bound route generation/turn/boot/workspace/cognition identities must come from already-verified current MiniUnifiedDB prepare material;
- admission profile identity/hash must equal the bound route;
- provider/model/kind strings remain non-authorizing metadata;
- Claude Code remains `COMPILED_EXTERNAL` under the current capability contract;
- local latent/observe routing remains conditional on exact admitted capability evidence;
- no inference engine receives direct truth/state/effect authority.

## Validation helper

`tools/validate_cognitive_fabric_capability_ancestry_v1.py` is a composition-only fail-closed validator. It does not select a route and does not create canonical state.

It:

1. re-derives the exact `MINI_INFERENCE_BOUND_ROUTE/v1.route_digest` from route material;
2. verifies admission generation/profile/route/capability/engine/J-Space identity;
3. requires those same identities inside the exact admission receipt bytes;
4. re-derives `cognitive_fabric_receipt_digest`;
5. cross-binds the exact InferencePacket digest.

The helper is intended to be composed into the single retained pre-inference materializer/runtime handler. It is not a second Cognitive Fabric implementation.

## Failure obligations

At minimum fail closed on:

- missing/malformed/placeholder `inference_route_digest`;
- bound-route digest tamper;
- missing/malformed/placeholder capability binding or receipt digest;
- generation drift;
- profile id/hash drift;
- target engine drift;
- J-Space mode drift;
- admission receipt not carrying the same bound-route/capability identities;
- post-hoc mutation of admission receipt bytes;
- InferencePacket digest mismatch.

## Evidence boundary

Source presence and focused validator tests are component/mechanism evidence only. They grant zero reference-runtime, model, bundled-0.8B, J-Space, Whole-GWT, Claude-adapter, HCU-capacity or whole Mini Entity runtime credit.

Promotion requires the single retained `pipeline_cognitive_fabric_admit` runtime path to consume the canonical bound-route resolver, preserve `route_digest` plus capability identities inside the exact pre-inference receipt, validate this ancestry (or an equivalent fail-closed composition), and execute on exact source bytes in an actually-started authorized isolated executor.
