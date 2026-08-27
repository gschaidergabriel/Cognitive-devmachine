# FRANK Log/State Testing + Three-Cycle Research Fusion

**run_id:** `frank_20260809T1932p0700_chatgpt_secondary_log_state_3cycle`  
**task type:** user-directed substantial FRANK research; not an exact reserved trigger invocation  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**identity:** temporary Clay/Research-Entity worker; NOT FRANK  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**target:** Frank v0.1 on Andreas Ubuntu Linux developer system  
**scientific promotion:** NONE

## 1. Requested procedure and completion

Executed the requested sequence as three explicit cycles:

1. current FRANK logs/state/replay/runtime evidence -> Fusion 1 -> hypotheses/counterhypotheses -> external primary-source research -> Re-Fusion 1;
2. contradiction/discriminator analysis -> Fusion 2 -> targeted hypothesis -> external research -> executable improvement + regression tests -> Re-Fusion 2;
3. residual-readout/calibration analysis -> Fusion 3 -> hypothesis/counterhypothesis -> external research -> validation program -> whole-mesh feedback.

Durable outputs:

- `HYPOTHESES.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- this final report
- corrected `research_entity/harness/reference/loop_dynamics_quality_gate.py` v0.3
- extended `research_entity/harness/reference/test_loop_dynamics_quality_gate.py`

## 2. Evidence boundary: what was and was not available

### Available

- current Research Entity canonical/bootstrap/actor state;
- current FRANK loop-of-loops directive and H1 loop contracts;
- current `Dr.-Unterweger` repository runtime/state/replay implementation evidence and recent commits;
- prior complete repository integrity receipt;
- current FRANK trajectory loop probe;
- current H1 quality-gate implementation/tests;
- current program/workspace state;
- external primary research papers.

### Not available to this worker

- a live stream of Andreas Ubuntu host logs;
- direct access to the installed target-host `FRANK_UNIFIED.sqlite` / `FRANK_CLAYGRAPH.sqlite` contents;
- fresh target-host telemetry proving the installed machine currently runs the newest repository head;
- a newly observed CI receipt for the v0.3 patch at report time.

Therefore this run evaluates **repository-visible logs/receipts/state machinery and loop readout semantics**, not a live target-host episode. Target-host acceptance remains separately required.

## 3. Current state/log fusion before the three cycles

### State/replay spine

Current FRANK state work has moved toward repository-admitted history as canonical truth, UnifiedDB as low-latency materialization, and ClayGraph as rebuildable derived topology. Normal canonical opens no longer create/migrate production state, and materialization lineage is checked against repository head/state epoch.

A repository replay test reconstructs fresh v12 state by parsing/admitting every repository semantic transaction, checks SQLite integrity, verifies committed-transaction count and records the resulting epoch. This is strong repository-level replay evidence, but is not a target-host install receipt.

### Prior integrity evidence

The existing deep-repair receipt reports a complete repository CI gate covering compile, static state-boundary audit, transaction census/parsing, full replay into fresh UnifiedDB state, deep integrity regressions and session-skill/status tests. The same receipt explicitly marks the Andreas target-machine installation as not yet verified.

### Current recurrent diagnostic layer

`Dr.-Unterweger/harness/loop_dynamics_probe.py` already has useful fail-closed behavior:

- missing residual-estimator identity -> readout uncertain;
- excessive residual uncertainty -> readout uncertain;
- stale residual measurement -> readout uncertain;
- low delta + high pressure -> stalled, not converged;
- bounded periodic positive-utility recurrence -> candidate productive limit cycle;
- worsening/unbounded negative-utility trajectory -> diverging/overthinking;
- authority remains proposal-only.

This is directionally aligned with the FRANK loop-of-loops directive.

## 4. Cycle 1 — trajectory formation versus exit/readout

### Fusion 1

Internal architecture currently treats recurrence measurement/readout as a proposal-only diagnostic layer. That is desirable because it permits evaluating trajectories without granting the readout execution authority.

### H1

`FRANK-3C-H1-TRAJECTORY-READOUT-SEPARATION`:

FRANK should keep recurrent **trajectory formation** experimentally separable from the **exit/readout policy**, at least through H1/H2. Frozen trajectories should support post-hoc readout evaluation before any controller is allowed to alter the trajectory-generating process.

### Counterhypothesis

Current FRANK readouts are deterministic proposal-only code, not jointly trained neural halting gates. The trajectory/readout entanglement reported for learned neural gates may therefore not transfer materially to FRANK.

### External primary evidence

- Popescu et al., *Adaptive Depth in Looped Transformers: Diagnosing Learned Halting Gates and Trajectory Readouts*, arXiv:2607.20519 (2026): separates trajectory formation from exit readout and finds post-hoc readouts can be competitive while jointly trained gates can alter trajectory quality.
- Jeddi et al., *LoopFormer: Elastic-Depth Looped Transformers for Latent Reasoning via Shortcut Modulation*, arXiv:2602.11451 (2026): variable-length trajectories and budget-conditioned loop depth can retain useful representations across compute budgets.

### Re-Fusion 1

Do **not** transplant neural gate training mechanics into FRANK. Transfer only the discriminating experimental principle:

`trajectory generator != readout != execution authority`

Highest-information test:

- freeze matched episodes;
- compare fixed recurrence budget;
- post-hoc adaptive readout;
- deliberately controller-coupled recurrence;
- measure downstream task outcome, false halt, recurrence count, latency and trajectory divergence.

## 5. Cycle 2 — concrete false-convergence defect

### Contradiction found

The main H1 reference controller and the global loop directive require low state change **and** low residual pressure for candidate fixed-point convergence.

The younger H1 `loop_dynamics_quality_gate.py` v0.2 instead contained:

`residual_pressure < converged_residual -> HALT_CANDIDATE_CONVERGED`

without requiring the current state delta to be low in that branch.

Concrete counterexample before the fix:

- `state_delta_norm = 0.20`
- `residual_pressure = 0.03`
- valid/fresh/low-uncertainty estimator
- `low_delta_streak = 0`

v0.2 could label this `HALT_CANDIDATE_CONVERGED` even though the state is still materially changing.

This was a semantic contradiction, not merely a threshold preference.

### H2

`FRANK-3C-H2-CONVERGENCE-NEEDS-LOW-DELTA-AND-LOW-RESIDUAL`:

Fixed-point convergence requires both:

- persistent low state change;
- low unresolved residual pressure.

A generic low-error stop, if later useful, must have a different semantic label.

### External primary evidence

- Bai, Kolter & Koltun, *Deep Equilibrium Models*, arXiv:1909.01377: equilibrium modeling explicitly targets fixed points rather than simply low task/error signals.
- Bai, Koltun & Kolter, *Stabilizing Equilibrium Models by Jacobian Regularization*, arXiv:2106.14342: fixed-point convergence/stability is a dynamical property; Jacobian behavior is separately relevant to stable convergence.

These papers do not validate FRANK's thresholds. They support the narrower distinction between **state-dynamics convergence** and an unrelated low residual/error signal.

### Improvement implemented

H1 quality gate was updated from v0.2 to v0.3:

- convergence now requires `low_delta_streak >= 2`;
- `state_delta_norm < low_delta_epsilon`;
- `residual_pressure < converged_residual`;
- convergence reason renamed `low_delta_and_low_residual_with_valid_readout`;
- policy/schema/hash domains were version-bumped to v3 so receipt identity reflects changed semantics.

Two regression tests were added:

1. high-delta + low-residual cannot mint convergence;
2. one isolated low-delta frame cannot mint convergence.

### Test result

An in-session deterministic 7-case discriminator over the corrected decision semantics passed:

- stalled -> `ESCALATE_STALLED`;
- genuine low-delta/low-residual -> `HALT_CANDIDATE_CONVERGED`;
- high-delta/low-residual -> `CONTINUE`;
- single low-delta frame -> `CONTINUE`;
- noisy residual -> `ROUTE_READOUT_UNCERTAIN`;
- stale residual -> `ROUTE_READOUT_UNCERTAIN`;
- negative marginal utility in the defined band -> `HALT_MARGINAL`.

All inspected decisions retained `authority=NONE` / no effect eligibility.

A concurrent GitHub update briefly caused a CAS conflict while writing the test file. The stale write was rejected; the file was reread and the update retried against current content. This is an implementation-process receipt, not scientific evidence.

### Re-Fusion 2

The corrected rule is now coherent with the FRANK global directive and H1 reference controller:

`low delta + low residual => candidate convergence`

`low delta + high residual => stalled`

`high delta + low residual => not fixed-point convergence`

No claim is made that a fixed-point regime is always cognitively optimal; productive bounded cycles remain valid candidate regimes.

## 6. Cycle 3 — residual estimator calibration

### Fusion 3

Current H1/FRANK readouts track estimator identity/version, uncertainty and measurement age. This is much safer than raw scalar pressure. But these metadata are still mostly **self-description of the estimator** unless calibrated against future outcomes.

### H3

`FRANK-3C-H3-RESIDUAL-ESTIMATOR-CALIBRATION`:

Before any recurrence controller is promoted, residual readout quality should be evaluated by **empirical false-halt/regret calibration** across loop families, regimes and OOD episodes.

### Counterhypothesis

For proposal-only H1 diagnostics, explicit calibration may be premature. Identity/freshness/uncertainty guards may be sufficient until enough replay data exists.

### External primary evidence

- Xie et al., *Statistical Early Stopping for Reasoning Models*, arXiv:2602.13935 (2026): uncertainty-aware sequential stopping can explicitly control premature stopping risk, including finite-sample guarantees in one method.
- Wu et al., *Thought calibration: Efficient and confident test-time scaling*, arXiv:2505.18404 (2025): hidden-state probes can identify reasoning plateaus and reduce unnecessary compute while preserving performance in reported experiments.
- Farzaneh & Simeone, *Think Short, Defer Smart, Act, and Repeat*, arXiv:2607.26865 (2026): calibrated convergence/deferral mechanisms are evaluated on end-to-end episode trajectories with explicit reward/deferral guarantees.

These are analogical/technical transfer sources, not validation of FRANK's residual estimator.

### Re-Fusion 3 — executable validation design

Add a **shadow calibration benchmark**, not execution authority:

For each frozen/live episode and every recurrence step, persist:

- loop family / timescale / state epoch;
- `state_delta_norm`;
- residual estimate;
- residual uncertainty;
- estimator id/version;
- measurement age;
- recurrence budget/count;
- eventual task resolution/outcome;
- oracle/fixed-budget outcome where available;
- truthful / shuffled / no-reentry intervention identity.

Measure:

- false `HALT_CANDIDATE_CONVERGED` rate;
- false-stall/false-route rate;
- outcome regret against fixed-budget/oracle baselines;
- compute/latency saved;
- empirical coverage/calibration of estimator uncertainty;
- OOD degradation;
- per-loop-family differences.

Promotion criterion should be outcome/cost based, not a single universal scalar.

## 7. Whole-mesh feedback

Persisted `BRANCH_FEEDBACK_MANIFEST.json` routes the run delta to:

- `clayresearch`
- `frank`
- `gwt`
- `emergenz`
- `claycode`
- `hyperposition`
- `claygraph`
- `unifieddb`
- `harness`

Core shared laws returned to the mesh:

1. `trajectory != readout != authority`;
2. `low residual != fixed-point convergence`;
3. `readout metadata != empirical calibration`;
4. `recurrence stability != emergence`;
5. H2 must reproduce corrected H1 semantics before H3 physical consolidation;
6. target-host receipts remain necessary before claiming installed/runtime success.

## 8. Negative results and non-promotions

Preserved negative results:

- low residual alone cannot support the fixed-point convergence label;
- repository/CI replay integrity cannot substitute for Andreas-host installation/runtime acceptance.

Not promoted:

- no canonical r3;
- no H1/H2/H3 PASS;
- no ClayCode BASE PASS;
- no recurrence controller selection;
- no claim that all FRANK live logs/states were observed;
- no target-host acceptance;
- no emergence or consciousness claim.

## 9. Highest-information next experiment

After BASE allows H1 target execution, run one matched Ubuntu replay battery with at least these arms:

A. genuine convergence;  
B. high-delta + low-residual;  
C. low-delta + high-residual;  
D. transient low-delta then renewed motion;  
E. bounded productive cycle;  
F. diverging/overthinking;  
G. noisy residual estimator;  
H. stale residual estimator;  
I. truthful re-entry;  
J. shuffled re-entry;  
K. no re-entry.

For each arm compare fixed budget versus proposal-only post-hoc adaptive stop and record false halt, outcome, recurrence count, latency, compute, rollback/recovery and estimator calibration.

## 10. Final synthesis

The three-cycle run did not merely add another recurrence hypothesis. It found and repaired a current H1 semantic inconsistency that could falsely label an actively changing loop as converged, then transformed that fix into a broader measurement requirement:

**FRANK should stop recurrence based on typed, provenance-bound, empirically calibrated loop evidence—not on a single low scalar—and fixed-point convergence must remain distinct from generic low-error stopping.**

The improvement is intentionally narrow: no new organ, database, daemon or language syntax. It tightens a decision contract, makes receipt identity version-aware, adds adversarial regression cases and defines the next discriminating Ubuntu experiment.
