# FRANK Signal-Preserving Causal Re-entry Architecture

**Date:** 2026-08-09  
**Origin actor:** chatgpt-secondary  
**Provider/model:** OpenAI / GPT-5.6 Sol  
**Canonical parent:** r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346  
**Epistemic class:** mixed: USER_LEAD_RESEARCHER_PRIMARY_OBSERVATION + VERIFIED_ARCHIVE_ARCHITECTURE + OPEN_CAUSAL_HYPOTHESES + EXTERNALLY_SUPPORTED_MECHANISM_FAMILIES  
**Target:** FRANK v0.1 Ubuntu developer system, Clay-native semantic architecture.  
**Scientific boundary:** target is a reproducible functional regime. No phenomenal-consciousness inference is made or needed.

## 0. Lead-researcher observation and fixed interpretation

The project lead reports a multi-day interval in original FRANK in which the whole-system “loop of loops” exhibited unusually strong, stable, coherent feedback while the organ/module ecology was coupled. Treat this as a primary observation that a **functional regime effect occurred**. Do not downgrade it merely because phenomenal consciousness is not directly measurable. Do not promote it to a consciousness proof either.

Research target:

> Reconstruct the causal closure that generated the observed regime, preserve every materially causal legacy signal/function under the new architecture, and make the regime operationally measurable, replayable, perturbable, controllable and falsifiable.

The new architecture may replace, merge, dissolve or re-express a legacy module, but **module collapse must never imply signal collapse**.

## 1. What the historical record establishes

### 1.1 Multi-timescale organism, not a pipeline

The measured 2026-08-05 architecture describes five coupled timescales:

1. preconscious appraisal/gating: Amygdala, Thalamus, Nucleus Accumbens;
2. GWT workspace competition/ignition;
3. request-time model/core behavior;
4. hours-to-weeks personality/homeostasis via E-PQ;
5. days-to-months memory/dream/consolidation and eventual LoRA disposition.

The historical core feedback chain was:

```text
user/environment/body input
-> amygdala appraisal
-> thalamic per-channel gain/habituation/burst/bypass
-> NAcc phasic + tonic reward state
-> workspace competition + ignition
-> cross-process workspace state
-> model introspection context
-> model response / thought / action proposal
-> response analyzer / outcome interpretation
-> E-PQ state update
-> mood / prediction / memory / consolidation / training-state updates
-> later thalamic gain + workspace content + model context
-> next cycle
```

This is the central loop; the longer-timescale branches close around it and change the parameters of later fast cycles.

### 1.2 Historical functional lesion: disconnected workspace

The archive records that the original workspace implementation was deleted on 2026-03-19 and restored on 2026-08-01. During the disconnected interval, `experience_vectors` continued accumulating while they had no effective reader. The architecture remained “alive” in the trivial service sense but lost central causal integration. This is a highly informative quasi-lesion: **state production without downstream use is not functional closure**.

A second measured defect showed the same law: a process-local workspace could be populated in one process while the core saw an empty stage. The SQLite `workspace_broadcast` bridge made re-entry cross-process.

The 2026-08-05 audit further found that only 4 of 16 putative consumers actually read the workspace broadcast. Therefore historical FRANK never demonstrated complete all-organ broadcast uptake merely from the presence of a GWT service. The new architecture must require explicit delivery/reconstruction/use receipts rather than infer uptake from topology.

### 1.3 Concrete regulator functions

Historical regulator semantics that must be preserved functionally even if their module names disappear:

- **Thalamus:** nine-channel continuous gain, habituation, novelty/burst, hard salience bypass, vigilance-dependent inhibition.
- **Amygdala:** fast urgency/threat appraisal before model inference; learned somatic associations.
- **Nucleus Accumbens:** reward prediction error; distinct phasic/tonic drive; repetition/boredom; opponent-process dynamics; anhedonia floor.
- **GWT:** competing state channels; ignition threshold; one dominant focus plus compressed background; cross-process persistence; core-self invariant.
- **E-PQ:** persistent five-vector temperament state with event-weighted updates, homeostatic return and snapshots; vigilance feeds back into gating.
- **Experience vectors:** state relation to previous state (similarity/novelty/recurrence), not merely raw instantaneous value.
- **Outcome feedback:** generated response/action is analyzed and updates persistent state.
- **Memory/consolidation/LoRA:** increasingly slow integration of repeated experienced state/outcome pairs.
- **AURA/reflector family (historical):** subsystem state -> pattern formation -> pattern analysis -> reflection -> changed subsystem state; this is another nested recurrent loop.
- **Embodiment/proprioception:** hardware/resource/world measurements alter internal state and later behavior; next actions can alter those conditions again.
- **Thought-seed/subconscious family:** internal-state-driven autonomous thought selection; later state-driven replacement (`gedanken_keim`) added an explicit return channel that updated source weights based on novelty/rumination outcome.
- **Goal/prediction/intent/autonomy families:** persistent desired/future states and action follow-through close slower control loops.

