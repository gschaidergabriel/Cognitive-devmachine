# FRANK as a Loop-of-Loops — Recurrent Reasoning / Dynamical-Systems Transfer

Status: OPEN_RESEARCH_NOTE_NOT_CANONICAL_PROMOTION  
Date: 2026-08-09  
Origin actor: chatgpt-secondary  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346  
Operational target: Frank v0.1 on the Ubuntu developer system only; Android/mobile/edge are outside this v0.1 research/release path unless explicitly reintroduced by the owner.

## Research question

Test the owner hypothesis that FRANK should be modeled not as one loop module but as a complex recurrent dynamical system made of nested, interacting loops at different timescales, and that methods used to analyze/stabilize recurrent-depth reasoning models may transfer to FRANK's whole-system control and emergence research.

## Finding 1 — the architectural analogy is materially supported

Current FRANK runtime is already a top-level recurrence over persistent state:

observation -> self/world/memory assembly -> possibility/prospection -> control pressures -> workspace selection/broadcast -> intent/action -> verified outcome -> causal credit -> learning/state delta -> next cycle.

The next cycle consumes persistent effects of the previous one, so the system is not merely a stateless orchestration DAG. It is a stateful recurrent system. Within it sit faster and slower loops: attention/workspace selection, prospection, adaptive recognition/learning, outcome-credit learning, memory/graph activation, replay/consolidation, research/harness feedback, and long-timescale goal/self/world updates.

Therefore the closest machine-learning analogy is not a single looped Transformer block. It is a hierarchical/multiscale recurrent control system (a loop-of-loops) with heterogeneous state variables, timescales and authority boundaries.

## Finding 2 — external recurrent-reasoning work transfers at the mechanism level

Primary-source evidence reviewed:

- Kohli et al., arXiv:2604.07822, Loop, Think, & Generalize: recurrent depth can scale inference-time computation and extrapolate reasoning depth, but excessive recurrence produces overthinking.
- Blayney et al., arXiv:2604.11791, A Mechanistic Analysis of Looped Reasoning Language Models: many looped models approach cyclic fixed points; attention behavior stabilizes; block size, input injection and normalization affect stability.
- Prairie et al., arXiv:2604.12946, Parcae: looped models can be treated as nonlinear dynamical systems over recurrent state. A linearized stability criterion links divergence to the recurrent operator; constraining the recurrent dynamics and normalizing input injection improves stability.
- Bae et al., NeurIPS 2025, Mixture-of-Recursions: recursion depth can be routed adaptively rather than fixed uniformly.
- Graves, arXiv:1603.08983, Adaptive Computation Time: learned halting can allocate different amounts of recurrence to different inputs.
- Bai et al., arXiv:1909.01377, Deep Equilibrium Models: recurrent/deep computation can be characterized by fixed-point behavior.
- Wang et al., arXiv:2506.21734, Hierarchical Reasoning Model: slow and fast recurrent modules are one concrete example of multiscale recurrent reasoning. This evidence is task-specific and does not prove FRANK equivalence.

Transfer claim: these papers do not prove FRANK itself reasons in the same latent way. They provide a mathematically relevant toolkit for measuring and controlling recurrent state dynamics.

## Finding 3 — emergence measurement and loop regulation must remain separate

Existing Clay GWT/Emergence contracts already correctly state recurrence != emergence and require typed multi-measure readouts, interventions, lesion/rescue, re-entry controls and cross-timescale coupling.

The new proposal is to add a dynamics/stability readout layer over the whole FRANK loop network. This layer must observe and regulate dynamics without turning an emergence score into truth or authority.

## Proposed LoopDynamicsReadout

Candidate fields:

- loop_id / loop_family / timescale
- state_epoch / basis_epoch
- state_delta_norm
- unresolved_error_or_pressure
- input_injection_norm
- recurrence_count / recurrence_budget
- local_gain_estimate
- local_jacobian_or_linearized_spectral_radius_proxy
- convergence_rate
- phase_lock / oscillation_period
- attractor_class = CONVERGING_FIXED_POINT | PRODUCTIVE_LIMIT_CYCLE | STALLED | DIVERGING | CHAOTIC_OR_UNCLASSIFIED
- marginal_utility_of_next_recurrence
- overthinking_index
- stagnation_index
- cross_loop_coupling_strength
- intervention_applied
- halt_or_continue_reason
- rollback/checkpoint reference
- evidence/provenance/uncertainty

No single field is an emergence score.

## Four control regimes

### A. Healthy convergence
State updates shrink while task error/uncertainty/pressure also shrinks.
Action: continue until marginal utility falls below threshold, then halt/commit.

### B. Productive bounded cycle
State follows a bounded periodic/metastable trajectory and continues producing information gain, useful alternation, or causal progress.
Action: preserve; do not force every healthy recurrent process into a fixed point.

