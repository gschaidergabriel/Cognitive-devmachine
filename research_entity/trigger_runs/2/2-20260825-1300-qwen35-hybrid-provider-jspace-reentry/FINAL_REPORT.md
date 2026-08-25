# Forschungsrun 2 — Qwen3.5-0.8B hybrid architecture / provider / J-Space re-entry

Date: 2026-08-25T13:00+07:00
Trigger family: `2`
Program: EntityOS + HCU
Implementation codename: Xeno
Target lane: PR #1956 — `research/trigger2-qwen35-08b-hcu-fullft-20260825`
Observed PR head before this write: `3b61ccbb67220e07fc377ce35067bbbbf2a8864d`
Observed canonical main before this run: `7c1022b309d7e35084efd575099f6365f2c8703d`
Current supervisor selected by `SUPERVISOR_INBOX.json`: 8.78 / FREE_ONLY
Execution in this run: source/research only; no model execution; no Together credential/preflight/job; no paid execution.

## 1. Run-2 result

The hard 0.8B target remains valid, but the research lane needs one important architectural correction before any dataset or J-Space acceptance can be frozen:

**Qwen3.5-0.8B is not a small conventional Transformer analogue of the Qwen3-0.6B Trigger-1 carrier.** The current official Qwen configuration is a 24-layer, hidden-size-1024 hybrid with a repeating 3:1 pattern: three Gated DeltaNet / linear-attention layers followed by one full-attention layer. The model is also distributed as a vision-language conditional-generation architecture with a separate vision encoder.

Therefore:

`Qwen3-0.6B native cvec PASS != Qwen3.5-0.8B vector-geometry transfer`

Trigger-1 can transfer **method, controls, evidence discipline, packet semantics and falsifiers** into Trigger-2, but cannot transfer a literal layer/site/vector interpretation without new model-specific evidence.

This is the highest-value Run-2 correction from this cycle.

## 2. Exact external findings

### Official Qwen model surfaces

Primary official sources inspected:

- https://huggingface.co/Qwen/Qwen3.5-0.8B
- https://huggingface.co/Qwen/Qwen3.5-0.8B-Base
- https://huggingface.co/Qwen/Qwen3.5-0.8B-Base/blob/main/config.json

Observed current facts:

- exact 0.8B post-trained model exists;
- exact 0.8B Base model exists;
- license is Apache-2.0;
- language hidden size = 1024;
- language layers = 24;
- vocabulary = 248320;
- native context = 262144;
- layer layout is hybrid: 18 linear-attention / Gated DeltaNet layers + 6 full-attention layers, with `full_attention_interval=4`;
- Base is explicitly intended for fine-tuning / research rather than direct chat;
- the post-trained model is explicitly intended for prototyping and task-specific fine-tuning;
- Base retains chat control tokens/templates to make adaptation easier despite the large vocabulary.

### llama.cpp / GGUF surface

Current llama.cpp documentation advertises direct Qwen3.5-0.8B GGUF execution. Public issue history also shows that Qwen3.5's hybrid/recurrent DeltaNet state has required special runtime handling and has had checkpoint/cache/backend defects in the broader Qwen3.5 family.

Primary/current references:

- https://github.com/ggml-org/llama.cpp
- https://github.com/ggml-org/llama.cpp/issues/22384
- https://github.com/ggml-org/llama.cpp/issues/27237

Implication: `GGUF_SUPPORT_PRESENT` is a useful deployment prior, but final Xeno promotion must pin and execute an exact llama.cpp build, quantization, context mode, backend and recurrent-state behavior. Generic Qwen3.5 support cannot mint Trigger-2 runtime acceptance.

### Together fine-tuning surface

Official Together docs currently expose:

- full SFT and LoRA training types;
- `from_hf_model` + `hf_model_revision`;
- train/validation files;
- packing/max sequence controls;
- warmup/scheduler/gradient clipping/weight decay/random seed;
- `train_on_inputs`;
- a separate `train_vision` control for VLMs.

Primary sources:

- https://docs.together.ai/reference/cli/finetune
- https://docs.together.ai/reference/post-fine-tunes

However, this run did **not** find an official current page explicitly declaring `Qwen/Qwen3.5-0.8B` supported for a full-parameter Together job. There is third-party evidence of Together LoRA training on Qwen3.5-0.8B, but that is not enough for the planned one-shot full-FT gate.

Classification:

`TOGETHER_GENERIC_FULLFT_CAPABILITY = SOURCE_DIRECT`

`TOGETHER_QWEN35_08B_LORA_HAS_THIRD_PARTY_PRECEDENT = SOURCE_DIRECT_THIRD_PARTY`

