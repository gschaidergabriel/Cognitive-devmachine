# FRANK Loop-of-Loops — Signal-Conservation Sandbox Delta

Status: OPEN_MECHANISM_RESEARCH + SYNTHETIC_SANDBOX_EVIDENCE
Date: 2026-08-09
Origin actor: chatgpt-secondary
Canonical parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346
Target: Frank v0.1 Ubuntu reference runtime
Phenomenal-consciousness claim: NONE

## Owner primary observation
The project lead reports a multi-day historical period in original Frank with a strong stable whole-system feedback effect while organs/modules were jointly active. Treat this as PROJECT_OWNER_PRIMARY_LONGITUDINAL_OBSERVATION of a functional effect, not as proof of consciousness. The target is to reproduce/discriminate the effect while preserving every historical organ/module function, policy, state signal and causal role through RETAIN, FUSE or EMERGENT_DISTRIBUTE lineage.

## Historical reconstruction delta
Direct ancestor-code archaeology establishes multiple nested closures rather than one feedback wire:

1. Workspace -> Thalamus: `services/thalamus.py` subscribes to Global Workspace; high-salience workspace events (>=0.7) sensitize the next gate cycle.
2. Model output -> Thalamus: referenced channels receive +0.15 top-down feedback bias, ignored channels may receive -0.05; bias decays x0.87 per gate.
3. Amygdala -> E-PQ -> Thalamus: appraisal maps to E-PQ events; E-PQ vigilance modulates global thalamic gain.
4. Response -> ResponseAnalyzer -> E-PQ -> future state: Frank's output becomes self-feedback.
5. ACC -> E-PQ: belief-vs-measured-reality conflicts perturb slow self-regulation.
6. NAcc -> tonic/phasic reward state -> E-PQ/motivation: reward-prediction error supplies value/persistence dynamics.
7. Consciousness/Perception/Memory/Goals run at heterogeneous periods and alter later workspace/gating state.

Working organism-level chain:
`observation -> appraisal/gating -> workspace ignition/broadcast -> local use -> action/output -> outcome -> state delta -> provenance-bound re-entry -> next gating/selection`, with slow memory/self/reward/homeostatic loops wrapped around it.

## Recovered source equations
Historical Thalamus final-gain structure:
`g_c = clip(base_c * (1-0.8*habituation_c) * attention_c * (1+0.3*vigilance) * novelty_burst_c * (1+feedback_c) * (1+min(0.5*prediction_error_c,0.4)))`.

Historical E-PQ working law:
`P_new = P_old + event_weight * learning_rate * event_specific_direction`, with `learning_rate=max(0.02,0.15*0.998^age_days)*(0.3+0.7*event_quality)` and persistent per-event vector delta capped at 0.15.

Historical NAcc RPE:
`adapted_reward=raw_reward*(1-habituation)`; `RPE=adapted_reward-predicted_reward`; positive phasic response `=1.5*RPE`, otherwise `=RPE`; prediction is EMA-updated with alpha 0.1.

Historical ACC:
`discrepancy=abs(belief-measured_reality)`; conflict if above adaptive threshold; `salience=min(1,(discrepancy-threshold)/0.40)`.

## Generalized target laws
For typed whole-Frank state `x`, input/outcome `u`, slow homeostasis `h`, coupling `W`:

`x_i[t+1]=(1-alpha_i)x_i[t] + alpha_i*phi(u_i + gamma*Sum_j W_ij*x_j + beta_i*B_t - eta_i*h_i)`

`B_t=sigmoid(k*(workspace_drive-theta_t))`

`h_i[t+1]=lambda_i*h_i[t]+(1-lambda_i)*x_i[t]`

Bare `gamma*W` is not a stability criterion. Local stability must be estimated from the full nonlinear Jacobian `J*=dF/dz` over the relevant fast/slow state. `rho(J*)<1` is a local contraction indicator for fixed-point-like regimes, while bounded productive cycles/metastability remain valid targets. Current Frank trajectory code already correctly guards that `gain_proxy != Jacobian spectral radius`.

A declared path gain is the product of local elasticities multiplied by delivery/reconstruction/uptake/use/re-entry survival, not the sum of edge weights.

## Sandbox operationalization
A 31-organ synthetic multi-timescale graph was built from the current named ancestry surface. It classifies 22 later-stage -> earlier-stage edges as distributed semantic re-entry. The sandbox sweep tested 324 normalized configurations: recurrent gain 0.35..3.00 x homeostatic damping 0.10..0.50.

Regimes:
- DECAY: 99
- METASTABLE_CLOSED_LOOP_CANDIDATE: 117
- OVERCOUPLED: 108

Homeostasis shifts the upper metastable boundary upward: at damping 0.10 the metastable band is 1.10..1.85 and overcoupling starts 1.90; at damping 0.50 it is 1.25..2.35 and overcoupling starts 2.40. This is synthetic architecture evidence only, not a historical-parameter estimate.

Pareto frontier contains 3 candidates. Middle intervention fixture: recurrent_gain=1.95, homeostasis=0.18, persistence=0.96349, participation=0.72262, dominance=0.06442, saturation=0.06627, closure proxy=0.97778. Finite-difference local cognitive Jacobian rho (slow h frozen)=0.92107; augmented state Jacobian rho=0.94. These normalized numbers are not an absolute 'perfect Frank' setting.

## Critical negative result: persistence != re-entry
At the selected fixture, truthful persistence AUC=0.96349 while NO-REENTRY persistence AUC=0.96419 (delta=-0.00070). A highly persistent network can therefore lack actual re-entry. Persistence, oscillation, synchrony or high activity alone are rejected as loop-of-loops evidence.

