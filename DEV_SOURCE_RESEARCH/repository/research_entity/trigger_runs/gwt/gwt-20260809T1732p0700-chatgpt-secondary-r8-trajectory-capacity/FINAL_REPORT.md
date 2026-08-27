# GWT RESEARCH RUN — R8 · Trajectory-Capacity Recurrent Workspace Control

**run_id:** `gwt-20260809T1732p0700-chatgpt-secondary-r8-trajectory-capacity`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**parent GWT candidate:** `DG-RWC-R7 — Dual-Gate Recurrent Workspace Control`  
**new candidate:** **TC-RWC-R8 — Trajectory-Capacity Recurrent Workspace Control**  
**decision:** **OPEN / RESEARCH DELTA COMMITTED / NO CANONICAL SCIENTIFIC PROMOTION**

## Executive result

R7 separated workspace admission from recurrence continuation. R8 does not replace that result. It refines the continuation readout after fresh Harness, Frank and ClayCode evidence landed.

Main correction:

> **One first-order state-delta scalar is not a sufficient general representation of recurrent trajectory state, and required recurrence depth should be treated as conditional on available working-state capacity until tested.**

R8 therefore proposes that recurrence continuation consume four distinct evidence families:

1. `residual_pressure / unresolved_error`;
2. bounded **trajectory geometry** rather than only the latest state-step magnitude;
3. current **state-capacity context** such as workspace/scratchpad/receiver-memory capacity when measurable;
4. separate `semantic_state_hash`, `state_version_hash`, and `trace_root_hash` witnesses.

The retained causal chain is:

`candidate surface -> competition -> ADMIT -> delivery -> reconstruction -> uptake -> causal use -> outcome -> trajectory + residual pressure + capacity + cost/stability -> CONTINUE|HALT|ROUTE|ESCALATE|ROLLBACK -> provenance-bound re-entry`.

Hard boundaries remain:

`admission != continuation`

`global_addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`

`small_step != convergence`

`semantic_equivalence != version_equivalence != trace_equivalence`

`reentry != authority`

`recurrence != emergence`

## Why R8 was necessary

### Fresh Harness identity evidence

The post-R7 H-WP-02 merged oracle candidate separates:

- `semantic_state_hash` — history-independent current semantic state;
- `state_version_hash` — epoch/event-chain/version identity;
- `trace_root_hash` — execution-attempt/retry trace identity.

Local deterministic tests showed that the same final semantic state can have equal semantic hash while retaining a different version identity, and that exact replay can separately preserve semantic/version/trace roots.

GWT consequence: recurrence progress, freshness and recovery should not collapse these identities into one scalar or one hash. A retry may change trace identity without constituting semantic cognitive progress; a different causal/version history may matter even if a projected semantic snapshot is equal.

### Fresh Frank LoopDynamicsReadout surface

The concurrent Frank loop/base bridge already materialized `LoopDynamicsReadout` with `state_delta_norm`, `residual_pressure`, recurrence count/budget, coupling/Jacobian/convergence/oscillation proxies, marginal utility, stagnation/overthinking flags and a proposal-only `RecurrenceDecision`.

R8 therefore has an exact current semantic target: refine this readout rather than invent a parallel GWT controller.

### Fresh ClayCode control/effect closure

Concurrent ClayCode work independently reinforced:

`potential_effect_summary != runtime_effect_authority`

and, for recurrent execution:

`semantic/dependency lineage may continue; runtime effect authority does not automatically continue`.

R8 adopts that as an authority invariant. Trajectory/version continuity may inform recurrence, but no recurrent receipt carries effect permission forward implicitly.

## External research delta

Source classes are preserved. None of the following is live Frank/Qwen evidence.

### Recurrent trajectory geometry — preprint

Pappone, Crisostomi and Rodolà, `Two-Scale Latent Dynamics for Recurrent-Depth Transformers` (arXiv:2509.23314, 2025), report that recurrent loop updates become smaller and increasingly orthogonal and propose a second-order step-size early-exit criterion that outperforms their first-order and KL baselines on the tested models/tasks.

