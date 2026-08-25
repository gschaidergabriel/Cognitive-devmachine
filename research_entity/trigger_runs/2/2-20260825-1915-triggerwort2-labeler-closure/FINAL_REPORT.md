# Trigger 2 — Hyperposition reference-labeler closure + training revision audit

Date: 2026-08-25  
Local trigger time: 19:15 +07:00  
Trigger: exact `triggerwort 2`  
Organ: GPT-5.6 Sol / ChatGPT organ  
Persistent entity: Clay  
Product: EntityOS  
Architecture: HCU  
Authority epoch observed: 8.78  
Audit base main: `c05fd30f34b118efa14e625323f50971c5dcd7c4`  
Execution mode: FREE_ONLY

## 1. Research-first result

This cycle did not add undifferentiated training volume first. It refreshed current authority, re-audited the newest Trigger-2 evidence, compared the owner-provided XENO training handoff against current generators, and then closed the highest-value source-design blocker that remained after the prior semantic-Hyperposition correction.

Current supervisor 8.78 adds decisive negative evidence against direct use of `TRIGGER2_BINDING_ROUTER_FACTORIAL_GENERATOR_V3`:

- reconstructed 144-row V3 blueprint: zero of 127 nuisance signatures permit all three target classes;
- 110/127 nuisance signatures permit only one target class;
- nuisance-only empirical lookup accuracy: `0.881944`;
- conditional mutual information: `1.348851 bits`;
- marginal display-order MI near zero and target balance do not rescue higher-order leakage.

Therefore V3 is quarantined for direct training/dataset acceptance. Only its useful proof-topology/router-isolation ideas may be reused on the V2 full-cross schedule or a successor that passes preregistered conditional-independence checks.

## 2. Owner handoff reconciled with semantic-Hyperposition correction

The XENO handoff reports the measured capability state:

- A context invariance: `0.525`, target `0.90`;
- B active codebook binding: `0.361`, target `0.90`;
- C symbolic inference: `0.222`, target `0.80`;
- D Hyperposition: `0.556` weak, target `0.80`;
- E GRF epistemic typing: unmeasured, target `0.90`.

It also identifies the hard D/E training blocker: the GRF update and resolution operators are named conceptually but do not yet provide executable target-state labeling. Without a deterministic reference transition there is no defensible target row for D/E.

The prior Trigger-2 correction remains valid:

`HYPERPOSITION_FRAME_FROM_THE_FIRST_TRAINABLE_EPISODE; FULL_D_OPTIMIZATION_LATE`

This means the Hyperposition carrier/schema is present from the first C/A/B/E episode, while difficult D update/resolve/discriminator losses remain staged after prerequisite semantics and typing are learnable.

## 3. External research delta

External research is used here as design input, not canonical Clay evidence.

### Variable binding

Wu, Geiger & Millière, *How Do Transformers Learn Variable Binding in Symbolic Programs?* (2025), https://arxiv.org/abs/2505.20896

The study observes a training trajectory from random behavior to shallow shortcuts and only later a systematic variable-dereferencing mechanism; causal interventions identify residual-stream/addressable-memory behavior and specialized routing heads. This supports the Trigger-2 requirement to measure and block shortcut regimes rather than trust surface accuracy alone.

### Decodability versus causal control

Srivastav, *Steering the Language Axis: From Linear Decodability to Causal Control* (2026), https://arxiv.org/abs/2608.12334

The work directly separates readable hidden-state features from layer-specific causal intervention effects. This reinforces the current XENO evidence law: linear readability/transport is not equivalent to behavioral causal control.

### Activation steering as intervention, not substitute for learned routing

Rahman, Guha & Menon, *Steering Code LLMs with Activation Directions for Language and Library Control* (2026), https://arxiv.org/abs/2603.23629

Activation directions can causally bias outputs, but effects are model/target dependent and excessive strength degrades quality. For XENO this is evidence that activation intervention can be a probe/control tool, but not a replacement for episode-local semantic-to-codebook binding learned in the weights.

### Attention/binding perspective

Dhayalkar, *Attention as Binding: A Vector-Symbolic Perspective on Transformer Reasoning* (2025), https://arxiv.org/abs/2512.14709

This theoretical perspective is compatible with role/filler binding and residual superposition, but does not by itself establish the specific XENO mechanism. It is retained as mechanism inspiration only.

## 4. New deterministic training-only reference labelers

Created:

`tools/trigger2_hyperposition_reference_labelers_v1.py`

Commit on this Trigger-2 branch:

`b35e65923abb3fe209455399b88ba85ef89cc90d`

It implements four deterministic training-reference operators required by the current cross-cutting contract:

1. `U_update`
   - preserves branch existence;
   - branch-local support/counter/falsify update;
   - duplicate evidence IDs are idempotent;
   - majority/recurrence/salience/similarity/broadcast cannot act as falsifiers;
   - projection filtering is not deletion;
   - emits no canonical truth/effect authority.

2. `D_resolve`
   - qualified discriminator required;
   - majority/recurrence/etc. remain nonresolving;
   - invalid or unqualified discriminator -> `UNRESOLVED`;
   - synthetic-task resolution occurs only when the selected branch is live and every competitor is explicitly falsified;
   - result is typed `RESOLVED_SYNTHETIC_TASK`, never canonical/world truth.