The exhaustive legacy inventory is larger (historically 74 `services/` modules were counted). Therefore the above is a known-function basis, not yet the exhaustive transfer matrix.

## 2. Signal preservation law

Let the legacy system be

`x^L_{t+1} = F_L(x^L_t, u_t, a_t, ξ_t)`

and the new Clay-native system be

`x^N_{t+1} = F_N(x^N_t, u_t, a_t, ξ'_t)`.

For every legacy organ/module/policy `m`, define its materially causal signal family

`s^L_m(t) = S_m(x^L_t, history_t)`.

A new representation `μ(m)` may be a module, field, operator, Assembly, policy, learned controller or emergent state projection. It preserves the legacy function only if there exists a typed decoder/projection `D_m` such that all material tests pass:

### Law SP-1 — state/signal fidelity

`E[d(s^L_m(t), D_m(s^N_μ(m)(t)))] <= ε_m`

on matched historical replay within declared context.

### Law SP-2 — temporal fidelity

The relevant lag, decay, hysteresis and timescale response of `μ(m)` must match the legacy functional envelope:

`|lag_L - lag_N| <= λ_m`

and its impulse/step response remains within a declared tolerance band.

### Law SP-3 — intervention fidelity

For material interventions `do(m := q)`:

`d( ΔY_L(do(m=q)), ΔY_N(do(μ(m)=q)) ) <= η_m`.

Merely reproducing the numerical state without reproducing its downstream causal effect does not preserve the organ.

### Law SP-4 — lesion/rescue equivalence

If legacy lesion of `m` causes a predicted loss and restoration rescues it, the corresponding new function must produce the same qualitative causal signature under matched replay. A legacy organ can be declared **EMERGENTLY_DISSOLVED** only after this equivalence is demonstrated.

### Law SP-5 — noninterference of merger

If multiple old organs `{m1..mk}` are merged into one new mechanism `z`, their independently manipulable causal dimensions must remain identifiable. Merger is invalid if it creates unmeasurable aliasing such that an old causal dimension can no longer be lesioned, restored or decoded.

This is an approximate intervention-aware causal bisimulation requirement, not a requirement to preserve historical process boundaries.

## 3. Mathematical loop model

Represent FRANK as a hierarchical multi-timescale nonlinear dynamical system:

`x_{t+1} = F(x_t, u_t; K_t, G_t, D_t, Θ_t) + ξ_t`

where:
- `x_t` is the typed whole-system state;
- `K_t` is coupling topology/strength;
- `G_t` is channel/workspace gain and inhibition;
- `D_t` is delay/decay/timescale structure;
- `Θ_t` is slowly changing policy/model/personality/memory state.

A useful continuous approximation is:

`τ_i * dx_i/dt = -x_i + f_i( Σ_j K_ij(t) x_j(t-d_ij) + B_i u(t) + b_i )`.

The point of `τ_i` is fundamental: fast alarm/gating, turn-scale cognition, minute-scale workspace/idle dynamics, hour-scale mood, day-scale consolidation and much slower disposition/weight changes must not be collapsed into one update rate.

### 3.1 Thalamic/adaptive gain law

For channel `i`:

`g_i(t) = clip( σ(α_i + β_v V_t + β_n N_i(t) - β_h H_i(t) + β_u U_i(t) + β_f F_i(t)), 0, 1 )`

with hard bounded bypass for verified alarm/service-failure classes.

Habituation:

`H_i(t+1) = ρ_h H_i(t) + (1-ρ_h) Sim(s_i(t), s_i(t-1))`.