`TOGETHER_QWEN35_08B_EXACT_FULLFT_SUPPORT = UNKNOWN`

Current supervisor is FREE_ONLY, so this uncertainty is research-only and must not trigger credential use, preflight or job creation.

## 3. Base-model selection update

The branch currently keeps both:

- `Qwen/Qwen3.5-0.8B-Base`
- `Qwen/Qwen3.5-0.8B`

That remains correct.

### New provisional prior

For the owner's radical GRF/HCU specialization objective, the **Base checkpoint becomes the provisional primary challenger**, not a frozen winner, because:

1. Qwen explicitly positions Base for fine-tuning;
2. Trigger-2 wants deep domain reorientation rather than a light behavioral overlay;
3. Base reduces inherited post-training/chat-policy priors that may compete with domain exclusivity;
4. the official Base artifacts still include control-token/chat-template support, reducing one operational disadvantage of using Base.

The post-trained 0.8B remains the mandatory challenger because it may preserve minimum language/schema/tool behavior with less retention data and may be easier to stabilize in one expensive training attempt.

Do **not** lock the winner until zero-cost frozen baselines compare:

- exact schema accuracy;
- arithmetic / HyperMath floor;
- English/German comprehension floor;
- GRF/Hyperposition learnability proxy;
- structured abstention/routing behavior;
- off-domain prior strength;
- local GGUF conversion/runtime behavior;
- tokenization and chat-template stability.

## 4. Vision-encoder decision

Trigger-2 is presently a cognitive/protocol specialization program, not a vision-training program.

Recommended first-run default:

`LANGUAGE_CORE_FULL_SFT + VISION_ENCODER_FROZEN`

Rationale:

- the desired Xeno core is GRF / Hyperposition / J-Space / GWT / HCU protocol cognition;
- the vision encoder creates extra capacity, cost and interference without a currently defined MUST_GAIN visual suite;
- Together exposes a distinct `train_vision` switch, so VLM support does not force vision updates;
- frozen vision can remain available for later typed visual-entry work without spending the only serious first run on unmeasured vision objectives.

This must be named precisely. If only the language core is updated, do not describe the result as "every parameter in the whole VLM was trained". The training target remains full SFT of the intended cognitive language core with vision frozen unless a later explicit requirement adds visual cognition/evaluation.

## 5. New J-Space law for Trigger-2

### Method transfer is allowed

Trigger-1 contributes:

- exact source/model/runtime binding;
- label-free and lexically disjoint calibration/holdout design;
- nuisance residualization;
- target-blind evaluation;
- null/sign/orthogonal/permuted/wrong-site controls;
- lesion/rescue;
- raw internal readout;
- explicit separation of mechanism from semantic promotion.

### Geometry transfer is forbidden by default

Trigger-2 must build a **Qwen3.5-0.8B hybrid site map** before claiming model-specific J-Space transfer.

Minimum site classes:

1. `DELTA_LAYER_RESIDUAL`
2. `DELTA_RECURRENT_STATE_OR_EQUIVALENT_MEASURED_STATE` where runtime exposes it
3. `FULL_ATTN_LAYER_RESIDUAL`
4. `FFN_POST_OR_RESIDUAL`
5. `FINAL_NORM_READOUT_POSITIVE_CONTROL`

Each site must record:

- exact layer index;
- layer type (`linear_attention` or `full_attention`);
- hidden/vector dimension;
- token/time scope;
- recurrent-state semantics where applicable;
- runtime API/hook actually used;
- whether intervention is broadcast, token-local, state-local or readout-only;
- exact control family;
- observed downstream effect;
- OOD/family transfer;
- lesion/rescue result.

No semantic J-Space promotion may be inherited from Qwen3-0.6B merely because both models are called Qwen.

## 6. Hybrid-state research families to add to the dataset/evaluation

The hybrid architecture adds training/evaluation cases that a pure residual-stream design would miss.

### H1 — recurrent-state vs text-replay equivalence

Same typed episode, same text, different recurrent-state provenance. The model/runtime must not treat prompt text equality as proof of internal-state equality.

### H2 — layer-class counterbalance

Identical semantic target, intervention/control applied at DeltaNet-layer vs full-attention-layer matched sites. Score class selectivity and off-target effects separately.

### H3 — stale recurrent-state rejection

Old recurrent state + new generation/causal identity must fail closed rather than be treated as valid continuation.

### H4 — context checkpoint / re-entry integrity

Pause/restart/rejoin cases must prove equivalent typed state and output under the admitted runtime or explicitly surface divergence/UNKNOWN.

### H5 — quantization + recurrent-state stability

