# Trigger 2 — Together Qwen3.5-0.8B public full-FT contract v1

Status: **PUBLIC-PRIMARY-SOURCE CONTRACT / NO PROVIDER EXECUTION**  
Date: 2026-08-25  
Trigger: `2` / `triggerwort 2`  
Program: EntityOS + HCU  
Implementation codename: Xeno  
Canonical owner authority observed: `60a81a1eafed6d878b7b27bc074ebf01924528ae`  
Trigger-2 branch observed before this delta: `bfb500a42b0d2cf6d461c4764dccc5fb686ccab4`  
Supervisor observed: `8.78` / `FREE_ONLY`

## Purpose

Close only the provider facts that can be established from current public primary documentation, while preserving the separate pre-job account/API/runtime gate. No Together credential was read, no Together API request was made, no dataset was uploaded, and no job was created.

## 1. Direct catalog full-FT route — CLOSED AT PUBLIC-DOC SCOPE

Together's current `Supported models` page says its tables list every base model available through the fine-tuning API. In the **Full fine-tuning** table it currently lists:

- organization: Qwen;
- model: `Qwen3.5 0.8B`;
- API ID: `Qwen/Qwen3.5-0.8B`;
- SFT max context: `131072`;
- DPO max context: `131072`;
- max packed SFT batch: `8`;
- max packed DPO batch: `8`;
- min batch: `8`.

Provider fact classification:

`Qwen/Qwen3.5-0.8B -> PUBLIC_DOC_FULL_FT_SUPPORTED`

This closes the prior statement `exact Together Qwen3.5-0.8B full-FT support UNKNOWN` **for the public catalog path only**. It does not establish account eligibility, current quota/credits, exact live model limits, dataset acceptance, or a successful job.

Primary source:

- https://docs.together.ai/docs/fine-tuning/supported-models

## 2. Full-FT method must be explicit

Together's current CLI documentation states that `--lora/--no-lora` forces LoRA/full training and that the API otherwise defaults to LoRA on most base models.

Therefore the frozen Trigger-2 job candidate must contain an explicit full-training choice equivalent to:

`training_method = SFT`

`lora = false`

A job configuration that silently relies on provider auto-detection is not admissible for the one-shot Xeno full-FT run.

The same documentation currently gives general fine-tuning controls for epochs, learning rate, scheduler, warmup, gradient clipping, weight decay, seed, packing, max sequence length, input masking, validation/evaluation, checkpoints, and `from_hf_model` / `hf_model_revision`.

Provider-wide defaults or bounds are **not** silently converted into model-specific optimal hyperparameters.

Primary source:

- https://docs.together.ai/reference/cli/finetune

## 3. Vision scope — text-centric target by design

Official Qwen configuration identifies Qwen3.5-0.8B as `Qwen3_5ForConditionalGeneration` with a language core plus vision configuration. The language core has hidden size `1024`, `24` hidden layers, and a repeating hybrid layer map of three `linear_attention` layers followed by one `full_attention` layer, six times, with `full_attention_interval = 4` and native `max_position_embeddings = 262144`.

Together's CLI exposes `--train-vision/--no-train-vision` for vision-language models and currently defaults vision training to `false`.

Current Xeno owner target is shared-state cognition/protocol behavior, not a visual-perception training objective. The Trigger-2 **candidate recipe therefore freezes vision training OFF as a project design decision unless a newer owner instruction makes visual cognition part of the first accepted Xeno target**.

This does not assert that the vision encoder is irrelevant to Qwen generally; it prevents unrequested multimodal scope from consuming the one-shot specialization budget.

Primary sources:

- https://huggingface.co/Qwen/Qwen3.5-0.8B/raw/main/config.json
- https://docs.together.ai/reference/cli/finetune

## 4. Pretrained Base challenger — BYOM route remains conditional

Trigger 2 still compares exactly two candidate starting checkpoints:

1. `Qwen/Qwen3.5-0.8B-Base`
2. `Qwen/Qwen3.5-0.8B`

Together documents a BYOM flow in which a Together catalog model supplies the training template while `from_hf_model` supplies the actual Hugging Face weights. Its documentation explicitly uses `Qwen/Qwen3.5-9B` + `Qwen/Qwen3.5-9B-Base` as the example and requires architecture/size/context compatibility.

However, the generic requirements on the same page also describe BYOM as `CausalLM only`, while the official Qwen3.5-0.8B Base configuration is a conditional-generation/VLM architecture. The 9B Qwen3.5 Base example makes a same-family Base route plausible, but this contract does **not** infer exact 0.8B BYOM acceptance from analogy.

Classification:

`Qwen/Qwen3.5-0.8B-Base -> PUBLIC_DOC_BYOM_ROUTE_PLAUSIBLE__EXACT_08B_ACCEPTANCE_PENDING`

Required later pre-job discriminator, only after execution authority permits provider access:

- query current fine-tuning support/model-limits for the exact template;
- validate the exact pinned Base revision against BYOM architecture/size/context rules;
- preview/tokenize the frozen candidate dataset without creating a job;
- record exact provider response and cost estimate;
- fail closed on any mismatch.

