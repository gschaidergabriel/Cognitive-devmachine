# Semantic Intervention Equivalence — candidate contract

Status: OPEN research candidate; not accepted ClayCode syntax and not a stage gate by itself.

## Problem

A cross-implementation causal claim is meaningful only if the intervention being compared denotes the same semantic causal operation.

`same label != same physical target != same semantic intervention`

This matters especially for H3: logical FRANK planes may survive while physical/module coordinates are fused or remapped.

## Formal sketch

Let:

- `S` be the frozen semantic state space;
- `X_j` be implementation `j`'s low-level state;
- `alpha_j : X_j -> S` be its semantic projection/refinement witness;
- `I` be a semantic intervention;
- `lambda_j(I)` be the implementation-specific lowering of `I`;
- `tau_j(lambda_j(I), c)` be the intervened low-level trajectory under context/input fixture `c`.

Cross-implementation intervention equivalence requires, for preregistered channels/horizon/tolerance:

`E_cross(I,i,j,c) = D(alpha_i(tau_i(lambda_i(I),c)), alpha_j(tau_j(lambda_j(I),c))) <= epsilon`

A stronger per-implementation commutation test compares low-level execution with the semantic reference transition:

`E_commute = D(alpha_j(F_j^{lambda_j(I)}(x,u)), F_S^I(alpha_j(x),u))`

No single scalar proves equivalence. Preserve channel-wise trajectory errors, state/hash mismatches, collateral writes, timing and uncertainty.

## Candidate SemanticIntervention fields

```text
SemanticIntervention {
  semantic_intervention_id
  semantic_contract_version
  target_semantic_handle
  intervention_kind
  value_or_transform_spec
  activation_condition
  start_epoch_or_time
  duration_or_horizon
  common_snapshot_id
  controlled_inputs_ref
  expected_semantic_write_set
  forbidden_semantic_write_set
  rescue_or_inverse_ref?
  provenance
}
```

Candidate `intervention_kind` family:

- `HARD_SET`
- `CLAMP`
- `REMOVE_RELATION`
- `DISABLE_CAUSAL_USE`
- `TRANSFORM_MECHANISM`
- `GAIN_CHANGE`
- `DELAY_CHANGE`
- `SHUFFLE`
- `PROVENANCE_BREAK`
- `FREEZE_ADAPTATION`
- `RESTORE_STATE`
- `RESCUE`

## Candidate InterventionLoweringReceipt fields

```text
InterventionLoweringReceipt {
  semantic_intervention_id
  implementation_id
  implementation_artifact_hash
  semantic_projection_id
  semantic_projection_hash
  lowering_id
  lowering_version
  low_level_targets
  low_level_transform
  expected_low_level_write_set
  observed_low_level_write_set
  expected_semantic_write_set
  observed_semantic_write_set
  collateral_semantic_write_set
  pre_state_hash
  post_state_hash
  baseline_trace_hash
  intervention_trace_hash
  channelwise_commutation_error
  trajectory_equivalence_error
  effect_equivalence_error
  tolerance_contract_id
  pass_fail_unknown
  evidence_status
  provenance_refs
}
```

## Hard invariants

1. `semantic_intervention_id` is bound to semantic meaning, never to a process/module address.
2. Two implementations may use different low-level target sets for the same semantic intervention.
3. Same unlesioned output is insufficient for causal equivalence.
4. A low aggregate output error cannot hide forbidden collateral semantic writes.
5. Rescue must state what is restored: mechanism only, semantic state, learner state, topology, or a full common snapshot.
6. UNKNOWN is valid when the semantic projection or intervention lowering cannot be validated.
7. Measurement/readout code cannot mint execution authority.
8. H1/H2/H3 comparisons must preserve implementation and projection hashes.

## BASE-stage test before language change

Attempt to express the structures above using the current admitted ClayCode G9 typed IR and execute a small parser/canonicalizer/type-effect/evaluator fixture.

- If it works: no language redesign; keep this as a library/schema/test contract.
- If it fails because the semantics cannot be represented or validated: preserve the executable counterexample and reopen the smallest necessary BASE design surface.

## Future H1/H2/H3 Golden test family

For each semantic causal handle:

1. run common-snapshot baseline;
2. lower the same semantic intervention into H1/H2/H3;
3. compare semantic projected trajectories, not only user-visible output;
4. inject deliberately wrong low-level mappings;
5. require the validator to reject mappings with collateral semantic writes or excess commutation error;
6. run rescue/restoration with explicit state-lineage semantics;
7. preserve timing/cost shadows.

The candidate is validated only if it catches representation-fusion counterexamples while accepting correct alternative low-level implementations.
