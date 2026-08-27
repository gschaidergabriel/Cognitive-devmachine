# Hyperposition H2 Hypothesis Matrix

All hypotheses are OPEN unless explicitly marked as a bounded synthetic negative result. No live-FRANK truth is promoted.

1. **H-HYP2-001 — Three-topology separation.** Semantic dependency, coordination/invariant interference and physical locality are distinct topologies. Falsifier: one topology predicts the other two without material loss across representative workloads.
2. **H-HYP2-002 — Delta/coordination separation.** Negative or replacing deltas do not intrinsically require global synchronization. Falsifier: every non-monotone transition requires global ordering for correctness.
3. **H-HYP2-003 — Invariant-scoped closure.** Coordination can be limited to the smallest sound invariant-conflict scope. Falsifier: scoped closure violates invariants even with complete scope knowledge.
4. **H-HYP2-004 — Scope inference is safety-critical.** Missing a true interference edge causes unsafe concurrency. Falsifier: deliberate scope omissions preserve all tested invariants.
5. **H-HYP2-005 — Central closure queue phase change.** Global closure develops severe tail latency near service saturation even when semantic work is partitionable. Falsifier: tail latency remains comparable to scoped closure under saturation.
6. **H-HYP2-006 — Relation identity is canonical.** N-ary relation-instance identity + roles preserves semantics across storage backends. Falsifier: equal-semantics roundtrip differs between compliant encodings.
7. **H-HYP2-007 — Pairwise flattening is a projection only.** Pairwise edges without relation-instance identity generate spurious n-ary reconstructions. Bounded counterexample already supports this; live relevance remains open.
8. **H-HYP2-008 — Native hyperedges are optional.** Reified relation nodes can preserve canonical semantics when event identity/roles are explicit. Falsifier: some required FRANK semantics cannot be represented without native hyperedges.
9. **H-HYP2-009 — Signed delta algebra is portable.** ADD/RETRACT/REPLACE/COMPENSATE can form a backend-neutral transition contract. Falsifier: a target backend needs destructive mutation semantics that cannot be losslessly expressed this way.
10. **H-HYP2-010 — Revocation must retain lineage.** Negative deltas should preserve causal/provenance ancestry rather than erase history. Falsifier: destructive deletion preserves every recovery/audit requirement.
11. **H-HYP2-011 — Adaptive rebuild crossover.** Incremental propagation beats rebuild only below workload-specific impact thresholds. Bounded synthetic evidence supports this; target crossover remains open.
12. **H-HYP2-012 — Cascade tails predict crossover better than mean fanout.** q95/q99 touched-state fraction improves mode selection. Falsifier: mean fanout alone matches or beats tail-aware routing.
13. **H-HYP2-013 — Physical colocation is conditional.** Strong semantic coupling does not imply shared-memory colocation when coherence/contended cache lines dominate. Falsifier: colocating semantically related state always improves end-to-end performance.
14. **H-HYP2-014 — Decentralization can dominate zero-copy.** Removing centralized scheduling/coordination can yield larger latency wins than copy elimination in some regimes. Falsifier: copy cost dominates all representative FRANK hot paths.
15. **H-HYP2-015 — Batching can trade mean for tail.** Batched atomics/cache-line transfers can improve throughput while worsening worst-case latency. Falsifier: batching improves all latency quantiles monotonically.
16. **H-HYP2-016 — Coordination topology is n-ary.** One invariant may couple multiple semantic regions and should be representable as a higher-order interference relation. Falsifier: every invariant scope reduces losslessly to independent pairwise locks.
17. **H-HYP2-017 — Effect authority is orthogonal.** A transition can be computationally monotone and coordination-free yet still require external capability authorization. Falsifier: semantic/coordination classification fully predicts effect authority.
18. **H-HYP2-018 — Projection crash recovery.** Disposable active topologies can be destroyed and rebuilt from canonical events without loss of authority history. Falsifier: any required truth exists only in derived projection state.
19. **H-HYP2-019 — Scope-fuzzing is a promotion gate.** Selective closure should not be promoted until randomized reorder/partition/concurrency tests fail to find invariant violations. Falsifier: scope proof/analysis alone is demonstrably sufficient for target runtime.
20. **H-HYP2-020 — Dynamic topology remapping.** Runtime remapping using queue/coherence/cascade telemetry beats static placement across heterogeneous workloads. Falsifier: static placement matches adaptive policy within noise.

## Transformed second-generation hypotheses

- **HYP-H2-A:** replace H1's single monotonicity gate with `delta semantics × invariant interference × effect authority`.
- **HYP-H2-B:** maintain separate semantic topology `S`, coordination topology `C`, and physical topology `P`.
- **HYP-H2-C:** compile invariants into provenance-bearing n-ary coordination scopes.
- **HYP-H2-D:** relation-instance identity is the canonical higher-order ABI; pairwise and native-hyperedge views are derived indexes.
- **HYP-H2-E:** use signed/typed deltas as the universal change contract.
- **HYP-H2-F:** route each change to incremental propagation, partial rebuild or full rebuild from impact/tail estimates.
- **HYP-H2-G:** treat centralized closure queue saturation as an overcoupling signal.
- **HYP-H2-H:** optimize physical topology from hardware telemetry rather than semantic relevance alone.