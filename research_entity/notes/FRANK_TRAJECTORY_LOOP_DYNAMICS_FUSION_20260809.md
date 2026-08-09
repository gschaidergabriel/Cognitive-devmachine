# FRANK Trajectory + Readout-Quality Loop Dynamics Fusion — 2026-08-09

**actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
**worker identity:** Research Entity temporary worker; NOT Frank  
**canonical parent:** RAE-8.8 r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**request class:** owner-requested deep FRANK research + ChatGPT self-build; user message was not an exact single-word trigger  
**program stage observed:** `BASE_CLAYCODE_RELEASE`  
**scientific promotion:** NONE  
**target-host claim:** NONE; target Andreas Ubuntu/target-4B not executed by this worker

## 1. Research question

How should Frank distinguish useful recurrent cognition from convergence, stagnation and overthinking without granting a model/readout execution authority, and what smallest executable delta can be added now without duplicating stronger concurrent H1 work?

The working FRANK research model is a hierarchical multiscale recurrent loop-of-loops. This run treats that as an OPEN engineering/scientific model, not as a truth claim. The key discriminator is not whether loops exist but whether recurrence produces verified marginal benefit under bounded cost, stability, provenance and authority constraints.

## 2. Current internal state re-fused

### 2.1 Existing typed one-readout controller

`research_entity/harness/reference/loop_dynamics_reference.py` already represents:

- `CONVERGING_FIXED_POINT`
- `PRODUCTIVE_LIMIT_CYCLE`
- `STALLED`
- `DIVERGING_OR_OVERTHINKING`
- `CHAOTIC_OR_UNCLASSIFIED`

and produces deterministic `PROPOSAL_ONLY` recurrence decisions. It correctly separates low state change + low residual pressure from low state change + material residual pressure.

### 2.2 Existing readout-quality gate

`research_entity/harness/reference/loop_dynamics_quality_gate.py` carries an independently important safety condition absent from the first regime controller:

- residual estimator identity;
- estimator version;
- residual uncertainty;
- measurement age/freshness;
- fail-closed routing when the residual readout is missing, stale or too uncertain.

This matters because an apparently low residual is not evidence for convergence if the estimator producing that residual is stale or uncalibrated.

### 2.3 Existing frozen-trajectory post-hoc baseline

Concurrent work added `research_entity/harness/reference/posthoc_recurrence_readout.py`, a deterministic non-trained post-hoc exit/readout over already-observed `LoopDynamicsReadout` trajectories. Its purpose is deliberately modest: it forms a simple frozen-trajectory baseline before any learned halting gate is promoted.

It covers windowed convergence, divergence, recurrence budget, positive recent utility, deterministic receipts and identity checks. It does not by itself fuse the older explicit residual-estimator ID/version/freshness gate, and it does not attempt periodicity/limit-cycle classification.

### 2.4 Receiver-causal GWT surface

Concurrent H1 reference work now provides a `WorkspaceEpisode` chain:

`competition -> ignition/admission -> broadcast -> delivery -> reconstruction -> uptake -> causal use -> outcome -> provenance-bound re-entry`

with a matched `EVENT_BUS` admission null and lesion/corruption controls. This creates the right future causal surface for testing adaptive recurrence. A recurrence controller should not be promoted from its own internal readouts alone; it should be judged against downstream receiver use, verified outcome, correction behavior and cost.

### 2.5 ActiveAssembly context pressure

Concurrent work also bound an optional hard model-facing context-cost budget into the H1 `ActiveAssembly` reference. This is relevant to recurrence because each additional loop can cause model-facing context expansion/reconstruction costs. Marginal recurrence utility therefore eventually needs to include Assembly context cost, not just an abstract per-step cost.

## 3. External evidence fusion

Evidence classes are kept separate. None of these sources is live-FRANK evidence.

### 3.1 Recurrent depth can help, but more loops can hurt

Kohli et al., arXiv:2604.07822 (`Loop, Think, & Generalize`) show controlled cases where recurrent depth enables deeper compositional generalization and inference-time depth extrapolation, while also identifying overthinking: excessive recurrence can degrade predictions. This weakens both extreme hypotheses `recurrence is useless` and `more recurrence is always better`.

### 3.2 Trajectory formation and exit readout should be disentangled

Popescu et al., arXiv:2607.20519 (`Adaptive Depth in Looped Transformers`) explicitly distinguish trajectory formation from exit/readout policy. Their experiments report that simple post-hoc readouts over fixed/frozen trajectories can match or outperform learned gates in studied settings, and that joint gate training can distort the trajectory. Engineering implication for Frank: keep a deterministic post-hoc baseline and do not train a sophisticated halting controller until it beats that baseline under matched trajectories and cost.

