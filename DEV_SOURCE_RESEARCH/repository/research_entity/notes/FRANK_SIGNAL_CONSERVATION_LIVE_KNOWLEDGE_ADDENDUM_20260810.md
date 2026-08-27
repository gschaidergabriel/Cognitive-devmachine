# FRANK Signal Conservation Audit — Live-Knowledge Addendum 2026-08-10

Status: `LIVE_PRIMARY_RESEARCH_DELTA`
Actor: `chatgpt-secondary`
Parent audit: `research_entity/notes/FRANK_FUNCTION_SIGNAL_CONSERVATION_AUDIT_20260810_CHATGPT.md`
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Purpose

Second recursive external-knowledge refresh after the initial function/signal-conservation audit. This addendum asks whether newer 2026 evidence changes the architecture conclusion.

## 2026 primary/recent evidence

### 1. Reward timing is itself a learning variable

Burke et al., Nature Neuroscience 2026, `Duration between rewards controls the rate of behavioral and dopaminergic learning`, DOI `10.1038/s41593-026-02206-2`.

Reported result: across tested mouse conditions, behavioral and dopaminergic learning rates depended on the duration between rewards/punishments; the authors propose a retrospective-learning model to explain this.

Frank implication: preserve outcome/reward timing, inter-outcome interval, credit lag and adaptation cadence as explicit state. A reward scalar without timing can be functionally lossy even when total reward is unchanged.

### 2. Heterogeneous dopamine signals are context/phase gated

Jang et al., Nature Neuroscience 2026, `Acetylcholine demixes heterogeneous dopamine signals for learning and moving`, DOI `10.1038/s41593-026-02227-x`.

Reported result: relative acetylcholine/dopamine dynamics differentiated whether dopamine predicted later learning or movement vigor in the studied rat task.

Frank implication: the engineering abstraction should permit a signal's causal meaning to depend on receiver/context and relative timing. Do not assume a single scalar `dopamine/reward` value has invariant semantics independent of phase/receiver state.

This is evidence about biological systems, not a requirement to imitate acetylcholine. The transferable principle is **multiplexed signal + contextual demixing**.

### 3. Predictive functions can be distributed rather than organ-local

`Desegregation of neuronal predictive processing`, Nature Communications 2026, DOI `10.1038/s41467-026-70347-w`.

Reported result: in recurrent-network modeling and experimental comparison, prediction and prediction-error representations were not restricted to specialized cell classes; high-dimensional predictive functions could be distributed.

Frank implication: this supports the project's `EMERGENT_DISTRIBUTE` option. It does **not** weaken the conservation gate. If an old organ boundary disappears, the distributed successor still needs state/signal lineage, intervention handles and functional differential evidence.

### 4. Recurrent depth helps reasoning but overthinking is real

Kohli et al., arXiv 2026, `Loop, Think, & Generalize: Implicit Reasoning in Recurrent-Depth Transformers`, arXiv:2604.07822.

Reported result in controlled recurrent-depth transformer experiments: increasing inference recurrence can extend reasoning depth, but excessive recurrence can degrade predictions (`overthinking`).

Frank implication: recurrence count itself is not quality. Preserve adaptive continuation/halt control with unresolved residual plus expected marginal value/cost. This independently supports Frank's `DIVERGING_OR_OVERTHINKING` regime and bounded recurrence.

### 5. Looped models require explicit stability control

Prairie et al., arXiv 2026, `Parcae: Scaling Laws For Stable Looped Language Models`, arXiv:2604.12946.

Reported result: looped architectures can suffer residual explosion/loss spikes; their proposed architecture constrains injection spectral norms and shows improved stability/quality in their experiments.

Frank implication: preserving recurrence without preserving gain/damping/stability state is unsafe. Per-path/per-route gain and stability controls are not optional observability if the loop core is recurrent.

### 6. Different recurrence phases can converge to distinct cyclic fixed points

Blayney et al., arXiv 2026, `A Mechanistic Analysis of Looped Reasoning Language Models`, arXiv:2604.11791.

Reported result: studied recurrent blocks can follow consistent cyclic trajectories with different layers in the cycle converging to distinct fixed points; attention behavior can stabilize across recurrences.

Frank implication: do not insist that all useful Frank recurrence converge to one scalar/fixed point. Preserve phase/cycle identity and support `PRODUCTIVE_LIMIT_CYCLE`/metastable regimes. A single state-delta norm can hide phase-specific structure.

### 7. Long-horizon agent learning benefits from finer credit assignment

Tao et al., arXiv 2026, `TRACE: Turn-level Reward Assignment via Credit Estimation for Long-Horizon Agents`, arXiv:2607.13988.

Reported result: the proposed method derives denser turn-level rewards from state-value changes at tool-call boundaries and reports stronger long-horizon tool-use learning than outcome-only assignment in its experiments.

Frank implication: outcome verification remains necessary, but one terminal reward should not automatically credit every active state/turn. Preserve causal-use/step identity and uncertainty so credit can remain sparse when evidence is weak and become denser only through a validated estimator/counterfactual mechanism.

## Updated architecture conclusion

The 2026 refresh **strengthens**, not weakens, the initial signal-conservation conclusion:

1. preserve multidimensional/feature-specific state where historical function depended on it;
2. preserve timing/phase/lag as first-class causal metadata;
3. permit distributed implementation, but demand causal lineage and intervention evidence;
4. preserve gain/damping/stability controls for recurrence;
5. preserve regime/phase identity rather than forcing one fixed-point scalar;
6. keep outcome verification separate from credit assignment;
7. avoid universal scalar reward/ignition/convergence metrics.

No evidence found justifies reverting to the original multi-service topology. The stronger design is still **one executable loop-core with typed multirate internal state**, plus exact SignalConservationReceipts and matched Original/Perfected/One-Module differential tests.

## New test obligations added by this refresh

- **Inter-reward interval invariance falsifier:** same number/total reward, different reward spacing; compare old/successor learning trajectories.
- **Phase-demixing test:** same reward/control scalar under different receiver/context phase; test whether successor preserves context-dependent downstream function where baseline does.
- **Distributed-successor intervention test:** if an old organ is EMERGENT_DISTRIBUTE, lesion the distributed causal path rather than a service name and rescue it.
- **Loop phase test:** compare recurrence states by phase, not only global delta norm; detect productive cyclic fixed-point structure versus true stagnation.
- **Gain-instability stress:** sweep cross-loop injection/gain and damping, record residual explosion, permanent ignition, diversity collapse and recovery.
- **Terminal-vs-step-credit test:** identical final outcome with different useful/harmful intermediate actions; compare outcome-only credit against receipt-gated finer credit while guarding Goodhart leakage.

## Epistemic boundary

The neuroscience evidence is used to generate engineering hypotheses about dimensionality, timing, demixing and control. It is **not** evidence that Frank should copy biological anatomy, and it is not evidence of phenomenal consciousness.
