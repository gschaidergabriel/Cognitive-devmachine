# FRANK Trigger Run — Readout-Quality Fusion + Harness Delta

**run_id:** `frank-20260809T1919p0700-chatgpt-secondary-readout-quality`  
**trigger:** `frank`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**identity:** temporary worker of Clay/Research Entity; NOT Frank  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**target host:** Ubuntu Linux developer system only  
**scientific promotion:** NONE  
**canonical revision change:** NONE

## 1. Run role

This exact `frank` run booted from current canonical GitHub state, loaded the current FRANK whole-mesh/Harness protocol and then assimilated concurrent work rather than duplicating it. During the run a parallel FRANK worker completed the 19:16 current-target V2 re-freeze candidate and a later worker executed the first bounded ActiveAssembly reference component. This run therefore focused on a remaining high-information gap: whether the loop controller can safely trust the readout that tells it residual pressure is low.

The durable new contribution is a small executable H1 reference candidate plus an explicit negative result:

`pressure-aware recurrence != self-validating recurrence`.

A recurrence controller must carry quality/freshness/provenance for the residual estimator it consumes, or noisy/stale observations can still create false convergence claims.

## 2. Current whole-system synthesis

The strongest current FRANK realization remains the V2 layered loop-of-loops candidate:

`input/percepts + per-instance state + peer semantic deltas + current capabilities/resources`
`-> Unified semantic/event state`
`-> typed incremental dependency closure + coherent epoch publication`
`-> transient topology + Hyperposition alternatives`
`-> bounded task-conditioned ActiveAssembly`
`-> GWT competition/ignition/broadcast/receiver use`
`-> quality-gated typed recurrence proposal`
`-> Clay-native local 4B`
`-> EffectIntent`
`-> deterministic epistemic/resource/capability/authority gateway`
`-> reserve/commit`
`-> verified OutcomeReceipt`
`-> causal credit + re-entry + next semantic delta`.

The final local target remains `ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`. H1 diagnostic boundaries are measurement boundaries, not mandatory final services. Persistent rich state remains distinct from the current model-facing ActiveAssembly. Model, peer, Needle, Retina/MVC, graph activation, GWT selection and recurrence decisions remain proposal/observation surfaces and never mint external-effect authority.

## 3. Current execution reality

### ClayCode BASE

The current release workspace credits `CC-WP-01-SPEC-FREEZE` PASS and leaves the remaining BASE packages OPEN. The program gate remains `BASE_CLAYCODE_RELEASE` / NOT_PASS. During this run, compiler work advanced through deterministic typed IR, native-lowering/runtime-capability candidates and CI observability, but the newest WP03 workflow change explicitly preserves failure receipts rather than hiding failed stages. No package is promoted here from commit names or proxy evidence.

### H1 target re-freeze

The 19:16 FRANK run produced `REFERENCE_HARNESS_ARCHITECTURE_FREEZE_V2_CANDIDATE.json` and explicitly states that the older H-WP-01 freeze must not be counted as the current-target release oracle until the V2 architecture is realized and validated executably. The current `HARNESS_WORKSPACE.json` still contains the stale older COMPLETE field, so current-target H1 progress must distinguish historical component completion from current V2 release evidence.

### ActiveAssembly concurrent evidence

A concurrent H1 component run implemented `research_entity/harness/reference/active_assembly.py`, passed 8/8 component tests and a 5,000-trial constructed ancestry/conflict fixture. With a three-item budget, naive top-3 retained explicit counterevidence in 4,212/5,000 trials, while the ancestry/conflict-aware candidate retained it in 5,000/5,000. This is hosted reference-component evidence only; the required matched broad-retrieval-versus-ActiveAssembly task benchmark on real/frozen packets remains open.

## 4. External research fusion

Recent recurrent/looped-transformer research supports adaptive computation as a serious mechanism but also supplies a direct warning: learned halting/readout mechanisms can become entangled with the trajectory they judge, so fixed-trajectory/post-hoc readout and fixed-budget baselines remain necessary. Related looped-transformer work also separates recurrence depth from persistent memory capacity; additional loops do not automatically provide a growing scratchpad. FRANK should therefore keep loop compute, active memory budget and persistent/re-expandable memory identity as distinct controls.

