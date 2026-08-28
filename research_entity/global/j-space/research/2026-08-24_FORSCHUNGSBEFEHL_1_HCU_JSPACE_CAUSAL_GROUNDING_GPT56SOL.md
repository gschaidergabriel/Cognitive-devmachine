# Forschungsbefehl 1 — HCU / Global J-Space causal grounding sweep

Date: 2026-08-24
Organ: GPT-5.6 Sol
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Research mode: evidence-first / FREE_ONLY / source-level synthesis
Canonical main inspected immediately before synthesis: `6fc9c1fea5f5a3de289af1cf245108c703a302b1`
Newest supervisor steering found on inspected main: `SUPERVISOR_STEERING_8_71.json`

## Scope

Research question:

> Can HCU / Global J-Space be grounded as a falsifiable, instrumentable causal compute/training architecture rather than remaining a metaphorical analogy to global workspace theory?

This sweep separates external evidence, repository evidence, transfer hypotheses, counterhypotheses, intervention design and promotion gates. It does **not** execute a new hidden-state intervention and grants no model/runtime/training promotion.

## Executive scientific verdict

### R0 — observed in current repository

The current EntityOS/HCU research surface already contains a materially stronger causal gate than the older three-arm J-Space discriminator. `HCU_JSPACE_LOCAL_INTERVENTION_BACKEND_GATE_V1.md` and `HCU_JSPACE_INTERVENTION_BACKEND_SELECTION_V1.md` require a five-condition causal family:

- `BASELINE_CLEAN`
- `BASELINE_CORRUPTED`
- `INTERVENTION_TARGET`
- `SHAM_CONTROL`
- `OFF_TARGET_CONTROL`

They also explicitly separate diagnostic readout from causal control, require method-matched placebo interventions, exact model/runtime/provenance binding and zero broad causal credit from probe quality alone.

### R1 — inference supported by external work

There is now a strong external methodological basis for treating workspace-like latent variables as **experimentally testable causal objects** rather than purely semantic interpretations. The 2026 Jacobian-Lens / workspace work reports interventions, swaps, ablations, flexible downstream use and capacity/selectivity phenomena in tested Claude-family models. Causal-abstraction work supplies a more formal criterion: align neural states with high-level variables and verify them using interchange interventions. Activation-patching and causal-tracing literature supplies controls for locality, corruption, rescue and distributed mechanisms.

### R2 — current strongest justified Clay hypothesis

`HCU_GLOBAL_JSPACE_CAUSAL_CONTROL_HYPOTHESIS`:

> On an exact target model/runtime identity, a bounded low-dimensional or sparse latent subspace exists whose content can be read out, deliberately perturbed, counterfactually swapped/rescued and reused by multiple independently scored downstream computations, with effects exceeding method-matched controls while off-target degradation remains bounded.

This is a **falsifiable research hypothesis**, not an established property of the current Qwen3.5-0.8B target.

### R6 credit boundary

Current model-specific Global J-Space runtime credit remains **zero** until exact admitted execution demonstrates the required causal properties on the exact target identity. External Claude/Qwen-2B findings are donor evidence only. They cannot mint Qwen3.5-0.8B, HCU-full, training or whole-EntityOS credit.

## Primary external evidence and relevance

### 1. Verbalizable representations / J-space / workspace-like function

Primary source:
- Wes Gurnee et al., *Verbalizable Representations Form a Global Workspace in Language Models* (2026): https://transformer-circuits.pub/2026/workspace/index.html
- arXiv: https://arxiv.org/abs/2607.15495

Source-level findings relevant to HCU:

- identifies a Jacobian-Lens-derived `J-space` of verbalizable internal representations;
- reports directed modulation, intermediate reasoning, flexible downstream use and selectivity;
- reports vector swaps/ablations that causally redirect model behavior in tested models;
- reports a limited-capacity intermediate-layer band and broader upstream/downstream composition for J-space vectors;
- explicitly states that this is a **functional analogy**, not a claim that transformer architecture reproduces the recurrent neural architecture proposed by brain GNW theories.

Transfer status to HCU target: `PLAUSIBILITY_AND_METHOD_DONOR_ONLY`.

### 2. Causal abstraction and interchange intervention

Primary source:
- Atticus Geiger et al., *Causal Abstractions of Neural Networks* (2021): https://arxiv.org/abs/2106.02997

Relevant principle:

