# ATOMIC FINAL REPORT — Counterfactual Effect Antichain (CEA-001)

## Decision
**NO ARCHITECTURE PROMOTION. Status: SUPPORTED_SYNTHETIC_PROXY_RETEST.**

CEA targets the open Frank v0.1 gap between an authorized external attempt and a verified, provenance-bound DONE state. Current scalar `OUTCOME_UNKNOWN` is replaced only as a research possibility by a finite reduced set of still-possible outcome worlds. Trusted identity-bound observations monotonically eliminate worlds. Retry is legal only when it is safe in every surviving world; VERIFIED success requires singleton expected-world collapse plus independent evidence; DONE still requires provenance-bound UnifiedDB re-entry.

## Live collision handling
During this invocation ECT-001, SCF-001 and MCM work landed concurrently. The candidate was narrowed after refresh. CEA does not infer or repair an unresolved Needle CallContract; it consumes an exact contract or fails closed, leaving ECT's contract-tomography lane separate. CEA does not replace SCF's semantic-integrity hypothesis or CJC/MCM transport/coordination candidates.

## Proxy measurements
Five deterministic seeds x 30,000 cases = 150,000 synthetic effect outcomes across three known and one declaratively specified OOD provider contract.

- CEA resolved 100% with 100% correctness among resolved cases and 0 unsafe retries.
- Strong precompiled conventional control resolved 100% on known providers with the same mean observation cost (1.566 units) but 0% on the OOD provider because it had no handler.
- CEA resolved 100% of OOD cases from the contract data without changing control-flow code.
- Python p50 decision latency: scalar 949 ns; precompiled control 3523 ns; CEA 4150 ns. CEA is slower.
- Serialized recovery-state shadow: 116 B scalar versus 237 B CEA, 2.04x amplification.
- 10,000 stale-epoch, stale-provider-contract and shuffled-attempt binding mutations were rejected in the proxy.
- Causal ablation: replacing universal retry safety with 'retry if any surviving world is safe' produced 50.31% unsafe retries in 20,000 adversarial ambiguous-world cases; the universal rule produced 0.
- Negative epistemic control: false but structurally well-formed observation truth caused wrong resolution in 97.51% of 10,000 cases. CEA therefore does not solve external evidence trust.

## Interpretation
The strongest conventional counterhypothesis survives substantially. On known providers it matches CEA correctness and observation cost while running faster and using less state. The only surviving advantage measured here is generic interpretation of a declarative OOD provider recovery contract. This may be valuable for Frank's multi-provider effect fabric, but it is not yet enough for promotion.

## Novelty
Possible-world belief states, idempotency/reconciliation, exactly-once recovery, and idempotence verification are established. No equivalent complete Frank-specific composition was found in the searched scope, so the candidate remains `NOVEL_COMBINATION_CANDIDATE`, not world-first.

## Strongest next falsifier
Use a harmless reversible write fixture on the accepted Hostinger Ubuntu target. Inject a disconnect/timeout after provider dispatch but before durable local outcome. Compare CEA against a conventional provider-specific reconciler using exact current request/auth/reservation/provider-contract identities. Measure duplicate side effects, unresolved rate, number/cost of provider reads, p50/p95/p99 CPU latency, RSS, crash/restart recovery, stale evidence rejection and the final VERIFIED -> provenance-bound UnifiedDB re-entry -> DONE chain. If the conventional reconciler matches CEA under an OOD/new-provider contract with less complexity, CEA should be archived as NO_GAIN.