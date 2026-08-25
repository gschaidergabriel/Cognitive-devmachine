# Qwen3-0.6B J-Space — Native Scope-Matched Split-Prefill Carrier v1

Date: 2026-08-25

Organ: GPT-5.6 Sol

Product: EntityOS

Compute architecture: HCU

Mode: FREE_ONLY

Evidence class: SOURCE/RESEARCH DESIGN ONLY. This document creates no runtime, J-Space-model, HCU, training, canonical-semantics or whole-product credit.

## 1. Problem

The currently credited PyTorch nonterminal witness and the current native llama.cpp cvec witness do not apply the same intervention over token positions.

PyTorch reference semantics at the selected block output:

`hidden[:, -1, :] = hidden[:, -1, :] + vector`

Therefore only the final prompt-token residual state is changed.

Pinned native llama.cpp commit:

`bb4caa7540188872173c44d161602d9271386413`

implements cvec through `llama_adapter_cvec::apply_to()` as:

`ggml_add(ctx, cur, layer_dir)`

and Qwen3 applies `build_cvec(cur, il)` to the post-FFN residual tensor. When the entire prompt is decoded in one batch, the 1D layer direction broadcasts over every prompt-token row in that graph.

Therefore:

`NATIVE_CVEC_ALL_PROMPT_TOKENS != PYTORCH_LAST_TOKEN_ONLY`

This is a causal-scope difference, not merely an implementation detail.

## 2. Source-supported no-fork solution

A native last-token-only carrier can be approximated closely without modifying the Qwen3 graph:

1. create a fresh llama context;
2. leave cvec unset/disabled;
3. tokenize the complete prompt;
4. decode the prefix `[0 .. n-2]` with no cvec;
5. on the same context, enable the exact selected cvec;
6. decode only token `[n-1]` in a second `llama_decode` call;
7. read logits from that second decode.

The pinned public llama batch API states that when `batch.pos == NULL`, token positions are tracked automatically by `llama_encode` / `llama_decode`. Thus the second decode can continue after the cached prefix rather than restarting at position zero.

Because the second graph contains one input token, the 1D cvec broadcast has only that token position available. Prefix states and their KV-memory contribution were created before cvec was enabled.

Call this carrier:

`LAST_TOKEN_ONLY_SPLIT_PREFILL`

This is not claimed as bitwise identical to a one-shot PyTorch forward pass. It is a sharply matched causal carrier whose remaining differences can be measured.

## 3. Critical baseline law

Splitting prefill can itself change numerical behavior because graph shape, kernels, memory scheduling or quantized execution may differ.

Never compare a split-prefill intervention only against a one-shot baseline.

Required baselines:

- `NATIVE_ONE_SHOT_BASELINE`: full prompt, no cvec;
- `NATIVE_SPLIT_BASELINE`: prefix decode + final-token decode, no cvec.

Define:

`split_baseline_drift = metric(NATIVE_SPLIT_BASELINE) - metric(NATIVE_ONE_SHOT_BASELINE)`

If this drift exceeds a preregistered calibration-derived tolerance, stop semantic promotion and characterize decode-partition effects first.

## 4. Scope factorial

After all semantic/lexical/norm decisions are frozen, use this carrier matrix:

### Native

1. `NATIVE_ONE_SHOT_BASELINE`
2. `NATIVE_SPLIT_BASELINE`
3. `NATIVE_ALL_PROMPT_TOKENS_CVEC`
4. `NATIVE_LAST_TOKEN_ONLY_SPLIT_PREFILL_CVEC`

### PyTorch reference

5. `PYTORCH_LAST_TOKEN_ONLY`
6. `PYTORCH_ALL_PROMPT_TOKENS`

The PyTorch all-token condition is a bridge control, not a new semantic authority.

Primary contrasts:

- PyTorch LAST vs PyTorch ALL isolates token scope without changing checkpoint/runtime family;
- native one-shot baseline vs native split baseline isolates decode partitioning;
- native ALL vs native LAST isolates cvec token scope within the same native carrier family;
- PyTorch LAST vs native LAST tests matched-scope carrier transfer;
- PyTorch ALL vs native ALL tests matched-broadcast carrier transfer.

## 5. Scope-specific six controls

For each active cvec scope preserve:

- `BASELINE`
- `+VECTOR`
- `SIGN_FLIP`
- `NULL_VECTOR`
- `ORTHOGONAL_SAME_NORM`
- `PERMUTED_SAME_NORM`

Each intervention must be compared to its own scope-matched baseline.

`SIGN_FLIP` remains a sign control and MUST NOT be renamed lesion.

## 6. Receipt fields

Every native observation should bind at least:

- exact source repo/tree and dirty state;
- exact Qwen3-0.6B source checkpoint/tokenizer identity;
- exact Q8_0 GGUF digest;
- exact llama.cpp commit and binary/library digests;
- exact cvec bytes/digest;
- target layer;
- gain and residual-norm-relative magnitude where measurable;
- semantic derivation family digest;
- lexical nuisance/control digest;
- calibration and holdout family identities;
- semantic target and output-code mapping identity;
- `intervention_token_scope`;
- `decode_partition`;
- `prefix_decode_token_count`;
- `final_decode_token_count`;
- `cvec_active_during_prefix`;
- `cvec_active_during_final_token`;
- cvec set return code;
- prefix decode return code;
- final decode return code;
- baseline scope identity;
- split-baseline drift;
- six-control family digest;
- metric definition digest;
- threshold/pre-registration digest.

