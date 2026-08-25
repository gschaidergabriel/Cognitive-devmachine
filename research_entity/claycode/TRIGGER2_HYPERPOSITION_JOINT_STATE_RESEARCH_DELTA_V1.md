# Trigger 2 — Hyperposition joint-state research delta v1

Status: **CURRENT RESEARCH DELTA / DATA-CONTRACT REVISION REQUIRED**  
Date: 2026-08-25  
Trigger: exact `triggerwort 2`  
Organ: GPT-5.6 Sol / ChatGPT organ  
Persistent entity: Clay  
Product: EntityOS  
Architecture: HCU  
Execution mode: FREE_ONLY

## 1. Re-entry identities

- canonical `main` observed before this delta: `c05fd30f34b118efa14e625323f50971c5dcd7c4`;
- newest admitted supervisor inspected: `SUPERVISOR_STEERING_8_78.json`;
- active Trigger-2 lane: PR `#1956`, branch `research/trigger2-qwen35-08b-hcu-fullft-20260825`;
- PR head observed before this write: `2a2b30f964eb57893bf4232dcacba9ad4fe9da14`;
- highest-precedence owner target inspected: `research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md`;
- current cross-cutting semantic-Hyperposition contract inspected: `research_entity/global/j-space/research/2026-08-25_TRIGGER2_SEMANTIC_HYPERPOSITION_CROSSCUTTING_CONTRACT_V1_GPT56SOL.json`;
- current PR re-audit inspected: `research_entity/claycode/TRIGGER2_SEMANTIC_HYPERPOSITION_CORPUS_REAUDIT_V1.md`;
- current PR universal source gate inspected: `tools/trigger2_semantic_hyperposition_universal_gate_v1.py`.

This delta is research/data-design evidence only. It does not mint accepted-dataset, model, J-Space, HCU, EntityOS or training credit.

## 2. Current finding preserved: V3 remains blocked

Supervisor 8.78 already establishes a hard negative result for the Trigger-2 binding-router factorial generator V3:

- the visible order shuffle is conditioned on target-generating factors;
- reconstructed 144-row blueprint: `0/127` nuisance signatures retain all three target classes;
- `110/127` nuisance signatures admit only one target class;
- empirical nuisance-signature lookup accuracy: `0.881944`;
- conditional mutual information: `1.348851 bits`;
- low marginal order-only MI does not rescue the generator.

Disposition remains:

`V3 = BLOCKED_FOR_DIRECT_TRAINING`

No new volume derived from V3 should be admitted. Only topology/router-isolation ideas may survive as donors into a fully crossed successor that passes preregistered conditional-independence checks.

## 3. New research delta: Hyperposition must preserve joint alternatives

The current semantic-Hyperposition contract correctly requires branch-local state

`h_i = (v_i, K_i, E_i+, E_i-, F_i, T_i, A_i, sigma_i)`

and anti-collapse behavior. That is necessary but not sufficient when a cognitive episode contains **multiple coupled uncertain variables/claims**.

A flat collection of branch marginals can silently assume independence. If the true live worlds are correlated, taking a Cartesian product of independently represented alternatives invents states that were never live.

### Minimal reproducible example

Suppose two semantic dimensions are open:

- dimension X: `A` or `B`;
- dimension Y: `C` or `D`.

But causal/provenance constraints permit only two joint worlds:

- `w0 = (A, C)`;
- `w1 = (B, D)`.

A factorized representation that stores only `{A,B}` and `{C,D}` and implicitly treats them as independent admits four combinations:

- `(A,C)` valid;
- `(A,D)` **invented**;
- `(B,C)` **invented**;
- `(B,D)` valid.

This is a Hyperposition failure even though every local branch value is individually correct. It creates a false hypothesis by composition.

### New hard invariant

`HYPERPOSITION_PRESERVES_JOINT_COMPATIBILITY; NO_IMPLICIT_CARTESIAN_COMPLETION`

