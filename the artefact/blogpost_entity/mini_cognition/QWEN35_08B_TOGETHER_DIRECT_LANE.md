# Qwen3.5-0.8B direct Together training lane

Status: SOURCE CANDIDATE — provider preflight and paid training have NOT run.
Date: 2026-08-22

## Decision

For the owner-requested approximately-1B ClayCode-only cognition experiment, use Together's native fine-tuning base:

`Qwen/Qwen3.5-0.8B`

This is a separate provider-admission lane beside the current Qwen2.5-0.5B BYOM work. It does not rewrite the existing corpus semantics, MiniUnifiedDB authority, effect authority, or application-neutrality contract.

Why this lane exists:

- Together's current supported-model table explicitly lists `Qwen/Qwen3.5-0.8B` for both LoRA and full fine-tuning.
- Together's current table does not list Qwen2.5-0.5B as a native fine-tuning base.
- Direct native fine-tuning removes the unresolved Qwen2.5 -> compatible-template BYOM question.
- 0.8B is the smallest currently documented native Qwen fine-tuning entry and is substantially closer to the owner's approximately-1B target than the 0.5B fallback.

Primary upstream evidence, refreshed 2026-08-22:

- https://docs.together.ai/docs/fine-tuning/supported-models
- https://docs.together.ai/docs/fine-tuning/supervised
- https://docs.together.ai/docs/fine-tuning/lora-vs-full
- https://docs.together.ai/docs/fine-tuning/pricing

## Canonical training data input

The direct 0.8B lane reuses the leakage-free `claycog-sft/v2` corpus rather than minting a provider-specific semantic corpus.

Current main manifest binds:

- total examples: 1,650;
- train: 1,485 unique;
- validation: 165 unique;
- exact cross-split overlap: 0;
- prompt cross-split overlap: 0;
- target representation: ClayCode only;
- identity/job policy: runtime config only.

The model change therefore tests capacity/provider admission, not a different target cognition language.

## Paid-create contract

`launch_together_qwen35_08b_v1.py` is preflight-only by default.

A billed create is admitted only after all of these hold:

1. exact SFT v2 regeneration and cross-split validation;
2. exact model id is `Qwen/Qwen3.5-0.8B`;
3. Together `model_limits` reports `supports_full_training=True`;
4. Together accepts both uploaded files;
5. provider price estimate says the job is allowed;
6. estimated price is <= USD 18;
7. operator binds `CLAYCOG_CREATE_FINGERPRINT` to the exact printed campaign fingerprint;
8. no matching campaign exists in provider job history;
9. no local create-intent ledger exists for the same campaign;
10. a private/exclusive local CREATE_ARMED ledger is persisted;
11. the billed SDK client is constructed with `max_retries=0`;
12. any create transport exception becomes `UNKNOWN_REMOTE_CREATE` and forbids blind retry.

Full fine-tuning is explicit through `lora=False`.

## Promotion boundary

Native catalog support is not a tuned-model PASS.

Do not promote this lane until there is exact evidence for:

- provider preflight on the exact corpus and model;
- exact estimated price and credit/admission result;
- one known provider job id if paid create is authorized;
- training completion and downloadable artifact identity;
- strict ClayCode envelope evaluation;
- held-out/OOD semantic safety evaluation;
- compositional holdout evaluation when the v3 curriculum is admitted;
- base-vs-tuned-vs-larger-model comparison;
- quantized artifact identity;
- measured peak RSS under the owner memory target;
- integration through the existing generic local inference adapter.

## One unusual experiment for this `go`

`PAID_BASE_SUBSTITUTION_LESION`

Intervention: set `CLAYCOG_08B_MODEL=Qwen/Qwen3.5-2B` and invoke the launcher without provider credentials.

Prediction if the paid-base binding is sound: the launcher exits at its static contract with `MODEL_OVERRIDE_REJECTED` before local/provider preflight and therefore cannot upload data or create a paid job for the substituted base.

Counterprediction: if provider/model selection can drift through configuration, execution advances past the static gate. That would reject this launcher design.

This experiment is wired into the PR admission workflow. A workflow definition alone is not execution evidence; only an actually started exact-branch step can support the observation.
