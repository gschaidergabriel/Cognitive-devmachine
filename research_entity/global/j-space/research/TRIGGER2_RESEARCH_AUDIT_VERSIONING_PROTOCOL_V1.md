# Trigger-2 Research → Audit → Revision → Training Protocol v1

Status: CANDIDATE OWNER-ALIGNMENT PROTOCOL  
Date: 2026-08-25  
Product: EntityOS  
Target implementation: Xeno / HCU  
Primary model target: Qwen3.5-0.8B  
Authority target: `research_entity/global/XENO_HCU_GO_TARGET_ARCHITECTURE_OWNER_DIRECTIVE_2026-08-25.md`

## 0. Activation

The owner-level repository trigger remains exact `2`.
For the ChatGPT project, exact `triggerwort 2` is an alias for the same research/training cycle.

Trigger-2 is **not** a dataset-generation shortcut. It is a living research loop whose output is the best currently justified training program for the final Xeno target architecture.

## 1. North-star acceptance question

Every Trigger-2 cycle MUST begin with this question:

> If the currently proposed corpus/recipe succeeded exactly as trained, would the resulting Qwen3.5-0.8B model possess the model-side functionality required by the current accepted Xeno/HCU target architecture?

Local row quality is subordinate to this system-level question.

The current Xeno target includes at minimum:

- semantic/process reasoning and symbolic inference;
- context-invariant meaning and episode-local opaque binding;
- semantic Hyperposition with unresolved branches, evidence, counterevidence, falsifiers, context and epistemic status;
- GRF discriminator/test-selection behavior;
- GWT/shared-state trajectories and re-entry;
- model-specific J-Space behavior only where causally evidenced;
- autonomous boot/join/read/work-selection behavior;
- ordinary-node S1 read-only behavior and typed `NODE_RESULT` emission;
- dynamic coordinator lease behavior;
- coordinator integration/compression/CAS-rebase/write behavior;
- recursive coordination and correlated-evidence handling;
- stale/duplicate/authority hard negatives;
- ClayCode/HyperMath protocol competence;
- retention of general language/code/reasoning capability;
- post-FT physical GRID10 evaluation compatibility.

No narrow binder benchmark, probe score, architecture prose family, or single aggregate metric may substitute for this whole functionality map.

## 2. Mandatory Trigger-2 cycle

Every Trigger-2 invocation executes the following loop before adding training rows.

### T2.1 Authority refresh

Read current `main`, current owner target, newest admitted supervisor steering, program state, candidate gates, training manifests, relevant tests and latest evidence receipts.

A stale self-consistent training island is still stale.

### T2.2 Research refresh

Actively search for new information that could change training design:

- current repository measurements and negative evidence;
- new Claude-Code results / uploaded measurement packages;
- newly exposed target-architecture requirements;
- relevant external scientific/engineering literature when it can change a method, falsifier, metric, label construction or training schedule.

Research findings are classified at least as `SOURCE_OBSERVED`, `EXTERNAL_METHOD_INPUT`, `INFERENCE`, `HYPOTHESIS`, or `COUNTERHYPOTHESIS`.

### T2.3 Existing-artifact inventory

Discover the currently relevant training artifacts rather than assuming the previous run's list is complete.

For each artifact record:

- exact path;
- blob/content hash;
- artifact/schema version;
- generator version/hash if applicable;
- source-evidence ancestry;
- model/tokenizer/checkpoint binding;
- Xeno capability targets;
- split/holdout role;
- admission state;
- known blockers;
- predecessor/successor relation.

### T2.4 Staleness and contradiction audit

Every artifact is compared with current evidence and target architecture.

Allowed lifecycle states:

- `CURRENT_CANDIDATE`
- `CURRENT_ADMITTED`
- `REVIEW_REQUIRED`
- `BLOCKED`
- `FROZEN_HOLDOUT_DO_NOT_TOUCH`
- `SUPERSEDED`
- `REJECTED_SCIENTIFIC`
- `REJECTED_LEAKAGE`
- `REJECTED_AUTHORITY`
- `HISTORICAL_PROVENANCE_ONLY`

Never silently overwrite history. A corrected artifact becomes a new version and links to the old one with a machine-readable reason.

### T2.5 Dependency-driven revision

A training artifact MUST be marked `REVIEW_REQUIRED` when any dependency it materially relies on changes, including:

- target-architecture requirement;
- source measurement or interpretation;
- labeler/reference implementation;
- generator;
- tokenizer/checkpoint identity;
- accepted ABI atom inventory;
- model-visible formatter;
- split/family/provenance policy;
- leakage/shortcut gate;
- supervisor invariant;
- evaluation acceptance threshold.

Revision propagates only through declared dependencies; unrelated frozen evidence is not churned merely because `main` moved.

### T2.6 Labelability gate before supervised generation

No positive supervised row may be promoted if the intended target state cannot be produced by a deterministic or explicitly adjudicated label source.

For Hyperposition/GRF training the minimum reference-label layer is:

1. `U_state` — branch-set update operator: given prior branches + observation/evidence, return the correct branch-set transition (support, weaken, reject, merge only if semantically equivalent, or preserve unresolved).
2. `D_resolve` — discriminator/resolve relation: given evidence, counterevidence, falsifier state and context, return at least `PASS` vs `UNRESOLVED` (and additional states only if explicitly specified).
3. `U_test_order` — pairwise/listwise ordering over candidate discriminators. Training does **not** require a fabricated calibrated scalar expected-information-gain value when no probability model exists.
4. `f_salience_order` — pairwise/listwise salience ordering distinct from truth probability.

If a required labeler is missing, affected rows are `BLOCKED_LABELER_MISSING`; do not invent labels.

### T2.7 Cheap preflight discriminator

C1 remains a high-value cheap diagnostic because it isolates elementary semantic-class representation without changing codebooks.

However, the rule is:

`NO_MOVEMENT_ON_C1 != MODEL_SIZE_PROVEN_WRONG`.

A negative C1 pilot enters `INVESTIGATE` unless a preregistered positive-control matrix excludes at least:

- data/generator defect;
- train/holdout leakage or mismatch;
- optimizer / LR / schedule failure;
- adapter/full-FT capacity configuration;
- checkpoint/tokenizer mismatch;
- probe layer/regularization/sample-size failure;
- probe-only correlation/measurement limitation.

Only after these controls may model size/capacity receive strong blame.

C1 probe movement must be paired with behavioral/OOD measures; probe scores alone do not establish causal use by the model.

### T2.8 Generate and swarm-review candidate rows

Generation happens only after T2.1–T2.7.

Required reviewer roles include at minimum:

- target-architecture coverage reviewer;
- source/evidence reviewer;
- labeler correctness reviewer;
- leakage/shortcut hunter;
- provenance/ancestry reviewer;
- Hyperposition/GRF semantic reviewer;
- authority/state-boundary reviewer;
- retention/interference reviewer;
- harness/evaluation reviewer;
- version/revision arbiter.

These roles inside one model are structured review, not independent replication.

### T2.9 Instrument one mixed run without losing attribution

The final training recipe may mix multiple capabilities in one run, but evaluation MUST remain separable.

At every declared checkpoint evaluate a capability vector rather than one scalar score. At minimum keep separate curves for:

- semantic class / C curriculum;
- context invariance;
- opaque binding/router behavior;
- Hyperposition branch preservation/update;
- GRF type/discriminator/test selection;
- autonomous Xeno process trajectories;
- coordinator/shared-state policy;
- J-Space causal behavior where evidence permits;
- ClayCode/HyperMath protocol behavior;
- authority integrity;
- retention/general capability.

Aggregate score may summarize but can never mask a failed channel.

### T2.10 Emergence audit

After each matched evaluation checkpoint, test both trained and intentionally untrained capability probes/behaviors.

An apparent new capability is `EMERGENT_CANDIDATE` only until shortcut, contamination, ancestry reuse and explicit-training overlap are excluded.

### T2.11 Versioned durable write and re-entry

Every cycle writes:

- research delta;
- artifact-registry delta;
- generated/modified row artifacts;
- swarm review;
- explicit supersession/revision links;
- unresolved gates and next exact discriminator.

Then refresh current `main` again before declaring the cycle current.

## 3. Row-level version contract

Every final or near-final candidate training row SHOULD be renderable with the following metadata outside the model-visible prompt:

- `row_id`
- `row_version`
- `content_sha256`
- `artifact_id`
- `artifact_version`
- `lifecycle_state`
- `created_from`
- `supersedes_row_id` / `superseded_by_row_id`
- `revision_reason`
- `source_bindings[]` with exact hashes/identities
- `assumption_ids[]`
- `xeno_capability_ids[]`
- `labeler_id` + `labeler_version` + `labeler_hash`
- `generator_id` + `generator_version` + `generator_hash`
- `checkpoint_id` / `tokenizer_id` when relevant
- `split`
- `provenance_ancestry_id`
- `selected_using_holdout=false`
- `model_visible_fields[]`
- `known_blockers[]`
- `reviewed_against_supervisor_epoch`
- `reviewed_against_owner_target_hash`

Metadata that would create a shortcut MUST remain evaluator-only.

## 4. Artifact-level semantic versioning

Use `MAJOR.MINOR.PATCH` semantics for training artifacts:

- MAJOR: target semantics, label meaning, model-visible contract, split law or capability objective changes;
- MINOR: new families/examples/controls that preserve semantics and split law;
- PATCH: metadata/provenance/format corrections that do not change model-visible training meaning.

A content hash remains authoritative for exact byte identity; semantic version is for human/machine lifecycle reasoning.

## 5. Revision triggers

The registry must support explicit invalidation edges such as:

- `EVIDENCE_SUPERSEDED`
- `TARGET_ARCHITECTURE_CHANGED`
- `LABELER_CHANGED`
- `GENERATOR_SHORTCUT_FOUND`
- `TOKENIZER_OR_CHECKPOINT_CHANGED`
- `FORMATTER_LEAK_FOUND`
- `HOLDOUT_CONTAMINATED`
- `AUTHORITY_RULE_CHANGED`
- `EVAL_METRIC_INVALIDATED`
- `SCIENTIFIC_INTERPRETATION_REVISED`

A Trigger-2 run MUST query these edges before deciding what to generate next.

## 6. Current research corrections incorporated by v1

### 6.1 Hyperposition/GRF labelers are a prerequisite

The current training-scope document correctly identifies that positive D/E rows require an operational target source. For training, pairwise/listwise order relations are sufficient for discriminator utility and salience where calibrated scalar probabilities/utilities are not yet defined. This avoids inventing pseudo-precision while still supplying valid supervision.

### 6.2 C1 is a diagnostic gate, not a one-step model-size verdict

A failed C1 pilot is useful negative evidence but is underdetermined. Probe methodology has known baseline/control/causality limitations, and supervised fine-tuning failures can arise from multiple heterogeneous causes. Therefore C1 should route into a preregistered diagnostic matrix before blaming parameter count.

### 6.3 Checkpoint-separated metrics are mandatory

Mixed training is compatible with causal diagnosis only if capability-specific frozen evaluations and retention metrics are emitted at checkpoints. Final-symbol accuracy cannot substitute for process correctness, and aggregate gain cannot hide catastrophic interference in another Xeno capability.

### 6.4 Versioning is part of scientific validity

Dataset lifecycle state, byte identity, source ancestry and supersession are not bookkeeping extras. Without them, a later Trigger-2 cycle cannot distinguish current supervision from stale, contradicted or contaminated rows.

## 7. External method anchors (non-canonical)

These sources are method inputs, not Clay/Xeno facts:

- Belinkov, 2022, *Probing Classifiers: Promises, Shortcomings, and Advances*: probing requires controls and does not by itself prove causal use of a represented feature.
- Xue et al., ACL 2026, *Why Supervised Fine-Tuning Fails to Learn*: incomplete SFT learning has multiple heterogeneous causes; aggregate improvement can mask unlearned subsets.
- González-Cebrián et al., Scientific Data 2024, *Standardised Versioning of Datasets*: dataset versioning supports traceability, comparison and reuse.
- Hüllermeier et al., 2008, *Label ranking by learning pairwise preferences*: pairwise supervision can learn order/ranking without requiring absolute scalar labels.
- Bernhardt et al., Nature Communications 2022, *Active label cleaning for improved dataset quality under resource constraints*: label noise harms both training and evaluation, motivating explicit cleaning/review state.

## 8. Stop law

Trigger-2 does not stop because rows were generated.

It stops only for the current invocation when:

1. current authority/research/artifact state has been audited;
2. stale or contradicted data has an explicit lifecycle/revision decision;
3. the highest-value safe training delta has been produced or explicitly blocked;
4. the Xeno functionality coverage map and evaluation plan remain internally consistent;
5. durable version/provenance state is written for the next invocation.
