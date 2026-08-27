# UnifiedDB U10 — Epoch-Versioned State Continuity Candidate

## Result
Current UnifiedDB is not yet sufficient evidence for arbitrary exact epoch replay. A concrete current-schema falsifier was reproduced locally: after one prior row already has `status='SUPERSEDED'`, attempting to supersede a second historical version of the same `(record_kind, record_key, scope)` violates the current UNIQUE constraint. Mutable `world_state` likewise retains only the latest row in the tested update path.

## Candidate
Use one authoritative SQLite/WAL canonical transaction plane on the single target VPS, but make semantic state append-only by epoch. Keep current heads as derived transactional pointers. Bind every authoritative commit to `tx_id`, `state_epoch`, root hash, and (when executing Frank work) current `execution_id/lease_epoch`. Publish ClayGraph/vector/FTS as rebuildable projections with explicit source epoch and readiness.

## Why hybrid, not one physical mega-store
The target has one active Frank execution lease, making SQLite's single-writer model attractive for canonical state. But graph activation and vector/tensor indexes are non-authoritative and may enlarge common-mode crash/recovery risk. They stay logically unified and epoch-bound while physical colocation remains benchmark-gated.

## Local evidence
- Current `semantic_records`: second same-key transition to `SUPERSEDED` -> UNIQUE constraint failure.
- Current mutable `world_state`: two states -> one remaining row; no point-in-time reconstruction from that table alone.
- U10 reduced prototype: epochs 1/2/3 replayed exactly as sun/rain/cloud.
- stale base writer rejected.
- uncommitted transaction vanished after connection close; `integrity_check=ok`.
- five counterbalanced FULL+WAL local microbench runs: mutable p50 ~715.8 us, append-only versioned p50 ~651.8 us; p95 ~1502 vs ~1573 us; versioned p99 worse (~11339 vs ~6962 us). This is local synthetic evidence only.

## Promotion gate
Do not promote on these local results. Next exact-source target-VPS run must test: simultaneous/stale lease writes, crash/restart, WAL FULL durability, online backup/restore, FK+integrity checks, projection lag/rebuild, replay hash equivalence, idempotency, p50/p95/p99, WAL/write amplification, DB growth, and resource shadows.

## Architecture decision
- Semantic/logical unification: SUPPORT.
- Canonical SQLite physical colocation for authoritative state/transactions/lease/effect-outcome-reentry: TESTING CANDIDATE.
- Physical graph/vector/tensor consolidation: HOLD / KEEP_ISOLATED until differential target evidence.