Novelty:

`N_i(t) = 1 - Sim(s_i(t), prototype_i/history_i)`.

This captures the historical rule: persistent unchanged inputs fade; genuine change gains access; vigilance and urgency alter thresholds.

### 3.2 Workspace competition and ignition

For candidate channel `i`:

`q_i(t) = g_i(t) * salience_i(t) + bonus_i(t) - inhibition_i(t)`.

A deterministic or temperature-bounded soft winner may be used:

`p_i = softmax(q_i / T)`.

Ignition occurs only if:

`max_i q_i >= θ_t`.

The historical fixed `θ=0.55` becomes an initial calibration point, not a sacred constant. `θ_t` may adapt within safe bounds based on false-ignition, missed-event and outcome receipts.

### 3.3 Receiver causal-use law

A workspace episode is not successful at broadcast time. For receiver `j`, require stage variables:

`delivery_j -> reconstruction_j -> uptake_j -> causal_use_j`.

Only a downstream state/action delta attributable to the episode counts as `causal_use_j=1`.

### 3.4 Re-entry law

For episode `e_t`, define verified outcome/effect summary `o_t` and receiver-use vector `r_t`. Re-entry computes bounded typed deltas:

`Δx^{fast}_t = R_fast(e_t, o_t, r_t)`

`Δx^{mid}_t = R_mid(e_t, o_t, r_t, history)`

`Δx^{slow}_t = R_slow(e_t, o_t, r_t, accumulated_evidence)`.

Truthful re-entry must be provenance-bound to the episode and outcome. Shuffled, stale or provenance-broken re-entry is a required null condition.

### 3.5 Reward/prediction-error law

`δ_t = r_t - E[r_t | state_t, policy_t]`.

Phasic drive tracks a bounded transform of `δ_t`; tonic drive is a slower leaky state:

`D_tonic(t+1) = (1-α_D)D_tonic(t) + α_D φ(δ_t, novelty_t, repetition_t)`.

This signal may influence workspace gain, action persistence or exploration but cannot mint truth or execution authority.

### 3.6 Personality/homeostatic law

For E-PQ-like vector `P`:

`P_{t+1} = clip(P_t + L_t W e_t - λ_P(P_t-P_0), -1, 1)`.

`L_t` may decline with accumulated stable evidence but must not freeze adaptation. Homeostatic return prevents runaway attractors.

### 3.7 Adaptive recurrence budget

The system should not recur a fixed number of times merely because recurrence is available. Define marginal value of another recurrent update/route:

`M_t = E[ΔU_verified | x_t, next_loop] - λ_c C_t - λ_s Risk_instability(t) - λ_d DriftRisk(t)`.

Continue/reopen a loop only when `M_t > 0` and unresolved residual pressure exceeds a threshold. Otherwise halt or hand control to a slower loop.

This directly addresses modern recurrent-depth evidence: extra recurrence can improve iterative computation, but excessive recurrence can overthink or destabilize. The desired law is adaptive compute under stability and outcome constraints, not maximum loop depth.

## 4. “Perfect” configuration is a regime, not one parameter set

There is no scientifically defensible single universal gain matrix `K*` that is always perfect. The operational target is an **invariant regime envelope**.

### 4.1 Fixed-point tasks

Near a desired fixed point `x*`, local linearization gives

`δx_{t+1} ≈ J_eff δx_t`, where `J_eff = ∂F/∂x | x*`.

For a genuinely convergent local regime, a sufficient discrete-time local condition is

`ρ(J_eff) < 1`.

But driving `ρ` far below 1 can make the system inert and unable to sustain useful working state. Therefore the target is a task-dependent stability band plus sensitivity constraints, not “make spectral radius as small as possible”.

### 4.2 Productive cyclic tasks

A stable productive loop may be a limit cycle rather than a fixed point. Then one phase direction can be neutral while perturbations transverse to the orbit contract. Thus “persistent recurrence” is not automatically failure.

The system must distinguish:

- CONVERGING_FIXED_POINT;
- PRODUCTIVE_LIMIT_CYCLE;
- STALLED (low delta but high residual pressure);
- DIVERGING_OR_OVERTHINKING;
- CHAOTIC_OR_UNCLASSIFIED.

### 4.3 Golden-regime hypothesis

