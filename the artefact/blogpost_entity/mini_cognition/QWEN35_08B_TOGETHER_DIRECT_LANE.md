# Qwen3.5-0.8B direct Together lane

Status: SOURCE CANDIDATE — no authenticated preflight or paid training yet.
Date: 2026-08-22

Primary paid-training base for the owner-requested approximately-1B generic ClayCode cognition experiment: `Qwen/Qwen3.5-0.8B`.

Together's current supported-model table lists this model for Full fine-tuning. The direct native lane removes the old Qwen2.5-0.5B BYOM architecture/template blocker while preserving the same application-neutral cognition target: ClayCode only, GRF R0..R6, Hyperposition, typed omega, runtime-bound identity/job/personality, MiniUnifiedDB truth/state authority, and deterministic effect admission.

The launcher uses current SDK/API contracts:
- `fine_tuning.model_limits(model_name=...)`, requiring Full support;
- price estimate with files/model/epochs/evals plus nested `training_method={method:sft, train_on_inputs:auto}` and `training_type={type:Full}`;
- billed create additionally binds random seed, learning rate and warmup ratio;
- deprecated `lora`, top-level `train_on_inputs`, and BYOM source/template fields are absent.

Paid create is preflight-only by default and requires exact corpus gates, provider file validation, estimate <= USD 18 within the EUR 20 campaign ceiling, exact fingerprint confirmation, provider/local duplicate fences, a private fsynced CREATE_ARMED intent, zero-retry billed create, and UNKNOWN_REMOTE_CREATE after ambiguous transport outcomes.

Promotion still requires trained artifact identity, held-out/OOD/compositional tuned-vs-base-vs-larger evaluation, Q4_K_M, measured peak process RSS <1 GiB at context 2048, and real generic local_exec integration without MiniUnifiedDB reset.

Exactly one unusual experiment for this user-triggered go was already selected by the parallel worker: `PAID_BASE_SUBSTITUTION_LESION` (`CLAYCOG_08B_MODEL=Qwen/Qwen3.5-2B`). This branch may reproduce only that same lesion as regression and must reject it with `MODEL_OVERRIDE_REJECTED` before secret/provider access.
