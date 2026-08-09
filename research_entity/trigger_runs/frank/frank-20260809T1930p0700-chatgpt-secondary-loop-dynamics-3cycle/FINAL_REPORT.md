# FRANK loop-dynamics testing, state/log fusion, web research and repair — 3-cycle report

Run id: `frank-20260809T1930p0700-chatgpt-secondary-loop-dynamics-3cycle`  
Execution class: `SUBSTANTIAL_FRANK_RESEARCH_TASK_NOT_EXACT_TRIGGER`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Research subject: FRANK v0.1 / Andreas Ubuntu target  
Authority: Research Entity independently researched/tested/implemented a Frank Harness diagnostic change; Frank self-observation did not authorize the change.

## Input and evidence boundary

Repository state, recent commit history, FRANK loop-dynamics code, Research Entity reference semantics, Harness/Program state and current research directives were inspected. The live local `state/FRANK_UNIFIED.sqlite` on Andreas' machine is not present in the accessible repository, so this run did not inspect that live SQLite state. The newest loop probe initially had no associated GitHub Actions/workflow receipt. Local hosted execution therefore remains component/reference evidence, not target-Ubuntu release evidence.

## Cycle 1 — internal state/log/code fusion + tests

The current Frank trajectory probe correctly preserved `PROPOSAL_ONLY` authority and the critical distinction `low state_delta + high residual pressure = STALLED`, not convergence. Baseline fixtures distinguished convergence, stalled, productive cycle, divergence and unclassified trajectories.

Adversarial analysis exposed two material continuation hazards:

1. `tail_net_utility` was projected as `marginal_utility_next` while the code itself marked that value as a proxy. A historical tail proxy is not a validated causal estimate of the utility of the next recurrence.
2. The divergence classifier required both tracked slopes to grow materially in its main positive-utility path. Strong growth in only state delta or only residual pressure could remain `CHAOTIC_OR_UNCLASSIFIED` and still receive `CONTINUE` from positive historical proxy utility.

A fixed-seed synthetic stress run over 100,000 trajectories found 17,280 concern cases under the predicate: unclassified + material growth on at least one tracked axis + `CONTINUE` based on positive history-only proxy utility. This count is a diagnostic stress result, not a real-world incidence estimate.

Additional input-validation gap: non-finite threshold values (`NaN`, `Inf`) were not rejected although sample values were finite-checked.

## Cycle 2 — external research + hypotheses

Primary external research used:

- Popescu et al. (2026), arXiv:2607.20519, *Adaptive Depth in Looped Transformers: Diagnosing Learned Halting Gates and Trajectory Readouts* — supports explicitly separating trajectory formation from exit/readout evaluation and reports strong simple post-hoc trajectory readouts.
- Kohli et al. (2026), arXiv:2604.07822, *Loop, Think, & Generalize: Implicit Reasoning in Recurrent-Depth Transformers* — supports useful recurrent depth while also documenting degradation/overthinking under excessive recurrence.
- Graves (2016), arXiv:1603.08983, *Adaptive Computation Time for Recurrent Neural Networks* — establishes task-dependent adaptive recurrent computation as a viable control family.

These sources support studying adaptive recurrence; they do not validate FRANK's specific thresholds or prove that any particular FRANK loop is causally useful.

### Hypotheses

- `H-FRANK-LOOP-01` OPEN: history-only tail net utility is insufficient evidence for continued recurrence in a STALLED state; continuation should require a validated next-step marginal-utility estimate or an external reseed/route decision.
- `H-FRANK-LOOP-02` OPEN: material worsening on one tracked axis is sufficient to fail closed from an UNCLASSIFIED state when the only continuation evidence is a history-only utility proxy; this does not itself prove the trajectory is globally divergent.
- `H-FRANK-LOOP-03` OPEN/SUPPORTED_IMPLEMENTATION_HINT: residual-readout identity, version, uncertainty and age should gate classification; missing/stale/high-uncertainty readouts should not emit convergence.
- `H-FRANK-LOOP-04` OPEN: trajectory generation, trajectory readout and effect authority should remain separate layers.
- `H-FRANK-LOOP-05` OPEN: detrended periodicity plus turning-point evidence should reduce monotone-trend aliases relative to raw lag similarity while preserving genuinely productive non-fixed-point recurrence.
- `H-FRANK-LOOP-06` OPEN: non-finite policy thresholds must be rejected to preserve deterministic policy/receipt integrity.

### Counterhypotheses

