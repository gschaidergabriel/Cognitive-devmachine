# Qwen3-0.6B J-Space — Native Carrier Geometry Reconstruction v1

Date: 2026-08-25

Organ: GPT-5.6 Sol

Product: EntityOS

Architecture: HCU

Mode: FREE_ONLY

Evidence class: SOURCE/RESEARCH DESIGN ONLY. No runtime/J-Space-model/HCU/training/canonical-semantic/whole-product credit is minted by this document.

## 1. Motivation

The current native llama.cpp cvec PASS proves that a full-precision-derived control direction can be serialized into the pinned Q8_0 carrier and causally affect output under matched controls.

That does **not** establish that the Q8_0 target carrier itself contains the same semantic geometry.

The current Trigger-1 promotion gate v6 makes this distinction explicit through `native_carrier_geometry`: the strongest native candidate requires the target runtime basis to be reconstructed independently, imported source basis excluded from the native parity decision, carrier-local norm calibration, subspace alignment evidence, leave-one-family-out stability, a permutation null and a within-carrier causal matrix.

This design supplies the measurement interpretation for those fields.

## 2. Same-coordinate activation site

For a cvec intervention applied to Qwen3 layer 20, pinned llama.cpp adds cvec to the post-FFN residual before it becomes the next layer input.

Therefore the native activation coordinate that corresponds most directly to the cvec payload is:

`layer 21 input == layer 20 post-residual output`

under the pinned Qwen3 graph.

Use the layer-input extraction API at tap 21 on **no-cvec baseline** matched semantic scenario triplets to reconstruct target-carrier geometry.

Do not derive the native basis from already-steered activations.

Do not use the imported PyTorch vector in native basis construction, layer choice, sign choice, rank choice or family filtering.

## 3. Four carrier cells

Let:

- `S` = source full-precision PyTorch carrier;
- `N` = native Q8_0 llama.cpp carrier;
- `D_S` = source-derived semantic basis/subspace;
- `D_N` = native-derived semantic basis/subspace.

Evaluate the following cells separately.

### S -> S

Derive `D_S` from full-precision baseline activations and intervene in the full-precision carrier.

Role: source causal reference.

### S -> N

Transfer frozen `D_S` into native cvec and intervene in Q8_0.

Role: cross-carrier actuator transfer.

The existing native cvec component result is of this general class, although its older basis/evaluation design is not yet the strict semantic successor.

### N -> N

Derive `D_N` solely from native Q8_0 no-cvec baseline activations and intervene with `D_N` in Q8_0.

Role: **strongest native carrier geometry/causality cell**.

This is the critical cell for v6 `target_runtime_basis_reconstructed_independently` and `within_carrier_causal_matrix_passed`.

### N -> S (optional but high information)

Transfer frozen `D_N` back to the source full-precision carrier at the matched residual coordinate.

Role: reverse-transfer symmetry diagnostic.

This cell is not required for native promotion, but asymmetry between S->N and N->S can reveal quantization/runtime-specific geometry or gain/scope mismatch.

## 4. Matched native geometry packet

Construct native no-cvec activations only from label-free, matched scenario triplets:

- AFFIRMATIVE-like variant;
- NEGATIVE-like variant;
- NEUTRAL-like variant;

within each scenario family.

Requirements:

- same content skeleton within a family;
- semantic pole metadata is experiment-side only;
- no explicit semantic pole words/synonyms in model-facing derivation prompts;
- no A/B/C output-code identity in derivation prompts;
- BASIS/CALIBRATION only;
- fresh HOLDOUT unopened;
- family IDs disjoint from source holdout and native holdout;
- exact Q8_0 GGUF, llama.cpp build, tap API/header, token scope and prompt hashes bound;
- raw native layer-input F32 bytes hashed before numeric conversion.

Feed the admitted numeric activations to the existing matched/blocked simplex rank authority rather than implementing another rank statistic.

## 5. Native rank and basis

