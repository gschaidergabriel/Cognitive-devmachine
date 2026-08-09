# SPAWN FINAL REPORT — GWT Adaptive Recurrence / Compute Routing

Run: `spawn_20260809T1743p0700_gwt_adaptive_recurrence`  
Origin branch: `gwt`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Evidence status: **OPEN — SYNTHETIC PROXY SUPPORTED, NOT LIVE FRANK EVIDENCE**

## 1. Spawn selection

Canonical weighted distribution was used:

- claycode 50%
- harness 10%
- frank 10%
- gwt 6%
- emergenz 6%
- hyperposition 5%
- claygraph 5%
- unifieddb 4%
- clayresearch 4%

OS CSPRNG branch draw: `74/100` -> **GWT**.  
Five evidence-grounded microdirections were generated. OS CSPRNG microdirection draw: `1/5` -> **GWT as an adaptive recurrent-compute admission/continuation router**.

The recent-10-spawn duplicate audit could not be proven exhaustive with the exposed GitHub connector because code search returned no indexed SPAWN_RECEIPT hits and `fetch_file` cannot enumerate the spawn directory. This limitation is preserved in `SPAWN_RECEIPT.json`; no duplicate-free claim is manufactured.

## 2. Research question

Can GWT ignition/focus participate in an adaptive recurrence controller that continues expensive loop processing only when another recurrence is expected to yield verified benefit exceeding compute/resource/instability cost, while correctly distinguishing:

- resolved convergence;
- productive bounded cycles;
- stagnation/stall;
- divergence/overthinking;
- unclassified dynamics?

Primary discriminating baseline: fixed recurrence budgets / conventional event-driven scheduling.

Critical project law retained:

`low state delta + high unresolved pressure = STALLED candidate, not convergence`

and

`recurrence != emergence`.

## 3. Internal evidence synthesis

Current project state already makes this a high-value GWT question:

1. `FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md` explicitly asks GWT to test ignition/focus as adaptive recurrent-compute admission/continuation routing and compare it to fixed budgets.
2. `GWT_EMERGENCE_READOUT_CONTRACT.md` requires typed causal receipts, re-entry linkage, counterfactual replay and cost shadows.
3. `RAE_GWT_MICROKERNEL.clay` currently contains selection/broadcast/receipt/re-entry, but not recurrence budget, halt reason, loop regime or marginal-value semantics.
4. `CLAYCODE_G9_FUSION_SPEC_V3.clay` already has generic record/rule machinery and a GWT tensor, so this run found no evidence that new core language semantics are required. The missing pieces can first be attempted as a typed library/schema contract.
5. `CLAYCODE_RELEASE_WORKSPACE.json` is in the compile/realize phase and requires an executable counterexample before semantic redesign.
6. `HARNESS_WORKSPACE.json` leaves GWT and ablation work open; H1 is the required later live executable discriminator on the Ubuntu target.

## 4. External evidence synthesis

External primary research supports the broad feasibility of adaptive computation, not the specific FRANK/GWT controller proposed here.

- Graves' Adaptive Computation Time demonstrated learned input-dependent numbers of recurrent computation steps.
- PonderNet formalized adaptive pondering with an explicit computation/accuracy trade-off.
- Mixture-of-Depths, CoTFormer and related variable-depth work provide additional evidence that useful computation demand can vary by input/token and that dynamic allocation can reduce aggregate compute in some settings.
- Looped/recurrent transformer work supports repeated depth as a mechanism for iterative computation.
- Important counterevidence/caveats remain: recent work reports shallow-halt traps for ACT-like routing and memory-versus-depth trade-offs; FlexiDepth reports that dynamic skipping need not translate into wall-clock speedup because routing/I/O overhead can dominate.

Therefore:

`adaptive compute is feasible`

but does **not** imply

`GWT focus is the correct FRANK recurrence controller`.

That causal linkage remains OPEN.

## 5. Executed synthetic proxy experiment

