# UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1 — revision 2

Status: SOURCE CONTRACT / RUNTIME CREDIT ZERO UNTIL EXACT EXECUTION

Purpose: bind one executable Mini Entity / EntityOS / Zero cognition cycle to exact source, identity, bundled cognition bytes, Unified J-Space/GWT workspace state, inference-engine capability mode, candidate-only return, deterministic validation and final state/effect outcome.

Revision 2 corrects a semantic alias in the originally merged v1 source contract. **The local bundled Unified J-Space/GWT Fabric has its own latent mode, independent of the selected inference engine's latent capability mode.** This matters especially for Claude Code: Claude remains `COMPILED_EXTERNAL`, while the mandatory bundled ~0.8B reference substrate may simultaneously run `LOCAL_OBSERVE_ONLY` or calibrated `FULL_LOCAL_LATENT` J-Space/GWT processing around the compiled external inference packet.

No accepted runtime receipt existed under revision 1, and all executable J-Space/GWT/Claude-adapter credit was already zero. Revision 2 therefore fails closed on the ambiguous revision-1 field shape instead of preserving it as a second semantic path.

## ClayCode semantic contract

```claycode
receipt UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT_V1_REV2 {
  receipt_version := "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1";
  contract_revision := 2;

  R0.source := exact(commit, tree, dirty=false);
  R0.identity := digest(Zero) + digest(GRF) + entity_generation;
  R0.core := digest(manifest, checkpoint, tokenizer, runtime) + exact_bytes_verified;

  fabric.local_jspace_mode := oneof(
    FULL_LOCAL_LATENT,
    LOCAL_OBSERVE_ONLY,
    DISABLED
  );

  inference.engine_jspace_mode := oneof(
    FULL_LOCAL_LATENT,
    LOCAL_OBSERVE_ONLY,
    COMPILED_EXTERNAL,
    PLAIN_COMPATIBILITY,
    NONE
  );

  invariant MODE_SEPARATION {
    fabric.local_jspace_mode != inference.engine_jspace_mode_authority;
    fabric_intervention_authority derives_only_from fabric.local_jspace_mode;
    engine_capability derives_only_from inference.engine_jspace_mode;
  }

  invariant PORTABILITY {
    PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY;
    active_local_fabric -> exact(
      checkpoint,
      tokenizer,
      runtime,
      lens,
      workspace_calibration,
      boot_binding_receipt,
      jlens_admission_receipt
    );
  }

  law ACTIVE_LOCAL_FABRIC {
    local_jspace_mode in [FULL_LOCAL_LATENT, LOCAL_OBSERVE_ONLY]
      -> bundled_core.exact_bytes_verified == true
      -> fabric.local_activation_access == true
      -> lens_profile present
      -> workspace_calibration_status == MEASURED_EXACT_BUNDLE
      -> upstream.boot_binding_validated == true
      -> upstream.jlens_admission_phase == PASS_BOUNDED_JACOBIAN;
  }

  law CLAUDE_CODE {
    engine_class == CLAUDE_CODE
      -> engine_jspace_mode == COMPILED_EXTERNAL
      -> engine_local_activation_access == false
      -> external_hidden_state_claimed == false;
    result = CANDIDATE_INFERENCE;
  }

  law BUNDLED_ENGINE {
    engine_class == BUNDLED_08B
      -> engine_jspace_mode in [FULL_LOCAL_LATENT, LOCAL_OBSERVE_ONLY];
    active_local_fabric + engine_class == BUNDLED_08B
      -> engine_jspace_mode == fabric.local_jspace_mode;
  }

  law OBSERVE_INTERVENE_SPLIT {
    JSPACE_OBSERVED != JSPACE_INTERVENED;
    intervention.executed -> fabric.local_jspace_mode == FULL_LOCAL_LATENT;
    intervention.executed -> digest(implementation) + digest(calibration);
  }

  law GWT {
    winner subset_of candidates;
    workspace_before + competition + workspace_after are receipt-bound;
  }

  law INFERENCE_BINDING {
    digest(capability_profile) + digest(adapter_contract) + adapter_version;
    result = CANDIDATE_INFERENCE;
  }

  law AUTHORITY {
    inference_result != canonical_truth;
    candidate_direct_state_mutation | candidate_direct_effect -> validation != ACCEPT_CANDIDATE;
    candidate_direct_state_mutation -> no_committed_state_write;
    candidate_direct_effect -> no_executed_effect;
    committed_state_write -> validation == ACCEPT_CANDIDATE;
    executed_effect -> validation == ACCEPT_CANDIDATE;
    digest(reconciliation) binds validation return path;
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

### Contract / source / runtime
- `receipt_version`: exact `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`
- `contract_revision`: integer `2`
- `source.commit`: 40-hex Git commit SHA
- `source.tree`: 40-hex Git tree SHA
- `source.dirty`: must be `false`
- `runtime.entityos_version`
- `runtime.mini_entity_version`
- `runtime.entity_generation`

### Identity / bundled core
- `identity.zero_digest`: SHA-256
- `identity.grf_digest`: SHA-256
- `bundled_core.manifest_digest`: SHA-256
- `bundled_core.checkpoint_digest`: SHA-256
- `bundled_core.tokenizer_digest`: SHA-256
- `bundled_core.runtime_digest`: SHA-256
- `bundled_core.exact_bytes_verified`: boolean

### Local Unified Cognitive Fabric
- `fabric.local_jspace_mode`: `FULL_LOCAL_LATENT | LOCAL_OBSERVE_ONLY | DISABLED`
- `fabric.local_activation_access`: boolean
- `fabric.jspace_profile_digest`: SHA-256
- `fabric.lens_profile_digest`: SHA-256 for active local fabric; nullable only when local fabric is disabled
- `fabric.workspace_policy_digest`: SHA-256
- `fabric.workspace_calibration_digest`: SHA-256
- `fabric.workspace_calibration_status`: `MEASURED_EXACT_BUNDLE | UNMEASURED_SOURCE_ONLY`
- `fabric.intervention.executed`: boolean
- `fabric.intervention.implementation_digest`: SHA-256 when executed, else nullable
- `fabric.intervention.calibration_digest`: SHA-256 when executed, else nullable

### Upstream exact admission bindings
- `upstream.boot_binding_receipt_digest`: SHA-256
- `upstream.boot_binding_validated`: boolean
- `upstream.jlens_admission_receipt_digest`: SHA-256
- `upstream.jlens_admission_phase`: `PASS_BOUNDED_JACOBIAN | PASS_WEIGHTED_FORWARD_HOOKS | PASS_LAYOUT_SOURCE_RUNTIME | NOT_RUN`

Active local J-Space/GWT runtime credit requires a validated exact boot binding and `PASS_BOUNDED_JACOBIAN`; source/layout/forward-only evidence cannot silently promote the fabric.

### Workspace/GWT
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

### Selected inference engine
- `inference.engine_class`: `BUNDLED_08B | CLAUDE_CODE | ADAPTIVE_BACKEND | NONE`
- `inference.engine_jspace_mode`: `FULL_LOCAL_LATENT | LOCAL_OBSERVE_ONLY | COMPILED_EXTERNAL | PLAIN_COMPATIBILITY | NONE`
- `inference.adapter_version`
- `inference.capability_profile_digest`: SHA-256
- `inference.adapter_contract_digest`: SHA-256
- `inference.engine_local_activation_access`: boolean
- `inference.external_hidden_state_claimed`: boolean
- `inference.inference_packet_digest`: SHA-256
- `inference.candidate_result_digest`: SHA-256

### Validation / execution / freshness
- `validation.decision`: `ACCEPT_CANDIDATE | REJECT_CANDIDATE | ABSTAIN | ERROR`
- `validation.reconciliation_digest`: SHA-256
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

## Why the mode split is mandatory

The unified product path is conceptually:

```text
canonical evidence/state
    -> bundled ~0.8B reference substrate
    <-> local J-Space/GWT Fabric
    -> targeted InferencePacket
    -> selected engine
         Claude Code: COMPILED_EXTERNAL
         hookable local engine: local latent mode if admitted
         plain API: compatibility mode
    -> candidate inference
    -> deterministic reconciliation
    -> canonical state/effect decision
