# GRF + Hyperposition + GWT — mathematical foundation v0

Status: RESEARCH_CANDIDATE / NOT_VALIDATED
Date: 2026-08-23
Origin seed: `GRF + H^ -> Phi` / `GWT + Hyperposition -> higher-order cognition`
Scope: generic ClayCode cognition research. This document proposes a falsifiable mathematical model; it does not establish consciousness, AGI, superiority, or runtime correctness.

## Research question

Can explicit preservation of unresolved semantic alternatives (Hyperposition), when coupled to a bounded global workspace/broadcast-selection mechanism (GWT-like workspace), create measurable cognitive capability that neither mechanism provides alone?

The strong claim is not ordinary addition. The candidate is a coupled operator:

`Phi_t = G_t ⊕_Gamma Hhat_t`

where `Gamma` denotes an interaction between globally selected content and unresolved alternative structure.

Primary empirical statistic:

`Delta_synergy = J(G=1,H=1) - J(G=1,H=0) - J(G=0,H=1) + J(G=0,H=0)`

Promotion requires positive held-out interaction under matched parameter, token, latency, evidence/tool and training budgets.

## Mathematical objects

Let the semantic state space be `S subset R^d`. At time `t`, let admissible alternatives be `x_i in R^d`, `i=1..K`.

Hyperposition tensor:
`H_t = [x_1; ...; x_K] in R^(K x d)`.

Attach posterior mass and provenance:
`p_i >= 0`, `sum_i p_i = 1`, and `pi_i = provenance/evidence identity`.

Explicit hyperposition:
`Hhat_t = (H_t, p_t, Pi_t)`.

Invariant:
`Hhat_t != sum_i p_i x_i`.
The weighted mean is only one statistic and can be semantically invalid for multimodal alternatives.

## Workspace competition and broadcast

For current query/context `q_t`:

`s_i = q_t^T W_k x_i + lambda log(p_i + eps) + eta e_i`

`alpha_i = exp(s_i/tau) / sum_j exp(s_j/tau)`

`g_t = sum_i alpha_i W_v x_i`

`tau` is a competition temperature: low values sharpen selection; high values preserve broader competition.

## Hyperposition statistics that survive selection

Shannon uncertainty:
`S_t = -sum_i alpha_i log(alpha_i)`

Normalized uncertainty for `K>1`:
`S_norm = S_t / log(K)`

Effective number of live hypotheses:
`N_eff = exp(S_t)`

Semantic covariance:
`C_t = sum_i alpha_i (x_i - mu_t)(x_i - mu_t)^T`, with `mu_t=sum_i alpha_i x_i`.

Candidate uncertainty feature vector:
`u_t = [vec(C_t), S_t, S_norm, N_eff, max(alpha), prune_mass]`.

### Concrete finding: count-only uncertainty is insufficient

Any metric using only alternative count, e.g. `U_count=(K-1)/K`, cannot distinguish equal ambiguity from near-collapse.

For `K=3`:
- `p_A=(1/3,1/3,1/3)` -> `U_count=2/3`, `S_norm=1`, `N_eff=3`.
- `p_B=(0.98,0.01,0.01)` -> same `U_count=2/3`, but `S_norm≈0.1019`, `N_eff≈1.118`.

Therefore count-only uncertainty should not be treated as a sufficient probabilistic Hyperposition statistic.

## Coupled cognition operator

Define bilinear coupling:
`Gamma(g_t,u_t) = W_x (g_t tensor u_t)`.

Candidate state:
`Phi_t = sigma(W_g g_t + W_u u_t + Gamma(g_t,u_t) + b)`.

The key hypothesis is that the interaction term can encode task information unavailable from `g_t` or `u_t` alone.

## Evidence update

For new observation `o_(t+1)` under action/test `a_t`:

`p_(i,t+1) = p_(i,t) P(o_(t+1)|H_i,a_t) / sum_j p_(j,t) P(o_(t+1)|H_j,a_t)`.

Posterior mass controls cognitive competition/accessibility only. It does not mint canonical truth. Existing R6/receipt/authority rules remain binding.

## Discriminator / value-of-information law

Candidate action value:

`V(a) = E_p[U_task(a,H)] + kappa I(H;O_next|a) - c(a)`

Select:
`a*_t = argmax_a V(a)`.

This gives GRF R4 DISCRIMINATE an explicit information-value objective.

## Collapse law

Do not collapse on argmax alone. Candidate collapse guard requires:
1. `p_max >= theta_p`
2. `S_norm <= theta_H`
3. no remaining discriminator with positive expected information value above cost
4. required exact R6/provenance/authority receipt exists
5. no unresolved contradictory evidence above admitted threshold

Only then may exact collapse be proposed; canonical runtime validation remains authoritative.

## Resource law

Bound effective hypothesis load:
`N_eff <= N_max`.

When pruning is necessary, retain lost posterior mass:
`epsilon_prune = sum_(discarded i) p_i`.

Never silently convert pruned mass into certainty.

## Hypotheses

H1 — Explicit multimodality improves calibration/reversal recovery when the mean/MAP is invalid or later evidence reverses the leader.

H2 — Workspace x Hyperposition produces positive factorial interaction on tasks requiring global access to unresolved alternatives plus discriminator/action selection.

H3 — Bilinear/tensor coupling outperforms additive-only fusion on genuinely joint dependencies at matched budget.

H4 — Value-of-information collapse beats fixed confidence/entropy thresholds on utility vs compute.