Primary source:

- https://docs.together.ai/docs/fine-tuning/byom

## 5. Current public pricing contract

Together's current pricing page states standard supervised fine-tuning pricing for models up to 16B as:

- LoRA: `$0.48 / 1M processed tokens`;
- **Full fine-tuning: `$0.54 / 1M processed tokens`**;
- minimum fine-tuning job charge: **`$4.00`**.

It defines processed-token cost basis as training dataset tokens multiplied by epochs plus validation tokens multiplied by evaluation count. Hosting/deployment is a separate cost surface and is not required for the intended local Xeno checkpoint path.

At the current $0.54/M rate, the raw standard full-SFT token charge reaches the $4 minimum at approximately `7.407407M` processed tokens. **This is a cost crossover, not a data target.** Trigger 2 must never pad or duplicate low-value rows to approach the minimum; family diversity, causal ancestry, hard negatives and evaluation coverage outrank token volume.

Primary sources:

- https://www.together.ai/pricing
- https://support.together.ai/articles/7922061943-fine-tuning-pricing

## 6. Provider ceiling != chosen training context

The current Together public full-FT ceiling for Qwen3.5-0.8B is `131072` SFT tokens. Official Qwen config exposes native language context `262144`.

Neither number is the Trigger-2 training sequence target.

Required rule:

`chosen_max_seq_length = smallest empirically sufficient value that covers the intended HCU/Xeno trajectory distribution without destructive truncation`

The dataset compiler must measure token-length percentiles and truncation risk before freezing this field. Long native context must not be used as justification for expensive long-sequence training when HCU episodes are shorter.

## 7. Candidate provider recipe surface

The current pre-job candidate recipe is now constrained as follows:

```text
training_objective: supervised fine-tuning
training_type: full
lora: false
vision_training: false unless newer owner target requires vision
catalog candidate: Qwen/Qwen3.5-0.8B
catalog full-FT public support: CONFIRMED
catalog SFT provider ceiling: 131072
catalog packed batch range: exactly 8 in current public table
Base candidate: Qwen/Qwen3.5-0.8B-Base
Base provider route: BYOM challenger
Base exact 0.8B BYOM acceptance: PENDING
model/checkpoint/tokenizer/config revisions: MUST_BE_HASH_PINNED
max_seq_length: DATA_DERIVED_NOT_PROVIDER_MAX_BY_DEFAULT
n_epochs: UNFROZEN; compare 1 vs 2 initially
learning_rate: UNFROZEN; conservative zero-cost/proxy-informed search before one job
scheduler: UNFROZEN; cosine vs linear challenger
warmup: UNFROZEN
packing: UNFROZEN; decide from length/family leakage analysis
train_on_inputs: format-dependent; freeze after tokenizer preview
validation/eval/checkpoints: MUST detect overfit/forgetting within one-shot budget
paid job: FORBIDDEN under current supervisor
```

## 8. Closed vs open gates after this delta

### Closed at source/public-documentation scope

- post-trained Qwen3.5-0.8B exists as official Qwen artifact;
- Qwen3.5-0.8B hybrid language architecture shape is source-observed;
- Together publicly lists `Qwen/Qwen3.5-0.8B` under **Full fine-tuning**;
- current public SFT context and batch limits are known for that catalog path;
- explicit `--no-lora` requirement for deterministic full-FT intent is documented;
- BYOM mechanism and same-family Qwen3.5 Base example are documented;
- current standard full-FT pricing/cost formula/minimum charge are publicly documented.

### Still open

- exact zero-cost Base-vs-posttrained behavioral baseline;
- non-persisting adaptation/specialization proxy;
- exact Base 0.8B BYOM acceptance at live provider boundary;
- exact provider model-limits at the future pre-job instant;
- tokenized frozen-dataset preview and provider estimate;
- exact training revision and selected starting checkpoint;
- Qwen3.5 hybrid-site activation/J-Space semantics;
- sealed family-level holdout;
- final dataset mixture/curriculum/hyperparameters;
- physical GRID10 post-training acceptance;
- owner authorization for paid execution.

## 9. Authority and credit boundary

Supervisor `8.78` is `FREE_ONLY`. Therefore this run performs **zero** credential lookup, Together API preflight, upload, job creation, paid inference or paid training.

Credits after this contract:

- public provider documentation progress: `1`;
- provider executable/runtime credit: `0`;
- Qwen3.5 model runtime credit: `0`;
- Qwen3.5 J-Space runtime credit: `0`;
- checkpoint selection credit: `0`;
- training credit: `0`;
- physical GRID10 credit: `0`;
- whole EntityOS/HCU credit: `0`.

## 10. Next highest-information free gate

Do **not** spend another Trigger-2 cycle rediscovering catalog support.

Next free gate remains the exact same frozen Base-vs-posttrained baseline protocol on an authorized zero-cost runtime surface, now using the pinned official candidate identities already recorded by Trigger 2. In parallel, deterministic dataset work may proceed on evidence census, family dedupe/coverage and the JSONL+ancestry compiler because none of those require a provider account.
