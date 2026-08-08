# Retina PerceptualField — Mathematical Research Model

**Status:** OPEN MATHEMATICAL CANDIDATE  
**Purpose:** Convert the dissolved-perception idea into quantities that can be implemented, intervened on and falsified. No equation here is an owner-fixed architecture law.

## 1. State model

Let:

- `S_t` = physical sensor/source state at time t;
- `E_t = {e_t^k}` = timestamped evidence produced by transform k;
- `P_t` = distribution/set of current perceptual hypotheses;
- `W_t` = persistent world state;
- `M_t` = memory/ClayGraph context;
- `G_t` = active goals/task state;
- `A_t` = prior action/sensing action;
- `V_t` = visibility-state variables;
- `B_t` = bounded model/GWT-visible Assembly.

The target is a partially observed recurrent state estimator, not necessarily a literal Bayesian implementation.

## 2. Evidence-factorized hypothesis score

For a candidate perceptual hypothesis h, retain separate support terms:

`L_sensor(h) = sum_k q_k * log p(e_t^k | h, calibration_k)`

`L_temporal(h) = log p(h_t | h_(t-1), A_(t-1), V_(t-1))`

`L_world(h) = log p(h | W_(t-1), M_t)`

`B_goal(h) = task/goal-dependent computational bias`

Candidate total inference score:

`S(h) = L_sensor(h) + lambda_T L_temporal(h) + lambda_W L_world(h) + lambda_G B_goal(h) - C_complexity(h)`

Critical design law:

The terms remain separately observable even if the runtime computes an optimized fused representation. `B_goal` may affect selection/compute but must not be reported as increased sensor likelihood.

## 3. Precision/calibration

Each evidence source k has a precision/reliability state `q_k` derived from calibration, source class and current degradation.

Examples:
- detector reliability by source domain;
- OCR reliability under stylized text/blur;
- CLIP similarity calibration with realistic negatives;
- sensor quality under motion/low light;
- transform version/calibration age.

World prior has separate precision `q_W`.

A research diagnostic for expectation domination can be defined as:

`D_prior = max(0, L_world + goal_support) / (epsilon + |L_sensor| + max(0, L_world + goal_support))`

This exact formula is not frozen. The falsifiable question is whether an observable prior-dominance measure predicts misleading-prior errors and can support safer abstention/active sensing.

## 4. Set-valued perception

Do not always collapse to top-1.

Let normalized candidate probabilities/weights be `p_i`.

Useful uncertainty measures:

`H(P_t) = -sum_i p_i log p_i`

`margin = S(h_1) - S(h_2)`

`conflict = support(h_i) intersect contradiction(h_i)` or disagreement across evidence classes.

A candidate selection rule is:

- if evidence support is strong and margin/calibration sufficient -> `STABLE`;
- if multiple candidates remain plausible -> preserve set `P_t`;
- if evidence is weak and prior dominance high -> `UNKNOWN` or active sensing;
- if current evidence contradicts a stable prior belief -> `CONFLICT/REOPENED`.

Harness must compare this to simple calibrated top-k + abstention. Hyperposition is justified only if it adds measurable semantic/intervention value.

## 5. Temporal visibility model

For each persistent entity i, define visibility state:

`V_t^i in {VISIBLE_CONFIRMED, VISIBLE_UNCERTAIN, OCCLUDED, OUT_OF_FOV, ABSENT_EXPLICIT_NEGATIVE, UNKNOWN, SENSOR_DEGRADED, STALE}`.

Transition probability/rule depends on:

- current positive evidence;
- explicit negative evidence;
- camera/FOV geometry;
- occluder evidence;
- sensor health;
- elapsed time/state dynamics;
- prior action.

Key asymmetry:

`P(ABSENT | explicit_clear_negative)` should generally rise much faster than `P(ABSENT | no_detection)`.

This is the mathematical expression of `non-observation != absence`.

## 6. Evidence debt

Define evidence age/uncertainty for world assertion j:

`Debt_j = f(age_j, uncertainty_j, action_impact_j, risk_j, source_degradation_j, contradiction_j)`.

A high-debt belief can still remain in the world model, but it becomes increasingly expensive/unsafe to use for high-impact decisions without refreshing evidence.

Testable prediction:

Debt-aware refresh reduces stale-belief action errors at lower cost than globally refreshing all objects on a fixed schedule.

## 7. Prediction error

Avoid one untyped residual. Candidate vector:

`PE_t = [identity_error, attribute_error, spatial_error, relation_error, temporal_error, expected_visibility_error, source/provenance_error]`.

