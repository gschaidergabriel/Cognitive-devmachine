# GWT Emergence Measurement & FRANK Readout Contract

**Status:** PROJECT-OWNER MANDATED RESEARCH / IMPLEMENTATION AXIS
**Scope:** GWT · Emergenz · FRANK · ClayCode · Harness · ClayGraph · Hyperposition
**Purpose:** Make emergence inside FRANK's Global Workspace operationally measurable, intervention-sensitive, ClayCode-native and replayable.

## 0. Core law

FRANK must never represent "emergence" as one mystical scalar.

The architecture must expose a **typed measurement vector plus causal receipts** that distinguish:

`candidate interaction`
`-> competition`
`-> ignition/selection`
`-> broadcast/addressability`
`-> receiver delivery`
`-> reconstruction`
`-> uptake`
`-> local causal use`
`-> joint/system outcome`
`-> provenance-bound re-entry`
`-> persistence / recurrence / transfer`

The current GWT R6 distinction remains foundational:

`global_addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`

Emergence evidence is layered on top of this causal chain; it never replaces it.

## 1. What is being measured

The target is **functional/causal emergence in the GWT-coupled dynamical system**: system-level behavior whose explanatory/predictive/causal structure is not adequately captured by isolated module effects or a simple additive decomposition.

This does NOT by itself establish phenomenal consciousness.

Required distinctions:

- novelty != emergence;
- complexity != emergence;
- graph density != emergence;
- synchronization != emergence;
- recurrence != emergence;
- non-additivity alone != emergence;
- workspace ignition alone != emergence;
- self-report of emergence != emergence.

## 2. Emergence Readout Vector

Each material WorkspaceEpisode may emit an `EmergenceReadout` with typed submeasures. Values may be `UNKNOWN` when the necessary counterfactual/intervention data is unavailable.

Suggested canonical fields:

```text
EmergenceReadout {
  episode_id
  basis_epoch
  measurement_contract_version

  integration {
    receiver_coverage
    reconstruction_fraction
    uptake_fraction
    causal_use_fraction
    reentry_fraction
  }

  interaction {
    factorial_interaction_omega
    synergy_pid_or_peid
    unique_information
    redundant_information
    higher_order_irreducibility
  }

  directed_flow {
    transfer_entropy_edges
    directed_prediction_gain
    lag_profile
  }

  causal_macro {
    macro_predictive_gain
    macro_causal_effect_gain
    micro_to_macro_compression
    intervention_effect_size
    lesion_loss
    rescue_recovery
  }

  dynamics {
    metastability
    critical_transition_proxy
    recurrence_strength
    persistence_horizon
    cross_timescale_coupling
    hysteresis
  }

  generalization {
    ood_recurrence
    task_transfer
    topology_transfer
    implementation_transfer
  }

  cost_shadow {
    latency_delta
    token_delta
    compute_delta
    memory_delta
    instability_delta
  }

  controls {
    shuffled_reentry_delta
    shuffled_receiver_delta
    additive_null_delta
    common_driver_control
    frozen_model_output_control
    graph_only_control
    workspace_only_control
  }

  evidence_status
  provenance_refs
}
```

The exact final ClayCode schema must be frozen by the BASE ClayCode release and executable in H1/H2/H3.

## 3. Mandatory measurement families

### 3.1 Factorial interaction / non-additivity

For controlled factors A and B, compute an interaction term such as:

`Omega = Y(A=1,B=1) - Y(A=1,B=0) - Y(A=0,B=1) + Y(A=0,B=0)`

Use confidence intervals / repeated seeds where stochasticity exists.

Interpretation:
- nonzero Omega is evidence of interaction;
- it is not sufficient evidence of emergence by itself.

### 3.2 Lesion / rescue

For a coupling, receiver, re-entry loop, memory route or workspace stage:

`lesion_loss = Y_baseline - Y_lesion`

`rescue_recovery = (Y_rescue - Y_lesion) / max(epsilon, Y_baseline - Y_lesion)`