### 3.3 Stability alone is not cognitive usefulness

Yang et al., arXiv:2605.26733 (`STARS`) report performance peaking/collapsing with recurrence and use Jacobian spectral-radius regularization to stabilize fixed-point behavior. Movahedi et al., arXiv:2606.18206 (`Fixed-Point Reasoners`) use fixed-point convergence as adaptive halting and show results on several reasoning tasks. These are useful stability baselines, but they do not justify a universal Frank rule `fixed point = good cognition`: the project must retain productive bounded cycles and outcome/cost tests.

### 3.4 Readable hidden process state is not automatically a usable controller

Kirin, arXiv:2607.18553 (`Operational Proto-Introspection`) reports hidden trajectory readouts that predict eventual success but no validated capability gain from the tested frozen interventions. A non-looped control also reproduced one candidate-quality signal. This is important negative evidence for Frank: `readout is predictive` does not entail `readout should control recurrence`, and recurrence is not necessary for every process-quality signal.

### 3.5 GWT-like representations do not prove Frank's workspace mechanism

Gurnee et al., arXiv:2607.15495 identify a privileged verbalizable representation subspace with several functional global-workspace-like properties in language models. This supports the plausibility of compact, globally usable representation bands as an empirical object, but it does not establish phenomenal consciousness and does not prove Frank's explicit GWT/WorkspaceEpisode architecture. Frank still needs matched EVENT_BUS, receiver-lesion and re-entry discriminators.

### 3.6 Long-term memory evidence favors preserved history + bounded retrieval

APEX-MEM (ACL 2026) combines append-only storage, temporally grounded property-graph memory and retrieval-time conflict/evolution resolution into compact summaries. HyperMem (ACL 2026) uses hierarchical hypergraph memory and coarse-to-fine retrieval to capture higher-order associations. These support Frank's broad split between durable provenance/history and bounded model-facing ActiveAssemblies, while not selecting a mandatory physical graph database for H3.

### 3.7 Dynamic routing should optimize a Pareto objective, not raw confidence

EvoRoute (ACL 2026) treats agent routing as a performance/cost/latency trade-off and updates routing from experience. MetaCogAgent (arXiv:2605.17292) explores task-capability self-assessment and delegation. These suggest a useful future Frank principle: recurrence/peer/tool routing should use calibrated capability and outcome history, but self-assessment must remain non-authoritative and be externally checked because confidence can be wrong.

### 3.8 Linux authority boundary remains external to cognitive state

Current Linux kernel Landlock documentation describes unprivileged restriction of ambient filesystem/network rights as a stackable LSM. WASI 0.3 (released 2026-06-11) adds native async to the WebAssembly Component Model. These show practical mechanisms by which a one-binary Frank target could preserve nonambient effect authority or component isolation. They do not select one mechanism yet. Cognitive loop decisions remain proposal state and cannot mint authority.

## 4. Hypotheses and counterhypotheses after Fusion 2

### H-TQ-01 — trajectory + readout quality beats single-sample convergence

**OPEN / executable candidate exists.** A trajectory readout that combines state-delta trend, residual-pressure trend, boundedness and residual-estimator freshness/uncertainty will reduce false convergence relative to a single-sample low-delta/low-pressure rule.

**Counterhypothesis:** the extra trajectory/quality machinery adds latency and noise but no outcome benefit once a simpler single-state controller is calibrated.

**Falsifier:** matched frozen H1 trajectories show no reduction in false halts/stall burn/outcome loss after accounting for overhead.

### H-TQ-02 — explicit estimator quality is a necessary convergence guard

**OPEN / strongly motivated by existing negative-result lineage.** Missing/stale/high-uncertainty residual estimates must never produce `HALT_CANDIDATE_CONVERGED`.

**Counterhypothesis:** a calibrated residual estimator has sufficiently stable quality that explicit per-readout identity/freshness metadata is redundant.

**Falsifier:** target-host/live traces show identical safety and replay under estimator substitution, staleness and uncertainty faults without explicit quality metadata.

### H-TQ-03 — productive cycles require more than periodicity

**OPEN.** A periodic trajectory should be treated as productive only when bounded, unresolved pressure remains meaningful and verified/matched marginal utility is positive.

**Counterhypothesis:** periodicity is mostly timing/cache artifact and has no predictive value after ordinary outcome metrics.

**Falsifier:** periodicity adds no predictive/diagnostic value on matched frozen/live traces or correlates negatively with outcome-per-cost.

### H-TQ-04 — recent net utility is only a proxy