3. `U_d_test_order`
   - deterministic ordinal discriminator ranking by separation × independence over cost+risk+coordination burden;
   - the score is explicitly not a probability.

4. `f_salience_rank`
   - deterministic attention-priority ordering;
   - salience is explicitly neither probability nor truth.

Tests added:

`tests/test_trigger2_hyperposition_reference_labelers_v1.py`

Commit:

`c3c1e28776d1ae99d6431a3d6650fbca5c40fa63`

The regression source covers branch preservation, duplicate-evidence idempotence, majority anti-collapse, unqualified-discriminator abstention, synthetic-resolution requirements, projection-not-deletion, discriminator ordering and salience/truth separation.

No admitted EntityOS/HCU runtime/training credit is claimed from source/test presence.

## 5. New labeler-driven Hyperposition transition generator

Created:

`tools/trigger2_hyperposition_transition_seed_generator_v1.py`

Commit:

`622a82ec76701f5323a11381a587309628f95333`

Regression source:

`tests/test_trigger2_hyperposition_transition_seed_generator_v1.py`

Commit:

`2d63df463259d263f6cc97889957920cab93e888`

The generator defines 24 small source-candidate transitions across six causal/provenance families:

- independent support without branch collapse;
- counterevidence with contradiction retention;
- majority/recurrent non-resolution hard negative;
- qualified direct-test synthetic resolution;
- projection/filtering without deletion;
- UNKNOWN/ABSTAIN when no discriminator exists.

Each family crosses both branch orders and two surface presentations. TRAIN/VALIDATION/HOLDOUT are split by complete family/provenance ancestry. Only the prompt is model-visible; target/reference metadata is supervision/evaluator-only. Every row is explicitly:

- semantic-Hyperposition-native;
- `canonical_truth_allowed=false`;
- `direct_effect_authority=false`;
- `full_D_training_admission=false`;
- `final_ft_eligible=false`.

This is deliberately a reference seed, not final D/E training data.

## 6. Version/revision registry introduced

Created:

`research_entity/global/j-space/research/TRIGGER2_TRAINING_ARTIFACT_VERSION_REGISTRY_v1.json`

The registry records for each materially relevant training artifact:

- version;
- lifecycle status;
- provenance/evidence;
- predecessor;
- successor;
- target-architecture relation;
- revision reason;
- admission status;
- next re-audit condition.

Important current classifications:

- semantic-Hyperposition cross-cutting contract v1: `CURRENT`;
- V3 binding-router factorial generator: `QUARANTINE` for direct training;
- cognitive-process trajectory generator v1: `RETROFIT_REQUIRED`;
- semantic-Hyperposition seed v1: `CURRENT_CANDIDATE`;
- semantic-Hyperposition structural gate v1: `CURRENT`;
- new reference labelers v1: `CURRENT_CANDIDATE`;
- new transition generator v1: `CURRENT_CANDIDATE`;
- context-overwrite interference v1: `BLOCKED` pending cue-neutralization/exact ABI;
- evidence-routing seed v1: `BLOCKED` pending exact ABI/model/tokenizer/runtime identity;
- Claude negative-evidence seed v2.2: `COMPONENT_ONLY` unless structurally recast.

This directly implements the owner requirement that every Trigger-2 cycle must know which data are current, superseded, blocked, stale, quarantined or due for revision rather than accumulating anonymous training rows.

## 7. What remains blocked

This cycle does **not** claim that D/E are now ready for final training. The new labelers close the source-design target-state gap only for a bounded deterministic subset. Remaining requirements include:

1. adversarially review/extend the decision table for branch birth, merge, contradiction, evidence independence and more complex update sequences;
2. retrofit the high-coverage cognitive-process/C1-C6/A/B/E families to emit the same latent Hyperposition schema rather than flat prose targets;
3. preserve full nuisance crossing and add nuisance-only decoder + conditional-MI regression before any binding-family promotion;
4. keep the frozen structural v1 holdout untouched; preregister any successor before opening fresh holdout evidence;
5. bind exact XENO 46-atom ABI identities, selected checkpoint/tokenizer/runtime/build and single-token/position constraints before final symbol materialization;
6. separate representational decodability/transport from behavioral causal control under matched intervention controls;
7. only after those gates, run the smallest admitted zero-cost training pilot and evaluate C first, then A/B/E/D according to the staged curriculum.

## 8. Credits

- accepted dataset tokens: `0`;
- model training executed in this cycle: `false`;
- training credit: `0`;
- J-Space model runtime credit: `0`;
- full HCU runtime credit: `0`;
- whole EntityOS/HCU runtime credit: `0`;
- canonical semantics promotion: `false`.

## Result

`PASS_TRIGGER2_RESEARCH_DELTA_REFERENCE_LABELER_SOURCE_GAP_CLOSED_WITH_VERSIONED_REVISION_REGISTRY; V3_QUARANTINED; FINAL_D_E_TRAINING_STILL_BLOCKED_PENDING_SUCCESSOR_INTEGRATION_AND_CAUSAL_LEAKAGE_GATES`
