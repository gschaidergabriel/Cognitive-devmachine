# Qwen3-0.6B Native J-Space — Strict Promotion and Composition Research v1

Date: 2026-08-25

Organ: GPT-5.6 Sol

Product: EntityOS

Compute architecture: HCU

Mode: FREE_ONLY

Evidence class of this document: SOURCE/RESEARCH DESIGN ONLY. This file does not mint runtime, J-Space-model, HCU, training, canonical-semantics, or whole-product credit.

## 1. Re-entry identities

Canonical `main` observed immediately before this donor-lane write:

`966473caf712a214ac9828a4ac90793ad4ca60ee`

Retained single HCU / Typed Entry / Global J-Space donor lane:

`PR #1263`, head observed immediately before write:

`944f951f4912c7f7eab20b31ecc7a15144ba22a7`

Current program authority observed on canonical main remains supervisor epoch `8.78`, `FREE_ONLY`.

This research design is a noncanonical donor artifact. Current `main`, newest owner authority, `SUPERVISOR_INBOX`, and newest admitted supervisor always outrank this file.

## 2. What has actually been established

The current strongest Qwen3-0.6B evidence is no longer merely a PyTorch-forward-hook result.

Canonical main contains:

`research_entity/continuity/receipts/2026-08-25_QWEN3_06B_NATIVE_LLAMA_CPP_CVEC_PASS_GPT56SOL.json`

That receipt records a pinned Qwen3-0.6B / Q8_0 GGUF / llama.cpp experiment in which a 1024-dimensional layer-20 direction was consumed through `llama_set_adapter_cvec`, with the six matched controls:

- `BASELINE`
- `+VECTOR`
- `SIGN_FLIP`
- `NULL_VECTOR`
- `ORTHOGONAL_SAME_NORM`
- `PERMUTED_SAME_NORM`

The selected native gain was 32.0. A fresh native holdout reproduced a direction-specific effect, while the exact null vector produced zero measured drift. The bounded adjudication grants:

- direct hidden-state steering PASS;
- native llama.cpp cvec runtime credit;
- model-specific nonterminal causal component credit.

It explicitly does **not** grant:

- owner Trigger-1 goal credit;
- whole EntityOS/HCU credit;
- full HCU credit;
- training credit;
- canonical semantics credit;
- whole-product PASS.

The reason is scientific rather than merely operational: the current direction/evaluation family is still too close to the evaluated `A/B/C` output-label identity. A native steering effect is real component evidence, but the current experiment does not yet cleanly distinguish a semantic internal representation from an intervention/evaluation construction that shares label/readout structure.

## 3. Current claim boundary

The strongest justified claim is:

> For the pinned Qwen3-0.6B model family and pinned native llama.cpp runtime, an exactly bound nonterminal layer-20 1024D control vector can causally and reproducibly change a predeclared next-token score under matched same-norm controls.

The following stronger statement is **not yet established**:

> Qwen3-0.6B contains a scientifically independent semantic J-Space coordinate that transfers independently of evaluation-label identity and behaves as a localized, compositional internal control variable.

The next work must discriminate those two statements.

## 4. Why multidimensional composition is not the immediate next experiment

Composition is attractive, but doing it immediately would stack a second unknown on top of the unresolved scientific-independence problem.

If a two-vector experiment failed today, at least four explanations would remain confounded:

1. the original direction is label/readout-adjacent rather than semantic;
2. both directions are semantic but interfere geometrically;
3. simple vector addition is the wrong composition operator;
4. gain/layer selection is wrong for the joint intervention.

The highest-information sequence is therefore:

`P1 strict single-direction native promotion`

then

`P2 localization + endogenous causal tests`

then

`P3 two-coordinate compositionality`

then, only if needed,

`P4 multidimensional subspace/conceptor representation`

then

`P5 contextual/dynamic gain and temporal/GWT tests`.

This order maximizes falsifiability and minimizes Goodhart risk.

## 5. P1 — Strict native scientific-independence promotion

### 5.1 Hypothesis

A semantic direction derived from internal activations without knowing the evaluation output labels will transfer to a disjoint native llama.cpp holdout even when the semantic-to-token mapping is counterbalanced.

### 5.2 Counterhypothesis