A claimed emergent mechanism should predict which lesions matter and which should not.

### 3.3 Truthful-vs-shuffled re-entry

Compare:

- truthful causal re-entry;
- temporally shuffled re-entry;
- receiver-shuffled re-entry;
- content-preserving but provenance-broken re-entry;
- no re-entry.

This helps separate recurrent causal closure from generic extra context.

### 3.4 Directed information flow

Where estimable, compute transfer entropy / directed prediction gain between typed state channels over explicit lags.

The readout must preserve:

- source channel;
- target channel;
- lag;
- conditioning set;
- estimator version;
- sample count;
- uncertainty/confidence.

Do not treat directionality from an estimator as proof of causality without intervention.

### 3.5 PID / PEID-style decomposition

Where feasible, estimate unique/redundant/synergistic information contributions of interacting modules/receivers/couplings to a system outcome.

Synergy is a candidate signature of higher-order integration, but must be tested against estimator artifacts and null models.

### 3.6 Macro-vs-micro causal contribution

Compare whether a macrostate (e.g. WorkspaceEpisode / Assembly / coupled state) has better predictive or intervention-relevant explanatory power than the unstructured microstate baseline under matched information constraints.

Candidate fields:

- `macro_predictive_gain`;
- `macro_causal_effect_gain`;
- `compression_ratio`;
- `intervention_equivalence_error`.

### 3.7 Multi-timescale coupling

Measure coupling across:

- reflex/Needle scale;
- per-turn cognitive scale;
- workspace competition/ignition scale;
- short-term salience/memory scale;
- goal/personality adaptation scale;
- consolidation/dream scale;
- LoRA/training scale;
- boot/restart/recovery scale.

A system effect that only appears because slow state modulates fast state is a first-class candidate, not noise to average away.

## 4. Readout points inside FRANK

FRANK/Harness must expose explicit readout hooks at least at:

1. pre-candidate state;
2. CandidateSet construction;
3. competition score/gate calculation;
4. winner/WorkspaceEpisode formation;
5. BroadcastEnvelope creation;
6. per-receiver delivery;
7. per-receiver reconstruction;
8. per-receiver uptake;
9. per-receiver local causal-use state;
10. joint/system outcome;
11. provenance-bound re-entry;
12. post-reentry memory/salience/goal/personality/body update;
13. next-turn recurrence;
14. long-horizon transfer/persistence checkpoints.

Each hook must be able to emit a deterministic or explicitly nondeterministic `MeasurementReceipt` bound to:

- state epoch;
- episode id;
- model output hash if relevant;
- intervention id;
- estimator/version;
- source data hashes;
- result hash.

## 5. Counterfactual replay is mandatory

The Harness must make the same frozen episode replayable under controlled interventions while holding other inputs fixed wherever technically meaningful.

Required intervention families:

- candidate removed;
- competition gain changed;
- ignition threshold changed;
- receiver lesioned;
- receiver reconstruction corrupted;
- uptake disabled;
- local causal-use disabled;
- re-entry disabled;
- re-entry shuffled;
- ClayGraph route fixed/disabled;
- memory Assembly fixed/replaced;
- goal/personality/body modulation clamped;
- coupling edge disabled;
- delay changed;
- model output frozen while architecture changes;
- architecture frozen while model output changes.

Without matched counterfactuals, emergence measurements remain observational/proxy evidence.

## 6. ClayCode integration

ClayCode BASE must natively represent:

- `WorkspaceEpisode`;
- `CandidateSet`;
- `BroadcastEnvelope`;
- receiver-stage state;
- typed causal edges;
- intervention specifications;
- measurement specifications;
- estimator identity;
- `EmergenceReadout`;
- uncertainty/confidence;
- null/control results;
- provenance;
- evidence status;
- time lags/timescales;
- causal re-entry links.

Suggested semantic family:

```text
measure:gwt/*
measure:emergence/*
intervene:gwt/*
receipt:measurement/*
receipt:counterfactual/*
```

