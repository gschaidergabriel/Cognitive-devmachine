# Hyperposition × GWT — information-geometric mathematical foundation v1

Status: RESEARCH_CANDIDATE / NOT_VALIDATED / NOT_PRODUCT_AUTHORITY
Owner seed: `GRF + H^ -> Phi` / `GWT + Hyperposition -> higher-order cognition`
Scope: generic ClayCode cognition research only. This document does not alter canonical truth, state, effect, permission, or training authority.

## 0. Claim boundary

This work formalizes a falsifiable computational hypothesis. It does **not** claim consciousness, AGI, biological equivalence to GNWT, mathematical proof of intelligence, or product superiority.

The strongest current scientific statement is conditional:

> An explicit, provenance-bound multimodal belief state may improve bounded cognition when a global workspace must select/broadcast information while preserving unresolved alternatives, **if and only if** matched-budget ablations show positive task-level interaction beyond simpler latent or additive baselines.

GNWT is useful here as an engineering abstraction for global access/broadcast, not as proven biological authority. Modern adversarial consciousness experiments challenge key GNWT predictions, so no consciousness inference is licensed from a workspace implementation.

## 1. State objects

Let a relation/task at time `t` have `K` admissible semantic hypotheses.

`x_i in R^d` = normalized semantic state/embedding of hypothesis i.

`ell_i in R` = unnormalized log-belief derived from admitted evidence.

`pi_i` = provenance/ancestry/evidence lineage.

Define the Hyperposition set:

`Hhat_t = {(x_i, ell_i, pi_i)}_(i=1..K)`

and posterior:

`p_i = exp(ell_i) / sum_j exp(ell_j)`.

The state is a **set**, not a sequence. Therefore every semantic operator must satisfy permutation invariance:

`F(sigma(Hhat)) = F(Hhat)` for every permutation `sigma`.

Canonical hashing must sort stable candidate/evidence identities rather than depend on prompt order.

## 2. Evidence dynamics in log space

For observation `o_(t+1)` under action/test `a_t`:

`ell_(i,t+1) = ell_(i,t) + log P(o_(t+1) | H_i, a_t)`.

This is Bayes' rule before normalization and is both numerically stable and compact.

For binary alternatives only one scalar is needed:

`L_t = log(p_1/p_2)`

`L_(t+1) = L_t + log[P(o|H_1,a)/P(o|H_2,a)]`.

Thus a two-way Hyperposition can carry its complete relative epistemic state in one real number plus the two candidate identities and provenance.

### Provenance dependence guard

Repeated descendants of one source must not be counted as independent evidence. Let `c` index ancestry/evidence clusters and `rho_c in [0,1]` be an admitted dependence weight:

`ell'_i = ell_i + sum_c rho_c log P(E_c | H_i)`.

`rho_c=0` means duplicated/echo evidence adds no independent credit; `rho_c=1` is reserved for admitted independent evidence. Exact dependence modeling remains an empirical/runtime contract, not a model privilege.

## 3. Three different quantities must not be conflated

### 3.1 Epistemic uncertainty

Shannon entropy:

`S(H) = -sum_i p_i log p_i`.

Effective hypothesis count:

`N_eff = exp(S)`.

This answers: **how distributed is posterior mass?**

### 3.2 Semantic conflict / tension

Entropy alone cannot distinguish three near-duplicates from three mutually incompatible hypotheses.

For normalized `||x_i||=1`, define semantic mean:

`mu = sum_i p_i x_i`.

Define Hyperposition tension:

`Theta_H = 1 - ||mu||^2`

which is equivalent to:

`Theta_H = (1/2) sum_(i,j) p_i p_j ||x_i-x_j||^2`.

`Theta_H=0` for semantically identical alternatives, even when entropy is maximal. It rises when substantial posterior mass occupies distant semantic modes.

For a task/relation-specific positive semidefinite metric `M_r`:

`Theta_(H,r) = tr(M_r Sigma_H)`

where

`Sigma_H = sum_i p_i (x_i-mu)(x_i-mu)^T`.

This allows relation-sensitive conflict without letting similarity create truth.

### 3.3 Workspace accessibility

Workspace attention/broadcast weight `alpha_i` is **not** posterior probability `p_i`:

