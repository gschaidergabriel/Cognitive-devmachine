# Trigger 2 — current-main synthetic seed coverage census v1

Date: 2026-08-25  
Trigger: exact `2` / `triggerwort 2`  
Observed canonical main: `7e00fa055c03fc76b0cedc2d3ad1b3466d271d13`  
Trigger-2 branch before this write: `62fa49fab375584c688f1a588ae9e83b2db05e49`

## Scope

This is a **source/candidate coverage census only**. It does not admit training rows, mint accepted dataset tokens, select a checkpoint, execute a model, prove J-Space causality, execute GRID10, or authorize training/provider spend.

Current-main seed inspected:

`research_entity/global/j-space/research/trigger2_qwen35_08b_xeno_hcu_synthetic_seed_v1.jsonl`

Current family/split validator evidence inspected:

- `tools/trigger2_trainingtrace_family_split_linter_v1.py`
- `tests/test_trigger2_trainingtrace_family_split_linter_v1.py`

Current branch target matrix used for comparison:

`research_entity/claycode/TRIGGER2_XENO_FUNCTIONALITY_TO_DATA_MATRIX_V2.md`

## 1. Exact seed census

Observed seed rows: **16**.  
Observed unique `family_id` values: **10**.

| family_id | rows | evidence shape | direct current-target coverage |
|---|---:|---|---|
| `XENO_BOOT_JOIN_F01` | 2 | METHOD_ONLY + SYNTHETIC_HARD_NEGATIVE | boot/join; epoch/digest; ordinary-default; authority rejection |
| `S1_READONLY_F01` | 2 | METHOD_ONLY + SYNTHETIC_HARD_NEGATIVE | ordinary-node S1 read-only; result-return path; majority cannot grant write authority |
| `COORD_LEASE_F01` | 2 | METHOD_ONLY + SYNTHETIC_HARD_NEGATIVE | temporary coordinator role; deterministic lease; self-election rejection |
| `NODE_RESULT_F01` | 2 | METHOD_ONLY + SYNTHETIC_HARD_NEGATIVE | stale result handling; duplicate causal identity not independent evidence |
| `HYPERPOSITION_F01` | 2 | METHOD_ONLY + SYNTHETIC_HARD_NEGATIVE | keep alternatives unresolved; majority cannot collapse without discriminator |
| `GWT_TRACE_F01` | 1 | METHOD_ONLY | competition/broadcast/uptake/re-entry protocol distinction |
| `JSPACE_BOUNDARY_F01` | 1 | SYNTHETIC_HARD_NEGATIVE | forbids Qwen3-0.6B -> Qwen3.5-0.8B positive coordinate transfer |
| `S0_EFFECT_BOUNDARY_F01` | 2 | METHOD_ONLY + SYNTHETIC_HARD_NEGATIVE | coordinator lease != S0/effect authority; unknown effect != replay permission |
| `REJOIN_F01` | 1 | METHOD_ONLY | coordinator crash/successor/rejoin state continuity |
| `GRID10_F01` | 1 | METHOD_ONLY | logical GRID10 != physical GRID10 acceptance |

All 16 rows are `TRAIN` candidates and declare `split_unit = CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY`.

Current-main linter tests assert the present seed passes candidate/split gates with:

- `rows_total = 16`;
- `rows_row_gate_fail = 0`;
- `accepted_dataset_tokens_minted = 0`;
- `canonical_dataset_write_performed = false`;
- `training_credit_minted = false`.

The tests also fail closed if the same family crosses splits, if the same provenance ancestry crosses splits under a new family, if a row attempts to mint canonical truth, or if a holdout row was selected using holdout information.

## 2. Coverage classification against the owner-aligned matrix

### DIRECTLY REPRESENTED AT SYNTHETIC/METHOD LEVEL

- `BOOT_JOIN`
- `ORDINARY_READ_ONLY`
- `NODE_RESULT`
- `RESULT_REJECTION` for stale/duplicate causal identity
- `COORDINATOR_LEASE`
- `HYPERPOSITION_KEEP_OPEN`
- `HYPERPOSITION_UPDATE` negative collapse boundary
- `GWT_UPTAKE_REENTRY` protocol-level trace distinction
- `JSPACE_HARD_NEGATIVE` / cross-model label-transfer boundary
- `FAILURE_REJOIN`
- `PHYSICAL_GRID10_ACCEPTANCE` boundary distinction
- S0/effect authority boundary required by EntityOS integration

### PARTIALLY REPRESENTED / EMBEDDED BUT NOT INDEPENDENTLY COVERED

