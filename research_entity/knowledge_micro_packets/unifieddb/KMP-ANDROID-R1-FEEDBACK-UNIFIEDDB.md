# KMP — Android R1 -> UnifiedDB feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** unifieddb  
**Evidence class:** live Firebase Test Lab virtual ARM + constructed replay control

## R1 evidence receipt

On both Android 30 and Android 35 virtual ARM runtimes, repeated replay of the same constructed canonical event sequence produced equal state, while a missing-tail damaged sequence produced a distinguishable result. This was one of 9/9 passing controls per device in the R1 cross-version matrix.

This is **not production UnifiedDB persistence evidence**: no SQLite/embedded transaction log, process kill/restart, checkpoint, query planner or sidecar rebuild was exercised.

## Retrieval/emit rule

UnifiedDB runs MUST retrieve this Android feedback. Android storage experiments MUST retrieve current logical/physical, collection/query identity and recovery contracts. Logical semantics must be held fixed when comparing Android and Linux physical backends.

## Next UnifiedDB-facing falsifiers

- canonical event replay after real Android process kill/restart;
- typed query/collection equivalence on embedded SQLite/storage;
- damaged derived sidecar detection and rebuild;
- write amplification, checkpoint and storage-pressure measurements;
- cross-platform differential before promoting any Android-local backend optimization.
