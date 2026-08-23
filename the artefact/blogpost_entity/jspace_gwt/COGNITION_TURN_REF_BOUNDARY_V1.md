# MINI_ENTITY_COGNITION_TURN_REF/v1

Status: **SOURCE/MECHANISM CANDIDATE · RUNTIME UNVERIFIED**  
Date: 2026-08-23  
Scope: the missing lookup boundary between the canonical `.clay` pipeline and the already-landed same-MiniUnifiedDB cognition turn binding.

## Finding

The current canonical pipeline calls Cognitive Fabric with `previous + compiled + prompt`, but `resolve_prepare_binding()` requires an exact live `entity_generation`, `causal_turn_id`, and original `task_text`. The existing source therefore cannot implement a real handler without inventing or guessing causal identity.

That is forbidden. In particular:

`packet_hash != causal_turn_id authority`

`generation != causal_turn_id authority`

`prompt.user != canonical task-binding authority`

`profile field != cognition identity authority`

## Minimal boundary

A caller may supply one **untrusted lookup assertion**:

```text
MINI_ENTITY_COGNITION_TURN_REF/v1 {
  causal_turn_id
  task_text
  task_sha256
}
```

The turn ref has **zero truth/state/effect authority**. It is admissible only when the retained runtime revalidates the supplied id + task text through `tools/miniunifieddb_cognition_store_v1.py::resolve_prepare_binding()` against the exact live MiniUnifiedDB generation.

Therefore:

```text
untrusted turn_ref
-> same-MiniUnifiedDB resolve_prepare_binding
-> exact boot/turn/workspace/cognition identities
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> candidate inference
-> deterministic gate/CAS
-> post-terminal UCF finalization
```

A wrong, stale, malformed, or unbound turn ref fails before inference. No fallback may derive a turn id from packet hash, canonical hash, profile identity, wall clock, randomness, or prompt text.

## Why this is not a second authority

The turn ref is equivalent to a lookup key supplied to a database: it identifies what the caller wants to use, but the database decides whether that exact object exists and is currently admissible. MiniUnifiedDB remains the sole durable authority.

No new database, transcript, memory, effect path, identity service, recovery ledger, or truth ledger is introduced.

## Integration obligation

This candidate does **not** declare the current runtime converged. The canonical `.clay` entry boundary still needs one versioned mechanism to carry the turn ref into Cognitive Fabric prepare/admission, and the retained Python runtime must call the same-store resolver before compiling the Zero capsule/packet.

Exact runtime/model/J-Space/GWT/Claude/HCU/whole-product credit remains **0** until actually-started authorized isolated execution on exact integrated bytes.

## Unusual experiment for this `go`

`PACKET_HASH_TURN_ALIAS_POISON` deliberately aliases `causal_turn_id = compiled.packet_hash`. The new source guard must reject that derivation. This is the single unusual intervention for this user-triggered macrocycle; other checks are deterministic regressions.
