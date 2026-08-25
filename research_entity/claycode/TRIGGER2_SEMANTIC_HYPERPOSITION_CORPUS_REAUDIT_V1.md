# Trigger 2 — semantic Hyperposition corpus re-audit v1

Status: **SOURCE/DATA-DESIGN AUDIT — REPAIR REQUIRED BEFORE TRAINING-FREEZE**  
Date: 2026-08-25  
Owner correction: semantic Hyperposition is the universal semantic operating frame of the training data, not only a dedicated skill/family.

## Evidence identities inspected

- canonical `main` observed during audit: `ba78c2fa87f8b2637b621fbe6301eee1158c9cc9`;
- active Trigger-2 PR: `#1956`;
- active Trigger-2 branch observed before this audit write: `research/trigger2-qwen35-08b-hcu-fullft-20260825`;
- prior PR head observed: `e118f980104f9d0ac32dfb70eeca5046d563fdce`;
- new universal-frame protocol commit on the Trigger-2 branch: `9374617f9a981caf2144dd57eebf28d6d45be5a0`.

This audit is structural/source-level. It does not claim byte-level review of a frozen final training corpus because current project evidence still reports accepted dataset tokens = 0 and training credit = 0.

## Audit question

Does the current Trigger-2 training surface merely *contain Hyperposition examples*, or does **every cognitive example operate inside explicit semantic Hyperposition state semantics**?

New hard requirement:

- every trainable row has model-facing `H_before` and supervised `H_after`, with branch context/evidence/counterevidence/falsifier/validity/provenance/epistemic state, operation, projection semantics and resolution/discriminator state; or
- it explicitly proves a correctly resolved singleton.

Mentioning `Hyperposition`, `unresolved branches`, `UNKNOWN`, or `majority is not truth` in isolated examples is not sufficient.

## Surface 1 — current census-wide process generator

Path:

`tools/trigger2_cognitive_process_trajectory_generator_v1.py`

Observed design:

- 13 cognitive-process blueprint families;
- deterministic 2x2x2 nuisance cross;
- 208 source-design candidate rows;
- 104 positive / 104 synthetic hard-negative;
- family-level train/validation/holdout separation;
- the generator's `prompt_for(...)` emits scenario + generic provenance/UNKNOWN/candidate/effect-boundary instruction;
- the generator's `target_for(...)` emits `status`, `emit`, `rule`, authority fences and no explicit universal Hyperposition before/after state.

### Verdict

`REWRITE` for useful semantics; **0/208 structurally satisfy the new explicit universal-frame contract as currently generated**.

Important nuance: several families already preserve pieces of the intended semantics — e.g. CP02 preserves deferred contradictory evidence, CP04 preserves the stale-plan branch, CP05 explicitly teaches Hyperposition, CP07 preserves nonwinning alternatives, CP09 preserves minority counterevidence. Those are valuable donors. They are not yet enough because the common row schema does not make the H-state transition the ambient contract for every family.

Required repair:

- lift branch/evidence/context/type/discriminator state into a shared model-facing envelope used by every blueprint;
- make each blueprint specify its local operation over that envelope;
- render target `H_after` and output projection separately;
- add branch permutation and evidence-ancestry counterfactual twins.

## Surface 2 — integrated cognitive trajectory seed v4

Path:

`research_entity/global/j-space/research/trigger2_qwen35_08b_integrated_cognitive_trajectory_seed_v4.jsonl`

Observed:

- 10 TRAIN-only rows across 5 positive/hard-negative integrated families;
- some rows explicitly preserve alternatives or UNKNOWN;
- the missing-state pair directly exercises multiple live generation hypotheses and rejects majority collapse;
- resize/recovery rows mention unresolved branches;
- other rows focus on handoff/re-entry/effect recovery without an explicit common H-state representation;
- no row has explicit structured `H_before` / `H_after` fields.

### Verdict

All 10 rows are **legacy pre-universal-frame candidates**.

- semantic content: mostly `KEEP_AS_DONOR`;
- trainable rendering: `REWRITE`;
- none should be discarded merely for lacking the new envelope;
- every row must be regenerated/rendered under the same semantic-Hyperposition state contract before it can contribute to a frozen trainable corpus.

The missing-state Hyperposition pair is the closest donor but still needs explicit branch IDs, branch-local evidence/provenance, discriminator state and before/after transition so the model learns the representation rather than a prose policy slogan.

## Surface 3 — dynamic-binding blueprint v2.1

Path:

`tools/trigger2_dynamic_binding_blueprint_v2.py`

Observed design:

- 9,072 deterministic blueprint rows;
- 6 S3 mappings x 6 codebook orders x 2 layouts x 3 semantic outcomes x 2 polarities across train/validation/holdout template/atom families;
- generator correctly keeps these rows `training_eligible=false` pending exact ABI/tokenizer binding;
- row fields encode class, mapping, symbols, order, layout, evidence text and query;
- no semantic-Hyperposition before/after branch-state envelope is present.

### Verdict

`REWRITE_AT_MATERIALIZATION`, not discard.