For three centered semantic states, representation rank is at most 2.

Use the current canonical blocked analyzer's decision:

- `ONE_DIMENSIONAL_SUPPORTED`; or
- `TWO_DIMENSIONAL_REQUIRED`; or
- `UNRESOLVED`.

If unresolved, stop. Do not force a vector because cvec expects one-dimensional rows; a rank-2 result instead means the experiment needs two independently frozen native basis directions and a class-selective intervention matrix.

For rank 1, freeze `D_N = h1_native`.

For rank 2, freeze an orthonormal basis `U_N = [h1_native, h2_native]` only after the blocked rank decision and cross-family coherence requirements pass.

## 6. Source-native geometry comparison

Geometry comparison is **post hoc to independent derivation**, not part of native basis construction.

### Rank 1

Use sign-invariant angular alignment:

`alignment = abs(cos(D_S, D_N))`

and principal angle:

`theta = arccos(clamp(alignment, 0, 1))`.

Do not orient `D_N` by maximizing agreement with `D_S`. Orient it from native semantic metadata/frozen class definition, then report signed and absolute alignment separately.

### Rank 2

Given orthonormal bases `U_S` and `U_N`, compute singular values of:

`U_S^T U_N`.

The principal angles are:

`theta_i = arccos(sigma_i)`.

Report both angles and chordal/projection distance. Do not collapse a two-dimensional match to one favorable vector cosine.

### Rank mismatch

If source rank and native rank differ under adequately powered matched designs, classify:

`CARRIER_REPRESENTATION_RANK_MISMATCH`

and do not claim native geometry parity.

Quantization may preserve causal steerability while changing the locally recovered representation rank; that is a scientifically meaningful result, not an implementation failure.

## 7. Leave-one-family-out stability

A pooled native basis can be dominated by one scenario family.

For each BASIS/CALIBRATION family `f`:

1. reconstruct the native basis excluding `f`;
2. evaluate the held-out family's semantic geometry using that basis;
3. record sign/class consistency and subspace angle to the full calibration basis.

Require a preregistered minimum fraction of families to retain the expected semantic orientation.

V6 should receive `leave_one_family_out_stability=true` only from a receipt containing all family-level results, including failures.

## 8. Native permutation null

The native basis must beat a null generated by semantic-label permutation **within scenario family**, preserving scenario/domain/style structure.

Do not use global label shuffling across scenario families because that destroys the confound the test is supposed to control.

Use deterministic seed material bound to the exact activation packet and analysis config.

## 9. Carrier-local residual norm calibration

Raw cvec gain is not comparable across models, layers, scopes or quantization carriers.

Measure native residual norm at the exact intervention coordinate from no-cvec activation taps.

Parameterize dose as a dimensionless ratio such as:

`rho = ||delta_h|| / median(||h_native||)`

on CALIBRATION only.

For rank-1 unit basis `d`, choose cvec magnitude:

`||delta_h|| = rho * median_residual_norm`.

For rank 2, hold total intervention norm fixed across directions and mixtures so dimensionality/composition is not confounded with dose.

The 2026 cross-family steering audit by Wu, Zhao and Chen is directly relevant here: after residual-norm-comparable interventions and held-out operating-point selection, steering remained significant across model scales including 0.6B, while an apparent scale trend from raw units disappeared. This is external research input, not Clay runtime evidence.

## 10. Within-native causal matrix

After `D_N`/`U_N`, dose, token scope and thresholds are frozen on BASIS/CALIBRATION, execute only on unopened native HOLDOUT.

For each requested semantic target `j`, intervene with each native direction/class action `i` and measure:

`M_N[i,j] = effect_native(intervention_i, requested_target_j)`

under independently counterbalanced output codebooks.

Require:

- diagonal/class-selective advantage appropriate to the chosen rank;
- sign-flip reversal;
- exact null baseline-like;
- orthogonal/permuted controls fail to reproduce;
- lexical/label-only nuisance controls fail to reproduce;
- equal scenario-family weighting;
- explicit token-scope match;
- residual-norm-matched dose;
- context-valid likelihood and emitted-decision agreement;
- independent downstream semantic transport.

