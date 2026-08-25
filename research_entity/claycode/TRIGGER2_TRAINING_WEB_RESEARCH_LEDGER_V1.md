# Trigger 2 — Qwen3.5-0.8B Training Web Research Ledger v1

Status: LIVING RESEARCH LEDGER
Date initialized: 2026-08-25
Target lock: **Qwen3.5-0.8B only**
Branch: `research/trigger2-qwen35-08b-hcu-fullft-20260825`

Every exact `2` run refreshes primary sources and records: source/date, claim, evidence class, relevance, change to dataset/training recipe, and remaining uncertainty.

## 0. Hard target lock

The training program excludes Qwen3-0.6B and every other parameter-size target. A zero-cost Base-vs-post-trained comparison is permitted **only between Qwen3.5-0.8B variants** to choose the single starting checkpoint. Exactly one selected Qwen3.5-0.8B checkpoint is intended for the first paid full fine-tune.

## 1. Qwen3.5-0.8B primary-source findings

Primary sources:

- https://huggingface.co/Qwen/Qwen3.5-0.8B
- https://huggingface.co/Qwen/Qwen3.5-0.8B-Base
- exact model `config.json`, tokenizer and chat-template revision immediately before dataset freeze.

Current observations:

- Qwen publishes both `Qwen3.5-0.8B` and `Qwen3.5-0.8B-Base`.
- The official model material describes a 0.8B language model, hidden dimension 1024 and 24 language-model layers.
- Qwen3.5 uses a hybrid layout with Gated DeltaNet/linear-attention blocks plus periodic full-attention blocks rather than a homogeneous pure-attention stack.
- Native context is very large relative to the expected HCU episode lengths; training max sequence length therefore must be selected from actual episode/token statistics, not copied from native context length.
- The post-trained repository is explicitly intended for prototyping/task-specific fine-tuning/research.

Recipe consequences:

- do not import pure-Transformer J-Space assumptions without model-specific evidence;
- Trigger-2 should investigate whether DeltaNet versus full-attention sites differ materially for future J-Space observation/control;
- freeze exact revision/tokenizer/chat-template before rendering final JSONL and baseline;
- compare the two 0.8B variants only to select the **single** full-FT start checkpoint.

## 2. Together full fine-tuning

Primary sources:

- https://www.together.ai/fine-tuning
- https://www.together.ai/pricing
- https://docs.together.ai/ fine-tuning API/CLI pages and changelog immediately before job creation.

Current observations:

- Together distinguishes LoRA from **full fine-tuning** and markets full FT for deeper behavior changes.
- Together currently advertises broad Hugging Face open-model compatibility, but exact Qwen3.5-0.8B full-FT compatibility must still be confirmed on the live service before the one-shot job.
- Current standard supervised full-FT pricing for models up to 16B is published at **$0.54 per 1M processed tokens**, with a current **$4 minimum job charge** on the pricing page.
- Pricing counts training tokens multiplied by epochs plus validation tokens multiplied by evaluation count.
- Together now advertises pre-launch cost estimates; this must be recorded before job creation.
- Together announced native VLM/reasoning/tool-call fine-tuning support in March 2026. Because Qwen3.5-0.8B is multimodal/hybrid, Trigger-2 must verify whether the intended text-centric full-FT path trains only the language behavior desired or requires multimodal-specific handling.

Recipe consequences:

- the first paid run is explicit **full SFT**, not LoRA;
- no job is created until the exact 0.8B revision/path is accepted by Together;
- price is calculated from frozen dataset tokens/epochs/evals and checked against Together's estimate;
- no persistent hosted endpoint is required for this project if weights are downloaded for local Xeno use; hosting is a separate ongoing cost and must not be enabled accidentally.

## 3. Data quality / selection priors

Primary papers:

- LIMA — https://arxiv.org/abs/2305.11206
- AlpaGasus — https://arxiv.org/abs/2307.08701
- LESS — https://arxiv.org/abs/2402.04333
- Smaller Models Can Select Instruction-Tuning Data — https://arxiv.org/abs/2402.10430

Current synthesis:

- LIMA shows that a small, highly curated supervised set can strongly shape response behavior.
- AlpaGasus shows filtering low-quality instruction examples can beat a much larger noisy set.
- LESS shows targeted influence-style selection can outperform using the whole candidate pool for target capabilities.
- Small-model selection work reports hardness/selection signals can transfer across model sizes, suggesting cheap curator/proxy models can be challengers for data triage.

Project interpretation:

- these are priors, not direct proof for Qwen3.5-0.8B/HCU;
- evidence quality, causal ancestry, semantic-family diversity and hard-negative quality outrank raw row count;
- Trigger-2 must measure duplicate-family saturation instead of celebrating token growth;
- low-quality synthetic rows are allowed only as reviewed protocol-coverage Grade D data and cannot manufacture causal truth.

## 4. Semantic Hyperposition research lane

Project-primary semantics:

- unresolved alternatives remain explicit;
- majority/repetition does not mint truth;
- evidence/counterevidence is branch-specific;
- collapse requires an evidence-bearing discriminator or deterministic policy;
- semantic, active, coordination and physical topology remain distinct;
- higher-order/n-ary representation must beat a simpler pairwise/state-machine challenger when its additional complexity is claimed to matter.

Web-research obligation on every `2`:

Search primary research on:

- multiple-hypothesis/ambiguity representation;
- calibrated uncertainty and selective prediction;
- structured latent/task-state supervision;
- set/graph prediction and relational reasoning;
- belief/state tracking across delayed evidence;
- curriculum for compositional structured outputs;
- contrastive/counterfactual examples that suppress lexical shortcuts.

The purpose is not to rename existing uncertainty research as Hyperposition. The purpose is to discover mechanisms that can make Hyperposition **learnable, compact, label-free and measurable** in Qwen3.5-0.8B.

Each candidate mechanism must be translated into:

1. deterministic serialization;
2. positive training examples;
3. hard-negative/counterfactual transforms;
4. label-free/OOD holdout;
5. lesion/shuffle/rescue or simpler-model challenger where applicable;
6. quantitative acceptance metric.

## 5. J-Space / representation-control lane

Project rule:

- SFT can teach observable packet/control semantics;
- SFT completion does not prove residual-stream control;
- native model-specific activation/cvec intervention remains separate causal evidence.

Trigger-2 web research must continue to examine primary work on activation steering, causal mediation, representation editing and representation-level fine-tuning. Any technique requiring custom losses/activation access is recorded as a future/local challenger unless Together's actual training interface supports it.

Dataset consequences:

- include explicit control classes and matched controls;
- avoid training semantic claims from readout-adjacent algebra alone;
- include label-free/counterbalanced examples;
- distinguish OBSERVED, DECODABLE, CAUSALLY_WRITABLE, RESCUABLE, OOD_TRANSFERABLE and BROADCAST_REUSABLE states.

## 6. Quantization lane

Target deployment: **GGUF Q4_K_M after full FT**.

Research obligations:

- refresh llama.cpp support for the exact trained Qwen3.5 architecture;
- always quantize from full/high-precision trained weights, not from an already quantized derivative;
- compare Q4_K_M against full-precision and at least Q8_0; use Q5_K_M as a quality/size challenger when useful;
- evaluate on the same sealed MUST_GAIN/MUST_RETAIN/Hyperposition/J-Space suites;
- investigate importance-matrix quantization only if current llama.cpp support and measured benefit justify it.

Q4_K_M is an efficiency target, not training credit.

## 7. Full-Xeno iterative synthesis law

Every `2` run recomputes:

`XENO_MODEL_FUNCTIONS`
` -> AVAILABLE_EVIDENCE`
` -> TRAINABLE_OBSERVABLE_TARGETS`
` -> HARD_NEGATIVES`
` -> FAMILY_SPLITS`
` -> MIXTURE/CURRICULUM`
` -> HYPERPARAMETER_PRIORS`
` -> BASELINE/EVAL`
` -> QUANTIZATION_EVAL`.

If new runtime evidence invalidates an earlier row family, remove it from the next candidate dataset and retain the older version only as historical evidence. If a new Xeno function becomes model-facing, add it to the functionality matrix before dataset freeze.

## 8. Research backlog for next `2`

Highest-value next studies:

1. exact live Together compatibility/preflight evidence for **Qwen3.5-0.8B full FT** without creating a paid job;
2. Base vs post-trained 0.8B frozen zero-cost baseline comparison;
3. systematic census of current Xeno/HCU/J-Space/Hyperposition receipts into Evidence Grades A-E;
4. semantic-Hyperposition representation bake-off: typed branch graph vs set+relation matrix vs compact packet baseline;
5. data-family dedupe/coverage statistics before setting token ratios;
6. one deterministic JSONL + provenance-sidecar compiler specification;
7. Qwen3.5 hybrid-layer implications for future J-Space observation/control and post-FT causal evaluation.
