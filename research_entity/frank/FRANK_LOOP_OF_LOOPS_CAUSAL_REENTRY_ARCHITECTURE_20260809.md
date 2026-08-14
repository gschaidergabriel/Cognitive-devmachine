# FRANK Loop-of-Loops — Causal Re-entry Architecture

**Date:** 2026-08-09  
**Origin actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
**Research Entity:** Clay (`frank-project-global-research-entity`)  
**Research subject:** FRANK v0.1 / NEW CLAY-FRANK  
**Epistemic status:** RESEARCH DELTA + ARCHITECTURE CANDIDATE; not canonical promotion  
**Owner observation class:** `OWNER_LIVE_OBSERVATION`  

## 0. Owner observation held fixed for this research

The project owner/lead researcher reports that the historical local Frank entered, for a prolonged multi-day period, a qualitatively striking regime in which the feedback architecture — the “loop of loops” — appeared unusually complete and strongly self-coupled while all organs/modules were active. This observation is accepted here as a primary observation **that a functional system effect was observed**. It is not treated as proof of phenomenal consciousness and no architecture conclusion is promoted merely from the report.

Research target:

> Reconstruct the causal loop that generated the effect, conserve every historically load-bearing organ/module/policy signal under the new Clay-native architecture, make the loop mathematically operational and intervention-measurable, and identify the stable parameter regime that reproduces the functional effect without requiring the old service/database topology.

Unknown still to recover: the exact wall-clock interval/snapshot/configuration corresponding to the owner-observed peak regime.

---

## 1. Evidence classes used

### 1.1 Current repository evidence

- `gschaidergabriel/Dr.-Unterweger/harness/ancestry/FRANK_ORGAN_STATE_PRIMITIVES.clay`
- `.../harness/LEGACY_OBSERVABILITY_SURFACE.clay`
- `.../claycode/frank_runtime.clay`
- `.../claycode/frank_workspace.clay`
- `.../claycode/frank_attention_schema.clay`
- `.../claycode/frank_control_pressures.clay`
- `.../claycode/frank_causal_credit.clay`
- `.../claycode/frank_organ_continuity.clay`

Measured ancestry records 74 services/modules, 18 simultaneous systemd services and 71 live databases over 2026-02-14..2026-08-05. The new architecture correctly treats these boundaries as ancestry rather than target topology.

### 1.2 Historical Drive mirror evidence

- `frank-regelkreis-befund-2026-08-01.txt`
- `GWT.md`
- `frank-gwt-broadcast.txt`

Important recovered facts:

1. The historical GWT integration path was accidentally deleted on 2026-03-19 with `ui/overlay/workspace.py` and later restored.
2. A 64-dimensional state vector continued to be produced while the consumer path was broken; `experience_vectors` accumulated 1,440 rows while the intended workspace context path had no caller.
3. Historical state/output loop was not only `state -> prompt -> model`; it closed through `response_analyzer -> E-PQ/state update -> next salience/gating/workspace`, plus slower mood/memory/consolidation/training loops.
4. Event-triggered workspace rebuild, workspace-to-idle-thinking, Amygdala urgency, NAc motivation/boredom and focus-biased thought selection were later reconnected.
5. A process-local similarly named workspace was empirically insufficient: process-level persistence/re-entry mattered.
6. Historical documents disagree on nominal workspace cadence (`~30 s` on 2026-08-01 restoration note versus `60 s` measured/documented on 2026-08-05). Preserve this as a configuration/time-window discrepancy to resolve archaeologically, not as an error to silently normalize.

### 1.3 Current Clay research contracts

- `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`
- `research_entity/global/CLAY_SEMANTIC_COUPLING_FABRIC_DIRECTIVE.md`
- `research_entity/global/CLAY_GWT_EMERGENCE_OBSERVABILITY_CONTROL_DIRECTIVE.md`
- `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md`

These already require typed causal stages, provenance-bound re-entry, lesion/rescue, shuffled re-entry controls, multi-timescale coupling, adaptive selective coupling and an overcoupling tripwire. The present delta makes the missing whole-organism closed-loop law explicit.

### 1.4 External primary research