A deterministic-reference Python simulation was constructed and executed in the hosted Linux environment. It generated heterogeneous episode regimes and compared five policies across 20 matched seeds x 3000 episodes/seed = 60,000 episode draws per policy.

Policies:

- fixed4
- fixed8
- fixed12
- delta_only
- pressure_trend

Synthetic regimes:

- easy convergence 28%
- hard convergence 30%
- productive cycle 18%
- stalled 14%
- diverging 10%

### Aggregate result

| Policy | Success | Mean recurrence steps | Mean utility |
|---|---:|---:|---:|
| fixed4 | 27.84% | 4.000 | 0.3903 |
| fixed8 | 42.65% | 8.000 | 0.4130 |
| fixed12 | 60.66% | 12.000 | 0.3929 |
| delta_only | 45.92% | 5.810 | 0.4527 |
| pressure_trend | 60.67% | 6.346 | 0.5004 |

Within this authored synthetic generator, the pressure/trend controller:

- matched the fixed12 success rate to within about `+0.012 percentage points`;
- used about **47.1% fewer recurrence steps**;
- exceeded fixed12 on the test's cost-adjusted utility by about `+0.1075`;
- materially beat the delta-only controller on hard-converging and productive-cycle regimes.

This is **mechanism sanity-check evidence only**. The dynamics and thresholds were authored for the experiment. It cannot establish real FRANK performance, causal benefit of GWT focus, or a release decision.

## 6. Main mechanism finding

The strongest research delta is not a specific numeric threshold. It is the controller decomposition:

### Minimal candidate basis

A recurrence decision should combine at least:

1. unresolved pressure/error;
2. multi-step progress or expected marginal verified gain;
3. recurrence cost;
4. instability/overthinking cost;
5. remaining recurrence/probe budget;
6. typed regime classification;
7. episode/epoch/provenance-bound receipts.

GWT focus/ignition may be an input to this decision but must not be the decision itself.

A one-step low-delta halt rule is specifically challenged because it confuses:

- resolved contraction;
- stalled attractors;
- productive bounded cycles with locally flat/adverse steps.

## 7. ClayCode delta

Created candidate artifact:

`GWT_ADAPTIVE_RECURRENCE_CONTRACT.clay`

It introduces research-candidate library/schema types:

- `LoopRegime`
- `RecurrenceBudget`
- `LoopDynamicsReadout`
- `RecurrenceDecision`

and guards including:

- low delta + high pressure -> STALLED;
- productive-cycle regime must not halt from a single-step delta alone;
- CONTINUE requires material unresolved pressure plus expected marginal gain above recurrence + instability cost and remaining budget;
- GWT focus may inform but is not the recurrence decision;
- recurrence decision is proposal/control state, not effect authority;
- readout is not truth;
- recurrence is not emergence.

**No ClayCode core semantic change is proposed by this run.** BASE should first try to parse/canonicalize/type/effect/compile this contract with existing semantics. A real compiler failure is required before redesign.

## 8. Required H1 experiment

The next decisive experiment is a matched frozen-episode Ubuntu H1 test.

Compare:

- fixed recurrence budgets;
- conventional event-driven scheduler;
- typed pressure/trend adaptive router;
- focus-only router;
- typed-local versus one-global controller.

Required interventions:

- residual-pressure lesion;
- trend/patience lesion;
- GWT-focus lesion;
- shuffled GWT focus;
- truthful versus shuffled versus no re-entry;
- frozen-model-output architecture replay where meaningful.

Measure:

- task outcome;
- false halt;
- correction time;
- recurrence count;
- wall-clock latency;
- compute/memory;
- scheduler/routing overhead;
- instability/overthinking;
- recovery/rollback;
- receiver delivery/reconstruction/uptake/causal-use/outcome/re-entry traces.

This work was written into the dynamic-work event:

`WORK-SPAWN-GWT-ADAPTIVE-RECURRENCE-H1-01`

and is BLOCKED until the required BASE/H1 execution surfaces exist and current governance drift is resolved or explicitly handled.

