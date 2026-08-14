# FRANK Function + Signal Conservation Audit — 2026-08-10

Status: `CROSS_BRANCH_RESEARCH_DELTA · NO_REPLACEMENT_PROMOTION`
Actor: `chatgpt-secondary` temporary Clay research worker
Provider/model provenance: OpenAI / GPT-5.6 Sol
Subject: Frank v0.1 architecture
Authority: Research Entity research/build/test authority; Frank self-Harness authority remains PROPOSAL_ONLY
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Executive conclusion

Current evidence does **not** support the claim that the new Frank architecture has lost the whole historical loop function. The integrated sandbox has coarse evidence that Thalamus-like gain, NAcc-like persistence/reward state, GWT ignition, conflict sensing, causal credit, verification and provenance-bound re-entry are wired and causally consequential.

However, current evidence also does **not** support the stronger claim that historical signal semantics are losslessly conserved. The historical-completeness gate is correctly still HOLD. The strongest risk is not missing organ names; it is **signal compression**: a historical multidimensional, stateful, multirate signal can survive as one scalar/boolean readout while losing route identity, sign, feature identity, timing, adaptation law or downstream sensitivity.

Therefore:

`31/31 organ receipts != historical signal conservation`

and

`aggregate 74 conservation != 74/74 source-backed functional equivalence`.

No RETAIN/FUSE/EMERGENT_DISTRIBUTE/CLAY_REDESIGN promotion for a historical regulator should pass until its signal-level differential package is complete.

## Source-backed historical closures that must remain testable

Recovered historical Frank evidence describes at least these causal closures:

1. Workspace -> Thalamus sensitization for high-salience workspace events.
2. Model output -> Thalamus channel-specific feedback: referenced channels positive bias, ignored channels negative bias, with decay across gate calls.
3. Amygdala -> E-PQ -> Thalamus: appraisal perturbs slow personality/regulation; vigilance multiplicatively changes gate gains.
4. Response -> ResponseAnalyzer -> E-PQ -> later cognition: Frank's own output is analyzed and can change future state.
5. ACC -> E-PQ -> Thalamus/self-model: belief-vs-measurement mismatch generates conflict and adaptive control.
6. NAcc -> E-PQ/motivation: reward prediction errors update phasic/tonic state and affect future persistence/motivation.
7. Memory/consciousness/perception asynchronous loops -> later workspace.

Recovered historical state/update detail includes:

- 9 typed Thalamus channels, each with gain/habituation and channel-specific feedback.
- Thalamus gain factors for habituation, cognitive-mode attention, E-PQ vigilance, novelty/burst, prior-output feedback and prediction error.
- E-PQ slow vector with `precision`, `risk`, `empathy`, `autonomy`, `vigilance`, bounded per-event deltas and age/quality-dependent learning rate.
- NAcc adapted reward, signed reward prediction error, asymmetric positive phasic amplification, predicted-reward update, tonic dynamics and opponent/boredom effects.
- ACC mismatch magnitude, thresholded conflict salience and adaptive threshold damping/decay.

These are causal hypotheses inherited from the original system; neuro-inspired naming is not evidence. Their successor mechanisms may be fused or renamed, but their measurable functional roles may not silently disappear.

## Current sandbox evidence: what is actually demonstrated

The current integrated sandbox organ audit demonstrates coarse surfaces including:

- affect/control: `urgency`, `category`, `novelty`, `habituation`, scalar `gain`, `reward_prediction`, `persistence`;
- workspace: selected inputs and an attention receipt;
- verification and direct causal-credit receipts;
- loop controller: scalar `thalamus_gain`, scalar `nacc_persistence`, boolean `gwt_ignited`, boolean `conflict_sensor`, residual, recurrence count/budget, halt reason and utility proxy;
- a conflict-sensor lesion that creates a false halt while true residual remains high;
- provenance-bearing re-entry lineage fields in the master evidence package.

This is meaningful evidence that some regulatory mechanisms are not merely decorative. It is not sufficient evidence that their historical signal dimensionality or dynamics are preserved.

