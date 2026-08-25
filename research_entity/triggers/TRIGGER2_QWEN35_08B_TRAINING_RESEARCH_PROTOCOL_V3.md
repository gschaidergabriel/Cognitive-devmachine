# Reserved Trigger `2` / `triggerwort 2` — Universal Semantic-Hyperposition Training Protocol v3

Status: **OWNER-CORRECTED ACTIVE SUCCESSOR ON TRIGGER-2 RESEARCH LANE**  
Date: 2026-08-25  
Supersedes for Trigger-2 dataset semantics: `TRIGGER2_QWEN35_08B_TRAINING_RESEARCH_PROTOCOL_V2.md`  
Target model: **Qwen3.5-0.8B class only unless newer owner authority changes it**  
Product: EntityOS  
Architecture: HCU  
Xeno: transitional implementation compatibility codename only

## 1. Owner correction: semantic Hyperposition is the ambient training frame

Semantic Hyperposition is **not** a late curriculum topic, a dedicated CP05 family, a percentage bucket, or an optional GRID10 behavior that can be learned after the other capabilities.

It is the semantic operating frame in which every model-facing cognitive skill must be learned.

Therefore every trainable Trigger-2 example must teach its local task **inside** a valid Hyperposition state transition. A row may exercise binding, symbolic inference, context invariance, epistemic typing, planning, compression, Claude handoff/re-entry, database boundary behavior, GWT/workspace use, grid resizing, recovery, or effect proposal, but the row may not silently abandon the Hyperposition state model while doing so.

The intended invariant is:

`skill(x) is learned under H(Q), not skill(x) first and Hyperposition later`.

This changes dataset architecture, not merely family weights.

## 2. Universal model-facing state contract

Every trainable row MUST either carry an unresolved/partially resolved Hyperposition frame or explicitly prove that the state is a correctly resolved singleton.

Canonical conceptual form:

`H(Q) = {h_1 ... h_n}`

Each branch contains at minimum:

`h_i = (v_i, K_i, E_i+, E_i-, F_i, T_i, A_i, sigma_i)`

where the fields mean value/candidate, context predicate, evidence, counterevidence, falsifier/discriminator condition, validity/temporal scope, ancestry/provenance, and epistemic status.

A trainable example MUST make the following information part of the model-facing input/supervision contract, not evaluator-only metadata:

- `H_before`: branch set before the cognitive operation;
- stable opaque branch identities whose order carries no semantics;
- `K`: context predicate/scope for each branch;
- `E_plus` and `E_minus` separately, with provenance/ancestry where evidence dependence matters;
- `F`: explicit falsifier or discriminator condition;
- `T`: validity/time/generation scope where applicable;
- `A`: provenance/ancestry identity or reference;
- `sigma`: epistemic type/status;
- `operation`: the requested cognitive transform;
- `H_after`: expected branch set after the operation;
- `resolution`: `UNRESOLVED`, `REQUEST_DISCRIMINATOR`, or evidence/policy-gated `RESOLVED` with the exact discriminator/policy identity;
- `projection`: any attention/display/action projection, explicitly distinct from deletion of nonprojected branches;
- `falsifier`: what would make the supervised transition wrong;
- branch-retrieval targets when role/binding behavior is exercised.

A singleton row is legal only when it contains an explicit `resolved_singleton` reason and an admissible discriminator/policy provenance. Singleton-by-convenience is a failure.

## 3. Universal anti-collapse law

The following may never be used as truth or collapse rules unless a newer explicit owner specification defines a deterministic admissible rule for the exact case:

- majority of branches/nodes;
- model confidence;
- salience/attention weight;
- repeated phrasing or repeated support with shared ancestry;
- GWT/workspace broadcast;
- J-Space recurrence;
- embedding/vector proximity;
- node count;
- executor identity;
- lexical position/order;
- codebook order;
- projection/filtering from the active context.

Projection is not deletion. Attention omission is not falsity. Recurrence is not evidence. Correlated evidence is not independent evidence. Contradiction is an object to preserve and investigate, not an exception that licenses arbitrary collapse.