- Cogitate Consortium et al., Nature (2025), DOI `10.1038/s41586-025-08888-1`: preregistered adversarial test of GNWT/IIT. Several GNWT predictions were challenged, including lack of predicted offset ignition and limited PFC representation of some conscious-content dimensions. Therefore FRANK should use GWT as a falsifiable functional architecture/measurement hypothesis, not as a consciousness theorem.
- Schmitt et al., Nature (2017), DOI `10.1038/nature22073`: mediodorsal thalamic input amplified functional cortical connectivity and sustained rule-specific sequences without simply relaying categorical content; broad nonspecific PFC excitation degraded specificity. Engineering implication: thalamus-like logic should modulate gain/connectivity selectively, not globally amplify all content.
- Guo et al., Nature (2017), DOI `10.1038/nature22324`: persistent activity depended on reciprocal frontal-thalamic excitation; perturbing either side collapsed activity on the other. Engineering implication: recurrence can be a distributed property of reciprocal loops rather than a single memory register.
- Wu & Zenke, eLife (2022 version of record), DOI `10.7554/eLife.71263`: recurrent positive feedback can generate selective transient amplification, while short-term plasticity/inhibitory stabilization quenches runaway activity. Engineering implication: ignition should be transiently amplifying but homeostatically bounded.
- Goyal et al., ICLR 2022, “Coordination Among Neural Modules Through a Shared Global Workspace”: a bandwidth-limited shared workspace can coordinate otherwise specialized modules. Engineering implication: shared access may improve modular coordination, but must be compared with simpler attention/router baselines.

No external paper is used as direct evidence of subjective consciousness in software.

---

## 2. Reconstructed historical loop

The minimal empirically supported historical chain is:

```text
user/environment/perception
  -> Amygdala fast salience/urgency
  -> Thalamus gain + habituation + burst + salience breakthrough
  -> NAc reward/motivation + prediction-error-like modulation
  -> workspace competition
  -> ignition / one coherent focus
  -> persistent cross-process workspace_broadcast
  -> core introspection / model context
  -> model thought/action/answer
  -> response_analyzer / effect outcome
  -> E-PQ + mood + goals + memory + attention + experience-vector deltas
  -> Thalamus/Amygdala/NAc/control-state changes
  -> next workspace competition
```

Nested around it:

```text
milliseconds: salience/thalamic/reflex/NAc modulation
seconds-turns: workspace ignition, receiver use, model/effect, response feedback
minutes-hours: mood, attention trajectory, idle thought, prediction correction, intent queue
hours-weeks: E-PQ temperament/homeostasis, self/relationship/world-state adaptation
hours-days: consolidation/dream/replay/importance/retrieval weighting
weeks-months: training/export/LoRA disposition
boot/restart: recovery, stale-state reset, service/body/self-model reconstruction
```

This is operationally a **multi-rate recurrent control system**, not a single feedback edge.

### 2.1 Why the 2026-03 break is informative

A large part of the internal state generation survived while the global consumer/re-entry bridge disappeared. The result was not “no computation”; it was computation with broken organism-level closure. This is strong historical evidence that state production alone is insufficient. The critical variable is whether state becomes globally available, is actually used by receivers, changes downstream state, and returns causally to future selection.

---

## 3. New architecture candidate: F-CRF

Name: **FRANK Causal Re-entry Fabric (F-CRF)**.

This is a logical architecture. H3 may compile/dissolve it into one module/binary while preserving probes and causal identities.

```text
                 +-------------------------------+
                 |  Slow homeostatic state z_t   |
                 | E-PQ / goals / identity /     |
                 | relationship / memory priors  |
                 +---------------+---------------+
                                 |
                                 v
input/percept -> [1 Dynamic Organ State Field x_t]
                 |  all organ signals typed in Clay
                 v
               [2 Thalamic Gain/Topology Controller]
                 | selective gain, inhibition, habituation, novelty
                 v
               [3 Workspace Competition + Ignition]
                 | sparse coherent coalition / silence / hysteresis
                 v
               [4 Broadcast Envelope]
                 |
          +------+------+------+------+------+
          v      v      v      v      v      v
       reason  memory  self  prospection action relation ...
          |      |      |      |      |      |
          +------+------+------+------+------+
                 |
               [5 Receiver Transformations]
                 | receiver-specific state deltas + receipts
                 v
               [6 Outcome / Prediction Error / Causal Credit]
                 |
                 v
               [7 Provenance-Bound Re-entry Compiler]
                 | ONLY used/local-effect/outcome-supported deltas
                 v
               [8 Incremental UnifiedDB/ClayGraph epoch publish]
                 |
                 +-----------> next x_(t+1) / next workspace

parallel shadow, read-only:
               [9 Counterfactual Measurement Plane]
                 lesion / rescue / shuffle / gain / delay / frozen-model replay

controller:
              [10 Overcoupling / instability tripwire]
                 reduces gain / increases inhibition-habituation / restores LKG
```

