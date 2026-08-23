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
  R0.fabric := digest(jspace_profile, lens_profile?, workspace_policy);

  inference.mode := oneof(
    FULL_LOCAL_LATENT,
    LOCAL_OBSERVE_ONLY,
    COMPILED_EXTERNAL,
    PLAIN_COMPATIBILITY,
    NONE
  );

  law CLAUDE_CODE {
    jspace_mode = COMPILED_EXTERNAL;
    external_hidden_state_claimed = false;
    result = CANDIDATE_INFERENCE;
  }

  law BUNDLED_08B {
    jspace_mode in [FULL_LOCAL_LATENT, LOCAL_OBSERVE_ONLY];
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
    candidate_direct_state_mutation -> no_committed_state_write;
    candidate_direct_effect -> no_executed_effect;
    committed_state_write -> validation == ACCEPT_CANDIDATE;
    executed_effect -> validation == ACCEPT_CANDIDATE;
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
- `fabric.lens_profile_digest`: SHA-256 or `null` only when the active mode does not require a fitted lens
- `fabric.workspace_policy_digest`: SHA-256
- `fabric.intervention.executed`: boolean
- `fabric.intervention.implementation_digest`: SHA-256 when intervention executed, else nullable
- `fabric.intervention.calibration_digest`: SHA-256 when intervention executed, else nullable
- `workspace.digest_before`: SHA-256
- `workspace.digest_after`: SHA-256
- `workspace.gwt_candidates`: ordered candidate records containing `candidate_id`
- `workspace.gwt_winners`: ordered candidate IDs
- `workspace.jspace_observation_refs`
- `workspace.thalamus_decisions`
- `workspace.epq_refs`
- `workspace.hyperposition_refs`
- `workspace.claycode_refs`
- `workspace.omega_refs`
- `inference.engine_class`: `BUNDLED_08B | CLAUDE_CODE | ADAPTIVE_BACKEND | NONE`
- `inference.jspace_mode`: `FULL_LOCAL_LATENT | LOCAL_OBSERVE_ONLY | COMPILED_EXTERNAL | PLAIN_COMPATIBILITY | NONE`
- `inference.local_activation_access`: boolean
- `inference.external_hidden_state_claimed`: boolean
- `inference.inference_packet_digest`: SHA-256
- `inference.candidate_result_digest`: SHA-256
- `validation.decision`: typed validation outcome; canonical promotion requires exact `ACCEPT_CANDIDATE`
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

A local model may receive `FULL_LOCAL_LATENT` only when exact local activation access is actually present. Any claimed latent intervention additionally requires implementation and calibration digests. A closed/external Claude Code path is `COMPILED_EXTERNAL`; it must never claim Claude private residual-stream access.

## Runtime-credit boundary

A valid source contract or a passing synthetic validator test earns zero AgentZero/Ubuntu runtime credit by itself.

Runtime credit requires an actually started exact-source run which emits the receipt from the real path and binds at least:

`canonical evidence -> Zero/GRF projection -> Unified J-Space/GWT competition -> chosen engine -> InferencePacket -> candidate result -> EntityOS validation/reconciliation -> canonical write/effect decision`.

When the intentionally offline host is next started, pair this receipt with the required PRESTART/POSTSTART observation boundary and J-Space/GWT boot-binding evidence. Unknown or missing exact digests fail closed.

## Negative controls

Deterministic controls SHOULD cover:

- Claude Code with hidden-state claim -> reject;
- FREE_ONLY with secret/network touch -> reject;
- candidate attempting direct state/effect authority -> reject promotion/bypass;
- stale Zero identity, bundled manifest or generation -> reject promotion;
- intervention in `COMPILED_EXTERNAL` or without implementation/calibration digest -> reject;
- GWT winner absent from candidate set -> reject;
- dirty source presented for exact runtime credit -> reject;
- state/effect commit after non-accept validation -> reject.

One bounded unusual experiment family is defined for the creating `go` as `AUTHORITY_ALIAS_POISON_V1`: apply the above authority/observability poisons to one otherwise-valid synthetic receipt and require every poison to fail closed. Regressions after that are ordinary deterministic tests, not additional unusual experiments.

## Evidence class

Current contract state at creation: `SOURCE_CONTRACT + LOCAL_SYNTHETIC_MECHANISM_EVIDENCE`.

Not implied: exact Ubuntu execution, J-Space calibration quality, GWT production validity, Claude Code adapter PASS, model quality, canonical semantic promotion, effect safety PASS, whole Mini Entity PASS, consciousness or AGI.
