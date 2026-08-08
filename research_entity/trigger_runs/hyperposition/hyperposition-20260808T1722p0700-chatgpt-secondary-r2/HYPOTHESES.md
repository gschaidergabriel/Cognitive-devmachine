# Hyperposition H3 Hypothesis Matrix

All hypotheses are OPEN unless explicitly marked as a bounded negative result. No live-FRANK promotion.

## Epoch and causal basis
1. **H-HYP3-001** Topology version identity is required whenever activation or Assembly state can outlive the semantic topology that produced it. Falsifier: mixed-epoch execution produces no stale/revoked causal support under adversarial updates.
2. **H-HYP3-002** `semantic_epoch + activation_epoch + CognitiveFrame` predicts replay correctness better than a wall-clock timestamp. Falsifier: timestamp-only replay is equally exact under independent component updates.
3. **H-HYP3-003** Projection-semantics version belongs in the causal basis because reader transformations can change meaning without changing canonical facts. Falsifier: projection changes never alter reconstruction/uptake under matched canonical state.
4. **H-HYP3-004** Semantic revocation should emit negative activation deltas or force rebase. Falsifier: activation remains valid after arbitrary supported revocations without invalidation.
5. **H-HYP3-005** Immutable semantic epochs reduce reader tearing relative to mutable shared topology. Falsifier: mutable and epoch-pinned readers have identical consistency under concurrent updates/crashes.

## N-ary activation
6. **H-HYP3-006** Pairwise expansion of n-ary events creates false activation paths as relation density/overlap grows. Falsifier: pairwise candidate precision remains equivalent to relation-instance semantics across dense role-overlap workloads.
7. **H-HYP3-007** Relation-instance identity plus explicit role bindings are sufficient for portable lossless activation without mandatory native hyperedges. Falsifier: a tested native-hyperedge semantics cannot be reproduced by relation-instance reification.
8. **H-HYP3-008** Reader-facing role-labelled relation-instance projections outperform raw n-ary syntax for small models in at least some regimes. Falsifier: randomized-order target-4B tests show no benefit or reverse it consistently.
9. **H-HYP3-009** Pairwise materialization is safe only when a query-specific equivalence proof/test exists. Falsifier: unrestricted pairwise flattening preserves all tested higher-order query/activation semantics.

## Adaptive rematerialization
10. **H-HYP3-010** Rematerialization crossover depends jointly on update impact and reads-before-next-update. Falsifier: change fraction alone predicts the optimal choice across representative workloads.
11. **H-HYP3-011** An online workload estimator can outperform fixed incremental/rebuild policies under regime shifts. Falsifier: adaptive policy fails to beat the best fixed policy after overhead.
12. **H-HYP3-012** Partial rebuild is useful between local delta propagation and full rebuild. Falsifier: it never improves cost/recovery/latency Pareto frontier.
13. **H-HYP3-013** Cascade-tail estimates improve rematerialization decisions beyond mean changed-state fraction. Falsifier: q95/q99 amplification adds no predictive value.
14. **H-HYP3-014** Regime-change detection is required because a stationary optimizer can become wrong after read/write phase changes. Falsifier: stationary policy remains near-oracle across nonstationary traces.

## Activation dynamics
15. **H-HYP3-015** Unbounded spreading can create representation/noise collapse even when individual edges are semantically valid. Falsifier: broader/deeper diffusion monotonically improves task outcomes without loss of specificity.
16. **H-HYP3-016** Lateral inhibition, decay, saturation and active-set budgets form independent control dimensions. Falsifier: their ablations are redundant across workloads.
17. **H-HYP3-017** Activation should remain salience-only and never promote epistemic truth. Falsifier: activation strength alone robustly predicts verified truth under adversarial recurrence.
18. **H-HYP3-018** A truthful latent field can influence candidate generation before explicit retrieval. Falsifier: matched no-field/truthful/shuffled field tests show no specific benefit.
19. **H-HYP3-019** Latent activation is upstream of GWT competition, not evidence of ignition. Falsifier: activation lesions selectively remove a recurrent ignition signature while leaving candidate generation unchanged.

## Topology compiler / coordination / locality
20. **H-HYP3-020** H2 semantic `S`, coordination `C` and physical `P` topologies should be compiled from shared canonical semantics but versioned independently. Falsifier: one topology can be mutated as the universal source without semantic, safety or locality loss.
21. **H-HYP3-021** Coverage confidence is necessary before learned scopes can authorize a narrow coordination path. Falsifier: unsound/missing dependencies never create invariant violations.
22. **H-HYP3-022** Observed runtime dependency traces can narrow conservative envelopes but may not expand authority. Falsifier: observed-only widening remains safe under adversarial escapes.
23. **H-HYP3-023** Assemblies are disposable compiled views, not canonical truth. Falsifier: destruction of all Assemblies prevents exact reconstruction from canonical history.
24. **H-HYP3-024** Physical locality should be profile-driven and can change without changing semantic identity. Falsifier: remapping across equivalent layouts changes semantics after controlling timing/effects.
25. **H-HYP3-025** Near-zero boundary overhead is achieved by compiling only the currently necessary topology, not globally materializing every relation. Falsifier: universal eager materialization dominates on latency/energy/recovery at equal semantics.

## FRANK / GWT integration
26. **H-HYP3-026** A `TopologyBasis` witness reduces false causal attribution in workspace experiments by preventing mixed-frame/mixed-epoch candidates. Falsifier: matched causal interventions are unchanged by basis validation.
27. **H-HYP3-027** GWT reconstruction receipts should include the projection/topology basis used to produce model-visible state. Falsifier: basis identity adds no debugging/replay/causal discrimination.
28. **H-HYP3-028** The optimal Hyperposition runtime is a compiler over versioned semantics rather than a single database/backend. Falsifier: one fixed storage/topology representation dominates exactness, update/query latency, activation, coordination, portability and recovery across representative targets.

## Transformed second-generation hypotheses
- **H-HYP3-2A — HYP-RC3:** replace static Three-Topology Hyperposition with an epoch-pinned adaptive topology compiler.
- **H-HYP3-2B:** define `TopologyBasis = semantic_epoch + activation_epoch + CognitiveFrame + op/projection semantics` as the replay/causal identity of a compiled Assembly.
- **H-HYP3-2C:** treat activation invalidation as a negative-delta problem tied to semantic revocation.
- **H-HYP3-2D:** propagate higher-order activation through relation instances/roles; use pairwise views only as proven query-specific projections.
- **H-HYP3-2E:** control activation as bounded reaction/diffusion-like dynamics, not maximum spread.
- **H-HYP3-2F:** choose incremental/partial/full rematerialization from amortized predicted workload and cascade tails.
- **H-HYP3-2G:** allow scope learning and locality learning, but gate narrow coordination on trusted coverage and keep authority external.
- **H-HYP3-2H:** keep ClayGraph G1d on HOLD until live epoch/replay plus matched latent-field causal tests pass.
