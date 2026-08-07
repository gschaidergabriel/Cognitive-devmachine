# Clay G5 Hypothesis Matrix

All first-generation hypotheses are OPEN unless an existing G3/G4 result is explicitly referenced. No hypothesis is promoted to live FRANK truth by this file.

## Dual workspace
1. **H-G5-001** Receipt-defined GWT episodes and latent model-workspace states share a causal bottleneck when the same reasoning step is globally available. Falsifier: no cross-predictive or cross-lesion effect after compute matching.
2. **H-G5-002** Latent workspace perturbation is a stronger mediation test than verbal self-report. Falsifier: perturbations fail to alter outcomes or only track reporting artifacts.
3. **H-G5-003** External GWT receipts can anchor latent-workspace probes. Falsifier: alignment does not exceed shuffled episode controls.
4. **H-G5-004** A small privileged internal workspace can coexist with large automatic processing outside it. Falsifier: workspace lesion degrades all tasks uniformly.
5. **H-G5-005** Workspace capacity is a bounded control variable with task-specific interior optima. Falsifier: performance is monotonic in capacity.
6. **H-G5-006** Ignition-like nonlinearity is insufficient for GWT without broadcast/effect/re-entry. Falsifier: ignition always predicts causal closure under intervention.
7. **H-G5-007** Re-entry has a useful delay horizon beyond which adaptive value falls. Falsifier: delay has no systematic effect after compute matching.
8. **H-G5-008** Dual workspace observability reduces false causal attribution versus either channel alone. Falsifier: combined evidence adds no information over the best single channel.

## Incremental control
9. **H-G5-009** Change propagation has an effective reproduction number `R_delta` controlling recomputation cost. Falsifier: no transition with increasing fanout×propagation probability.
10. **H-G5-010** Overcoupling is better measured as change amplification than raw edge density. Falsifier: density rises without downstream amplification in relevant regimes.
11. **H-G5-011** Selective decoupling of low-value edges improves latency/robustness without semantic loss. Falsifier: any pruning causes equivalent functional degradation.
12. **H-G5-012** Incremental maintenance beats rebuild only below workload-specific amplification/edit thresholds. Falsifier: incremental always dominates or always loses.
13. **H-G5-013** Deletion/revocation is the strongest discriminator among information-preserving incremental backends. Falsifier: deletion cost tracks append cost identically.
14. **H-G5-014** Causal-path-aware materialization beats recall-maximizing broadcast under fixed active-context budgets. Falsifier: recall-max strategy matches causal completeness.
15. **H-G5-015** Active projections should be disposable derived views rather than canonical state. Falsifier: projection loss destroys irrecoverable truth.
16. **H-G5-016** Adaptive parallelism should follow observed bottleneck topology rather than fixed worker counts. Falsifier: fixed parallelism performs equally across regimes.

## ClayCode semantics
17. **H-G5-017** Grammar-constrained decoding solves syntax but not state validity. Falsifier: grammar validity implies semantic validity.
18. **H-G5-018** State-aware constrained decoding removes a large fraction of semantic-invalid ClayCode proposals before validation. Falsifier: runtime symbol/type masks do not improve validity.
19. **H-G5-019** Authority remains external even with semantic constraints. Falsifier: semantic validity fully predicts authorization under adversarial tests.
20. **H-G5-020** Typed effect classes separating pure transforms, state proposals and external effects reduce unnecessary gateway serialization. Falsifier: one undifferentiated transition type performs equally.
21. **H-G5-021** Pure ClayCode transforms can execute speculatively before authority validation. Falsifier: speculation gives no latency gain or leaks effects.
22. **H-G5-022** Runtime grammar Γ should bind to a state snapshot/root and expire on root change. Falsifier: root binding has no effect on stale semantic proposals.
23. **H-G5-023** Semantic roundtrip equivalence is a stronger correctness target than token compression. Falsifier: token efficiency predicts correctness without roundtrip checks.
24. **H-G5-024** Equality saturation is useful only in bounded pure-transform regions. Falsifier: global saturation scales without material memory/search cost.

## Hyperposition / distributed state
25. **H-G5-025** Hyperposition is realizable by temporal, faceted, relational-node or native hypergraph backends under equal semantics. Falsifier: only one backend preserves tested semantics.
26. **H-G5-026** Role-aware n-ary semantics are more fundamental than hyperedge storage. Falsifier: role-preserving reification necessarily loses tested semantics.
27. **H-G5-027** Conflicts should remain first-class until contextual projection; scalar merge destroys recoverable alternatives. Falsifier: scalar merge loses no useful information.
28. **H-G5-028** CRDT-like merge suits non-authoritative cognitive state but not effect authority. Falsifier: CRDT convergence safely authorizes adversarial external effects by itself.
29. **H-G5-029** Local-first state improves partition tolerance when only effects require synchronous closure. Falsifier: divergence overwhelms availability gains or creates unsafe effects.
30. **H-G5-030** Global ordering is needed only at effect/causal-conflict boundaries, not every cognitive event. Falsifier: unordered pure events produce irreducible correctness failures.
31. **H-G5-031** Branch-and-merge state beats destructive overwrite for counterfactual planning. Falsifier: branching adds cost without decision benefit.
32. **H-G5-032** Revocation must propagate as a first-class negative delta through projections. Falsifier: dependent derived state remains correct without explicit retraction.

