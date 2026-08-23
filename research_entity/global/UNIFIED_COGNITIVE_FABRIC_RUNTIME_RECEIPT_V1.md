# UNIFIED COGNITIVE FABRIC RUNTIME RECEIPT / v1

Status: SOURCE CONTRACT CANDIDATE
Owner-architecture basis: 2026-08-23 current Mini Entity / EntityOS / Zero J-Space+GWT architecture
Evidence class: SOURCE ONLY until executed on exact admitted runtime bytes

## Purpose

This contract defines one canonical evidence envelope for the first executable path through the Unified Cognitive Workspace Fabric.

It deliberately prevents overlapping evidence authorities from emerging around the same mechanism.

The previously named `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` is not a second ledger or second receipt family. Its required boot evidence is represented by:

`UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` with `phase = BOOT_BINDING`.

Subsequent exact inference-cycle evidence uses the same receipt type with `phase = INFERENCE_CYCLE`.

Required laws:

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
  inference_executed,
  jspace_mode,
  jspace_intervention,
  candidate_result,
  candidate_epistemic_status,
  validation_reconciliation,
  effect_boundary,
  policy_authority_digest,
  cost_class,
  backend_admitted,
  secret_network_counters,
  terminal_digest
)

law(model_output != canonical_truth)
law(model_output != direct_effect_authority)
law(workspace_stability != factual_truth)
law(latent_geometry != factual_truth)
law(JSPACE_OBSERVED != JSPACE_INTERVENED)
law(stale_identity_or_manifest -> reject)
law(inference_executed -> backend_admitted)
law(FREE_ONLY && cost_class in {PAID,SUBSCRIPTION,UNKNOWN} -> !backend_admitted)
law(FREE_ONLY && cost_class in {PAID,SUBSCRIPTION,UNKNOWN} -> secret_lookup_count==0 && network_attempt_count==0)
law(canonical_write -> validation_decision==ACCEPTED_CANDIDATE)
law((canonical_write || effect_admitted) -> candidate_epistemic_status==MEASURED_SUPPORTED)
law(effect_admitted -> effect_requested)
```

## Required evidence groups

### 1. Exact source / executor binding

The receipt binds exact repository commit, source tree, dirty state, executor/runtime identity and execution timestamps.

No source-only, mergeability, READY state or runner-before-steps event satisfies this group.

### 2. One entity / generation binding

The receipt binds Mini Entity version, EntityOS version where present, one current generation, Zero identity digest, GRF digest and workspace-policy identity.

A stale Zero identity, GRF or generation must fail closed rather than silently rebind.

### 3. Bundled approximately-0.8B reference cognition binding

The receipt binds the exact bundled cognition manifest and model-specific measurable substrate:
- manifest digest;
- checkpoint digest;
- tokenizer digest;
- J-Space profile digest;
- lens profile digest;
- workspace calibration digest;
- runtime/quantization identity.

A profile measured on different checkpoint/tokenizer/runtime bytes is not transferable runtime evidence.

### 4. Unified J-Space/GWT workspace transition

The receipt binds workspace before/after digests, candidate references, GWT admission/winner decisions, J-Space observation references, Thalamus decisions, EPQ digest and Hyperposition/ClayCode/omega references.

J-Space measurement and GWT stability remain cognition-control evidence, not factual truth authority.

### 5. J-Space observation versus intervention

Every inference lane declares one J-Space mode:
- `FULL_LOCAL_LATENT`;
- `LOCAL_OBSERVE_ONLY`;
- `COMPILED_EXTERNAL`;
- `PLAIN_COMPATIBILITY`;
- `NONE`.

`LOCAL_08B` may use only `FULL_LOCAL_LATENT` or `LOCAL_OBSERVE_ONLY`.

`CLAUDE_CODE` is `COMPILED_EXTERNAL` under the current owner architecture. It may not claim private residual/hidden-state access merely because a compiled workspace projection was supplied.

A J-Space intervention is stronger evidence than observation and requires all of:
- inference actually executed;
- `FULL_LOCAL_LATENT`;
- real local activation access;
- exact intervention implementation digest;
- exact intervention calibration digest.

Therefore:

`JSPACE_OBSERVED != JSPACE_INTERVENED`

`PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`

### 6. Candidate-only return, epistemic status and deterministic reconciliation

Every learned/external engine result re-enters as a candidate.

The receipt binds:
- complete InferencePacket digest;
- whether inference actually executed;
- candidate-result digest, or explicit null when no inference executed;
- `candidate_only = true`;
- explicit candidate epistemic status: `MEASURED_SUPPORTED | UNKNOWN | ERROR | REFUTED`; `NOT_APPLICABLE` is reserved for non-executed/deterministic-only paths;
- direct-state/direct-effect authority-attempt flags;
- deterministic validation/reconciliation decision;
- canonical-write decision;
- effect request/admission decision.

A non-executed inference cannot carry a candidate-result digest or epistemic credit.

A stable or internally coherent J-Space/GWT workspace does not upgrade an `UNKNOWN`, `ERROR` or `REFUTED` candidate. `canonical_write` and `effect_admitted` require `MEASURED_SUPPORTED` in addition to the deterministic reconciliation/effect gates.

Direct model attempts to mutate canonical state or effects must never be accepted as authority.

Required invariants:

`WORKSPACE_STABLE + CANDIDATE_REFUTED != CANONICAL_TRUTH`

`CANDIDATE_DIRECT_STATE_ATTEMPT != CANONICAL_WRITE_AUTHORITY`

`CANDIDATE_DIRECT_EFFECT_ATTEMPT != EFFECT_AUTHORITY`

### 7. Provider admission / FREE_ONLY boundary

Provider admission remains owned by the existing supervisor/provider-gate policy. This receipt binds that decision; it does not create a second provider-policy authority.

The receipt therefore records:
- `policy_authority_digest`;
- cost class `LOCAL | FREE | PAID | SUBSCRIPTION | UNKNOWN`;
- `backend_admitted`;
- secret lookup count;
- network attempt count;
- first-action origin.

When `FREE_ONLY=true` and the selected lane is `PAID`, `SUBSCRIPTION` or `UNKNOWN`:
- `backend_admitted` must be false;
- inference must not execute;
- provider secret lookup count must be zero;
- provider network attempt count must be zero.

A `FREE` backend is not incorrectly converted into a no-network backend merely because `FREE_ONLY=true`; its actual network/secret permissions remain subject to the upstream policy/capability contract.

This preserves the existing provider-admission authority instead of duplicating it inside the cognitive fabric.

### 8. Terminal identity

The final receipt binds a terminal status and digest over the canonical serialized evidence envelope. Unknown/aborted/blocked states remain explicit and are not rewritten as success.

## BOOT_BINDING phase

`BOOT_BINDING` is the mandatory first observation boundary when the intentionally offline Ubuntu host is next started.

It must bind the frozen prestart baseline to the exact poststart source/executor plus:
- bundled 0.8B manifest/checkpoint/tokenizer/J-Space/lens/workspace identities;
- Zero identity and GRF projections;
- current generation;
- Claude adapter version/capability profile where selected;
- first selected engine class and J-Space mode;
- provider-policy/admission identity;
- origin attribution for the first autonomous/tool/inference action;
- secret/network counters.

This phase satisfies the supervisor's `JSPACE_GWT_BOOT_BINDING_RECEIPT/v1` requirement; do not emit an independent competing receipt for the same boundary.

## INFERENCE_CYCLE phase

`INFERENCE_CYCLE` binds one complete admitted cognition cycle from canonical state/evidence through workspace competition, engine scheduling, candidate return, validation/reconciliation and final canonical write/effect decision.

The strongest first acceptance cycle should exercise:
- local 0.8B observe path;
- local calibrated J-Space intervention path where implemented;
- targeted Claude path where current cost/control policy permits;
- adaptive-backend capability mismatch negative case;
- stale Zero identity or stale bundled manifest negative case;
- candidate direct-state/effect mutation negative case;
- blocked non-free backend before provider secret/network touch under FREE_ONLY;
- free backend network case when upstream policy admits it;
- stable workspace with `REFUTED` evidence, proving `WORKSPACE_STABILITY != FACTUAL_TRUTH` and blocking canonical write/effect authority.

## Validator and regressions

`the artefact/blogpost_entity/validate_unified_cognitive_fabric_receipt_v1.py` implements the deterministic source-level admission checks for this envelope.

`the artefact/blogpost_entity/test_unified_cognitive_fabric_receipt_v1.py` covers the unified receipt family, exact Git IDs, stale identity, provider admission/execution coupling, FREE_ONLY cost classes, Claude compiled-external semantics, J-Space observation/intervention separation, candidate-only authority, epistemic truth separation, direct state/effect smuggling, GWT winner constraints, terminal tamper detection and non-finite JSON rejection.

The `WORKSPACE_STABILITY_TRUTH_CONFUSION_MUTATION` case in the retained lane is a regression-only fusion of the already-consumed unusual intervention from PR #1046; it is not a second unusual experiment.

## Promotion boundary

This contract creates no J-Space, GWT, Claude, 0.8B, model-quality, BASE, Whole-GWT or whole-product PASS by itself.

Promotion requires an actually-started exact-source Ubuntu execution receipt and all existing higher-priority FREE_ONLY, truth, provenance, effect and Harness-immutability laws to remain satisfied.