Only this `N -> N` matrix can set v6 `within_carrier_causal_matrix_passed=true`.

## 11. Cross-carrier causal matrix

After both S->S and N->N have independently passed their own within-carrier designs, compare:

- `M_SS`: source basis in source carrier;
- `M_SN`: source basis in native carrier;
- `M_NN`: native basis in native carrier;
- optionally `M_NS`: native basis in source carrier.

Useful classifications:

### CARRIER_INVARIANT

Ranks agree, principal angles are small under preregistered threshold, within-carrier matrices agree qualitatively, and both transfer directions preserve class selectivity.

### ACTUATOR_TRANSFER_WITH_GEOMETRY_DRIFT

S->N steering works, but independently reconstructed native geometry differs materially or N->N differs from S->S.

This means an imported vector can control the native model without proving the native carrier represents the same coordinate in the same way.

### NATIVE_GEOMETRY_PRESENT_TRANSFER_MISMATCH

N->N passes and native geometry is stable, but S->N fails. This suggests quantization/runtime coordinate deformation or scale/site mismatch rather than absence of a native semantic coordinate.

### SOURCE_ONLY_GEOMETRY

S->S passes, native reconstruction is null/unresolved and N->N fails. No native semantic J-Space promotion.

### RUNTIME_COMMON_SHORTCUT

S->N and N->N both change output but independent downstream transport/dual readout fails. This supports a shared control/readout shortcut, not semantic J-Space.

## 12. Quantization-specific falsifiers

Preserve these as first-class negatives:

1. native rank unresolved under adequately powered blocked families;
2. native basis unstable under leave-one-family-out;
3. native basis fails within-family permutation null;
4. high source-native vector cosine but N->N causal matrix fails;
5. low source-native alignment but both carriers independently show class-selective causal matrices;
6. S->N works only at much larger residual-normalized dose than N->N;
7. all-token broadcast passes while last-token-only N->N fails;
8. native output moves without independently measured downstream semantic transport;
9. likelihood margin moves but emitted decisions do not;
10. rank differs between representation, downstream transport and behavior.

None of these should be retuned away on holdout.

## 13. Relationship to multidimensional J-Space

A robust rank-2 N->N result would be the first strong reason to move from a single steering vector toward an actual local two-dimensional J-Space subspace in Qwen3-0.6B.

Only then test composition:

- individual h1 / h2;
- norm-matched linear mixtures;
- separate-layer simultaneous injections;
- cross-talk and second-order interaction;
- projector/conceptor-style control if vector composition is unstable.

Do not assume vector addition is semantic composition. Existing activation-steering research reports that merged behavior vectors can fail even when separate simultaneous interventions remain promising.

## 14. Global J-Space / GWT boundary

Even `N -> N` native semantic geometry plus downstream transport is still a **local model-specific** causal result.

Global J-Space/GWT requires an additional broadcast/coordination intervention across HCU stages/cells with path block/shuffle/rescue and downstream consumer effects.

No local rank, principal angle, cvec success, recurrence, self-report or workspace consensus can mint that claim.

## 15. Next exact implementation action

Reuse rather than duplicate the current authorities:

1. native raw layer-input tap harness -> capture no-cvec tap-21 BASIS/CALIBRATION triplets;
2. provenance adapter -> current canonical simplex rank admission/analyzer;
3. freeze native rank/basis and native residual-norm calibration;
4. serialize native-derived basis into cvec only after freeze;
5. scope-matched native N->N causal matrix on fresh holdout;
6. raw downstream taps -> independently derived downstream probe;
7. dual output readout + v6 candidate receipt;
8. submit to canonical v6 gate.

A future model run remains subject to current atomic unusual-experiment coordination and FREE_ONLY execution authority.
