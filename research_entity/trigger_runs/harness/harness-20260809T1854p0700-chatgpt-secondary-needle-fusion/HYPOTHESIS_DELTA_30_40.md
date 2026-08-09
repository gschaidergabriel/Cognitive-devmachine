# Needle Hypothesis Delta H-NDL-30..40

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Status: evidence-ranked hypotheses/corrections, not architecture promotion unless marked confirmed requirement.

| ID | Hypothesis / finding | Current status | Discriminating next test |
|---|---|---|---|
| H-NDL-30 | Cactus' Needle JSON-Schema adapter is semantically better than the Python path because it flattens `properties`, but its current string-scanner extraction is whitespace/escaping sensitive; Frank should emit a canonical compact runtime payload rather than arbitrary equivalent JSON. | CONFIRMED CURRENT-RUNTIME REQUIREMENT | Differential test compact canonical payload vs serializers with ordinary whitespace/escapes/types; require identical reconstructed Needle-flat schema. |
| H-NDL-31 | The exact-marker whitespace weakness is runtime-family independent across the inspected Python and Cactus Needle constrainers. | CONFIRMED CURRENT-SOURCE NEGATIVE | Re-run against pinned Cactus binary when available; legal whitespace mutation must never become an authority bypass because post-validator remains mandatory. |
| H-NDL-32 | Cactus' Needle response parser/syntax sanitizer is insufficient as Frank's acceptance boundary: offered-tool membership, required arguments and duplicate-key uniqueness are not guaranteed there. | CONFIRMED CURRENT-SOURCE REQUIREMENT | Inject unknown tool, missing required argument and duplicate-key calls into real Cactus Needle response path; H1 post-validator must reject all. |
| H-NDL-33 | Runtime profiles must reject schemas the current runtime cannot preserve safely instead of silently degrading them. | CONFIRMED IMPLEMENTATION REQUIREMENT | Schema fuzz across quotes, backslashes, braces, enums, types and serializer whitespace; compare pre-runtime canonical contract to runtime-reconstructed contract. |
| H-NDL-34 | Needle is a single-shot reflex, not a dialogue-memory component. Context-dependent/deictic requests must be resolved by an external normalizer into a self-contained current intent or bypass Needle to the 4B path. | OWNER-CONCEPT + CURRENT CACTUS SOURCE CONFIRMED | Longitudinal dialogue fixtures: `das von vorhin`, `mach weiter`, pronoun/coreference and changed-state cases; unresolved cases must never enter Needle. |
| H-NDL-35 | A compressed first-statement tool description may preserve most useful lexical retrieval signal while reducing catalogue size materially. | PLAUSIBLE, SMALL DIAGNOSTIC SUPPORT | Exact Needle-tokenizer size plus Needle/Cactus hybrid recall/route accuracy: full description vs first statement vs learned/manual discriminative compact text. |
| H-NDL-36 | Removing descriptions entirely is likely harmful for zero-shot/retrieval semantics even when it saves context. | STRONG SMALL DIAGNOSTIC + EXTERNAL SUPPORT | End-to-end official Needle comparison names-only vs descriptions on audited German/English tool-positive set. |
| H-NDL-37 | Fixing Cactus BM25 Unicode tokenization alone is unlikely to be the dominant performance lever; its direct benefit may be modest compared with embeddings and description semantics. | COUNTERHYPOTHESIS SUPPORTED BY SMALL DIAGNOSTIC | Hybrid Cactus RAG A/B with current byte tokenizer vs Unicode-aware lexical arm while holding embeddings and tool text fixed. |
| H-NDL-38 | A descriptive Needle-only alias for `crl_session` may help English routing but the effect is local/small and must not be generalized into a registry rename. | SMALL TARGETED SUPPORT / NOT PROMOTED | A/B paraphrase set separating CRL from `daily_check`, German and English, with same checkpoint/tool descriptions. |
| H-NDL-39 | Frank's Needle contract should accept at most one call. `[]` and every rejected/ambiguous output require 4B fallback; a valid single route remains proposal-only and still needs the independent effect gate. | OWNER-CONCEPT + IMPLEMENTED H1 CONTRACT | Real checkpoint/Cactus output replay, including multi-call adversarial outputs and no-tool cases; require deterministic fallback semantics. |
| H-NDL-40 | Retrieval failure, unresolved context or over-budget selected catalogue must fail closed *before* Needle instead of inheriting upstream fail-open-to-all/truncation behavior. | IMPLEMENTED H1 PREFLIGHT | Real tokenizer + Cactus/Needle retrieval failure injection; verify preflight receipt blocks invocation and sends the request to fallback. |

## New executable support

- `needle_runtime_contract.py` v0.4 fixes `FRANK_MAX_NEEDLE_CALLS = 1` and adds `fallback_required` to `NeedleDecisionReceipt`.
- 43 combined runtime-contract/profile unit/adversarial tests PASS after this change.
- fresh v0.4 mutation sanity: 25,000 valid + 25,000 invalid cases; 0 false rejects / 0 false accepts in the generated domain.
- `needle_ingress_preflight.py` adds a pre-Needle admissibility receipt for context resolution, retrieval success and exact complete encoder budget; 8/8 tests PASS.
- Historical 793-tool-token assumption + 200-token reserve leaves only 30 tokens for the query; 31 query tokens is a deterministic preflight rejection.

## Architecture consequence, still evidence-gated

The strongest current boundary is now:

`dialogue/current input -> context/intent normalization -> H1 ingress preflight -> runtime-profile canonicalization -> optional audited retrieval -> pinned Needle -> strict single-shot validator -> NeedleDecisionReceipt(authority=NONE, fallback_required=...) -> typed Clay ingress -> independent effect authority`

Retrieval method, confidence threshold, description compression and aliases remain experimental variables. The fail-closed outer boundary, single-shot/fallback semantics and provenance binding are implementation requirements supported by project contract plus executable counterexamples.