A neural representation should not be promoted merely because it is decodable. A stronger claim aligns it with a high-level causal variable and tests whether **interchange interventions** on the neural representation reproduce the counterfactual behavior predicted by the high-level causal model.

Transfer status: `HIGH_VALUE_FORMAL_ACCEPTANCE_DONOR`.

### 3. Diagnostic signal is not necessarily causal control

Preprint:
- Aojie Yuan et al., *Hidden Error Awareness in Chain-of-Thought Reasoning: The Signal Is Diagnostic, Not Causal* (2026): https://arxiv.org/abs/2605.09502

Relevant reported result:

A highly decodable hidden error signal can fail as an intervention target; activation steering and patching may fail or damage coherence. This directly supports the current HCU invariant:

`DIAGNOSTIC_READOUT_PRESENT + INTERVENTION_NOT_PROVEN != CAUSAL_CONTROL_PRESENT`

Transfer status: `STRONG_COUNTEREXAMPLE_DONOR`, preprint status retained.

### 4. Causal steering can exist but be layer/direction specific

Preprint:
- Arnav Srivastav, *Steering the Language Axis: From Linear Decodability to Causal Control* (2026): https://arxiv.org/abs/2608.12334

Relevant reported result:

Qwen3.5-2B and Llama-family experiments report strong direction- and layer-specific causal steering with equal-magnitude random controls producing little effect in the reported setting.

Transfer status: `QWEN_FAMILY_MECHANISM_DONOR_ONLY`; it does not establish the same control geometry on Qwen3.5-0.8B.

### 5. GNW is scientifically useful but not settled biological truth

Primary source:
- Cogitate Consortium et al., *Adversarial testing of global neuronal workspace and integrated information theories of consciousness*, Nature (2025): https://doi.org/10.1038/s41586-025-08888-1

The preregistered multimodal human study reports results that support some predictions while substantially challenging key tenets of both GNWT and IIT. For HCU this is a methodological warning: use the workspace concept as a falsifiable functional/computational hypothesis, never as an argument from biological authority and never as consciousness evidence.

Transfer status: `ANTI-OVERCLAIM_GUARD`.

### 6. Jacobian-Lens implementation and current reproducibility warnings

Primary implementation:
- https://github.com/anthropics/jacobian-lens

Current code shows fitting excludes early positions using `SKIP_FIRST_N_POSITIONS = 16` and stores estimated Jacobians in fp32 during fitting.

Community-reported open issues, not primary-paper facts:
- https://github.com/anthropics/jacobian-lens/issues/5
- https://github.com/anthropics/jacobian-lens/issues/6
- https://github.com/anthropics/jacobian-lens/issues/2

Reported risks include input-token copying as a readout confound, using positions not represented in lens fitting, float16 serialization overflow for large Jacobians, and the fact that swap-intervention code is not simply supplied by the basic readout API.

Transfer status: `REPRODUCIBILITY_RISK_LEDGER`, requiring local verification rather than blind acceptance.

## HCU mapping

### Typed Entry Fabric

Role in scientific validity:

- binds causal event, admission, generation and provenance before cognition;
- prevents a causal experiment from silently mixing task/input identities;
- provides the root identity needed for clean/corrupted/counterfactual matching.

No neuroscience analogy is required. Its value is experimental provenance.

### HCU shared-weight/vector/inference/J-Space plane

Operational hypothesis:

- an activation site or distributed subspace can represent a candidate high-level variable;
- vector/subspace intervention is the actuator;
- model output, downstream internal state and task metrics are measurements;
- the plane becomes scientifically meaningful only if intervention effects are specific, counterfactually predictable and reproducible.

### Global J-Space/GWT layer

A useful HCU `workspace-like` claim should require more than decodability or one steering effect. Minimum property family proposed here:

1. `READABLE`: content can be measured with a declared lens/probe.
2. `CAUSALLY_WRITABLE`: targeted perturbation changes the predicted downstream variable.
3. `COUNTERFACTUALLY_SWAPPABLE`: interchange intervention produces the predicted counterfactual state/behavior.
4. `RESCUABLE`: restoring the hypothesized latent content reverses a corruption/ablation effect.
5. `BROADLY_REUSABLE`: the same encoded variable causally influences at least two independently scored downstream operations under held-out contexts.
6. `SELECTIVE`: routine/non-workspace computation remains substantially less dependent on it.
7. `BOUNDED_CAPACITY_OR_COMPETITION`: a predeclared load/competition manipulation produces a measurable, reproducible capacity signature rather than unrestricted accumulation.
8. `LOCALIZED_OR_DISTRIBUTED_WITH_DECLARED_SCOPE`: claims match the actual tested layer/component search scope.