`p_i != alpha_i`.

A low-probability but catastrophic alternative may deserve high workspace access. Conversely, a salient/fluent alternative may have low evidence.

Candidate workspace score:

`s_i = gamma log(p_i+eps) + salience(q,x_i) + lambda_risk R_i + lambda_novel N_i`

`alpha_i = softmax(s_i/tau)`.

Broadcast:

`g_t = sum_i alpha_i W_v x_i`.

This separation is mandatory:

`BELIEF != ACCESS != TRUTH != ACTION_AUTHORITY`.

## 4. Information geometry of Hyperposition

The posterior vector lives on the probability simplex.

Use square-root coordinates:

`psi_i = sqrt(p_i)`.

Then `||psi||_2=1`; the simplex interior maps to the positive orthant of a sphere. Under the conventional `2*sqrt(p)` embedding, Fisher-Rao distance is:

`d_FR(p,q) = 2 arccos(sum_i sqrt(p_i q_i))`.

This provides a coordinate-invariant measure of how far a belief update moved.

Useful derived dynamics:

`v_FR(t) = d_FR(p_t,p_(t+1))`  (belief velocity)

`a_FR(t) = v_FR(t)-v_FR(t-1)`  (coarse acceleration)

These are **diagnostics**, not truth. High oscillatory `v_FR` may identify unstable evidence or conflicting updates; stable low velocity may mean either convergence or no new information, so provenance/outcome context is required.

## 5. Workspace × Hyperposition coupling

A pure mean broadcast can destroy multimodality. Therefore retain both selected/broadcast state and unresolved structure.

Define uncertainty descriptor:

`u_t = [S_t, N_eff_t, Theta_t, margin_t, tail_mass_t, v_FR_t, provenance_features_t]`.

Minimal additive candidate:

`Phi_add = sigma(W_g g_t + W_u u_t + b)`.

Interaction candidate:

`Phi_x = sigma(W_g g_t + W_u u_t + W_x(g_t tensor u_t) + b)`.

Compact notation:

`Phi_t = GWT(Hhat_t) (+)_Gamma Hhat_t`.

`Gamma` is the interaction operator, not ordinary scalar addition.

Primary counterhypothesis: if the base model/GWT already contains a sufficient statistic for the belief distribution, then the explicit term is redundant and `J_GH - J_G ~= 0` after matched budgets.

## 6. Action without epistemic collapse

The system often does **not** need to know which hypothesis is true before acting.

For task utility `U(a,H_i)`:

`Q(a) = sum_i p_i U(a,H_i)`

`a* = argmax_a Q(a)`.

If all high-mass hypotheses recommend the same action, action may commit while Hyperposition remains open.

Therefore define two distinct transitions:

`ACTION_COMMIT != EPISTEMIC_COLLAPSE`.

No action confidence, model fluency, recurrence, or workspace winner may promote a fact.

## 7. Discriminator / value-of-information law

For candidate discriminator/test `d`:

`V(d) = kappa * EIG(d) + DeltaEU(d) - C(d)`

where:
- `EIG(d)=I(H;O_d)` is expected information gain,
- `DeltaEU(d)` is expected improvement in task utility from better decisions,
- `C(d)` includes time, tokens, money, risk, tool use, latency, and opportunity cost.

Select:

`d* = argmax_d V(d)`.

Continue information acquisition only if:

`max_d V(d) > 0`.

This avoids both premature collapse and analysis paralysis.

## 8. Collapse law

A Hyperposition may stop active search because no positive-value discriminator remains, while still remaining epistemically unresolved.

Define:

`SEARCH_STOP` iff `max_d V(d) <= 0` or resource gate closes.

Define:

`EPISTEMIC_COLLAPSE(H_i)` only after the existing exact Clay contract supplies the required admitted R6/evidence receipt and provenance/authority/generation checks.

Posterior thresholds, entropy, semantic tension, or workspace selection may gate investigation but cannot mint truth.

## 9. Resource-rational / rate-distortion compression

Hyperposition can grow combinatorially. The cognitive transport view should therefore minimize decision distortion rather than merely preserve highest posterior mass.

Choose compressed representation `Htilde` by:

`Htilde* = argmin_Htilde [ D_V(H,Htilde) + beta L(Htilde) ]`

where:
- `L` = tokens/bytes/latency/memory,
- `D_V` = decision/value distortion, e.g. expected regret or change in discriminator ranking.

A low-probability, high-consequence state may therefore survive while a higher-probability redundant state is compressed away.

If omitted posterior mass is non-negligible, preserve an explicit tail pseudo-state `~` so compression cannot masquerade as certainty.

### Synthetic discriminator

A private toy simulation with 8 hypotheses and 5 actions was used only as a mathematical discriminator, not product evidence. Keeping two hypotheses by top posterior preserved the full expected-utility action in roughly 73% of random cases, while a brute value-directed two-state subset preserved it in roughly 99.8% in that deliberately small synthetic setup. This result is **not externally validated** and must not be promoted; it only demonstrates that posterior mass and decision sufficiency can diverge dramatically.

## 10. Quantized relative-log representation

A K-way distribution has only K-1 degrees of freedom. Transport should therefore avoid serializing K decimal probabilities.

Choose one stable reference hypothesis `r`, normally the current posterior leader, and store quantized relative logits:

`q_i = round((ell_i-ell_r)/delta)` for `i != r`, with `q_r=0` implicit.

Decoder:

`p_i = softmax(delta*q_i)`.

Candidate v1 quantization: `delta=0.25 nat`.

Analytic/synthetic sweep (not product evidence):
- binary probabilities 0.01..0.99: max absolute probability error about 0.0312; mean about 0.0106; p95 about 0.0259;
- random K=3..8 sparse/simplex samples: mean max-component error around 0.012..0.014 and mean KL below about 0.0013 in the sampled runs.

Near-ties can quantize to equal logits, so the explicitly designated reference identity is the deterministic tie-break. Quantized values are a **derived cognition/transport view only** and must never overwrite canonical full-precision evidence/posteriors.

## 11. Token-efficient H1 transport candidate

See `the artefact/blogpost_entity/mini_cognition/HYPERPOSITION_COMPACT_H1_CANDIDATE.md`.

Core example:

`h(c,"a-3|b#e7?d4!6")`

Interpretation under candidate H1 grammar:
- `a`,`b`: local stable candidate aliases resolved through evidence bundle `e7`;
- exactly one alternative omits a signed integer and is reference logit 0 (`b` here);
- `a-3`: relative logit = `-3*0.25=-0.75` nat;
- `#e7`: canonical evidence/provenance bundle reference;
- `?d4`: current cheapest/value-positive discriminator reference;
- `!6`: R6-only collapse contract.

Decoded binary probabilities:

`p(b)=1/(1+exp(-0.75)) ~= 0.679`

`p(a)~=0.321`.

The prior explicit Hyperposition call sequence is about 161 characters for its five Hyperposition-specific lines in a representative current example; the compact H1 call above is 20 characters, about 87.6% character reduction. Exact Qwen3.5-0.8B tokenizer savings remain **UNMEASURED** and require exact-tokenizer benchmarking before any token-efficiency claim.

## 12. Derived features should not be serialized

Do not transmit entropy, N_eff, covariance, tension, posterior margin, Fisher-Rao velocity, or normalized probabilities when they can be deterministically derived from canonical bundle + compact logits.

Rule:

`SERIALIZE SUFFICIENT STATE; DERIVE STATISTICS`.

This prevents token waste and duplicated state authority.

## 13. Hypotheses

H1 — explicit multimodality improves reversal recovery versus mean/MAP-only state.

H2 — GWT × Hyperposition has positive matched-budget interaction on tasks requiring globally accessible unresolved alternatives.

H3 — semantic tension `Theta` predicts false collapse better than alternative count or entropy alone when alternatives are correlated/near-duplicate.

H4 — action-without-collapse reduces unnecessary epistemic commitment without lowering task utility.

H5 — value-directed compression yields lower decision regret per token than top-p/top-k compression.

H6 — relative-logit H1 encoding preserves downstream decision/discriminator choice at materially lower token cost than verbose calls.

H7 — bilinear/set-interaction coupling helps only on genuinely joint dependencies; additive fusion should win simpler cases due to lower complexity.

