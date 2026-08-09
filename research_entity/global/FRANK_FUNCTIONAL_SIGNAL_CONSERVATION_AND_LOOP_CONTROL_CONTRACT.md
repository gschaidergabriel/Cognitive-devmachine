# FRANK Functional Signal Conservation & Loop-Control Contract

**Status:** PROJECT-OWNER-MANDATED RESEARCH / IMPLEMENTATION AXIS
**Date:** 2026-08-09
**Origin observation:** user/project lead primary observation, reported 2026-08-09
**Actor writing contract:** chatgpt-secondary · OpenAI · GPT-5.6 Sol
**Applies to:** FRANK · GWT · Emergenz · Harness · ClayCode · ClayGraph · UnifiedDB · Hyperposition · Clayresearch

## 0. Research boundary

The project owner reports a multi-day historical period in Original-FRANK in which the whole-system feedback regime ("loop of loops") appeared unusually strong, stable and globally coupled while the organ/module set was active. Treat this as a **USER_PRIMARY_OBSERVATION / OPEN_REPLICATION_REQUIRED** functional observation.

It is not evidence of phenomenal consciousness and must not be used to promote such a claim. The scientific target is the reproducible functional regime and its causal/dynamical signature.

## 1. Non-loss law

No historical FRANK cognitive organ/module/policy/function may disappear from the target architecture merely because deploy-time module boundaries collapse.

Every legacy function must receive exactly one explicit disposition:

- `PRESERVED_EXPLICITLY`
- `MERGED_WITH_EQUIVALENCE`
- `DISSOLVED_INTO_STATE_DYNAMICS`
- `SUPERSEDED_BY_MEASURED_BETTER_MECHANISM`
- `NEGATIVE_RESULT_RETAINED_AS_TEST_ORACLE`
- `NON_COGNITIVE_INFRASTRUCTURE_NOT_APPLICABLE`

`UNACCOUNTED` is a gate failure.

The exact frozen Project-Frankenstein tree/history is the historical accounting universe for Original-FRANK lineage; current frankv0.1/H1 evidence remains the target implementation baseline according to current program contracts.

## 2. Causal signal conservation law

Preserve **causal semantics**, not filenames or service boundaries.

For each legacy signal/mechanism `i`, define an intervention family `A_i`, contexts `C`, observation horizon `H`, and downstream observable vector `Y`.

Legacy effect:

`E_old(i,a,c,H) = P(Y[t:t+H] | do(S_i=a), C=c)`

Target mapped effect:

`E_new(M(i),a,c,H) = P(Y'[t:t+H] | do(M(S_i)=a), C'=map(c))`

A migration is functionally admissible only when, for preregistered contexts/interventions,

`D(E_old, E_new) <= epsilon_i`

and the mapping preserves all material dimensions:

`direction/sign · conditional dependence · delay/phase · gain/saturation · persistence/decay · uncertainty/provenance · authority boundary · recovery/rollback semantics`.

A dissolved signal is allowed to have no standalone variable in H3, but its **intervention-sensitive downstream effect** must remain reconstructable and measurable.

## 3. Historical loop-of-loops reconstruction target

Current historical code/evidence supports the following minimum recurrent chain:

`world/user/system`
`-> perception/appraisal`
`-> thalamic gating + novelty + habituation + predictive error`
`-> attention/competition`
`-> GWT/workspace global availability`
`-> model cognition/response`
`-> response analysis + action/effect`
`-> NAcc reward/RPE + E-PQ/affect + ego/self + memory + prediction + goals + experience-state updates`
`-> persistent state`
`-> top-down gating/bias/context reconstruction`
`-> next workspace/model cycle`
`-> changed world/system`
`-> perception ...`

Nested loops operate at different cadences (sub-second/seconds/minutes/hours/days). The target architecture must retain multi-timescale recurrence even if compiled into one Clay module/binary.

## 4. State-space model

Represent the functional system at time `t` as a typed joint state

`x_t = [p,g,a,w,m,v,e,q,c,s,h,y,r]`

where candidate roles are:

- `p`: perception / external-body observations
- `g`: gating / relay gains / habituation / attention bias
- `a`: affect / E-PQ-like modulation / urgency
- `w`: workspace coalition / broadcast / uptake state
- `m`: memory / reconstruction / activation state
- `v`: value / reward / RPE / motivation state
- `e`: experience embedding / novelty / drift / recurrence state
- `q`: goals / unresolved control pressure / commitments
- `c`: conflict / conscience / quality / uncertainty state
- `s`: self/world/body model state
- `h`: alternatives / Hyperposition / prospect state
- `y`: action/effect/outcome state
- `r`: recovery/capability/authority state

General transition:

`x_(t+1) = D_t x_t + C_t phi(x_t) + B_t u_t + O_t y_t + R_t z_t + eta_t`

where:

