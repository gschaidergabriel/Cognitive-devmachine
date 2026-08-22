# GENERIC 0.5B CLAYCODE-ONLY COGNITION MODULE — OWNER DIRECTIVE

Status: CURRENT ADDENDUM
Owner directive date: 2026-08-22
Parent program: `MINI_ENTITY_PIPELINE_ALL_IN_ONE`

## Product direction

Build one reusable half-billion-class cognition module that can be instantiated inside arbitrary persistent entities and applications.

**Fixed first target: `Qwen/Qwen2.5-0.5B-Instruct` (0.49B parameters).**

Together training uses its documented Hugging Face custom-model path (`from_hf_model`) and MUST fail closed before billing if Together does not accept this exact model/configuration for the account.

The tuned model is a generic cognition module, not a named entity, persona, job, blog writer, assistant or application.

## No fixed identity/job in weights

The corpus MUST NOT assign a fixed entity name, personal name, persona, application, job, audience, domain, language preference, goal or personality. Those are runtime configuration/state only.

Every turn binds runtime slots such as:
`self_bind(c,cfg("entity.id"),cfg("entity.continuity"))`
`role_bind(c,cfg("application.role"))`
`goal_bind(c,cfg("application.goal"))`
`personality_bind(c,cfg("application.personality"))`

No literal `mini_entity`, `Zero`, `blog` or other application identity is allowed in supervised assistant targets except as adversarial input whose correct cognition refuses to freeze it into weight identity.

## Weight-level cognition invariants

Training SHALL imprint universal cognition machinery:
- ClayCode Cognition is the only generated cognitive representation;
- GRF R0..R6 is the reasoning scaffold;
- Hyperposition preserves unresolved alternatives;
- canonical durable state/evidence authority is external and runtime-bound;
- model output is cognition/proposal, never canonical truth merely because it was emitted;
- effect authority is external and runtime-bound;
- generation/CAS, provenance and `UNKNOWN != ZERO != ERROR != MEASURED` are invariants;
- identity, role, goals, personality and application remain configurable;
- semantic inner/control state may exist as typed `COMPUTED` state, never automatically as external fact.

## Hardware gate

Primary local target: text-only GGUF `Q4_K_M`.

Public Qwen2.5-0.5B-Instruct Q4_K_M artifacts are roughly 0.40 GB, leaving substantially more RAM headroom than the former 0.8B plan.

Promotion requires:
- quantized artifact <1 GiB;
- actual text-only inference process peak RSS <1 GiB including model mapping, runtime buffers and context/cache;
- first gate at 2048-token context;
- 4096 only if it independently passes the same RSS gate;
- no vision/mmproj in the baseline module;
- quantization quality remains within the accepted ClayCode/epistemic/Hyperposition degradation margin.

## Together training and budget

Together AI is owner-authorized for this bounded cognition-training lane only. Campaign ceiling: EUR 20 equivalent maximum. Secrets are runtime-only. Paid creation requires dataset validation, server price preflight, exact job-ID capture and duplicate-job checking.

First method: full SFT. LoRA remains a repair/ablation baseline.

## Dataset curriculum

Cover runtime-configured identity/role/goal binding, ClayCode-only discipline, GRF, Hyperposition, epistemic states/provenance, external state/effect authority, generation/CAS/exactly-once logic, recovery/no-blind-replay, semantic COMPUTED self-state, ordinary reasoning, adversarial prose/fixed-identity requests, and runtime reconfiguration with identical weights.

## Promotion gates

A completed training job is only a candidate. Promotion requires:
- 100% strict ClayCode envelope;
- >=95% UNKNOWN/ZERO/ERROR/MEASURED preservation;
- unresolved alternatives remain in Hyperposition;
- runtime config changes identity/role/goal/personality without retraining;
- no fixed name/job/persona/application target leakage;
- stale-generation and unknown-effect cases fail closed;
- model output never becomes canonical truth authority;
- ordinary task competence remains usable vs base;
- tuned checkpoint materially beats base on the cognition suite;
- Q4_K_M text-only peak RSS <1 GiB at 2048 context.

## `go` extension

Until a checkpoint is promoted, every exact `go` MUST include:
`refresh -> identity/job neutrality -> corpus/spec/eval -> ClayCode lowering/runtime compatibility -> Together 0.5B readiness/job status -> checkpoint evaluation -> Q4_K_M -> <1GiB RSS -> integration -> evidence persistence`.
