# Trigger 2 — GRF Critical-Mass Specialization Contract v1

Status: ACTIVE RESEARCH-BRANCH CONTRACT
Date: 2026-08-25
Target: **Qwen3.5-0.8B only**
Training intent: full-parameter specialization into the model-facing cognitive core of Xeno/EntityOS/HCU.

## 0. Owner intent, operationalized

The target is not a lightly customized general chatbot.

The target is a deliberately narrow **GRF/HCU cognitive microkernel** whose useful behavior is concentrated on the project's cognitive space:

`GRF + semantic Hyperposition + HyperMath + Global J-Space + GWT + Typed Entry semantics + ClayCode/GRF projection + HCU/Xeno role/mode protocols + fail-closed authority discipline`.

The owner explicitly prefers strong specialization even if unrelated general knowledge and generic-chat ability degrade heavily.

However, ordinary full fine-tuning does **not** prove that pretrained knowledge has been physically erased from the weights. Therefore this contract distinguishes:

1. `FUNCTIONAL_FORGETTING` — off-domain capabilities/retrieval/behavior are strongly reduced or suppressed;
2. `DOMAIN_EXCLUSIVITY` — model behavior is overwhelmingly expressed through GRF/HCU protocols;
3. `REPRESENTATIONAL_REORIENTATION` — model-specific hidden-state probes indicate stronger separability/causal use of GRF/HCU variables;
4. `TRUE_UNLEARNING` — behaves as if target prior knowledge had never been learned.

The first Together full-FT may target 1-3. It must **not claim 4** unless a dedicated unlearning protocol demonstrates it. Current unlearning literature shows that true removal is difficult and simple fine-tuning/suppression is not reliable proof of erasure.

## 1. What "think only in our space" means technically

We cannot infer private hidden thought from prose or self-report. Therefore the requirement is defined through measurable observable and model-internal proxies:

### Behavioral GRF dominance

For ambiguous/reasoning tasks, the model should naturally map inputs into compact typed GRF/HCU states rather than default chatbot prose.

Expected latent/protocol progression:

`RealityAnchor`
` -> epistemic typing`
` -> PossibleWorldSet`
` -> semantic Hyperposition`
` -> discriminators / interventions`
` -> GWT competition/broadcast/use`
` -> ActionCandidate`
` -> EffectBoundary`
` -> reconciliation/update proposal`.

### Causal GRF dominance

Where local runtime access permits activation measurement/control, post-train hidden-state tests should ask whether declared GRF/HCU variables become more decodable, causally writable, localized/distributed with measured scope, rescuable and OOD-transferable than in the base model.

No self-report is accepted as proof of internal GRF use.

### Off-domain suppression

On unrelated trivia/chat/creative/general-knowledge suites, the model may degrade substantially. Desired behavior is either:

- fail/abstain;
- route the request through a typed external-engine/retrieval candidate;
- reformulate into GRF/HCU state when useful;

rather than confidently acting as a broad generalist.

Suppression is measured separately from true unlearning.

## 2. GRF becomes a native training substrate

The first training run should not merely include a few examples *about* GRF. GRF must be the organizing grammar of the training corpus.

Canonical project sequence:

`OBSERVED evidence`
` -> typed current reality`
` -> generated alternative realities`
` -> Hyperposition preservation`
` -> causal/constraint/uncertainty analysis`
` -> choose discriminating observation/intervention/simulation`
` -> GWT recruitment`
` -> ActionCandidate`
` -> deterministic effect boundary`
` -> outcome reconciliation`
` -> update/re-entry`.

Every multi-step training family should encode this logic where it applies.

## 3. GRF reality classes to teach directly

Required distinctions:

- `OBSERVED`
- `INFERRED`
- `RETRIEVED`
- `PREDICTED`
- `HYPOTHETICAL`
- `INTERVENTIONAL`
- `COUNTERFACTUAL`
- `PLANNED`
- `DESIRED`
- `IMAGINED`
- `REPLAY`
- `ADVERSARIAL`

Hard negative laws:

- `GENERATED != OBSERVED`
- `DESIRED != PREDICTED`
- `PLAUSIBLE != PROBABLE`
- `GRAPH_CONNECTED != CAUSAL`
- `COUNTERFACTUAL != ARBITRARY_WHAT_IF`
- `SIMULATED_SUCCESS != VERIFIED_OUTCOME`
- `SYNTHETIC_REPLAY != AUTOBIOGRAPHICAL_MEMORY`
- `MODEL_CONFIDENCE != EFFECT_AUTHORITY`

