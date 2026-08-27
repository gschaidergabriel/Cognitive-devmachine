# HCU J-Space Observe / Control / Translate Architecture v1

Status: CURRENT ARCHITECTURE DELTA / SOURCE-CONTRACT ONLY
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Authority epoch observed before write: supervisor 8.73 / FREE_ONLY
Canonical main observed before write: `f042b0c081ca95cc2247be5b23dfe81f16c7b08c`

## 0. Purpose

This document converts the accumulated Trigger-1 / Global J-Space research into an explicit HCU architecture delta.

The central design change is that J-Space is no longer treated as one undifferentiated vector-steering idea. HCU SHALL separate three roles:

1. **J-Space Observation Plane** — measure/model internal state without claiming causal control.
2. **J-Space Control Plane** — apply exact, bounded, causal interventions when model/runtime access permits it.
3. **J-Space Translation Plane** — learn mappings between model-local latent spaces and a protocol-level shared communication representation without assuming that different models share native geometry.

This is a source architecture contract. It creates no model-runtime, J-Space-model, HCU-full, training, canonical-semantics or whole-product credit.

## 1. Non-negotiable authority boundary

J-Space is part of HCU cognition/compute, not a new truth store or effect authority.

Invariant:

`JSPACE_MEASUREMENT_OR_CONTROL != CANONICAL_FACT`

All J-Space observations, latent packets, translations, steering vectors, causal verdicts and workspace states remain measurements/candidates/projections until separately admitted by deterministic EntityOS authority.

Real/state-changing effects remain behind `EffectGate + EffectJournal`.

A high-confidence J-Space state MUST NOT mint factual truth merely because it is stable, recurrent, agreed across models, decodable, causally writable or translated successfully.

## 2. HCU placement

The target path becomes:

`Typed Entry`
` -> deterministic route / capability / generation admission`
` -> verified engine + loader consumption`
` -> model execution`
` -> J-Space Observation Plane`
` -> optional J-Space Control Plane`
` -> downstream model computation`
` -> J-Space causal receipts`
` -> optional Translation Plane`
` -> Global Workspace / Hyperposition packet`
` -> ActionCandidate / TrainingTrace`
` -> deterministic downstream admission`

No J-Space component may bypass Typed Entry provenance, source/model/runtime identity, generation boundaries or EffectGate.

## 3. Plane A — J-Space Observation Plane

### Responsibility

Observe internal model state at declared sites without changing it.

### Required model-local adapter

Each controllable model/runtime SHALL expose a model-specific `JSpaceAdapter` with at least:

- exact model/checkpoint identity;
- tokenizer identity;
- runtime/build identity;
- consumed-weight/loader identity when available;
- activation site identity (`layer`, component, token position/span);
- activation shape/dtype;
- extraction operator;
- source event/admission/inference identity;
- deterministic digest of measured activation/materialized derived representation.

### Observation classes

At minimum distinguish:

- `RAW_ACTIVATION_MEASUREMENT`
- `PROJECTED_LATENT_MEASUREMENT`
- `JACOBIAN_OR_READOUT_MEASUREMENT`
- `PROBE_SCORE_MEASUREMENT`
- `WORKSPACE_CANDIDATE_MEASUREMENT`

Decodability does not imply causality.

## 4. `JSPACE_TRACE_ABI/v1`

All new J-Space data generation SHOULD converge on a single trace envelope rather than ad-hoc experiment JSON.

Minimum logical fields:

- `schema = JSPACE_TRACE_ABI/v1`
- `causal_event_id`
- `admission_id`
- `generation`
- `model_id`
- `model_revision`
- `checkpoint_sha256`
- `tokenizer_sha256`
- `runtime_build_sha256`
- `loader_consumption_identity | UNKNOWN`
- `inference_receipt_id`
- `jspace_adapter_id`
- `activation_site`
- `token_position_policy`
- `observation_class`
- `activation_or_projection_sha256`
- `semantic_family_id`
- `task_family_id`
- `context_polarity_id | NONE`
- `split_id` (`CALIBRATION`, `DEV`, `CAUSAL_HOLDOUT`, `OOD_HOLDOUT`)
- `intervention_id | NONE`
- `control_class | NONE`
- `target_metrics`
- `off_target_metrics`
- `result_classification`
- `credit_scope`