## 4. Two-axis curriculum

The previous competence ordering remains useful, but it is now orthogonal to the semantic frame.

### Axis A — capability difficulty

Use the evidence-driven progression approximately:

`C symbolic inference -> A context invariance -> B dynamic codebook binding -> E epistemic typing/GRF -> D explicit multi-branch Hyperposition mastery -> integrated A+B+C+D+E`

This ordering exists to isolate which capability fails.

### Axis B — Hyperposition frame complexity

Every stage above is rendered under progressively harder Hyperposition structure:

1. explicitly resolved singleton with valid discriminator provenance;
2. two live branches with one local operation that must not collapse them;
3. two/three branches with branch-local evidence updates;
4. contradictions and UNKNOWN without forced resolution;
5. multi-round updates with stable branch identity and evidence ancestry;
6. explicit discriminator request/selection;
7. evidence-gated resolution;
8. cross-node/grid-distributed branch ownership with exact ancestry and rejoin/recovery.

Thus even C1/A/B/E examples teach the correct semantic frame from row one; full D competence is still learned later as a harder composition.

## 5. Required extra invariants beyond the previous protocol

Trigger-2 generation and review MUST now include these controls:

### Set/permutation invariance

Branch order and branch ID surface form must be randomized/counterbalanced. Reordering the same branch set must not change the semantic target.

### Cardinality generalization

Train across different branch counts and reserve higher-cardinality OOD families. Do not let `n=2` become an implicit uncertainty label.

### Evidence locality

Evidence updates only the branch(es) whose predicates/ancestry it actually bears on unless an explicit cross-branch rule applies. Detect evidence bleed.

### Evidence dependence

Paraphrases, repeated packets, or multiple nodes sharing one evidence ancestor do not count as independent confirmations. Include correlated-consensus hard negatives.

### Context coexistence

The same surface value may be valid under one `K` and invalid/unknown under another. Context projection must not erase the unselected branch from the recoverable state.

### Re-opening / revision

A previously resolved candidate may require reopening when newer admissible evidence invalidates the resolution preconditions. Do not train irreversible commitment bias.

### UNKNOWN / ABSTAIN / REQUEST_DISCRIMINATOR

The model must be rewarded for preserving nonknowledge and asking for the highest-information discriminator when the state is unresolved. A forced final answer is not always a valid target.

### Output/state separation

Choosing one action/output for a bounded interface is not equivalent to declaring all other semantic branches false. The training target must distinguish `visible_projection` or `ActionCandidate` from the underlying branch set.

### Semantic-skeleton leakage control

Split identity is not enough. Train/validation/holdout construction must hash/group the underlying semantic Hyperposition skeleton, ancestry and causal transformation before rendering lexical variants. Paraphrases of the same H-state transition stay in one family.

## 6. Trigger-2 corpus migration law

Every exact `2` / `triggerwort 2` run now starts with a **corpus-wide semantic-Hyperposition migration gate** before it expands row count.

For every living Trigger-2 candidate row/generator/family classify:

- `KEEP`: already conforms to the universal model-facing Hyperposition contract;
- `REWRITE`: semantic task is useful but must be re-rendered inside the universal frame;
- `REGENERATE`: shortcut/leak/collapse assumptions are structurally embedded and a new example must be generated;
- `REJECT`: stale, contradictory, ungrounded, authority-violating, irreparable, duplicate/leaky, or unsupported positive label.

The run MUST NOT increase the claimed trainable/accepted corpus merely to satisfy a growth target while the universal gate is failing.

If the gate fails, that Trigger-2 cycle is a **repair/migration cycle**. Expansion resumes only after the relevant candidate corpus passes the universal frame gate.

No source-design row, blueprint row, or narrative example earns accepted-dataset credit merely because it can be wrapped mechanically. The resulting model-visible bytes and supervision target must be audited after rendering.

## 7. Swarm review changes

