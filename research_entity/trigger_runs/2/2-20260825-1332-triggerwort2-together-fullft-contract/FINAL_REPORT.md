# Trigger 2 — Together Qwen3.5-0.8B public full-FT contract run

Date: 2026-08-25  
User trigger: `triggerwort 2`  
Program: EntityOS + HCU  
Implementation codename: Xeno  
Target lane: PR #1956 / `research/trigger2-qwen35-08b-hcu-fullft-20260825`  
Canonical owner main observed at orientation: `60a81a1eafed6d878b7b27bc074ebf01924528ae`  
Trigger-2 branch observed before this run's writes: `bfb500a42b0d2cf6d461c4764dccc5fb686ccab4`  
Supervisor observed: `8.78 / FREE_ONLY`  
Paid/provider/model execution: **NONE**  
Together credential/preflight/upload/job: **NONE**

## Trigger resolution

Current owner authority on `main` explicitly binds exact trigger `2` to the living Qwen3.5-0.8B full-fine-tuning corpus/recipe/evaluation program for the autonomous shared-state Xeno/HCU target architecture. This run therefore continued PR #1956 and did not treat the trigger as another Qwen3-0.6B structural-cvec experiment.

## Highest-information question selected

The previous Trigger-2 report listed exact Together Qwen3.5-0.8B full-FT support as `UNKNOWN`. That uncertainty directly affects model selection, recipe design and future one-shot training readiness, but it can be partly resolved from current public primary documentation without touching credentials or creating spend.

Question:

`What exact provider facts about Qwen3.5-0.8B full SFT can be closed now from public primary sources, and what must remain a later live pre-job gate under FREE_ONLY?`

## Public primary-source findings

### 1. Post-trained catalog checkpoint — direct full FT confirmed

Together's current Supported Models page says its tables list every base model available through the fine-tuning API. Its **Full fine-tuning** table explicitly lists:

- `Qwen/Qwen3.5-0.8B`;
- SFT max context `131072`;
- DPO max context `131072`;
- packed SFT/DPO batch max `8`;
- min batch `8`.

This changes Trigger-2's provider evidence state from:

`POSTTRAINED_FULL_FT_SUPPORT = UNKNOWN`

to:

`POSTTRAINED_FULL_FT_SUPPORT = PUBLIC_DOC_CONFIRMED`

It grants no account, runtime or job credit.

Source: https://docs.together.ai/docs/fine-tuning/supported-models

### 2. Full FT must be explicit because provider defaults favor LoRA

Together's current CLI docs state that `--lora/--no-lora` forces LoRA/full fine-tuning and that the API defaults to LoRA on most base models when omitted.

Trigger-2 recipe consequence:

`training_method = SFT`

`lora = false`

must be explicit in the frozen job configuration. Auto-detection is not accepted for the intended one-shot full-FT run.

The same docs expose current generic knobs for epochs, LR, scheduler, warmup, gradient clipping, weight decay, seed, packing, max-seq, input masking, evaluation/checkpoints and BYOM fields.

Source: https://docs.together.ai/reference/cli/finetune

### 3. Qwen3.5-0.8B hybrid/VLM structure remains material

Official Qwen config currently shows:

- `Qwen3_5ForConditionalGeneration`;
- language hidden size `1024`;
- `24` language layers;
- `18` `linear_attention` layers;
- `6` `full_attention` layers;
- `full_attention_interval = 4`;
- native language `max_position_embeddings = 262144`;
- an explicit vision configuration.

Together exposes `train_vision` and currently defaults it false for VLMs. Because the current owner target is shared-state cognitive/protocol specialization rather than first-run visual cognition, this run makes `train_vision=false` the **project recipe candidate** unless newer owner authority expands the target.

Source: https://huggingface.co/Qwen/Qwen3.5-0.8B/raw/main/config.json

### 4. Base checkpoint — BYOM is plausible but exact 0.8B admission remains open

Together's current BYOM docs permit a Hugging Face checkpoint to supply actual weights while a Together catalog model supplies the training template. The documented example is exactly a Qwen3.5 post-trained template paired with its `-Base` counterpart (`Qwen3.5-9B` + `Qwen3.5-9B-Base`).

However, the same BYOM page describes generic eligibility as `CausalLM only`, while the official Qwen3.5-0.8B config is conditional-generation/VLM. Therefore this run refuses to infer exact 0.8B Base acceptance from the 9B example alone.

Classification:

`Qwen/Qwen3.5-0.8B-Base = BYOM_ROUTE_PLAUSIBLE__EXACT_08B_LIVE_VALIDATION_PENDING`

This preserves both baseline challengers without granting the Base candidate provider eligibility it has not yet earned.

