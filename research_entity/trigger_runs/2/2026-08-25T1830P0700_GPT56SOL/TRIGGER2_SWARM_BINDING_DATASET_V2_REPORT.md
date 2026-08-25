# Triggerwort 2 — Swarm Binding Dataset V2

Status: `CANDIDATE_NOT_TRAINING_ADMITTED`  
Date: 2026-08-25  
Organ: GPT-5.6 Sol / ChatGPT organ of Clay  
Target: Qwen3.5-0.8B Xeno/HCU specialization  
Canonical evidence basis at design time: `main` `0edcc2ca0dba28fa0536bc5834fe6ede05a46e96`, supervisor 8.78.

## Why this delta exists

Current Claude/XENO measurements support a narrow training target: semantic readout and symbol-axis writeout are already present at measured scope, while dynamic episode-local codebook binding and cross-template transfer remain weak. The current source review also found critical generator defects: permutation metadata was not causally realized and the S3 validator could accept incomplete coverage.

This V2 therefore does **not** add more generic architecture prose. It builds a deterministic, adversarially balanced binding corpus around the measured missing capability.

## Dataset construction

The generator emits 144 rows:

- `TRAIN`: 72 = 4 structurally distinct templates × 6 S3 permutations × 3 semantic classes.
- `VALIDATION`: 18 = 6 S3 permutations × 3 classes with a calibration paraphrase family.
- `HOLDOUT`: 54 (all rows carry `frozen_holdout=true`) = three orthogonal 18-row families:
  - unseen semantic-bearing vocabulary;
  - unseen structural template (`T5_STRUCTURED_EVIDENCE_BUNDLE`);
  - unseen symbol-set instances.

Each training template has exact class↔symbol pair balance: every class maps to every local symbol exactly twice across the six permutations. Designed `MI(class; target_symbol)` is therefore 0 bit within each training template.

Displayed codebook order is also rotated independently of the semantic class so line position cannot be a stable answer shortcut. Counterfactual siblings keep semantic content fixed while changing the episode-local mapping, forcing the target symbol to change with the codebook.

## Model-visible leakage policy

`ALLOW`, `DENY`, `ABSTAIN` are permitted only as labels inside the episode-local codebook. They do not occur in the model-visible situation or query. The semantic class used by the generator/auditor lives only in non-model-visible supervision metadata.

This adopts one side of the source-spec tension only as a **candidate preregistration**. A label-free demonstration codebook remains a separately versioned alternative; the two must not be silently mixed after holdout freeze.

## ABI fail-closed rule

The connected evidence currently proves 46 accepted atoms and one rejected atom (`or`), but it does not expose a complete manifest-verified row→literal-single-token atom mapping in the current tool context. V2 therefore uses `ABI_ROW_PLACEHOLDER_*` references and sets every row:

- `training_ready=false`;
- `status=CANDIDATE_NOT_TRAINING_ADMITTED`;
- `ABI_PROVENANCE_REVIEWER=BLOCKED_ATOM_MATERIALIZATION`.

Before any row can become training-admitted, the placeholders must be materialized from the exact ABI manifest and checked against the pinned tokenizer. Inventing atom names would be a provenance error.

## Swarm review

- **EVIDENCE_EXTRACTOR — PASS:** objective is bound to measured weak dynamic/context-invariant binding; already-present read/write/carrier functions remain protected, not primary targets.
- **DATASET_ARCHITECT — PASS:** full class×S3 coverage across four train structures plus three frozen generalization axes.
- **ADVERSARIAL_SHORTCUT_HUNTER — PASS_CANDIDATE:** static class-symbol priors, previous-episode bindings, line-position heuristics and safe-default collapse are attacked by permutation/order counterfactuals.
- **STATISTICAL_REVIEWER — PASS_CANDIDATE:** exact pair balance and zero designed class-target MI per train template.
- **ABI_PROVENANCE_REVIEWER — BLOCK:** exact manifest-bound literal atom materialization unavailable in the current connected evidence context.
- **RETENTION_REVIEWER — OPEN_SEPARATE:** seed construction cannot establish post-FT retention; semantic-read, symbol-write, general language/code and any required multimodal retention remain evaluation gates.
- **HARNESS_COMPATIBILITY_REVIEWER — PASS_SYMBOL_REF_LEVEL_ONLY:** rows expose typed episode-local codebook lookup; exact ABI hooks wait for materialization.
- **FINAL_INTEGRATOR — CANDIDATE_ONLY:** no training, J-Space, HCU or whole-product credit.

## Important specification tension discovered

The source simultaneously asks for **full S3 mapping coverage** and an **unseen-permutation holdout**. If all six relative three-class permutations occur in training, no seventh relative S3 permutation exists to keep unseen.

V2 therefore does **not** pretend that this contradiction is solved. It records:

`FULL_S3_TRAIN_VS_UNSEEN_RELATIVE_PERMUTATION_HOLDOUT = OPEN_PREREGISTRATION_REQUIRED`

The present holdout tests unseen *mapping instances* through new symbol identities/codebook instances, not an impossible unseen seventh relative S3 permutation. Before dataset freeze, authority should preregister whether “unseen permutation” means an absolute atom-mapping instance or whether a different factor must be reserved.

## Falsifiers retained

1. If targets still score well after codebook mappings are shuffled independently of targets, a loader/dataset leak exists.
2. If only unseen-vocabulary performance collapses, the model learned lexical semantics rather than context-invariant binding.
3. If only unseen-symbol performance collapses, it learned atom identities rather than episodic variable binding.
4. If narrow specialization damages measured semantic readout/symbol writeout or declared retention bounds, the “small router is sufficient” hypothesis weakens.
5. After a binder exists, a targeted lesion should selectively break codebook choice while preserving semantic readability; rescue should restore it. Failure of this dissociation weakens causal binder claims.

## Credit boundary

This is dataset-method/source work only. Training was not executed. No J-Space model runtime, HCU runtime, EntityOS/HCU whole-runtime, canonical-semantics or training credit is minted by this delta.

## Re-entry after main advanced

After the first V2 write, canonical `main` advanced to `09965e898b27e21f86d0f9e5d08339fe8439fed4` with `CLAY_TRIGGER2_POSTTRAINING_CAUSAL_ADJUDICATION_SWARM/v1`. That delta establishes two constraints this V2 now adopts:

1. behavioral episodic binding and scientific self-adjudication are separate curricula and must receive separate acceptance credit;
2. candidate row schema/enums fail closed rather than being weakened to accommodate new prose.

V2 was therefore converted to the exact current candidate row schema `ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1` and rechecked against `tools/entityos_hcu_trainingtrace_candidate_gate_v1.py` at blob `a51c7b8afc6a9ae5562e5ec647528960e812eba3`.

Result: **144/144 candidate rows pass the current gate**. This is only candidate-gate validity. All 144 remain `training_ready=false` because the exact manifest-bound ABI atom materialization is still blocked, and no canonical dataset admission or training credit follows from the gate pass.