Raw high-dimensional activations MAY remain private/local and be referenced by digest/object reference rather than committed to GitHub. Public/durable receipts SHALL not leak secrets or private prompt content.

## 5. Plane B — J-Space Control Plane

### Responsibility

Turn a measured/model-local representation into an explicit intervention only on runtimes that expose the required internal hook.

Normal black-box chat/completion APIs are **not** J-Space Control Plane implementations merely because prompts, logprobs or sampling parameters can alter behavior.

### `JSPACE_VECTOR_CONTROL_ABI/v1`

A control packet SHALL bind:

- source trace / derivation family identity;
- exact source model/runtime identity;
- target model/runtime identity;
- target activation site;
- vector/subspace identity and digest;
- construction method;
- explicit proof that holdout data was not used for derivation;
- gain policy and frozen calibration identity;
- token-position policy;
- intervention operator (`ADD`, `ABLATE`, `PROJECT_OUT`, `PATCH`, `SWAP`, `RESCUE`, bounded successor);
- matched control family;
- target metric definition;
- off-target metric definition;
- allowed magnitude/energy envelope;
- causal receipt identity after execution.

### Minimum causal control family

Promotion-bearing J-Space control SHOULD preserve at least:

- baseline;
- +target vector/intervention;
- sign flip where meaningful;
- null vector;
- orthogonal same-norm control;
- permuted/random same-norm control;
- wrong-layer/site localization;
- lesion/ablation;
- rescue;
- counterfactual swap/interchange when the causal claim requires a semantic variable rather than generic steerability.

## 6. Causal promotion ladder

Architecture-level J-Space capability is graded, not binary.

1. `JSPACE_OBSERVED` — reliable measurement only.
2. `JSPACE_DECODABLE` — held-out prediction from representation.
3. `JSPACE_CAUSALLY_WRITABLE` — intervention changes predicted target beyond matched controls.
4. `JSPACE_LOCALIZED_OR_DISTRIBUTED_WITH_SCOPE` — site dependence is measured rather than assumed.
5. `JSPACE_RESCUABLE` — lesion/corruption can be selectively rescued.
6. `JSPACE_COUNTERFACTUALLY_SWAPPABLE` — interchange follows a declared causal variable.
7. `JSPACE_OOD_TRANSFERABLE` — frozen control survives semantic/task-family shift.
8. `JSPACE_BROADCAST_REUSABLE` — same latent variable causally affects multiple independently scored downstream operations.
9. `JSPACE_SELECTIVE_WITH_BOUNDED_OFFTARGET` — target effect exceeds off-target damage under a declared bound.
10. `JSPACE_REPLICATED_MODEL_SPECIFIC` — exact model/runtime evidence survives independent held-out families/seeds.

No lower rung automatically implies a higher rung.

## 7. Required OOD / specificity architecture gates

Trigger-1 exposed that an in-family positive result can still be a narrow stance/output-bias axis. Therefore future `go` architecture work SHALL treat the following as first-class gates rather than optional analysis:

### A. Semantic OOD transfer

Freeze vector/layer/gain before OOD evaluation. Require per-family results and a worst-family margin, not only aggregate average.

### B. Direction coherence

Measure whether independent calibration subsets/families derive geometrically and behaviorally consistent directions. A lucky small-sample vector is not a stable J-Space coordinate.

### C. Full localization profile

Test the same selected vector at all predeclared candidate layers/sites when affordable. Nearest-wrong-layer alone is a minimal fence, not a full localization map.

### D. Token-position localization

Separate last-prompt-token effects from persistent multi-token/generation-state effects where the runtime permits this.

