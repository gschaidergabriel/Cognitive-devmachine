# FRANK Feedback Refinement — Verified Innovation Packets instead of self-output reinforcement

**Status:** OPEN_RESEARCH_DELTA_NOT_CANONICAL_PROMOTION  
**Date:** 2026-08-10  
**Origin actor:** chatgpt-secondary  
**Provider/model:** OpenAI / GPT-5.6 Sol  
**Canonical parent:** revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**Fresh concurrent parent:** `FRANK_PERFECT_FEEDBACK_LOOP_SYNTHESIS_20260810.md` / commit `da0e06d031df0b2e233b7bfababa1a2ea70f1505`  
**Operational target:** Frank v0.1 on Andreas' Ubuntu developer system  
**Authority:** Research Entity research proposal/evidence only; no Frank self-harness authority.

## 0. Why this delta exists

A concurrent Clay worker already synthesized and distributed `VERIFIED_ADAPTIVE_RECURRENT_LOOP_CORE_V1` while this research run was active. The current worker therefore does not duplicate that result. This note adds one narrower mechanism refinement that was not yet explicitly tested in that synthesis:

> The primary positive feedback signal should not be Frank's previous model output or generic recurrent activity. It should be a bounded, receiver-specific, provenance-valid **verified innovation packet**: the typed difference between what the system predicted and what actually happened, plus uncertainty change, utility change and causally supported credit.

Historical direct model-output -> Thalamus feedback remains ancestry evidence and a possible weak salience prior. It should not be the main durable control signal unless matched tests show a benefit.

## 1. Historical risk being addressed

Recovered original-Frank ancestry includes a direct top-down closure in which channels referenced by the model answer received positive feedback and ignored channels could receive negative feedback, with decay across later gate calls. That mechanism creates useful short-term continuity, but it has an obvious falsifiable failure mode:

`model mentions channel -> channel gets more gain -> same channel is more likely to recur -> model mentions it again`

This can produce a self-confirming attractor even when the external outcome does not validate the channel.

The original Frank already had ingredients that could repair this if coupled perfectly: prediction error, ACC conflict, NAcc reward prediction error, ResponseAnalyzer, memory consolidation, Thalamus habituation, GWT selection and slow E-PQ adaptation. The perfected loop should couple them around verified prediction/outcome mismatch instead of raw self-reference.

## 2. External primary-source refresh fused in this delta

### 2.1 Recurrent depth can help and can overthink

Kohli et al. 2026, arXiv:2604.07822, show that additional recurrent depth can unlock deeper compositional reasoning but excessive recurrence can degrade predictions. This supports adaptive recurrence and an explicit overthinking exit condition.

### 2.2 Injection dynamics are a stability surface

Prairie et al. 2026, arXiv:2604.12946 (Parcae), model looped architectures as dynamical systems and trace instability in a linearized analysis to large spectral norms in injection parameters. This makes **re-entry injection strength** a first-class Frank control variable: feedback can be correct in content and still destabilizing if injected too strongly.

### 2.3 Fixed-point halting is useful but local

Movahedi et al. 2026, arXiv:2606.18206, use fixed-point convergence as an adaptive halting mechanism in looped Transformers. Frank should borrow this only for fixed-point-like local regimes. Productive bounded cycles, external tool waits and asynchronous outcome loops require typed non-fixed-point states.

### 2.4 Event-triggered control reduces unnecessary control work

Gräfe & Trimpe 2025, arXiv:2504.19540, show an event-triggered robust MPC design that retains stability under disturbances while limiting which systems solve optimization problems at a given time. Transfer to Frank: not every loop needs to recur on every tick; a material innovation, uncertainty change, residual violation, deadline/risk event or verified outcome can trigger the next expensive recurrence.

### 2.5 Uncertainty and tail risk belong in the control state

Enwerem, Baras & Belta 2026, arXiv:2604.03868, optimize control in belief space under latent uncertainty with explicit CVaR safety constraints. Transfer: Frank's recurrence decision should be conditioned on calibrated uncertainty and hard authority/safety constraints, not expected utility alone.

### 2.6 Biological recurrent loops are frequency/timescale selective

Yoshimoto et al. 2025, Communications Biology, report a reciprocal ACC-mediodorsal-thalamic circuit with frequency-selective facilitation/resonance in the theta range at the population level. This is not evidence that Frank should copy brain frequencies. It supports the engineering counterhypothesis that heterogeneous recurrent paths may need distinct gain/delay/timescale tuning rather than one global feedback gain.

Song et al. 2026, Nature Communications, report that large-scale cortical trajectory geometry toward attractors changes with attentional state, including faster/direct task-relevant convergence during effortful attention. Again, this is analogy-level evidence only; it motivates measuring trajectory geometry and context-dependent convergence rather than one static stability scalar.