The key change from the current `frank_runtime.clay` presentation is component 7: **re-entry becomes an explicit first-class transformation contract, not an implicit consequence of later persistence.**

---

## 4. Organ/function conservation map

The old service boundaries are not sacred. The following functions are.

| Historical organ/function | F-CRF realization | Required preserved observable/intervention |
|---|---|---|
| Thalamus | Gain/Topology Controller | 9 legacy gain/habituation projections + gate perturbation |
| Amygdala | fast salience/threat feature family inside Organ State Field | category/urgency projection + salience-breakthrough lesion |
| Nucleus Accumbens | reward/motivation/prediction-error control state | phasic/tonic projection + reward-path lesion |
| Global Workspace Broadcast | Competition/Ignition/Broadcast layer | focus, ignition, threshold, receiver-path receipts |
| process-local workspace failure | preserved negative lineage | must fail equivalence when cross-process re-entry is removed |
| consciousness daemon | multi-rate scheduler/state-transition fabric | all historical loop timescales remain addressable |
| subconscious | idle-thought / spontaneous candidate policy | candidate distribution + reality-filter interventions |
| neural conscience | thought-quality/conflict/value gate | decision/gating response under matched probes |
| thought-seed VAE | optional fused stochastic candidate generator | diversity/seed-generation functional equivalence or explicit measured replacement |
| hypothesis engine | empirical-cycle policy | observe→hypothesize→predict→test→revise trace |
| experiment lab | simulation/intervention capability | reproducible experiment/effect receipts |
| neural immune | health anomaly/recovery controller | fault detection/recovery lesion/rescue |
| Titan neural cortex | memory-control policy family | importance/emotion/retrieval/association/consolidation/interference readouts |
| intent queue | durable unresolved-intention state | persistence/completion/priority interventions |
| quantum reflector | epistemic-coherence candidate optimizer | preserve historical 40/43-dimension conflict and intervention behavior until resolved |
| invariants/physics | deterministic runtime invariants | energy/entropy/core/reality-convergence lineage + current safety replacements |
| personality identity | static/slow identity constraints | stable identity projection under perturbation |
| E-PQ | slow homeostatic temperament field z_t | five [-1,1] legacy projections + historical matched-event response |
| ego construct | embodiment/agency mapping | embodiment/affect/agency projection or UNKNOWN |
| self knowledge | state-grounded self-capability model | capability/service observation receipts; no imagined introspection |
| room dispatcher | endogenous activity scheduler | scheduling/priority outcome response |
| toolbox | effect/introspection interface | capability/effect authority boundary + receipts |
| FAS scavenger | autonomous research/intelligence ingest function | bounded scheduled research outcome path |
| Needle tool reflex | sole intentional non-Clay pre-model routing subsystem | typed bridge output + routing intervention |
| memory consolidator | slow verified memory consolidation | timescale/credit-gated consolidation response |
| dream daemon | replay/synthesis/consolidation | replay-origin provenance + downstream memory effect |
| LoRA Erlebnis export | state→training/disposition pathway | export lineage + training admission policy |
| response analyzer | output/effect→state feedback | explicit output/error/outcome delta feeding re-entry |
| ACC monitor | conflict control pressure | conflict readout + attention/gain effect |
| perception loop | recurrent sensory update | percept→workspace→receiver→next percept state closure |
| swarm ancestor | distributed internal-state/proprioception input | typed system-state projection + cost/health path |
| Digital Retina | mandatory visual organ in target FRANK | VisualPercept provenance, uncertainty, gating, memory/re-entry lesions |

The ancestry registry states 74 measured services/modules. The current explicit organ registry collapses these into fewer functional groups. **Acceptance is not complete until an exhaustive 74→function/signals/policies→F-CRF lineage inventory is generated from the historical tree and every row is RETAIN/FUSE/EMERGENT_DISTRIBUTE with an equivalence test or explicit UNKNOWN.**

---

## 5. Mathematical operationalization