### E. Dose response

Measure monotonicity, saturation, sign reversal and off-target degradation over a frozen predeclared gain ladder.

### F. Off-target cross-effect matrix

Each promoted control dimension SHOULD report effects on unrelated behavior/task families. A large target effect with broad unrelated changes is a low-specificity actuator, not clean semantic control.

## 8. Plane C — J-Space Translation Plane

### Core law

**Do not assume shared native geometry across models.**

`MODEL_A_VECTOR_COORDINATES != MODEL_B_VECTOR_COORDINATES` unless exact evidence establishes an alignment at declared scope.

The shared HCU J-Space is initially a **protocol-level latent communication fabric**, not a universal Euclidean coordinate system.

### Translation architecture

Target path:

`Model A local activation`
` -> ModelA JSpaceAdapter`
` -> model-local latent representation`
` -> learned Translator A->Shared`
` -> JSPACE_LATENT_PACKET/v1`
` -> learned Translator Shared->B`
` -> ModelB JSpaceAdapter`
` -> bounded target-model intervention / prediction`

Direct pairwise `A->B` translators MAY be used as challengers/baselines. A central shared latent becomes justified only if it improves multi-model transfer and survives held-out models/tasks without collapsing into textual labels.

## 9. `JSPACE_LATENT_PACKET/v1`

A latent packet is a communication object, not factual truth.

It SHALL support unresolved/Hyperposition content rather than forcing one scalar label.

Minimum logical fields:

- `schema`
- source causal/admission/inference identities;
- source model/adapter identity;
- latent encoder/translator identity;
- latent vector/subspace reference + digest;
- uncertainty/calibration metadata;
- alternative/hyperposition references when applicable;
- semantic/task family identity if known;
- provenance/derivation family;
- allowed downstream consumers;
- translation confidence/coverage;
- `truth_status = CANDIDATE_MEASUREMENT_ONLY`;
- optional target translator identity;
- roundtrip / transfer receipt references.

The packet SHOULD be able to carry information that is richer than a natural-language summary, but no field may claim that richer information exists until measured.

## 10. One-month private trace program

The correct sequence is **data first, translator second**.

For the initial private J-Space period, EntityOS SHOULD collect only necessary, provenance-bound traces from authorized local/self-controlled models and keep high-dimensional private states out of public Git history.

After sufficient data exists, freeze a dataset version and evaluate translation hypotheses.

### Split law

Avoid leakage through near-duplicate episodes. Split by causal event/task/semantic family and time where appropriate, not randomly by individual rows only.

Recommended partitions:

- `TRANSLATOR_TRAIN`
- `TRANSLATOR_DEV`
- `CROSS_TASK_HOLDOUT`
- `CROSS_TIME_HOLDOUT`
- `CROSS_MODEL_HOLDOUT` when enough models exist
- `NEGATIVE_CONTROL_FAMILIES`

## 11. Cross-model communication acceptance

`JSPACE_LATENT_INTERMODEL_COMMUNICATION` is a hypothesis until all required evidence exists.

Minimum promotion tests:

1. **Prediction:** source latent predicts a target-model internal/downstream state better than text-only and trivial baselines.
2. **Roundtrip:** `A -> shared -> A` preserves declared task-relevant structure within bounded distortion.
3. **Cross-model transfer:** `A -> shared -> B` changes/predicts B in the predeclared direction on held-out families.
4. **Causal intervention:** translated state changes B beyond matched random/orthogonal/sham translations.
5. **OOD:** frozen translator survives unseen task/semantic families.
6. **Off-target:** translated control has bounded unrelated behavioral effects.
7. **Ablation:** removing the translated packet degrades the claimed information path.
8. **Text baseline:** demonstrate whether the latent channel carries useful information beyond an equivalent natural-language intermediate representation. If it does not, retain text as the cheaper interface.
9. **No shared-geometry shortcut:** direct cosine similarity across unrelated native model spaces cannot establish translation quality.
10. **Negative evidence retained:** partial/narrow transfer remains narrow transfer, never relabeled universal communication.