Allowed scope values:

- `ALL_PROMPT_TOKENS_ONE_SHOT`
- `LAST_TOKEN_ONLY_SPLIT_PREFILL`
- `NONE_ONE_SHOT_BASELINE`
- `NONE_SPLIT_BASELINE`

Unknown scope fails closed.

## 7. Strict semantic prerequisites

Do not execute this scope experiment as a promotion-bearing run until the candidate simultaneously satisfies:

1. vector derivation independent of output token labels;
2. semantic targets counterbalanced across AFFIRMATIVE-like, NEGATIVE-like and NEUTRAL-like states;
3. A/B/C code mapping independently counterbalanced;
4. model-facing derivation families lexically deconfounded from explicit pole-name shortcuts;
5. lexical nuisance vector/control present;
6. disjoint derivation, calibration and fresh holdout families;
7. operating point selected on calibration only;
8. intervention strength expressed relative to observed residual norm, not only a raw scalar gain;
9. per-family direction coherence / stability recorded;
10. semantic-target x intervention interaction metric frozen before holdout;
11. off-target drift criterion frozen before holdout;
12. token-scope condition frozen before holdout.

The current semantic native executor on canonical main at the time of this design does not yet satisfy this entire conjunction. Its existence is therefore not authorization to perform a promotion-bearing model run.

## 8. Acceptance classes

### A. STRICT_MATCHED_SCOPE_REPLICATION

Require:

- split baseline within tolerance;
- PyTorch LAST specific effect PASS;
- native LAST specific effect PASS;
- semantic-target interaction survives lexical, code, nuisance and matched controls;
- direction/sign relationship agrees under preregistered criterion;
- no material off-target violation.

This is the strongest carrier-equivalence result available without a custom native graph hook.

### B. BROADCAST_SCOPE_REPLICATION_ONLY

If native ALL and PyTorch ALL agree, but native LAST fails against PyTorch LAST, classify native evidence as broadcast-scope carrier replication only.

Do not call it last-token replication.

### C. TOKEN_SCOPE_ROBUST_SEMANTIC_COORDINATE

If both ALL and LAST native conditions independently pass the same target-specific pattern and their treatment interaction is within a preregistered equivalence band, the coordinate is robust across the tested token scopes.

This is stronger than one-scope steering but still not full Global J-Space/GWT evidence.

### D. SCOPE_MEDIATED_EFFECT

If native ALL passes while native LAST fails, and PyTorch LAST remains positive, infer that broadcast scope materially contributes to the native effect.

### E. DECODE_PARTITION_CONFOUNDED

If split baseline materially differs from one-shot baseline, do not adjudicate cvec scope until partition effects are isolated.

### F. SCIENTIFIC_NEGATIVE

If the strict semantic interaction does not survive the matched scope/control design, preserve the negative result. Do not retune on holdout.

## 9. Dimensionality sequencing

The newer three-state semantic simplex hypothesis should be tested after or alongside strict carrier equivalence, but dimensionality must not be inferred from one AFFIRMATIVE-vs-rest vector.

For three centered semantic class means, the class simplex spans at most two dimensions. A principled next representation test is therefore:

- estimate centered class centroids over lexically disjoint families;
- compute a preregistered rank/permutation-null test;
- retain rank 1 if the second singular component is null-like;
- promote to rank 2 only if the second component is stable and causal on fresh holdout;
- evaluate the full intervention-direction x requested-semantic-target treatment matrix.

Do not jump directly to an arbitrary high-dimensional J-Space.

## 10. Composition sequencing

Only after at least two independently promoted coordinates or a reproducible rank-2 subspace exist:

1. compare individual coordinate interventions;
2. compare naive vector sum;
3. compare simultaneous separate-layer injections;
4. measure cross-talk matrix and second-order interaction;
5. only then test multidimensional projector/conceptor-style control if single-vector composition is unstable.

Existing activation-steering research reports that naive merging of multiple steering vectors can fail while separate simultaneous interventions can work better. Recent conceptor work provides a plausible multidimensional successor but does not substitute for Qwen3-0.6B-specific causal evidence.

## 11. Global J-Space / GWT boundary

Even a strict semantic, scope-matched, rank-2 causal subspace is still local model-control evidence.

Global J-Space/GWT promotion additionally requires causal coordination/broadcast evidence across downstream consumers or HCU stages, with shuffle/block/rescue controls and exact causal identities.

No recurrence, semantic coherence, model self-report or majority vote can substitute for that intervention evidence.

## 12. Next exact source action

Extend the existing pinned native harness as one reusable scope parameter, not as a second J-Space implementation:

`scope = ALL_PROMPT_TOKENS_ONE_SHOT | LAST_TOKEN_ONLY_SPLIT_PREFILL`

and add a matched no-cvec split baseline.

Before any runtime:

- deterministic parser test rejects unknown scope;
- deterministic source regression proves cvec is not set before prefix decode in LAST mode;
- deterministic source regression proves final decode receives exactly one token;
- deterministic receipt validator requires scope and decode-partition identities;
- promotion gate rejects missing split-baseline evidence when LAST mode is claimed;
- semantic/lexical/norm guards remain independently mandatory.

A future runtime intervention still requires the current canonical atomic unusual-experiment coordination and current FREE_ONLY execution law.