```

Therefore these two facts may be simultaneously true and are **not contradictory**:

```text
fabric.local_jspace_mode = FULL_LOCAL_LATENT
inference.engine_class = CLAUDE_CODE
inference.engine_jspace_mode = COMPILED_EXTERNAL
```

The first describes the bundled local cognitive fabric. The second describes Claude Code's exposed capability boundary. Revision 1 incorrectly let the second field veto the first; revision 2 removes that false coupling.

## Observation / intervention / truth boundaries

`JSPACE_OBSERVED != JSPACE_INTERVENED`

`LENS_READOUT_PRESENT != CAUSAL_STEERING_PRESENT`

`PORTABLE_ARCHITECTURE != PORTABLE_GEOMETRY`

`JSPACE_SIGNAL != FACT`

`INFERENCE_ENGINE != CANONICAL_TRUTH_AUTHORITY`

`INFERENCE_ENGINE != DIRECT_EFFECT_AUTHORITY`

An active local fabric requires exact bundled bytes, local activation access, matching lens/profile/calibration evidence, validated boot binding and bounded Jacobian admission. A latent intervention additionally requires a `FULL_LOCAL_LATENT` local **fabric** mode plus exact implementation/intervention-calibration identity. External engines never gain hidden-state credit by being surrounded by a local fabric.

## Runtime-credit boundary

A valid revision-2 receipt or passing validator regression remains only a contract/component result until emitted by an actually started exact-source Mini Entity / EntityOS / AgentZero path.

Exact runtime evidence must bind:

`boot/admitted exact bundle -> calibrated local J-Space/GWT workspace -> engine/capability choice -> InferencePacket -> candidate result -> deterministic reconciliation -> canonical write/effect decision`.

No current source/fixture result implies exact Ubuntu/AgentZero runtime PASS, model quality, Whole-GWT PASS, Claude adapter PASS, factual truth, consciousness or AGI.

## Deterministic regression obligations

At minimum:

- Claude `COMPILED_EXTERNAL` + local `LOCAL_OBSERVE_ONLY` fabric -> structurally valid when exact admissions are bound;
- Claude `COMPILED_EXTERNAL` + local calibrated `FULL_LOCAL_LATENT` fabric intervention -> structurally valid;
- active local fabric with `UNMEASURED_SOURCE_ONLY` -> reject;
- active local fabric without validated boot binding or bounded Jacobian admission -> reject;
- bundled engine mode disagreeing with active bundled local fabric mode -> reject;
- intervention when local fabric is not `FULL_LOCAL_LATENT` -> reject;
- external engine hidden-state claim -> reject;
- FREE_ONLY network/secret touch -> reject;
- stale identity/generation promotion -> reject;
- direct candidate state/effect authority -> reject;
- GWT winner outside candidate set -> reject;
- dirty source exact-runtime claim -> reject;
- canonical write/effect after non-accept validation -> reject.

All such controls are ordinary deterministic regressions for this correction. No unusual-experiment slot is claimed without an upstream atomic macrocycle lease.