## 12. Black-box API boundary

External free APIs such as ordinary Groq/Mistral/OpenRouter/NVIDIA hosted chat endpoints MAY participate in HCU as text/reasoning engines, but without internal activation access they cannot receive direct J-Space model-runtime credit.

They may participate in:

- text baseline comparisons;
- semantic labeling/candidate generation;
- external reasoning;
- behavioral proxy modeling.

They SHALL NOT be represented as hidden-state/J-Space controlled unless the concrete provider/runtime exposes and proves an actual internal intervention primitive.

## 13. Dynamic control as challenger, not default

A future context-conditioned/dynamic gain controller MAY be evaluated after fixed-vector causal evidence exists.

Fixed, frozen control remains the scientific baseline because it is easier to falsify and attribute. Dynamic gain/policy promotion requires held-out improvement plus no unacceptable off-target increase and exact policy identity in receipts.

## 14. SAE / sparse feature integration

Sparse autoencoders or other feature decompositions MAY be used to inspect/refine candidate controls, but decomposition quality is not causal proof.

A reconstructed/refined vector must preserve or improve measured causal behavior under the same controls before it receives control credit.

## 15. HCU mode integration

### GRID10

J-Space packets are typed inter-cell coordination inputs/measurements. Logical cells do not imply independent physical models.

### COGSIM10

Allows bounded counterfactual J-Space candidate simulation without canonical truth promotion.

### WM_TEST

May test world-model/state hypotheses represented in J-Space; outputs remain noncanonical projections.

### NESTED_SIM

May perform high-cost nested counterfactual latent rollouts only when a discriminator justifies the cost.

### SCALEOUT

Scale logical J-Space producers/consumers while preserving shared physical-worker and provenance boundaries. Cross-model translators must remain explicitly model/version bound.

## 16. GO integration law

Future `go` macrocycles SHALL make J-Space architecture progress visible as concrete deltas under Track B and/or Track C rather than generic research narration.

Valid architecture deltas include:

- implement/extend `JSPACE_TRACE_ABI/v1`;
- implement model-specific `JSpaceAdapter`;
- wire `JSPACE_VECTOR_CONTROL_ABI/v1` to an admitted runtime;
- add OOD/off-target/localization/dose-response gates;
- emit causal TrainingTrace rows;
- build private trace retention/privacy boundaries;
- implement `JSPACE_LATENT_PACKET/v1`;
- implement translator training/evaluation after sufficient private data exists;
- add text-vs-latent communication baselines;
- integrate J-Space packets into GRID10/Global Workspace routing without creating a second truth/effect authority.

A `go` that touches J-Space SHOULD state exactly which layer changed:

`OBSERVATION | CONTROL | TRANSLATION | DATASET | WORKSPACE_INTEGRATION | NO_CHANGE_WITH_REASON`.

## 17. Near-term implementation order

The architecture does **not** justify skipping supervisor 8.73's higher-priority executable funnel work. The recommended order is:

1. close the current Forge->Distillery replay-stable identity/runtime gate;
2. preserve the lease-gated local Qwen3-0.6B causal discriminator;
3. normalize its receipts toward `JSPACE_TRACE_ABI/v1`;
4. add semantic OOD + off-target specificity to the promotion path;
5. accumulate private model-local traces;
6. only after sufficient data, train/test Translation Plane adapters;
7. promote a shared latent communication layer only if it beats text and pairwise baselines under OOD/causal controls.

## 18. Credit boundary

At creation of this architecture delta:

- whole EntityOS/HCU runtime credit: `0`;
- full HCU runtime credit: `0`;
- J-Space model runtime credit: `0`;
- translation/intermodel communication credit: `0`;
- training credit: `0`.

This document advances architecture and future `go` convergence only. Executable evidence must separately promote measured scope.
