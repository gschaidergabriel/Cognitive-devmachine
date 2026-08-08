# KMP — Android R1 -> ClayGraph feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** claygraph

## Current feedback

Android R1 does not yet test ClayGraph activation or traversal. It establishes an ARM execution lane and a constructed canonical-replay control useful for later process-death/rebuild experiments.

Android is especially useful for measuring sparse activation, bounded Assembly memory, conditional graph traversal and rebuild/rematerialization costs under constrained RAM.

## Retrieval/emit rule

ClayGraph runs MUST retrieve Android graph/memory efficiency results when material. Android runs MUST retrieve current ClayGraph semantic epoch, activation, Assembly and provenance contracts before graph experiments.

## Next ClayGraph-facing falsifiers

- sparse activation + conditional traversal versus always-traverse;
- immutable epoch/rebuild after Android process death;
- compact relation/index representations under matched recall;
- salience/activation never gains truth or effect authority;
- Linux replication required for general graph-runtime claims.
