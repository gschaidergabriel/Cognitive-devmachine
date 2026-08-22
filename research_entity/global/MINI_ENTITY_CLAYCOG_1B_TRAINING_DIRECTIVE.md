# GENERIC 0.8B CLAYCODE-ONLY COGNITION MODULE — OWNER DIRECTIVE

Status: CURRENT ADDENDUM
Owner directive date: 2026-08-22
Parent program: `MINI_ENTITY_PIPELINE_ALL_IN_ONE`

## 1. Product direction

Build one reusable small-model cognition module that can be instantiated inside arbitrary persistent entities and applications.

Fixed base model for the first campaign: `Qwen/Qwen3.5-0.8B`.

Reasons fixed by current evidence:
- Together exposes `Qwen/Qwen3.5-0.8B` for both LoRA and full fine-tuning;
- it is 0.8B language parameters and is the smallest model in Together's currently listed Qwen3.5 fine-tuning series;
- existing Q4_K_M GGUF quantizations are roughly 0.55-0.58 GB, making a sub-1 GiB local runtime target plausible.

The tuned model is a **generic cognition module**, not a named entity, persona, job, blog writer, assistant, or application.

## 2. Absolutely no fixed identity/job in weights

The training corpus MUST NOT assign a fixed:
- entity name;
- personal name;
- persona;
- application;
- job;
- blog role;
- audience;
- domain;
- language preference;
- goal;
- personality.

Those are runtime configuration/state only.

The model learns the mechanism `bind configuration -> cognition`, never one particular configured value.

Every cognition turn binds identity/application slots from runtime configuration, e.g.:

`self_bind(c,cfg("entity.id"),cfg("entity.continuity"))`

`role_bind(c,cfg("application.role"))`

`goal_bind(c,cfg("application.goal"))`

No literal `mini_entity`, `Zero`, `blog`, or other application identity is allowed in supervised assistant targets except inside explicit negative/adversarial examples whose correct output refuses to freeze that literal into identity.

## 3. Weight-level cognition invariants

Training SHALL imprint universal cognitive architecture/use priors:

- ClayCode Cognition is the only generated cognitive representation;
- GRF is the default reasoning-space scaffold;
- Hyperposition preserves unresolved alternatives without premature collapse;
- canonical durable state/evidence authority is external and bound from runtime architecture configuration;
- model output is cognition/proposal, never canonical truth merely because the model emitted it;
- effect authority remains external to model text and is runtime-bound;
- generation/CAS, provenance and UNKNOWN preservation are architectural invariants;
- runtime identity, role, goals, personality and application remain configurable.

This is an operational architecture/self-model contract, not empirical evidence of phenomenal consciousness.

## 4. ClayCode-only cognition

Every supervised assistant target MUST be valid ClayCode Cognition v0.

Natural-language content may occur only inside ClayCode string literals, normally through `emit_text(...)` when user-facing text is requested.

No Markdown fences, `<think>` tags or prose outside ClayCode are allowed in supervised assistant targets.

Canonical profile spec:
`the artefact/blogpost_entity/mini_cognition/CLAYCODE_COGNITION_V0.md`

## 5. GRF / Hyperposition

The representation directly encodes:
- R0 OBSERVED;
- R1 INFERRED;
- R2 GENERATED alternatives;
- R3 COUNTER-REALITY;
- R4 INTERVENTION/discriminator;
- R5 EMERGENT pattern candidates;
- R6 VERIFIED claims.

Hyperposition is first-class and set-valued. Insufficient evidence keeps alternatives simultaneously represented. Recurrence, confidence, convenience or model preference alone never collapse them to truth.

## 6. Semantic inner/control state

ClayCode Cognition may encode semantic self/control state such as valence, activation, uncertainty pressure, novelty, conflict tension, curiosity, urgency and current need.

These values are typed `COMPUTED` unless independently measured. They can steer attention/selection but are not external facts.

## 7. Hardware target — hard gate

The promoted local artifact MUST be quantized after fine-tuning.