The Trigger-2 swarm retains generator/falsifier/leakage/provenance/acceptance roles and adds mandatory Hyperposition-specific adversaries:

1. `HYPERPOSITION_FRAME_AUDITOR` — verifies every row actually operates in H(Q), not merely mentions the word;
2. `PREMATURE_COLLAPSE_ADVERSARY` — searches for implicit truth selection without a discriminator;
3. `BRANCH_SET_INVARIANCE_REVIEWER` — permutes branch order/IDs/cardinality and checks target invariance;
4. `EVIDENCE_ANCESTRY_REVIEWER` — injects repeated/correlated support and checks that it is not double-counted;
5. `PROJECTION_VS_DELETION_REVIEWER` — tests attention/filter/display decisions without loss of recoverable alternatives;
6. `SEMANTIC_SKELETON_LEAKAGE_REVIEWER` — prevents paraphrase/render variants of one H-transition from crossing train/validation/holdout;
7. `MECHANISTIC_ACCEPTANCE_REVIEWER` — requires branch/type/class decodability plus lesion/shuffle/rescue where meaningful, not output accuracy alone.

## 8. Labeler/reference-implementation prerequisite

The training data may only supervise state transitions that can be labeled deterministically enough for the declared scope.

Before promoting D/E-style rows, use executable reference labelers for at least:

- `U` / update: `(H_t, observation) -> H_t+1`;
- `Resolve`: evidence/falsifier/context -> `PASS` or `UNRESOLVED`;
- discriminator ranking: pairwise/ordinal test choice is sufficient for training if calibrated utility is not defined;
- salience ranking: ordinal ranking is sufficient, but salience never becomes probability/truth.

Rows outside the executable labeler's admitted domain are rejected or retained as research hypotheses, not converted into positive training labels by narration.

## 9. Acceptance gates

Universal semantic-Hyperposition schema/compliance is a hard gate, not an average metric.

A candidate training freeze requires:

- 100% of trainable rows have the model-facing Hyperposition contract or an explicitly justified resolved-singleton contract;
- branch/order/codebook/template/nuisance counterfactual invariance passes;
- branch retrieval remains >0.90 on declared role-binding tests;
- semantic/class/epistemic types meet their declared decodability floors;
- collapse-without-discriminator rate -> 0 on adversarial families;
- hypothesis-as-fact and UNKNOWN/ZERO/ABSENT/MEASUREMENT_ERROR confusions -> 0 within declared tolerance;
- correlated-consensus, recurrence, salience and projection hard negatives pass;
- semantic-skeleton/provenance family split leakage = 0;
- existing semantic readout/required operational capabilities remain within their retention floors;
- output accuracy cannot compensate for failed state-structure gates.

## 10. What exact Trigger `2` means after this correction

Each invocation performs, in order:

1. refresh current main, owner/supervisor authority and active Trigger-2 lane;
2. census all living candidate training sources/generators/materialized rows;
3. run the universal semantic-Hyperposition audit;
4. classify each surface/family `KEEP/REWRITE/REGENERATE/REJECT`;
5. repair/regenerate the highest-value failing families with swarm review;
6. run branch-set, evidence-ancestry, projection, leakage and mechanistic gates;
7. only when the relevant corpus gate passes, expand with new examples;
8. generate new examples directly in the universal frame rather than wrapping an old collapsed example after the fact;
9. emit a corpus-level compliance report and per-family failure counts;
10. feed discovered failure modes, counterexamples and harness requirements back into Clay/EntityOS/HCU research.

The trigger therefore optimizes **valid semantic operating-frame coverage**, not raw row count.

## 11. Evidence boundary

This protocol changes training-data semantics and Trigger-2 workflow. It does not by itself prove that Qwen3.5-0.8B can learn the required representation, does not create J-Space causal evidence, does not authorize paid training, and does not mint EntityOS/HCU runtime credit.

A small C1-plus-Hyperposition pilot remains a high-information early test: if the desired class/branch state does not become measurably decodable at 0.8B, scale/model assumptions must be challenged before a large run.
