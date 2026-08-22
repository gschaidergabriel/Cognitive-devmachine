# Qwen3.5-0.8B direct Together training lane

Status: SOURCE CANDIDATE — provider preflight and paid training have NOT run.
Date: 2026-08-22

## Decision

For the owner-requested approximately-1B ClayCode-only cognition experiment, use Together's native fine-tuning base:

`Qwen/Qwen3.5-0.8B`

This replaces the blocked Qwen2.5-0.5B BYOM path as the primary paid-training lane. It does not rewrite the corpus semantics, MiniUnifiedDB authority, effect authority, or application-neutrality contract.

Why:
- Together's current supported-model table explicitly lists `Qwen/Qwen3.5-0.8B` for Full fine-tuning;
- the current table does not list Qwen2.5-0.5B as a native fine-tuning base;
- direct native Full-FT removes the unresolved Qwen2.5 architecture/template compatibility class;
- 0.8B is the smallest currently documented native Qwen Full-FT entry and is close to the owner's approximately-1B target.

Primary upstream evidence refreshed 2026-08-22:
- https://docs.together.ai/docs/fine-tuning/supported-models
- https://docs.together.ai/docs/fine-tuning/supervised
- https://docs.together.ai/docs/fine-tuning/lora-vs-full
- https://docs.together.ai/docs/fine-tuning/pricing
- current Together API/SDK fine-tuning model-limits, price-estimate and create contracts.

## Canonical training data input

The direct 0.8B lane reuses the leakage-free `claycog-sft/v2` corpus. The model change tests capacity/provider admission, not a different cognition language.

Current canonical invariants remain:
- 1,650 examples;
- 1,485 unique train + 165 unique validation;
- zero exact cross-split overlap;
- zero prompt cross-split overlap;
- ClayCode-only targets;
- runtime-only identity/job/application binding;
- GRF/Hyperposition/omega safety semantics.

## Current API contract

The launcher is deliberately split between preflight cost estimation and billed create because the provider schemas are not identical.

Model admission:
- SDK-v2 call: `fine_tuning.model_limits(model_name="Qwen/Qwen3.5-0.8B")`;
- require `supports_full_training=True` and concrete `full_training` limits.

Price estimate:
- exact uploaded training/validation file ids;
- model;
- epochs/evals;
- `training_method={"method":"sft","train_on_inputs":"auto"}`;
- `training_type={"type":"Full"}`.

The estimate endpoint does not receive seed/LR/warmup.

Billed create additionally binds:
- `random_seed`;
- `learning_rate`;
- `warmup_ratio`;
- checkpoint count and suffix;
- the same nested SFT method and explicit Full training type.

Deprecated/ambiguous `lora`, top-level `train_on_inputs`, `from_hf_model`, `hf_model_revision` and template-pair fields are absent by design.

## Paid-create contract

A billed create is admitted only after:
1. exact SFT v2 regeneration and cross-split validation;
2. exact paid base binding;
3. current provider Full-FT model limits;
4. server-side file validation;
5. exact provider price estimate;
6. price <= USD 18 and within the owner's EUR 20 campaign ceiling;
7. operator binds `CLAYCOG_CREATE_FINGERPRINT` to the exact printed campaign fingerprint;
8. no matching campaign exists in provider job history;
9. no local create-intent ledger exists for the same campaign;
10. a 0600 exclusive local `CREATE_ARMED` record is fsynced;
11. billed SDK client uses `max_retries=0`;
12. any transport exception becomes `UNKNOWN_REMOTE_CREATE` and forbids blind retry.

## Promotion boundary

Native catalog support is not a tuned-model PASS. Promotion still requires trained artifact identity, strict ClayCode/OOD and compositional evaluation, tuned-vs-base and larger-model comparison, GGUF Q4_K_M, measured process RSS under 1 GiB at context 2048, and real generic `local_exec` integration without MiniUnifiedDB reset.

## Exactly one unusual experiment for this user-triggered `go`

The globally selected experiment is `PAID_BASE_SUBSTITUTION_LESION`, first established by the parallel current-go worker.

Intervention: set `CLAYCOG_08B_MODEL=Qwen/Qwen3.5-2B` and invoke the launcher without provider credentials.

Prediction: static paid-base validation returns `MODEL_OVERRIDE_REJECTED` before secret/provider access.

This fusion branch may only **reproduce/regress the same intervention**. It does not consume or invent a second unusual experiment.