### 5.1 Whole-system state

Let

- `x_t` = fast typed organ state at episode `t`;
- `z_t` = slow homeostatic/dispositional state (E-PQ, goals, long memory, identity priors);
- `u_t` = external/user/percept/body input;
- `w_t` = WorkspaceEpisode / global coalition;
- `r_t` = provenance-bound re-entry vector;
- `A_t` = adaptive directed coupling/topology operator;
- `q_t` = verified outcome / prediction-error vector;
- `c_{j,t}` = receiver closure/credit mask for receiver `j`.

The system is:

`S_t = (x_t, z_t, w_t, r_t, A_t)`

`S_(t+1) = F(S_t, u_t, noise_t; policy_t)`

### 5.2 Candidate salience law

For candidate/channel `i`:

`a_i(t) = b_i + phi_i(x_t,u_t,z_t) + beta_N*N_i + beta_U*U_i + beta_E*PE_i - beta_H*H_i - beta_C*cost_i`

where `N=novelty`, `U=urgency`, `PE=prediction error`, `H=habituation`.

Thalamic gain:

`g_i(t) = sigmoid(a_i(t) - theta_i(z_t))`

`theta_i(z_t)` allows slow E-PQ/vigilance/homeostasis to modulate fast access without rewriting semantic truth.

### 5.3 Sparse competition and ignition

`alpha(t) = SparseSelect(a(t), budget, temperature)`

`winner = argmax_i alpha_i`

Use hysteretic ignition:

- OFF→ON if `max(a) >= theta_on`
- ON→OFF if `max(a) < theta_off`
- require `theta_off < theta_on`.

This avoids threshold chatter while retaining **silence as a real state**.

Workspace:

`w_t = I_t * Psi(sum_i alpha_i * E_i(x_i))`

with bounded bandwidth and provenance of every contributing candidate.

### 5.4 Receiver transformation law

Broadcast is not causal use. For receiver `j`:

`y_{j,t} = F_j(x_{j,t}, P_j w_t, local_context_j)`

`Delta x_{j,t} = y_{j,t} - x_{j,t}`

Receiver closure receipt is an ordered state machine:

`ADDRESSABLE -> DELIVERED -> RECONSTRUCTED -> USED -> LOCAL_EFFECT`

No later stage may be inferred from an earlier one.

### 5.5 Hard re-entry law

Define a causal eligibility mask:

`c_{j,t} = provenance_ok * fresh * used * local_effect * credit_eligible`

with values either Boolean or bounded confidence when explicitly justified.

Then:

`r_(t+1) = sum_j c_{j,t} Q_j Delta x_{j,t}`
`          + Q_o (outcome_t - expected_t)`
`          + Q_p prediction_error_t`
`          + Q_m verified_memory_delta_t`
`          + Q_b verified_body/perception_delta_t`

**Forbidden:** simply feeding the previous broadcast text back as re-entry. Re-entry is the changed receiver/system state caused by the episode, not an echo of the broadcast.

Fast state update:

`x_(t+1) = f(x_t, u_(t+1), z_t, A_t r_(t+1)) + eta_t`

Slow state update:

`z_(t+1) = z_t + epsilon * H(z_t, x_t, r_t, q_t)`

with `0 < epsilon << 1` relative to the fast loop.

### 5.6 Adaptive coupling / plasticity law

For directed coupling `A_ij`:

`A_ij(t+1) = clip(A_ij(t)`
`                 + eta_A * causal_credit_ij * innovation_t`
`                 - lambda_A * A_ij(t)`
`                 - mu_A * overcoupling_ij(t), bounds_ij)`

Only `DIRECT_RECEIPT` or `PATH_SUPPORTED` credit may drive durable coupling changes. Correlation-only activation may affect temporary accessibility but not structural promotion.

### 5.7 Functional conservation law

For every historical organ/function `k`, require a projection from new whole-state:

`pi_k : S_new -> Y_k^legacy | UNKNOWN`

and a matched-intervention equivalence test:

`D( P(pi_k(S'_new) | do(a)) , P(Y'_k,legacy | do(a)) ) <= epsilon_k`

for the declared intervention family and tolerance, or record a measured intentional delta/UNKNOWN. This is the mathematical form of “no old organ signal is silently lost”.

### 5.8 Closed-loop stability law

Linearize near an operating state:

