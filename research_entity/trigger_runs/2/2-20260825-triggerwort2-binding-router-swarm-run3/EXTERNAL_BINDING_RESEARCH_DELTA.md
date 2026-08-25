# Triggerwort 2 — external binding/ICL research delta

Date: 2026-08-25
Organ: GPT-5.6 Sol / ChatGPT organ
Scope: external research input; NOT canonical Clay fact and NOT Qwen3.5-specific evidence

## Purpose

Triangulate the project-derived hypothesis that the measured Qwen3.5-0.8B deficit is best targeted as episode-local semantic -> current mapping -> output-symbol binding/routing rather than broad semantic relearning.

## Primary/near-primary research signals

### Wu, Geiger, Millière (2025) — *How Do Transformers Learn Variable Binding in Symbolic Programs?*

Source: arXiv:2505.20896.

Reported result: a transformer trained on symbolic dereferencing passes through a developmental sequence from random prediction, through a shallow heuristic, to a systematic variable-dereferencing mechanism. Causal analysis attributes the learned mechanism to information routing through specialized attention heads and residual-stream state.

Trigger-2 implication:

- do not score only final accuracy; probe for heuristic intermediate solutions;
- include distractor/irrelevant binding chains and counterfactual remaps;
- after any successful full-FT, lesion/rescue the learned binder while separately checking semantic readout and output writeability;
- treat attention/residual routing as a mechanistic hypothesis to test on the exact Qwen3.5 checkpoint, never as inherited evidence.

### Jang et al. (2024/2025) — *Rectifying Demonstration Shortcut in In-Context Learning*

Source: OpenReview / CoRR.

Reported result: LLMs can rely on pretrained semantic priors of demonstrations rather than learning the actual input-label relation; the paper evaluates a task-learning setting with semantically unrelated labels and proposes demonstration-aware calibration.

Trigger-2 implication:

- opaque/unrelated output atoms are not cosmetic; they are a direct test against pretrained label priors;
- every semantic instance should appear under counterfactual label/code mappings;
- fixed label semantics, display order or prompt topology must not predict the answer;
- a clean semantic decision with a wrong episode mapping must be scored separately from semantic failure.

### Fang et al. (2024) — *Rethinking Invariance in In-context Learning*

Source: OpenReview.

Reported result: standard ICL can be sensitive to context-example ordering; the work identifies information non-leakage and context interdependence as important properties for invariant ICL design.

Trigger-2 implication:

- the swarm's discovery of a codebook display-order shortcut is consistent with a broader known ICL failure class;
- exact factorial crossing / measured nuisance independence is preferable to assuming random shuffling creates invariance;
- codebook order, evidence/query layout, template, polarity and mapping need explicit counterfactual invariance tests.

### Abbas et al. (AISTATS 2024) — *Enhancing In-context Learning via Linear Probe Calibration*

Source: PMLR 238.

Reported result: ICL predictions can be unreliable across prompt templates and demonstration permutations; linear-probe calibration improves robustness in their evaluated settings.

Trigger-2 implication:

- template/permutation robustness should be a first-class evaluation axis;
- calibration can be retained as an evaluation/challenger idea, but it must not replace learning the target binder inside the specialized model;
- compare raw binder behavior with any calibration-assisted challenger so post-hoc calibration is not mistaken for learned internal routing.

### Abernethy et al. (ALT 2024) — *A Mechanism for Sample-Efficient In-Context Learning for Sparse Retrieval Tasks*

Source: PMLR 237.

Reported/theoretical decomposition: transformer ICL can be analyzed as segmentation of examples/labels, inference of a hypothesis, and application of that hypothesis to the query.

Trigger-2 implication:

- preserve explicit stage scoring: parse/segment codebook -> infer semantic class -> apply episode mapping -> emit symbol;
- vary delimiters/layouts to prevent a single serialization topology from becoming the learned algorithm;
- distinguish mapping inference from output serialization in the harness.

### Li et al. (ICML 2023) — *Transformers as Algorithms: Generalization and Stability in In-context Learning*

Source: PMLR 202.

Reported framing: ICL can be formalized as an algorithm-learning problem in which the transformer constructs an inference-time hypothesis; generalization relates to algorithm stability and task complexity.

Trigger-2 implication:

- treat the binder as an algorithmic capability, not a static class association;
- freeze unseen semantic/template/provenance families rather than relying on row-level random splits;
- measure stability under nuisance changes that should leave the inferred episode mapping decision invariant.

## Research synthesis for Clay

External literature strengthens, but does not prove, the current Clay hypothesis:

`READABLE SEMANTICS + WRITABLE OUTPUT != DYNAMIC EPISODIC BINDING`

A credible binder training/evaluation family should therefore simultaneously require:

1. opaque or semantically unrelated output labels;
2. causal counterfactual remapping of the same semantic case;
3. exact crossing/balancing of codebook order, layout, polarity and other nuisance factors;
4. train/validation/holdout separation by semantic/provenance family, not by cosmetic split labels;
5. distractors and shortcut probes;
6. separate scoring of semantic decision, mapping application and symbol emission;
7. post-training causal analysis on the exact Qwen3.5 model to distinguish learned routing from superficial behavioral compensation.

## Important evidence boundary

These papers establish general mechanisms/failure modes in other models/tasks. They do NOT establish that the exact selected Qwen3.5-0.8B checkpoint uses the same attention heads, residual-stream organization, calibration behavior or causal binder. All model-specific mechanism claims remain gated by same-model intervention evidence.

## Current design consequence

The strongest current local blueprint (`tools/trigger2_dynamic_binding_blueprint_v2.py` v2.1 on main) is directionally consistent with this literature because it fully factorializes mapping, codebook order, layout, semantic class and query polarity and keeps an unseen template/symbol holdout. It remains non-trainable until the exact accepted ABI atom inventory and pinned tokenizer materialization gates pass.