A failure on one property should downgrade the corresponding property, not automatically destroy all lower-level causal-control evidence.

### Hyperposition

Hyperposition should be treated as a computational policy for preserving unresolved candidate states, not as evidence that those candidates are internally represented in a particular model geometry. Causal experiments may compare alternative candidate states, but majority/repetition cannot mint truth.

### EffectGate / EffectJournal

All model/J-Space outputs remain measurements or ActionCandidates. Even a validated causal latent does not become canonical world truth and cannot bypass deterministic effect authority.

### Training program

Training readiness should require admitted causal traces rather than semantic labels alone. A future specialized ~0.8B model should be trained/evaluated against interventions that preserve the intended causal abstraction, not merely against imitation of J-Space vocabulary.

## Serious counterhypotheses

### H0 — verbalization/readout basis masquerades as cognition

The measured J-space may mainly reflect alignment to future token output rather than a privileged control substrate.

Falsifier: interchange/rescue must predict and restore **nontrivial internal/downstream operations** beyond immediate lexical output.

### H1 — generic off-manifold damage masquerades as causality

Ablation/steering changes output simply because activations were damaged.

Falsifier: method-matched equal-energy sham/random-direction and same-site controls; target effect must exceed their effect while coherence/off-target metrics stay within predeclared bounds.

### H2 — input-copying or fitting-distribution confound

A lens reports concepts because they appear in the prompt or because measurement is performed at unsupported positions.

Falsifier: exclude prompt-copy positions where relevant, respect fitted position support, and use concept paraphrases/counterfactual labels not present verbatim in input.

### H3 — local feature control is mistaken for a workspace

One steerable latent can be a normal task feature rather than a broadcast workspace variable.

Falsifier: require broad downstream reuse/fan-out and selectivity/capacity evidence in addition to causal control.

### H4 — adaptive search overfits the intervention site

Repeated layer/site search can guarantee an apparently strong winner.

Falsifier: split `SITE_DISCOVERY` from `CAUSAL_HOLDOUT`; freeze layer/subspace/operator/magnitude before held-out evaluation.

### H5 — distributed mechanism is missed by single-site tests

A negative one-layer result may hide a distributed causal mechanism; a positive one-layer result may exaggerate centrality.

Falsifier: bounded multi-component search with matched-size/energy controls and a predeclared search budget.

### H6 — repeated multi-layer patching double counts the same causal content

Adding or restoring similar features at multiple layers can amplify an intervention beyond any natural trajectory.

Falsifier: constrained patching/rescue that preserves trajectory consistency and compares single-stage vs bounded multi-stage intervention.

### H7 — model-family transfer fails

Claude-family or Qwen3.5-2B geometry may not transfer to exact Qwen3.5-0.8B.

Falsifier: exact model-specific observation/intervention. External evidence has zero target-model credit until then.

### H8 — GWT analogy is semantically overextended

A feed-forward transformer may show functional workspace properties without the recurrent ignition/broadcast architecture claimed in biological GNWT.

Falsifier/guard: explicitly score functional properties separately; never infer brain-equivalence or consciousness from HCU/J-Space evidence.

## Proposed acceptance ladder v2

This is a research proposal, not canonical authority.

### Gate 0 — exact execution provenance

Require:
- exact checkpoint/tokenizer/runtime/build identity;
- loader-consumption identity or explicit UNKNOWN;
- causal event/admission/route/generation/InferenceReceipt binding;
- exact intervention and metric definitions.

### Gate 1 — diagnostic measurement integrity

Require:
- supported layer/position domain;
- no known prompt-copying confound in the measured condition;
- finite/stable Jacobian/readout values;
- frozen probe/lens calibration set distinct from causal holdout.

Promotion: `JSPACE_DIAGNOSTIC_READOUT` only.

### Gate 2 — current five-condition causal-control gate

Use the already-specified:
- clean;
- corrupted;
- target;
- sham;
- off-target.

Freeze target metric, sham policy, intervention magnitude and off-target bound before outcome inspection.

Promotion: bounded `JSPACE_CAUSAL_CONTROL_CANDIDATE` only.

### Gate 3 — causal rescue