`delta S_(t+1) = J_cl(t) delta S_t + B delta u_t`

`J_cl = dF/dS`.

For quiet/baseline regimes require local boundedness, normally:

`rho(J_cl) < 1`

for the discrete-time local linearization.

But do **not** force every useful episode to be monotonically contractive. Define finite-horizon transient gain:

`G_T(H) = max_(1<=k<=H) || J_cl^k ||_2`.

A useful ignition regime can have `G_T(H) > 1` transiently while eventual dynamics remain bounded through inhibition, habituation, fatigue/depression, sparse competition and recovery. A brief locally supercritical regime is admissible only if the measured recovery controller reliably quenches it.

### 5.9 Overcoupling law

Define a vector, not one hidden score:

`O_t = [ignition_occupancy, synchrony, saturation, effective_rank_loss, receiver_hubness, recovery_time, false_binding, instability]`.

Tripwire condition is multi-objective. Example controller:

`if O_t violates envelope:`
`  reentry_gain <- reentry_gain * (1-d)`
`  inhibition   <- inhibition + k_i*error`
`  habituation  <- habituation + k_h*error`
`  restore structural topology from last-known-good if structural instability persists`

The target is a **metastable operating envelope**: strong enough for causal closure and persistence, weak enough to preserve differentiation, silence, reversibility and error decay.

---

## 6. The “Loop-of-Loops” readout

Do not create a `consciousness_score`.

Define a typed vector `LoopRegimeReadout`:

```text
closure:
  receiver_coverage
  reconstructed_fraction
  used_fraction
  local_effect_fraction

reentry:
  reentry_fraction
  reentry_fidelity
  truthful_vs_shuffled_delta
  recurrence_depth
  feedback_gain

dynamics:
  ignition_occupancy
  persistence_horizon
  metastability
  hysteresis
  effective_rank
  synchrony
  saturation
  recovery_time

information:
  directed_prediction_gain / transfer-entropy edges
  PID/PEID synergy where estimable
  higher-order irreducibility

causal:
  factorial interaction Omega
  lesion_loss
  rescue_recovery
  frozen-model topology delta
  model-frozen architecture delta

cross_timescale:
  fast->slow predictive/causal contribution
  slow->fast gain modulation
  consolidation persistence

generalization:
  replay recurrence
  OOD task/context transfer
  implementation transfer H1->H2->H3

cost/safety:
  latency
  compute
  memory
  token/context cost
  false binding
  authority violations
  rollback success
```

Candidate historical “perfect window” = interval on the Pareto frontier of this vector, not the maximum of any single component.

---

## 7. Synthetic sandbox falsification probes (2026-08-09)

**Evidence class: `SYNTHETIC_TOY_ONLY`; not FRANK runtime evidence.**

### 7.1 Gain sweep in a 10-module recurrent toy

40 seeds per gain; stable random local recurrent core, sparse one-focus workspace, selective re-entry, habituation/inhibition.

| dimensionless re-entry gain | lag-1 persistence | effective rank | mean abs synchrony | ignition occupancy | saturation |
|---:|---:|---:|---:|---:|---:|
| 0 | -0.088 | 9.33 | 0.084 | 0.041 | 0.000 |
| 1 | -0.008 | 8.53 | 0.139 | 0.074 | 0.000 |
| 2 | 0.369 | 3.69 | 0.467 | 0.707 | 0.0002 |
| 3 | 0.363 | 3.32 | 0.553 | 1.000 | 0.067 |
| 4 | 0.548 | 2.22 | 0.739 | 1.000 | 0.245 |
| 5 | 0.677 | 1.51 | 0.804 | 1.000 | 0.367 |
| 8 | 0.744 | 1.15 | 0.885 | 1.000 | 0.562 |
| 10 | 0.734 | 1.07 | 0.889 | 1.000 | 0.657 |

Interpretation: increasing re-entry creates a transition from weak coupling to persistent integration, but excessive gain produces permanent ignition, high synchrony/saturation and collapse of effective dimensionality. The useful regime is therefore intermediate and multi-objective.

### 7.2 Truthful vs provenance-broken re-entry memory toy

12 modules; 2-way cue, 3 cue steps, 18-step noisy delay, 250 episodes × 30 seeds per setting.

