# Qwen3.5-0.8B direct Together lane

Status: SOURCE CANDIDATE — no authenticated preflight or paid training yet.
Date: 2026-08-22

Primary paid-training base for the owner-requested approximately-1B generic ClayCode cognition experiment: `Qwen/Qwen3.5-0.8B`.

Together's current supported-model table lists this model for Full fine-tuning. The direct native lane removes the old Qwen2.5-0.5B BYOM architecture/template blocker from the ~1B paid lane while preserving the same application-neutral cognition target: ClayCode only, GRF R0..R6, Hyperposition, typed omega, runtime-bound identity/job/personality, MiniUnifiedDB truth/state authority, and deterministic effect admission.

The launcher uses current SDK/API contracts:
- `fine_tuning.model_limits(model_name=...)`, requiring Full support;
- price estimate with files/model/epochs/evals plus nested `training_method={method:sft, train_on_inputs:auto}` and `training_type={type:Full}`;
- billed create additionally binds random seed, learning rate and warmup ratio;
- deprecated `lora`, top-level `train_on_inputs`, and BYOM source/template fields are absent;
- after create, the exact provider job is retrieved and its training/validation files, model, epochs, evals and random seed must match the campaign before it is considered identity-verified.

Paid create is preflight-only by default and requires exact corpus gates, provider file validation, estimate <= USD 18 within the EUR 20 campaign ceiling, exact fingerprint confirmation, provider/local duplicate fences, a private fsynced CREATE_ARMED intent, zero-retry billed create, and UNKNOWN_REMOTE_CREATE after ambiguous transport outcomes.

Promotion still requires trained artifact identity, held-out/OOD/compositional tuned-vs-base-vs-larger evaluation, Q4_K_M, measured peak process RSS <1 GiB at context 2048, and real generic local_exec integration without MiniUnifiedDB reset.

## Global unusual-experiment slot

This lane defines **no additional unusual experiment**. Current main #870 reconciled the single unusual experiment for this user-triggered `go` as the Qwen2.5-0.5B versus current Together-template BYOM architecture falsifier. Any checks in this direct 0.8B lane are ordinary deterministic safety regressions only.