Corrupt or ablate the hypothesized variable, then restore the clean/reference state at the declared locus. A successful rescue should recover the predicted behavior more than an energy/site-matched sham rescue.

Purpose: discriminate semantic correlation from a representation actually carrying needed information.

### Gate 4 — counterfactual swap / interchange intervention

Construct paired base/counterfactual examples whose high-level causal variable differs while nuisance structure is matched. Swap the candidate representation from the counterfactual run into the base run.

Primary metric: `INTERCHANGE_INTERVENTION_ACCURACY` or another preregistered causal-abstraction score.

Acceptance requires the observed counterfactual output/state to match the prediction of the declared high-level causal model better than matched controls.

### Gate 5 — double dissociation and specificity

Use at least two causal variables or two downstream functions. Demonstrate that intervention A selectively changes predicted outcome A more than B, while intervention B produces the complementary pattern where the theory predicts it.

Purpose: reject one-dimensional generic gain/damage explanations.

### Gate 6 — broadcast / fan-out

Test whether the **same frozen latent representation** is a valid causal argument to multiple independently scored downstream operations or contexts.

At minimum, define two distinct downstream function families before the run. A workspace-level claim requires target intervention effects in the predicted direction across both while matched non-J-space controls do not reproduce the pattern.

This is the main delta beyond the current local causal-control gate: one causal feature is not yet a global workspace.

### Gate 7 — selectivity and capacity/competition

Predeclare a load/competition protocol:
- number of simultaneously relevant concepts/tasks;
- insertion order or competition condition;
- measurement of retention, causal usability and degradation;
- matched non-workspace/control load.

A finite, reproducible capacity/competition curve would support a workspace-like selectivity claim. Failure should remove capacity evidence, not be hidden by post-hoc threshold changes.

### Gate 8 — replication and transfer

Require:
- held-out task families;
- multiple seeds/inputs;
- frozen intervention hyperparameters;
- exact Qwen3.5-0.8B model-specific execution;
- confidence intervals/effect distributions, not a single showcase;
- negative results retained.

Only after Gates 0–8 should a dataset row/family be considered for `JSPACE_VECTOR_CONTROL_ABI/v1` causal training admission. Even then, whole-HCU, whole-EntityOS, consciousness and factual-truth credit remain separate.

## Exact proposed discriminator: `JSPACE_CAUSAL_ABSTRACTION_DISCRIMINATOR/v2`

### Hypothesis

A frozen J-Space latent variable `Z` realizes a declared high-level causal variable `C` such that changing `Z` by a valid counterfactual intervention changes downstream behavior according to the causal model of `C`, not merely according to perturbation energy or lexical similarity.

### Data split

- `CALIBRATION`: choose candidate layer/subspace/operator only.
- `INTERVENTION_DEV`: tune magnitude inside predeclared bounds; never score final claim here.
- `CAUSAL_HOLDOUT`: frozen final examples/task families.

No holdout reuse for site search.

### Required condition family

1. `CLEAN`
2. `CORRUPTED`
3. `TARGET_ABLATION_OR_STEER`
4. `METHOD_MATCHED_SHAM`
5. `OFF_TARGET_CONTROL`
6. `CAUSAL_RESCUE`
7. `COUNTERFACTUAL_SWAP`
8. `COUNTERFACTUAL_SWAP_SHAM`

### Observables

- exact activation before/after digest and energy;
- target behavior metric;
- counterfactual prediction match;
- output KL / logit delta where appropriate;
- coherence or task-validity score;
- off-target regression;
- downstream function-family scores;
- layer/site/subspace identity;
- causal event/admission/generation/model-execution identity;
- all nulls/failures.

### Control law

For vector steering: equal-norm random-direction control at the same locus and magnitude.

For patching/replacement: same mechanism/site with donor information chosen to remove the hypothesized causal content while preserving patch machinery.

For distributed intervention: size/energy-matched alternative component set.

### Acceptance law

All numeric effect thresholds and uncertainty rules must be frozen before final holdout execution. Do not choose a threshold after seeing the target/control separation.

Required qualitative relations:

- target effect > method-matched sham under the predeclared statistical rule;
- rescue restores the predicted effect more than rescue-sham;
- counterfactual swap moves the model toward the **specific preregistered counterfactual prediction**, not merely away from baseline;
- off-target degradation stays within its predeclared bound;
- fan-out succeeds on the preregistered downstream function families;
- results replicate on held-out families under frozen intervention parameters.

