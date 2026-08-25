# Forschungsrun 2 — frozen structural source + promotion-boundary audit

## Scope

This is an additive pre-execution audit for the already-dispatched Qwen3-0.6B structural native discriminator. It does **not** create a new intervention, open a new holdout, repeat the native mechanism test, or change the frozen scientific design.

Observed authority before this write: supervisor `8.78`, `FREE_ONLY`, EntityOS + HCU. Prior Run-2 transport receipt: `research_entity/research/receipts/FORSCHUNGSRUN2_2026-08-25_RUNNER_LIVENESS_DISCRIMINATOR.md` at commit `a1e65971f990b7865c6c79e3ca9da57b9856645b`.

## 1. Frozen-source drift discriminator

The queued structural workflow run `32810213066` was dispatched at head:

`77f30f11b0102a2f1fd279edfafccf2bfcb22679`

A direct commit comparison from that dispatch head to current observed main:

`a1e65971f990b7865c6c79e3ca9da57b9856645b`

shows `14` commits of main movement, but **none** of the following frozen scientific files changed:

- `tools/trigger1_structural_label_free_cases.py`
- `tools/trigger1_nuisance_residualize.py`
- `tools/trigger1_structural_native_abstract_execute.py`
- `.github/workflows/clay-trigger1-structural-native-abstract-run.yml`

Therefore the already-queued experiment is, at this observed head, not contaminated by post-dispatch edits to its frozen scientific source or original workflow. This is a source-integrity observation only; because the workflow checks out `ref: main` at execution time, future edits before runner start would still need re-audit.

Classification:

`FROZEN_STRUCTURAL_SOURCE_UNCHANGED_SINCE_DISPATCH_AT_OBSERVED_HEAD`

## 2. Scientific design audit

The frozen discriminator materially addresses the known lexical/compliance confounds:

- model-facing prompts ban canonical AFFIRMATIVE/NEGATIVE/NEUTRAL labels plus decision/compliance synonyms;
- calibration and holdout use disjoint content-symbol vocabularies;
- a 3x3 Latin-square codebook rotates semantic target across opaque A/B/C outputs;
- query negation/polarity is counterbalanced;
- the semantic basis is reconstructed from calibration Q8 layer-input captures rather than imported full-precision basis bytes;
- nuisance residualization explicitly spans canonical-label lexemes, semantic-synonym lexicon, generic instruction compliance, and output-code identity;
- the nuisance basis is fit on calibration only and frozen before holdout;
- one common cvec gain is selected on calibration only;
- native `llama_set_adapter_cvec` intervention is applied at the pinned model/runtime identity and measured under direct `ALL_PROMPT_TOKENS` scope;
- holdout includes matched semantic, sign-flip, null, same-norm orthogonal, same-norm permuted, and nuisance-axis controls;
- behavior is measured with target-code logit margin and class-selective intervention x requested-target matrix;
- downstream transport is measured at a later nonterminal layer input;
- the executor explicitly refuses to claim last-token/native cross-scope mechanistic identity.

This is substantially stronger than the earlier native actuator mechanism PASS.

## 3. Remaining scientific claim boundary even if the queued run PASSes

A PASS from `trigger1_structural_native_abstract_execute.py` should be interpreted as strong **task-family-bounded abstract native causal component evidence**, not as universal semantic J-Space or whole-model canonical semantics.

Two reasons are visible in current source:

1. **Structural-family reuse remains.** Calibration and holdout are lexically disjoint, but they intentionally share one frozen formal grammar/template family (`F/R/Q`, demonstrations, probe structure, codebook mechanics). This falsifies simple lexical-label and output-code explanations much better than prior work, but it does not by itself establish cross-task-family semantic invariance.

2. **Current promotion successor is stricter than the standalone executor.** `tools/trigger1_jspace_promotion_gate_v12.py` requires v11 plus reconstruction/binding of the actual model-facing abstract challenge bytes, exact calibration/holdout executed row universes, runtime receipt hashes for BASELINE/+VECTOR/SIGN_FLIP/NULL/ORTHOGONAL/PERMUTED controls, generic-compliance counterevidence, and a six-family calibration + six-family holdout challenge binding. The standalone structural executor does not itself emit that v12 candidate/binding schema.

Therefore:

`STRUCTURAL_EXECUTOR_PASS != V12_PROMOTION_PASS`

and:

`STRUCTURAL_EXECUTOR_PASS != UNIVERSAL_SEMANTIC_JSPACE`

## 4. Acceptance-criterion caution

The standalone executor's local PASS is directional: positive matched mean effect, positive diagonal advantage, matched effect above control magnitudes, and downstream target-coordinate dominance. These are meaningful causal discriminators, but they are not by themselves a formal uncertainty/equivalence analysis across independent task families. The current v11/v12 promotion chain is the correct place to keep stronger promotion requirements.

No redesign is recommended before the already-frozen run executes; changing the experiment now would destroy the value of its preregistered comparison.

## 5. Next exact gates

1. Restore the retained self-hosted `Linux/X64` runner transport; do not spawn a duplicate experiment.
2. Execute existing run `32810213066` and persist the raw exact-source result.
3. If FAIL: preserve it as scientific counterevidence; do not tune on holdout and silently rerun.
4. If PASS: keep the result at component scope and construct/adjudicate the exact-current v12 promotion binding from immutable runtime receipts/challenge bytes, or explicitly record which v12 requirements remain unsatisfied.
5. Only after v12-compatible review should any stronger semantic J-Space candidate wording be considered; whole HCU/EntityOS/training credit remains separately gated.

## Credit delta

- native llama.cpp cvec component runtime credit: unchanged at 1
- structural label-free native runtime credit: 0 until execution
- J-Space model runtime credit: 0
- canonical semantics promotion: false
- full HCU runtime credit: 0
- whole EntityOS runtime credit: 0
- training credit: 0

## Result

`PASS_PREEXECUTION_FROZEN_SOURCE_AND_PROMOTION_BOUNDARY_AUDIT`