H5 — Posterior/provenance-aware uncertainty predicts error and reversal better than alternative count alone.

## Strong counterhypotheses

C1 — Latent redundancy: a sufficiently capable transformer already represents the same distribution; explicit Hyperposition adds bookkeeping only.

C2 — Interference: preserving alternatives increases latency/noise enough to erase gains.

C3 — False-alternative preservation: Hyperposition stabilizes hallucinated or low-quality candidates.

C4 — Workspace bottleneck: competition collapses the diversity Hyperposition was meant to protect.

C5 — Goodhart/confound: positive interaction comes from extra parameters/tool calls rather than architecture.

Controls: match parameter count, inference tokens, evidence/tool budget, training data and stopping criteria.

## Thought experiments / calculations

### Mean-of-modes failure
Valid modes `x_1=-1`, `x_2=+1`, equal mass. `E[X]=0`, but `0` is not a valid mode. Preserving only the expectation destroys multimodality.

### Contradictory evidence reversal
Start `P(H1)=P(H2)=0.5`.
Observation 1 likelihoods `(0.8,0.2)` -> posterior `(0.8,0.2)`.
Observation 2 likelihoods `(0.1,0.9)` -> `P(H1|e1,e2)=0.08/(0.08+0.18)=0.3077`, `P(H2|e1,e2)=0.6923`.
An irreversible early collapse fails; maintained Hyperposition can reverse.

### Value-of-information gate
First cue accuracy `r1=0.65`; optional discriminator accuracy `r2=0.90`; probe cost `c`.
`V_commit=0.65`, simplified `V_probe=0.90-c`.
Probe is rational iff `c < r2-r1 = 0.25`.
At `c=0.10`, utility gain is `0.15`; at `c=0.30`, further investigation is irrational.

### Pure synergy existence proof
Let independent bits `G,H in {0,1}` and target `Y=G XOR H`.
`I(Y;G)=0`, `I(Y;H)=0`, while `I(Y;G,H)=1 bit`.
Joint coupling can therefore contain task information absent from either source alone. This is an existence proof, not evidence that current Clay has measured such synergy.

## Required 2x2 ablation

- B00: no workspace, no explicit Hyperposition
- G10: workspace only
- H01: Hyperposition only
- GH11: both

Primary statistic:
`Delta_synergy = J_11 - J_10 - J_01 + J_00`.

Task families:
1. multimodal target where mean is invalid
2. delayed contradictory evidence/reversal
3. cheapest-discriminator selection
4. source conflict with provenance differences
5. bounded branching plan
6. OOD analogical task preserving FACT_UNKNOWN
7. crash/re-entry ambiguity where unknown outcome may not be promoted

Measurements:
- correctness/expected utility
- probabilistic calibration
- reversal recovery
- false-collapse rate and time-to-correct-collapse
- entropy, N_eff, covariance rank/trace, prune mass
- unsupported-truth rate
- tokens/latency/memory and discriminator cost
- factorial interaction with bootstrap confidence interval
- simpler-baseline comparison

## Candidate ClayCode extensions — experimental only

Possible derived cognition slots/intrinsics:
- `hyper_weight(hp,candidate,p,"POSTERIOR")`
- `hyper_entropy(hp,value,"COMPUTED")`
- `hyper_effective_count(hp,value,"COMPUTED")`
- `hyper_prune_mass(hp,value,"COMPUTED")`
- `hyper_value_of_info(hp,test,value,"COMPUTED")`
- `workspace_couple(c,hp,workspace,interaction_id)`

Do not add these to canonical language from theory alone. Computed values remain cognition state, not external evidence/effect authority.

## Worker handoff

Theory worker:
- derive finite-state version and compare Shannon, Renyi and effective-count uncertainty;
- derive conditions where additive fusion is sufficient vs bilinear coupling required.

Eval worker:
- implement matched-budget 2x2 ablation;
- report interaction effect and confidence interval, not only GH score.

ClayCode/corpus worker:
- audit SFT examples for actual GRF/Hyperposition interactions;
- keep new examples experimental until ablation support.

Runtime worker:
- preserve one canonical state/effect authority;
- assess richer derived uncertainty while retaining exact receipt-bound collapse.

Adversarial worker:
- attack duplicated/correlated facets, hallucinated alternatives, provenance spoofing, high-K overload, early false consensus, late reversal and equal-score symmetry.

## Literature anchors

These motivate components; none independently proves the combined architecture.

- Global Neuronal Workspace review: https://pmc.ncbi.nlm.nih.gov/articles/PMC8770991/
- Ramsauer et al., modern Hopfield networks/attention: https://arxiv.org/abs/2008.02217
- Williams & Beer, partial information decomposition/synergy: https://arxiv.org/abs/1004.2515
- Friston et al., active inference/epistemic value: https://pmc.ncbi.nlm.nih.gov/articles/PMC5167251/
- Elhage et al., neural feature superposition/interference: https://www.transformer-circuits.pub/2022/toy_model/

## Promotion rule

Remain RESEARCH_CANDIDATE until:
1. mathematical objects are implemented without violating truth/effect authority;
2. matched-budget held-out ablations show robust positive interaction;
3. simpler baselines fail to explain the gain;
4. resource/interference penalties do not erase utility;
5. adversarial fixtures do not increase false truth collapse;
6. evidence is exact-source-bound and reproducible.

Until then, `GWT + Hyperposition -> higher-order cognition` remains a falsifiable research hypothesis, not an established fact.