## 9. Counterhypotheses retained

- H0-A: ordinary persistent event-driven scheduling is sufficient; recurrent-control/GWT math adds little.
- H0-B: GWT focus is correlated with difficulty but adds no incremental predictive/causal value beyond local pressure/controller state.
- H0-C: routing overhead erases theoretical recurrence-count savings on the Ubuntu runtime.
- H0-D: the synthetic advantage is an artifact of authored regime dynamics and thresholds.
- H0-E: adaptive routing collapses into shallow-halt equilibria on hard cases.
- H0-F: one global controller is sufficient despite heterogeneous loop timescales.

None is refuted by this run.

## 10. Cross-branch feedback

Written to all current registered scientific branches:

- GWT: NEW_HYPOTHESIS
- Frank: NEW_HYPOTHESIS
- Harness: NEW_CONSTRAINT
- ClayCode: NEW_CONSTRAINT
- Emergenz: NEW_CONSTRAINT
- Hyperposition: NEW_HYPOTHESIS
- ClayGraph: NEW_CONSTRAINT
- UnifiedDB: NEW_CONSTRAINT
- ClayResearch: NEW_CONSTRAINT

No claim promotion was performed.

## 11. Infrastructure / governance finding

The required interconnect preflight currently has a registry-alignment defect:

- current `RESEARCH_TRIGGER_REGISTRY.json` registers the integrated foundry branch as `clayresearch`;
- `tools/research_interconnect_preflight.py` still hardcodes legacy `clay` in its PRIORITY tables;
- the tool explicitly raises a fail-closed governance-drift error when its priority branch sets differ from the registry-derived set;
- `ROOM_REGISTRY.json` and some older mesh text likewise retain legacy `clay` room/trigger semantics.

Therefore this run does **not** claim that the canonical interconnect preflight executed successfully. Instead it materializes a manual current-mesh `INTERCONNECT_MANIFEST.json` with the blocker preserved.

This is an infrastructure counterexample, not scientific evidence about adaptive recurrence.

## 12. Final synthesis

Current best research position:

> **Adaptive recurrence is worth implementing as a typed, receipt-bound GWT/loop-control experiment, but not as a promoted FRANK mechanism yet.** The project should specifically avoid a low-delta-only or focus-only halt controller. A better candidate combines unresolved pressure, multi-step marginal gain, cost/instability shadows, budget and loop-regime identity. Existing ClayCode appears expressive enough to encode this without changing core semantics; the decisive next evidence must come from matched Ubuntu H1 replay/intervention tests.

The synthetic experiment establishes only that this controller shape can produce a favorable outcome/compute trade-off in a deliberately heterogeneous toy dynamical system. H1 must decide whether that survives real FRANK semantics and real runtime overhead.

## 13. Durable artifacts

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `GWT_ADAPTIVE_RECURRENCE_CONTRACT.clay`
- `simulation_reference.py`
- `SIMULATION_RECEIPT.json`
- this `FINAL_REPORT.md`
- dynamic work event `research_entity/state/work/events/work_create_spawn_gwt_adaptive_recurrence_20260809T1743p0700.json`

## 14. Negative results / limitations

- No live FRANK/H1 evidence was produced.
- No evidence yet shows GWT focus adds independent causal value to recurrence routing.
- No evidence yet shows recurrence-count savings become Ubuntu wall-clock savings.
- No evidence yet selects global versus typed-local controllers.
- The recent-10 spawn duplicate audit was not exhaustive with the connector surface.
- The mandatory interconnect preflight could not be validly claimed due current `clayresearch`/legacy-`clay` governance drift.
- Current GWT room materialization was absent at the documented paths during this run, so no same-room peer activity was inferred.

## 15. Promotion decision

`NO_PROMOTION`

Status remains:

`OPEN_SYNTHETIC_PROXY_SUPPORTED`

Next promotion-relevant gate:

`MATCHED_UBUNTU_H1_INTERVENTION_EVIDENCE`.