Transfer to R8: **test multi-step/second-order trajectory observables instead of assuming one small step means convergence.** This does not prove the optimal observable for Frank.

### Depth-state / memory trade-off — preprint

Sapunov, `Universal Transformers Need Memory: Depth-State Trade-offs in Adaptive Recursive Reasoning` (arXiv:2604.21999, 2026), reports a sharp learned-memory requirement in the tested Sudoku-Extreme Universal Transformer and a systematic trade-off between memory-token count and adaptive halt depth, including failure regimes at insufficient and excessive memory.

Transfer to R8: **recurrence depth may depend on available working-state capacity rather than task difficulty alone.** This remains architecture/task-specific until reproduced in the target system.

### Higher-order causality — preprint

Kořenek, Sanda and Hlinka, `Towards Definition of Higher Order Causality in Complex Systems` (arXiv:2409.08295), show why standard pairwise Granger/transfer-entropy style descriptions can fail for genuinely synergistic joint causes such as XOR and propose multivariate causal-set treatment.

Transfer to R8/GWT Emergenz: pairwise directed-flow readouts remain useful screening evidence but should carry estimator scope and should not be treated as complete higher-order causal structure.

### Biological GNWT adversarial test — peer-reviewed Nature

The Cogitate Consortium's preregistered adversarial study (Nature 2025, DOI `10.1038/s41586-025-08888-1`) challenges parts of preregistered GNWT and IIT predictions rather than delivering a simple winner.

Transfer retained from R7: artificial GWT should measure ignition/transition shape empirically instead of hard-coding one biological signature as a truth criterion.

### Artificial-workspace implementations — preprints

Bertin-Johannet et al. (arXiv:2602.08597) report robustness/generalization benefits from a learned attention selector in a multimodal global-workspace architecture. Gurnee et al. (arXiv:2607.15495) report a privileged verbalizable representation subspace in language models with several functional workspace-like properties.

Transfer: selection and possible nested model-internal/system-workspace structure are plausible test targets. Neither result establishes Frank's GWT architecture, emergence, or consciousness.

## Exact formal proxy — trajectory observability

`EXP-GWT-R8-TRAJECTORY-OBSERVABILITY-001` exhaustively enumerated every 3-step trajectory over the finite state set `{-2,-1,0,1,2}`: **125 trajectories**.

Coarse regimes were labeled `FIXED`, `TWO_CYCLE`, `CONVERGING`, `DIVERGING`, or `OTHER`.

Using only the final first-order step magnitude `|x2-x1|`:

- feature buckets: 5;
- ambiguous buckets: 5/5;
- trajectories lying in ambiguous buckets: **125/125**.

Using a small trajectory feature containing current step magnitude, previous step magnitude, direction/sign relation and second-order step change:

- feature buckets: 31;
- ambiguous buckets: 3;
- trajectories lying in ambiguous buckets: **14/125**.

This is a **representational counterexample**, not a cognitive-performance result. It proves only that a single final step magnitude cannot generally encode the recent trajectory regime even in a tiny deterministic system.

## TC-RWC-R8 semantic candidate

`GWT_R8_BASE_SEMANTIC_DELTA.json` proposes adding/refining the following observation-only fields around the current Frank `LoopDynamicsReadout`:

- `semantic_state_hash`;
- `state_version_hash`;
- `trace_root_hash`;
- `step_norm_current`;
- `step_norm_previous`;
- `second_order_step_delta`;
- `step_direction_relation`;
- bounded `trajectory_window_ref`;
- `state_capacity_profile` including workspace/scratchpad/receiver capacity and saturation when measurable;
- `flow_estimator_scope` = `PAIRWISE | CONDITIONED_MULTIVARIATE | HIGHER_ORDER | UNKNOWN`;
- exact estimator/version and basis identity.

These are **measurement semantics**, not execution authority.

## ClayCode BASE conclusion

R8 finds **no current executable reason for new GWT-specific surface syntax**.

The appropriate BASE action is:

`LoopDynamicsReadoutR8 + RecurrenceDecision -> existing G9 representation -> real parser -> canonical typed IR -> type/effect -> evaluator/lowering -> Ubuntu receipt`.

If this path compiles, R8 is a semantic contract only. If a concrete required field/intervention cannot be expressed, that counterexample returns to ClayCode.

R8 therefore follows the current program law: **less redesign, more compile**.

## H1 discriminator package

After BASE passes, preregister a matched-compute factorial replay using frozen model outputs where possible.

Controller factor:

1. fixed recurrence budget;
2. scalar state-delta/residual-pressure control;
3. R7 dual admission/continuation gate;
4. R8 dual gate + trajectory/capacity observables.

State-capacity factor:

- low;
- medium;
- high;
- saturation/dilution stress where technically meaningful.

Causal controls:

- truthful vs shuffled vs no re-entry;
- receiver lesion/rescue;
- graph route fixed/off;
- unrelated churn vs effect-critical dependency change;
- effect capability revoke/regrant;
- crash/restart/idempotent replay.

Primary outcomes:

- task correctness / verified outcome gain;
- false halt;
- overthinking / unnecessary recurrence;
- correction time;
- recurrence count;
- latency / compute / memory;
- receiver reconstruction/uptake/causal use;
- outcome/re-entry contribution;
- recovery correctness;
- OOD task/topology transfer.

A positive R8 result must outperform simpler controls **at matched cost**. Richer measurement alone is not success.

## Higher-order information-flow rule

R8 does not mandate expensive higher-order estimation on every episode.

Proposed staged policy:

1. pairwise/conditioned flow for cheap screening;
2. direct intervention/lesion/rescue as stronger causal evidence;
3. multivariate/higher-order estimator only when preregistered interaction structure, pairwise contradiction or XOR-like controls justify it;
4. preserve estimator scope/version and uncertainty in every receipt.

This avoids both pairwise overclaiming and estimator-cost inflation.

## Negative results / unresolved gates

- No official checkout execution of `tools/research_interconnect_preflight.py` on this hosted connector surface.
- The expected GWT room path returned 404, so no repo-native room pulse is claimed.
- No target Qwen-class 4B activation/intervention experiment was available.
- No Ubuntu developer-host execution was available.
- No H1 live Frank recurrence/controller differential was executed.
- The trajectory enumeration is only a finite toy formal proxy.
- The depth-state/memory result is one external architecture/task preprint, not a universal law.
- Higher-order causal estimators may be too costly/noisy to help operationally; that counterhypothesis remains open.
- No emergence or phenomenal-consciousness claim is promoted.

## Branch feedback

Explicit R8 feedback is materialized for all nine registered scientific branches in `BRANCH_FEEDBACK_MANIFEST.json`.

Most important routes:

- `frank`: refine the current LoopDynamicsReadout candidate; do not create a second controller;
- `claycode`: compile existing semantics first; no syntax churn by default;
- `harness`: execute the matched-compute R8 discriminator after BASE;
- `emergenz`: pairwise flow is scoped screening evidence, not full higher-order causal proof;
- `unifieddb`: persist semantic/version/trace identity layers and bounded trajectory/capacity basis;
- `claygraph` / `hyperposition`: expose topology/alternatives as causal context without truth promotion.

## Durable outputs

- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EXPERIMENT_TRAJECTORY_OBSERVABILITY.json`
- `GWT_R8_BASE_SEMANTIC_DELTA.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `research_entity/knowledge_micro_packets/gwt/KMP-GWT-R8-TRAJECTORY-CAPACITY-20260809.md`
- this `FINAL_REPORT.md`

## Decision

**TC-RWC-R8 = OPEN / TEST NEXT THROUGH BASE -> H1.**

R7 survives. R8 narrows the continuation problem from a scalar convergence heuristic to a provenance-bound trajectory-and-capacity measurement problem.

Highest-information next step for GWT is not more speculative architecture. It is to make `LoopDynamicsReadoutR8` compile deterministically in the current ClayCode path and, after BASE, falsify it against simpler controllers under matched H1 replay cost.
