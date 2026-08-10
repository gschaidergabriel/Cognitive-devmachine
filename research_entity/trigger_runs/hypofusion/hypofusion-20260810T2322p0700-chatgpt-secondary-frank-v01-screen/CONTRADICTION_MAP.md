# Contradiction Map

## C1 — global epoch vs owned execution generation

**Internal conflict:** current V14 effect lifecycle can admit a caller that does not present session/client/lease ownership, while a global presence epoch may still be current. Existing strict replication shows stronger caller binding can fence this.

**Fusion:** observing the current epoch is state knowledge, not execution authority. Preserve current epoch as freshness evidence; require a non-forgeable caller-bound generation capability for effect admission.

**Still open:** whether the physical single-execution gate plus provider idempotency makes one of the three B1/B2/B3 checks redundant. Test rather than assume.

## C2 — structural IFC vs semantic influence

**Support side:** CaMeL/Fides show that data/control separation and deterministic labels can enforce strong safety properties.

**Counter side:** NeuroTaint argues that semantic transformation, causal influence and cross-session persistence exceed conventional taint propagation; AgentSys gains security by isolating memory contexts.

**Fusion:** hard labels/capabilities remain authoritative for effect decisions. Add a non-authoritative semantic provenance/audit layer to detect and study influence that hard enforcement does not model. Do not let semantic taint mint authority.

## C3 — semantic memory vs execution-state memory

**Support for execution state:** MAGE, ESAA and Context Folding all indicate value in explicit trajectory/branch/state management under long horizons.

**Counter:** semantic retrieval remains valuable for associative knowledge and may be cheaper on short tasks.

**Fusion:** dual plane. Execution lineage answers "what state/task generation am I in?" Semantic memory answers "what prior knowledge is relevant?" The active assembly must bind both to one epoch/provenance context.

## C4 — recurrence helps vs recurrence harms

**Support:** adaptive test-time compute, recurrent depth and learned termination can improve efficiency/quality.

**Counter:** loop instability, semantic livelock and shallow-wins results show more computation is not monotonic evidence of better reasoning.

**Fusion:** recurrence is a controllable resource, not a virtue. Continue only while expected verified outcome gain exceeds cost and instability; distinguish productive cycles from stalled/diverging regimes.

## C5 — explicit GWT vs emergent recurrent coordination

**Support:** bounded shared workspaces improve module coordination and cross-modal transfer in several controlled domains.

**Counter:** recurrent agents can develop useful partner models without dedicated specialist modules; shared memory/cross-attention may reproduce the same functional path.

**Fusion:** retain GWT only as an experimentally discriminable causal mechanism. The architectural claim requires selection -> broadcast -> receiver reconstruction/use -> outcome -> re-entry effects beyond information-equivalent baselines.

## C6 — hypergraph advantage vs pairwise sufficiency

**Support:** 2026 hypergraph systems show gains on higher-order relational and multi-agent tasks.

**Counter/boundary:** gains are task-dependent; stronger structured-support coverage can fail to increase final answer quality on some datasets.

**Fusion:** pairwise-first Hyperposition. Promote higher-order edges only when an irreducible interaction test predicts and then measures benefit.

## C7 — event sourcing vs simple transactional state

**Support:** append-only event lineage helps replay, audit, crash recovery and separation of probabilistic intention from deterministic mutation.

**Counter:** Frank v0.1 is a single server binary; universal event sourcing may create storage/query/implementation overhead.

**Fusion:** event-source authority-critical transitions only; use snapshots and rebuildable projections; permit ordinary mutable caches/projections where authority/replay is not needed. Benchmark against a simple SQLite baseline.

## C8 — rich typed cognition vs minimal compiled representation

**Support:** typed workflows/DSLs improve structured compliance in bounded tasks and match Frank's owner-fixed ClayCode-only target.

**Counter:** not every decision needs a heavyweight symbolic runtime; hidden-state routing and schema-constrained calls can be effective.

**Fusion:** semantic authority remains ClayCode; focus maximal typing on identity/provenance/effects/state transitions and compile aggressively elsewhere. Do not create a second hidden semantic architecture in host code.

## C9 — proactive autonomy vs liveness/goal drift

**Support:** persistent goals and goal evolution can improve long-horizon performance.

**Counter:** long-running agents can enter semantic livelock while appearing active; self-generated objectives can optimize proxies.

**Fusion:** proactive agency is allowed only through admitted persistent goals, bounded initiative, independent verified outcomes and a progress/liveness predicate. `idle` is a correct state when no useful opportunity exists.

## Highest-value unresolved contradictions

1. Is B1/B2/B3 triple effect fencing Pareto-superior to physical serialization + idempotency only?
2. Does Frank's explicit GWT cause useful outcome/re-entry effects beyond shared-memory/cross-attention?
3. Which interaction-order detector justifies Hyperposition hyperedge promotion without Goodharting on a synergy scalar?
4. Does selective event sourcing beat simple versioned SQLite under Frank's actual single-server workload and crash matrix?
5. Can bounded proactive agency increase verified useful work without increasing livelock, false reward or user-task interference?