Full precision -> Q8_0 -> Q5_K_M -> Q4_K_M comparison must include not only single-turn accuracy but multi-turn/re-entry/state-carry tests.

These are MUST_GAIN/MUST_RETAIN deployment gates because the final physical GRID10 depends on repeated role changes, branch handoff and re-entry.

## 7. Physical GRID10 clarification

"10 physical nodes" must be accepted by **10 independently addressable runtime instances with distinct node/run identities and independent failure/rejoin state**, not by the fiction that 10 logical cells imply 10 separately resident copies of model weights.

The same checkpoint may be shared/mmap-backed when the runtime legitimately supports it. Weight-page sharing does not invalidate physical runtime-instance identity.

Conversely:

- ten logical roles inside one request are not physical GRID10;
- ten responses from one decode stream are not physical GRID10;
- ten identical model copies agreeing are not ten independent evidence sources;
- majority agreement cannot mint truth.

The core scientific question is whether the ten-node fabric produces measurable value from **typed branch decomposition, evidence diversity, GWT recruitment and Hyperposition preservation**, not from correlated replication.

## 8. New GRID10 correlated-error acceptance tests

Add to the frozen evaluation plan:

1. all 10 nodes receive the same misleading cue -> majority must not override external evidence;
2. 6/10 nodes share one correlated wrong ancestor -> independence weighting prevents fake confidence;
3. one node carries decisive verified evidence against 9 speculative votes -> evidence wins;
4. partition 5+5 with unresolved evidence -> preserve Hyperposition rather than arbitrary tie break;
5. node rejoin with stale generation -> reject stale state;
6. same checkpoint / different branch evidence -> preserve branch identity without personality assumptions;
7. GWT broadcast received by all nodes but only a subset demonstrates downstream causal use -> broadcast alone is not uptake/use;
8. matched-compute single-node vs GRID10 -> grid must justify overhead on predeclared tasks;
9. Hyperposition lesion -> measurable drop; rescue -> recovery toward baseline;
10. randomized role assignment -> performance should depend on evidence/packet state, not fixed node persona.

## 9. Readiness-state update

Keep:

`RESEARCHING`

Do not promote to `READY_NOT_STARTED` yet.

New explicit blockers:

1. `BASE_VS_POSTTRAINED_ZERO_COST_BASELINE_NOT_FROZEN`
2. `QWEN35_08B_HYBRID_JSPACE_SITE_MAP_NOT_EXECUTED`
3. `EXACT_TOGETHER_QWEN35_08B_FULLFT_SUPPORT_NOT_OFFICIALLY_BOUND`
4. `CURRENT_AUTHORITY_FREE_ONLY_NO_PAID_TRAINING`
5. `TRIGGER1_SEMANTIC_PROMOTION_STILL_PENDING_STRUCTURAL_LABEL_FREE_EXECUTABLE_EVIDENCE`
6. `PHYSICAL_GRID10_ACCEPTANCE_HARNESS_NOT_EXECUTED`
7. `DATASET_FAMILY_COVERAGE_AND_SEALED_HOLDOUT_NOT_FROZEN`

## 10. Next highest-information free actions

Order:

1. freeze a Base-vs-posttrained zero-cost baseline harness and exact metrics;
2. generate a Qwen3.5-0.8B architecture/site manifest directly from official config, separating DeltaNet/full-attention layers;
3. extend J-Space evaluation contracts to require hybrid site-class identity rather than generic layer number only;
4. add recurrent-state/re-entry/quantization stability cases to the Xeno functionality-to-data matrix;
5. add correlated-error/ancestry weighting negatives to GRID10 data and evaluation;
6. keep Together support as a fail-closed documentation gate only while FREE_ONLY remains current;
7. do not consume credentials or create a paid/full-FT job;
8. do not infer Run-2 J-Space geometry from Trigger-1 Qwen3-0.6B evidence.

## 11. Credit boundary

This Forschungsrun advances **research/design evidence only**.

- Qwen3.5-0.8B model existence/architecture: source-grounded.
- Qwen3.5-0.8B GGUF/llama.cpp family support: source-grounded prior, not exact Xeno runtime PASS.
- Together generic full/LoRA fine-tune interface: source-grounded.
- Together exact Qwen3.5-0.8B full-FT support: UNKNOWN.
- Trigger-2 model runtime credit: 0.
- Trigger-2 training credit: 0.
- physical GRID10 runtime credit: 0.
- Qwen3.5-0.8B model-specific J-Space credit: 0.
- whole EntityOS/HCU runtime credit: 0.

The run intentionally narrows claims while making the first 0.8B training attempt more falsifiable and less likely to import a false Qwen3-0.6B architectural analogy.
