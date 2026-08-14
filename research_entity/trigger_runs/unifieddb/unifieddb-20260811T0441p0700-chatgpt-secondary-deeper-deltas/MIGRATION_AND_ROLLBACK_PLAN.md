# MIGRATION AND ROLLBACK PLAN — deeper delta run

## Current decision
No canonical migration or target-runtime promotion from this run.

Keep the active lanes:
- PR #286 = fused current-system SQLite storage safety + U12 schema-pair certificate;
- PR #288 = alternative private fixed SQLite 3.53.4 WAL preflight;
- PR #280 = selected V17 V3 causal-support candidate;
- PR #281 = rollback-domain diagnostic.

Do not merge conclusions merely because mechanisms are individually green.

## Shadow additions proposed for the selected V17 lane
1. pre-action `EffectIntent/DecisionReceipt` candidate table/receipt;
2. explicit reconciler execution/recovery-admission binding distinct from origin execution;
3. durable order/sequence fields or references sufficient to prove pre-action vs post-outcome ordering;
4. immutable terminal closure receipt freezing validity-at-admission and typed learning mode.

All additions must remain candidate-only until target differential gates pass. Rollback is additive-table/trigger removal while canonical V14/V15/V16 remains intact.

## Storage A/B target experiment

### A — current system SQLite, DELETE + FULL
Run a disposable exact-current target branch with:
- U12 schema pair certificate;
- bounded ATTACH transaction committing one UnifiedDB semantic epoch plus Graph projection watermark/batch;
- kill/crash windows before/within/after commit;
- recovery and pair/freshness verification.

### B — private SQLite 3.53.4, WAL
After PR #288 exact loader/source-id preflight passes:
- same semantic workload;
- Graph asynchronous projection with strict watermark/freshness gate;
- equivalent crash/recovery matrix.

Compare correctness first, then latency/concurrency/resources.

## Rollback laws
- if private SQLite loader/source-id or current Frank regressions fail -> discard profile B; system packages unchanged;
- if ATTACH path raises p95/p99 or lock contention beyond accepted budget -> keep Graph async/rebuildable; do not weaken authority gates;
- if Graph freshness metadata causes availability coupling -> scope Graph admission to Graph-dependent queries only;
- if temporal V17 obligations overconstrain valid crash recovery -> loosen only through explicit typed recovery semantics, never through free-string/sentinel bypass;
- if external rollback authority unavailable -> fail closed or bounded read-only recovery; never silently lower monotonic floor.