### C. Unstable / overthinking loop
State norm, update norm, contradiction, latency or error grows; quality degrades as recurrence continues.
Candidate controls: reduce loop gain/coupling, normalize/reweight input injection, shorten recurrence budget, apply damping/leaky integration, break phase lock, rollback to last-known-good state, or route to an alternate branch.

### D. Dead / stalled loop
State change is near zero while unresolved error/pressure remains high. This is not successful convergence.
Candidate controls: increase selective input injection/gain, retrieve new evidence, reopen a preserved Hyperposition branch, perturb/reseed within bounds, change routing, reset the local state from checkpoint, or escalate to a slower/higher-level loop.

This distinction is essential: low delta with low residual error is convergence; low delta with high residual error is stagnation.

## Hypothesis: reinterpretation of historical FRANK readouts as loop-control variables

OPEN and falsifiable; not yet a semantic promotion.

- Thalamus channel gain -> candidate per-loop/per-route gain control.
- Thalamus habituation -> candidate damping/refractory mechanism against repeated nonproductive activation.
- NAcc phasic/tonic state -> candidate value/utility signal for persistence vs disengagement.
- GWT ignition/focus -> candidate admission/selection/continuation router for expensive recurrent processing.
- experience-vector novelty -> candidate exploration/reseed signal to escape stale attractors.
- Amygdala urgency/category -> candidate pressure/time-budget modulation for recurrence allocation.

These mappings must be tested against historical behavior and lesions; neuro-inspired naming alone is not evidence.

## Mathematical working model

For a coupled loop-state vector x_t, external/current evidence u_t and nonlinear interaction R:

x_(t+1) = A_t x_t + B_t u_t + R(x_t, u_t)

A_t represents persistence and cross-loop coupling; B_t represents evidence/input injection.

Around a local operating point, estimate a Jacobian J_t. For a fixed-point-like regime, a local contraction proxy rho(J_t) < 1 is a useful stability condition. rho >= 1 is not automatically failure because bounded intentional oscillations/limit cycles exist, so classification must combine state norms, residual task error, periodicity, outcome utility and interventions.

Adaptive recurrence should optimize useful outcome improvement per unit cost, not recurrence count itself:

continue iff expected_delta_utility(next_loop) > cost + instability_risk and unresolved_pressure remains material.

## Executable toy check

A six-state synthetic coupled-loop linearization (perception, memory, workspace, prospection, action, learning) was tested locally as mechanism sanity-check only.

- unconstrained coupling spectral radius: 1.14816
- state norm with constant bounded input at step 30: 53.334
- same coupling scaled to spectral radius 0.92: state norm at step 30: 1.505

A separate 2D rotation with radius 1 maintained constant norm, demonstrating why bounded cyclic behavior must not be mislabeled as divergence simply because it does not converge to a single fixed point.

This toy result is control-theory illustration, not FRANK runtime evidence.

## Highest-information FRANK experiment

Target: Ubuntu developer system / H1 reference harness first, then differential H2.

1. Define an explicit state vector per material loop family from existing typed state/readouts.
2. Log per-cycle delta, residual pressure/error, outcome utility and cost.
3. Use frozen replay episodes and small controlled perturbations to estimate local finite-difference Jacobian/coupling proxies.
4. Classify each episode into convergence / productive cycle / stalled / divergent-unclassified.
5. Lesion candidate regulators independently: gain, habituation, ignition/selection, novelty, value/persistence, urgency/time-budget.
6. Rescue the lesion with the corresponding controller and measure recovery.
7. Compare fixed recurrence budgets against adaptive continue/exit routing.
8. Test truthful re-entry vs shuffled/no re-entry while holding external input fixed.
9. Measure task accuracy, correction time, recurrence count, latency, compute, memory, instability, false halts and recovery success.
10. Preserve all negative results; no controller is promoted because its biological analogy sounds plausible.

## Counterhypotheses

H0-A: FRANK's apparent recurrence benefit is primarily persistent event-driven orchestration; loop-transformer mathematics adds little beyond conventional control/queueing analysis.

H0-B: A single global stability controller will damage useful heterogeneous timescales; only local/typed controllers should exist.

H0-C: Historical Thalamus/NAcc/Amygdala variables are descriptive legacy readouts and do not causally improve loop regulation when intervened upon.

H0-D: Fixed-point/spectral-radius diagnostics predict numerical stability but not cognitive usefulness; outcome-gated adaptive control is required.

## Research implication

Promote the loop-of-loops view as an OPEN architecture/research hypothesis and add its measurements to future FRANK/GWT/Emergenz/Harness work. Do not alter FRANK's harness from this note. Implementation changes remain Research-Entity-owned proposals/tests and must be validated on the Ubuntu developer system.

No Android/mobile/edge work is required for this v0.1 hypothesis.