## Mobile/model runtime
33. **H-G5-033** On-device feasibility is dominated by total memory including KV/runtime buffers, not weights alone. Falsifier: weight size alone predicts deployment success.
34. **H-G5-034** Adaptive KV precision beats fixed KV precision on the memory/quality Pareto frontier. Falsifier: fixed precision matches adaptive policies.
35. **H-G5-035** Causal-context selection reduces both prompt and KV footprint while preserving reasoning chains. Falsifier: recency/full-history baselines match success per byte.
36. **H-G5-036** Backend-neutral semantic contracts are necessary because CPU/GPU/NPU winners vary by device/workload. Falsifier: one backend dominates across representative devices and contexts.
37. **H-G5-037** Routed 4B inference beats always-on 4B in energy/latency at equal task quality. Falsifier: routing lowers quality or gives no cost benefit.
38. **H-G5-038** Warm model residency can be more valuable than maximum model size for interactive loops. Falsifier: cold-load penalty is negligible end-to-end.
39. **H-G5-039** Speculative decoding is regime-sensitive and should be acceptance-monitored. Falsifier: speculation always speeds decoding across tested regimes.
40. **H-G5-040** Android runtime policy should adapt model/context/backend to thermal state. Falsifier: static routing performs equally under sustained load.

## Emergence
41. **H-G5-041** Emergent assembly claims require causal contribution beyond recurrence/novelty. Falsifier: recurrence alone predicts lesion/rescue function.
42. **H-G5-042** Macro causal contribution can exist when microscale description is sufficient but causally lossy. Falsifier: macro adds only compression under intervention.
43. **H-G5-043** Higher-order synergy must be measured alongside pairwise transfer. Falsifier: pairwise measures recover all constructed n-ary coordination.
44. **H-G5-044** Truthful-vs-shuffled re-entry is stronger than re-entry presence. Falsifier: event presence alone predicts benefit after matching count/compute.
45. **H-G5-045** Compute-matched rescue is necessary to separate specific rescue from extra compute. Falsifier: arbitrary added compute restores function equally.
46. **H-G5-046** OOD recurrence should be required before an `emergent organ` label. Falsifier: discovered effect consistently disappears out of distribution.
47. **H-G5-047** Broadcast can amplify internal noise and create an overcoupling failure mode. Falsifier: broader broadcast never increases perturbation propagation.
48. **H-G5-048** Emergence should remain vector-valued with robustness/cost shadows. Falsifier: one optimized scalar preserves every relevant tradeoff under adversarial optimization.

## Authority / recovery / security
49. **H-G5-049** Only effectful transitions require synchronous global authority closure; pure cognition can remain speculative/local. Falsifier: selective closure introduces unsafe effects or irrecoverable causal errors.
50. **H-G5-050** Capability scope, nonce, expiry, root freshness, rollback and effect receipt are independently useful adversarial dimensions. Falsifier: guard ablations show true redundancy.
51. **H-G5-051** WASI/component sandboxing is useful but cannot replace application-level authority semantics. Falsifier: sandbox alone enforces all FRANK policy under adversarial tests.
52. **H-G5-052** Runtime CVEs are part of FRANK's effective trust boundary. Falsifier: host/runtime compromise cannot bypass Clay authority/effects.
53. **H-G5-053** Replay should deterministically reproduce pure cognition while reauthorizing external effects. Falsifier: blind effect replay is safe under stale capabilities/roots.
54. **H-G5-054** Crash recovery should rebuild projections from canonical events and verify effect receipts before resume. Falsifier: mutable projection snapshots are necessary authority.
55. **H-G5-055** Quarantined preauthorization computation can reduce latency while preserving effect safety. Falsifier: speculation leaks effects or never improves end-to-end latency.
56. **H-G5-056** Distributed canonical roots should use selective synchronization boundaries. Falsifier: every cognitive event genuinely requires consensus.

## Second-generation transformed hypotheses
- **H-G5-2A** Replace `maximize connectivity` with adaptive control of `R_delta` and causal value.
- **H-G5-2B** Treat external event workspace and latent workspace as two measurements requiring cross-lesion agreement.
- **H-G5-2C** Coordinate active context and KV cache as one causal resource budget.
- **H-G5-2D** State-aware grammar reduces invalid proposals; capability authority remains outside decoding.
- **H-G5-2E** Split Clay transitions into `PURE_TRANSFORM`, `STATE_PROPOSAL`, `EFFECT_PROPOSAL`; only effects require synchronous closure.
- **H-G5-2F** Speculate only on pure/state work and quarantine outputs until authorization.
- **H-G5-2G** Define hyperposition as conflict-preserving branch/revocation semantics, not a backend product.
- **H-G5-2H** Use role-aware relation nodes as portable ABI; native hyperedges are optional optimization.
- **H-G5-2I** Use local-first merge for non-authoritative cognition and stronger ordering at effect-conflict boundaries.
- **H-G5-2J** Use a vector emergence certificate: recurrence, lesion, specific rescue, compute-matched rescue, OOD, synergy, macro causation, cost, robustness.
- **H-G5-2K** Treat broadcast/noise amplification as an explicit GWT failure mode.
- **H-G5-2L** Keep incremental projections disposable/rebuildable; canonical event/provenance history remains authority.
- **H-G5-2M** Adapt model/context/backend/thermal policy jointly on mobile.
- **H-G5-2N** Monitor speculative-decoding acceptance and disable dynamically in bad regimes.
- **H-G5-2O** Replay pure cognition deterministically but reauthorize historical effects against current authority.
- **H-G5-2P** Track sandbox/runtime security advisories inside the effective FRANK trust boundary.
