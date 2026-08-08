# KMP — Android R1 -> Clay feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** clay  
**Platform boundary:** Linux-primary; Android-secondary

## Current feedback

Android is a constrained-runtime falsification and efficiency arm for Clay, not a replacement target architecture. Android experiments must preserve canonical Clay semantics while measuring representation density, parsing/allocation cost, bounded-view memory pressure, safe-effect behavior and reconstruction/replay cost.

The first live ARM Android Test Lab smoke execution established that a constructed typed ClayCode semantic subset can execute with deterministic assertion and unknown-reference rejection. This is implementation-path evidence only; it does not prove full Clay semantics or Linux equivalence.

## Retrieval/emit rule

Clay runs MUST retrieve materially relevant Android `GENERALIZABLE_CANDIDATE` findings. Android runs MUST retrieve current Clay architecture before testing. Android-specific effects remain labeled Android provenance until Linux replication.

## Next Clay-facing falsifiers

- bounded Clay/MOSAIC view size vs context/RAM/latency on target Qwen-class 4B;
- compact semantic density vs parser/decoder cost at matched correctness;
- safe-effect and canonical replay invariants under Android process interruption;
- Linux-vs-Android differential equivalence before cross-platform promotion.