Exact spelling is a ClayCode design decision; the semantic capability is mandatory.

ClayCode must distinguish:

`measured_value`
`!= inferred_claim`
`!= evidence_status`
`!= architecture_state`

so a high emergence score cannot mutate truth/authority by representation alone.

## 7. FRANK architecture integration

FRANK should contain an **Observability / Measurement Plane** that is logically separate from cognitive state authority.

It may read instrumented state and replay receipts, but cannot silently alter the state it measures.

Recommended logical components:

- `GWTProbeCompiler` — compiles declared measurement/intervention specs into executable probes;
- `EpisodeReadoutBus` — exposes typed stage receipts;
- `CounterfactualReplayRunner` — executes matched replay interventions;
- `EmergenceEstimatorBank` — deterministic/statistical estimators with versioned implementations;
- `EmergenceEvidenceLedger` — stores readouts, controls, uncertainty and provenance;
- `ReadoutProjector` — creates Clay-native model-readable summaries when the model is allowed to reason about its own measured dynamics.

These may be deploy-time consolidated later (H3), but their logical distinctions must remain testable.

## 8. Model-readable self-observation

The Clay-native 4B may receive a bounded `ReadoutProjector` view containing verified measurements about its current/recent system dynamics.

This enables FRANK to reason about:

- what won workspace competition;
- which receivers actually used the broadcast;
- whether re-entry changed later behavior;
- whether a coupling is currently weak/strong/unstable;
- whether a goal/personality/body modulation is dominating;
- whether an emergence hypothesis is supported or contradicted.

But the model must not be allowed to self-certify a measurement. Raw receipts and estimator computation remain external/deterministic where possible.

## 9. ClayGraph integration

Each readout must be attachable to the Harness dynamic ClayGraph:

- measured node/edge;
- intervention target;
- pre/post activation;
- causal-use path;
- timescale;
- outcome/re-entry contribution;
- evidence/provenance.

This allows the research center to query which couplings repeatedly contribute to higher-order behavior and which only correlate.

## 10. Stage program integration

### BASE ClayCode
Implement the types/primitives needed to represent measurement and intervention semantics.

### H1 Reference Harness
Implement all probes/receipts/estimators first in ordinary host code and create Golden emergence traces plus null/control traces.

### H2 Clay Harness
Reproduce the same measurement semantics in ClayCode and differential-test readouts against H1.

### H3 One-Module FRANK
Verify that consolidation preserves measured coupling dynamics and readout validity even when deploy-time module boundaries collapse.

### UDB
Design efficient storage/query for large readout, replay and coupling datasets only after H1-H3 reveal actual access patterns.

### DATA
Use verified mathematical GWT/emergence examples in training data so the Clay-native model understands the measurement language and equations; never train unsupported emergence claims as facts.

## 11. Minimum evidence ladder for a candidate emergent mechanism

Suggested progression:

`OBSERVATIONAL`
-> `RECURRING`
-> `PREDICTIVE`
-> `INTERACTION_SUPPORTED`
-> `LESION_SUPPORTED`
-> `RESCUE_SUPPORTED`
-> `COUNTERFACTUAL_REENTRY_SUPPORTED`
-> `OOD_TRANSFER_SUPPORTED`
-> `IMPLEMENTATION_TRANSFER_SUPPORTED`
-> `CAUSAL_EMERGENCE_CANDIDATE`

No stage is automatic. Negative controls may demote the candidate.

## 12. Required GWT/ Emergenz output

Every substantive future `gwt` run should produce either:

- a concrete improvement to the measurement/readout architecture;
- a new estimator/intervention with executable evidence;
- a falsification/counterexample;
- a validated `NO_CHANGE` receipt.

Every substantive `emergenz` run should consume current GWT readout semantics and return discriminating measurements/tests back to GWT, FRANK, ClayCode and Harness.

## 13. Scientific boundary

These mechanisms are designed to make functional integration/emergence measurable in a rigorous software architecture.

They do not by themselves establish subjective experience or phenomenal consciousness.