Source: https://docs.together.ai/docs/fine-tuning/byom

### 5. Current public cost envelope

Together's current pricing page gives standard SFT pricing up to 16B as:

- LoRA `$0.48 / 1M processed tokens`;
- Full FT `$0.54 / 1M processed tokens`;
- minimum job charge `$4.00`.

Current public cost basis is:

`processed_tokens = train_tokens * epochs + validation_tokens * eval_count`

At `$0.54/M`, the raw Full-FT charge reaches `$4` at about `7.407407M` processed tokens. This is recorded only as a cost crossover and explicitly prohibited as a data-volume optimization target.

Sources:

- https://www.together.ai/pricing
- https://support.together.ai/articles/7922061943-fine-tuning-pricing

## Durable deltas written

### Contract

`research_entity/claycode/TRIGGER2_TOGETHER_QWEN35_08B_PUBLIC_FULLFT_CONTRACT_V1.md`

Commit:

`da553d376ec054f701ad8f00df1cba1484f0dcc1`

The contract separates:

- public-documentation facts;
- project recipe decisions;
- provider-live facts that remain unknown;
- execution/spend authority;
- scientific/runtime credits.

### Fail-closed provider recipe candidate

`research_entity/claycode/TRIGGER2_QWEN35_08B_PROVIDER_RECIPE_CANDIDATE_V1.json`

Commit:

`59f896cdc8a357c02df17c79ee55f8fd891488fc`

It freezes only fields justified now:

- Qwen3.5-0.8B target family;
- exactly one checkpoint eventually selected;
- post-trained catalog route;
- Base BYOM challenger route without exact acceptance credit;
- SFT + Full + `lora=false`;
- `train_vision=false` under current owner target;
- current catalog ceiling/batch facts;
- public pricing facts;
- mandatory pre-job fail-closed gates.

It deliberately leaves LR, epochs, scheduler, warmup, packing, max sequence length and other quality-sensitive hyperparameters unfrozen pending data statistics/baselines.

## Scientific interpretation

This is a real training-readiness delta but not model evidence.

The strongest change is epistemic cleanup:

- the post-trained checkpoint's **public provider full-FT compatibility is no longer UNKNOWN**;
- live account/provider acceptance is still unmeasured;
- the Base checkpoint remains a legitimate scientific challenger but its exact provider route is not yet proven;
- provider max context is explicitly separated from the future data-derived training max sequence length;
- Full FT is no longer allowed to accidentally degrade into provider-default LoRA;
- visual fine-tuning is excluded from the current first-run scope unless owner authority changes.

## Remaining blockers

1. exact zero-cost Base-vs-posttrained behavioral baseline;
2. non-persisting specialization/adaptation proxy;
3. exact config/manifest/runtime-consumed-byte identity completion for both candidates;
4. Qwen3.5 hybrid runtime hook/state discovery;
5. model-specific J-Space causal evidence on Qwen3.5-0.8B;
6. Base 0.8B exact BYOM live admission;
7. live provider model-limits/tokenizer-preview/cost estimate at the pre-job instant;
8. evidence-grade census and family dedupe/coverage statistics;
9. deterministic JSONL + ancestry compiler;
10. sealed family-level holdout and final mixture/curriculum/hyperparameters;
11. explicit future paid-job authority;
12. post-FT full-precision acceptance and Q4_K_M regression;
13. physical GRID10 acceptance and matched-compute superiority.

## Next exact free gate

Highest priority remains:

`PINNED QWEN3.5-0.8B BASE VS POSTTRAINED ZERO-COST BASELINE + NON-PERSISTING ADAPTATION PROXY`

using identical frozen packets, exact source/runtime identity and the existing Trigger-2 baseline decision gate.

If no authorized zero-cost model runtime is available in a run, the next useful nonduplicate source task is:

`EVIDENCE GRADE A-E CENSUS -> CAUSAL/SEMANTIC FAMILY DEDUPE -> COVERAGE MATRIX -> JSONL+ANCESTRY COMPILER SPEC`

Do not spend another run rediscovering catalog support.

## Credit delta

- Trigger-2 public provider documentation credit: `+1 bounded source delta`
- checkpoint selection credit: `0`
- Qwen3.5 model runtime credit: `0`
- Qwen3.5 J-Space model runtime credit: `0`
- provider runtime credit: `0`
- training credit: `0`
- paid execution credit: `0`
- physical GRID10 runtime credit: `0`
- whole EntityOS/HCU runtime credit: `0`

Result:

`TRIGGER2_PUBLIC_FULLFT_PROVIDER_CONTRACT_CLOSED__LIVE_PREJOB_AND_MODEL_GATES_OPEN`