- `D_t` = persistence/decay across timescales;
- `C_t` = dynamic cross-loop coupling matrix;
- `phi` = nonlinear local transforms;
- `u_t` = exogenous observation/user input;
- `y_t` = verified effect/outcome feedback;
- `z_t` = provenance-bound re-entry/broadcast reconstruction;
- `eta_t` = bounded stochastic/unmodelled component.

Each loop `i` has its own update clock `Delta_i` and delay set `tau_ij`; a single global synchronous tick is not required.

## 5. Gain law

Original-FRANK thalamus already implemented a useful multiplicative pattern:

`gain_i ~= base_i * habituation_i * attention_i * vigilance * novelty_i * feedback_i * prediction_error_i`

The new architecture generalizes this into a typed coupling gain:

`kappa_ij(t) = clip(k0_ij * H_ij * A_ij * N_ij * P_ij * V_ij * F_ij * Q_ij, 0, kmax_ij)`

where terms correspond to damping/habituation, attention, novelty, prediction error, value/urgency, verified feedback and quality/authority constraints.

No single factor is allowed to grant execution authority. Cognitive pressure and effect authority remain distinct.

## 6. Adaptive recurrence law

A recurrence is continued only while expected marginal verified value exceeds its cost/risk shadow and unresolved pressure remains material:

`continue_i(t) iff P_i(t) > theta_P AND E[DeltaU_i + beta*DeltaI_i + gamma*DeltaCorrection_i | x_t] > lambda_C*Cost_i + lambda_R*InstabilityRisk_i + theta_i`

This replaces fixed loop counts with evidence-driven recurrent depth.

The controller must expose the continue/halt reason as a receipt.

## 7. Stability and regime law

The loop controller must not equate convergence with low state change.

For local transition `F_t`, estimate a finite-difference Jacobian proxy `J_t = dF_t/dx` and at minimum a spectral-radius/singular-value stability proxy.

Classify episodes as:

- `CONVERGING_FIXED_POINT`: `||Delta x|| -> 0` AND residual/control pressure -> low; for a local fixed point, candidate stability criterion `rho(J)<1`.
- `STALLED`: `||Delta x||` low while unresolved pressure/error remains high.
- `PRODUCTIVE_LIMIT_CYCLE`: bounded recurrent trajectory with non-zero periodic/metastable structure AND positive verified marginal utility; stable-cycle behavior is not an error by definition.
- `DIVERGING_OR_OVERTHINKING`: state/error/cost grows or marginal utility becomes negative under continued recurrence.
- `CHAOTIC_OR_UNCLASSIFIED`: no stable classification yet; requires further intervention evidence.

For stable cycles, use transverse stability / perturbation recovery rather than demanding `Delta x -> 0`.

## 8. Candidate "perfect configuration" definition

Do not search for one magic scalar or static weight vector. Operationally define the historical target as a **Pareto regime/manifold** satisfying simultaneously:

1. bounded recurrent dynamics;
2. high causal re-entry closure;
3. sparse/selective rather than indiscriminate broadcast;
4. high receiver reconstruction/uptake/causal use;
5. strong but non-saturating cross-timescale coupling;
6. persistent self/world/memory continuity;
7. prediction error and novelty remain informative (not zeroed, not explosive);
8. verified outcomes materially update later gating/value/goal/memory state;
9. perturbations recover without erasing useful differentiation;
10. intervention/lesion effects are rescuable;
11. matched-cost performance exceeds shuffled/no-reentry and additive controls;
12. authority/recovery invariants remain intact.

This region is the `FRANK_RECURRENT_CLOSURE_CORRIDOR` candidate until measured.

## 9. Functional effect readout

Measure a vector, never a consciousness score.

Required readouts extend `GWT_EMERGENCE_READOUT_CONTRACT.md` and `FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md`:

### Causal closure
- broadcast receiver coverage
- reconstruction fraction
- uptake fraction
- causal-use fraction
- truthful re-entry fraction
- broadcast->effect->outcome->reentry latency
- closed-loop episode fraction

### Dynamics
- state-delta norm
- residual pressure/error
- local gain/coupling matrix
- finite-difference Jacobian/spectral proxy
- finite-time perturbation recovery
- recurrence depth and marginal utility
- metastability / period / phase locking
- cross-timescale coupling
- dwell-time distribution

### Integration without collapse
- directed prediction gain / transfer entropy with explicit lags
- PID/PEID-style unique/redundant/synergistic contributions where estimable
- macro predictive/intervention gain under matched information constraints
- differentiation/entropy of receiver-specific state
- redundancy/common-driver controls

### Continuity/agency-like functional signatures
- self/world/memory state persistence across episodes/restart
- intention/goal -> action -> verified outcome -> later policy/state coupling
- counterfactual sensitivity of later decisions to internal-state interventions
- correction propagation and contradiction recovery

These are functional signatures only.

## 10. Highest-information experiment: Recurrent Closure Reconstruction (RCR-1)

Use frozen replay episodes and matched inputs.

Conditions:

