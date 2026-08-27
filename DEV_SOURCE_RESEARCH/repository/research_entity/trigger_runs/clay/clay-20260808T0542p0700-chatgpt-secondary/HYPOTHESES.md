# Clay G7 Hypothesis Matrix

Run: `clay-20260808T0542p0700-chatgpt-secondary`  
Actor: `chatgpt-secondary`  
Canonical parent: r2 / `04234efd...`  
All hypotheses are OPEN unless a bounded synthetic result explicitly weakens a universal form. Counts are not padded.

## Generation 1 — 60 falsifiable hypotheses

### A. GWT / dual workspace
1. **H-G7-001** Cross-lesion symmetry is stronger evidence of a shared workspace bottleneck than either lesion alone. Falsifier: matched lesions affect disjoint functions.
2. **H-G7-002** Workspace is multidimensional; ignition, reportability, receipt completeness, lesion and rescue can dissociate. Falsifier: metrics co-vary near-perfectly across interventions.
3. **H-G7-003** J-space-like representations are partly verbalization-biased; some nonverbal/routine cognition bypasses them. Falsifier: all tested cognition depends equally on J-space perturbation.
4. **H-G7-004** Receipt completeness predicts downstream causal effect better than ignition steepness alone. Falsifier: ignition dominates matched lesion outcomes.
5. **H-G7-005** Re-entry delay and gain interact with effective workspace capacity. Falsifier: no interaction under controlled delays/gains.
6. **H-G7-006** Low-activation causal bridge states can have greater lesion effects than high-activation peripheral states. Falsifier: activation magnitude fully explains lesion impact.
7. **H-G7-007** Excessive re-entry gain can destabilize workspace topology and increase change propagation. Falsifier: topology/propagation invariant to gain sweep.
8. **H-G7-008** In recurrent models, workspace signatures can align more strongly to recurrence iteration than layer depth. Falsifier: iteration adds no explanatory power.
9. **H-G7-009** Active latent probing can itself perturb workspace state; passive and intervention probes will differ. Falsifier: probe method has no measurable effect.
10. **H-G7-010** Receipt/J-space divergence can detect logging or mediation anomalies but will false-positive under modality mismatch. Falsifier: divergence is nondiscriminative across anomaly controls.

### B. Causal budget / control
11. **H-G7-011** A hierarchical governor with fast safety loops and slower semantic utility optimization beats a flat vector under coupled pressures. Falsifier: flat vector matches quality/cost after overhead.
12. **H-G7-012** Heterogeneous change propagation is better represented by a type-conditioned offspring matrix `M_delta` than scalar `R_delta`. Falsifier: matrix structure adds no cascade predictive power.
13. **H-G7-013** Tail-risk/uncertainty control near critical propagation outperforms mean-only control. Falsifier: uncertainty terms do not reduce rare large cascades.
14. **H-G7-014** Observation/control delay can destabilize the governor; predictor compensation improves stability. Falsifier: delay has no instability/regret effect.
15. **H-G7-015** Hysteresis/rate limits reduce mode chatter without material utility loss. Falsifier: switching falls only by harming objective utility.
16. **H-G7-016** Budget dimensions interact through shadow prices; constrained joint optimization beats independent tuning. Falsifier: independent controls match joint controller.
17. **H-G7-017** Controller overhead can erase adaptive gains during low-load regimes. Falsifier: adaptive controller remains net-beneficial at all loads.
18. **H-G7-018** Recovery debt/history is a necessary governor state variable. Falsifier: including pending recovery cost adds no predictive/utility value.
19. **H-G7-019** Explicit regime detection should select controller policy in nonstationary workloads. Falsifier: one continuous policy has equal/lower regret.
20. **H-G7-020** Runtime objective should maximize task utility subject to energy, latency, recovery and safety constraints rather than raw throughput. Falsifier: throughput-only gives equal downstream utility/cost.

### C. Distributed state / invariants
21. **H-G7-021** Invariant-confluence is operation-pair/path-sensitive, not only operation-class-sensitive. Falsifier: class-level labels are minimal and complete on real traces.
22. **H-G7-022** Asymmetric dependency semantics reduce coordination beyond G6 binary risky/safe classes without correctness loss. Falsifier: pair-sensitive planner misses invariants or gains no availability.
23. **H-G7-023** Escrow/reservation rights can convert bounded numeric updates from closure-required to coordination-free. Falsifier: invariant violations remain under correct escrow allocation.
24. **H-G7-024** Commutativity alone is insufficient for safe local execution; invariant preservation is decisive. Falsifier: all commuting operations preserve declared invariants.
25. **H-G7-025** Incomplete invariant specifications are a first-order correctness bottleneck; unknown coverage must fail closed. Falsifier: optimistic execution stays safe under omitted invariants.
26. **H-G7-026** Minimal contested causal cuts can define narrower coordination scope than whole-operation serialization. Falsifier: subpath coordination creates anomalies.
27. **H-G7-027** Idempotency plus deduplication allows some authorized effects without total order. Falsifier: duplicate/reordered effects still violate semantics.
28. **H-G7-028** Partition mode should allow only reversible or proven invariant-confluent cognition. Falsifier: broader local execution remains correct under adversarial partitions.
29. **H-G7-029** Rooted receipts plus logical clocks enable deterministic replay/rebase after partition. Falsifier: branches cannot reconcile without semantic loss.
30. **H-G7-030** Coordination plans can be compiled from ClayCode read/write/effect sets plus invariant declarations and fuzz/model-checked. Falsifier: static summaries cannot predict required closure.

