# HCU J-Space Model-Input Control Closure Source Revalidation Gate v1

Status: **CURRENT 8.63 SOURCE ACCEPTANCE LAW — NO RUNTIME OR TRAINING CREDIT**

Persistent entity: Clay  
Product: EntityOS  
Compute architecture: HCU  
Mode: FREE_ONLY

## Finding

`ENTITYOS_HCU_JSPACE_MODEL_INPUT_CONTROL_CLOSURE/v1` has two deliberately different evidence levels:

1. `jspace_model_input_control_closure_v1.validate_closure(closure)` proves the serialized field contract and canonical self-hash of one closure object.
2. `jspace_model_input_control_closure_revalidation_v1.revalidate_closure_against_canonical_sources(...)` re-derives the exact control admission from the existing canonical MiniUnifiedDB path and reconstructs the closure from exact producer evidence before equality is accepted.

A self-consistent closure digest is therefore not independent proof that the packet/control identities inside it were observed at the model-input boundary.

At the observed retained donor head, `jspace_training_control_delivery_gate_v1.require_model_input_control_closure(...)` uses level 1 plus cross-field equality with TrainingTrace and JSpaceInferenceBinding, while `compile_admitted_jspace_training_dataset_v1.compile_admitted_records(...)` accepts a caller-provided `admitted_model_input_control_closures` mapping. That mapping does not by itself establish level-2 source revalidation.

`FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`: the existence of the semantic revalidator does not mean a particular persisted closure passed it.

## Mandatory single-path rule

Before a non-`BASELINE` record may be emitted by the serious J-Space training compiler, the single retained path MUST:

1. complete the existing DatasetAdmission, Vector-Control preimage admission, InferenceReceipt parent admission and J-Space inference-binding gates;
2. resolve the exact `JSpaceModelInputControlClosure/v1` associated with the admitted J-Space binding;
3. resolve the exact canonical source evidence required by `revalidate_closure_against_canonical_sources(...)`:
   - caller-supplied existing canonical MiniUnifiedDB connection;
   - exact `ModelInputControlBinding` producer object;
   - exact consumed model-input bytes;
   - scheduler-owned `GridPlan` object;
   - admitted `HCU_INFERENCE_RECEIPT/v4` producer object;
   - exact `JSpaceInferenceBinding/v3` object;
   - current canonical generation;
4. call the existing single semantic revalidation boundary and require returned equality with the supplied closure;
5. fail closed before any lower-level training-row emission if the canonical source bundle is missing, ambiguous, stale-generation, or semantically mismatched;
6. only after level-2 source revalidation apply/complete the existing training control-delivery cross-binding checks;
7. preserve an explicit source-revalidation fact or exact source identities in emitted provenance so downstream dataset/training stages cannot silently downgrade the evidence level to self-hash-only.

No second database, model-input admission store, truth authority, effect path, J-Space implementation, inference implementation or training authority may be introduced to satisfy this gate. Reuse the existing canonical MiniUnifiedDB and producer/revalidation code.

## Persisted registry boundary

A caller-owned mapping named `admitted_model_input_control_closures` is not authority merely because its keys and objects are digest-valid. If persisted registries are used, the compiler must obtain the producer preimages from already-admitted canonical records or receive them explicitly from the single upstream admission path. It MUST NOT manufacture producer objects from the closure's own flattened fields and then claim independent revalidation.

## Required negative discriminator

Before source promotion, add at least this regression:

1. build one exact valid non-BASELINE training/inference/control-delivery chain;
2. copy the resulting closure;
3. replace `control_admission_sha256` and/or `control_binding_sha256` with different valid lowercase non-placeholder SHA-256 values while keeping all trace/inference-facing fields unchanged;
4. recompute the outer `closure_sha256` canonically so level-1 `validate_closure()` still succeeds;
5. place the forged object into the same caller-owned closure registry position used by the serious compiler;
6. require serious training promotion to fail at canonical-source revalidation with a source-mismatch class before lower-level row emission;
7. require the exact canonical closure to remain idempotently admissible through the same path.

Additional useful negatives:

- same closure digest family but wrong control binding producer -> reject;
- correct control binding but different consumed input bytes -> reject;
- GRID plan transplant -> reject;
- stale generation -> reject before admission/write;
- InferenceReceipt/JSpaceBinding transplant -> reject;
- missing canonical source bundle for non-BASELINE -> reject rather than downgrade to level 1.

## Evidence boundary

Satisfying this source gate would establish deterministic provenance that one serious-training intervention row's control-delivery closure was reconstructed from the canonical admitted source chain. It would **not** establish:

- hidden-state causal use of the control vector;
- real model execution;
- whole HCU runtime acceptance;
- model quality or training benefit;
- EntityOS whole-runtime PASS;
- paid-training permission.

Current credits remain:

- whole EntityOS/HCU runtime: 0
- full HCU runtime: 0
- J-Space model runtime: 0
- training: 0
- whole product PASS: false

## Next exact implementation gate

In the single retained PR1263 compiler path, wire `revalidate_closure_against_canonical_sources(...)` into non-BASELINE serious training promotion using exact admitted producer evidence; add the forged-self-consistent closure regression above; keep the existing control-delivery gate and inference-binding source-revalidation law; then execute only on an admitted exact-source FREE_ONLY surface when auth/quota/upgrade fences permit.