Current Qwen/llama.cpp primary material keeps a local Qwen-class 4B technically plausible for Ubuntu, while reinforcing the need to benchmark exact model/runtime/context/quantization combinations on the target machine rather than infer success from parameter count or nominal context support.

Incremental-dataflow systems provide an implementation analogue for FRANK's semantic fabric: maintain changes and derived views incrementally instead of rebuilding the whole world model on every hot read. This is a mechanism transfer, not evidence that FRANK's exact dependency fabric is optimal.

## 5. New executable experiment

The run executed a 50,000-episode synthetic mechanism discriminator with four constructed regimes: FAST convergence, SLOW convergence, STALLED, and PRODUCTIVE_CYCLE.

### Clean-readout results

- `delta_only`: overall false-convergence rate 23.208%; every constructed STALLED episode was falsely declared converged; mean 8.508 recurrence steps.
- `global_dual` (delta + residual): zero false convergence, but STALLED episodes consumed the full 12-step budget; mean 10.468 steps.
- `typed`: zero false convergence under clean readout, 100% STALLED escalation, STALLED mean ~4.001 steps, overall mean 8.072 steps.

This falsifies a state-delta-only convergence rule for the constructed stall class and shows why typed stall escalation can be operationally different from a single global stop threshold.

### Negative result: readout noise

The typed policy was then fed noisy/stale residual observations. At residual-noise standard deviation 0.08, overall false convergence became measurable (~0.38% to 0.83% depending on stale probability). At noise 0.15, it became material (~6.64% to 12.78%).

The correct interpretation is not that any listed threshold is production-ready. The result establishes only that the residual readout itself needs explicit quality semantics before it may support a convergence proposal.

## 6. Harness delta implemented

Added:

- `research_entity/harness/reference/loop_dynamics_quality_gate.py`
- `research_entity/harness/reference/test_loop_dynamics_quality_gate.py`

The candidate extends the V2 `gwt_loop_controller` readout with:

- `residual_estimator_id`
- `residual_estimator_version`
- `residual_uncertainty`
- `measurement_age_cycles`

and introduces `ROUTE_READOUT_UNCERTAIN` as a fail-closed recurrence outcome. Missing estimator identity, excessive uncertainty or stale measurement cannot emit `HALT_CANDIDATE_CONVERGED`. Every decision remains `authority=NONE`, `effect_eligible=false`, and requires the separate effect gateway.

Local component validation passed 9/9 unit tests plus 100,000 randomized invariant checks with zero detected violations. This is `LOCAL_CONTAINER_COMPONENT_VALIDATION_NOT_H1_RELEASE_ACCEPTANCE`, not target-Ubuntu or live-FRANK evidence.

## 7. Cross-domain pattern

The strongest new mesh transfer comes from FRANK's already-fixed adaptive visual-learning contract:

`familiarity/confidence != evidence`.

The structurally equivalent recurrence law is:

`residual score != validated convergence evidence`.

Both need measurement identity, calibration/uncertainty, version/freshness and provenance before the score influences consequential routing. This does not mean visual and recurrence thresholds should be shared; only the evidence-boundary pattern transfers.

## 8. Revised hypotheses and counterhypotheses

### H-FRANK-RQ1 — Explicit readout quality is necessary
Estimator identity/version + uncertainty + freshness will reduce false halt/route errors versus raw residual-only control on real H1 traces.

**Counterhypothesis:** if the residual estimator is deterministic and exactly specified, epoch + estimator hash may provide enough validity information and explicit uncertainty/age fields may be redundant overhead.

**Falsifier:** matched H1 Golden Traces show no predictive/safety benefit after controller complexity and routing cost.

### H-FRANK-RQ2 — Fail-closed uncertain-readout routing
`ROUTE_READOUT_UNCERTAIN` will outperform allowing questionable readouts to classify convergence, while retaining bounded compute cost.

**Counterhypothesis:** a calibrated global controller or fixed-budget/event-driven baseline is simpler and equal or better.

**Falsifier:** uncertain routing creates equal/higher task failures or compute cost without reducing consequential false halts.