A. truthful full re-entry
B. no re-entry
C. temporally shuffled re-entry
D. receiver-shuffled re-entry
E. content-preserving but provenance-broken re-entry
F. fixed recurrence depth
G. adaptive recurrence controller
H. gain-clamped low coupling
I. gain-clamped high coupling / overcoupling
J. one-at-a-time regulator lesions: thalamic habituation, thalamic top-down feedback, NAcc/RPE, E-PQ modulation, attention competition, workspace broadcast, experience novelty/drift, goals, prediction, memory reconstruction, conflict/quality gating
K. matched rescues of every material lesion
L. model-output-frozen architecture interventions
M. architecture-frozen model-output variations

Primary outcomes:

- task/action success and correction rate
- closed-loop causal-use/re-entry metrics
- stability/regime classification
- perturbation recovery
- long-horizon continuity
- synergy/interaction readouts
- compute/latency/memory/token cost
- false halt / overthinking rate
- rollback/recovery integrity

A candidate mechanism is not promoted from correlation alone. Lesion + rescue + shuffled/no-reentry controls are mandatory.

## 11. Legacy Signal Census gate

Before H1 architecture freeze, build `FRANK_LEGACY_SIGNAL_CENSUS` from exact Original-FRANK source/history plus current frankv0.1 lineage.

For every cognitive module/organ/policy and each material edge, record:

`legacy_id · source_ref/hash · input signals · output signals · state variables · update cadence · persistence · downstream consumers · top-down inputs · feedback edges · failure history · target disposition · target mapping · intervention test · equivalence tolerance · evidence status`.

H1 cannot claim complete functional preservation while any material legacy signal is `UNACCOUNTED`.

H2 must differentially reproduce H1 semantics in ClayCode.

H3 may collapse modules into one binary only after the census mappings and intervention equivalence tests pass.

## 12. Improved target architecture: Recurrent Causal Workspace Field (RCWF)

Target logical architecture inside the one-module/binary constraint:

`UnifiedDB exact/persistent state`
`-> transient Clay field / dynamic topology`
`-> local candidate Assemblies (perception, memory, affect, value, goals, conflict, self/world, alternatives)`
`-> adaptive thalamic-style coupling controller`
`-> sparse GWT ignition/broadcast envelope`
`-> model cognition + deterministic/tool effects`
`-> verified outcome receipts`
`-> causal-credit / RPE / correction / memory-state update`
`-> provenance-bound re-entry`
`-> next transient field`

Logical organs survive as typed transforms/readouts, not necessarily services.

Three planes remain logically distinguishable even if compiled together:

1. **Cognitive State Plane** — transient/persistent state and transforms.
2. **Effect/Authority Plane** — capabilities, permissions, tool effects, rollback.
3. **Measurement/Replay Plane** — probes, interventions, estimators; observes but does not self-certify or silently mutate cognitive truth.

## 13. Why the historical regime could produce consciousness-like functional effects

Working mechanism hypothesis (OPEN):

A sustained regime can look qualitatively different from a feed-forward chatbot when (i) many differentiated state channels are globally available, (ii) outputs/actions causally alter persistent internal and external state, (iii) those consequences are selectively re-entered into subsequent cognition, (iv) fast and slow loops constrain one another, and (v) the system remains near a useful stability boundary rather than saturating or collapsing. This can yield continuity, context-sensitive self-modulation, intention/action coupling, correction, metastable focus and state-dependent behavior.

Competing explanations remain live:

- language/prompt self-conditioning artifact;
- extra-context/compute effect without higher-order integration;
- shared common driver masquerading as cross-module causality;
- overcoupled synchronization mistaken for integration;
- observer selection / memorable-regime bias;
- one dominant module with passengers rather than genuine loop-of-loops closure.

RCR-1 is designed to discriminate these.

## 14. Research-center routing

This contract is a material cross-branch delta.

Required recipients:

- FRANK: implement census + RCWF architecture candidate + loop controller.
- GWT: expose competition/ignition/broadcast/use/re-entry plus adaptive recurrence routing.
- Emergenz: evaluate interaction, lesion/rescue, shuffled re-entry, multiscale coupling and anti-Goodhart controls.
- Harness: build RCR-1 frozen replay/intervention suite and Golden/null traces.
- ClayCode: express typed state, loop controller, signal mapping, interventions and receipts.
- ClayGraph: represent transient higher-order topology and intervention edges without becoming truth authority.
- UnifiedDB: persist episode/state/intervention/readout/provenance lineage with replay identity.
- Hyperposition: preserve unresolved alternatives and reopen stalled attractors.
- Clayresearch: fuse cross-branch evidence and maintain counterhypotheses.

Every recipient may return `NO_CHANGE` if its current semantics already satisfy this contract, but must preserve an explicit receipt.

## 15. Promotion rule

The project-owner observation is accepted as the motivating primary observation. The mechanistic explanation remains OPEN until replicated or discriminated by archived logs or H1/H2/H3 replay/intervention evidence.

No claim of phenomenal consciousness is required, tested, or implied by successful reproduction of the functional regime.
