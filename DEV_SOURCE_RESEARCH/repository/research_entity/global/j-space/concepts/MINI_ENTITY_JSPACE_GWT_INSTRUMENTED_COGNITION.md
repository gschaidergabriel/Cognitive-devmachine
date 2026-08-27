# MINI ENTITY — J-SPACE / GWT INSTRUMENTED COGNITION

Status: CURRENT CONCEPT
Owner direction date: 2026-08-23
Parent directive: `research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md`
Base product directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`

## Core decision

The approximately-1B local cognition module is not valuable only because it is small enough to run locally. Its strategic role is to become an **instrumentable cognition substrate** whose internal workspace can be measured, compared with explicit ClayCode reasoning, perturbed under bounded experiments, and trained against mechanistic evidence.

The Mini Entity therefore treats the combination

`small replaceable cognition model + Jacobian Lens observer + bounded GWT selector + ClayCode/GRF exterior + deterministic MiniUnifiedDB authority`

as one research architecture.

This does **not** make the language model the entity, the state authority, the effect authority, or evidence authority. The model remains replaceable cognition. The lens remains an observer/intervention instrument. MiniUnifiedDB plus deterministic gates remain authoritative.

## External evidence anchor

Anthropic's official 2026 Jacobian Lens reference implementation is:

`https://github.com/anthropics/jacobian-lens`

Companion paper:

`https://transformer-circuits.pub/2026/workspace/index.html`

Repository/paper facts admitted into this concept:

- the Jacobian Lens reads a residual-stream activation by transporting it with an average input-output Jacobian into the final-layer basis and decoding with the model's own unembedding;
- the reference implementation exposes `fit()` and `jacobian_for_prompt()` and supports open-weight Hugging Face decoder transformers; its README examples use Qwen and state that other HF decoders adapt cleanly;
- the paper's lenses use 1000 sequences of 128 tokens, while the reference README states that quality saturates quickly and approximately 100 prompts is usable;
- fitting cost is dominated by the model's own backward pass;
- the paper identifies a capacity-limited, selective J-space occupying only part of the residual representation and behaving in several experiments like a functional global workspace;
- ablation/intervention experiments causally affect complex reasoning behavior;
- counterfactual reflection training changes concepts represented in the J-space and changes behavior in uninterrupted contexts; ablating the implanted J-space directions reverses much of the observed behavior change in the reported experiments.

These findings were established primarily on Anthropic models and must not be silently generalized to Qwen3.5-0.8B without measurement.

## What is hypothesis, not fact

The following attractive claims are **research hypotheses** for Mini Entity and MUST NOT be encoded as truths before measurement:

- smaller models have intrinsically less polysemantic representations;
- a 0.8B model necessarily has a cleaner or smaller J-space than larger models;
- a lens for Qwen3.5-0.8B will fit in only a few minutes on every target consumer GPU;
- the additional lens memory will always be negligible;
- a fixed steering coefficient such as alpha `0.2..0.5` is universally safe;
- a GWT setting such as `max_slots=3` is optimal;
- a visible J-space concept is consciousness, subjective experience, canonical truth, or proof of reasoning correctness.

Each of these must be tested empirically on the exact checkpoint, quantization/runtime where applicable, prompt distribution and hardware under study.

## Architecture

### 1. Replaceable cognition substrate

Primary research substrate: `Qwen/Qwen3.5-0.8B` or the exact admitted successor selected by the owner training directive.

The substrate produces ClayCode cognition and remains runtime-replaceable. Its weights never own canonical entity state.

### 2. J-Lens observer

A Jacobian-Lens-compatible observer may attach to an admitted open-weight local cognition model during research/evaluation mode.

Observer inputs MUST bind:

- exact model/checkpoint digest;
- tokenizer identity/digest;
- exact fitted lens digest;
- fitting corpus identity/digest and sample count;
- lens implementation/version/commit;
- prompt/run identity;
- layer and token position;
- decoding/top-k parameters.

Observer outputs are typed `MEASURED_INTERPRETABILITY`, not `FACT` merely because a decoded token appears in the J-space.

