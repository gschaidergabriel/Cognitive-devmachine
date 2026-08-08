# ClayGraph G3 — Negative Results / Blockers

Run: `claygraph-20260809T0149p0700-chatgpt-secondary-sol-04`  
Candidate: `IBCA-G3 — Intent-Bound Causal Assembly`  
Decision boundary: **OPEN/HOLD; accepted ClayGraph remains G0.**

1. **More graph is not automatically better.** In the 12-question staged current-RAE self-use benchmark, lexical top-1 was 0.916667 while one-hop graph and temporal-fresh graph were 0.833333. A precise FRANK-C9 lookup was pulled toward strongly linked ClayCode neighbors.
2. **Empty admissible memory is a real state.** The first stricter prototype produced an empty trust+intent candidate set and failed at `max(empty)`. This is preserved as a design negative: consequential routing must support `EMPTY_ADMISSIBLE_SET -> ESCALATE/EXACT_VALIDATE`; nearest-neighbor fallback is not semantics.
3. **Hard trust/intent gating has utility cost.** Provisional low-trust but correct memories can be useful for associative cognition. G3 therefore rejects global deletion/censorship and retains `SUPPLEMENT_ONLY` with stricter consequential validation.
4. **CASAR-like validity filtering is not sufficient under deliberately adversarial high-salience poison.** In EXP-G3-INTENT-ASSEMBLY-001 the CASAR proxy selected poison frequently. This construction is intentionally different from G2a and does not refute G2a's original reported proxy results.
5. **G2a-like itemwise utility learning becomes fragile when its verifier is noisy in the G3 construction.** The strongest IBCA advantage partly comes from an embedded structural origin/intent prior; the magnitude is not an unbiased production estimate.
6. **Activation/retrieval success is not task legitimacy.** Live ClayCode Lane D showed in its own constructed domain that capability validity can coexist with intent inadequacy. ClayGraph may preserve/use task-bound influence labels, but cannot infer that this independently proves IBCA.
7. **Graph exposure is not GWT uptake.** GWT R6 explicitly distinguishes addressability, delivery, reconstruction, uptake, causal use, outcome and re-entry. A MemoryInfluenceReceipt cannot claim receiver uptake unless GWT supplies that evidence.
8. **No live target-Qwen/FRANK cognitive benefit was measured.** No production memory corpus, real user task distribution, or consequential effect system was exercised.
9. **No new live database enumeration exists.** The inherited historical 71-store count remains dated; current writer/reader/WAL/backup/privacy/latency topology is unknown.
10. **No formal noninterference/security proof exists.** Zero false accepts in finite constructed cases are not proof against arbitrary prompt injection, semantic poisoning or confused-deputy paths.
11. **No E2B run was executed by this ClayGraph worker.** E2B was not directly exposed in the current worker tool context; local fallback was used. Imported E2B receipts from other provenance-bound runs remain those runs' evidence.
12. **External temporal/graph-memory papers do not transfer their benchmark gains to FRANK.** They motivate mechanism tests only.
13. **Accepted graph is unchanged.** `research_entity/claygraph/CLAYGRAPH_LATEST.claycode.json` remains G0; IBCA-G3 is not promoted.

## Highest-information falsifiers

- Target-Qwen/FRANK factorial: exact vs associative vs consequential tasks × CASAR/IBCA × truthful/shuffled intent binding × stale/poisoned memory, with effect policy fixed.
- Blinded automatically generated RAE corpus where gold and query class are frozen before retrieval.
- Noisy/partial causal-credit test using real outcome attribution rather than synthetic item verifiers.
- Real selection-integrity mutation with authentic records but manipulated graph/query structure.
- Trace-driven crash/replay/rebuild against UnifiedDB placement vectors and graph epochs.
