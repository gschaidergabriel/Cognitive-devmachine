# UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1

Status: SOURCE CONTRACT / RUNTIME CREDIT ZERO UNTIL EXACT EXECUTION

Purpose: bind one executable Mini Entity / EntityOS / Zero cognition cycle to exact source, identity, bundled cognition bytes, Unified J-Space/GWT workspace state, inference-engine capability mode, candidate-only return, deterministic validation and final state/effect outcome.

This instrument operationalizes the current owner architecture without promoting architecture prose to runtime truth.

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
    observation != intervention;
    intervention.executed -> jspace_mode == FULL_LOCAL_LATENT;
    intervention.executed -> digest(implementation) + digest(calibration);
  }

  law GWT {
    winner subset_of candidates;
    workspace_before + competition + workspace_after are receipt-bound;
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
      -> no_accept + no_state_write + no_effect;
  }

  law FREE_ONLY {
    free_only == true -> secret_touch_count == 0 + network_touch_count == 0;
  }

  R6.credit := EXACT_RUNTIME_ONLY_IF_ALL_REQUIRED_FIELDS_AND_LAWS_PASS;
}
```

## Required JSON fields

- `receipt_version`: exact `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`
- `source.commit`: 40-hex Git commit SHA
- `source.tree`: 40-hex Git tree SHA
- `source.dirty`: must be `false` for runtime credit
- `runtime.entityos_version`
- `runtime.mini_entity_version`
- `runtime.entity_generation`
- `identity.zero_digest`: SHA-256
- `identity.grf_digest`: SHA-256
- `bundled_core.manifest_digest`: SHA-256
- `bundled_core.checkpoint_digest`: SHA-256
- `bundled_core.tokenizer_digest`: SHA-256
- `bundled_core.runtime_digest`: SHA-256
- `fabric.jspace_profile_digest`: SHA-256
- `fabric.lens_profile_digest`: SHA-256 for local J-Space modes; nullable only when the active mode does not require a fitted lens
- `fabric.workspace_policy_digest`: SHA-256
- `fabric.workspace_calibration_digest`: SHA-256; exact calibration identity, distinct from policy identity
- `fabric.intervention.executed`: boolean
- `fabric.intervention.implementation_digest`: SHA-256 when intervention executed, else nullable
- `fabric.intervention.calibration_digest`: SHA-256 when intervention executed, else nullable
- `workspace.digest_before`: SHA-256
- `workspace.digest_after`: SHA-256
- `workspace.gwt_candidates`: ordered candidate records containing unique `candidate_id`
- `workspace.gwt_winners`: ordered unique candidate IDs, each present in `gwt_candidates`
- `workspace.jspace_observation_refs`
- `workspace.thalamus_decisions`
- `workspace.epq_refs`
- `workspace.hyperposition_refs`
- `workspace.claycode_refs`
- `workspace.omega_refs`
- `inference.engine_class`: `BUNDLED_08B | CLAUDE_CODE | ADAPTIVE_BACKEND | NONE`
- `inference.jspace_mode`: `FULL_LOCAL_LATENT | LOCAL_OBSERVE_ONLY | COMPILED_EXTERNAL | PLAIN_COMPATIBILITY | NONE`
- `inference.adapter_version`: nonempty version string
- `inference.capability_profile_digest`: SHA-256
- `inference.adapter_contract_digest`: SHA-256
- `inference.local_activation_access`: boolean
- `inference.external_hidden_state_claimed`: boolean
- `inference.inference_packet_digest`: SHA-256
- `inference.candidate_result_digest`: SHA-256
- `validation.decision`: `ACCEPT_CANDIDATE | REJECT_CANDIDATE | ABSTAIN | ERROR`
- `validation.reconciliation_digest`: SHA-256 binding deterministic validation/reconciliation identity/result
- `validation.candidate_attempted_direct_state_mutation`: boolean
- `validation.candidate_attempted_direct_effect`: boolean
- `validation.canonical_state_write_committed`: boolean
- `validation.effect_executed`: boolean
- `execution_policy.free_only`: boolean
- `execution_policy.secret_touch_count`: nonnegative integer
- `execution_policy.network_touch_count`: nonnegative integer
- `freshness.stale_zero_identity`: boolean
- `freshness.stale_bundled_manifest`: boolean
- `freshness.stale_generation`: boolean
- `terminal_result_digest`: SHA-256

## Observation versus intervention

The receipt deliberately separates latent observation from causal intervention.

`JSPACE_OBSERVED != JSPACE_INTERVENED`

`LENS_READOUT_PRESENT != CAUSAL_STEERING_PRESENT`

`PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`

A local model may receive `FULL_LOCAL_LATENT` only when exact local activation access is actually present. Both local J-Space modes require an exact lens profile and exact workspace calibration identity. Any claimed latent intervention additionally requires implementation and intervention-calibration digests. A closed/external Claude Code path is `COMPILED_EXTERNAL`; it must never claim Claude private residual-stream access. The same no-fake-hidden-state rule applies to every external/compatibility mode.

## Candidate and authority boundary

An inference engine result is always candidate inference. A candidate that attempts direct state mutation or direct effect authority cannot be accepted as-is, even when no mutation/effect actually occurred. Canonical writes/effects require `ACCEPT_CANDIDATE` only after deterministic reconciliation, whose digest is bound into the receipt.

This preserves:

`INFERENCE_ENGINE != CANONICAL_TRUTH_AUTHORITY`

`INFERENCE_ENGINE != DIRECT_EFFECT_AUTHORITY`

## Runtime-credit boundary

A valid source contract or a passing synthetic validator test earns zero AgentZero/Ubuntu runtime credit by itself.

Runtime credit requires an actually started exact-source run which emits the receipt from the real path and binds at least:

`canonical evidence -> Zero/GRF projection -> Unified J-Space/GWT competition -> chosen engine/capability profile -> InferencePacket -> candidate result -> EntityOS validation/reconciliation -> canonical write/effect decision`.

When the intentionally offline host is next started, pair this receipt with the required PRESTART/POSTSTART observation boundary and J-Space/GWT boot-binding evidence. Unknown or missing exact digests fail closed.

## Negative controls

Deterministic controls SHOULD cover:

- Claude Code or another external mode with hidden-state claim -> reject;
- FREE_ONLY with secret/network touch -> reject;
- candidate attempting direct state/effect authority -> reject acceptance/promotion/bypass;
- stale Zero identity, bundled manifest or generation -> reject promotion;
- local J-Space mode without an exact lens profile/workspace calibration identity -> reject;
- intervention in `COMPILED_EXTERNAL` or without implementation/calibration digest -> reject;
- GWT winner absent from candidate set or duplicated winner/candidate IDs -> reject;
- dirty source presented for exact runtime credit -> reject;
- state/effect commit after non-accept validation -> reject.

`AUTHORITY_ALIAS_POISON_V1` is a deterministic adversarial regression family over those controls. For the `go` that created this source delta, no upstream atomic macrocycle lease/identifier was available to this organ, so the unusual-experiment classification is explicitly `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`. No macrocycle identifier is invented after the fact. The locally observed 8/8 fail-closed poison result remains mechanism evidence, not an unusual-experiment slot claim.

## Evidence class

Current contract state at creation: `SOURCE_CONTRACT + LOCAL_SYNTHETIC_MECHANISM_EVIDENCE`.

Not implied: exact Ubuntu execution, J-Space calibration quality, GWT production validity, Claude Code adapter PASS, model quality, canonical semantic promotion, effect safety PASS, whole Mini Entity PASS, consciousness or AGI.
