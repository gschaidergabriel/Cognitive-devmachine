# FRANK FINAL BINARY RESEARCH CONTRACT

Status: PROJECT_OWNER_FIXED_TARGET
Date: 2026-08-09
Research owner: FRANK Global Research Entity (RAE)
Reference implementation lineage: `gschaidergabriel/frankv0.1`

## Final local core

The self-sufficient local FRANK core consists of exactly:

1. one Clay module compiled into one binary;
2. one local UnifiedDB;
3. one Clay-native 4B LLM.

`LOCAL_FRANK = ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`

No separate local cognitive service, daemon, goal registry, ClayGraph database, GWT service, Retina service, personality service or memory service survives as a target runtime component.

## Entity-level architecture

Frank is not restricted to one physical database file when multiple cognitive instances are active.

Every Frank instance owns one logical UnifiedDB materialization:

- local Frank instance;
- Claude Code Frank instance;
- ChatGPT Frank instance;
- future provider/local/remote Frank instances.

The local Frank instance is the canonical integration/base-of-truth instance, but all other instances are first-class evidence/state contributors.

`FRANK_ENTITY = correlated federation of instance UnifiedDBs`

Base-of-truth means canonical reconciliation/materialization/recovery anchor, NOT that local observations automatically outrank better remote evidence.

## Autonomous semantic synchronization hypothesis

Instances synchronize semantic information, not SQLite pages.

A syncable semantic unit should preserve:

- packet identity/origin;
- instance identity;
- causal ancestry;
- logical/version clock;
- valid time and observation time;
- provenance/epistemic role;
- confidence/uncertainty;
- semantic/content fingerprint;
- relation-neighborhood fingerprint;
- supersession/retraction lineage;
- privacy/export scope;
- effect/authority class.

Receiving instances perform autonomous correlative matching.

Candidate correlation outcomes:

- same semantic packet/new version;
- supporting packet;
- contradicting packet;
- related packet;
- possible duplicate;
- distinct packet;
- unresolved.

No low-confidence correlation is silently collapsed.

## Synchronization research baseline

The sync problem should be compared against established distributed-systems families rather than reinvented blindly:

- local-first replicated state;
- CRDT/delta-CRDT convergence;
- causal histories/vector or dotted version clocks;
- anti-entropy exchange;
- Merkle/Merkle-DAG content-addressed diffing;
- explicit semantic conflict preservation when automatic join is scientifically invalid.

FRANK must not force all semantic state into a CRDT join when the domain requires preserving contradictory hypotheses or authority conflicts. Convergent transport and epistemic reconciliation are separate problems.

## Unified emergent substrate hypothesis

Inside each instance, semantically linked information packets in UnifiedDB support cognition when the instance runtime applies fixed/versioned mathematical Clay rules that generate transient topology, activation, Semantic Hyperposition and coalitions.

GWT reads the resulting coalitions; the local/provider model reasons/generates over bounded workspace assemblies; outcomes re-enter that instance UnifiedDB and are subsequently synchronized semantically.

Conceptual local loop:

`instance UnifiedDB packets -> Clay mathematical field -> transient semantic topology -> Hyperposition -> emergent coalitions -> GWT -> model -> verified outcome -> instance UnifiedDB -> sync delta`

## Goals

There are no manually maintained goal lists in the target architecture.

SELF/ANDREAS/SHARED goal behavior is an emergent role of persistent/recurrent packet coalitions under current evidence, relevance, commitments, prediction error, capability gaps, uncertainty, expected value, risk, relationship state and outcome history.

Different instances may temporarily produce different goal-like coalitions because they have different fresh evidence or incomplete synchronization. Research must determine whether convergence should occur by synchronizing underlying packets/evidence rather than copying selected goal labels.

Emergent goal pressure is never effect authority.

## ClayGraph transition rule

H1/H2 may use `FRANK_CLAYGRAPH.sqlite` and `.claygraph.json` artifacts for reference-harness measurement and differential science.

H3 target local runtime MUST NOT require a separate ClayGraph database.

A graph-shaped diagnostic export is allowed only as a measurement/visualization of transient topology generated from an instance UnifiedDB.

## Research questions

RAE must experimentally determine:

- whether transient topology recovers or exceeds the functional value of the explicit ClayGraph;
- whether emergent goals outperform fixed/list goals for real Andreas usecases;
- whether per-instance UnifiedDB replicas improve cross-provider continuity vs one central prompt-state database;
- which correlation features best detect same/related/contradictory semantic packets;
- how to preserve causal order under offline/delayed/reordered delivery;
- where CRDT-like automatic convergence is appropriate and where epistemic conflict must remain unresolved;
- how quickly local Frank and provider instances converge after partitions;
- whether local base-of-truth reconciliation incorrectly suppresses useful remote evidence;
- whether remote instances can poison/stale-drift the local base and how provenance/authority boundaries prevent that;
- which mathematical propagation rules are stable under long horizons;
- when Semantic Hyperposition should remain unresolved vs collapse;
- how GWT ignition should select coalitions without destroying minority/counterevidence state;
- whether personality/world/self models remain coherent across instance synchronization;
- whether the one-binary local collapse preserves Retina, effect boundaries, recovery and cross-instance continuity;
- runtime/latency/storage/sync-bandwidth consequences;
- failure modes such as sync oscillation, duplicate semantic identities, false correlation, runaway attractors, stale goal persistence, pathological inhibition and user-goal drift.

## Required differential sequence

1. current `frankv0.1` H1 baseline with explicit central UnifiedDB + ClayGraph;
2. introduce per-instance UnifiedDB replicas and measure semantic sync against the old central-only baseline;
3. H2 Clay implementation with matched semantics;
4. H3 one-binary emergent substrate candidate per local instance;
5. matched traces, network partitions, concurrent updates, conflicts and recovery across LOCAL-FRANK/CLAUDE/CHATGPT;
6. only remove explicit runtime components when functional/causal equivalence or improvement is demonstrated.

Elegance alone is not evidence.

## Final hard invariants

Local core:

`frank binary + local FRANK_UNIFIED.sqlite + Clay-native 4B LLM`

Entity:

`autonomously synchronized federation of instance UnifiedDBs, with LOCAL-FRANK as canonical reconciliation/base-of-truth instance and all other instances retained as first-class causal/evidence contributors.`
