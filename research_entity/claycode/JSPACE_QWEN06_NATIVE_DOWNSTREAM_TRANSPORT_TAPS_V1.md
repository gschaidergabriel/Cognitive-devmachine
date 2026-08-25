# Qwen3-0.6B J-Space — Native Downstream Semantic Transport Taps v1

Date: 2026-08-25

Organ: GPT-5.6 Sol

Product: EntityOS

Architecture: HCU

Mode: FREE_ONLY

Evidence class: SOURCE/RESEARCH DESIGN ONLY. No runtime/model/J-Space/HCU/training/canonical-semantics/whole-product credit is created by this file.

## 1. Research question

A cvec intervention can change output logits without proving that a stable semantic state is transported through downstream nonterminal computation.

Two competing mechanisms can produce the same output effect:

- **semantic transport**: the intervention changes an internal semantic coordinate/subspace that persists through later layers and causally supports the output decision;
- **narrow control/readout shortcut**: the intervention perturbs a local route whose downstream semantic geometry is weak or absent but whose effect reaches the output head.

A model-specific J-Space claim should distinguish them.

## 2. Exact pinned llama.cpp capability

Pinned llama.cpp source identity used by the current native Qwen3-0.6B path:

`bb4caa7540188872173c44d161602d9271386413`

At this commit `src/llama-ext.h` exposes staging APIs:

- `llama_set_embeddings_layer_inp(ctx, lid, true)`
- `llama_get_embeddings_layer_inp(ctx, lid)`

The API is explicitly marked WIP/staging and must therefore remain pinned to exact source/build identity.

`llama_context::set_embeddings_layer_inp()` toggles the requested layer-input tap and sets `sched_need_reserve = true`.

During decode, `llama_context::extract_layer_inputs()` copies the graph result's layer-input tensor into a context buffer with token-row offsets.

The Qwen3 graph stores `inpL` as the input of each transformer layer. Because cvec is added at the end of a selected layer before assigning `inpL = cur`, the input of the **next** layer is the first direct post-cvec observable state.

Thus, for an intervention applied at layer 20:

- tap 20 = pre-intervention input to layer 20;
- tap 21 = immediate post-layer-20 / post-cvec state entering layer 21;
- taps 22..27 = progressively transformed downstream residual states;
- tap `n_layer` = last-layer output / input to the final head, according to the pinned context implementation.

Indexing must be verified against exact pinned Qwen3 graph source before runtime and recorded in the receipt.

## 3. Combine with scope-matched split-prefill

For `LAST_TOKEN_ONLY_SPLIT_PREFILL`:

1. decode prefix with cvec disabled and downstream taps disabled;
2. after prefix completion, enable the exact cvec;
3. enable only the preregistered downstream layer-input taps;
4. decode exactly the final prompt token;
5. extract each requested layer input;
6. evaluate output logits from the same final-token decode.

This is especially clean because the tap buffer for that decode contains one current token row, avoiding ambiguity about which prompt position is being scored.

For `ALL_PROMPT_TOKENS_ONE_SHOT`, either extract the final prompt-token row explicitly from each tapped layer or classify the result as all-token/broadcast evidence. Do not mix row semantics across scopes.

## 4. Independent semantic probes

Do not score a tapped activation with the same exact vector that was used as the intervention and call that independent transport evidence.

At least one downstream measurement must be independently derived.

Recommended cross-fitted design:

- intervention direction/subspace derived from scenario-family block `D_intervene` at layer 20;
- downstream probe direction/subspace derived from disjoint scenario-family block `D_probe` at downstream layer `k`;
- calibration family `C` selects only preregistered operating point/tap choices;
- fresh holdout family `H` is unopened until all decisions freeze.

No output A/B/C token identity may enter intervention or downstream probe derivation.

For three semantic states, estimate centered class geometry and allow rank 1 or rank 2 according to a preregistered within-scenario permutation-null criterion rather than assuming dimensionality.

## 5. Scenario blocking

Lexically different prompt families can confound semantic class with scenario/domain geometry.

Construct matched triplets within each scenario skeleton:

- same underlying situation/content;
- one AFFIRMATIVE-like target variant;
- one NEGATIVE-like target variant;
- one NEUTRAL-like target variant;
- avoid explicit pole-name tokens and obvious synonyms in model-facing derivation text;
- store semantic class in experiment metadata, not as a model-facing label.

Center activation contrasts **within scenario family** before aggregating across families.

Use equal scenario-family weighting.

A global centroid separation without within-family semantic consistency is not promotion evidence.

## 6. Transport metrics

For a frozen downstream semantic probe `p_k` at layer-input tap `k`, define a scalar signed semantic coordinate:

`z_k = dot(h_k, p_k)`

