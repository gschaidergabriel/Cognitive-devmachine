# MINI_ENTITY_CAUSAL_TURN_ALLOCATION/v1

Status: **SOURCE CANDIDATE / RUNTIME UNVERIFIED**

## Problem

`causal_turn_id` is an event identity. It must not be derived only from task/workspace/content material.

Two deliberately separate turns can be byte-identical while still being different causal events. If content-equivalent turns receive the same id, outcomes, retries, UCF ancestry, recovery state, and effect provenance can be collapsed onto the wrong event.

Therefore:

```text
same content != same causal event
```

and:

```text
content hash MUST NOT be causal event identity
```

## v1 rule

The canonical MiniUnifiedDB allocates one monotone turn identity for each newly admitted causal event:

```text
ct1:g<entity_generation>:a<allocation_id>
```

`allocation_id` is allocated by SQLite `INTEGER PRIMARY KEY AUTOINCREMENT` in the same MiniUnifiedDB. It is not model-generated, wall-clock-derived, random, provider-derived, or inferred from task content.

The allocation and the immutable `mini_cognition_turn_bindings` write occur atomically. If binding fails, the new allocation rolls back. A caller-owned transaction is protected by a savepoint so failure cannot strand a partially allocated turn.

## New event versus retry

A new call to `allocate_and_bind_turn(...)` means a **new causal event**, even when task/workspace/boot/provenance bytes equal an earlier turn.

A retry of an already admitted event must carry the previously allocated `causal_turn_id` and use `bind_existing_turn(...)`. Existing MiniUnifiedDB binding collision checks then reject changed material being laundered through the old id.

This intentionally does not guess whether two identical invocations are retries. Without a durable event identity, that distinction is not recoverable from content alone.

## Recovery boundary

If a runtime loses the returned `causal_turn_id` and later submits byte-identical material as a fresh allocation, v1 treats that submission as a new event. Exact crash/retry deduplication therefore requires the surrounding canonical ingress/effect lifecycle to persist and replay the allocated id. v1 does not manufacture idempotency from content similarity.

This is safer than silently merging two potentially distinct events.

## Authority

- MiniUnifiedDB remains the only durable state/evidence/configuration authority.
- This allocation table lives inside that same MiniUnifiedDB and is identity metadata only.
- Zero/model/J-Space/GWT/HCU outputs remain candidate or measurement only.
- EffectGate remains the only real-effect authority.
- No second state store, identity service, truth ledger, UCF, recovery ledger, or effect path is introduced.

## Fail-closed obligations

The path must reject before inference when:

- entity generation is stale or malformed;
- canonical cognition-store schema is absent;
- foreign-key enforcement is not active on the connection;
- boot/workspace/provenance/Zero-mode material fails the existing turn-binding contract;
- an explicit retry references an unallocated id;
- an explicit retry changes any already-bound turn material.

## Required regressions

1. two byte-identical new turns allocate different causal ids;
2. explicit retry reuses one existing id and remains idempotent;
3. changed material cannot reuse an existing id;
4. failed binding rolls back the allocation;
5. stale generation cannot allocate;
6. outer transaction rollback removes both allocation and binding.

## Evidence boundary

The source candidate is implemented in `tools/mini_causal_turn_allocation_v1.py` with focused regressions in `tests/test_mini_causal_turn_allocation_v1.py`.

No actually-started authorized isolated executor was available to this organ at creation time. Therefore this candidate has **zero runtime/model/J-Space/GWT/Claude/HCU/whole-product execution credit** until exact-source execution is observed.

## Integration gate

A real `pipeline_cognitive_fabric_admit` path may use this allocator only after admitted boot/workspace/provenance material exists. It must then propagate the allocated `causal_turn_id` through:

```text
MiniUnifiedDB turn binding
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> Unified Cognitive Fabric admission
-> inference
-> deterministic gate/commit
-> terminal UCF receipt/recovery
```

No handler may derive event identity from packet hash, prompt hash, profile id, provider id, wall clock, random bytes, or model output.
