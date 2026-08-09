# Needle Deep-Fusion Hypothesis Matrix

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: `r2 · 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Subject: Frank H-WP-04 Needle boundary. Research Entity remains separate from Frank.

## Evidence-driven hypotheses

| ID | Hypothesis | Current status | Falsifier / next test |
|---|---|---|---|
| H-NDL-01 | A deterministic fail-closed wrapper can make Needle output structurally safe without changing Needle weights. | STRONGLY SUPPORTED COMPONENT | Run real checkpoint output through wrapper; validator unsafe escape rate must remain 0 over audited eval + fuzz. |
| H-NDL-02 | Frank/OpenAI-style `parameters.properties` must be normalized to Needle-flat parameters before current upstream `constrained.py`. | CONFIRMED IMPLEMENTATION REQUIREMENT | Upstream changes to correctly consume `properties` would require version-profile migration, not silent behavior change. |
| H-NDL-03 | Needle constrained decoding alone cannot guarantee JSON/tool validity. | CONFIRMED NEGATIVE | Current code fails open off-trie/empty-trie and constraint activation depends on exact compact markers. |
| H-NDL-04 | Blind encoder truncation is unsafe for the tool catalogue; complete-catalog fit must be checked before inference. | CONFIRMED IMPLEMENTATION REQUIREMENT | Exact tokenizer measurement with official tokenizer; a complete shortlist/full set must fit or call is rejected/escalated. |
| H-NDL-05 | Needle's own contrastive head can act as an inference-time tool retriever, reducing the 51-tool catalogue before generative routing without retraining Needle. | PLAUSIBLE / HIGH VALUE | Measure audited recall@k and downstream accuracy for k={4,8,12,16,24}; reject if relevant-tool recall cannot reach near-lossless target. |
| H-NDL-06 | Full-51 training and top-k inference are compatible: the old objection to prefiltering during training does not establish that inference-only retrieval is harmful. | PLAUSIBLE | Same checkpoint, full-51 generation vs contrastive top-k generation on identical audited cases; paired error and latency analysis. |
| H-NDL-07 | Tool descriptions are simultaneously useful semantic signal and a source of ambiguity/manipulation; description policy must be experimentally optimized rather than universally removed. | STRONGLY SUPPORTED BY EXTERNAL WORK / UNTESTED ON NEEDLE | Factorial: full descriptions vs compressed discriminative descriptions vs names+params only, controlling tool set and language. |
| H-NDL-08 | A raw Needle probability/margin is not a calibrated correctness probability. Pre-constraint scores can support abstention only after held-out calibration. | STRONGLY SUPPORTED GENERAL ML / NEEDLE-SPECIFIC UNTESTED | Capture pre-mask logits; reliability diagram, ECE/Brier, risk-coverage; compare max logit, margin, entropy, normalized-logit scores. |
| H-NDL-09 | Confidence after constrained masking is an invalid primary confidence surface because grammar masking can distort probability mass. | PLAUSIBLE / LITERATURE-SUPPORTED | Log both pre- and post-mask scores; compare error prediction and risk-coverage. |
| H-NDL-10 | Selective routing (Needle only on high-confidence cases, fallback otherwise) can improve risk at reduced coverage. | PLAUSIBLE | Freeze target error, measure coverage; no threshold chosen before audited calibration set exists. |
| H-NDL-11 | German zero-shot remains a hard empirical risk; aliases/descriptions may matter more than tokenizer coverage alone. | OPEN / PROJECT HISTORY NEGATIVE | Run official checkpoint on audited German paraphrase set, English aliases, German names, bilingual descriptions and code-switch cases. |
| H-NDL-12 | The project’s old 90% gate and later no-finetuning decision may be jointly infeasible for a 26M-class SLM; this must be treated as a falsifiable combination, not assumed. | OPEN | Zero-shot first; if below gate, compare retrieval/alias/description inference methods before reconsidering training policy. |
| H-NDL-13 | Existing 328-case labels contain enough known reference errors to materially bias a 90% gate. | CONFIRMED LABEL-QUALITY RISK | Audit every disagreement in high-confusion pairs and a random clean sample; version corrected gold set before model comparison. |
| H-NDL-14 | Alias normalization must be bidirectional, collision-checked, versioned and hash-bound. | CONFIRMED IMPLEMENTATION REQUIREMENT | Mutation test future registry names; any many-to-one normalized collision must fail closed. |
| H-NDL-15 | An ONNX implementation can serve as a second runtime for differential inference testing. | PLAUSIBLE / EXTERNAL PARITY EVIDENCE | JAX vs ONNX identical tokenizer/query/tool JSON, greedy unconstrained and wrapper-validated constrained paths; compare logits/tokens/receipts. |
| H-NDL-16 | Checkpoint provenance must be pinned; arbitrary pickle loading is incompatible with a hardened harness. | CONFIRMED SECURITY REQUIREMENT | Verify official SHA256/source before pickle; prefer safetensors/ONNX/CQ4 safe transport where runtime permits. |
| H-NDL-17 | Needle must remain proposal-only: routing quality cannot confer execution authority. | OWNER-FIXED + IMPLEMENTED | Every decision receipt authority `NONE`, effect_eligible false, external authorization/effect gate mandatory. |
| H-NDL-18 | Retry-by-shrinking the candidate list can help only if each removal is provenance-bound and never deletes the correct tool silently. | OPEN | Compare deterministic shortlist/retry policies on audited cases; log candidate recall each round and fallback when unsure. |

## Counterhypotheses preserved

1. Top-k retrieval can reduce accuracy by excluding the correct tool; context savings alone do not justify it.
2. Removing descriptions can harm zero-shot semantics, especially for ambiguous names.
3. English aliases may improve Needle but can create translation/argument-value errors on German requests.
4. Constrained decoding can make invalid continuations impossible yet still steer probability toward a semantically wrong valid call.
5. Raw token confidence can be miscalibrated; a high margin may still correspond to a wrong tool under distribution shift.
6. The 90% target may be unreachable zero-shot for the unchanged checkpoint; wrapper hardening fixes structure, not semantic route accuracy.
7. The current Python constraint bug may not exist in Cactus' production runtime; do not generalize beyond the inspected implementation without direct Cactus execution.
8. ONNX parity reported by its port maintainers is strong replication evidence but not yet independent reproduction by this Harness worker.

## Experiment matrix locked for next executable checkpoint availability

- Catalogue: full-51-minimal / full-51-descriptions / retrieved-k={4,8,12,16,24}
- Language: original German query / normalized German / English-translated query / code-switch controls
- Names: Frank names / deterministic English Needle aliases
- Decoder: upstream constrained on/off, always followed by fail-closed validator
- Confidence: pre-mask max logit / margin / entropy / normalized-logit score; post-mask retained only as diagnostic
- Routing: no abstention / calibrated selective abstention at several risk targets
- Gold: original labels vs audited labels, with disagreement ledger
- Runtime: JAX/Flax vs ONNX differential when binaries are locally available
- Safety: malformed JSON, whitespace variants, unoffered/blocked tools, unknown/missing/type-wrong args, alias collision, toolset tamper, budget overflow, stale version/hash

No hypothesis above is promoted to Frank architecture merely because it is attractive. Promotion requires the stated discriminating tests.
