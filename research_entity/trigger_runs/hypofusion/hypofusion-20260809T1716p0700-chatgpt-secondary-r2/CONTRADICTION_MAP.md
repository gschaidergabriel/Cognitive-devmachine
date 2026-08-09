# Hypofusion r2 — Contradiction Map

## Open contradictions after Fusion 2

1. **Native higher-order structure vs reducibility.** Clay benefits from explicit role-bearing n-ary semantics in some local counterexamples, while independent 2026 work demonstrates exact pairwise reductions for nontrivial hypergraph model classes and argues graph representations can encode multivariate interactions. Resolution: native n-ary form is no longer presumed necessary; reducer-first equivalence testing becomes the gate.

2. **Shared epoch vs scoped freshness.** H-CR-004/027 support coherent semantic epochs for snapshot/read consistency. H-WP-10 synthetic evidence shows a single global epoch at effect commit can reject safe work under unrelated churn. Resolution: shared epochs remain useful read/replay coordinates; effect commit should revalidate scoped dependency/capability/resource state rather than require global equality.

3. **Provenance integrity vs semantic correctness.** The provenance chain catches stale/mixed ancestry, but 10,000/10,000 deliberately wrong self-consistent lowerings passed chain integrity in the current ClayCode probe. Resolution: provenance is necessary audit evidence but not semantic-preservation evidence; pair it with an independent reference/translation oracle.

4. **More recurrence vs stable recurrence.** FRANK's architecture is intentionally recurrent and loop-of-loops. External Looped-LM evidence reports performance can peak then collapse with additional recurrence. Resolution: recurrence remains a mechanism candidate, while depth/gain must be actively controlled and tested for overcoupling/stability.

5. **Incremental state vs batch recomputation.** Differential/incremental dataflow strongly supports work reuse under change, but current synthetic Clay tests already show dense closure can erase the advantage. Resolution: adaptive crossover, not always-incremental doctrine.

6. **Deterministic replay vs real-world fault discovery.** Deterministic simulation gives exceptional reproducibility/localization, but independent high-reliability systems pair it with outside-in/non-deterministic testing. Resolution: two complementary lanes; no single lane is treated as complete validation.

7. **Capability safety vs composition-sensitive flow.** seL4/WASI-style capabilities strongly support least authority, but capability possession alone does not express all harmful compositions such as separately allowed secret-read + public-send. Resolution: keep capabilities as authority substrate and separately test provenance/information-flow at commit.

8. **Exactly-once local ledger vs external effects.** Local idempotency/transaction state can serialize retries, but crash-before-effect and crash-after-effect can be observationally indistinguishable without remote cooperation. Resolution: remote idempotency/transactional coupling/reconciliation or typed `UNCERTAIN`; no exactly-once claim from a local ledger alone.

9. **Standard JCS vs Clay typed numeric semantics.** RFC 8785 supplies a mature canonicalization mechanism for an IEEE-754/I-JSON domain, but Clay may require exact integers or semantic distinctions outside that domain. Resolution: standard-first; introduce typed extensions only when the admitted Clay domain proves they are required.

10. **BASE semantic freeze vs ambiguous legacy G9.** Current BASE direction says freeze semantics and compile; a late ClayCode worker found three legacy rule lines with multiple plausible AST meanings. Resolution: fail closed on ambiguous legacy rules, freeze authoritative intent explicitly, then preserve it through typed PredicateIR/ConstraintIR. Do not infer intended semantics from formatting alone.

## No contradiction interpreted as refutation without discriminating evidence

All unresolved alternatives remain `OPEN_ALTERNATIVE`, `NOT_SELECTED`, or bounded negative results. No canonical scientific promotion is made in this run.