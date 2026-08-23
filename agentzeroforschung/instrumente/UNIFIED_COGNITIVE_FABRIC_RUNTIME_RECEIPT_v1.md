# UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1

Status: SOURCE CONTRACT / RUNTIME CREDIT ZERO UNTIL EXACT EXECUTION

Purpose: bind one executable Mini Entity / EntityOS / Zero cognition cycle to exact source, identity, bundled cognition bytes, Unified J-Space/GWT workspace state, inference-engine capability mode, candidate-only return, upstream backend admission, deterministic validation and final state/effect outcome.

This instrument operationalizes the current owner architecture without promoting architecture prose, workspace stability or model output to runtime/factual truth.

## ClayCode semantic contract

```claycode
receipt UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT_V1 {
  R0.source := exact(commit, tree, dirty=false);
  R0.identity := digest(Zero) + digest(GRF) + entity_generation;
  R0.core := digest(manifest, checkpoint, tokenizer, runtime);
  R0.fabric := digest(jspace_profile, lens_profile?, workspace_policy, workspace_calibration);

  invariant PORTABILITY {
    PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY;
    local_jspace_credit -> exact(checkpoint, tokenizer, runtime, lens, workspace_calibration);
  }

  inference.mode := oneof(
    FULL_LOCAL_LATENT,
    LOCAL_OBSERVE_ONLY,
    COMPILED_EXTERNAL,
    PLAIN_COMPATIBILITY,
    NONE
  );

  law INFERENCE_BINDING {
    executed -> backend_admitted;
    executed -> candidate_result_digest + epistemic_status;
    !executed -> candidate_result_digest == null;
    !executed -> epistemic_status == NOT_APPLICABLE;
    result = CANDIDATE_INFERENCE;
    digest(capability_profile) + digest(adapter_contract) + adapter_version;
  }

  law CLAUDE_CODE {
    jspace_mode = COMPILED_EXTERNAL;
    external_hidden_state_claimed = false;
    result = CANDIDATE_INFERENCE;
  }

  law BUNDLED_08B {
    jspace_mode in [FULL_LOCAL_LATENT, LOCAL_OBSERVE_ONLY];
    digest(lens_profile) + digest(workspace_calibration);
  }

  law OBSERVE_INTERVENE_SPLIT {
    JSPACE_OBSERVED != JSPACE_INTERVENED;
    intervention.executed -> inference.executed;
    intervention.executed -> jspace_mode == FULL_LOCAL_LATENT;
    intervention.executed -> local_activation_access == true;
    intervention.executed -> digest(implementation) + digest(calibration);
  }

  law GWT {
    winner subset_of candidates;
    workspace_before + competition + workspace_after are receipt-bound;
  }

  law EPISTEMIC_AUTHORITY {
    workspace_stability != factual_truth;
    latent_geometry != factual_truth;
    canonical_state_write_committed | effect_executed
      -> epistemic_status == MEASURED_SUPPORTED;
  }

  law AUTHORITY {
    inference_result != canonical_truth;
    candidate_direct_state_mutation | candidate_direct_effect -> validation != ACCEPT_CANDIDATE;
    candidate_direct_state_mutation -> no_committed_state_write;
    candidate_direct_effect -> no_executed_effect;
    committed_state_write -> validation == ACCEPT_CANDIDATE;
    executed_effect -> validation == ACCEPT_CANDIDATE;
    digest(reconciliation) binds the validation return path;
  }

  law FRESHNESS {
    stale_zero_identity | stale_bundled_manifest | stale_generation
      -> no_backend_admission + no_inference_execution + no_accept + no_state_write + no_effect;
  }

  law PROVIDER_ADMISSION {
    provider_policy_authority = external_existing_supervisor_gate;
    receipt binds digest(provider_policy_authority) + cost_class + backend_admitted;
    receipt does not mint provider policy;
  }

  law FREE_ONLY {
    free_only && cost_class in [PAID, SUBSCRIPTION, UNKNOWN]
      -> backend_admitted == false
      + secret_touch_count == 0
      + network_touch_count == 0;
    free_only && cost_class == FREE
      != universal_no_network_policy;
  }

  law ENVELOPE_INTEGRITY {
    receipt_envelope_digest = sha256(canonical_json(receipt_without_receipt_envelope_digest));
  }

  R6.credit := EXACT_RUNTIME_ONLY_IF_ALL_REQUIRED_FIELDS_AND_LAWS_PASS;
}
```

## Required JSON fields

The original v1 fields remain required, with these strengthened bindings:

- `source.commit`, `source.tree`: exact 40- or 64-hex Git object IDs;
- `source.dirty`: exact `false` for runtime credit;
- `runtime.entity_generation`, Zero/GRF digests and bundled core manifest/checkpoint/tokenizer/runtime digests;
- J-Space/lens/workspace policy/calibration identities;
- `fabric.intervention.executed` plus exact implementation/calibration digests when true;
- GWT candidate/winner sets and workspace/J-Space/Thalamus/EPQ/Hyperposition/ClayCode/omega references;
- `inference.engine_class`: `BUNDLED_08B | CLAUDE_CODE | ADAPTIVE_BACKEND | NONE`;
- `inference.executed`: boolean;
- `inference.epistemic_status`: `MEASURED_SUPPORTED | UNKNOWN | ERROR | REFUTED | NOT_APPLICABLE`;
- `inference.jspace_mode`: `FULL_LOCAL_LATENT | LOCAL_OBSERVE_ONLY | COMPILED_EXTERNAL | PLAIN_COMPATIBILITY | NONE`;
- adapter/capability/inference-packet identities;
- `inference.candidate_result_digest`: SHA-256 only when inference executed; explicit null otherwise;
- validation decision/reconciliation and direct-state/direct-effect attempt flags;
- canonical state-write/effect results;
- `execution_policy.free_only`;
- `execution_policy.cost_class`: `LOCAL | FREE | PAID | SUBSCRIPTION | UNKNOWN`;
- `execution_policy.backend_admitted`;
- `execution_policy.policy_authority_digest`: digest of the existing upstream supervisor/provider policy state used for admission;
- provider secret/network touch counters;
- stale Zero/manifest/generation flags;
- `terminal_result_digest`;
- `receipt_envelope_digest`: SHA-256 over canonical JSON of the receipt with this field omitted.

## Observation versus intervention

`JSPACE_OBSERVED != JSPACE_INTERVENED`

`LENS_READOUT_PRESENT != CAUSAL_STEERING_PRESENT`

`PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`

A local model may receive `FULL_LOCAL_LATENT` only when exact local activation access is actually present. Both local J-Space modes require exact lens/workspace-calibration identity. Any claimed latent intervention additionally requires inference execution, activation access, intervention implementation identity and intervention calibration identity.

A closed/external Claude Code path is `COMPILED_EXTERNAL`; it must never claim Claude private residual-stream access. The same no-fake-hidden-state rule applies to every external/compatibility mode.

## Epistemic and authority boundary

An inference engine result is always candidate inference. Workspace/GWT/J-Space stability is not factual truth.

`WORKSPACE_STABLE + CANDIDATE_REFUTED != CANONICAL_TRUTH`

`CANDIDATE_UNKNOWN != CANONICAL_WRITE_AUTHORITY`

`CANDIDATE_ERROR != EFFECT_AUTHORITY`

A canonical write or executed effect requires `MEASURED_SUPPORTED` in addition to deterministic `ACCEPT_CANDIDATE` reconciliation. Direct candidate state/effect attempts remain fail-closed.

## Provider-admission boundary

The existing supervisor/provider gate remains the policy authority. This receipt only binds its exact policy digest, cost classification and admission result.

Under current `FREE_ONLY=true`:
- `PAID`, `SUBSCRIPTION` and `UNKNOWN` lanes must be rejected before backend execution, provider secret lookup or provider network I/O;
- a `FREE` backend is not automatically converted into a no-network backend; its network/secret permissions remain subject to the upstream capability/policy contract;
- inference execution without recorded backend admission is invalid.

This avoids a second provider-policy authority inside the cognitive fabric.

## Freshness and envelope integrity

Stale Zero identity, bundled manifest or generation now blocks backend admission/inference execution as well as acceptance/state/effect promotion.

`receipt_envelope_digest` detects post-receipt mutation of bound evidence fields. Non-finite JSON is rejected so canonical digest identity cannot depend on permissive NaN/Infinity serialization.

## Runtime-credit boundary

A valid source contract or passing isolated validator tests earn zero AgentZero/Ubuntu runtime credit by themselves.

Runtime credit requires an actually started exact-source run which emits this receipt from the real path and binds at least:

`canonical evidence -> Zero/GRF projection -> Unified J-Space/GWT competition -> upstream backend admission -> chosen engine/capability profile -> InferencePacket -> candidate result/epistemic status -> EntityOS validation/reconciliation -> canonical write/effect decision`.

When the intentionally offline host is next started, pair this receipt with PRESTART/POSTSTART observation and the J-Space/GWT boot-binding boundary. Unknown or missing exact digests fail closed.

## Regression status for this fusion

The canonical validator and test bytes on branch `go/fuse-ucf-receipt-canonical-v1` passed `py_compile` and 20/20 deterministic isolated tests. Their exact Git blob IDs matched the locally executed bytes.

The `WORKSPACE_STABILITY_TRUTH_CONFUSION_MUTATION` case is the single unusual experiment already consumed by the current user-triggered `go`; its retained canonical form is regression-only after fusion. `AUTHORITY_ALIAS_POISON_V1` remains an ordinary deterministic adversarial regression family.

No additional unusual experiment was consumed during fusion.

## Evidence class

Current fusion evidence: `EXACT_GIT_BLOB_LOCAL_COMPONENT_MECHANISM_SUPPORTED`.

Not implied: exact Ubuntu execution, J-Space calibration quality, GWT production validity, Claude Code adapter PASS, bundled 0.8B model quality, canonical semantic promotion, whole Mini Entity PASS, consciousness or AGI.