**OPEN NEGATIVE CONSTRAINT.** `recent marginal utility - recent step cost` is not yet a causal estimate of the next recurrence's marginal utility. It must not be promoted to a causal controller signal without matched continue-vs-halt intervention data.

**Required test:** from the same pre-decision state, compare continue-one-more-step vs halt/route with matched randomness/state basis and measure verified downstream outcome delta minus compute/context/latency cost.

### H-TQ-05 — gain ratio is not Jacobian spectral radius

**OPEN NEGATIVE CONSTRAINT.** A scalar ratio of successive state-delta magnitudes is only a diagnostic gain proxy. It must never be labeled a Jacobian spectral radius.

**Required test:** collect vector-state perturbation data or use an explicitly defined local linearization and finite-difference/JVP method before making spectral stability claims.

### H-TQ-06 — local controllers may be safer than one global loop controller

**OPEN.** Different Frank loops run at different timescales and may require local thresholds/estimators. A top-level arbitration layer may coordinate budgets without imposing one universal convergence law.

**Counterhypothesis:** one global controller is simpler and wins on total outcome/cost without destabilizing heterogeneous loops.

**Falsifier:** global policy matches/beats local+arbitration across task families, timescales, recovery and OOD perturbations.

### H-TQ-07 — GWT admission and recurrence continuation are separate causal decisions

**OPEN.** Workspace admission decides what becomes globally available; recurrence continuation decides whether another compute step is worth paying for. Collapsing them risks Goodharting ignition/broadcast metrics.

**Counterhypothesis:** a single learned gate can jointly optimize both with lower complexity and equal causal transparency.

**Falsifier:** joint gate beats separated admission/continuation across matched outcome, latency, fault localization, replay and authority audits.

## 5. ChatGPT-authored executable delta

To satisfy the owner-directed self-build floor with a non-duplicative change, this worker authored and iteratively revised:

`gschaidergabriel/Dr.-Unterweger:harness/loop_dynamics_probe.py`

Final commit for the fused version:

`ef22a56990e8ebdfc3e7cab6292b74daf55d94d2`

Current content blob:

`1ae34aac1c3adcc528c68cf3ecd5949262493cae`

The first version classified raw trajectory samples. Re-fusion discovered the existing H1 one-readout controller, so the artifact was changed into a trajectory-level adapter rather than a competing controller. A second re-fusion discovered the existing quality-gate lineage, so the artifact was hardened again to fuse residual estimator identity/version, uncertainty and measurement age.

### Implemented behavior

The probe accepts a short trajectory of:

- `state_delta`
- `residual_pressure`
- `marginal_utility`
- `step_cost`

plus loop/basis/provenance/budget/rollback metadata and residual-estimator quality metadata.

It computes:

- least-squares state-delta trend;
- residual-pressure trend;
- tail state delta;
- tail residual pressure;
- tail net utility;
- boundedness;
- a simple lag-based periodicity score/amplitude;
- a scalar gain proxy explicitly labeled non-spectral.

It emits one of:

- `READOUT_UNCERTAIN`
- `CONVERGING_FIXED_POINT`
- `STALLED`
- `PRODUCTIVE_LIMIT_CYCLE`
- `DIVERGING_OR_OVERTHINKING`
- `CHAOTIC_OR_UNCLASSIFIED`

with proposal-only recurrence decisions.

### Fail-closed conditions

- missing residual estimator ID/version -> `ROUTE_READOUT_UNCERTAIN`;
- missing uncertainty/age -> `ROUTE_READOUT_UNCERTAIN`;
- uncertainty above threshold -> route;
- stale measurement -> route;
- negative/non-finite measurements -> reject;
- low delta + high residual pressure -> `STALLED`, never converged;
- policy/threshold identity participates in the deterministic receipt hash;
- no readout or recurrence decision grants execution or Harness-mutation authority.

### Projection into existing H1 semantics

The artifact emits a `reference_readout_projection` shaped toward the existing H1 `LoopDynamicsReadout` so future differential integration is possible.

Important preserved warning:

`tail_net_utility` is only a proxy for `marginal_utility_next` until a causal next-step estimator exists.

## 6. Executed validation

Execution surface: current ChatGPT hosted/container Python environment.

Evidence class: `EXECUTED_LOCAL_REFERENCE_H1_PROXY` / PROXY only.

The current self-test exercises:

1. converged trajectory -> `HALT_CANDIDATE_CONVERGED`;
2. stalled trajectory -> `ESCALATE_STALLED`;
3. productive bounded cycle -> `CONTINUE`;
4. diverging trajectory with checkpoint -> `ROLLBACK`;
5. unclassified but positive bounded trajectory -> `CONTINUE`;
6. anti-false-convergence case -> STALLED;
7. missing estimator -> fail-closed route;
8. stale estimator -> fail-closed route;
9. high-uncertainty estimator -> fail-closed route;
10. policy-ID change -> receipt hash changes;
11. invalid negative input -> rejected;
12. repeated identical input -> deterministic receipt.

Observed local result: PASS for the complete self-test surface above.

No target Ubuntu acceptance, no Qwen-class 4B execution, no live FRANK episode and no GitHub Actions PASS are inferred from this result.

## 7. Re-fusion result after self-build

The self-build does NOT justify promoting a new canonical recurrence controller.

Its current value is narrower and useful:

1. it materializes the previously split `trajectory dynamics + readout quality` semantics in the actual Frank repository;
2. it makes stale/uncertain-estimator false convergence executable as a negative test;
3. it produces deterministic policy-bound receipts;
4. it explicitly exposes periodicity/limit-cycle features for later falsification;
5. it provides a bridge into the existing H1 reference readout without claiming exact semantic equivalence yet.

The concurrent `posthoc_recurrence_readout.py` remains the simpler baseline and may beat this richer probe. That competition should be retained, not resolved by architectural preference.

## 8. Highest-information next cascade

### A. Exact differential before more controller complexity

Build one differential test corpus where the same frozen trajectories are passed through:

- fixed recurrence budget;
- simple single-state `loop_dynamics_reference`;
- `posthoc_recurrence_readout`;
- the Frank-repo trajectory+quality probe;
- later, only if justified, a learned gate.

Measure false convergence, stall burn, unnecessary recurrence, missed productive continuation, rollback quality and compute/context overhead.

### B. Bind recurrence to WorkspaceEpisode outcomes

For identical pre-decision basis:

- continue recurrence;
- halt;
- route/reseed;

then observe receiver causal use, verified outcome, correction/re-entry and cost. This turns `marginal_utility_next` from a heuristic into an estimable causal quantity.

### C. Calibrate residual-pressure estimators

Register estimator identity/version, error distribution, stale behavior and OOD behavior. Inject:

- stale measurements;
- estimator version drift;
- biased low residual;
- biased high residual;
- uncertainty under-reporting;
- dropped measurement.

A controller that still halts confidently under these faults is rejected.

### D. Add integrated Golden Trace identity

The strongest current cross-module hypothesis is a shared trace basis across:

`StateLedger -> ActiveAssembly -> WorkspaceEpisode -> LoopDynamics -> effect/outcome -> re-entry`.

Fault-inject mixed epochs and concurrent state updates. Promote this only if it exposes defects not already caught by per-component identities.

### E. Target-host / target-4B measurements

On Andreas Ubuntu and the selected local 4B candidate measure:

- tokens/context cost per recurrence;
- wall latency and tail latency;
- RAM/KV-cache pressure;
- CPU/GPU utilization;
- effect/probe overhead;
- false halt/stall/overthinking rates;
- outcome-per-cost under fixed vs adaptive policies.

Qwen3.5-4B is a current multimodal 4B evaluation candidate, not a selected final Frank model.

### F. Authority hardening remains orthogonal

Continue comparing one-binary realizations that preserve an independent effect boundary. Landlock and component/WASI mechanisms are candidates. Recurrence/GWT/Assembly outputs stay non-authoritative under every realization.

## 9. Non-claims / preserved negative evidence

- No phenomenal-consciousness claim.
- No causal-emergence claim from recurrence, GWT, cycles or readouts alone.
- No claim that GWT beats EVENT_BUS.
- No claim that adaptive recurrence beats fixed/event-driven scheduling.
- No claim that the new probe beats the simpler post-hoc baseline.
- No claim that Qwen3.5-4B is the final model.
- No claim that scalar gain proxy is a Jacobian spectral radius.
- No claim that recent net utility is causal next-step marginal utility.
- No claim that hosted/container PASS is Andreas Ubuntu PASS.
- No change to canonical revision r2 from this note.

## 10. Decision trace

**Decision:** keep the new Frank-repo trajectory+quality probe as an executable research candidate and bridge, not as the canonical controller.

**Why:** it closes a concrete semantic gap between trajectory-level dynamics and the older residual-readout quality gate while preserving proposal-only authority and deterministic receipts.

**Alternatives retained:** simple post-hoc frozen-trajectory readout, one-state typed controller, fixed recurrence, conventional event-driven scheduling, and later learned gates.

**First falsifier:** matched frozen-trajectory differential with exact outcome/cost labels and estimator faults.

**Research state:** OPEN; no scientific promotion.