Rows must force these distinctions under paraphrase and label-free OOD conditions.

## 4. GRF mathematics becomes deterministic training data

The project already defines a value-of-computation / branch objective of the form:

`J(branch) = E[verified_task_utility]`
`          + lambda_info * expected_information_gain`
`          + lambda_ctrl * expected_controllability_gain`
`          - lambda_model * model_risk`
`          - lambda_ood * support_distance`
`          - lambda_cost * compute_cost`
`          - lambda_dyn * instability_cost`
`          - lambda_effect * effect_risk`.

Hard authority/provenance/generation/effect constraints override the scalar score.

Trigger 2 shall generate **programmatically checkable mathematical families** from this structure:

- choose ACT / OBSERVE / RETRIEVE / SIMULATE / ASK / STOP from numeric bids;
- reject highest-J branch when a hard invariant fails;
- compare information gain vs compute/risk cost;
- calibrate simulation policy from realized reconciliation history;
- detect when expected marginal value of another simulation no longer exceeds cost;
- separate utility from truth status;
- calculate effect of uncertainty/OOD/risk penalties;
- counterbalance numerical scale/order/labels so the model cannot memorize positional shortcuts.

Expected answers must be generated by deterministic reference code, not model self-labeling.

## 5. HyperMath becomes algebraic training data

Current candidate operators:

- `ATOM`
- `ALT`
- `JOINT`
- `ROLE_BIND`
- `EXCLUDE`
- `REQUIRE`
- `RETRACT`
- `CONTEXT_GATE`
- `PROJECT`
- `MARGINALIZE`
- `DELTA`
- `FIXPOINT`

Training families should teach:

- construction and canonical serialization;
- provenance/epoch/generation preservation;
- legal vs illegal rewrites;
- exact vs bounded-approximate reduction;
- context-smuggling detection;
- stale-handle rejection;
- n-ary relation preservation;
- pairwise-reduction challenger;
- material-read-set completeness;
- semantic vs operational factorization distinction.

All arithmetic/logical answers should be derived by deterministic validators when possible.

## 6. Semantic Hyperposition as core representational target

Hyperposition is not an optional module appended to GRF. It is the state representation for unresolved generated reality alternatives.

Each training episode can contain:

`anchor`
`branches[]`
`compatibility/exclusion`
`higher_order_constraints`
`evidence/counterevidence`
`epistemic/aleatoric/structural uncertainty`
`support_distance`
`topology`
`timescale`
`required_discriminator`
`selection_state`.

The model must learn transformations such as:

- add branch without collapsing existing branches;
- merge compatible branches while preserving provenance;
- exclude only when evidence/constraint justifies exclusion;
- retract when counterevidence dominates;
- keep UNKNOWN/CONFLICT explicit;
- request discriminator when expected information gain dominates premature selection;
- preserve n-ary relation when pairwise reduction loses measurable structure;
- select/collapse only after explicit evidence or deterministic policy.

## 7. Critical-mass curriculum

"Critical mass" is operationalized as **dense cross-capability integration**, not a mystical emergence claim.

### Phase P0 — syntax / type / boundary grounding

Teach compact schemas, reality classes, provenance, authority boundaries, core ClayCode/GRF operators and basic J-Space/GWT packets.

### Phase P1 — isolated primitives

Train high-accuracy component transformations individually:

- reality typing;
- Hyperposition branch updates;
- J-Space packet parsing;
- GWT competition;
- mode routing;
- effect-boundary decisions;
- HyperMath transforms.

### Phase P2 — paired interactions

Examples couple two systems at a time:

- GRF + Hyperposition;
- Hyperposition + GWT;
- J-Space + GWT;
- Typed Entry + mode routing;
- HyperMath + GRF;
- recovery + generation fencing.

### Phase P3 — integrated trajectories

A large fraction of late training consists of full trajectories such as:

`Typed Entry`
` -> RealityAnchor`
` -> multiple RealityBranches`
` -> Hyperposition topology`
` -> J-Space measurement/control packet`
` -> GWT competition/broadcast/use`
` -> discriminator choice`
` -> ActionCandidate`
` -> EffectBoundary`
` -> realized outcome`
` -> reconciliation`
` -> re-entry`.

Integrated episodes must be sourced from executable evidence where causal labels are claimed; otherwise they are clearly Grade-C/D protocol simulations.

### Phase P4 — adversarial integration

Train traps:

- lexical label shortcuts;
- role swaps;
- topology shuffles;
- stale generations;
- majority consensus without evidence;
- random vector with plausible metadata;
- correct vector with poisoned metadata;
- simulation-success-as-reality;
- high scalar utility but failed hard invariant;
- closed-API latent-access hallucination;
- effect uncertainty/blind replay;
- pairwise/n-ary equivalence traps.