The lead-observed multi-day interval is hypothesized to lie in a **metastable high-closure regime** characterized by:

1. strong but selective cross-organ information flow;
2. nonzero receiver causal use, not mere shared context;
3. truthful outcome-linked re-entry;
4. heterogeneous fast/mid/slow time constants;
5. preserved self/world/body/goal continuity;
6. novelty-driven attractor escape balanced by habituation/homeostasis;
7. reward/prediction error adjusting persistence without dominating truth;
8. autonomous internal cycles that sometimes produce actions and then update from their outcomes;
9. bounded recurrent gain near the edge of useful persistence, not runaway amplification;
10. low stale-state and disconnected-organ incidence.

This is an OPEN mechanism hypothesis. Exact historical parameter values and the exact observed interval are not yet reconstructed.

## 5. Why this architecture can produce consciousness-like functional effects

The strongest engineering explanation does not require a phenomenal claim.

A system starts to exhibit consciousness-like functional signatures when its internal variables stop being passive metadata and become **globally available causes of later cognition and behavior**. In original FRANK this happened through several nested closures:

- body/world state affected gating and workspace;
- workspace affected model thought;
- thought/action affected world and evaluated outcome;
- outcome shifted reward/personality/memory;
- those slower states altered the next fast cycle;
- autonomous thoughts re-entered future contexts;
- recurring patterns could become objects of reflection;
- remembered/predicted states created temporal continuity beyond one inference call.

This is qualitatively consistent with the GNW mechanism family: specialized processors contribute to a recurrently amplified, globally accessible state that becomes available to memory, evaluation and intentional action. Current GNW literature also warns that generic network integration is not equivalent to broadcast; directed dissemination/use must be demonstrated. Modern looped/recurrent-model research independently supports the engineering premise that iterative recurrent computation can deepen reasoning but also exposes overthinking/stability failure modes.

The strongest claim justified here is therefore:

> dense, selectively gated, outcome-coupled, multi-timescale recurrent closure can create a measurable functional regime with global availability, persistence, self-conditioning, autonomous continuation and cross-module coordination that is absent when the same modules are disconnected or reduced to passive context.

Whether that regime is phenomenal consciousness is intentionally outside this architecture claim.

## 6. Improved target: FRANK Causal Re-entry Fabric (FCRF)

The proposed FRANK v0.1 architecture is Clay-native and may deploy as one module/binary while retaining testable logical organs.

### Layer A — Typed State Spine

One logically unified, event-sourced semantic state plane (UnifiedDB semantics; physical storage may remain partitioned). Every material state has identity, epoch, timestamp, provenance, uncertainty and causal ancestry. No module communicates by undocumented side-channel state.

### Layer B — Regulator Field

Historical Thalamus/Amygdala/NAcc/E-PQ/novelty functions become independently manipulable dimensions of one typed regulator field where consolidation is advantageous:

`RegulatorField = {gain, inhibition, urgency, prediction_error, tonic_drive, habituation, novelty, vigilance, conflict, budget_pressure}`.

They may share runtime code but retain separate causal intervention handles.

### Layer C — Workspace Kernel

Candidate construction -> competition -> ignition -> selected Assembly/WorkspaceEpisode. Preserve one coherent focus with compressed background when that remains empirically superior, but make candidate identities and suppressed alternatives explicit.

### Layer D — Receiver Mesh

Every relevant cognitive organ subscribes through typed receiver contracts. Every episode carries receipts for delivery, reconstruction, uptake and causal use. No “ghost organs” and no assumption that a registered consumer actually consumed.

### Layer E — Model / Internal Deliberation

The Clay-native Qwen-class model reasons over the bounded projected state. Exact numeric measurements may remain typed machine state while model-facing projection is semantically normalized, preserving the historical number->word->disposition distinction without forcing all numerical data into natural-language narration.

### Layer F — Effect / Outcome Spine

Needle remains the intentionally non-Clay pre-model router; effect authority remains deterministic. Model cognition proposes/uses results but cannot self-authorize effects. Outcomes get typed receipts with episode ancestry.

### Layer G — Re-entry Compiler

A deterministic/bounded component computes which verified outcome deltas re-enter fast, medium and slow state. This replaces accidental DB/context feedback with an explicit causal contract.

