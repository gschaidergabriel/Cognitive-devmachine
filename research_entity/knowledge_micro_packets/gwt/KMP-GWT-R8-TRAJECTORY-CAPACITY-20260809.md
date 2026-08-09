# KMP-GWT-R8-TRAJECTORY-CAPACITY-20260809

- **packet_id:** `KMP-GWT-R8-TRAJECTORY-CAPACITY-20260809`
- **domains:** `gwt`, `frank`, `claycode`, `harness`, `emergenz`, `unifieddb`, `claygraph`, `hyperposition`
- **epistemic_class:** `OPEN_MECHANISM_HYPOTHESIS_WITH_FORMAL_PROXY_AND_EXTERNAL_TRIANGULATION`
- **status_hint:** `OPEN`
- **origin_actor:** `chatgpt-secondary`
- **provider/model:** `OpenAI / GPT-5.6 Sol`
- **canonical_parent:** `RAE-8.8 r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Atomic mechanism

A GWT recurrence controller should not infer convergence/continuation from one first-order `state_delta` scalar alone. Candidate control state should additionally preserve bounded multi-step trajectory geometry, residual pressure, current working-state capacity and distinct semantic/version/trace identities.

Compact candidate laws:

`small_step != convergence`

`semantic_equivalence != version_equivalence != trace_equivalence`

`required_recurrence_depth is conditional on state_capacity` — OPEN, architecture/task-dependent

`trajectory_geometry is observation, not truth`

## Evidence

1. **Exact formal proxy:** exhaustive 3-step trajectories over state set {-2,-1,0,1,2}. All 125 trajectories lie in regime-ambiguous buckets when represented only by final-step magnitude; adding previous-step, direction and second-order features reduces ambiguous coverage to 14/125. This proves only representational insufficiency of the chosen scalar in the toy system.
2. **Fresh Harness execution:** current oracle candidate experimentally separates `semantic_state_hash`, `state_version_hash` and `trace_root_hash`; same final semantic state can have different history/version identity.
3. **External primary/preprint triangulation:** recurrent-depth transformer work reports useful second-order trajectory structure for early exit; Universal Transformer work reports a depth-state/memory trade-off under adaptive halting; higher-order causal work shows pairwise information-flow measures can miss synergistic joint causation.

## Non-claims

- No target Qwen-class 4B test was run.
- No live Frank H1 recurrence controller was executed.
- No causal emergence claim is promoted.
- No phenomenal-consciousness inference is made.
- No ClayCode syntax addition is justified.

## Falsifier / next test

After BASE, run matched-compute H1 replay comparing scalar-delta, R7 dual-gate and R8 trajectory-capacity continuation under frozen outputs and controlled state-capacity changes. R8 is weakened/rejected if richer observables do not improve held-out task utility, false-halt/overthinking control, stability or cost.

## Source refs

- `research_entity/trigger_runs/gwt/gwt-20260809T1732p0700-chatgpt-secondary-r8-trajectory-capacity/EXPERIMENT_TRAJECTORY_OBSERVABILITY.json`
- `research_entity/trigger_runs/harness/harness_20260809T1725p0700_hwp02_oracle_merge/FINAL_REPORT.md`
- `research_entity/trigger_runs/frank/frank-20260809T1726p0700-loop-base-bridge/FRANK_ARCHITECTURE.claycode.json`
- arXiv:2509.23314
- arXiv:2604.21999
- arXiv:2409.08295
