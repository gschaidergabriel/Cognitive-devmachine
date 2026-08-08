# KMP — Android R1 -> Hyperposition feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** hyperposition

## Current feedback

Android is a constrained substrate for testing whether physical/process placement assumptions remain beneficial under tight memory and latency budgets. R1 does not yet establish a Hyperposition mechanism; it establishes the executable ARM Android lane.

## Retrieval/emit rule

Hyperposition runs MUST retrieve Android placement/IPC/rematerialization findings when material. Android runs MUST retrieve current Hyperposition topology/firebreak contracts before changing component placement.

## Next Hyperposition-facing falsifiers

- same-process versus IPC boundary cost on Android;
- compact typed handles versus copied rich payloads;
- resident versus rematerialized state under memory pressure;
- topology changes must preserve authority and semantic firebreaks;
- general placement claims require matched Linux replication.
