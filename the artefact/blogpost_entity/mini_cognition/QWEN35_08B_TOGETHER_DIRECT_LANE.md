# Qwen3.5-0.8B direct Together lane

Status: OWNER_SELECTED — source/preflight lane only; no authenticated preflight or paid training yet.
Date: 2026-08-22
Owner selection: Variant 1 — `Qwen/Qwen3.5-0.8B` Full Fine-Tuning on Together.

Primary paid-training base for generic ClayCode cognition: `Qwen/Qwen3.5-0.8B`.

Together's current supported-model table explicitly lists `Qwen/Qwen3.5-0.8B` for Full fine-tuning. This direct native lane therefore replaces the old Qwen2.5-0.5B BYOM architecture/template route for the paid campaign while preserving the same application-neutral cognition target: ClayCode only, GRF R0..R6, Hyperposition, typed omega, runtime-bound identity/job/personality/tools, MiniUnifiedDB truth/state authority, and deterministic effect admission.

The launcher uses current SDK/API contracts:
- exact model is hard-bound to `Qwen/Qwen3.5-0.8B`;
- live fine-tuning model limits must advertise Full training support;
- price estimate binds files/model/epochs/evals plus nested `training_method={method:sft, train_on_inputs:auto}` and `training_type={type:Full}`;
- billed create additionally binds random seed, learning rate and warmup ratio;
- BYOM source/template fields are absent by design;
- after create, the exact provider job is retrieved and its training/validation files, model, epochs, evals and random seed must match the campaign before it is considered identity-verified.

Paid create is preflight-only by default and requires exact corpus gates, provider file validation, estimate <= USD 18 within the EUR 20 campaign ceiling, exact fingerprint confirmation, provider/local duplicate fences, a private fsynced CREATE_ARMED intent, zero-retry billed create, and UNKNOWN_REMOTE_CREATE after ambiguous transport outcomes.

**Owner-selection boundary:** choosing this lane authorizes the model/provider direction, not a billed job. The final `--create` remains blocked until the training/evaluation bundle is hardened and the owner gives an explicit run/cost authorization for the exact preflight fingerprint.

Promotion still requires trained artifact identity, held-out/OOD/compositional tuned-vs-base-vs-larger evaluation, Q4_K_M, measured peak process RSS <1 GiB at context 2048, and real generic local_exec integration without MiniUnifiedDB reset. If the larger 0.8B checkpoint falsifies the existing RSS gate, report that result rather than silently changing the gate.

## Evaluation hardening before paid create

The compositional Hyperposition -> R6 -> omega OOD family must be scored against the **exact typed omega vector** (operation, every typed argument/value, schema, authority expression, generation expression, all five validators, exactly one commit). Marker-only semantic credit is insufficient.

## Coordination note

This owner-selection update performs no unusual experiment. Cross-organ unusual-experiment uniqueness can only be adjudicated when the orchestration layer supplies an exact shared `macrocycle_id`; timestamps or nearby commits are not a valid substitute.
