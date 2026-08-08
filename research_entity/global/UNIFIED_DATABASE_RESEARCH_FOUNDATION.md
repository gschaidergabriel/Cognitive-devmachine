# UnifiedDB Research Foundation — Unified Cognitive Database/Substrate

## Status

Project-owner research target. This document establishes a dedicated scientific branch for the **Unified Database** concept. It is a research programme, not a pre-approved implementation result.

Trigger word: `unifieddb`

## Core concept

Research whether FRANK can operate over **one logically unified, Clay-native cognitive data substrate** in which exact event/state truth, temporal history, relational/graph memory, vector/tensor semantics, provenance, uncertainty, goals, self/world state, GWT/Assembly state, activation/salience and effect/outcome receipts share one coherent semantic identity and query contract.

"Unified" does **not** mean "force every byte into one physical database". The branch must explicitly distinguish:

1. **semantic unification** — one type/identity/provenance system;
2. **logical query unification** — one typed query/transaction interface across data classes;
3. **physical storage unification** — optional and benchmark-gated;
4. **derived indexes/views** — rebuildable FTS/vector/graph/activation/materialized views;
5. **hard isolation boundaries** — retained where safety, capability, crash recovery, device constraints or external systems require them.

A valid research result may therefore conclude `KEEP_ISOLATED`, `UNIFY_LOGICALLY`, `COLOCATE_PHYSICALLY`, or a hybrid per store/data class.

## Seed architecture

The current seed comes from FRANK C6's Clay-Native Unified Cognitive Substrate and the existing ClayGraph/Hyperposition/ClayCode work:

`exact append-only events/state`
`-> typed Clay semantic identities + provenance + temporal validity`
`-> unified logical transaction/query plane`
`-> derived relational / graph / vector / FTS / activation views`
`-> bounded Assemblies / COVE / GWT`
`-> Clay-native model view`
`-> proposal`
`-> capability/effect gateway`
`-> outcome + re-entry`

The branch must test whether this architecture is actually better than coordinated specialized stores.

## Mandatory scientific questions

- Can one canonical semantic identity span exact state, event history, graph relations, vectors and GWT state without losing domain-specific information?
- Which objects must be canonical and which should remain derived/rebuildable?
- Can transactionality and causal snapshot identity span graph/vector/FTS/materialized views without excessive write amplification or latency?
- What consistency model is required for cognition-critical reads versus exploratory association?
- Can exact-address, relational, graph, vector and temporal retrieval share a planner while preserving selection provenance?
- When does physical consolidation reduce IPC/cache/serialization cost, and when does it worsen contention, crash radius, write amplification or recovery?
- How should epochs, MVCC/snapshots, outbox/effect receipts and re-entry interact?
- Can Android/edge deployments retain the same logical semantics with different physical lowerings?
- How are authority/capabilities kept outside non-authoritative graph/vector/activation layers?
- How can migration from existing FRANK stores be reversible and verified?

## Hard invariants

- canonical truth is not activation, embedding similarity, retrieval rank or model output;
- record provenance and selection/query-plan provenance are distinct;
- exact event/state history remains replayable and auditable;
- derived indexes are rebuildable from authoritative data or explicitly declare their independent authority;
- unknown consistency/alias/closure/selection integrity escalates rather than silently passing;
- physical colocation never changes semantic identity or grants authority;
- one unified API must not create one catastrophic common-mode failure domain without measured justification;
- migration is reversible until target live evidence justifies promotion;
- Synthetic/remote benchmarks do not become live FRANK evidence through repetition.

## Relationship to existing branches

### Clay
UnifiedDB is a persistence/query substrate input to the integrated foundry. Clay determines how the database interacts with the complete cognitive architecture.

### FRANK
FRANK consumes UnifiedDB architecture as a whole-system substrate and returns runtime/architecture requirements, live traces and migration constraints.

### ClayCode
ClayCode defines typed semantic/query/transaction/effect contracts and compiler lowerings for the UnifiedDB interface.

### ClayGraph
ClayGraph remains the specialist branch for associative graph memory, graph topology, activation and database-migration experiments. UnifiedDB researches how graph memory fits into a broader unified persistence/query system. Neither branch subsumes the other.

### Hyperposition
Hyperposition researches versioned semantic/coordination/physical topologies and supplies topology/epoch/firebreak constraints to UnifiedDB.

### GWT
GWT supplies cognition-critical snapshot, candidate-selection, projection, uptake and re-entry requirements. UnifiedDB supplies auditable candidate/query provenance and state snapshots.

### Emergenz
Emergenz uses UnifiedDB instrumentation only as a measurement substrate; database unification itself is not evidence of emergence or consciousness.

## Required empirical baselines

Every major architecture proposal should compare at least:

1. current coordinated/specialized-store baseline;
2. logically unified API over specialized stores;
3. hybrid shared canonical store + derived sidecars;
4. physically consolidated candidate where technically feasible.

Measure at minimum correctness/replay, p50/p95/p99 latency, write/read amplification, memory/storage, recovery/crash behavior, migration cost, token/context cost where model-facing, selection integrity, concurrent snapshot consistency and device/thermal/energy effects where applicable.

## Promotion boundary

This foundation creates a dedicated research branch. It does not promote a universal single-database implementation. Physical merge decisions remain evidence-driven and reversible.