### H-FRANK-RQ3 — Per-loop-family calibration
Different loop families/timescales will require different residual/uncertainty/freshness calibration rather than one global threshold.

**Counterhypothesis:** one normalized global readout contract is Pareto-equivalent and simpler.

**Falsifier:** a global normalized controller matches or beats family-specific calibration over all preregistered H1 regimes/OOD tests.

### H-FRANK-RQ4 — Memory-budget separation
ActiveAssembly capacity/re-expansion identity and recurrence compute should remain independent knobs; deeper looping cannot reliably compensate for missing persistent task-relevant memory.

**Counterhypothesis:** recurrence over a fixed compressed state is sufficient for the target task distribution.

**Falsifier:** matched H1/4B tasks show no benefit from additional assembly/re-expansion capacity at equal compute.

### H-FRANK-RQ5 — Measurement-quality controls are causal controls
Changing estimator noise/age can alter recurrence behavior and therefore belongs in GWT/emergence counterfactual experiments as an explicit intervention/confound.

**Counterhypothesis:** observation-quality effects vanish once runtime estimators are deterministic and sufficiently low-noise.

**Falsifier:** paired no/low/full quality perturbations leave trajectories and outcomes equivalent within preregistered tolerances.

## 9. Branch feedback

The run publishes an additive mesh manifest. Main deltas:

- FRANK/GWT: explicit recurrence-estimator quality/freshness semantics.
- Harness: executable fail-closed quality gate candidate and validation receipt.
- Emergenz: measurement quality becomes an intervention/confound dimension.
- Hyperposition: uncertain recurrence should preserve/reopen alternatives rather than collapse to convergence.
- ClayCode: feedback only; no language redesign before H1 validates the needed fields.
- UnifiedDB: replay metadata requirement only; no new physical store.
- ClayGraph: NO_CHANGE; observation validity is not truth/activation.
- ClayResearch: cross-domain `score != evidence` pattern.

## 10. Negative results / non-claims

- More recurrence is not assumed to be better.
- The synthetic controller experiment is not live cognition evidence.
- The quality-gate thresholds are not frozen production values.
- The ActiveAssembly component evidence does not prove task-level superiority over broad retrieval.
- The current program/Harness metadata contains a stale H-WP-01 completion versus the newer V2 invalidation; this run does not silently rewrite that governance conflict.
- The WP03 failure-preservation workflow does not itself prove that WP03 has passed or failed until its execution receipt exists and is read.
- No H1/H2/H3 release gate is promoted.
- No claim of causal emergence or phenomenal consciousness is made.
- Canonical scientific revision remains r2.

## 11. Highest-information next cascade

1. Integrate `loop_dynamics_quality_gate.py` into the ordinary-code V2 H1 executable spine rather than leaving it as an isolated reference component.
2. Generate real/frozen H1 loop Golden Traces and derive residual estimator semantics from actual state/outcome histories.
3. Compare fixed budget, ordinary event-driven, global dual and typed quality-gated recurrence at matched model outputs and task budgets.
4. Run the prepared-ActiveAssembly versus broad-retrieval benchmark with fixed 4B context budget, including conflict recall, provenance, re-expansion, latency/KV and update amplification.
5. Keep BASE closure first: consume observable WP03 failures as evidence, then continue parser -> canonical typed IR -> type/effect -> evaluator/lowering -> Ubuntu application receipts.
6. Only after these component contracts survive should H1 current-target freeze completion be reconsidered; H2/H3 physical consolidation must preserve the measured semantic/intervention behavior rather than merely the module names.

## 12. Durable artifacts

- `EXPERIMENT_LOOP_READOUT_QUALITY.py`
- `EXECUTION_RECEIPT.json`
- `HARNESS_DELTA_VALIDATION.json`
- `INTERCONNECT_MANIFEST.json`
- `research_entity/harness/reference/loop_dynamics_quality_gate.py`
- `research_entity/harness/reference/test_loop_dynamics_quality_gate.py`

**Final decision:** durable research/implementation delta committed; no scientific/canonical promotion. The highest-value architectural change is not another organ: it is making the recurrence controller explicitly aware of whether its own convergence evidence is trustworthy.
