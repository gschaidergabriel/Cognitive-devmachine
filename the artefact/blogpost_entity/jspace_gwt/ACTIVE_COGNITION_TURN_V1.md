# ACTIVE_COGNITION_TURN/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Scope: the same-MiniUnifiedDB selection boundary that makes one already-bound causal turn resolvable by `pipeline_cognitive_fabric_admit` without inventing causal identity inside the runtime handler.

## Problem

The current canonical `.clay` path reaches `pipeline_cognitive_fabric_admit` after `pipeline_build_prompt`, but the admitted Cognitive Fabric prepare contract requires an exact pre-existing `causal_turn_id`, task binding, workspace binding and cognition boot binding. The handler must not synthesize these from generation, packet hash, wall clock, randomness, profile identity or prompt content.

`miniunifieddb_cognition_store_v1.py` already owns the causal-turn binding. What is missing is a deterministic way to identify which existing bound turn is the one active for the live entity generation.

## One-authority law

`tools/miniunifieddb_active_turn_v1.py` adds one generation-scoped pointer table **inside the same MiniUnifiedDB**.

It does not create:

- a second turn ledger;
- a second task store;
- a second truth/state authority;
- a second recovery ledger;
- a second effect path;
- a generated causal-turn identity.

The canonical turn material remains `mini_cognition_turn_bindings`. The active-turn row is only a fail-closed selection/index over one exact existing binding.

## Activation rule

A turn may become active only when all of the following already exist and match:

- live `entity_state.generation`;
- caller-supplied `causal_turn_id` already present in `mini_cognition_turn_bindings`;
- exact expected `turn_binding_digest`;
- exact task text whose SHA-256 equals the already-bound task hash;
- non-empty provenance refs.

No turn id is derived by this module.

Exactly one active pointer is allowed per entity generation. Repeating the exact same activation is idempotent; a conflicting second activation in the same generation fails closed.

## Prepare resolution

`resolve_active_prepare`:

1. verifies the requested generation is still live;
2. re-hashes retained task text and checks it against the active row;
3. re-checks the referenced canonical turn binding and task hash;
4. delegates to `miniunifieddb_cognition_store_v1.resolve_prepare_binding` for the authoritative boot/turn/workspace/cognition identities;
5. requires that resolver to return the same exact turn binding and task hash;
6. returns that canonical prepare material plus the activation identity and exact task text.

This gives `pipeline_cognitive_fabric_admit` a safe lookup point, but does not itself implement the handler or run inference.

## Causal shape

```text
external/admitted turn creation
-> MiniUnifiedDB bind_turn
-> ACTIVE_COGNITION_TURN/v1 activate exact existing turn
-> pipeline_build_prompt
-> pipeline_cognitive_fabric_admit resolves active prepare
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2 exact downstream-context binding
-> inference_generate
-> deterministic gate + MiniUnifiedDB CAS
-> final UCF runtime receipt
-> post-turn causal binding
```

The upstream mechanism that creates/binds the causal turn remains a separate required contract. This pointer does not define that missing creator.

## Fail-closed requirements

At minimum fail on:

- missing canonical cognition turn-binding table;
- stale generation;
- missing referenced turn;
- mismatched turn-binding digest;
- task text/hash mismatch;
- second different active turn in one generation;
- post-activation task tampering;
- canonical turn-binding drift;
- cognition-store resolver returning a different turn or task binding.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration/turn authority`

`Active cognition turn = selection/index only`

`Zero/J-Space/GWT/model = candidate or measurement only`

`EffectGate = only real-effect authority`

## Acceptance boundary

Source presence plus focused component tests grants no Mini Entity runtime, bundled-0.8B, J-Space, Whole-GWT, Claude-adapter or HCU runtime credit.

The next gate is to connect an admitted upstream turn creator/binder to this pointer and make the retained `ProfilePipelineRuntime.pipeline_cognitive_fabric_admit` resolve it before compiling the existing Zero capsule + packet-v2 path, followed by actually-started authorized isolated exact-source execution.
