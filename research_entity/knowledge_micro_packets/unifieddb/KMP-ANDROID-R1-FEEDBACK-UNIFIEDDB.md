# KMP — Android R1 -> UnifiedDB feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** unifieddb

## Current feedback

Android R1 includes a constructed canonical-event replay control but does not yet establish a production UnifiedDB backend result. Android is a useful constrained laboratory for event-spine replay, SQLite/embedded query semantics, write amplification, checkpointing and sidecar rebuild costs.

## Retrieval/emit rule

UnifiedDB runs MUST retrieve Android storage/query/replay findings when material. Android runs MUST retrieve current UnifiedDB logical/physical, collection/query identity and recovery contracts before persistence experiments.

## Next UnifiedDB-facing falsifiers

- canonical event replay after process kill/restart;
- typed query/collection equivalence on embedded Android storage;
- damaged derived sidecar detection and rebuild;
- write amplification/checkpoint/storage pressure;
- logical semantics held fixed across Android and Linux physical backends before cross-platform promotion.