The master evidence package itself correctly records:

- 31 required current organs and 31 current function receipts;
- 102 mixed inventory/ancestry mappings;
- historical aggregate measurement 74;
- 40 individually source-resolved historical technical identities;
- `historical_functional_completeness_gate = HOLD_UNRESOLVED_LEGACY_IDENTITIES`;
- `historical_74_completion_gate = HOLD_SOURCE_BACKED_74_SLOT_MAPPING`;
- no permission to claim a 74/74 per-slot mapping without a primary slot ledger.

## Signal-loss risk register

### R1 — Thalamus channel identity: HIGH

Historical evidence: 9 typed channels with per-channel habituation, attention weighting, prior-output feedback and prediction-error contribution.

Current demonstrated readout: one scalar `gain` / `thalamus_gain`.

Risk: route identity can disappear while the scalar average remains unchanged. Two historical states can have exactly the same aggregate gain while a +feedback bias is assigned to different channels. Their next admitted candidate/route differs although the coarse scalar is identical. Thus a scalar gain is a non-identifying projection of the historical state unless hidden per-channel state is independently demonstrated.

Required proof: `RouteGain[channel]`, `Habituation[channel]`, `TopDownFeedback[channel]`, `PredictionError[channel]`, channel identity and downstream route sensitivity under matched replay.

### R2 — NAcc/reward decomposition: HIGH

Historical evidence: predicted reward, adapted reward, signed RPE, phasic response, tonic state, habituation and opponent/boredom dynamics.

Current demonstrated readout: `reward_prediction` and `persistence`.

Risk: sign, feature identity, timing and teaching-vs-persistence roles may be collapsed.

Live primary research strengthens this concern rather than the biological metaphor itself:

- Lee et al., Nature Neuroscience 2024, DOI `10.1038/s41593-024-01689-1`: feature-specific prediction errors explain dopaminergic heterogeneity; a homogeneous scalar RPE is insufficient for the observed high-dimensional signal structure.
- Cone et al., Nature Communications 2024, DOI `10.1038/s41467-024-50205-3`: RPE-like activity depends on learned temporal representations, emphasizing delayed-outcome/time-basis structure.
- Greenstreet et al., Nature 2025, DOI `10.1038/s41586-025-09008-9`: reward prediction error and value-free action prediction error can act as distinct teaching signals and together improve/stabilize learning in the studied task.
- Naude et al., Nature Communications 2024, DOI `10.1038/s41467-024-53976-x`: phasic dopamine can participate in both learning and online motivational modulation in a recurrent attractor architecture.

Engineering consequence: do not replace historical NAcc semantics by one universal reward scalar. Use typed, lesionable components and let evidence decide which are necessary for Frank.

Suggested successor surface:

`RewardControl = {reward_prediction, adapted_reward, rpe_signed, rpe_feature, phasic, tonic, habituation, action_prediction_error?, persistence, disengagement, credit_lag, outcome_ref}`

The `action_prediction_error?` field is a research candidate, not a historical fact about Frank.

### R3 — E-PQ slow regulatory vector: HIGH

Historical evidence: five persistent dimensions plus a specific slow adaptation schedule.

Current organ audit: no full E-PQ vector or update-law equivalence receipt is shown.

Required proof: all five dimensions, update provenance, learning-rate schedule (or justified superior replacement), caps/bounds, restart persistence, effect on downstream gain/selection, lesion/rescue and long-horizon replay.

### R4 — ACC adaptive conflict controller: MEDIUM-HIGH

Current evidence proves that a conflict sensor matters: lesioning it can cause false halt with unresolved residual.

Missing proof: preservation/replacement of mismatch magnitude, adaptive threshold, post-conflict damping and threshold decay. A boolean conflict flag can retain the existence of conflict while losing the controller dynamics.

### R5 — ResponseAnalyzer self-output feedback: HIGH

Historical role: model/response output is converted into a state event that changes E-PQ/future cognition.

