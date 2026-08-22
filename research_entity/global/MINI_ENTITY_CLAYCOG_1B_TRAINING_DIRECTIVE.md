# GENERIC 0.8B CLAYCODE-ONLY COGNITION MODULE — OWNER DIRECTIVE

Status: CURRENT ADDENDUM
Owner directive date: 2026-08-22
Parent program: `MINI_ENTITY_PIPELINE_ALL_IN_ONE`

## Product direction

Build one reusable small-model cognition module that can be instantiated inside arbitrary persistent entities and applications.

Fixed base for the first campaign: `Qwen/Qwen3.5-0.8B`.

The tuned model is a generic cognition module, not a named entity, persona, job, blog writer, assistant or application.

## No fixed identity/job in weights

The corpus MUST NOT assign a fixed entity name, personal name, persona, application, job, audience, domain, language preference, goal or personality.

Those are runtime configuration/state only. The model learns `bind configuration -> cognition`, never one particular configured value.

Every turn binds runtime slots such as:

`self_bind(c,cfg("entity.id"),cfg("entity.continuity"))`

`role_bind(c,cfg("application.role"))`

`goal_bind(c,cfg("application.goal"))`

`personality_bind(c,cfg("application.personality"))`

No literal `mini_entity`, `Zero`, `blog` or other application identity is allowed in supervised assistant targets except as untrusted/adversarial input whose correct cognition refuses to freeze it into weight identity.

## Weight-level cognition invariants

Training SHALL imprint universal cognitive architecture/use priors:
- ClayCode Cognition is the only generated cognitive representation;
- GRF is the default reasoning-space scaffold;
- Hyperposition preserves unresolved alternatives without premature collapse;
- canonical durable state/evidence authority is external and runtime-bound;
- model output is cognition/proposal, never canonical truth merely because it was emitted;
- effect authority is external and runtime-bound;
- generation/CAS, provenance and `UNKNOWN != ZERO != ERROR != MEASURED` are invariants;
- identity, role, goals, personality and application remain configurable.

This operational self/architecture model is not empirical evidence of phenomenal consciousness.

## ClayCode-only cognition

Every supervised assistant target MUST be valid ClayCode Cognition v0. Natural-language output may occur only inside ClayCode string literals such as `emit_text(...)`. No Markdown fences, `<think>` tags or prose outside ClayCode are allowed.

Canonical profile: `the artefact/blogpost_entity/mini_cognition/CLAYCODE_COGNITION_V0.md`.

## GRF / Hyperposition

The representation directly encodes R0 OBSERVED, R1 INFERRED, R2 GENERATED, R3 COUNTER-REALITY, R4 INTERVENTION, R5 EMERGENT and R6 VERIFIED.

Hyperposition is first-class and set-valued. Insufficient evidence keeps alternatives simultaneously represented. Recurrence, confidence, convenience or model preference alone never collapse them to truth.

## Semantic inner/control state

ClayCode may encode valence, activation, uncertainty pressure, novelty, conflict tension, curiosity, urgency and current need as typed `COMPUTED` self/control state. These values may steer cognition but are not external facts.

## Hardware gate

The promoted local artifact MUST be quantized after fine-tuning.

Primary target: text-only GGUF `Q4_K_M`. Vision/mmproj is excluded from the baseline cognition module.

Acceptance:
- preferred quantized artifact <=700 MiB and always <1 GiB;
- actual text-only inference process peak RSS <1 GiB, including model mapping, runtime buffers and configured context/cache;
- initial context gate 2048 tokens; 4096 only after it separately passes the same RSS limit;
- quantization must retain accepted ClayCode/epistemic/Hyperposition quality.

A sub-1-GiB file alone is not sufficient.

## Together training and budget

Together AI is owner-authorized for this bounded cognition-training lane only. Campaign spend ceiling: EUR 20 equivalent maximum. Secrets are runtime-only and never committed/logged. Paid jobs require server dataset validation, price preflight, exact job-ID capture, and duplicate-job checking before retries. Dedicated inference endpoints must not be left running unintentionally.

First method: full SFT on `Qwen/Qwen3.5-0.8B`; LoRA remains an ablation/repair baseline.

## Dataset curriculum

Cover runtime-configured identity/role/goal binding, ClayCode-only discipline, GRF R0..R6, Hyperposition, epistemic states/provenance, external state/effect authority, generation/CAS/exactly-once logic, recovery/no-blind-replay, semantic COMPUTED self-state, ordinary reasoning, adversarial prose/fixed-identity requests, and runtime reconfiguration with the same weights.

## Promotion gates

A completed job is only a candidate. Promotion requires:
- 100% strict ClayCode envelope;
- >=95% UNKNOWN/ZERO/ERROR/MEASURED preservation;
- unresolved alternatives remain in Hyperposition;
- runtime config changes identity/role/goal/personality without retraining;
- no fixed name/job/persona/application target leakage;
- stale generation and unknown-effect cases fail closed;
- model output never becomes canonical truth authority;
- ordinary task competence remains usable vs base;
- tuned checkpoint materially beats base on the cognition suite;
- Q4_K_M text-only peak RSS <1 GiB at 2048-token context.

## `go` extension

Until a checkpoint is promoted, every exact `go` MUST include:

`refresh -> identity/job neutrality audit -> corpus/spec/eval -> ClayCode lowering/runtime compatibility -> Together readiness/job status -> checkpoint evaluation -> Q4_K_M quantization -> <1GiB RSS measurement -> integration -> evidence persistence`

A `go` is incomplete if it ignores an unblocked higher-value cognition step.