H8 — permutation-invariant Hyperposition processing reduces order-induced instability versus sequence-sensitive candidate lists.

H9 — Fisher-Rao movement plus semantic tension distinguishes stable convergence, redundant alternatives, and oscillatory conflicting evidence better than scalar confidence.

## 14. Counterhypotheses / failure worlds

C1 LATENT SUFFICIENCY — the LLM already stores sufficient multimodal state; explicit H is redundant.

C2 INTERFERENCE — preserving alternatives harms reasoning due to context/attention competition.

C3 HALLUCINATION STABILIZATION — explicit H gives invented hypotheses undeserved persistence.

C4 CORRELATED-EVIDENCE DOUBLE COUNT — multiple paraphrases inflate posterior confidence.

C5 GWT BOTTLENECK — workspace competition collapses multimodality before useful interaction occurs.

C6 TOKENIZER BACKFIRE — punctuation-heavy H1 is character-small but token-expensive for the target tokenizer.

C7 QUANTIZATION REVERSAL — near ties alter action/discriminator ranking.

C8 VALUE-MODEL ERROR — value-directed compression preserves the wrong states because the utility model is misspecified.

C9 METRIC ERROR — embedding distance does not correspond to task-relevant contradiction; `Theta` becomes misleading.

C10 COMPUTE GOODHART — GH wins only because it receives more parameters, steps, or tests.

C11 ORDER LEAK — aliases or parser implementation accidentally reintroduce sequence semantics.

C12 PREMATURE ACTION — expected-utility action under a bad posterior causes harm despite keeping epistemic H open.

## 15. Required ablations

Primary 2x2:

- `B00`: neither explicit workspace nor explicit Hyperposition
- `G10`: workspace only
- `H01`: Hyperposition only
- `GH11`: both

Primary interaction:

`Delta_syn = J_11 - J_10 - J_01 + J_00`.

Require matched model, training data, parameters where possible, token/tool/time budgets, evidence access, and stopping policy.

Additional ablations:
- full precision vs H1 quantized logits;
- verbose current Hyperposition calls vs H1 compact carrier;
- top-k posterior vs value-directed compression;
- entropy-only vs `(S,Theta)`;
- additive vs bilinear/set coupling;
- sequence-sensitive vs permutation-invariant set aggregation;
- collapse-before-action vs action-without-collapse;
- ancestry-independent vs ancestry-corrected evidence.

Primary metrics:
- task utility/correctness;
- calibration/Brier/log loss;
- false-collapse rate;
- reversal recovery;
- unsupported-truth rate;
- action regret;
- discriminator value/cost;
- time/tokens/bytes/memory;
- H1 decode error and downstream decision equivalence;
- permutation stability;
- exact resource-normalized `Delta_syn` with uncertainty interval.

Partial-information-decomposition synergy may be exploratory only; PID redundancy definitions remain contested, so no single PID scalar is canonical evidence of architectural synergy.

## 16. Recommended architecture law

The research candidate can be summarized as:

`EVIDENCE -> HYPERPOSITION(p,semantic_geometry,provenance) -> VALUE-DIRECTED COMPRESSION -> GWT ACCESS/BROADCAST -> ACTION/TEST -> EVIDENCE REENTRY`

with four separate authorities:

`EPISTEMIC BELIEF != WORKSPACE ACCESS != ACTION SELECTION != CANONICAL TRUTH`.

The compact conceptual formula remains:

`Phi = GWT(Hhat) (+)_Gamma Hhat`

but executable semantics require the full state/update/action/collapse laws above.

## 17. Promotion boundary

Do not merge this candidate into canonical cognition semantics merely because the equations are coherent.

Promotion requires:
1. exact target-tokenizer token benchmark;
2. parser/grammar fail-closed tests;
3. H1 round-trip property tests;
4. quantization error + decision-equivalence tests;
5. duplicate/provenance adversarial tests;
6. matched-budget 2x2 held-out ablation;
7. simpler latent/additive baseline comparison;
8. OOD reversal/conflict/discriminator tasks;
9. no new truth/effect/state authority;
10. exact current-source runtime evidence under the active execution policy.

Until then: RESEARCH_CANDIDATE / NOT_VALIDATED.