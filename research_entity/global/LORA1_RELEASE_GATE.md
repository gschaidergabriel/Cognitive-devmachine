# LoRA-1 Release Gate — Project Owner Fixed Conditional Authorization

**Status:** PROJECT_OWNER_FIXED_CONDITIONAL_AUTHORIZATION
**Date:** 2026-08-09

## Owner decision

The first paid Clay-native LoRA training job may be started **only after BOTH of the following gates are complete and machine-verifiably PASS in the canonical repository**:

1. **CLAYCODE_RELEASE_GATE = PASS**
2. **HARNESS_RELEASE_GATE = PASS**

When both gates are PASS, LoRA-1 is authorized by the project owner without requiring a new architecture approval turn. Training still requires the operational preflight below.

Before both gates pass:

`LORA1_AUTHORIZED = false`

After both gates pass:

`LORA1_AUTHORIZED = true`

No Together fine-tuning job, paid model-training call or equivalent may be started merely because credentials or budget exist.

## Gate A — ClayCode release

ClayCode must be an executable frozen language/runtime release, not a research memo or JSON schema candidate.

Minimum machine-verifiable release evidence:

- frozen semantic-language specification and exact version/hash;
- parser for the frozen model-facing ClayCode representation;
- canonicalizer;
- typed canonical semantic IR;
- deterministic semantic hashing/identity;
- validator and type/effect checker;
- executable/reference evaluator for the defined core;
- defined control/data semantics;
- TCQS/collection semantics;
- representation of general-purpose computations and typed effect intents without granting authority;
- lowering interface plus translation-validation receipts;
- explicit UNKNOWN/CONFLICT/REVOKED/error semantics;
- conformance suite;
- unit/integration/property/fuzz/mutation/round-trip tests;
- broad application/program corpus;
- dataset generator derived from the frozen semantics;
- separately frozen held-out evaluation generator/corpus;
- release manifest with exact artifact hashes;
- executed test manifest showing required tests actually ran;
- no unresolved blocker that makes the language unusable by the Harness or target 4B.

Expected release artifact:

`CLAYCODE_RELEASE_MANIFEST.json`

with at minimum:

```json
{
  "gate": "CLAYCODE_RELEASE_GATE",
  "status": "PASS",
  "release_id": "...",
  "spec_hash": "...",
  "runtime_hash": "...",
  "test_manifest_hash": "...",
  "training_corpus_generator_hash": "...",
  "heldout_generator_hash": "..."
}
```

## Gate B — Harness release

The FRANK Test-1 Harness must execute/simulate the complete frozen current FRANK architecture around the model call and satisfy `research_entity/triggers/HARNESS_BUILD_PROTOCOL.md` plus `research_entity/experiments/FRANK_TEST1_CLAY_NATIVE_FULL_SIMULATION_CONTRACT.md`.

Minimum machine-verifiable release evidence:

- current nine-branch mesh freeze with exact artifact hashes;
- full frozen FRANK module/state/transition coverage;
- executable ClayCode integration using Gate-A release;
- canonical state/epoch/provenance identity;
- Needle and human-language boundary integration without redesigning Needle;
- UnifiedDB logical/query/result/transaction semantics;
- ClayGraph route/admissibility/Assembly semantics;
- GWT competition/workspace/broadcast/receiver causal-chain semantics;
- personality/self/world/body/goal state support;
- model adapter `ClayReaderFrame -> ClayModelOutput` boundary;
- proposal/effect/authority/resource/receipt boundaries from the frozen architecture;
- outcome/re-entry/salience/credit paths;
- deterministic replay or explicit receipts for nondeterministic boundaries;
- checkpoint/recovery/idempotency behavior;
- ablation/intervention controls;
- golden trace suite;
- unit/integration/end-to-end/property/fuzz/mutation/adversarial/concurrency/crash/long-horizon tests;
- architecture coverage report;
- open limitations explicitly classified and no unresolved limitation that invalidates Test 1.

Expected release artifact:

`HARNESS_RELEASE_MANIFEST.json`

with at minimum:

```json
{
  "gate": "HARNESS_RELEASE_GATE",
  "status": "PASS",
  "release_id": "...",
  "architecture_freeze_hash": "...",
  "claycode_release_ref": "...",
  "state_schema_hash": "...",
  "replay_validation_hash": "...",
  "test_execution_manifest_hash": "..."
}
```

## Operational preflight after both gates PASS

Conditional owner authorization does not waive execution hygiene. Immediately before LoRA-1 start, the worker must still:

1. verify the exact current Together model ID and supported fine-tuning mode;
2. load the Together API key only from runtime secret/environment, never repository text;
3. freeze the exact training dataset and hashes;
4. freeze held-out evaluation separately and prove it is excluded from training;
5. record hyperparameters and random seeds;
6. record the Together cost estimate and available budget;
7. define stop/failure criteria;
8. create a training run manifest linking the two PASS gate manifests;
9. only then submit the paid job.

## LoRA-1 target

LoRA-1 trains the Qwen-class 4B as the **Clay-native cognitive kernel** defined by the current Test-1 curriculum: ClayCode fluency plus the frozen cognitive/self/personality/goal/digital-body/GWT concepts required by the project. It does not replace the repository-driven FRANK architecture, Needle, canonical state machine, external authority, tool/effect paths or runtime receipts.

## Hard law

`ClayCode PASS AND Harness PASS -> LoRA-1 may start`

`otherwise -> no training`