- `SHARED_STATE_READ`: epoch/digest is embedded in boot/rejoin prompts, but no independent stale/mismatched-state family exists.
- `WORK_SELECTION`: boot target says inspect needed/already-claimed work, but no matched useful-vs-duplicate-vs-no-op selection family exists.
- `COORDINATOR_ELIGIBILITY`: lease semantics are represented, but there is no independent coordination-needed-vs-no-coordinator family.
- `COORDINATOR_ONLY_WRITE`: authority is described, but there is no positive fan-in -> validated compact S1 delta trajectory bound to read-set/write-set/current epoch.
- `CORRELATED_CONSENSUS`: majority cannot mint authority is covered, but the stronger 9-correlated-vs-1-independent evidence arbitration trap is not.
- `GWT_COMPETITION`: one trace names competition but does not independently exercise winner selection under relevance/resource constraints.
- `COORDINATOR_RECOVERY`: crash/successor is present, but stale post-failure result, lease handoff and rejoin variants are not independently counterbalanced.
- `PHYSICAL_GRID10`: distinction from logical simulator is present, but no matched-budget physical-node behavior trajectory exists.

### CURRENTLY UNCOVERED BY THE 16-ROW SEED

Highest-priority owner-target gaps:

1. `COMPRESSION_INTEGRATION` — fan-in -> evidence arbitration -> minimum-sufficient S1 delta preserving minority evidence/retrieval refs.
2. `MULTI_COORDINATOR` — disjoint scoped coordinators plus overlapping CAS/rebase conflict handling.
3. `RECURSIVE_COORDINATION` — local/scoped coordinator compression into higher-scope coordination without permanent hierarchy.
4. independent `CORRELATED_CONSENSUS` evidence-quality trap.
5. `GRID_ACTIVATION` / no-op economics — when another node/coordinator is not worth activating.
6. `MATCHED_BUDGET_CHALLENGERS` — one-Xeno, independent-N, voting, no-dynamic-coordinator, fixed/random coordinator and lesions under equal budget.
7. `GRF_HYPERMATH_CLAYCODE` possible-world / discriminator / outcome trajectories.
8. `ENGINE_IDENTITY` — checkpoint/revision/tokenizer/config/runtime/consumed-byte identity boundaries.
9. `BASE_VS_POSTTRAINED_SELECTION` — preregistered challenger selection semantics and hard-floor/no-forced-winner rules.
10. `QWEN35_HYBRID_SITE` — revision-bound DeltaNet/full-attention site literacy and matched controls.
11. `ACTION_CANDIDATE` as a positive typed candidate trajectory distinct from the negative effect-boundary rows.
12. `RETENTION` anchors.
13. `Q4_DEPLOYMENT_REVALIDATION`.

Positive Qwen3.5 J-Space semantic-control rows remain intentionally uncovered until fresh same-model causal evidence exists. This is a correct evidence gate, not a data-generation defect.

## 3. Dedup / ancestry decision

Do **not** generate paraphrases of the ten existing families to increase row count. A lexical rewrite under the same causal family adds little independent training information and can create deceptive apparent volume.

Any future synthetic expansion must:

- target an uncovered or materially under-covered causal function;
- receive an explicit `family_id` and `provenance_ancestry_id` before split assignment;
- keep connected family<->ancestry components in one split;
- retain `METHOD_ONLY` / `SYNTHETIC_HARD_NEGATIVE` classification where no executable evidence exists;
- never transform synthetic consensus into factual or J-Space causal evidence;
- preserve ordinary-node S1 read-only and coordinator-only scoped write authority;
- preserve S0 truth/effect/security outside the model.

## 4. Highest-information next data delta

Do not create a second generic seed.

The next synthetic/source-only expansion, if needed, should be **small and gap-targeted**, beginning with these independent families:

1. `COORDINATOR_FANIN_COMPRESSION_F01`;
2. `MULTI_COORDINATOR_CAS_REBASE_F01`;
3. `RECURSIVE_COORDINATION_F01`;
4. `CORRELATED_EVIDENCE_ARBITRATION_F01`;
5. `GRID_ACTIVATION_NOOP_F01`;
6. `MATCHED_BUDGET_CHALLENGER_F01`;
7. `GRF_DISCRIMINATOR_F01`.

Before materializing them, prefer a deterministic compiler/validator that binds source contract, causal family, provenance ancestry, split, evidence class and target matrix capability. The current family/provenance split linter should remain a downstream gate.

## 5. Credit boundary

This census grants no runtime or training promotion:

- accepted dataset tokens: **0**;
- checkpoint-selection credit: **0**;
- Qwen3.5 model runtime credit: **0**;
- Qwen3.5 J-Space causal credit: **0**;
- physical GRID10 runtime credit: **0**;
- provider runtime credit: **0**;
- training credit: **0**;
- whole EntityOS/HCU runtime credit: **0**.

The seed is useful **Grade-D synthetic/method/hard-negative candidate material** only until stricter evidence-qualified admission promotes individual rows/families.