For rank-2 probes use the frozen 2D coordinates or equivalent projector score.

For every case and control measure:

`delta_z_k = z_k(intervention) - z_k(scope_matched_baseline)`

and the output semantic metric:

`delta_y = output_metric(intervention) - output_metric(scope_matched_baseline)`

Primary transport requirement:

- target-specific sign-sensitive `delta_z_k` survives on fresh scenario families;
- the effect persists across at least one preregistered downstream tap beyond the immediate `k=21` state;
- null/orthogonal/permuted/label-nuisance controls do not reproduce it;
- sign flip changes/reverses the preregistered transport pattern;
- downstream transport and output effect agree in semantic target direction.

Do not require monotonic transport magnitude across layers; downstream computation may rotate/rescale the representation. Require class-selective information under the independently derived probe/subspace instead.

## 7. Multi-tap trajectory

A useful first trajectory for a layer-20 intervention is a sparse preregistered set such as:

`21 -> 24 -> 27 -> final-head-input`

Exact indices must respect Qwen3's 28-layer indexing and pinned API semantics.

This gives four qualitatively different outcomes:

### A. persistent transport

Semantic displacement remains independently detectable through multiple later taps and corresponds to the behavioral effect.

### B. rapidly decaying transport

Strong at 21, weak/null by 24/27 while output still changes. This is evidence for a local perturbation or nonlinear route, not automatically a persistent workspace coordinate.

### C. delayed re-emergence

Weak immediately but stronger later. This suggests nonlinear transformation/routing and motivates subspace rather than fixed-vector matching across layers.

### D. output-only effect

No independent downstream semantic displacement despite output change. Classify as a narrow readout/control-path shortcut at this scope.

## 8. Mediation-style strengthening

Correlation between `delta_z_k` and `delta_y` is not sufficient causal mediation evidence.

A stronger later test should add a downstream intervention at tap/site `k`:

- source intervention at layer 20 changes `z_k` and output;
- downstream lesion/removal of the transported semantic component reduces the output effect;
- downstream rescue restores it;
- matched sham/orthogonal lesion does not reproduce the pattern.

Native true lesion still requires a live tensor transformation mechanism; the public layer-input tap is observation only. Do not rename sign flip as lesion.

## 9. Public-API stability boundary

The required layer-tap calls live in pinned `src/llama-ext.h`, whose own source says it is a staging/WIP API with breaking changes allowed.

Therefore every positive runtime receipt must bind:

- exact llama.cpp commit;
- exact `llama-ext.h` digest;
- exact linked library digest;
- exact harness binary/source digest;
- requested tap indices;
- extracted activation byte identity or digest;
- row/token identity;
- intervention scope;
- cvec identity;
- decode partition and return codes.

A result produced on a different llama.cpp revision is a new runtime identity and requires re-admission.

## 10. Harness successor design

Do not modify the existing credited v1 harness.

Extend the source-only scope donor with a separate successor, e.g.:

`tools/trigger1_native_llamacpp_cvec_scope_transport.cpp`

It should:

1. include the exact pinned `llama-ext.h` in addition to the public header;
2. accept a preregistered list of downstream tap layers;
3. for split-prefill, enable taps only after natural prefix decode and before final-token decode;
4. extract exactly the final-token row per tap;
5. write each raw F32 activation to a deterministic per-case file rather than only emitting a self-selected scalar score;
6. output file byte count and path in the runtime observation;
7. let the Python adjudicator hash the raw bytes and apply independently frozen probes;
8. never derive or select the downstream probe inside the native harness;
9. fail closed if a tap is outside `[0, n_layer]`;
10. fail closed if the expected row width is not exactly `n_embd` for split-final-token mode.

Keeping raw activation extraction separate from semantic adjudication prevents the native harness from silently becoming a second measurement authority.

## 11. Deterministic source tests before runtime

Required source-level regressions:

- unsupported tap index -> fail;
- duplicate tap index -> fail or deterministic deduplication with explicit receipt;
- split mode enables no tap before prefix decode;
- split mode enables cvec and taps only before the one-token final decode;
- extracted split row width == `n_embd`;
- all-token mode explicitly selects final prompt-token row;
- output activation paths are deterministic and collision-safe per case/tap/scope;
- no probe/semantic label enters native harness scoring;
- raw activation files and output observations carry exact tap/scope identities;
- failure to extract any required tap -> entire case fails closed.

## 12. Scientific promotion boundary

A positive result from this design can strengthen evidence from:

`native intervention changes output`

toward:

`native intervention changes an independently measurable nonterminal semantic state that persists through downstream computation and corresponds to output behavior`.

Even that is still bounded model-specific causal evidence. It does not establish Global J-Space/GWT broadcast across HCU cells, canonical truth, whole HCU, whole EntityOS, or training success.