The factorial anti-shortcut design is valuable and should be retained. The missing operation is to embed each binding episode inside H(Q): the semantic class/decision must be derived from branch state and then routed through the episode-local codebook. This prevents the binder from becoming a detached classification trick that cannot operate in the Xeno/HCU semantic frame.

Required new composition test:

`H_before -> semantic decision S -> episode-local mapping M -> emitted symbol Y`, while preserving all unresolved branches not resolved by the binding operation.

The harness must continue scoring `S`, `M`, and `Y` separately.

## Surface 4 — active Trigger-2 PR #1956 patch

The current PR contains extensive Hyperposition specialization material and dedicated Hyperposition/GRID10 documents. However, a patch-level search of the active PR changes before this correction found:

- no `H_before` occurrences;
- no `H_after` occurrences;
- no explicit `E_i` branch tuple occurrences.

### Verdict

The lane already treats semantic Hyperposition as an important capability and architecture target, but **not yet as a universal row-level semantic contract**. That is exactly the gap identified by the owner correction.

The new protocol v3 fixes the execution meaning; existing candidate-data artifacts remain subject to migration.

## What was missing conceptually

The previous design had two partially correct but insufficient ideas:

1. `Hyperposition as a capability`: teach dedicated branch-preservation/collapse behavior;
2. `Hyperposition as an architecture property`: GRID10/HCU holds distributed alternatives.

The missing third level was:

3. **Hyperposition as the semantic coordinate system of the whole training distribution.**

Without level 3, a model can learn binding, planning, handoff, typing, recovery and symbol emission in ordinary collapsed prompt semantics, then fail when those abilities must operate over branch-structured Xeno/HCU state.

The new rule is therefore not "increase Hyperposition examples". It is "render all model-facing cognitive examples in Hyperposition semantics".

## Additional required repairs discovered in this re-audit

### 1. Branch identity must not become a label leak

Use opaque branch IDs; permute IDs/order while preserving target state. The model must learn relations, not `branch_0 = preferred`.

### 2. Evidence locality must be supervised

An observation updates only branches it bears on. Include negative examples where evidence for one branch incorrectly bleeds into another.

### 3. Evidence ancestry must be visible enough to prevent vote-counting

Ten packets copied from one source are not ten independent confirmations. Correlated-consensus traps belong in every relevant family, not just GRID10-specific data.

### 4. Context projection must be reversible

If a branch is outside the active context, its omission from the current projection must leave a recoverable reference. Projection/filtering != deletion.

### 5. Output selection must not equal semantic collapse

A one-symbol response or one ActionCandidate can be required by an interface while multiple semantic branches remain live. Supervision must represent both states separately.

### 6. Resolution must carry causal provenance

`RESOLVED` without `discriminator_id` / deterministic policy identity is invalid. This applies even when the answer happens to be correct.

### 7. Reopening must exist

Train explicit cases where a prior resolution becomes invalid because its context, generation or evidence precondition changes.

### 8. Semantic skeletons, not rendered text, define split families

Hash/group branch graph + causal operation + evidence ancestry + resolution rule before paraphrase/codebook/template rendering. This closes a leak that lexical family splitting alone cannot.

### 9. Hard negative families must be paired with corrected alternatives

Required recurring hard negatives:

- majority -> truth;
- confidence/salience -> truth;
- recurrence/GWT/J-Space reuse -> truth;
- duplicate/correlated evidence -> independent support;
- projection -> deletion;
- contradiction -> forced choice;
- UNKNOWN -> ZERO/ABSENT;
- output selection -> branch deletion;
- stale context/generation -> silent carryover;
- branch reorder/ID change -> changed semantic answer.

### 10. Mechanistic acceptance must precede behavioral celebration

For C/D/E-style state targets measure whether class/branch/type information is decodable, then test lesion/shuffle/rescue where meaningful. Final-token accuracy alone can hide shortcut learning.

## Revised Trigger-2 migration disposition

Until the universal semantic-Hyperposition gate passes:

- current useful rows are donor/candidate material, not final trainable truth;
- Trigger `2` spends its high-value work on migration/repair rather than raw corpus growth;
- new examples are generated natively in the universal frame;
- no post-hoc wrapper earns credit unless the model-visible bytes and target actually teach the state transition;
- no accepted dataset/training credit is claimed.

## Next exact engineering gates

1. Add one shared serialized Hyperposition envelope to the candidate training schema/collator path.
2. Update the census-wide 208-row generator to render every family through that envelope.
3. Update the dynamic-binding materializer so `S -> M -> Y` occurs inside H(Q), including unresolved alternatives.
4. Migrate/regenerate the integrated seed v4.
5. Add a corpus linter that fails rows lacking the universal frame or an admissible resolved-singleton proof.
6. Add branch-order/ID, evidence-ancestry, projection, reopening and semantic-skeleton split tests.
7. Re-run swarm review and only then materialize a small pilot.
8. Use a small C1 + universal-Hyperposition pilot as an early 0.8B learnability discriminator before scaling.

## Credit boundary

This re-audit establishes a design defect and a corrected training contract. It does not prove model learnability, does not execute fine-tuning, does not create accepted dataset tokens, and does not grant J-Space/HCU/EntityOS runtime credit.
