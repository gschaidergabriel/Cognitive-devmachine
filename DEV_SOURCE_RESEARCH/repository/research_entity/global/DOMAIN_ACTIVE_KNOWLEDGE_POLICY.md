# RAE Domain Active Knowledge Policy

## Purpose

Scientific domains must retain enough compact working knowledge to behave like persistent research programmes rather than thin wrappers around the latest report. Topic Packets and Knowledge Micro-Packets are the preferred active knowledge layer because they preserve compact, provenance-linked research state without forcing raw source files into every model context.

This policy makes domains deliberately **fleshier** while preserving token efficiency.

## Two-level knowledge model

Each branch maintains two distinct sets:

1. **indexed/reachable knowledge** — all discoverable branch research remains addressable through manifests, ledgers, source indexes and ClayGraph;
2. **active packet envelope** — a larger bounded set of Topic Packets and Knowledge Micro-Packets kept immediately visible to the research preflight.

Active does not mean true, canonical or promoted. Negative results, contradictions and unresolved hypotheses can be active and should often be prioritized precisely because they prevent repeated mistakes.

Raw files are expanded on demand. A worker must not blindly concatenate the entire active envelope into one prompt.

## Baseline active envelopes

Unless a trigger has a deeper dependency override, target branches keep approximately:

| Branch | Active Topic Packets | Active Knowledge Micro-Packets |
|---|---:|---:|
| clay | 48 | 96 |
| frank | 40 | 80 |
| claycode | 40 | 80 |
| claygraph | 48 | 96 |
| unifieddb | 48 | 96 |
| gwt | 32 | 64 |
| hyperposition | 32 | 64 |
| emergenz | 32 | 64 |

These are selection ceilings, not quotas that must be filled with low-value material.

## Deep dependency overrides

The following relationships intentionally maintain still richer envelopes:

- `frank <- clay`: 64 Topic / 128 Micro
- `frank <- claycode`: 64 / 128
- `frank <- claygraph`: 64 / 128
- `frank <- unifieddb`: 64 / 128
- `claycode <- frank`: 64 / 128
- `claycode <- claygraph`: 64 / 128
- `claycode <- unifieddb`: 56 / 112
- `gwt <- claygraph`: 56 / 112
- `gwt <- unifieddb`: 48 / 96
- `hyperposition <- claygraph`: 56 / 112
- `hyperposition <- unifieddb`: 48 / 96
- `claygraph <- unifieddb`: 64 / 128
- `unifieddb <- claygraph`: 64 / 128
- `unifieddb <- frank`: 64 / 128
- `unifieddb <- claycode`: 64 / 128
- `claygraph`: indexes the complete mesh but still marks a bounded high-priority active envelope for reasoning/self-use.
- `unifieddb`: indexes the complete mesh but keeps a bounded active envelope for store-role, query, migration, consistency and benchmark reasoning.
- `fusion`: indexes the complete mesh and uses branch active envelopes as its first reasoning layer before raw-evidence expansion.

## Selection priority

Within an envelope, selection is not pure recency. Prefer a balanced mixture of:

1. `CURRENT`, `OPEN`, `ACTIVE`, `IN_PROGRESS` material;
2. unresolved contradictions and supersession edges;
3. negative results / failed approaches that prevent rediscovery of dead ends;
4. active or high-information experiments and falsifiers;
5. architecture/state/interface packets with downstream dependencies;
6. recent cross-branch feedback packets;
7. older but still dependency-central packets.

`SUPERSEDED`, `REFUTED`, `ARCHIVED` or `STALE` material may remain active when it explains a contradiction, falsifier, migration rollback, safety boundary or current design decision. It is never silently treated as current truth.

## Diversity invariant

A branch envelope should not collapse to near-duplicate packets from one recent run. Where material exists, preserve representation of:

- claims/current model;
- open hypotheses;
- experiments/results;
- negative results;
- contradictions/supersessions;
- architecture/runtime constraints;
- cross-branch feedback;
- unresolved questions/falsifiers.

Shared evidence ancestry is still collapsed for evidential counting even when several descendant packets are active.

## Trigger behavior

`tools/research_interconnect_preflight.py` materializes the active packet envelope for every branch and records both active counts and total indexed candidate counts. The worker should:

1. reason first over active packet summaries/metadata;
2. use ClayGraph/SQLite/file search to expand only the paths needed to discriminate a hypothesis or resolve a contradiction;
3. promote newly useful compact findings into Topic/Micro-Packets so later runs benefit without rereading raw corpora;
4. demote redundant/stale packets from the active envelope without deleting their durable history.

## ClayGraph and UnifiedDB relationship

ClayGraph should eventually become a better selector for active associative memory envelopes. UnifiedDB should eventually provide a better logical persistence/query plane across authoritative and derived data classes. Neither result is assumed in advance.

ClayGraph self-use experiments should compare graph-selected assemblies against deterministic packet-envelope baselines on recall, precision, latency, token cost, multi-hop recovery and false association.

UnifiedDB self-use experiments should compare specialized-store baselines, logically unified routing, hybrid canonical-store/sidecar layouts and physical consolidation candidates on correctness/replay, snapshot consistency, latency/amplification, storage/memory, crash recovery, migration and selection integrity.

Activation/relevance never upgrades evidence status. Logical database unification never by itself justifies physical merge.

## Scientific and operational boundary

More active context is useful only if it increases retained constraints and useful associations without producing context bloat, stale anchoring or echo amplification. Each branch may experimentally tune its envelope sizes, but changes should be benchmarked and versioned rather than assumed beneficial.