### D. ClayCode / formal IR
31. **H-G7-031** Gamma masks should be root-bound and dependency-scoped; irrelevant state changes need not rebuild them. Falsifier: dependency-scoped invalidation admits current-invalid proposals.
32. **H-G7-032** Some root mismatches can be safely rebased if proof dependencies are unchanged. Falsifier: rebase produces semantic divergence despite identical dependency digest.
33. **H-G7-033** Semantic constrained decoding can enforce local type/invariant properties but cannot confer authority. Falsifier: authority can be safely and completely encoded in model-controlled constraints.
34. **H-G7-034** ClayCode read/write/effect types can feed a coordination compiler before expensive execution checks. Falsifier: effect/dependency classification error remains high.
35. **H-G7-035** Proof-carrying pre/postcondition metadata reduces gateway validation work without weakening external authority. Falsifier: proof overhead exceeds savings or misses attacks.
36. **H-G7-036** Weakest-precondition/SMT validation can verify a bounded ClayCode transition fragment when a solver is available. Falsifier: state space or semantics prevents useful proof coverage.
37. **H-G7-037** Grammar caching improves latency only if cache invalidation follows root dependencies. Falsifier: dependency-aware cache gives no advantage over full rebuild.
38. **H-G7-038** Learned grammars from execution traces are vulnerable to poisoning/rare-operation overfit. Falsifier: robust OOD precision/recall under adversarial trace contamination.
39. **H-G7-039** Authority terminals/capabilities must remain outside model-expandable grammar/state. Falsifier: formally verified self-hosted authority remains non-escalatory.
40. **H-G7-040** Self-description/meta-schema mutations require a stronger migration gate than ordinary state transitions. Falsifier: same validation policy is sufficient under schema evolution.

### E. Edge/model runtime / KV
41. **H-G7-041** Hierarchical semantic KV with coarse summaries plus on-demand zoom outperforms binary retain/evict under shifting relevance. Falsifier: equal-memory retain/evict matches quality/latency.
42. **H-G7-042** Predicting future causal contribution can outperform instantaneous attention for KV retention. Falsifier: prediction adds no task-quality gain.
43. **H-G7-043** Recurrence-aware retention preserves tokens that regain importance later. Falsifier: recurrence model adds no future-hit advantage.
44. **H-G7-044** KV/context and thermal budgets should be jointly controlled; context reduction can precede frequency collapse. Falsifier: joint control does not improve sustained utility.
45. **H-G7-045** CPU/GPU/NPU winner is device- and regime-specific and can reverse with context/thermal state. Falsifier: one backend dominates target fleet.
46. **H-G7-046** Speculative decoding should use online acceptance/task regime rather than always-on policy. Falsifier: adaptive policy fails to improve sustained latency/energy.
47. **H-G7-047** Qwen-class 4B wake threshold should depend on expected value of computation over deterministic/small paths. Falsifier: adaptive wake loses task utility per joule.
48. **H-G7-048** Model routing should jointly use thermal, memory, battery, deadline and uncertainty signals. Falsifier: simpler routing matches objective.
49. **H-G7-049** Sustained useful work per joule is a better edge objective than peak tok/s. Falsifier: peak ranking predicts sustained task utility across devices.
50. **H-G7-050** Each model call should emit backend/thermal/KV/speculation receipts to the runtime governor. Falsifier: receipts add overhead without control benefit.

