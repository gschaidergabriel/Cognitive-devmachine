# Hyperposition decision geometry addendum v1

Status: RESEARCH_CANDIDATE / NOT_VALIDATED
Parent: `HYPERPOSITION_GWT_INFORMATION_GEOMETRY_V1.md`

## 1. Why semantic conflict is not enough

Two hypotheses can be semantically very different while implying the same optimal action. Conversely, two superficially similar hypotheses can imply opposite high-stakes actions.

Therefore Hyperposition should distinguish:

`EPISTEMIC UNCERTAINTY` — how posterior mass is distributed;

`SEMANTIC TENSION` — how far the candidate meanings are apart;

`DECISION TENSION` — how differently the candidates value available actions.

## 2. Semantic tension identity

For normalized semantic states `||x_i||=1` and posterior `p_i`, let:

`mu_x = sum_i p_i x_i`.

Define:

`Theta_X = 1 - ||mu_x||^2`.

Then exactly:

`Theta_X = (1/2) sum_(i,j) p_i p_j ||x_i-x_j||^2`.

Proof:

`(1/2) sum_ij p_i p_j (||x_i||^2+||x_j||^2-2 x_i^T x_j)`

`= 1 - (sum_i p_i x_i)^T(sum_j p_j x_j)`

`= 1-||mu_x||^2`.

Thus the O(K^2) expected pairwise squared distance can be computed in O(Kd) from the weighted mean when embeddings are unit-normalized.

This scalar is diagnostic only. Embedding geometry is not semantic truth.

## 3. Decision / utility geometry

Let there be M admitted actions. For each hypothesis define its utility vector:

`u_i = [U(a_1,H_i), ..., U(a_M,H_i)] in R^M`.

Posterior mean utility vector:

`mu_U = sum_i p_i u_i`.

Define decision tension:

`Theta_U = sum_i p_i ||u_i-mu_U||^2`.

Equivalent identity:

`Theta_U = (1/2) sum_(i,j) p_i p_j ||u_i-u_j||^2`.

Interpretation:
- high entropy + low `Theta_U`: uncertainty exists, but hypotheses mostly agree about action values;
- high entropy + high `Theta_U`: unresolved state materially changes decisions;
- low entropy + high tail regret: a rare hypothesis may still deserve workspace access;
- low entropy + low `Theta_U`: near decision collapse.

`Theta_U` is smoother than merely comparing argmax action labels.

## 4. Expected utility without collapse

Current-belief action value:

`V_now = max_a sum_i p_i U(a,H_i)`.

Choose:

`a* = argmax_a sum_i p_i U(a,H_i)`.

This does not require selecting one H_i as true.

Therefore:

`ACTION_COMMIT != EPISTEMIC_COLLAPSE`.

## 5. Expected Value of Perfect Information (EVPI)

If the hypothesis were revealed perfectly before acting:

`V_PI = sum_i p_i max_a U(a,H_i)`.

Define:

`EVPI = V_PI - V_now`.

By `E[max] >= max E`:

`EVPI >= 0`.

Interpretation: EVPI is the maximum one-step decision value available from completely resolving the current Hyperposition, before paying information-acquisition cost.

Powerful special case:

`EVPI = 0`

means perfect resolution cannot improve the current decision. The system may act while keeping the Hyperposition epistemically open.

This is a stronger stopping signal than entropy alone.

## 6. Expected Value of Sample Information (EVSI)

For a discriminator/test d with possible observation o:

`EVSI(d) = E_o[ max_a E[U(a,H)|o,d] ] - V_now`.

Net decision value:

`V_task(d) = EVSI(d) - C(d)`.

For explicitly epistemic/research goals, an information-value term can be added without pretending it is task utility:

`V_research(d) = EVSI(d) + kappa*EIG(d) - C(d)`

where `EIG(d)=I(H;O_d)`.

Do not double-count information gain as task benefit unless the objective explicitly values knowledge itself.

## 7. Hypothesis-specific regret contribution for GWT access

Let `a*` be the current posterior-optimal action.

For each hypothesis:

`R_i = p_i [max_a U(a,H_i) - U(a*,H_i)]`.

A low-probability state with catastrophic regret can have large `R_i` and deserve workspace access even when `p_i` is small.

Candidate access score:

`s_i = gamma log(p_i+eps) + lambda_R R_i + salience_i + novelty_i`.

`alpha_i = softmax(s_i/tau)`.

Again:

`alpha_i` controls cognition/access; it must not overwrite `p_i`.

## 8. Value-directed compression distortion

Let compressed belief/view `Htilde` induce action `a_tilde`.

Define decision regret under the original full belief:

`D_V(H,Htilde) = V_now - sum_i p_i U(a_tilde,H_i)`.

Compression objective:

`Htilde* = argmin_Htilde [D_V(H,Htilde) + beta L(Htilde)]`.

This directly expresses the token/decision tradeoff.

Posterior top-k is only one heuristic; it is not generally optimal for `D_V`.

## 9. Exact binary relative-logit quantization bound

For binary Hyperposition define log-odds:

`L = log(p/(1-p))`

and `p=sigma(L)`.

Round L to nearest grid of width `delta`:

`Lq = delta*round(L/delta)`.

Then:

`|Lq-L| <= delta/2`.

Since the logistic derivative satisfies:

`max_L sigma'(L) = 1/4`,

by the mean value theorem:

`|sigma(Lq)-sigma(L)| <= (1/4)(delta/2) = delta/8`.

For candidate H1 `delta=0.25 nat`:

`|p_q-p| <= 0.03125`.

So the maximum binary probability error is bounded by 3.125 percentage points, independent of L.

This is an analytic bound, not a benchmark of downstream cognition.

## 10. Adaptive quantization option

A fixed delta may be wasteful when posterior margin is large and risky near ties.

Research alternative:

`delta_t = clamp(delta_min, k*margin_logit, delta_max)`

or select the coarsest delta whose worst-case decision regret remains below epsilon.

The second option is preferred conceptually because it ties precision to downstream value, not probability aesthetics.

Quantization metadata should live in the canonical bundle/schema when possible rather than being repeated in every ClayCode string.

## 11. Four-dimensional diagnostic map

A compact research diagnostic for a Hyperposition is:

`Z_H = (S, Theta_X, Theta_U, EVPI)`.

Interpretation examples:

1. `S high, Theta_X low, Theta_U low, EVPI low` -> redundant/paraphrased alternatives; compress aggressively.
2. `S high, Theta_X high, Theta_U low, EVPI low` -> genuine semantic disagreement but same practical action; act, preserve epistemic openness if relevant.
3. `S high, Theta_X high, Theta_U high, EVPI high` -> true consequential ambiguity; prioritize discriminator.
4. `S low, Theta_U high, EVPI high` -> low-probability high-consequence tail; do not discard by top-p alone.
5. `S low, Theta_X low, Theta_U low, EVPI ~0` -> safe near-collapse/low-value ambiguity, subject to R6 truth law.

None of these diagnostics independently promotes truth.

## 12. Experimental falsifiers

The decision-geometry hypothesis fails if, under matched budgets:
- `Theta_U`/EVPI do not outperform entropy/count for predicting when further evidence changes optimal action;
- value-directed compression does not lower decision regret per token versus top-k/top-p;
- risk/regret-based workspace access increases false alarms or harms utility;
- adaptive quantization does not improve token/error tradeoff over fixed delta;
- H0/H1 indirection costs exceed any saved generation/context cost.

Until tested, all formulas in this addendum are candidate control mathematics, not canonical Clay semantics.