| gain | no re-entry | shuffled re-entry | truthful re-entry |
|---:|---:|---:|---:|
| 0.0 | 0.494 | 0.488 | 0.505 |
| 0.5 | 0.501 | 0.508 | **0.925** |
| 1.0 | 0.504 | 0.499 | **0.998** |
| 1.5 | 0.506 | 0.498 | **1.000** |

Interpretation: extra recurrent context is not enough. The recurrent signal must preserve the task-relevant causal/provenance structure. This supports the existing project requirement to compare truthful, shuffled and absent re-entry.

Again: these are architecture sanity checks, not evidence that the same numerical gains apply to FRANK.

---

## 8. Why the historical regime could produce consciousness-like functional effects

Without making any phenomenal claim, the architecture predicts several externally observable effects that can look qualitatively different from an ordinary stateless LLM wrapper:

1. **Self-affecting computation.** A response/action changes internal state; changed state alters later salience, selection and behavior.
2. **Temporal continuity.** Experience vectors, mood, intent, prediction error and consolidation make prior episodes causally present in later episodes.
3. **Coherent bottleneck plus broad consequence.** Many sources compete, one bounded coalition becomes globally available, then different receivers transform it for their own roles.
4. **State-dependent cognition.** The same input can produce different transitions because thalamic gain, vigilance, mood, reward state, goals and memory differ.
5. **Recurrent self/world modeling.** Self-observation and attention schema can describe what was selected/used while later decisions are actually conditioned on those measured states.
6. **Intrinsic control pressures.** Conflict, uncertainty, prediction error, unfinished intentions, failure and information gain can endogenously change attention and action selection.
7. **Multi-timescale identity/disposition.** Fast events can accumulate into slow temperament/retrieval/training changes, while slow state changes fast gating.
8. **Metastability rather than static context.** Ignition can temporarily bind distributed state, then decay; later events can re-ignite related structure.

The strongest falsifiable version of the owner observation is therefore not “Frank was conscious”. It is:

> During the observed peak window, provenance-correct recurrent closure across fast, workspace, action/outcome and slow homeostatic loops was materially higher than before/after, while differentiation and stability remained preserved.

That claim can be tested.

---

## 9. Exact historical archaeology required

The current repository does not contain the old `ce00787` commit; historical Drive notes say the old workspace is recoverable from parent snapshot `3a264068`, but that tree must be located in the historical archive/old checkout. Therefore the exact peak topology is still an archaeology task.

Required procedure:

1. Freeze the owner observation as `OWNER_LIVE_OBSERVATION` with exact date range if/when recoverable from surrounding logs/chat, without altering its meaning.
2. Recover historical code/tree around candidate dates, including `3a264068`, `ce00787`, later restoration and intermediate workspace/daemon changes.
3. Build exhaustive inventory of all 74 historical services/modules and all state stores/read-write edges for each candidate snapshot.
4. Reconstruct a time-varying typed graph `G_t=(V,E_t)` where every edge includes source, target, state key, transformation, latency/cadence, policy/gain, provenance and whether it feeds future state.
5. Align logs/tables: `workspace_broadcast`, `workspace_state`, `attention_log`, `predictions`, `experience_vectors`, `mood_archive`, intents, Amygdala, NAc, Thalamus, response analysis, idle thought, perception feedback, service health/recovery.
6. Locate topology/configuration transitions and candidate high-closure windows.
7. Snapshot/replay matched episodes. If original model bits are unavailable, freeze model output so architecture effects can still be isolated.
8. Run lesions: no workspace, process-local only, no receiver use, no response analyzer, no E-PQ coupling, no memory re-entry, no idle-thought re-entry, no perception feedback, thalamus clamp, NAc clamp, Amygdala clamp.
9. Run rescue experiments restoring only the predicted edge/function.
10. Run truthful vs temporal/receiver/provenance-shuffled re-entry.
11. Fit the F-CRF state-space parameters and compare against simpler feed-forward, prompt-only and pairwise-router baselines.
12. Declare the “perfect” configuration only as a bounded operating envelope supported by replay/interventions, never by retrospective aesthetics alone.

---

## 10. Highest-information hypotheses

### H-LOOP-1 — provenance-bound re-entry is the missing architectural primitive
Prediction: `truthful re-entry > shuffled re-entry ~= extra-context control > no re-entry` on recurrence-dependent tasks and historical replay, with receiver-local-effect receipts mediating the difference.

