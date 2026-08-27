# Hypofusion r2 — Contradiction Map

Hard close cutoff: `2026-08-09T10:22:35Z`.

1. **Native higher-order structure vs reducibility.** Some role-bearing relations lose semantics under naive pairwise reduction, while independent work demonstrates exact pairwise reductions for nontrivial higher-order model classes. **Resolution:** reducer-first equivalence testing; native n-ary remains conditional.

2. **Shared epoch vs scoped freshness.** Shared semantic epochs help coherent reads/replay, but one global epoch at effect commit can falsely abort safe work under unrelated churn. **Resolution:** coherent snapshot epochs plus scoped commit revalidation.

3. **Provenance integrity vs semantic correctness.** Self-consistent wrong lowerings can preserve ancestry/hash chains. **Resolution:** provenance is audit evidence, not semantic-preservation proof; pair it with an independent oracle.

4. **More recurrence vs stable recurrence.** FRANK is intentionally loop-of-loops, while recurrent-model evidence and current hypotheses allow overthinking/collapse before or with instability. **Resolution:** recurrence retained as controlled intervention, with explicit halt/stall/overcoupling observables.

5. **One workspace gate vs dual gates.** GWT R7 proposes separate admission and recurrence-continuation decisions; the simpler alternative is one ignition/reentry score or fixed budget. **Resolution:** unresolved; H1 matched-compute one-gate/fixed/dual-gate replay is the discriminator.

6. **Incremental state vs batch recomputation.** Sparse synthetic dependency closure gave exact answers with very low touched-state cost, while dense/high-fanout changes may erase the gain. **Resolution:** adaptive crossover, not always-incremental doctrine.

7. **Capability safety vs composition-sensitive flow.** Least-authority capabilities constrain primitive operations but do not by themselves prove safety of allowed-operation compositions. **Resolution:** retain capability substrate plus commit-time flow/invariant controls and ambient-authority tests.

8. **Exactly-once/local idempotency vs external effects.** Transaction-safe semantic idempotency can serialize/reject changed local requests, yet local state cannot generally distinguish crash-before vs crash-after a remote effect. **Resolution:** local semantic idempotency plus remote idempotency/transactional coupling/reconciliation or typed `UNCERTAIN`.

9. **Standard JCS vs Clay typed numeric semantics.** RFC 8785 covers a mature IEEE-754/I-JSON canonical domain, while Clay may admit exact integers or distinctions outside it. **Resolution:** standard-first; add typed extensions only where required.

10. **BASE freeze vs grammar/surface closure.** Current admitted G9 artifacts use constructs missing from the published grammar, and three legacy rule lines also admit multiple plausible semantic parses. **Resolution:** separate surface repair from semantic choice; close missing generic syntax mechanically, but fail closed where authoritative meaning is ambiguous.

11. **Database core primitive vs typed adapter.** APP-03 locally achieved deterministic CRUD/transaction behavior through existing G9 semantics plus a typed SQLite adapter, but one local backend cannot establish cross-backend sufficiency. **Resolution:** adapter-first candidate; core DB primitive only after a target-host semantic counterexample.

12. **Function calls vs function definitions.** Current G9 can denote calls but the published statement grammar lacks a reusable general typed function-definition body. **Resolution:** this is a genuine BASE closure candidate, but the lowest-risk repair is a minimal generic typed function/signature contract, not FRANK-specific syntax.

13. **Hypothesis IDs vs concurrent research.** Two completed ClayResearch runs use overlapping bare `H-CR-*` IDs for different statements. **Resolution:** all current references are run-qualified; durable hypothesis identity needs a global uniqueness/run-qualification rule.

14. **Pairwise flow false positives vs pairwise false negatives.** Common drivers can create apparent directed flow, while XOR-style mechanisms can hide genuine joint causality from pairwise measures. **Resolution:** emergence measurement requires conditioned/multivariate causal triangulation, not one pairwise scalar.

## Epistemic rule

No unresolved alternative is called refuted without a discriminating result. Shared-repository descendants are not independent replication. No canonical scientific promotion is made by this run.