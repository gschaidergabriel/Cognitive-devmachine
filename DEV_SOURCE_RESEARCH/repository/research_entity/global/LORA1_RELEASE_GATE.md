# LoRA-1 Release Gate — Project Owner Fixed Conditional Authorization

**Status:** PROJECT_OWNER_FIXED_CONDITIONAL_AUTHORIZATION
**Date:** 2026-08-09

## Owner decision

The first paid Clay-native LoRA training job may be started **only after ALL THREE release gates below are complete and machine-verifiably PASS in the canonical repository**:

1. **CLAYCODE_RELEASE_GATE = PASS**
2. **REFERENCE_HARNESS_RELEASE_GATE = PASS**
3. **CLAY_HARNESS_RELEASE_GATE = PASS**, including differential equivalence against the frozen Reference Harness

The order is strict:

`finish ClayCode -> finish normal/reference Harness -> rebuild same frozen Harness in ClayCode -> differential/replay equivalence -> LoRA-1`

Before all three gates pass:

`LORA1_AUTHORIZED = false`

After all three gates pass:

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
- no unresolved blocker that makes the language unusable by either Harness.

Expected release artifact: `CLAYCODE_RELEASE_MANIFEST.json` with `gate=CLAYCODE_RELEASE_GATE` and `status=PASS`.

## Gate B — Reference Harness release

The first Harness implementation is the **normal host/reference implementation**. Python and other ordinary host languages may be used. Its job is correctness, observability and ease of independent inspection, not ClayCode self-hosting.

It must execute/simulate the complete frozen current FRANK architecture around the model call and satisfy `research_entity/triggers/HARNESS_BUILD_PROTOCOL.md` plus `research_entity/experiments/FRANK_TEST1_CLAY_NATIVE_FULL_SIMULATION_CONTRACT.md`.

Minimum machine-verifiable evidence:

- current nine-branch mesh freeze with exact artifact hashes;
- complete architecture/module/state/transition coverage;
- canonical state/epoch/provenance identity;
- translator/Needle boundary exactly modeled without redesigning Needle;
- UnifiedDB, ClayGraph, GWT, personality/self/world/body/goals, model adapter, effect/authority/outcome/re-entry, recovery and observability paths;
- deterministic replay or explicit nondeterminism receipts;
- checkpoint/recovery/idempotency;
- ablation/intervention controls;
- golden traces;
- unit/integration/end-to-end/property/fuzz/mutation/adversarial/concurrency/crash/long-horizon tests;
- architecture coverage report;
- historical architecture-knowledge audit proving relevant Project-Frankenstein predecessors/failures were reviewed;
- no unresolved limitation invalidating Test 1.

Expected release artifact: `REFERENCE_HARNESS_RELEASE_MANIFEST.json` with `gate=REFERENCE_HARNESS_RELEASE_GATE` and `status=PASS`.

## Gate C — Clay Harness release

After Gate A and Gate B PASS, rebuild the **same exact frozen architecture** as a ClayCode-native Harness using the frozen ClayCode release.

The Clay Harness is not allowed to simplify the Reference Harness merely to fit the language. If ClayCode cannot express a required state/transition/module, that is a ClayCode release defect and Gate A must be reopened.

Required evidence:

- exact architecture freeze identical to the Reference Harness;
- all architecture-relevant state represented in ClayCode or through explicitly typed Clay/host boundary contracts;
- same Golden Trace input corpus;
- same deterministic model fixtures for pre-LoRA testing;
- same interventions/ablations;
- same failure/recovery scenarios;
- cross-implementation differential oracle comparing every architecture-relevant state transition and receipt;
- semantic identity equivalence after allowed representation normalization;
- no unexplained state, ordering, authority, memory, GWT, replay or outcome divergence;
- Clay Harness executes its own nontrivial test scenarios and can be inspected/debugged by ClayCode-capable workers;
- self-simulation tests in which workers use the Harness as if they were FRANK, while preserving that this is a simulation and not evidence of consciousness.

Expected release artifact: `CLAY_HARNESS_RELEASE_MANIFEST.json` with `gate=CLAY_HARNESS_RELEASE_GATE` and `status=PASS`.

A final aggregate `HARNESS_RELEASE_MANIFEST.json` may only report `PASS` if both Reference and Clay Harness release manifests are PASS and their differential-validation manifest is PASS.

## Historical architecture knowledge gate

Before either Harness may PASS, the project must maintain a durable, queryable architecture archaeology/knowledge base derived from `gschaidergabriel/Project-Frankenstein` plus current RAE research.

For every material FRANK subsystem or design family, record:

- source commit/file/paper;
- version/time period;
- intended mechanism;
- measured or reported result;
- success/failure/partial/superseded status;
- discovered bugs/failure modes;
- causal confidence/evidence class;
- what replaced it and why;
- current reusable invariant/best practice;
- affected current modules;
- explicit decision: reuse, adapt, reject, or retest;
- originality classification and prior-art status.

Commit messages are useful historical evidence but do not automatically prove measured performance claims. Preserve source class and uncertainty.

## Operational preflight after all gates PASS

Immediately before LoRA-1 start, the worker must still:

1. verify the exact current Together model ID and supported fine-tuning mode;
2. load the Together API key only from runtime secret/environment, never repository text;
3. freeze the exact training dataset and hashes;
4. freeze held-out evaluation separately and prove it is excluded from training;
5. record hyperparameters and random seeds;
6. record the Together cost estimate and available budget;
7. define stop/failure criteria;
8. create a training run manifest linking all three PASS gate manifests;
9. only then submit the paid job.

## LoRA-1 target

LoRA-1 trains the Qwen-class 4B as the Clay-native cognitive kernel defined by the current Test-1 curriculum. It does not replace the repository-driven FRANK architecture, Needle, canonical state machine, external authority, tool/effect paths or runtime receipts.

## Hard law

`ClayCode PASS AND Reference Harness PASS AND Clay Harness PASS -> LoRA-1 may start`

`otherwise -> no training`
