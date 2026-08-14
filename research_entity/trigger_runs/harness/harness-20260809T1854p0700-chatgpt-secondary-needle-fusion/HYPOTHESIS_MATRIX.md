# Needle Deep-Fusion Hypothesis Matrix

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: `r2 · 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
Subject: Frank H-WP-04 Needle boundary. Research Entity remains separate from Frank.

## Evidence-driven hypotheses

| ID | Hypothesis | Current status | Falsifier / next test |
|---|---|---|---|
| H-NDL-01 | A deterministic fail-closed wrapper can make Needle output structurally safe without changing Needle weights. | STRONGLY SUPPORTED COMPONENT | Run real checkpoint output through wrapper; validator unsafe escape rate must remain 0 over audited eval + fuzz. |
| H-NDL-02 | Frank/OpenAI-style `parameters.properties` must be normalized to Needle-flat parameters before current upstream Python `constrained.py`. | CONFIRMED IMPLEMENTATION REQUIREMENT | Upstream/runtime profile that consumes JSON Schema natively requires explicit migration and differential validation. |
| H-NDL-03 | Needle Python constrained decoding alone cannot guarantee JSON/tool validity. | CONFIRMED NEGATIVE | Current code fails open off-trie/empty-trie and constraint activation depends on exact compact markers. |
| H-NDL-04 | Blind encoder truncation is unsafe for the tool catalogue; complete-catalog fit must be checked before inference. | CONFIRMED IMPLEMENTATION REQUIREMENT | Exact tokenizer measurement with official tokenizer; a complete shortlist/full set must fit or call is rejected/escalated. |
| H-NDL-05 | Needle's own contrastive head can act as an inference-time tool retriever, reducing the 51-tool catalogue before generative routing without retraining Needle. | PLAUSIBLE / HIGH VALUE | Measure audited recall@k and downstream accuracy for k={4,8,12,16,24}; reject if relevant-tool recall cannot reach near-lossless target. |
| H-NDL-06 | Full-51 text-generation training and top-k inference are compatible enough to test: the old objection to prefiltering does not establish that inference-only retrieval is harmful. | PLAUSIBLE / HISTORICAL RATIONALE WEAKENED | Same checkpoint, full-51 generation vs retrieval+generation on identical audited cases; paired accuracy/latency/token analysis. |
| H-NDL-07 | Tool descriptions are simultaneously useful semantic signal and a source of ambiguity/manipulation; description policy must be experimentally optimized rather than universally removed. | STRONGLY SUPPORTED BY EXTERNAL WORK / UNTESTED ON NEEDLE | Full descriptions vs compressed discriminative vs bilingual vs names+params only. |
| H-NDL-08 | A raw Needle probability/margin is not a calibrated correctness probability. Pre-constraint scores can support abstention only after held-out calibration. | STRONGLY SUPPORTED GENERAL ML / NEEDLE-SPECIFIC UNTESTED | Reliability/ECE/Brier/risk-coverage on audited held-out set. |
| H-NDL-09 | Confidence after constrained masking is an invalid primary confidence surface because grammar masking can distort probability mass. | PLAUSIBLE / LITERATURE-SUPPORTED | Log pre/post-mask scores and compare error prediction/risk-coverage. |
| H-NDL-10 | Selective routing (Needle only on high-confidence cases, fallback otherwise) can improve risk at reduced coverage. | PLAUSIBLE | Freeze acceptable risk, measure coverage; no threshold chosen before calibration. |
| H-NDL-11 | German zero-shot remains a hard empirical risk; aliases/descriptions may matter more than tokenizer coverage alone. | OPEN / PROJECT HISTORY NEGATIVE | Official checkpoint on audited German paraphrase, English alias, bilingual and code-switch arms. |
| H-NDL-12 | The old 90% semantic gate and later no-finetuning decision may be jointly infeasible for a 26M-class SLM. | OPEN | Zero-shot + retrieval/alias/description arms first; only then reconsider training policy. |
| H-NDL-13 | Existing 328-case labels contain enough known reference errors to materially bias a 90% gate. | CONFIRMED LABEL-QUALITY RISK | Audit all high-confusion disagreements plus random clean sample; version corrected gold set. |
| H-NDL-14 | Alias normalization must be bidirectional, collision-checked, versioned and hash-bound. | CONFIRMED IMPLEMENTATION REQUIREMENT | Registry mutation tests; any many-to-one collision fails closed. |
| H-NDL-15 | An ONNX implementation can serve as a second runtime for differential inference testing. | PLAUSIBLE / EXTERNAL PARITY EVIDENCE | JAX vs ONNX exact input, logits/tokens/receipts. |
| H-NDL-16 | Checkpoint provenance must be pinned; arbitrary pickle loading is incompatible with a hardened harness. | CONFIRMED SECURITY REQUIREMENT | Verify source/hash before pickle; validate safe-format/runtime parity before substitution. |
| H-NDL-17 | Needle must remain proposal-only: routing quality cannot confer execution authority. | OWNER-FIXED + IMPLEMENTED | Every receipt authority NONE, effect_eligible false, external authority/effect gate mandatory. |
| H-NDL-18 | Retry-by-shrinking the candidate list can help only if each removal is provenance-bound and never silently deletes the correct tool. | OPEN | Log candidate recall per round and deterministic fallback. |
| H-NDL-19 | Needle's contrastive retrieval head cannot replace the no-tool decision because no-tool examples have no positive tool and are excluded from contrastive batches and retrieval evaluation. | CONFIRMED CODE-LEVEL LIMIT | Keep separate no-tool/fallback; retriever tested only as candidate ranker. |
| H-NDL-20 | The documented 720-example Frank mini-finetune could not have trained the contrastive head under Aug-4 defaults: ~600 train / batch 64 / 1 epoch ≈ 9 steps while contrastive loss runs only every 1000 steps. | STRONGLY SUPPORTED HISTORICAL CORRECTION | Recover exact CLI/log overrides; under defaults contrastive updates = 0. |
| H-NDL-21 | Frank needs a dedicated no-tool metric in checkpoint selection/evaluation because stock Needle quick finetune evaluation and best-checkpoint metric exclude empty/no-tool examples. | CONFIRMED EVALUATION REQUIREMENT | Add no-tool precision/recall/false-trigger gate to any Frank-specific evaluation; reject checkpoint if it regresses. |
| H-NDL-22 | Reverse aliasing must occur only after strict structured parse; upstream invalid-JSON string replacement is unsafe for argument-value integrity. | CONFIRMED IMPLEMENTATION REQUIREMENT | Fuzz malformed output containing alias words in values; H1 wrapper must never mutate values. |
| H-NDL-23 | Frank must own/version normalization because upstream snake-case normalization can silently collapse distinct tool names. | CONFIRMED IMPLEMENTATION REQUIREMENT | Future-registry collision tests and toolset hash binding. |
| H-NDL-24 | The historical 793-token minimal catalogue does not satisfy the later >=200-token-headroom gate for ordinary long queries: it leaves only 30 query tokens. | CONFIRMED ARITHMETIC CONSTRAINT | Exact official-tokenizer distribution over real German queries; if many exceed 30, availability mask/retrieval is required for the frozen headroom goal. |
| H-NDL-25 | Cactus-native Tool RAG is a realistic candidate prefilter because it already implements hybrid embedding+BM25/RRF top-k over tool name+description, but its fail-open-to-all behavior must be wrapped by Frank's complete-budget gate. | STRONGLY SUPPORTED RUNTIME CANDIDATE / NOT YET NEEDLE-EVAL VALIDATED | Run Cactus Needle on audited set for k={2,4,8,12,16}; on retrieval failure, verify Frank rejects/escalates rather than overflowing context. |
| H-NDL-26 | Cactus Tool-RAG BM25 tokenization is lossy for German UTF-8 because it byte-tokenizes with ASCII `isalnum`; English/bilingual retrieval text or a Unicode-aware lexical tokenizer may improve recall. | CONFIRMED TOKENIZATION LOSS / PERFORMANCE EFFECT OPEN | A/B exact Cactus tool-RAG recall@k using German vs English/bilingual descriptions; 65/945 registry content words contain non-ASCII and are altered, including `für`/`größe` disappearing entirely. |
| H-NDL-27 | `crl_session` is semantically opaque to an English-trained router; source-resolved meaning is Consciousness Research Loop, a weekly Claude-Code research session. A descriptive Needle-only alias such as `run_weekly_research_session` may improve routing. | SOURCE MEANING CONFIRMED / ALIAS BENEFIT OPEN | A/B `crl_session` vs descriptive alias on paraphrases that distinguish it from `daily_check`. |
| H-NDL-28 | Cactus' generic confidence threshold is not a calibrated Needle correctness probability: normal path derives confidence from `1 - entropy`, while explicit `p_wrong` is a separate probe mechanism used where available. | CONFIRMED RUNTIME SEMANTICS / NEEDLE CALIBRATION OPEN | Audit Cactus Needle confidence against correctness; compare first-token/mean entropy, pre-mask margin and task-level errors before choosing threshold. |
| H-NDL-29 | Tool-description lexical similarity explains some confusion families but not the historically strong `system_check`↔`moeglichkeiten` error; label/training conflict remains a more plausible cause there. | SUPPORTED BY REGISTRY ANALYSIS / CAUSAL CLAIM OPEN | On corrected gold data, perturb descriptions while holding labels/checkpoint fixed and measure pairwise confusion. |

## Counterhypotheses preserved

1. Top-k retrieval can reduce accuracy by excluding the correct tool; context savings alone do not justify it.
2. Removing descriptions can harm zero-shot semantics, especially for ambiguous names.
3. English aliases may improve Needle but can create translation/argument-value errors on German requests.
4. Constrained decoding can make invalid continuations impossible yet still steer probability toward a semantically wrong valid call.
5. Raw token confidence can be miscalibrated; a high margin may still correspond to a wrong tool under distribution shift.
6. The 90% target may be unreachable zero-shot for the unchanged checkpoint; wrapper hardening fixes structure, not semantic route accuracy.
7. Python constraint bugs do not automatically imply identical bugs in Cactus' separate C++ constraint/runtime implementation.
8. ONNX parity reported by its port maintainers is external implementation evidence, not yet independent reproduction by this Harness worker.
9. Historical Frank finetune command-line overrides may have changed epochs/batch size; H-NDL-20 remains conditional until exact run logs are recovered.
10. Cactus Tool RAG may outperform Needle's contrastive head, underperform it, or fail differently; neither retriever is promoted without audited recall@k.
11. Lossy UTF-8 BM25 tokens do not automatically imply ranking loss because the same transformed fragments can match on both query and description and embedding RRF carries higher weight.
12. A descriptive `crl_session` alias could collide semantically with `daily_check`; A/B disambiguation is mandatory.

## Experiment matrix locked for next executable checkpoint availability

- Catalogue: full-51-minimal / full-51-descriptions / retrieved-k={2,4,8,12,16,24}
- Retriever: none / Needle contrastive / Cactus hybrid Tool RAG
- Language: original German / normalized German / English-translated / code-switch controls
- Retrieval text: German / English / bilingual / Unicode-normalized lexical arm
- Names: Frank names / deterministic English Needle aliases / `crl_session` A/B alias
- Decoder: Python/JAX constrained on/off where relevant; Cactus native constraints; fail-closed post-validator always
- Confidence: pre-mask max logit / margin / entropy / Cactus confidence; post-mask diagnostic only until calibrated
- Routing: no abstention / calibrated selective abstention at frozen risk targets
- Retrieval evaluation: tool-positive recall@k/MRR; no-tool remains separate gate/fallback
- Gold: original labels vs audited/versioned labels with disagreement ledger
- Runtime: JAX/Flax vs Cactus/CQ4 vs ONNX differential when exact binaries are locally available
- Safety: malformed JSON, whitespace variants, unoffered/blocked tools, unknown/missing/type-wrong args, duplicate keys, nonfinite values, alias collision, toolset tamper, budget overflow, retrieval failure, stale source/checkpoint/tokenizer hashes

No hypothesis above is promoted to Frank architecture merely because it is attractive. Promotion requires the stated discriminating tests.