## 3. Proposed primitive: FeedbackInnovationPacket

A material re-entry object should carry at minimum:

```text
FeedbackInnovationPacket {
  episode_id
  signal_id
  state_epoch
  source
  receiver
  predicted_outcome
  predicted_uncertainty
  verified_outcome
  verification_class
  innovation_typed
  uncertainty_delta
  utility_delta
  residual_delta
  constraint_violations
  causal_use_receipt_ids
  causal_credit_vector
  credit_uncertainty
  transformation_chain
  lag
  validity_window
  proposed_gain
  applied_gain
  gain_cap
  habituation_state
  instability_shadow
  rollback_ref
}
```

Rules:

1. `verified_outcome` is never silently replaced by model self-evaluation when independent verification exists.
2. `innovation_typed` is task-specific; it may be numeric error, categorical mismatch, state-transition mismatch, missing-effect evidence, calibration error, or another typed residual.
3. No durable learning authority is created merely because a signal was broadcast or recurrently active.
4. A stale/wrong-epoch/provenance-broken packet is rejected, not approximately applied.
5. The packet may target different receivers with different bounded gains and delays.
6. Historical previous-model-output reference may enter only as a weak decaying salience prior unless tests justify more.

## 4. Three orthogonal feedback dimensions

The perfected loop should preserve three dimensions instead of collapsing feedback into one reward scalar:

### A. Epistemic innovation

`what did prediction/model/state get wrong or newly learn?`

Inputs: predicted-vs-verified outcome, uncertainty change, conflict, missing evidence.

### B. Goal/value utility

`did the action/reasoning actually improve the declared task/goal under cost and constraints?`

Inputs: verified task outcome, residual reduction, resource cost, deadline/safety/authority state.

### C. Causal/provenance credit

`which selected/delivered/reconstructed/used path actually contributed?`

Inputs: causal-use receipts, local effects, interventions, lesion/rescue, matched rerollouts where warranted.

These dimensions can interact, but none should mint truth or durable learning alone.

## 5. Candidate bounded gain law

For feedback path `j -> i`:

```text
g_eff(j,i,t) = clip(
    g0(j,i)
  * q_verification
  * q_provenance
  * q_calibration
  * f(residual_materiality, novelty, deadline)
  / (1
     + lambda_h * habituation
     + lambda_s * instability_shadow
     + lambda_age * staleness),
  g_min,
  g_max
)
```

This is a research law, not a frozen parameterization.

Implications:

- correct but weakly verified feedback is downweighted;
- provenance-broken feedback approaches zero;
- repetitive low-value feedback is damped;
- stale feedback decays;
- high residual/novelty can increase selective gain without increasing all-loop gain;
- instability suppresses further positive recurrence before runaway coupling;
- hard safety/authority constraints remain outside this soft gain calculation.

## 6. Adaptive recurrence / event-trigger law

A new expensive recurrence is eligible when at least one material event exists:

- verified outcome arrived;
- prediction innovation exceeds typed deadband;
- uncertainty crosses a decision-relevant threshold;
- residual/control pressure remains high;
- contradiction/conflict crosses threshold;
- deadline/risk state changes;
- tool/effect dependency changes state;
- stalled regime requests new evidence/reroute/reseed;
- recovery/rollback event requires revalidation.

Then continue only if:

```text
E[marginal verified utility gain + information gain]
  > compute + latency + risk + instability + opportunity cost
AND unresolved pressure remains material
AND authority/recovery constraints permit recurrence
```

Use hysteresis/deadbands to avoid chatter around thresholds.

## 7. Synthetic mechanism falsifier — self-output feedback vs innovation feedback

**Scope:** synthetic controller stress test only. This is not Frank runtime evidence and must not be promoted as such.

Protocol:

- 1,000 matched random seeds;
- 400 steps per seed;
- binary latent target changes stochastically over time;
- noisy observations;
- noisy but higher-quality post-step verification signal;
- same recurrent memory/sensory coefficients across candidates;
- compare no feedback, direct previous-output reinforcement, direct verified-outcome feedback, and event-triggered verified-innovation feedback;
- metrics: state-choice accuracy, switch recovery time, saturation, post-switch error and fraction of steps receiving a feedback update.

Mean results:

```text
mode              accuracy   switch_recovery   feedback_fraction   saturation   post_switch_5step_error
no_feedback        0.95980       1.9464             0.0000          0.03404          0.18270
direct_output      0.92332       3.6610             1.0000          0.21185          0.46230
direct_outcome     0.98868       1.4195             1.0000          0.23243          0.07881
innovation_event   0.98963       1.2516             0.4011          0.06325          0.04500
```