These components can route different responses:
- spatial error -> track/relocalize;
- OCR/text conflict -> OCR retry;
- identity error -> open-vocabulary/fine-grained detector;
- expected-visibility error after action -> GWT/action re-entry;
- provenance error -> reject/quarantine.

Falsifier: a scalar error must be kept if it produces equal routing/outcomes with less cost.

## 8. GWT ignition value

Candidate, not frozen:

`I_t = w_N * novelty + w_PE * prediction_error + w_U * uncertainty + w_G * goal_relevance + w_R * risk + w_C * crossmodal_conflict + w_A * action_consequence + w_D * evidence_debt - w_H * habituation - w_K * expected_global_compute_cost`

The correct object is a **decision policy**, not the exact linear formula.

Evaluation must use:
- important-event recall;
- workspace precision;
- downstream causal-use/outcome;
- token/model-call cost;
- latency.

Optimizing only `low ignition rate` is forbidden.

## 9. Active sensing / value of information

For a candidate sensing action a with possible result o:

`VOI(a) = E_o[ U(P_t, W_t) - U(P_(t+1), W_(t+1) | o,a) ]`

Decision utility can include task/safety value:

`J(a) = VOI(a) + task_value(a) + safety_value(a) - compute_cost(a) - latency_cost(a) - physical_risk(a)`

Choose:

`a* = argmax_a J(a)` when `max_a J(a) > 0`; otherwise stop/escalate/abstain according to policy.

Possible actions are not only camera motions. They include crop, resolution, OCR retry, detector choice, anchor refresh and model/GWT escalation.

## 10. Perceptual sufficiency / stopping

Define decision-relevant regret or uncertainty `R_t`.

A local episode may stop without GWT when:

`expected_regret(current local state) < tau_task`

and no hard interrupt condition is active.

A `PerceptualSufficiencyReceipt` can record:
- relevant task/goal;
- evidence epoch;
- uncertainty/conflict;
- skipped expensive operations;
- reason for no GWT escalation.

This makes ignored frames testable rather than invisible.

## 11. Sparse state update economics

Let:
- `F` = full-frame semantic computation cost;
- `d_t` = changed fraction / affected entities at t;
- `c_delta(d_t)` = delta processing cost;
- `c_anchor` = anchor refresh cost;
- `p_anchor(t)` = anchor policy.

Expected cost over T:

`C = sum_t c_delta(d_t) + sum_t 1[anchor_t] * c_anchor + GWT/model costs`.

Compare against:

`C_full = T * F`.

But cost gain is valid only if temporal correctness, static semantics and recovery remain within preregistered bounds.

## 12. Causal recurrence test

To show world/memory recurrence is useful, not merely correlated:

Factorial outcome Y:

`Omega_world_memory = Y(W=1,M=1) - Y(W=1,M=0) - Y(W=0,M=1) + Y(W=0,M=0)`.

Additionally compare:
- truthful recurrence;
- shuffled world/context recurrence;
- stale recurrence;
- lesion;
- rescue.

A gain that survives only truthful recurrence is stronger mechanistic evidence than `extra context helps`.

## 13. Representation sufficiency

For model-facing projection `B_t = project(P_t,W_t,G_t)` compare against full state X.

Measure:
- task loss delta;
- token/byte ratio;
- causal intervention equivalence;
- omitted-evidence error;
- reconstruction/provenance loss.

A useful Assembly is not merely smaller; it must be approximately sufficient for the current decision under stated error bounds.

## 14. Physical-lowering invariance

Let semantic trace `T_sem` be produced by different physical implementations L:

- standalone service;
- in-process CPU;
- Android/NPU;
- future event-camera path.

Required H1/H2/H3 property:

`distance_sem(T_sem(L1), T_sem(L2)) <= epsilon_defined`

for deterministic fixtures/interventions, except explicitly permitted nondeterminism.

This is the mathematical contract behind `physical boundary != semantic boundary`.

## 15. What would refute the mathematical architecture

The elaborate model should be rejected or simplified if:

- tracker/cache + simple calibrated state is information-equivalent;
- evidence/prior separation does not improve calibration or safety;
- typed visibility states do not change downstream correctness;
- active sensing policies do not beat fixed cascades;
- sparse updates fail to save meaningful compute on real workloads;
- bounded Assemblies lose too much visual information;
- recurrence gains vanish under clean held-out controls;
- replay/provenance overhead dominates runtime.

The mathematics is a tool for falsification and implementation, not a metaphysical description of seeing.
