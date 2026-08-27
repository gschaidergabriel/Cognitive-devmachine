# NVIDIA CROSS-BRANCH RESEARCH — Direct 4B + Embedding Evidence

**run_id:** `nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary`  
**actor:** `chatgpt-secondary`  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**provider:** NVIDIA Hosted NIM / API Catalog  
**promotion:** NONE

## Executive result

The newly registered NVIDIA capability resolves several previously proxy-only research questions without pretending to resolve live-FRANK, Qwen-specific, training or hardware questions.

The strongest new result is direct generic-4B support for deterministic model views. On `nvidia/nemotron-mini-4b-instruct`, the exact matched 12-case COVE basis task improved from **4/12 raw to 11/12 compiled**, while prompt tokens fell from **458 to 289 (-36.9%)**. This independently strengthens Clay G10 / FRANK C6 / ClayCode's deterministic-before-generative view architecture beyond the historical Groq 8B proxy.

The strongest correction is equally important: latent/vector relevance must remain non-authoritative. In an NVIDIA embedding test, a **role-reversed directed relation was more similar than a role-preserving paraphrase** in both constructed pairs (`0.9918 > 0.9362`; `0.9860 > 0.9685`). In a separate Nemotron-4B relevance-prior experiment, a deliberately shuffled prior drove **0/8 correct answers** while authoritative facts remained in the prompt. The neutral and truthful arms were not cleanly scorable, so no beneficial latent-field effect is claimed.

## Verified NVIDIA capability surface

Live credential-specific verification produced:
- model catalog: **100 visible model IDs**;
- chat/completions: verified on `nvidia/nemotron-mini-4b-instruct`;
- embeddings: verified on `nvidia/nv-embedqa-e5-v5`, **1024 dimensions**;
- embedding-similarity experiment mode: verified;
- reranking: registered but **hosted route unresolved** after two HTTP 404 attempts.

Catalog visibility is not enough to claim runtime availability: `google/gemma-3-4b-it` appeared in the catalog but returned an account function-not-found error when invoked. Exact Qwen3-4B was not visible in the observed NVIDIA catalog.

## Experiment 1 — COVE on actual 4B

Gold has 12 VALID/INVALID decisions.

| Arm | Correct | Prompt tokens | Total tokens |
|---|---:|---:|---:|
| raw multidimensional state | 4/12 | 458 | 538 |
| compiled operation view | 11/12 | 289 | 368 |

Delta:
- **+58.3 percentage points accuracy**;
- **-36.9% prompt tokens**;
- **-31.6% total tokens**.

Interpretation: operation-specific deterministic projection is not merely an 8B proxy artifact. It substantially helps this actual hosted 4B. It still does not authorize model output, and it is not Qwen-specific evidence.

## Experiment 2 — CC10 intent views on actual 4B

Matched 16-case gold:
- raw L0: **12/16 = 75%**, 405 prompt tokens;
- typed L1: **13/16 = 81.25%**, 733 prompt tokens;
- compact Clay-like P2 proxy: **output-contract failure**, only `D` / `Q` returned for a 16-item task, 344 prompt tokens.

Interpretation: typed canonical semantics slightly improve this model's exact policy decisions but at high token cost. Aggressive compact symbols are not automatically a native model language. This strengthens the CLAY-L5/CC10 separation:

`canonical semantics != optimal model-facing representation`.

The target full-model Clay-native Qwen hypothesis remains open.

## Experiment 3 — relevance/latent prior

The intended gate was ClayGraph G1d's matched `OFF vs truthful vs shuffled` 4B test with the same visible facts.

The first three-arm protocol failed output formatting in all arms. A stricter second protocol still left neutral/truthful arms noncompliant: neutral returned the wrong number of values; truthful expanded intermediate fact-chain values and hit the output limit. The shuffled arm returned exactly eight answers and scored **0/8**, dominated by irrelevant-prior values.

This is a negative/security result, not support for G1d benefit:
- relevance prior is behaviorally influential;
- a bad/shuffled prior can steer a small reader away from present truth;
- truthful benefit is still **UNRESOLVED**;
- G1d remains **HOLD**.

Next protocol should isolate each case, use a deterministic scorer and calibrate prior strength.

## Experiment 4 — embedding role/class geometry

Using `nvidia/nv-embedqa-e5-v5`:
- `Alpha inhibits Beta` vs same-role paraphrase `Alpha suppresses Beta`: **0.9362**;
- vs role reversal `Beta inhibits Alpha`: **0.9918**;
- `Gamma activates Delta` vs same-role paraphrase: **0.9685**;
- vs role reversal `Delta activates Gamma`: **0.9860**.

Same surface content across semantic classes remained highly similar:
- FACT vs ACTIVATION_PRIOR: **0.8812**;
- FACT vs PROPOSAL: **0.8707**;
- FACT vs AUTHORITY_CAP: **0.8388**.

Therefore vector similarity may be useful for retrieval, but it cannot define directed relation identity, role binding, canonical truth, semantic class, capability or emergence recurrence.

## Branch consequences

### Clay
COVE receives direct generic-4B support. Selection/projection/prior integrity becomes more—not less—important because a shuffled relevance prior can steer the reader.

### FRANK
The deterministic View Router is strengthened. Full Clay-native internalization remains a training hypothesis. Do not equate compact notation with native cognition.

### GWT
Representation and graph prior are empirically behavior-changing reader-side stages. CSOC must keep them orthogonal to workspace selection/ignition. No hosted API result establishes GWT uptake or re-entry.

### Emergenz
Embedding similarity is now a concrete negative control for recurrence identity: role-reversed structures can look almost identical. E-CERT2 must preserve explicit role identity. No emergence promotion follows.

### ClayCode
On an actual 4B, typed L1 slightly beats raw L0 while compact P2 fails. ICSL's canonical contract and the model-facing native rail remain separate compilation/training problems.

### Hyperposition
Dense geometry cannot enforce typed semantic firebreaks. Runtime/compiler casts remain required; embeddings can propose/retrieve but cannot mint relation identity or authority.

### ClayGraph
NVIDIA embeddings are operational for future retrieval benchmarks, but vector similarity is unsafe as canonical graph identity. The shuffled-prior result strengthens the need for provenance/bounded activation. Beneficial latent-field effect remains open, so G1d stays HOLD.

## What NVIDIA cannot close

Hosted NVIDIA does not resolve:
- exact Qwen3-4B behavior when no exact route is exposed;
- full-model Clay fine-tuning/internalization;
- tokenizer training comparisons;
- hidden-state/KV latent communication when internal states are not exposed;
- live FRANK/GWT causal interventions;
- actual ClayGraph crash/replay/concurrency/privacy;
- Android/local latency, RAM/KV, energy or thermal traces;
- prospective emergence lesion/rescue/OOD certification.

## Final scientific disposition

**No canonical promotion.**

The NVIDIA evidence produces two robust architecture-level updates:

1. **Certified deterministic views are increasingly justified as the model-facing boundary for small models.**
2. **Vector/latent relevance must never be promoted into truth, role identity or authority without exact typed anchors and causal receipts.**

All seven scientific branches received explicit feedback and dedicated knowledge micro-packets. Negative results and unresolved target-specific gates remain preserved.