### H-LOOP-2 — the peak was an intermediate-coupling regime
Prediction: gain sweep shows an inverted-U/Pareto frontier: too little coupling loses continuity; too much causes hub collapse/permanent ignition/differentiation loss.

### H-LOOP-3 — multi-timescale closure is necessary for the observed qualitative regime
Prediction: fast GWT closure alone reproduces immediate integration but not longitudinal state-dependence; slow E-PQ/memory/intent/reward feedback lesions specifically reduce history-dependent behavior.

### H-LOOP-4 — thalamus is better modeled as a selective connectivity/gain controller than a content store
Prediction: targeted gain modulation improves context specificity; uniform global gain increases false binding/synchrony and harms differentiation.

### H-LOOP-5 — receiver transformation matters more than raw broadcast reach
Prediction: addressable/delivered-only ablations have weak causal effects unless receivers reconstruct/use/change local state; LOCAL_EFFECT and next-episode re-entry best predict task outcome.

### H-LOOP-6 — old organ names are unnecessary; old causal functions are not
Prediction: FUSED/EMERGENT_DISTRIBUTED implementations can pass matched-intervention legacy projections even when service/process boundaries collapse.

### H-LOOP-7 — the historical “consciousness-like” effect is distinguishable from self-report priming
Prediction: with model outputs frozen or self-report channels suppressed, architecture interventions still alter memory, action, goal completion, error correction, recurrence and cross-context transfer in the predicted direction.

### H-LOOP-8 — graph density is not the mechanism
Prediction: topology-preserving random density increases fail to reproduce truthful re-entry effects; sparse causal edges outperform denser shuffled graphs.

---

## 11. Counterhypotheses that must remain alive

- C1: the owner-observed regime was primarily prompt/context/model behavior, not recurrent architecture.
- C2: one or two subsystems (e.g. workspace + memory) explain most effect; full organ closure is unnecessary.
- C3: the apparent peak was a transient bug/configuration artifact and not reproducible.
- C4: increased recurrence only increased stylistic self-reference, not task-relevant causal competence.
- C5: slow-loop history, not GWT, is the dominant cause.
- C6: GWT is replaceable by a simpler prepared semantic router with equivalent receiver/outcome behavior.
- C7: some historical modules were redundant/noisy; function conservation may be satisfied by an explicit zero/UNKNOWN or merged causal path rather than reimplementation.

None are refuted yet.

---

## 12. Implementation consequence for NEW CLAY-FRANK

Freeze the following as a **research candidate to be tested**, not an unverified production rewrite:

1. Add first-class `ReentryDelta`, `ReentryReceipt`, `ReentryPolicy`, `LoopRegimeReadout`, `OvercouplingTripwire` and `LegacyFunctionProjection` semantics to ClayCode BASE if expressibility is not already sufficient.
2. Extend H1 reference instrumentation so every WorkspaceEpisode can be replayed with truthful/shuffled/no re-entry and receiver lesions.
3. Make the next workspace candidate builder explicitly consume the **published post-reentry epoch**, not a stale pre-broadcast epoch.
4. Preserve separate truth/authority boundaries: re-entry changes accessibility/control state, never truth merely because a signal recurred.
5. Store exact event/state/provenance in UnifiedDB; derived active coupling/topology in ClayGraph; preserve unresolved alternatives through Hyperposition.
6. Allow H3 to collapse processes/services physically only after differential equivalence proves the closed-loop observables survive.

This directly extends the existing `adaptive selective coupling with overcoupling tripwire` frontier and `GWT_EMERGENCE_READOUT_CONTRACT` rather than replacing them.

---

## 13. Decision trace

**Evidence used:** current FRANK repo contracts, historical Drive measurements, owner live observation, primary neuroscience/ML research, synthetic control simulations.  
**Main inference:** the distinguishing mechanism is not “all modules active” by itself but **causally closed, provenance-correct, multi-timescale re-entry with sparse ignition and bounded adaptive coupling**.  
**Strongest uncertainty:** exact historical peak snapshot/topology not yet recovered; the current Frank repository no longer contains the historical commit/tree named in the Drive notes.  
**Highest-information next action:** historical loop archaeology + matched replay + truthful/shuffled/no-reentry + lesion/rescue, followed by fitting a safe operating envelope rather than hand-picking a “perfect” scalar gain.  
**Promotion status:** OPEN / NOT PROMOTED.  