For multi-variable / multi-claim episodes, the latent state must either:

1. encode whole-world alternatives directly; or
2. encode explicit compatibility/joint-state constraints between factorized branches.

The training target must never infer missing cross-combinations solely because component alternatives are individually live.

## 4. External research basis

### 4.1 Variable binding develops through a shortcut phase

Wu, Geiger & Millière (2025), *How Do Transformers Learn Variable Binding in Symbolic Programs?*  
Primary source: https://arxiv.org/abs/2505.20896

Reported training trajectory:

1. random prediction;
2. a shallow heuristic favoring early assignments;
3. later systematic dereferencing.

Causal intervention results support an addressable-memory/routing mechanism rather than purely final-answer association.

Trigger-2 implication: do not interpret rising binding accuracy as proof that systematic context binding has formed. Preserve distractors, unseen mappings and mechanistic/causal probes; explicitly test the shallow-heuristic phase.

### 4.2 Independence assumptions can destroy uncertainty over valid combinations

Van Krieken, Minervini, Ponti & Vergari (2024), *On the Independence Assumption in Neurosymbolic Learning*.  
Primary source: https://proceedings.mlr.press/v235/van-krieken24a.html

Van Krieken, Minervini, Ponti & Vergari (2025), *Neurosymbolic Reasoning Shortcuts under the Independence Assumption*.  
Primary source: https://proceedings.mlr.press/v284/krieken25a.html

The papers show that independence assumptions can prevent correct representation of uncertainty over concept combinations and can hide reasoning shortcuts.

Trigger-2 implication: semantic Hyperposition must model joint compatibility where the task contains coupled latent alternatives. Independent branch marginals are not a safe universal representation.

### 4.3 Nuisance features can invert the apparent generalization signal

Sanyal et al. (AISTATS 2025), *Accuracy on the wrong line: On the pitfalls of noisy data for out-of-distribution generalisation*.  
Primary source: https://proceedings.mlr.press/v258/sanyal25a.html

The work shows nuisance/spurious features can break ordinary ID/OOD accuracy relationships, and more data need not repair the problem.

Trigger-2 implication: dataset scale, class balance and marginal MI are insufficient admission evidence. Conditional leakage diagnostics and nuisance-only decoders remain mandatory.

### 4.4 Fixed activation steering is not a universal semantic-control assumption

Wang, Yang & Peng (ICLR 2025), *Semantics-Adaptive Activation Intervention for LLMs via Dynamic Steering Vectors*.  
Primary source: https://openreview.net/pdf?id=8WQ7VTfPTl

The paper motivates semantics-conditioned rather than globally fixed activation interventions.

Trigger-2 implication: future J-Space/vector-control training should prefer context-/state-conditioned control hypotheses over assuming one fixed semantic steering vector generalizes across Hyperposition states. This is external design evidence only and does not establish Qwen3.5-0.8B or Claude Code causal access.

## 5. Required schema successor

The current universal gate v1 validates branch-local fields but only checks that `E_plus` and `E_minus` are lists. It does not structurally require evidence identity/ancestry/independence-group fields and does not require a representation of joint compatibility.

A successor frame should add at minimum:

```text
semantic_hyperposition:
  schema: SEMANTIC_HYPERPOSITION_FRAME/v2
  joint_state:
    representation: WHOLE_WORLD_BRANCHES | EXPLICIT_COMPATIBILITY_SETS
    cartesian_completion_allowed: false
    live_worlds: [...]   # required for factorized compatibility-set form
  model_input:
    H_before: ...
    operation:
      type: ...
      affected_branch_ids: [...]
  supervision:
    H_after: ...
    resolution: ...
    output_projection: ...
```

Every non-empty evidence entry should be a typed object carrying at least:

- `evidence_id`;
- `provenance_or_ancestry_id`;
- `independence_group`;
- `relation` / polarity to the branch.

This prevents duplicate evidence packaging from becoming accidental independent votes.