Current coarse organ audit does not explicitly prove an equivalent response-analysis -> slow-state -> future-gating closed receipt.

Required test: freeze identical model outputs; vary only ResponseAnalyzer successor; show downstream state change and later-cycle behavior. Then lesion/rescue with exact episode/signal lineage.

### R6 — GWT content/receiver semantics: MEDIUM-HIGH

Current evidence includes selected workspace inputs, ignition and provenance-aware re-entry. That is stronger than a pure boolean architecture.

Still required: candidate universe, competition scores, ignition threshold/hysteresis/focus, receiver addressability/delivery/reconstruction/uptake/causal-use/outcome/re-entry chain, and content/signal identity across the chain.

The 2025 preregistered adversarial GNWT/IIT collaboration in Nature (DOI `10.1038/s41586-025-08888-1`) challenged several strong GNWT predictions. Engineering consequence for Frank: GWT ignition should remain an operational selection/broadcast mechanism under test, not a privileged consciousness or quality scalar; content- and receiver-specific causal receipts matter more than an `ignited=true` flag.

### R7 — Amygdala/appraisal richness: MEDIUM

Current evidence preserves urgency/category. Historical reconstruction also mentions salience/threat and somatic-marker-like state. The latter is not yet demonstrated as conserved or useful.

Disposition: preserve as UNKNOWN/CANDIDATE until source-backed state and lesion/rescue evidence discriminates useful function from biological metaphor.

### R8 — Experience vector / novelty: MEDIUM

Current evidence exposes scalar novelty. Historical architecture used experience-vector concepts and novelty/reseed coupling. Verify whether vector identity, recurrence/drift/shifting/recurring annotations and downstream anti-stagnation effects are preserved, fused or intentionally removed.

### R9 — Multirate asynchronous loops: HIGH

Historical Frank had background/asynchronous memory, perception, prediction/consciousness and slow adaptation loops. A one-module runtime may safely fuse process boundaries, but only if distinct time constants/cadences and delayed re-entry remain representable.

Do not replace multirate dynamics by one global synchronous recurrence tick merely to simplify packaging.

## Non-identifiability witness: why current coarse receipts cannot prove conservation

This is an analytical falsifier, not Frank runtime evidence.

Take two historical Thalamus states with identical base gains, habituation, attention, vigilance, novelty and prediction error. In state A, channel 1 gets the historical +0.15 prior-output bias and the other channels get -0.05. In state B, channel 9 gets +0.15 and the others get -0.05.

The **aggregate mean gain is identical** because the vectors are permutations. Yet the highest-gain channel identity differs, so candidate admission/routing can differ.

Therefore any audit that records only one scalar `thalamus_gain` cannot distinguish these two historically different causal states. The scalar is compatible with both preserved and lost channel semantics.

The same logic applies to a boolean `gwt_ignited`, a boolean `conflict_sensor`, and a scalar `persistence`: existence of an effect is not equivalence of the underlying signal.

## Required new contract: SignalConservationReceipt

Add a machine-comparable receipt per material historical signal or signal family:

- `historical_signal_id`
- historical source/path/version/hash
- historical dimensionality/schema/units/range
- state variables
- update law/equation or `UNKNOWN`
- cadence/timescale/delay
- initialization/boot dependency
- upstream causal parents
- downstream consumers
- feedback/re-entry route
- historical lesion/rescue handle
- successor mechanism(s)
- disposition: `RETAIN|FUSE|EMERGENT_DISTRIBUTE|CLAY_REDESIGN_CANDIDATE`
- successor dimensionality/schema
- transformation/projection function
- information intentionally discarded, if any
- reason discarded
- matched replay error vector
- impulse/step-response error
- downstream sensitivity delta
- lesion/rescue delta
- delayed-outcome/credit delta
- restart/recovery equivalence
- resource/latency delta
- OOD delta
- confidence + missing evidence
- status: `UNMAPPED|MAPPED_UNTESTED|PARTIAL|EQUIVALENT_WITHIN_TOLERANCE|INTENTIONALLY_CHANGED_SUPPORTED|REFUTED`