- `C0-1`: one-axis growth can be productive exploration; fail-closed routing may over-halt useful recurrence.
- `C0-2`: historical tail utility may become a sufficiently calibrated proxy for next-step utility in some loop families after empirical calibration.
- `C0-3`: readout-quality gating alone may eliminate most unsafe continuation cases, making additional single-axis routing unnecessary.
- `C0-4`: detrended/turning-point cycle detection may reject useful non-sinusoidal or transient metastable cycles.

## Cycle 3 — concurrent fusion + implementation

During the run, concurrent workers independently hardened the same probe with residual-readout quality gating and then trend-safe cycle detection using detrending/turning points. A stale write attempt was correctly rejected by GitHub CAS with HTTP 409. The file was re-read and the concurrent changes were preserved rather than overwritten.

The final fused Frank change is commit `a1f3604ee2f6075c316dfd6fb683c83b21547898`, semantic version `trajectory-probe-v1.4-proxy-safe`:

- preserves detrended/turning-point cycle detection;
- STALLED no longer continues solely from positive history-only utility proxy;
- UNCLASSIFIED + material growth on either tracked axis routes/reseeds rather than continuing solely from the proxy;
- bounded stable UNCLASSIFIED trajectories may still continue when the existing proxy case remains positive;
- rejects non-finite thresholds;
- binds the new policy choices into deterministic receipt identity;
- retains `PROPOSAL_ONLY` and explicit proxy warnings.

Hosted local regression execution passed the existing fixtures plus monotone-trend alias, stalled-positive-proxy, single-axis-growth, readout-quality, deterministic-policy-receipt, invalid-input and non-finite-threshold tests. Re-running the same 100,000-case diagnostic predicate under the hardened policy produced 0 concern cases. This does not establish outcome optimality; it only verifies the targeted continuation hazard is closed under that test predicate.

No GitHub workflow run was associated with the final Frank commit when checked. Target Ubuntu replay was not executed in this run. Therefore H1 release gate remains NOT_PASS and no scientific claim is promoted to CURRENT.

## Three-cycle fusion synthesis

The strongest cross-cycle result is not "loops are good" or "more recurrence is better". It is a control-boundary refinement:

`observed past utility != validated causal utility of the next recurrence`

and therefore:

`uncertain/worsening dynamics + history-only proxy -> route/reseed/fail closed`

while:

`bounded, measured recurrence + validated next-step value + material unresolved pressure -> candidate continuation`

This preserves productive limit cycles as a possible useful regime without turning recurrence itself into an objective.

## Cross-branch feedback

- `frank`: adopt proxy-vs-validated-next-step utility as an explicit semantic distinction; do not infer continuation authority from readout.
- `harness`: add frozen-episode differential replay for v1.3 trend-safe vs v1.4 proxy-safe vs fixed recurrence budgets; measure false-continue, false-route, correction time, task outcome, cost, rollback and recovery.
- `gwt`: treat ignition/continuation as adaptive compute routing hypotheses; test whether workspace signals predict useful recurrence depth rather than merely recurrence count.
- `emergenz`: preserve `recurrence != emergence`; loop stability is an observable/control variable, not an emergence score.
- `claycode`: represent utility evidence basis explicitly, e.g. `HISTORY_PROXY` vs `VALIDATED_NEXT_STEP_ESTIMATE`, plus estimator identity/quality/age and proposal-only decision receipts.
- `unifieddb`: persist estimator identity/version, uncertainty, measurement age, utility evidence basis, trajectory identity and eventual next-step outcome so calibration can be reconstructed.
- `claygraph`: represent readout/coupling/decision edges without turning a diagnostic projection into authority.
- `hyperposition`: route/reseed from ambiguous worsening states is a candidate place to test preservation/reopening of alternatives against stale-attractor escape.

## Highest-information next discriminator

On frozen real or accepted reference episodes, run matched replay across:

A. fixed recurrence budgets;  
B. pre-proxy-safety trend-safe policy;  
C. v1.4 proxy-safe policy;  
D. a policy using a genuinely calibrated next-step marginal-utility estimator.

Primary outcomes: task correctness/outcome, false continuation, false route/halt, recurrence count, latency/compute, correction time, rollback/recovery and calibration between history proxy and actually observed next-step benefit. Include one-axis-growth benign-exploration episodes specifically to falsify `H-FRANK-LOOP-02` if routing is too conservative.

## Claim-state decision

Research delta: COMMITTED as implementation evidence + OPEN hypotheses/counterhypotheses.  
Scientific promotion: NONE.  
Canonical revision bump: NONE.  
Target Ubuntu execution: NOT_EXECUTED.  
Target 4B execution: NOT_EXECUTED.  
H1 release gate: NOT_PASS.