## 6. New hard-negative families

Add paired corrected/incorrect examples for:

1. **Cartesian-product hallucination** — invent a joint world from separately live marginal alternatives;
2. **independence collapse** — treat correlated evidence packets as independent confirmations;
3. **joint-state deletion** — project one factor and silently delete compatibility constraints;
4. **cross-branch evidence bleed** — evidence bearing on one branch mutates unrelated branches;
5. **output-collapse confusion** — selecting one emitted symbol is treated as deleting other live semantic worlds;
6. **branch permutation leakage** — opaque branch ID/order predicts winner;
7. **reopening failure** — a prior resolution remains frozen after its provenance/context precondition becomes stale;
8. **fixed-vector overreach** — one activation/control direction is assumed semantically valid across incompatible contexts without model-specific causal evidence.

## 7. Curriculum consequence

The prior rule remains correct:

`HYPERPOSITION_FRAME_FROM_THE_FIRST_TRAINABLE_EPISODE; FULL_D_OPTIMIZATION_LATE`

It is strengthened to:

`JOINT_COMPATIBILITY_FROM_THE_FIRST_MULTI_VARIABLE_EPISODE; NO_IMPLICIT_INDEPENDENCE`

C/A/B/E examples may still precede full D optimization, but whenever their semantic state contains coupled alternatives, the carrier must already preserve the correct joint hypothesis space.

## 8. Evaluation additions

Before trainable-pilot promotion, add:

- joint-world exact-match / set-F1 on held-out semantic skeletons;
- impossible-combination false-positive rate;
- branch-ID/order permutation invariance;
- evidence-ancestry duplication test;
- nuisance-only decoder;
- conditional MI on all model-visible nuisance signatures;
- evidence-locality mutation tests;
- output-selection-vs-state-retention tests;
- resolution-reopening tests;
- READ / BIND-ROUTE / WRITE separation retained from PR #1956;
- mechanistic decodability before interpreting final-token accuracy as semantic-state learning.

## 9. Versioning / disposition impact

This delta does **not** supersede the cross-cutting semantic-Hyperposition contract v1. It identifies a required successor amendment.

Immediate dispositions:

- semantic-Hyperposition contract v1: `CURRENT_BUT_SUCCESSOR_REQUIRED`;
- universal gate v1: `CURRENT_SOURCE_GATE_BUT_SUCCESSOR_REQUIRED`;
- semantic-Hyperposition seed v1: `DIAGNOSTIC_CANDIDATE_RETROFIT_REQUIRED` because its evidence lists are not yet typed joint-state evidence objects;
- V3 binding-router generator: `BLOCKED`;
- V2.1 fully crossed dynamic-binding blueprint: `CURRENT_NONTRAINABLE_BLUEPRINT`, pending universal-frame materialization and exact ABI/split gates;
- old flat/census/integrated pre-universal-frame rows: `DONOR_OR_RETROFIT_REQUIRED`, not final trainable rows.

A machine-readable status registry is added separately so predecessor/successor/revision reasons are explicit rather than implicit in prose.

## 10. Next exact gate

Implement a versioned universal semantic-Hyperposition gate successor that:

1. validates typed evidence identity/ancestry/independence groups;
2. validates explicit joint-state representation and forbids implicit Cartesian completion;
3. validates evidence locality for declared unaffected branches;
4. keeps output projection separate from semantic resolution;
5. requires reopening policy for resolved states;
6. preserves current branch/projection/authority fail-closed checks.

Then add mutation tests and use the gate on a small newly materialized pilot before any corpus scaling.

## Credit boundary

- accepted dataset tokens: `0` unless separately proven by admitted pipeline evidence;
- training credit: `0`;
- Qwen3.5 causal J-Space credit: `0`;
- whole HCU runtime credit: `0`;
- whole EntityOS runtime credit: `0`.

No paid training, Together call, provider preflight or model intervention is authorized by this delta.