A readout is a measurement of what an activation is disposed to make the model verbalize under the fitted lens. It is not a complete decode of all model computation.

### 3. GWT selector / bottleneck

Mini Entity adds a bounded **GWT selector** above raw J-Lens readouts.

Its job is to reduce a high-volume layer x position x vocabulary readout into a tiny typed workspace trace suitable for visualization and comparison with ClayCode reasoning.

Candidate signals may compete on:

- J-Lens rank/logit or normalized strength;
- persistence across adjacent layers/positions;
- novelty/change from the previous workspace snapshot;
- contradiction with current explicit ClayCode state;
- relevance to active GRF R0..R6 slots;
- task relevance where task metadata is explicitly supplied;
- stability across small prompt perturbations.

Initial experiments MAY use `max_slots=3`, but slot count is a configurable hypothesis, not an architectural constant. It must be swept against alternatives.

The GWT selector may summarize and broadcast observations. It may not mint truth or effects.

### 4. Dual-trace cognition

For instrumented runs, Mini Entity records two distinct reasoning traces:

`explicit_trace = ClayCode / GRF / Hyperposition / omega output`

`latent_trace = J-Lens / J-space workspace observations`

The research objective is **not** to force them to be identical. The objective is to measure their relationship.

Required comparison classes include:

- `AGREE` — explicit ClayCode concept and J-space concept align under an admitted mapping;
- `LATENT_ONLY` — J-space carries a task-relevant concept absent from explicit ClayCode;
- `EXPLICIT_ONLY` — ClayCode names a concept not detected by the lens;
- `CONTRADICTION` — explicit and latent traces support conflicting interpretations;
- `UNRESOLVED` — lens coverage/tokenization/strength is insufficient for a meaningful comparison.

No mismatch is automatically a model fault: the Jacobian Lens is incomplete and token-vocabulary-limited.

### 5. MiniUnifiedDB telemetry, separated from canonical truth

Instrumented observations may be persisted in a dedicated research/telemetry domain with provenance. Minimum fields SHOULD include:

- entity generation / run id;
- model digest;
- lens digest;
- prompt/input digest;
- layer;
- token position;
- top-k decoded J-space tokens and scores/ranks;
- selected workspace slots;
- explicit ClayCode GRF state digest;
- comparison classification;
- intervention id if any;
- pre/post behavior metrics;
- timestamp and implementation version.

This telemetry must never be joined into canonical application facts by default.

Required law:

`JSPACE_MEASUREMENT != CANONICAL_ENTITY_TRUTH`

`MODEL_SELF_REPORT != JSPACE_MEASUREMENT`

`JSPACE_MEASUREMENT != CONSCIOUSNESS_PROOF`

### 6. Causal intervention mode

Reading and steering are separate authority surfaces.

Default product/runtime mode is **observe-only**.

Ablation or vector steering is allowed only in an explicit research/evaluation mode with exact checkpoint/lens identity and bounded experiment metadata.

Intervention sequence:

`baseline -> observe -> select target direction -> bounded intervention -> rerun matched task -> compare behavior/J-space -> rollback`

A steering coefficient MUST be experimentally swept around zero. No fixed alpha range is canonical.

Required safeguards:

- baseline and intervention use matched prompts/seeds/settings where possible;
- negative and positive controls are included;
- output coherence/degeneration is measured;
- causal claims require reproducible behavioral deltas, not merely changed lens tokens;
- steering can never bypass grammar/type/schema/authority/generation/effect gates;
- no intervention writes canonical state unless the normal deterministic pipeline independently admits the resulting external evidence.

### 7. Counterfactual Clay Reflection Training

Anthropic's counterfactual reflection result creates a direct training hypothesis for ClayCog.

Mini Entity MAY add an experimental training lane called **Counterfactual Clay Reflection Training (CCRT)**:

1. take a task context before the decisive action/output;
2. append a reflection probe only in the training continuation;
3. train the model to emit a concise ClayCode GRF reflection covering relevant truth/authority/counterhypothesis structure;
4. remove the reflection probe at evaluation time;
5. test whether the uninterrupted context now shows stronger desired ClayCode/J-space structure and improved task behavior;
6. use J-Lens readouts to verify whether the trained concepts actually entered the workspace;
7. ablate/steer the corresponding J-space directions to test causal mediation.

CCRT is an experiment, not an automatic replacement for the current ClayCog curriculum. It must beat matched ordinary SFT controls and must not degrade generic capability, epistemic calibration, authority separation or OOD behavior.

### 8. Training/evaluation promotion gates

The approximately-1B cognition campaign gains a new mechanistic evaluation lane.

A tuned checkpoint SHOULD NOT be preferred merely because its text benchmark improves. Promotion research should compare at least:

- base checkpoint;
- ordinary ClayCog-tuned checkpoint;
- CCRT checkpoint if trained;
- a larger general-model reference where feasible.

Mechanistic measurements SHOULD include:

- J-Lens fit reproducibility and held-out readout quality;
- empirically identified workspace layer band;
- workspace occupancy/selectivity under controlled prompts;
- ClayCode/J-space agreement and contradiction rates;
- response to task perturbations;
- ablation sensitivity of reasoning-heavy vs automatic tasks;
- steering dose-response and collapse threshold;
- CCRT pre/post concept occupancy if applicable;
- whether mechanistic improvements survive OOD prompts rather than only training-like prompts.

No J-space score alone promotes a checkpoint.

### 9. Dashboard / synesthetic cognition view

The existing synesthetic cognition-visualization goal gets a concrete mechanistic substrate.

A live research dashboard SHOULD be able to display:

- model layer x token J-Lens readout;
- current bounded GWT slots;
- transitions/ignitions across layers;
- explicit GRF R0..R6 ClayCode trace;
- Hyperposition branches;
- omega candidates;
- agreement/contradiction edges between explicit and latent traces;
- intervention targets and pre/post deltas.

The visualization is an observer. It must visually distinguish measured internal readouts, model self-report, derived interpretation and canonical external truth.

## Why the small model is the lever

The architectural bet is deliberately narrower than "small models are more interpretable."

The leverage comes from **experimental tractability**:

- an approximately-0.8B open-weight model makes repeated forward/backward mechanistic experiments materially cheaper than frontier-scale models;
- exact weights and activations are locally accessible;
- lens fitting can be repeated for checkpoint variants rather than treated as a one-off expensive audit;
- ablations and steering sweeps can be run densely enough to produce dose-response curves;
- ClayCog training, mechanistic observation and causal intervention can be performed on the same replaceable cognition substrate;
- the resulting observer can become part of the Mini Entity research harness without granting the model or lens canonical authority.

This is the product-level leverage: **Mini Entity can be developed as an observable and experimentally steerable cognitive machine rather than a black-box local chatbot.**

## Immediate research sequence

1. Confirm exact Jacobian-Lens compatibility with the selected Qwen3.5-0.8B checkpoint/runtime.
2. Fit a baseline lens using a versioned generic corpus; start with the upstream approximately-100-prompt usable regime and compare with larger samples.
3. Identify the empirical workspace layer band instead of copying layer numbers from Claude experiments.
4. Measure occupancy/selectivity and choose an evidence-based GWT slot count.
5. Add dual-trace ClayCode/J-space telemetry.
6. Run matched reasoning/automatic-task ablations.
7. Run bounded steering dose-response sweeps with coherence controls.
8. Compare base vs ClayCog-tuned model.
9. If the signal is robust, build a small CCRT ablation against ordinary SFT.
10. Only then decide whether J-space-guided training becomes a required part of the final approximately-1B checkpoint recipe.

## Promotion law

J-Space/GWT instrumentation is now part of the Mini Entity cognition research concept, but no unmeasured assumption receives product PASS.

A strong outcome would be a cognition module whose explicit ClayCode reasoning, measured latent workspace and behavior can be triangulated and causally tested while MiniUnifiedDB remains the sole durable truth/state authority.