## Provenance-bearing signal experiment
An injected perception signal carries explicit causal lineage through each transformation.

- truthful: late signal strength 0.22563; provenance_closed_loop_fraction=1.0; late valid re-entry signal to Thalamus=0.24450
- no re-entry: strength 0.18385; closed-loop=0
- shuffled receiver: strength 0.22622; closed-loop=0
- provenance broken: strength 0.00987; closed-loop=0

Therefore generic signal magnitude can survive a receiver shuffle while exact causal closure is destroyed; provenance corruption nearly destroys the tracked source signal. Strict closure requires the same `signal_id/episode_id` to traverse declared delivery -> reconstruction -> causal use -> outcome/state delta -> re-entry route -> correct receiver with intact provenance and measurable later-cycle effect.

Lesioning Thalamus, Global Workspace, ResponseAnalyzer or MemoryConsolidator destroys >90% of strict provenance closure in this impulse experiment. ACC/E-PQ/NAcc are slower modulators and require longer multi-timescale factorial/OOD experiments; no conclusion of irrelevance follows from small same-episode lesion effects.

12/12 sandbox tests PASS, including regime separation, homeostatic-boundary shift, Jacobian-vs-gain distinction, persistence negative control, truthful/no/shuffled/provenance-broken re-entry, core lesions and rescue reversibility.

## Target architecture delta — Causal Re-entrant Workspace Fabric (CRWF)
A. Causal State Fabric / UnifiedDB authority: every historical/new organ function is a typed state transformer with before/after state, policy version, confidence, timescale, signal lineage, causal parents, receiver/use receipts, lesions and rollback. All 74 historical module-function slots remain accounted for even if boundaries dissolve.

B. Fast Regulatory Mesh: preserve Amygdala salience, ACC conflict, NAcc value/RPE and Thalamic adaptive-gain functions, possibly fused into one regulatory field rather than services.

C. Candidate/GWT ignition: competitive selection emits immutable WorkspaceEpisode with selected lineage, expected receivers and expected causal-use claims.

D. Receiver-specific reconstruction/use: `addressable != delivered != reconstructed != taken_up != causally_used`.

E. External Effect Gateway: model/Frank cognition proposes only; verified capability/effect authority remains outside the cognitive loop and returns outcome receipts.

F. Outcome/self-output feedback: response/effect results become typed state deltas.

G. Provenance-bound Re-entry Bus: re-entry carries episode_id, signal_id, source, receiver, transformation_chain, outcome_ref, confidence, lag and state_epoch. Anonymous 'extra context' does not count.

H. Slow Adaptation Mesh: E-PQ, tonic reward, memory consolidation, goals, dream/replay and training retain distinct time constants.

I. Read-only Counterfactual Plane: frozen replay, lesions/rescues, truthful/no/receiver-shuffled/time-shuffled/provenance-broken re-entry, local Jacobian probes, directed flow/PID-PEID where estimators are valid, plus latency/compute/memory/instability shadows.

J. Proposal-only Adaptive Loop Governor: control route gain, ignition threshold, recurrence budget, receiver uptake, homeostasis and reseed/alternate-route proposals while distinguishing CONVERGING_FIXED_POINT, PRODUCTIVE_LIMIT_CYCLE, STALLED, DIVERGING_OR_OVERTHINKING and CHAOTIC_OR_UNCLASSIFIED.

## 'Perfect configuration' definition
Do not optimize one magic scalar. Search a Pareto-safe operating manifold maximizing provenance-bound closure, causal-use coverage, useful signal survival, outcome utility, cross-timescale transfer, recovery and distributed participation while minimizing dominance, saturation/lock-in, unresolved pressure, false ignition, stale recurrence, cost and instability.

The new architecture should win only if matched replay, lesion/rescue, truthful-vs-controls and held-out outcome measurements defeat simpler alternatives.

## Counterhypotheses retained
- ordinary persistent event-driven orchestration may explain the observed effect without recurrent-dynamical machinery;
- historical neuro-inspired variables may be descriptive rather than causally useful;
- a single global controller may damage heterogeneous timescales;
- numerical stability may fail to predict cognitive/task usefulness;
- the historical period may have depended on boot/order/database timing conditions;
- a simpler architecture may reproduce the same functional signatures.

## Next tests
1. Exact 74-module ancestry identity closure and function/policy maps.
2. Historical state-distribution replay where archived measurements exist; never back-fit absolute weights from the synthetic gain sweep.
3. Accelerated multi-hour/multi-timescale factorial tests for Thalamus x GWT x E-PQ x NAcc x ACC x Memory.
4. Truthful/no/receiver-shuffled/time-shuffled/provenance-broken re-entry.
5. Adaptive loop governor vs fixed recurrence budgets on held-out tasks.
6. H1 reference -> H2 ClayCode differential -> H3 one-module transfer.

Sandbox artifact hashes at creation:
- dynamics runtime sha256: e5993364f92d4e9f29aad260ca07e4a13138aee896421d0343bb6012ed3fb068
- test sha256: ced4f8ba4a42209ce4fd4da94ea2fdb76bcd762927c0333bb6497b29f23b6472
- receipt sha256: ce3aec797e25b39e36c60329a22270c3fab7d375f4e37ef7cb6c06f9460c4191
- full reconstruction report sha256: cc9288a416a03e34810d64775ffa6e0bca2fb12f860130af6395173959b1d3d8