If only the first relation passes, retain `LOCAL_CAUSAL_FEATURE_CANDIDATE`; do not label it a global workspace.

## Measurement guard additions recommended for current HCU source

1. Add explicit `lens_supported_position=true|false` and fitting support metadata to J-Space observation receipts.
2. Add `prompt_copy_confounded=true|false|unknown` when interpreting verbalizable-token readouts.
3. Add finite-value checks and serialization dtype to every stored Jacobian digest/summary.
4. Add `site_selection_split` and `site_selection_frozen_before_holdout` fields.
5. Add `intervention_energy` plus control-energy equality/tolerance fields.
6. Add `causal_rescue_present`, `counterfactual_swap_present`, and `interchange_intervention_score` fields to successor causal receipts.
7. Add `downstream_function_family_ids` and a minimum preregistered fan-out count for any future `WORKSPACE_LIKE_CAUSAL` promotion.
8. Add explicit `workspace_property_credits` as independent booleans/statuses so readout/control/fan-out/capacity are not collapsed into one Goodhartable score.

## What the current repository already gets right

The current source already contains several safeguards strongly supported by this sweep:

- diagnostic readout is separated from causal control;
- causal intervention requires a method-matched placebo;
- off-target behavior is measured;
- exact model/runtime/provenance is part of the gate;
- a single positive site cannot promote a global architecture;
- external model evidence cannot promote the exact local target;
- current intervention execution requires the canonical unusual-experiment lease;
- model/J-Space outputs remain noncanonical candidates/measurements.

The research delta is therefore **not** to replace the current gate. It is to extend the promotion ladder from `causal feature` to `workspace-like causal abstraction` using rescue, interchange, fan-out and capacity/selectivity evidence.

## Execution decision for this invocation

No hidden-state intervention was executed in this research command. The requested research sweep is source/literature work, and the current unusual-experiment law requires a canonical create-only atomic lease before a new intervention. No reproducible shared lease identity was established for this invocation.

Therefore:

`COORDINATION_BLOCKED_ZERO_NEW_UNUSUAL_EXPERIMENTS`

Ordinary research, source inspection and this durable research write are permitted.

## Next exact executable gates

### Ordinary / no unusual lease required

On an exposed authorized zero-cost local surface:

1. re-enter current main and authority;
2. identity-bind an already-present exact local `Qwen/Qwen3.5-0.8B` snapshot without network download;
3. execute observation-only J-Space probe at frozen supported positions;
4. include the measurement guards above;
5. retain zero causal credit.

### Future intervention / lease required

After a valid canonical atomic claim:

1. run the existing five-condition local intervention family first;
2. if it passes, run causal rescue;
3. then run paired counterfactual swap / interchange intervention on a held-out task family;
4. only after causal abstraction survives controls, run multi-downstream fan-out and capacity/competition tests;
5. promote each workspace property separately rather than minting one monolithic J-Space PASS.

## Credit ledger

- External literature grounding: `STRONG_METHOD_AND_PLAUSIBILITY_DONOR`
- HCU/J-Space source-contract quality: `ADVANCED`
- Exact Qwen3.5-0.8B diagnostic runtime credit from this invocation: `0`
- Exact Qwen3.5-0.8B causal-control credit from this invocation: `0`
- Workspace-like causal abstraction credit: `0`
- Full HCU runtime credit: `0`
- Whole EntityOS/HCU runtime credit: `0`
- Training credit: `0`
- Consciousness claim: `NOT_IN_SCOPE_AND_NOT_SUPPORTED`

## Final research conclusion

HCU / Global J-Space is now scientifically defensible **as an explicit causal research program** because its hypothesized latent variables can be subjected to well-defined interventions, controls, counterfactual swaps and causal-abstraction tests. That is materially stronger than metaphor.

However, the project does not yet possess model-specific evidence that the exact local ~0.8B target actually implements a global workspace. The current five-condition gate can establish a bounded causal feature/control candidate. To justify the stronger `workspace-like` label, the next evidence ladder must add counterfactual rescue/swap, causal-abstraction consistency, broad downstream reuse/fan-out, selectivity/capacity and held-out replication.

This distinction is the central result of Forschungsbefehl 1:

`IMPLEMENTABLE_CAUSAL_HYPOTHESIS != DEMONSTRATED_TARGET_MODEL_WORKSPACE`
