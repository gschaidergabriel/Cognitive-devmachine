# External Evidence Ledger — hypofusion 2026-08-11 04:19 +07

Evidence is classified by mechanism match; architectural resemblance is not treated as causal replication.

| Cluster | Class | Primary / independent source | Finding used | Boundary |
|---|---|---|---|---|
| HC-01 provider retry | DIRECT_SUPPORT | Stripe API idempotent requests | Idempotency keys can be pruned after a documented retention period; reuse after pruning can become a new request. | Provider-specific; does not prove Frank integration. |
| HC-01 provider retry | DIRECT_SUPPORT | AWS ECS RunTask idempotency | Client-token idempotency has a finite TTL. | Service-specific; supports time-bounded authority principle only. |
| HC-02 causal provenance | PARTIAL_ANALOGUE | W3C PROV-O / PROV semantics | Provenance relations bind identified entities, activities and generation/use relations rather than arbitrary opaque strings. | General provenance standard, not Frank causal-credit proof. |
| HC-03 identity lineage | IMPLEMENTATION_PRECEDENT | The Update Framework | Rollback/freeze/mix-and-match threats require explicit trusted-version and metadata checks. | Software update security analogue, not semantic SELF identity. |
| HC-03 identity lineage | IMPLEMENTATION_PRECEDENT | in-toto Attestation Statement / SLSA provenance | Artifact subjects are digest-bound and provenance is separate authenticated metadata. | Supports artifact/build provenance separation from state lineage. |
| HC-04 ClayCode resolution | IMPLEMENTATION_PRECEDENT | Rust Reference — names/name resolution/use declarations | Names resolve to declarations and imports create bindings to explicit paths; unresolved/ambiguous bindings are errors. | Language-specific precedent. |
| HC-04 ClayCode resolution | IMPLEMENTATION_PRECEDENT | MLIR Symbols and Symbol Tables | Symbol references resolve through explicit symbol tables; external declarations stay explicit. | IR precedent, not ClayCode proof. |
| HC-05 live fusion | IMPLEMENTATION_PRECEDENT | Delta-state CRDT anti-entropy research | Small deltas plus anti-entropy can converge while avoiding full-state dissemination. | Distributed-state analogue; receiver semantic use still needs Clay receipts. |
| HC-05 live fusion | IMPLEMENTATION_PRECEDENT | Demers et al., epidemic algorithms | Randomized dissemination/anti-entropy is a classic repair path for replicated data. | Does not select Clay routing policy. |
| HC-06 adaptive recurrence | PARTIAL_ANALOGUE | Graves, Adaptive Computation Time | Recurrent networks can learn input-dependent compute; benefits were task-dependent rather than universal. | Supports adaptive-compute testability, not Frank loop-of-loops validity. |
| HC-07 GWT causal broadcast | THEORY_CRITIQUE_PLUS_ANALOGUE | global neuronal workspace/network communication literature | Integration alone can be compatible with multiple communication mechanisms; causal broadcast needs stronger discriminators. | Neuroscience analogy only; no consciousness inference. |
| HC-08 reward | PARTIAL_ANALOGUE | Bellemare et al., Distributional RL | Modeling value distributions can change learning/control behavior versus expectation-only value. | Does not validate Frank NAcc-like variables. |
| HC-08 reward | PARTIAL_ANALOGUE | Keramati & Gutkin, homeostatic RL | Reward/control can be coupled to deviations from internal physiological set-points. | Biological/computational analogue; no direct Frank evidence. |
| HC-09 Hyperposition | COUNTEREVIDENCE | 2026 higher-order interaction reduction work | A broad class of higher-order social-impact dynamics can be mapped exactly to a weighted pairwise projection preserving microscopic transition probabilities. | Strong reason to require pairwise baseline; not universal reducibility. |
| HC-09 Hyperposition | REPRESENTATION_DEPENDENCE | Nature Communications higher-order network work | Hypergraph vs simplicial representations can produce materially different dynamics. | Shows representation choice matters, not that higher-order is always better. |
| HC-10 SQLite WAL | DIRECT_PRIMARY_FAILURE_MODE | SQLite WAL documentation | WAL-reset corruption race affects documented versions through 3.51.2 under specific concurrent writer/checkpoint topology; fixed in later/current releases and selected backports. | Exact Ubuntu backport status must still be verified. |
| HC-11 Causal Quotient Compiler | DIRECT_FORMAL_ANALOGUE | Hansen-Estruch et al., ICML/PMLR 2022 goal-conditioned bisimulation | Bisimulation-style state abstractions can preserve functional equivalence for a declared downstream task class. | Supports scoped behavioral equivalence, not universal Frank-organ fusion. |
| HC-11 Causal Quotient Compiler | COUNTERBOUNDARY | Adhikary et al., ICML/PMLR 2024 behavioral representations | Exact/isometric behavioral compression objectives may fail to exist, motivating controlled distortion rather than assuming perfect equivalence. | Reinforces revocable/scoped certificates and explicit error budgets for approximate fusion. |

## Adversarial conclusions

1. Finite/unknown provider retention is a direct counterexample to treating an idempotency key as timeless retry authority.
2. Provenance standards support identity-bearing relations, but they do not by themselves prove Frank causal closure; target-level referential tests remain mandatory.
3. Adaptive recurrence and higher-order topology both have simpler viable countermodels. Neither should be promoted as a default because it sounds cognitively richer.
4. Anti-entropy is a correctness-repair mechanism, not evidence-strength amplification.
5. SQLite upstream evidence is strong enough for a fail-closed release gate, while the Ubuntu backport question remains explicitly unresolved rather than inferred.
6. Causal quotienting has a formal analogue in bisimulation/state abstraction, but equivalence is always scoped to declared observables/tasks/interventions; unknown interventions or approximation error invalidate a universal fusion claim.