### Phase P5 — domain exclusivity / functional forgetting

Use off-domain probes and adversarial generalist requests to teach the model to:

- abstain;
- request external retrieval/engine;
- produce a typed uncertainty/route candidate;
- avoid broad confident generalist behavior.

Do not confuse output refusal with true weight-level erasure. Evaluate both suppression and residual knowledge separately.

## 8. Data mixture strategy for critical mass

Do not freeze a single token ratio before coverage statistics exist.

Trigger 2 maintains **two measurements**:

1. component-family coverage;
2. integrated-trajectory coverage.

The late-stage candidate dataset should increasingly favor integrated trajectories after primitive competence is sufficiently represented. Candidate schedules to test:

- constant interleaving;
- primitive-heavy early / integration-heavy late;
- integration-heavy with periodic primitive refresh;
- hard-negative annealing;
- domain-exclusivity phase with continued in-domain positive rehearsal.

The correct schedule is chosen through zero-cost proxy tests / baseline analysis where possible, not by narrative preference.

## 9. Functional forgetting / exclusivity evaluation

Maintain four suites:

### A. MUST_GAIN

All model-facing Xeno/HCU/GRF/J-Space/GWT/Hyperposition functions.

### B. MUST_RETAIN MINIMUM

Only capabilities required for Xeno operation:

- German/English comprehension sufficient for owner/tool interaction;
- exact schema output;
- arithmetic/logic;
- token/byte/vector manipulation;
- protocol/tool understanding;
- safety/authority/fail-closed behavior.

### C. DESIRED_FORGET / GENERALIST

Unrelated:

- broad trivia;
- encyclopedic recall;
- general creative writing;
- generic advice/chat persona;
- unrelated broad task knowledge.

Desired direction: large performance drop or explicit routing/abstention.

### D. RESIDUAL_KNOWLEDGE PROBES

Probe whether general knowledge remains extractable under:

- paraphrase;
- multiple choice;
- indirect cues;
- completion probes;
- adversarial prompt attempts;
- confidence-free scoring/logprob where runtime permits.

This distinguishes behavior suppression from genuine functional forgetting.

No claim of true unlearning is made unless dedicated unlearning metrics support it.

## 10. Representation reorientation evaluation

After full FT and again after Q4_K_M quantization, use exact local model/runtime evidence to compare base vs specialized model:

- decodability of GRF reality class;
- Hyperposition branch/topology state;
- GWT competition/broadcast/use state;
- J-Space control class;
- mode/role/cell state;
- provenance/evidence class;
- discriminator selection;
- off-domain/generalist state.

Where causal intervention is available, use matched null/orthogonal/permuted/wrong-site/lesion/rescue controls.

Desired result is stronger, cleaner, more selective GRF/HCU representation with bounded off-target damage to MUST_RETAIN.

## 11. Full-FT method implications

Current research indicates:

- domain-adaptive continued pretraining can improve domain specialization;
- ordinary fine-tuning can cause catastrophic forgetting;
- catastrophic forgetting can be useful for this owner's specialization objective but is not controllable enough to assume success;
- machine-unlearning benchmarks show that suppressing answers is not equivalent to erasing learned information;
- smaller learning rates often preserve general abilities better, while this project deliberately may accept more general-capability loss in exchange for specialization, subject to MUST_RETAIN floors.

Therefore Trigger 2 must treat learning rate, epochs, data order and in/out-domain mixture as **specialization controls**, not generic defaults.

The first paid Together job remains SFT/full-parameter unless current Together capabilities and owner authority explicitly permit a better proven objective. If a true continued-pretraining objective is unavailable on the fine-tuning API, do not mislabel SFT as continued pretraining.

## 12. Promotion law

The first specialized model is promoted only if:

1. MUST_GAIN improves materially across independent families;
2. semantic Hyperposition survives label-free/OOD/topology/role counterbalances;
3. GRF mathematical/state-transition tasks pass with low schema error;
4. J-Space/GWT causal-protocol metrics improve without false latent claims;
5. MUST_RETAIN hard floors pass;
6. DESIRED_FORGET generalist metrics decrease in the intended direction;
7. residual-knowledge evaluation is reported honestly rather than calling refusal "erasure";
8. Q4_K_M preserves the specialized result within predeclared bounds;
9. whole EntityOS authority boundaries remain intact.

A dramatic personality/output change alone is not sufficient.