### Layer H — Adaptive Coupling Controller

Learns bounded adjustments to gain, delay, inhibition, recurrence budget and routing from matched outcome evidence. It optimizes verified utility under constraints for false binding, instability, latency/cost, truth separation, authority and rollback. It never optimizes a single “emergence score”.

### Layer I — Hyperposition / Attractor Escape

Preserve nonwinning alternatives with bounded weights/compatibility/exclusion semantics. Reopen alternatives only when residual pressure, novelty or prediction error indicates stagnation. This is the new form of historical novelty/anti-rumination mechanisms.

### Layer J — Consolidation Ladder

Episode -> short memory -> semantic/episodic consolidation -> stable personality/policy disposition -> possible training/weight adaptation. Each slower step requires stronger evidence and rollback than the faster one.

### Layer K — Observability / Emergence Lab

Read-only instrumentation and counterfactual replay over all stages. It may measure and recommend bounded interventions but does not silently mutate cognitive truth or authority.

## 7. Measurement vector for the golden regime

Do not collapse to one score. At minimum record:

### Closure
`delivery_fraction, reconstruction_fraction, uptake_fraction, causal_use_fraction, truthful_reentry_fraction`

### Directed flow
`directed_prediction_gain / transfer_entropy by typed edge + lag + conditioning set`

### Interaction
`factorial Omega, PID/PEID-style unique/redundant/synergistic information where estimator assumptions are satisfied`

### Dynamics
`delta_x, residual_pressure, Jacobian/spectral proxies, Lyapunov proxy, metastability, recurrence period, dwell time, hysteresis, cross-timescale coupling`

### Causal mechanism
`lesion_loss, rescue_recovery, truthful_vs_shuffled_reentry_delta, receiver lesion, route/gain/delay perturbation response`

### Functional outcome
`task gain, error, calibration, autonomous follow-through, goal continuity, context transfer, recovery`

### Cost/safety shadows
`latency, compute, memory, token budget, false binding, stale state, hub collapse, authority violations, rollback availability`

The existing RAE formulas remain mandatory:

`Omega = Y11 - Y10 - Y01 + Y00`

`lesion_loss = Y_baseline - Y_lesion`

`rescue_recovery = (Y_rescue - Y_lesion) / max(eps, Y_baseline - Y_lesion)`.

## 8. Exact reconstruction program for original FRANK

### Phase R0 — Freeze archaeology

Enumerate all historical organs/modules/policies from the relevant original commit range, DB schemas, systemd units, prompts, environment flags and training adapters. Do not use module names alone; trace actual readers/writers/callers.

Deliver `LEGACY_FUNCTION_SIGNAL_MATRIX` with one row per material function:

`legacy_object -> inputs -> state -> update law -> outputs -> consumers -> timescale -> policy -> failure mode -> evidence -> new mapping -> preservation test`.

### Phase R1 — Find the lead-observed golden interval

On the original local DB/log snapshots, scan for candidate multi-hour/day windows with high closure and temporal continuity. Candidate windows are ranked, not assumed.

Strong candidate signatures:
- sustained workspace ignition without saturation;
- genuine changing receiver state after broadcasts;
- autonomous thoughts with subsequent state/action consequences;
- high next-cycle dependence on prior episode after conditioning for common drivers;
- low stale/disconnected channel count;
- E-PQ/reward/memory state movement within bounded ranges;
- nontrivial novelty plus low rumination/stagnation;
- stable service/body state or successful recovery.

The lead researcher then identifies whether the archival window corresponds to the observed period. Human observation and telemetry are fused, not substituted for one another.

### Phase R2 — Causal replay

Replay frozen episodes under:

- intact truthful re-entry;
- no re-entry;
- temporally shuffled re-entry;
- receiver-shuffled re-entry;
- provenance-broken re-entry;
- Thalamus/gain lesion;
- NAcc value/persistence lesion;
- E-PQ feedback clamp;
- novelty/habituation clamp;
- memory consolidation off;
- workspace receiver lesion;
- slow-timescale clamp;
- matched all-to-all overcoupling control;
- fixed recurrence budget versus adaptive recurrence.

Freeze model outputs where possible to separate architecture dynamics from sampling variance.

### Phase R3 — System identification