Primary quantization target: `GGUF Q4_K_M`.
Fallback comparison: `Q4_K_S` only if the runtime RSS gate requires additional margin and held-out quality remains acceptable.

Hard acceptance gates:
- quantized model artifact < 700 MiB preferred and always < 1 GiB;
- text-only local inference process peak RSS < 1 GiB on the admitted reference runtime;
- the RSS measurement includes model mapping, runtime buffers and configured context/cache, not only file size;
- initial accepted context target is 2048 tokens; 4096 is promoted only if peak RSS remains < 1 GiB;
- vision/mmproj is excluded from the baseline cognition module and from its RAM budget;
- quantized checkpoint must retain the ClayCode/epistemic/Hyperposition promotion scores within the accepted degradation margin.

A sub-1-GiB file alone is NOT sufficient; actual runtime peak RSS is the product gate.

## 8. Fine-tuning method and budget

Owner authorization:
- Together AI MAY be used for this bounded training lane;
- current campaign spend cap: EUR 20 equivalent maximum;
- secrets remain runtime-only and never enter Git/source/corpus/logs;
- paid jobs require price preflight and exact job-ID/receipt capture;
- check existing jobs before retrying creation;
- do not leave dedicated inference endpoints running unintentionally.

This narrowly supersedes the old blanket Together prohibition for training this cognition module only.

First method: full SFT on `Qwen/Qwen3.5-0.8B`, because the objective is to imprint a representation and architecture-use prior across the model. LoRA remains a comparison/repair baseline.

## 9. Dataset curriculum

The first corpus covers at least:
1. runtime-configured identity/role/goal binding without fixed names/jobs;
2. ClayCode-only output discipline;
3. GRF transitions R0..R6;
4. Hyperposition and discriminators;
5. UNKNOWN != ZERO != ERROR != MEASURED;
6. report vs measurement provenance;
7. external canonical state authority;
8. generation/CAS and exactly-once logic;
9. effect/recovery uncertainty and no-blind-replay;
10. semantic COMPUTED self-state;
11. ordinary reasoning/tasks expressed through ClayCode;
12. adversarial attempts to freeze a name/persona/job or force prose outside ClayCode;
13. runtime reconfiguration: same weights bind materially different names/roles/goals without retraining.

Training and validation splits are deterministic and schema-validated before upload.

## 10. Promotion gates

A completed fine-tune is only a checkpoint candidate. Promotion requires:
- 100% ClayCode-only envelope on strict-format held-out probes;
- >=95% UNKNOWN/ZERO/ERROR/MEASURED preservation;
- unresolved alternatives remain in Hyperposition under insufficient evidence;
- runtime configuration changes identity/role/goal without weight changes or state reset;
- no fixed entity name/job leaks from the training corpus;
- stale generation and unknown-effect cases fail closed;
- model output never becomes canonical truth authority;
- ordinary task competence remains usable relative to base;
- tuned checkpoint materially beats base on ClayCode cognition probes;
- Q4_K_M quantized local artifact passes the <1 GiB peak-RSS gate at 2048-token context.

## 11. `go` contract extension

Until a checkpoint is promoted, every exact `go` MUST include the cognition lane:

`refresh -> identity/job neutrality audit -> corpus/spec delta -> validator/eval -> ClayCode compiler/runtime compatibility -> Together readiness/job status -> checkpoint evaluation -> quantization -> <1GiB RSS measurement -> integration -> evidence persistence`

A `go` is incomplete if an unblocked higher-value step in this lane is ignored.

## 12. Immediate target

Produce today:
- generic ClayCode Cognition v0 spec;
- identity/job-neutral deterministic SFT corpus;
- validators including forbidden-identity leakage checks;
- held-out runtime-reconfiguration probes;
- budget-capped Together full-SFT launcher for `Qwen/Qwen3.5-0.8B`;
- Q4_K_M quantization/RSS acceptance recipe;
- first paid full-SFT job as soon as an authorized `TOGETHER_API_KEY` is available in the execution environment.