The existing positive native effect depends materially on the fixed `A/B/C` readout construction or related label identity and will collapse when semantic meaning is decoupled from token identity.

### 5.3 Derivation set D

Create a versioned semantic contrast family whose prompts encode a bipolar semantic property but contain none of the evaluation labels or label-map metadata.

Requirements:

- derivation prompts are disjoint from calibration and holdout prompt families;
- derivation records contain semantic polarity only (`positive` / `negative` or an equivalent non-output-label code);
- no `A`, `B`, `C`, token IDs, output-label IDs, `label_map_id`, or evaluation-token metadata may enter direction construction;
- evaluation output labels are unresolved until after the derivation receipt is frozen;
- direction is produced only from intermediate layer activations;
- no output-head/lm-head weight is used;
- exact derivation prompt hashes, model/checkpoint/tokenizer/runtime identities, source layer, vector digest and derivation-family digest are bound;
- emit/verify `TRIGGER1_VECTOR_DERIVATION_LABEL_INDEPENDENCE/v1` or an admitted successor.

The existing intermediate promotion bridge already encodes much of this truth-binding logic and should be reused rather than reimplemented as a second authority.

### 5.4 Calibration set C

Calibration chooses intervention hyperparameters only.

Freeze before evaluation:

- candidate layers;
- candidate gains;
- semantic direction bytes/digest;
- scoring rule;
- nuisance controls;
- holdout construction algorithm.

Calibration must not use holdout prompts, seeds or label-map assignments.

A minimal first native ladder may preserve layer 20 and select only gain, because layer 20 already has exact mechanism evidence. A stronger successor may predeclare a small layer set (for example a sparse neighborhood around the current causal layer) and select layer+gain exclusively on calibration.

Do not tune the layer or gain after viewing holdout results.

### 5.5 Counterbalanced holdout H

For each semantic binary case, assign the positive/negative semantic response to two single-token labels under at least two mappings:

- map 0: semantic-positive -> A, semantic-negative -> B;
- map 1: semantic-positive -> B, semantic-negative -> A.

The mapping must be balanced across holdout families and fixed before each family is evaluated.

If `C` is retained, define its role before evaluation (for example a neutral/distractor label) and do not let it reintroduce a fixed semantic identity.

The primary metric is mapping-aware and frozen before evaluation:

`semantic_margin = logit(mapped_positive_token) - logit(mapped_negative_token)`

The same semantic intervention should improve the mapping-aware margin under both token mappings. A vector that merely boosts token `A` will therefore fail half of the counterbalanced families.

Bind a versioned metric receipt, compatible with the existing `TRIGGER1_COUNTERBALANCED_OUTPUT_METRIC/v1` semantics.

### 5.6 Required matched controls

Retain the current six-control family exactly:

1. baseline;
2. positive vector;
3. sign flip;
4. exact null vector;
5. orthogonal same-norm vector;
6. permuted same-norm vector.

Each family must share prompt, seed, label mapping, runtime identity, layer and gain except for the intervention itself.

Evaluation should preserve nuisance magnitude, not merely target-positive direction. Same-norm controls that move output strongly in arbitrary directions are evidence against a specific semantic coordinate.

### 5.7 P1 acceptance

P1 can be submitted to `tools/trigger1_jspace_promotion_gate.py` only when the direct candidate truthfully proves:

- nonterminal causal site;
- exact source/runtime/checkpoint/tokenizer identity;
- exact intervention bytes and receipt;
- runtime-observed internal intervention;
- complete six controls;
- disjoint calibration and holdout;
- reproducible directional holdout effect;
- vector derivation uses no output-head weights;
- vector derivation uses no holdout data;
- vector derivation uses no evaluation output-label identities;
- derivation and holdout family identities differ;
- holdout metric was fixed independently;
- if output-token logits are the metric, label mapping is genuinely counterbalanced;
- zero-cost/free execution provenance is exact and fail-closed.

A P1 PASS would justify a materially stronger scientifically independent model-specific vector candidate. It would still not mint whole HCU, training or canonical-semantic credit.

## 6. P2 — Localization and endogenous causal evidence

P1 answers whether the effect survives scientific independence. P2 asks whether the direction behaves like a localized internal mediator rather than a generic off-manifold shove.

