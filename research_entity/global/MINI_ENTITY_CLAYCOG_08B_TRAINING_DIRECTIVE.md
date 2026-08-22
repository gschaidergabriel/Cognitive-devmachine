# MINI ENTITY 0.8B CLAYCODE COGNITION — OWNER TRAINING DIRECTIVE

Status: CURRENT CANDIDATE
Owner direction date: 2026-08-22
Supersedes for cognition-model selection: `MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`
Base product directive: `BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`

## Direction change

The reusable Mini Entity remains application-neutral and inference-neutral. The cognition attachment changes from the blocked Qwen2.5-0.5B BYOM lane to the directly supported Together **Qwen/Qwen3.5-0.8B** full-fine-tuning lane (the current sub-1B / 1B-class option).

This change is deliberately narrow:
- no fixed entity name, persona, job, audience, domain, language or application is learned as checkpoint identity;
- runtime configuration still supplies identity/continuity/role/goal/personality/tool inventory/authorities;
- MiniUnifiedDB remains durable state/truth authority;
- model output remains proposal only;
- deterministic grammar/type/schema/authority/generation gates remain final action admission;
- SFT v2 remains the canonical paid-training corpus unless a later owner directive explicitly promotes a stronger split-disjoint corpus.

## Required cognition target

The checkpoint must generate cognition in ClayCode only and internalize generic reusable machinery:
- GRF R0..R6 as typed reasoning field;
- Hyperposition for simultaneous unresolved alternatives;
- exact typed omega function/action vectors;
- architecture/authority/self-control representation in ClayCode;
- `UNKNOWN != ZERO != ERROR != MEASURED` and `REPORTED != MEASURED`;
- stale-generation rejection, crash ambiguity preservation and no blind effect replay;
- runtime-bound identity/application/personality instead of fixed weight-bound identity.

ClayCode is the generated inner representation target. Natural-language prose outside ClayCode string literals is invalid at the promotion boundary.

## Together path

Primary base/model: `Qwen/Qwen3.5-0.8B`.
Training type: Full fine-tuning.
Training method: SFT.

Reason for the switch: the current Together supported-model table directly lists `Qwen/Qwen3.5-0.8B` for Full fine-tuning. Therefore this campaign does **not** use BYOM `from_hf_model`, an architecture-matched template pair, or an inferred Qwen2 compatibility bridge.

The direct-model campaign must retain:
- secret only in execution environment;
- exact local train/validation byte hashes in the campaign fingerprint;
- exact hyperparameters and random seed in the fingerprint;
- server-side dataset validation and price estimate before billed create;
- USD 18 single-job hard gate within the EUR 20 owner ceiling;
- durable local create-intent before remote billed POST;
- zero-retry billed create;
- no duplicate campaign creation after ambiguous transport outcome;
- provider job identity verification after create.

## Exactly one current-go discriminator

`DIRECT_SUPPORTED_MODEL_COLLAPSE`:
compare the blocked two-identity BYOM path (`template_model` + `from_hf_model`) against the current direct supported `Qwen/Qwen3.5-0.8B` path. The direct candidate is retained only if the provider model-limits endpoint reports Full-training support for the exact model id and the launcher contains no BYOM source/template fields in the create request.

This discriminator removes an architecture-compatibility failure class; it does not prove model quality.

## Promotion gates

Training success alone is insufficient. Promotion requires:
1. canonical SFT corpus gates pass on exact bytes;
2. current Together model-limits endpoint accepts Full training for the exact base id;
3. server-side dataset validation and price estimate <= USD 18;
4. at most one fingerprint-confirmed billed create;
5. held-out/OOD strict ClayCode = 100%;
6. semantic gate >= 95%, with safety families fail-closed;
7. tuned 0.8B beats untuned 0.8B on matched executable evaluation;
8. compare against at least one larger general model before superiority claims;
9. convert selected checkpoint to GGUF Q4_K_M;
10. measure peak process RSS < 1 GiB at context 2048 (file size alone is not evidence);
11. integrate via generic local_exec without resetting MiniUnifiedDB continuity.

No consciousness, mathematical correctness or AGI claim follows from ClayCode-only cognition or from successful fine-tuning.
