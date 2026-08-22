# the artefact — Multi-use Mini Entity pipeline

**Current program override — 2026-08-22.** The newest owner authority makes the active product the application-neutral, inference-neutral **Multi-use Mini Entity pipeline all-in-one**. The older ClayVerse single-container text that previously occupied this README is legacy/donor material and is not the current product endpoint.

Current authority is resolved from:

- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- `research_entity/global/MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md`

If cached bootstrap text conflicts with a newer explicit owner directive, the newer owner directive wins.

## Current product target

Ship one portable Mini Entity whose durable identity/state is independent of any one application, personality, provider or model:

```text
runtime config / .clay application
        |
        v
generic Mini Entity pipeline executable
        |
        +--> SQLite MiniUnifiedDB  (canonical durable state/evidence)
        |
        +--> runtime-selectable inference
              - remote API
              - loopback local API
              - configured local_exec model runner
```

`zero_blog` is a replaceable shipped preset, not executable identity.

The executable must not hard-code a replaceable entity name, blog job, personality, provider or model. Runtime configuration supplies application/personality/system prompt, identity/continuity, role, goal, inference profile, tool inventory and authorities below immutable generic architecture and secret gates.

Switching provider/model/backend must not reset the persistent entity.

## Truth and persistence laws

```text
UNKNOWN != ZERO != ERROR != MEASURED
REPORTED != MEASURED
MODEL_OUTPUT != CANONICAL_EVIDENCE
PROPOSAL != ADMISSION
```

SQLite MiniUnifiedDB is the canonical durable authority. Model output may propose structured cognition/actions, but deterministic runtime admission owns validation and execution. Exactly-once/CAS/atomic persistence and crash recovery remain product obligations rather than model promises.

Secrets are runtime inputs only. They must not be committed, emitted into model-visible context or turned into durable memory.

## 0.5B ClayCode cognition lane

The current owner-authorized extension adds an **optional reusable 0.5B ClayCode cognition module** without changing the generic product identity.

Primary checkpoint candidate:

```text
Qwen/Qwen2.5-0.5B
```

The training representation is `CLAYCODE_COGNITION_V1`: generated cognition must stay inside the ClayCode envelope; GRF, Hyperposition and typed `omega` action candidates are learned as compact internal representation. The model remains a proposal organ, never canonical truth/effect authority.

Current source/corpus lane:

- `blogpost_entity/mini_cognition/CLAYCODE_COGNITION_V1.md`
- `blogpost_entity/mini_cognition/generate_sft_v1.py`
- `blogpost_entity/mini_cognition/validate_sft_v1.py`
- `blogpost_entity/mini_cognition/generate_ood_v1.py`
- `blogpost_entity/mini_cognition/eval_outputs_v1.py`
- `blogpost_entity/mini_cognition/launch_together_v1.py`
- `blogpost_entity/mini_cognition/quantize_rss_gate_v1.sh`

Current deterministic corpus target is 1,650 SFT examples (1,485 train / 165 validation) plus a separate 200-case OOD promotion set.

### Admission law

A training target is not admitted merely because braces balance or it resembles ClayCode. `CLAYCODE_COGNITION_V1` requires fail-closed rejection of natural language outside string literals, unknown intrinsics, bad arity/grammar and incomplete `omega` validation.

The current cognition branch hardens `validate_sft_v1.py` with a strict parser/arity allowlist and pre-commit `omega` gate checks, plus deterministic regressions over the full generated corpus and adversarial mutations. Until that branch receives an actually-started exact-source isolated execution receipt and is merged, this is a **source candidate**, not runtime-verified corpus PASS.

## Bounded Together training exception

The base product remains inference-provider neutral. Together is not a product/runtime identity or mandatory dependency.

The newer `MINI_ENTITY_CLAYCOG_05B_TRAINING_DIRECTIVE.md` grants a bounded owner-authorized exception for the 0.5B training campaign only. It requires:

- secret only through environment/runtime secret injection;
- server-side dataset/template/checkpoint compatibility preflight before billed creation;
- server price estimate and hard per-job budget gate;
- no blind duplicate job creation/retry;
- no training success promoted directly to product acceptance.

No paid training job is implied by source readiness.

## Promotion gates for the tuned 0.5B candidate

Training loss or job completion does not establish useful cognition. Promotion requires held-out/OOD behavior, fail-closed invalid-action behavior, configuration neutrality, stale-generation/unknown-effect safety, comparison against the untuned 0.5B baseline and a larger general model, plus quantized local runtime evidence.

The target quantization is Q4_K_M. The `<1 GiB` requirement is **measured peak process RSS at 2048 context**, not checkpoint file size.

## Current convergent frontier

Two lanes are current and complementary:

1. **Native Mini Entity 0.7:** exact isolated build/runtime/fault evidence, semantic parity, local inference and persistence gates.
2. **CLAYCOG_05B_TRAINING/v1:** strict corpus admission -> Together BYOM compatibility/preflight -> budget-gated Full SFT -> OOD/base/larger-model comparison -> Q4_K_M -> measured `<1 GiB` RSS -> configured `local_exec` integration.

Parallel ClayVerse/EntityOS/Frank material is legacy/donor evidence only when it directly advances these current Mini Entity obligations. It must not silently restore an obsolete product endpoint.

## Evidence ladder

```text
SOURCE_CANDIDATE
-> STATIC/DETERMINISTIC TEST EVIDENCE
-> EXACT ISOLATED RUNTIME EVIDENCE
-> REAL MODEL/PROVIDER EVIDENCE
-> QUANTIZED LOCAL RUNTIME EVIDENCE
-> INTEGRATED MINI ENTITY ACCEPTANCE
```

Never infer a higher class from a lower one. Runner/control-plane admission failure before test steps is not a semantic test failure, and source coherence is not runtime PASS.

## `go`

A current `go` should advance the highest-information non-duplicate blocker across the complete Mini Entity target, while also advancing the 0.5B cognition lane when it is the highest-value frontier. It must preserve exact provenance, negative results and owner/budget/security gates.