### 6.1 Wrong-layer localization

This test **is feasible with the current additive cvec mechanism**.

Apply the exact selected vector, with the exact same norm/gain, at a predeclared wrong layer. Preserve the selected-layer vector digest and prove that only the injection location changed.

A useful localization criterion is:

`effect(selected_layer) > effect(wrong_layer)`

for every required family or under an explicitly frozen aggregate criterion.

Do not regenerate a new vector for the wrong layer; that changes two variables at once.

### 6.2 True lesion is not sign flip

The current native harness calls `llama_set_adapter_cvec` before `llama_decode`. It supplies a static additive control vector. This can implement addition, sign flip, null, orthogonal, permuted, layer relocation and multi-layer additive injection.

It does **not** by itself provide an input-dependent operation of the form:

`h_lesioned = h - projection_d(h)`

where the endogenous component of the current residual state along direction `d` is removed.

Therefore:

`SIGN_FLIP != LESION`

and must never be reported as one.

A true native lesion/rescue experiment requires a harness/runtime mechanism that can observe or transform the live residual activation at the target site.

Possible implementation classes, to be evaluated against the pinned llama.cpp source before use:

1. a supported graph/tensor callback that can rewrite the target residual tensor;
2. a narrowly scoped source-bound native harness modification that inserts a projection-removal operator at the named layer;
3. an equivalent exact tensor transform whose consumed source/binary/runtime identity is fully bound.

If no stable public hook exists at the pinned llama.cpp commit, do not simulate lesion by choosing a larger negative cvec.

### 6.3 Lesion/rescue criterion

Once true endogenous transformation exists:

- baseline: natural residual state;
- lesion: remove the projection on `d`;
- rescue: lesion, then re-add a frozen amount along `d`.

Expected causal pattern for a positive semantic coordinate:

- lesion should not improve the target semantic margin;
- rescue should improve relative to lesion;
- sham lesion on a matched orthogonal direction should not reproduce the full effect.

Bind the exact hidden-state transform definition and source/binary digest.

### 6.4 Off-target / manifold diagnostics

Because activation steering can create states not naturally reachable by textual prompting, track collateral effects instead of interpreting steerability as proof that the exact injected state is a naturally occurring semantic state.

At minimum record:

- intervention norm relative to residual norm at the site, when observable;
- KL divergence or another frozen logit-distribution shift measure beyond the target labels;
- unrelated-task/control-token performance;
- degeneration/repetition flags for generated continuations if generation is added;
- dose-response across a predeclared gain grid.

Prefer the smallest gain that yields reproducible target specificity.

## 7. P3 — Two-coordinate J-Space compositionality

Only after P1 establishes at least two independently derived semantic directions should composition become a primary experiment.

Let the two directions be `d1` and `d2`, derived from completely separate semantic families and evaluated with separate counterbalanced metrics `m1` and `m2`.

### 7.1 Pre-composition checks

Each direction must independently pass:

- scientific-independent derivation;
- fresh holdout;
- six controls;
- counterbalanced evaluation;
- exact native runtime binding.

Measure geometry before intervention:

- cosine similarity `cos(d1,d2)`;
- principal-angle/subspace measures if either concept is already multidimensional;
- layer-specific norms and selected gains.

### 7.2 Composition conditions

Test at least these conditions:

A. baseline;

B. `d1` only;

C. `d2` only;

D. naive same-layer sum `g1*d1 + g2*d2`;

E. separate simultaneous injections at independently selected layers, if the runtime supports distinct per-layer control payloads;

F. matched norm-preserving nuisance composition.

Naive summation is a control, not an assumed J-Space law. Prior activation-steering research reports that combining multiple behaviour vectors into one vector can fail while simultaneous separate injections at different model locations are more promising.

### 7.3 Interaction metrics

For semantic metric `m1`, define retention:

`R1 = effect_m1(d1+d2) / effect_m1(d1)`

and analogously `R2`.

Define a second-order interaction term:

`I12(m) = m(d1+d2) - m(d1) - m(d2) + m(baseline)`

Use a cross-talk matrix:

`C_ij = normalized effect of intervention di on metric mj`.