Hard law:

`ORGAN_PRESENT != SIGNAL_CONSERVED`

`SCALAR_PROXY_PRESENT != HISTORICAL_STATE_EQUIVALENCE`

`NO_SIGNAL_CONSERVATION_RECEIPT -> NO_FUNCTIONAL_DISSOLUTION_CLAIM`.

## Highest-value H1 differential suite

1. **Channel-permutation test** — same aggregate Thalamus gain, different channel-specific feedback identity; successor must preserve route-specific outcome differences when historical baseline does.
2. **RPE sign/feature test** — matched total reward with positive/negative and feature-specific prediction errors; measure learning, persistence and later selection separately.
3. **Delayed-credit test** — identical eventual outcome with different delays; test reward/credit/time-basis behavior.
4. **E-PQ slow-timescale test** — matched events across simulated ages/quality levels; compare five-dimensional state evolution and downstream gate sensitivity.
5. **ACC hysteresis test** — repeated conflicts vs isolated conflict; compare adaptive threshold/false-halt/overshoot.
6. **Self-output feedback test** — same external outcome, changed Frank response content; isolate ResponseAnalyzer successor and later-cycle effects.
7. **GWT receiver-chain test** — `addressable -> delivered -> reconstructed -> used -> local effect -> verified outcome -> credit -> re-entry`; shuffled receiver/provenance-broken/no-reentry controls mandatory.
8. **Async/multirate test** — same events delivered under preserved vs flattened cadence; measure memory, state drift, false ignition, missed correction and resource cost.
9. **Restart continuity test** — each slow state and pending credit survives/reconciles correctly without duplicate learning.
10. **Original vs Perfected Ancestor vs One-Module** — three-way matched comparison so feedback-law improvements are not falsely attributed to architectural consolidation.

Every test records latency, functional correctness, reliability/recovery, resources and complete Frank cognitive-state metadata per the global baseline contract.

## Architecture delta candidate

Do not create a new set of historical microservices. Keep the one-module target, but inside it expose a typed multirate `RegulatoryField` rather than flattened scalars:

- per-route gain/habituation/top-down feedback/prediction error;
- typed reward/teaching/persistence signals;
- five-dimensional or evidence-supported successor slow personality/control state;
- graded conflict plus adaptive threshold state;
- response/self-output feedback;
- GWT competition/threshold/hysteresis/focus plus receiver-specific causal chain;
- novelty/reseed state;
- exact episode/signal/provenance identity;
- separate provisional within-episode adaptation from verified durable learning.

Physical process boundaries may disappear. Semantic dimensions, dynamics and causal lineage may disappear only after a matched test shows `NO_BENEFIT` or a validated replacement.

## Counterhypotheses retained

- `H0-S1`: the apparent historical signal richness was mostly decorative; coarse successors preserve all task-relevant function at lower cost.
- `H0-S2`: per-channel Thalamus state matters only for introspection/logging, not behavior.
- `H0-S3`: NAcc phasic/tonic/feature decomposition adds no Frank-level benefit over one calibrated utility/persistence controller.
- `H0-S4`: E-PQ five-dimensional state can be reduced without measurable loss.
- `H0-S5`: ResponseAnalyzer self-feedback causes drift/self-reinforcement and should be removed rather than conserved.
- `H0-S6`: asynchronous old loops mostly reflected service topology; event-driven one-module scheduling reproduces their effective time constants.

These must be tested, not assumed false.

## Promotion consequence

Current conclusion class:

`PARTIAL_SIGNAL_CONSERVATION_EVIDENCE + MATERIAL_UNRESOLVED_RISK`

No evidence justifies rolling back the one-module direction. Evidence does justify strengthening H1/H2/H3 gates so that **signal-level conservation**, not organ-name presence, is the comparison unit.

The existing `historical_functional_completeness_gate = HOLD` remains scientifically correct and should remain HOLD until primary historical slot identities and critical SignalConservationReceipts are resolved.
