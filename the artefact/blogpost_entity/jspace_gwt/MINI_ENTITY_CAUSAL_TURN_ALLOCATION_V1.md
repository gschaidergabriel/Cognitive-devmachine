# MINIUNIFIEDDB_CAUSAL_TURN_ALLOCATION/v1

Status: **SOURCE / COMPONENT MECHANISM CANDIDATE — RUNTIME UNVERIFIED**

## Purpose

Give every logical Mini Entity turn a distinct causal **event identity** without deriving event identity from task/workspace/model content and without creating a second turn/state authority.

The canonical allocator lives inside the same MiniUnifiedDB. It only allocates an event namespace. The existing cognition turn binding remains the canonical binding of task/workspace/boot material to that event.

## Why content-derived causal IDs are rejected

A content digest answers “is this material identical?” It does not answer “is this the same event?”. Two deliberately separate turns can be byte-identical, especially after REJECT/BLOCKED/no-commit outcomes where the entity generation may remain unchanged.

Therefore:

`CAUSAL_EVENT_ID != TURN_MATERIAL_DIGEST`

`IDENTICAL_MATERIAL != SAME_EVENT`

A content-derived `ct1:<sha256(material)>` would collapse distinct identical turns in one generation into an idempotent replay and is not admitted as canonical causal identity.

## Allocation contract

`allocate_causal_turn(db, entity_generation, provenance_refs)` appends one immutable row in `mini_cognition_turn_allocations` and returns:

- `causal_turn_id = ct1:<allocation_id>`;
- live `entity_generation`;
- immutable allocation provenance;
- an `allocation_digest` over schema + allocation id + generation + provenance.

Every allocation is a new event, even when task/workspace material later proves identical to another event.

Retries MUST reuse a previously returned `causal_turn_id`. Calling the allocator again means “allocate a new logical event”.

## Atomic canonical path

The preferred upstream scheduler transaction is:

```text
BEGIN IMMEDIATE
-> allocate_causal_turn              # new event identity in MiniUnifiedDB
-> cognition_store.bind_turn         # exact task/workspace/boot material on that id
-> active_turn.activate_bound_turn   # exactly one active turn for live generation
-> COMMIT
```

If allocation or binding fails, roll back the transaction. An allocation row that is not bound cannot be activated and grants no inference/truth/effect authority.

The runtime pre-inference path then becomes:

```text
pipeline_build_prompt
-> pipeline_cognitive_fabric_admit
-> active_turn.resolve_active_prepare
-> cognition_store.resolve_prepare_binding
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> exact admitted candidate inference
```

The runtime handler MUST NOT allocate a new turn merely to satisfy PREPARE, and MUST NOT derive a causal id from packet hash, generation, wall clock, random bytes, profile id, task text or workspace content.

## Selector / active-pointer fusion

Current canonical `BLOGPOST_ENTITY.clay` passes `MINI_COGNITIVE_INVOCATION/v1` into `pipeline_cognitive_fabric_admit`. That pass-through is compatible with one-authority semantics only when the selector is a **read-only cross-check**, not a second lookup or allocation authority.

The upstream scheduler uses the selector identity to activate an already **allocated and bound** turn before the Clay run. At PREPARE, the handler MUST:

1. resolve the generation-bound Active Cognition Turn from MiniUnifiedDB using the read-only active-turn resolver;
2. require selector `expected_generation` equals the live generation;
3. require selector `causal_turn_id`, exact `task_text` and `turn_binding_digest` equal the resolved active turn;
4. reject missing/mismatched selector or missing active pointer before inference;
5. never allocate, bind or activate a turn inside PREPARE.

Direct selector -> cognition-store resolution that bypasses the active pointer is non-canonical because it would leave two competing runtime selection paths. Direct selector-to-inference bypass is also non-canonical.

Thus there is one runtime selection path:

`allocated turn -> bound turn -> active pointer -> PREPARE resolver`,

with the Clay-supplied selector serving only as an integrity assertion over that already-active identity.

## Authority

- MiniUnifiedDB: sole canonical durable state/evidence/configuration/turn authority.
- Allocation row: event identity namespace only.
- Turn binding: material/provenance binding for that event.
- Active pointer: generation-scoped selection/index only.
- Zero/J-Space/GWT/model: candidate or measurement only.
- EffectGate: only real-effect authority.

## Recovery / replay

A caller that receives an allocation and retries the same logical event reuses that causal id. A caller that deliberately starts a new logical turn allocates a new id, even if all content is identical.

Allocation + bind + activation SHOULD share one caller-owned transaction so a crash before commit cannot publish a partial event. Unknown or stale allocations are never guessed or reused by content similarity.

## Acceptance boundary

This contract and its deterministic component regressions do not establish the real `pipeline_cognitive_fabric_admit` handler, bundled ~0.8B runtime, J-Space/GWT causal use, Claude adapter, HCU runtime fit or whole Mini Entity acceptance. Exact integrated bytes still require actually-started authorized isolated execution.