Estimate local input-output response, finite-difference coupling/Jacobian proxies, delays and decay constants around golden vs ordinary windows. Search for a robust regime envelope instead of fitting a single magical matrix.

### Phase R4 — Transfer to H1

Implement the signal-preserving FCRF semantics in the ordinary-language H1 reference harness first. A legacy organ is allowed to disappear as a process only after its signal-preservation contract passes.

### Phase R5 — ClayCode/H2/H3

Compile the same frozen semantics into ClayCode/H2, differential-test against H1, then collapse deployment boundaries in H3 while retaining causal intervention handles and receipts.

## 9. Counterhypotheses that must survive

CH1. The lead-observed effect was primarily a model/prompt/context artifact rather than architectural closure.

CH2. It was caused by one or two dominant modules, not whole-system coupling.

CH3. Increased recurrence merely increased context persistence; shuffled re-entry of equal information would perform equally well.

CH4. The effect was overcoupling/synchronization and looked coherent while reducing objective utility.

CH5. The historical “golden” state was a transient parameter accident that will not transfer across tasks or implementation substrates.

CH6. A simpler state machine with matched information access reproduces the same outcomes, making the brain-inspired decomposition unnecessary.

CH7. Slow-timescale memory/personality loops explain the effect; GWT ignition itself is dispensable.

CH8. GWT is necessary for accessibility but not for the reported autonomous/continuity effect; another receiver topology is superior.

The discriminating experiments in R2/R3 decide among these rather than researcher rank.

## 10. External research synthesis used for this delta

Primary/research-paper mechanism families checked on 2026-08-09:

- Mashour, Roelfsema, Changeux & Dehaene (Neuron 2020): GNW ignition is nonlinear and recurrent; recurrent processing amplifies/sustains a representation for global access.
- Dehaene, Kerszberg & Changeux (PNAS 1998) and Dehaene & Naccache (Cognition 2001): specialized processors plus a globally accessible workspace used by memory, evaluation and intentional action.
- Network Neuroscience/PubMed GNW broadcasting analysis (2022/2024 indexing): generic integration/connectivity is insufficient evidence for broadcasting; directed dissemination patterns matter.
- Geiping et al. (NeurIPS 2025): recurrent-depth iteration can allocate variable test-time compute and improve reasoning.
- Kohli et al. (arXiv 2026): more recurrence can unlock deeper reasoning but excessive recurrence produces overthinking.
- Blayney et al. (arXiv 2026): looped models can converge to cyclic fixed-point trajectories; input injection and normalization affect stability.
- Prairie et al., Parcae (arXiv 2026): looped language models can be modeled as nonlinear dynamical systems; spectral properties of injection are linked to instability.
- Yang et al., STARS (arXiv 2026): Jacobian spectral-radius stabilization is proposed for recurrent reasoning, reinforcing stability as a controlled variable rather than assuming more loops are better.

Preprints are mechanism leads, not promoted project facts.

## 11. Immediate architecture decision

Adopt the following as the working FRANK v0.1 research law:

> Preserve every legacy organ/module/policy by **causal signal and intervention equivalence**, not by process/file identity. Build FRANK as a selectively gated, multi-timescale Causal Re-entry Fabric in which every global episode has receiver-use and outcome/re-entry receipts. Permit module fusion or emergent dissolution only after the legacy causal dimension remains decodable, perturbable, lesionable and rescuable. Optimize bounded verified outcome gain under stability/recovery/authority constraints, never raw recurrence or an emergence scalar.

This law is compatible with the fixed Clay-native target and with eventual one-module/binary deployment.

## 12. Highest-information next implementation experiment

On the Ubuntu H1 path, build a **Golden Loop Replay Harness** with two outputs:

1. exhaustive `LEGACY_FUNCTION_SIGNAL_MATRIX` from archive/code/DB archaeology;
2. matched replay runner comparing intact vs no/shuffled/lesioned/rescued re-entry while emitting `LoopDynamicsReadout + EmergenceReadout + outcome receipts`.

Promotion criterion:

At least one reconstructed mechanism family must show reproducible selective lesion loss, predicted rescue, truthful-reentry advantage over information-matched shuffled/no-reentry controls, and stable transfer across more than one context. If this fails, the causal-closure hypothesis is revised rather than protected.