### F. Emergence / hyperposition / system
51. **H-G7-051** `rho(M_delta)>1` indicates heterogeneous amplification, not emergence. Falsifier: every supercritical cascade exhibits robust macro causal function.
52. **H-G7-052** Emergence requires synergy + recurrence + lesion/rescue + macro causal gain rather than propagation alone. Falsifier: propagation metric predicts function independently.
53. **H-G7-053** Hyperposition-preserved alternatives improve function-specific counterfactual rescue. Falsifier: winner-only history gives equal rescue quality/cost.
54. **H-G7-054** Assembly boundaries should follow causal closure/bottlenecks rather than graph density. Falsifier: density communities predict lesion/OOD behavior equally well.
55. **H-G7-055** Topology adaptation needs regularization to avoid self-confirming causal edges. Falsifier: unrestricted adaptation does not increase spurious recurrence.
56. **H-G7-056** Higher-order relations should be materialized only when synergistic benefit exceeds representation/update cost. Falsifier: universal higher-order materialization is cheaper/better.
57. **H-G7-057** Shared incremental arrangements should be selected by reuse x fanout versus update/storage/rebuild cost. Falsifier: always/never materialization dominates adaptive selection.
58. **H-G7-058** Event-log compaction/snapshots must preserve contradiction, negative-result and falsifier lineage. Falsifier: aggressive compaction retains all adjudication-relevant history.
59. **H-G7-059** Distributed semantic identity allows heterogeneous local backends/projections as reconstructible caches. Falsifier: backend divergence breaks semantic replay.
60. **H-G7-060** Near-zero latency should come from adaptive boundary placement, semantic zoom and minimized necessary coordination, not universal shared memory. Falsifier: universal sharing wins complete-system latency/correctness/energy.

## Generation 2 — 24 transformed hypotheses after external research + experiments

1. **H-G7-T01** Replace scalar heterogeneous `R_delta` with typed `M_delta`; `rho(M_delta)` plus dominant eigenvectors should predict cascade risk and responsible state types better than scalar averages.
2. **H-G7-T02** `rho(M_delta)>1` must remain explicitly separated from emergence: it is a criticality/amplification diagnostic only.
3. **H-G7-T03** Governor should be hierarchical: fast safety loops for thermal/freshness/authority/cascade/deadline underneath a slower semantic utility allocator.
4. **H-G7-T04** Hierarchical control needs a switching-cost/hysteresis shadow because the G7 proxy improved loss but substantially increased mode changes.
5. **H-G7-T05** Causal-budget dimensions should share constraints/shadow prices rather than be treated as independent knobs.
6. **H-G7-T06** Coordination planning should compile asymmetric operation-pair/path dependencies, not only risky operation classes.
7. **H-G7-T07** Pair-sensitive coordination gains are conditional on complete dependency/invariant specifications; unknown coverage should fail closed.
8. **H-G7-T08** Escrow, reservations, idempotency and dedupe can potentially convert subsets of closure-required operations into safe local paths.
9. **H-G7-T09** ClayCode should expose typed effect/read/write/dependency summaries as input to the coordination compiler.
10. **H-G7-T10** Gamma caches should be root/epoch-bound but invalidated only by relevant dependency deltas; full rebuild on every state change is unnecessary.
11. **H-G7-T11** Root mismatch may be rebased only if a proof/dependency digest demonstrates referenced state is unchanged.
12. **H-G7-T12** Semantic constrained decoding can enforce local type/invariant conditions; capability authority remains outside model-controlled grammar.
13. **H-G7-T13** Grammar/policy constraints are themselves an attack surface; authority grammar must not be writable by the model.
14. **H-G7-T14** Clay memory should be multi-resolution: immutable exact history + coarse active summaries + on-demand exact zoom.
15. **H-G7-T15** KV/active-context retention should incorporate recurrence and predicted future utility, not instantaneous salience alone.
16. **H-G7-T16** Receipt-defined causal-spine signals should be compared head-to-head with recurrence, coverage, heavy-hitter and learned future-contribution KV policies.
17. **H-G7-T17** Workspace evidence should be a vector: selectivity, reportability, ignition, broadcast, receipt completeness, lesion, rescue and re-entry.
18. **H-G7-T18** J-space evidence should not force all FRANK cognition through a verbalizable latent workspace; deterministic/nonverbal paths may legitimately bypass it.
19. **H-G7-T19** Edge runtime should learn device x regime backend policy online and optimize sustained useful work/energy/latency/reliability rather than select a universal backend.
20. **H-G7-T20** Active arrangements/materialized views should be selected adaptively from query reuse, fanout, delta/update rate, storage and rebuild cost; rebuild churn is a shadow metric.
21. **H-G7-T21** Higher-order emergence testing should combine interventionist PEID/PID with alternative measures/limitations rather than canonize one decomposition scalar.
22. **H-G7-T22** Candidate emergent assemblies should be discovered from stable causal/higher-order closure and then tested by lesion/rescue/OOD, not named from density/novelty.
23. **H-G7-T23** Event projections and all memory-resolution levels should remain reconstructible from canonical event truth; hot state is disposable derived state.
24. **H-G7-T24** Architecture candidate: **Hierarchical Semantic Causal Kernel (HSCK-G7)** combining typed change-propagation matrix, hierarchical governor, asymmetric coordination compiler, root/dependency-bound ClayCode, multi-resolution memory, intervention-vector workspace and adaptive device control.
