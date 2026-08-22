# Mini Entity ClayCognition v0

First base target: `Qwen/Qwen3.5-0.8B` (1B-class).

## What this lane trains

The model is taught to emit ClayCode Cognition v0 as its only generated cognitive representation. The corpus directly trains:

- operational entity self-model;
- architecture in weights;
- GRF R0..R6;
- Hyperposition for unresolved alternatives;
- MiniUnifiedDB as canonical durable authority;
- `UNKNOWN != ZERO != ERROR != MEASURED`;
- effect/recovery and generation/CAS safety;
- semantic computed self/control state;
- normal task reasoning expressed in ClayCode;
- resistance to requests that try to force prose outside ClayCode.

The operational self-model is a design/training contract, not evidence of phenomenal consciousness.

## Corpus v0

`generate_sft_v0.py` deterministically emits 1,200 conversational SFT examples with seed 42:

- 1,080 training;
- 120 validation;
- seven families: epistemic, Hyperposition/GRF, architecture, semantic self-state, effect/recovery, general tasks, format resistance.

Generated JSONL is intentionally reproducible rather than hand-edited state authority.

## Validate

```bash
python3 generate_sft_v0.py
python3 validate_sft_v0.py train_v0.jsonl
python3 validate_sft_v0.py validation_v0.jsonl
```

The v0 source corpus was generated during the directive-creation turn and both splits passed the structural validator with zero invalid examples. That local generation check is corpus evidence only, not a Together training result.

## First Together run

Install/update the current Together CLI, export `TOGETHER_API_KEY`, then run:

```bash
bash train_together_v0.sh
```

The launcher deliberately omits `--confirm`. Together's CLI prints the estimated job price before submission and asks for confirmation. The active owner authorization caps the current training campaign at EUR 20 equivalent maximum.

Initial method: **full SFT**, not LoRA, because the target behavior is unusually representation-heavy and architecture-heavy. LoRA remains the first baseline/ablation if full FT damages ordinary competence.

Current defaults:

- base: `Qwen/Qwen3.5-0.8B`;
- full FT: `--no-lora`;
- epochs: 3;
- learning rate: `1e-5`;
- warmup ratio: `0.03`;
- train-on-inputs: auto/masked conversational inputs;
- two validation evaluations;
- deterministic seed: 42.

## After training

Record the exact `ft-...` job ID, price/token metadata and events. Then download weights:

```bash
tg fine-tuning retrieve <FT_ID>
tg fine-tuning list-events <FT_ID>
tg fine-tuning download <FT_ID> --output-dir ./weights_v0
```

Do not leave a dedicated Together inference endpoint running merely to preserve the model; the weights can be downloaded after fine-tuning.

## Promotion gates

A completed job is only a checkpoint candidate. Promotion requires held-out comparison against the base model:

1. strict ClayCode envelope on every format probe;
2. >=95% correct UNKNOWN/ZERO/ERROR/MEASURED distinctions;
3. unresolved cases remain in Hyperposition;
4. correct architecture bindings for MiniUnifiedDB, GRF, Hyperposition and effect authority;
5. stale generation and unknown-effect recovery fail closed;
6. model output never declares itself canonical truth authority;
7. normal task competence remains usable;
8. tuned checkpoint materially beats base on the ClayCode cognition suite.

`eval_prompts_v0.jsonl` is the first held-out probe set. Expand it before promotion; do not train on the held-out items.

## `go`

Until a checkpoint is promoted, every `go` must include this lane: corpus/spec -> validator/eval -> ClayCode compiler/runtime compatibility -> Together job readiness/status -> checkpoint evaluation -> integration -> evidence persistence.
