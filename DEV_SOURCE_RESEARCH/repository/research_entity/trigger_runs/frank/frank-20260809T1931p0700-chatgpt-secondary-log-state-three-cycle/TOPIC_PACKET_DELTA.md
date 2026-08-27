# Topic Packet Delta — FRANK Loop Quality, State Lineage and Adaptive Halting

Run: `frank-20260809T1931p0700-chatgpt-secondary-log-state-three-cycle`  
Status: mixed CURRENT component result + OPEN research hypotheses; no canonical promotion

## Topic

How FRANK should turn recurrent state/log trajectories into proposal-only continuation/halting/routing evidence while preserving measurement quality, policy identity, state lineage, replayability and adaptive compute.

## Compiled current view

1. **Low state change is not convergence.** A stall can have low delta and high unresolved residual pressure; FRANK must preserve that distinction.
2. **Trajectory beats isolated scalar classification for dynamic regimes.** Current FRANK lineage already summarizes a short state trajectory before producing an advisory loop decision.
3. **Readout quality is part of the evidence.** Estimator identity/version, uncertainty and freshness must gate convergence claims; stale or high-uncertainty readouts route fail-closed.
4. **Invalid telemetry is not merely high uncertainty.** NaN/Infinity, negative residual pressure, negative uncertainty and negative measurement age are invalid domain values and must not enter recurrence classification. H1 Quality Gate v0.2 now enforces this boundary.
5. **Decision provenance includes policy.** A recurrence result is not fully replayable from state/readout alone if controller thresholds can vary. v0.2 now binds policy/threshold identity separately from readout identity and then binds both into a receipt hash.
6. **State identity remains richer than a scalar epoch.** H-WP-02 already separates semantic-state, state-version/history and execution-trace identity. Future ordinary-spine fusion should test direct recurrence-receipt binding to those identities rather than create a duplicate lineage system.
7. **Adaptive recurrence remains an OPEN performance hypothesis.** ACT, PonderNet and 2026 recurrent-depth work justify adaptive compute as a serious candidate and document overthinking risk, but they do not validate FRANK's current thresholds or target 4B behavior.
8. **Authority remains separate.** Loop readouts/decisions are proposal/control evidence only. They do not grant external-effect authority or Harness mutation authority.
9. **Recurrence is not emergence by itself.** A stable/productive loop or adaptive stopping result does not establish causal emergence, global-workspace closure, or phenomenal consciousness.

## Linked knowledge packets

- `research_entity/knowledge_micro_packets/frank/KMP-FRANK-R10-LOOP-QUALITY-POLICY-RECEIPT-20260809.md`
- `research_entity/knowledge_micro_packets/frank/KMP-FRANK-R10-ADAPTIVE-RECURRENCE-HALTING-20260809.md`

## Linked executable delta

- `research_entity/harness/reference/loop_dynamics_quality_gate.py` v0.2
- `research_entity/harness/reference/test_loop_dynamics_quality_gate.py`
- implementation commit `312c532db49d570c4866b9015dc72d63d568291d`
- test commit `c8c2f7919f30b2060bc6f658bc3cd49269881703`

## Required next tests

- target-Ubuntu execution of the v0.2 gate and expanded regressions;
- frozen/live-derived Golden Trace materialization;
- H-WP-02 state-version/trace-root -> trajectory/readout receipt fusion;
- fixed-depth vs delta-only vs residual-aware vs typed quality-gated recurrence differential;
- threshold calibration by estimator/version/loop family where data supports it;
- stale/out-of-order/duplicate/cross-instance state message tests;
- lesion/rescue and causal-use checks before any GWT/emergence interpretation;
- confirm external-effect gateway remains independent under all recurrence outcomes.

## Negative/uncertain results preserved

- no target Ubuntu run in this worker surface;
- no live target 4B recurrence benchmark;
- no Golden Trace end-to-end H1 path;
- current threshold values remain engineering defaults;
- no claim of full RFC 8785/JCS implementation;
- no H1/FRANK release promotion.
