# UNIFIED COGNITIVE FABRIC RUNTIME RECEIPT / v1

Status: SOURCE CONTRACT CANDIDATE
Owner-architecture basis: 2026-08-23 current Mini Entity / EntityOS / Zero J-Space+GWT architecture
Evidence class: SOURCE ONLY until executed on exact admitted runtime bytes

## Purpose

This contract defines one canonical evidence envelope for the first executable path through the Unified Cognitive Workspace Fabric.

It deliberately prevents two overlapping evidence authorities from emerging around the same mechanism.

The previously named `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` is not a second ledger or second receipt family. Its required boot evidence is represented by:

`UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` with `phase = BOOT_BINDING`.

Subsequent exact inference-cycle evidence uses the same receipt type with `phase = INFERENCE_CYCLE`.

Required law:

`ONE_COGNITIVE_FABRIC -> ONE_RUNTIME_EVIDENCE_ENVELOPE`

`BOOT_BINDING_RECEIPT = UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT(phase=BOOT_BINDING)`

`NO_PARALLEL_JSPACE_GWT_RECEIPT_AUTHORITY`

## ClayCode semantic contract

```text
fabric_receipt_v1(
  receipt_type="UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1",
  phase,
  source_exact,
  entity_generation,
  zero_binding,
  bundled_cognition_binding,
  workspace_transition,
  inference_packet,
  candidate_result,
  candidate_epistemic_status,
  validation_reconciliation,
  effect_boundary,
  secret_network_counters,
  terminal_digest
)

law(model_output != canonical_truth)
law(model_output != direct_effect_authority)
law(workspace_stability != factual_truth)
law(latent_geometry != factual_truth)
law(stale_identity_or_manifest -> reject)
law(FREE_ONLY && (secret_lookup_count>0 || network_attempt_count>0) -> reject)
law(canonical_write -> validation_decision==ACCEPTED_CANDIDATE)
law((canonical_write || effect_admitted) -> candidate_epistemic_status==MEASURED_SUPPORTED)
law(effect_admitted -> effect_requested)
```

## Required evidence groups

### 1. Exact source / executor binding

The receipt binds:
- exact repository commit;
- exact source tree;
- dirty state;
- executor/runtime identity;
- environment digest or equivalent immutable execution identity where available;
- start and completion timestamps.

No source-only, mergeability, READY state or runner-before-steps event satisfies this group.

### 2. One entity / generation binding

The receipt binds:
- Mini Entity version;
- EntityOS version where present;
- one current generation;
- Zero identity digest;
- GRF digest;
- cognition/workspace policy digests where available.

A stale Zero identity, GRF or generation must fail closed rather than silently rebind.

### 3. Bundled approximately-0.8B reference cognition binding

The receipt binds the exact bundled cognition manifest and its model-specific measurable substrate:
- manifest digest;
- checkpoint digest;
- tokenizer digest;
- J-Space profile digest;
- lens profile digest;
- workspace calibration digest;
- runtime/quantization identity when present.

A profile measured on different checkpoint/tokenizer/runtime bytes is not transferable runtime evidence.

### 4. Unified J-Space/GWT workspace transition

The receipt binds:
- workspace digest before competition;
- candidate set references;
- GWT admission and winner decisions;
- J-Space observation references;
- Thalamus gate decisions;
- EPQ telemetry digest/summary;
- workspace digest after competition;
- Hyperposition, ClayCode and omega references used by the transition.

J-Space measurement and GWT stability remain cognition-control evidence, not factual truth authority.

### 5. Inference engine scheduling

The selected engine class is explicit:
- `LOCAL_08B`;
- `CLAUDE_CODE`;
- `ADAPTIVE_BACKEND`;
- `DETERMINISTIC_ONLY`.

For Claude Code the adapter version and capability-profile digest are mandatory. Claude receives a targeted `InferencePacket`; Claude is not Zero and never becomes state/effect authority.

For adaptive backends the exact capability profile is bound. A profile cannot claim hidden-state/J-Space access that the backend does not expose.

### 6. Candidate-only return, epistemic status and deterministic reconciliation

Every learned/external engine result re-enters as a candidate.

The receipt binds:
- complete InferencePacket digest;
- candidate-result digest or explicit null when no learned inference ran;
- `candidate_only = true`;
- explicit candidate epistemic status: `MEASURED_SUPPORTED | UNKNOWN | ERROR | REFUTED`; `NOT_APPLICABLE` is reserved for `DETERMINISTIC_ONLY`;
- deterministic validation/reconciliation decision;
- canonical-write decision;
- effect request/admission decision.

No engine result can directly mint durable truth or bypass deterministic effect authority.

A stable or internally coherent J-Space/GWT workspace does not upgrade an `UNKNOWN`, `ERROR` or `REFUTED` candidate. `canonical_write` and `effect_admitted` require `MEASURED_SUPPORTED` in addition to the existing deterministic reconciliation/effect gates.

This closes the specific truth-confusion failure mode:

`WORKSPACE_STABLE + CANDIDATE_REFUTED != CANONICAL_TRUTH`

### 7. FREE_ONLY / secret / network boundary

The receipt records explicit counters:
- secret/key lookups;
- network attempts.

When current control is `FREE_ONLY=true`, both counters MUST be zero for PAID/SUBSCRIPTION/UNKNOWN external lanes. A source declaration is insufficient; the executable receipt is the evidence.

### 8. Terminal identity

The final receipt binds a terminal status and digest over the canonical serialized evidence envelope. Unknown/aborted states remain explicit and are not rewritten as success.

## BOOT_BINDING phase

`BOOT_BINDING` is the mandatory first observation boundary when the intentionally offline Ubuntu host is next started.

It must bind the frozen prestart baseline to the exact poststart source/executor plus:
- bundled 0.8B manifest/checkpoint/tokenizer/J-Space/lens/workspace identities;
- Zero identity and GRF projections;
- current generation;
- Claude adapter version/capability profile;
- first selected engine class;
- origin attribution for the first autonomous/tool/inference action;
- secret/network counters.

This phase satisfies the supervisor's `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` requirement; do not emit an independent competing receipt for the same boundary.

## INFERENCE_CYCLE phase

`INFERENCE_CYCLE` binds one complete admitted cognition cycle from canonical state/evidence through workspace competition, engine scheduling, candidate return, validation/reconciliation and final canonical write/effect decision.

The strongest first acceptance cycle should exercise:
- local 0.8B path;
- targeted Claude path where current cost/control policy permits;
- adaptive-backend capability mismatch negative case;
- stale Zero identity or stale bundled manifest negative case;
- candidate direct-state/effect mutation negative case;
- a case where workspace is stable but candidate evidence is `REFUTED`, proving `WORKSPACE_STABILITY != FACTUAL_TRUTH` and blocking canonical write/effect authority.

## Validator

`the artefact/blogpost_entity/validate_unified_cognitive_fabric_receipt_v1.py` implements the deterministic source-level admission checks for this envelope.

Its tests are deterministic source regressions only. Runtime credit requires the actual exact runtime to emit a receipt and the validator to execute against those exact bytes on an admitted execution surface.

The `WORKSPACE_STABILITY_TRUTH_CONFUSION_MUTATION` test in the retained lane is a regression-only fusion of the already-consumed unusual intervention from PR #1046; it is not a second unusual experiment.

## Promotion boundary

This contract creates no J-Space, GWT, Claude, 0.8B, model-quality, BASE, Whole-GWT or whole-product PASS by itself.

Promotion requires an actually-started exact-source Ubuntu execution receipt and all existing higher-priority FREE_ONLY, truth, provenance, effect and Harness-immutability laws to remain satisfied.