Key observations inside this constructed model:

1. direct self-output reinforcement created the worst switching/lock-in behavior;
2. verified outcome feedback was strong and accurate but produced high saturation and ran every step;
3. event-triggered innovation achieved slightly higher classification accuracy and faster switching with about 40% of possible feedback applications and far lower saturation than direct outcome feedback;
4. direct outcome feedback produced a lower continuous-state MAE than innovation feedback in this toy model, so innovation does **not** dominate every metric; this tradeoff must be preserved.

### 7.1 Provenance corruption control

Using the same innovation controller:

```text
feedback provenance     accuracy   feedback_fraction
truthful                 0.98961       0.4014
receiver/time shuffled   0.88951       0.7458
provenance broken        0.88241       0.7766
```

In this constructed test, bad provenance not only reduced accuracy; it also caused more feedback work because the controller kept seeing unresolved innovation. This is the desired failure signature for a provenance-aware loop and motivates explicit rejection/quarantine of invalid feedback packets.

## 8. Architecture refinement to VERIFIED_ADAPTIVE_RECURRENT_LOOP_CORE_V1

Add the following candidate law:

`PRIMARY_REENTRY = VERIFIED_INNOVATION_PACKET`

not:

`PRIMARY_REENTRY = PREVIOUS_MODEL_OUTPUT`

The historical previous-output route becomes:

`PREVIOUS_MODEL_OUTPUT -> weak short-lived salience/context prior -> subject to verification/habituation/decay`

The stronger durable route becomes:

```text
prediction/prospection
  -> action/internal operation
  -> verified outcome
  -> typed innovation
  -> receipt-gated causal credit
  -> receiver-specific bounded re-entry
  -> provisional update
  -> outcome-admitted durable update where justified
```

This turns feedback from self-echo into correction-bearing causal re-entry.

## 9. Counterhypotheses to preserve

`H0-INNOV-1`: Direct verified-outcome feedback is simpler and can outperform innovation on continuous-state error; innovation packaging overhead may not justify itself in Frank.

`H0-INNOV-2`: Historical model-output feedback may improve semantic continuity when outcome verification is sparse; weakening it could cause excessive topic switching or loss of working context.

`H0-INNOV-3`: Event-triggered feedback can miss slow accumulating drift if thresholds/deadbands are too high.

`H0-INNOV-4`: Exact causal-use receipts may be too sparse/expensive and could starve useful learning.

`H0-INNOV-5`: Different loop families may require different error representations; one universal innovation type would recreate the global-controller mistake.

`H0-INNOV-6`: Biological frequency-selectivity and neural attractor findings may have no useful engineering transfer to Frank beyond generic multirate intuition.

## 10. Highest-information H1 experiment

On frozen original-Frank episodes, compare matched configurations:

A. `ORIGINAL_ANCESTOR` historical direct feedback;
B. `PERFECTED_ANCESTOR_DIRECT_VERIFIED_OUTCOME`;
C. `PERFECTED_ANCESTOR_VERIFIED_INNOVATION_EVENT_TRIGGERED`;
D. `ONE_MODULE_VERIFIED_INNOVATION` when H2/H3 become executable.

Required controls:

- truthful feedback;
- receiver-shuffled;
- time-shuffled;
- provenance-broken;
- no re-entry;
- direct-output frozen;
- outcome-verification lesion/rescue;
- causal-credit lesion/rescue;
- event-trigger threshold sweep;
- gain cap / habituation / hysteresis sweep;
- OOD episodes;
- crash/restart/out-of-order outcome delivery.

Required outcomes:

- task/outcome accuracy;
- calibration;
- correction/switch recovery;
- residual pressure;
- false halt/stall/overthinking;
- recurrence count;
- feedback application count;
- provenance rejection rate;
- durable-learning false-credit rate;
- saturation/dominance/diversity;
- latency/CPU/RAM/GPU/token/tool cost;
- recovery/replay equivalence.

Promotion criterion:

Do not promote innovation feedback because it sounds more principled. Promote only if it is Pareto-competitive against direct verified-outcome feedback and the original/perfected ancestor under matched real H1 episodes, with provenance controls and recovery intact.

## 11. Current conclusion

The strongest current engineering hypothesis is:

> Frank's ideal feedback loop is a multirate, event-driven, outcome-verified causal controller whose main re-entry signal is the *innovation between predicted and verified reality*, modulated by uncertainty, utility and exact causal provenance. The system's own previous output may preserve short-term continuity, but should not be allowed to become self-validating evidence.

This is an OPEN research candidate, not canonical promotion and not evidence of phenomenal consciousness.