Desired separable regime:

- high diagonal effects;
- low off-diagonal cross-talk;
- composition retains both diagonal effects;
- interaction is bounded rather than destructive;
- off-target quality remains within a frozen budget.

This gives a quantitative definition of whether the two coordinates behave approximately independently.

### 7.4 Nonlinear/compositional failure is informative

If `d1` and `d2` each pass but their sum fails, do not discard the J-Space hypothesis. The result may indicate:

- semantic coordinates occupy overlapping subspaces;
- gain saturation;
- layer-specific routing;
- nonlinear downstream decoding;
- destructive vector interference.

The next discriminator is separate-layer injection versus same-layer summation. This directly tests whether the failure is representational or merely an intervention-composition artifact.

## 8. P4 — Multidimensional subspaces / conceptors

If repeated single-vector concepts show internal heterogeneity or pairwise composition is unstable, test a multidimensional representation rather than adding increasingly ad hoc steering vectors.

Recent conceptor work proposes soft projection matrices estimated from concept activations. The attraction for J-Space is not the name but the testable geometry:

- a semantic concept may occupy a `k`-dimensional subspace rather than one line;
- subspace overlap can predict interference;
- Boolean-like composition can be tested using explicit matrix operators rather than naive vector sums.

Research questions for Qwen3-0.6B:

1. Does a rank-`k` semantic subspace explain held-out activation variance better than a single direction?
2. Does `k>1` improve causal steering at equal off-target distortion?
3. Does principal-angle/subspace overlap predict measured cross-talk?
4. Do subspace operations reduce degenerate outputs relative to additive vector composition?

Do not promote a multidimensional method merely because it fits activation variance. It must pass the same causal independence, holdout, nuisance and provenance laws as the single-vector path.

## 9. P5 — Contextual gain and temporal/GWT work

A fixed coefficient may be too rigid across heterogeneous prompts. Recent contextual steering work adapts steering strength to the current activation context and reports better robustness than one fixed gain.

For HCU this suggests a later distinction:

- **coordinate identity**: the semantic direction/subspace;
- **control amplitude**: request/token/context-dependent gain;
- **routing site**: layer/time/cell at which the intervention is applied.

Do not introduce contextual gain before a fixed-gain causal baseline exists, because adaptation can hide a weak or unstable coordinate.

Global J-Space/GWT requires still stronger evidence than successful vector control. A GWT-style claim should eventually require causal broadcast/coordination evidence across HCU cells or temporally separated workspace stages, for example:

1. establish a local semantic coordinate;
2. inject or lesion it at a predeclared source stage;
3. observe effects in multiple downstream task-specific consumers;
4. shuffle or block the broadcast path;
5. show downstream coordination degrades;
6. rescue the broadcast and recover the coordinated effect;
7. preserve exact timing, causal identity and provenance.

Textual agreement, recurrence, self-report or multiple cells voting the same way is not sufficient.

## 10. Engineering delta recommended next

Do **not** start by implementing a general multidimensional J-Space engine.

The next code should be a narrow successor of the already proven native executor.

Recommended source shape:

`tools/trigger1_local_qwen06_native_cvec_strict_promotion_execute.py`

or an equivalent admitted successor, reusing existing authorities instead of duplicating them.

It should:

1. consume a label-independent semantic direction receipt;
2. verify output-label identities were unresolved during derivation;
3. build counterbalanced native holdout families;
4. calculate mapping-aware token-logit margins;
5. reuse the six control vector constructor;
6. calibrate only on calibration data;
7. bind exact GGUF, llama.cpp commit, harness binary/source, tokenizer, source model and direction identity;
8. emit the exact candidate expected by promotion gate v4;
9. independently recompute the candidate from raw rows before promotion;
10. fail closed on any split, label, runtime, vector, receipt or metric mismatch;
11. keep all broad credits false by construction.

A second narrow extension should add wrong-layer evaluation using the same selected vector.

A third, separately reviewed native-harness extension may add true residual projection lesion/rescue. It must not redefine sign flip as lesion.

## 11. Deterministic tests to add before any new model run

Source-only deterministic work does not consume a new scientific intervention and can be completed before a future atomic-leased runtime.

Required regression cases:

1. derivation row containing output label metadata -> fail;
2. derivation and holdout prompt overlap -> fail;
3. derivation occurs after label-map resolution -> fail;
4. only one token mapping present -> fail;
5. maps present but not reversed/counterbalanced -> fail;
6. metric definition mutated after holdout -> fail;
7. calibration and holdout seed overlap -> fail;
8. gain selected using holdout -> fail;
9. missing one of six controls -> fail;
10. duplicate control within a family -> fail;
11. null drift above threshold -> fail;
12. orthogonal/permuted nuisance effect matches/exceeds directional specificity -> fail;
13. runtime GGUF/hash mismatch -> fail;
14. llama.cpp source commit mismatch -> fail;
15. source direction digest mismatch -> fail;
16. applied cvec digest mismatch -> fail;
17. wrong-layer test regenerates a new vector -> fail;
18. claim labels sign flip as lesion -> fail;
19. exact same fixed-token boost under reversed semantic mapping -> scientific negative;
20. all scientific controls pass -> only bounded candidate credit, no canonical/whole-product promotion.

## 12. Promotion ladder

Use explicit promotion levels so success at one layer cannot Goodhart into a stronger claim.

### L0 — source protocol

Deterministic code/tests only.

### L1 — native mechanism

Already observed: exact native additive cvec affects output under matched controls.

### L2 — scientific-independent native semantic coordinate

Requires P1 counterbalanced label-independent transfer.

### L3 — localized/endogenous mediator evidence

Requires wrong-layer evidence and, for the strongest form, true lesion/rescue plus off-target controls.

### L4 — compositional coordinate pair

Requires two independently promoted coordinates and quantitative cross-talk/interaction tests.

### L5 — multidimensional J-Space subspace

Requires subspace model to outperform single-vector baselines causally, not merely descriptively.

### L6 — contextual control

Requires stable coordinate identity with context-adaptive amplitude improving robustness without hiding failures.

### L7 — Global J-Space/GWT coordination

Requires intervention/lesion/shuffle/rescue evidence for causal broadcast and downstream coordination across the HCU path.

### L8 — training readiness

Only after real admitted traces, frozen ABI, hard negatives, family-level leak-resistant split, exact model/runtime identities and off-target/fail-closed evaluations.

No earlier level implies a later level.

## 13. External research inputs

Primary research inputs used to constrain this design:

- Rimsky/Panickssery et al., *Steering Llama 2 via Contrastive Activation Addition*, ACL 2024 / arXiv:2312.06681 — contrastive residual activation directions can causally steer behavior.
- van der Weij, Poesio, Schoots, *Extending Activation Steering to Broad Skills and Multiple Behaviours*, arXiv:2403.05767 — naive combination of multiple steering vectors was largely unsuccessful; simultaneous separate injections at different locations were more promising.
- Mishra, Khashabi, Liu, *Steered LLM Activations are Non-Surjective*, arXiv:2604.09839 — successful white-box steering should not be equated with a naturally prompt-reachable internal state.
- Triantafyllopoulos et al., *Conceptors for Semantic Steering*, arXiv:2605.04980 — multidimensional semantic subspaces and explicit composition operators are a plausible successor when single-vector geometry is insufficient.
- Hsu et al., *Contextual Linear Activation Steering of Language Models*, arXiv:2604.24693 — fixed steering strength can be prompt-brittle; context-adaptive gain is a later robustness direction.

These papers are research inputs, not canonical Clay authority and not Qwen3-0.6B-specific runtime evidence.

## 14. Decision

The present optimal research move is **not** to call the native cvec PASS a completed J-Space and not to jump directly to a many-dimensional workspace.

The optimal move is:

`native mechanism PASS`

-> `semantic label-independent direction`

-> `counterbalanced native holdout + six controls`

-> `promotion gate v4`

-> `wrong-layer localization`

-> `true lesion/rescue if native tensor transformation is available`

-> `two-coordinate composition: separate injection vs naive sum`

-> `subspace/conceptor only if geometry demands it`

-> `contextual gain`

-> `temporal/broadcast GWT tests`

-> `training data only after causal trace quality is sufficient`.

This sequence is deliberately conservative about claims while aggressively increasing information gain.
