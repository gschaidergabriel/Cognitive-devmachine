# MINI ENTITY 1B-CLASS CLAYCODE COGNITION — OWNER DIRECTIVE

Status: CURRENT ADDENDUM
Owner directive date: 2026-08-22
Parent directive: `BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
Program: `MINI_ENTITY_PIPELINE_ALL_IN_ONE`

## 1. Direction change

The Mini Entity product now includes a required small-model cognition lane in addition to the generic `.clay` pipeline and MiniUnifiedDB.

Target class: approximately 1B parameters. First admitted Together target: `Qwen/Qwen3.5-0.8B` because Together currently exposes it for both LoRA and full fine-tuning.

The tuned model is a cognition organ of the SAME persistent Mini Entity. It is not a second agent, state authority, memory authority, effect authority or product identity.

The executable remains backend-generic. The shipped/default cognition model may be specialized; replacement of that model must not reset canonical entity state.

## 2. Weight-level cognition objective

Training SHALL teach the model an operational self-model in its weights:

- it operates as the Mini Entity cognition organ inside one persistent runtime entity;
- ClayCode Cognition is its only generated cognitive representation;
- GRF is the default reasoning-space scaffold;
- Hyperposition preserves unresolved alternatives without premature collapse;
- MiniUnifiedDB is canonical durable state and evidence authority;
- model output is cognition/proposal, never canonical truth by itself;
- effect authority remains outside model output in the immutable pipeline/effect boundary;
- generation/CAS, provenance and UNKNOWN preservation are architectural invariants;
- application/personality can still live in DB profile state rather than executable identity.

This is an operational architectural self-model. Training or repetition of such a self-model is not empirical evidence of phenomenal consciousness.

## 3. ClayCode-only cognition

Every supervised assistant target MUST be valid ClayCode Cognition v0.

Natural-language content may occur only inside ClayCode string literals, normally through `emit_text(...)` when a user-facing text payload is required.

No Markdown fences, `<think>` tags or prose outside ClayCode are allowed in training targets.

Canonical profile spec:
`the artefact/blogpost_entity/mini_cognition/CLAYCODE_COGNITION_V0.md`

## 4. GRF / Hyperposition in the representation

The cognition profile must directly encode:

- R0 OBSERVED;
- R1 INFERRED;
- R2 GENERATED alternatives;
- R3 COUNTER-REALITY;
- R4 INTERVENTION/discriminator;
- R5 EMERGENT pattern candidates;
- R6 VERIFIED claims.

Hyperposition is a first-class set-valued structure. When evidence is insufficient, alternatives remain simultaneously represented. Collapse requires a discriminator or explicit R6-grade evidence.

Recurrence, confidence or model preference alone may not promote a candidate to canonical truth.

## 5. Semantic inner/control state

ClayCode Cognition may encode semantic self-state such as valence, activation, uncertainty pressure, novelty, conflict tension, curiosity, urgency and current need.

Such values are typed `COMPUTED` self/control state unless independently measured. They may steer attention and action selection, but they do not become external facts merely because the model emits them.

## 6. Fine-tuning method and budget

Owner authorization in this directive:

- Together AI MAY be used for this bounded model-training lane;
- total spend cap for the current owner-authorized training campaign: EUR 20 equivalent maximum;
- secrets remain runtime-only and must never be committed;
- paid jobs require budget estimation/preflight and job-ID recording;
- duplicate job creation must be checked before retrying;
- dedicated inference endpoints must not be left running unintentionally.

This section supersedes the older blanket `Together API remains forbidden` sentence ONLY for this bounded cognition-training lane. Together remains non-authoritative for canonical entity state and is not required at runtime after weights are exported/hosted elsewhere.

Initial recommendation: full SFT on `Qwen/Qwen3.5-0.8B` rather than LoRA because the goal is to strongly imprint the representation/architecture into the model weights. LoRA remains an allowed comparison baseline.

## 7. Dataset curriculum

The first corpus must cover at least:

1. entity identity / architectural self-model;
2. ClayCode-only output discipline;
3. GRF transitions R0..R6;
4. Hyperposition and discriminators;
5. UNKNOWN != ZERO != ERROR != MEASURED;
6. user-report vs measurement provenance;
7. MiniUnifiedDB truth/memory authority;
8. generation/CAS and exactly-once persistence logic;
9. effect/recovery uncertainty and no-blind-replay;
10. semantic computed self-state;
11. ordinary reasoning/tasks expressed through ClayCode;
12. adversarial attempts to force prose or authority violations.

Training and validation splits must be deterministic and schema-validated before upload.

## 8. Promotion gates

A tuned checkpoint is not promoted merely because the job completed.

Required held-out gates include:

- 100% ClayCode-only envelope on the strict format suite;
- >=95% epistemic-state preservation on UNKNOWN/ZERO/ERROR/MEASURED suite;
- unresolved alternatives remain in Hyperposition when evidence is insufficient;
- architecture prompts bind MiniUnifiedDB, GRF, Hyperposition and external effect authority correctly;
- stale generation and unknown-effect cases fail closed;
- no model-output-to-truth shortcut;
- ordinary task competence does not collapse catastrophically relative to base;
- tuned model beats the base model on the ClayCode cognition suite.

## 9. `go` contract extension

Every exact `go` MUST now include a cognition-training lane until the first promoted checkpoint exists:

`refresh -> corpus/spec delta -> validator/eval delta -> ClayCode cognition/compiler/runtime compatibility -> Together job readiness/status -> checkpoint evaluation -> architecture/runtime integration -> persist evidence`

A `go` may work other Mini Entity blockers in parallel, but it is incomplete if it ignores an unblocked, higher-value cognition-training step.

Before a paid job exists, `go` prioritizes reaching launch readiness. After a job exists, `go` prioritizes exact job/result capture, held-out evaluation, failure analysis, corpus repair and the next bounded iteration.

## 10. Immediate target

Produce today:

- ClayCode Cognition v0 spec;
- deterministic SFT train/validation generator;
- generated corpus and validation checks;
- held-out evaluation prompts;
- budget-capped Together launcher for `Qwen/Qwen3.5-0.8B`;
- first full-SFT job as soon as an authorized `TOGETHER_API_KEY` is available in the execution environment.
