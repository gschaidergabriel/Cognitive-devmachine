# HCU J-Space Serious Compiler Source Revalidation Gate v1

Status: **CURRENT 8.63 SOURCE ACCEPTANCE LAW — NO RUNTIME OR TRAINING CREDIT**

Persistent entity: Clay  
Product: EntityOS  
Compute architecture: HCU  
Mode: FREE_ONLY

## Finding

`ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v3` has two distinct evidence levels:

1. `validate_binding(binding)` proves structural validity, internal cross-binding and digest consistency.
2. `revalidate_binding_against_sources(binding, training_trace, inference_receipt, grid_plan)` re-derives the binding from its exact producer sources and rejects a digest-valid binding whose correlated summary fields were consistently relabelled.

The serious dataset compiler must not collapse these levels. A persisted/self-consistent binding is not independent source proof.

## Mandatory single-path rule

Before `compile_admitted_jspace_training_dataset_v1.py` may emit any serious train/validation/holdout row, its one canonical path MUST:

1. complete existing DatasetAdmission and Vector-Control preimage admission;
2. resolve the admitted `JSpaceInferenceBinding/v3` for the exact TrainingTrace;
3. resolve the exact admitted `HCU_INFERENCE_RECEIPT/v4` source consumed by that binding;
4. resolve the exact scheduler-owned `ENTITYOS_HCU_GRID_PLAN/v2` source identified by the binding;
5. resolve/reconstruct the exact typed TrainingTrace source rather than trusting only a flattened mapping summary;
6. call the single reusable `jspace_inference_binding_revalidation_v1.revalidate_binding_against_sources(...)` boundary, or a semantically identical single-authority adapter that reaches it;
7. fail closed before lower-level row compilation if source revalidation fails;
8. only then apply the existing model-input control-delivery gate for non-BASELINE intervention rows;
9. preserve the source-revalidation fact/digest or exact source identities in emitted metadata/receipt provenance so downstream training cannot forget which evidence level was satisfied.

No second compiler, second binding implementation, second GridPlan authority, second state store or second effect path may be created to satisfy this gate.

## Persisted mapping boundary

If the serious compiler receives persisted mappings rather than typed producer objects, it MUST NOT manufacture typed objects from caller-controlled flattened binding fields alone. It must obtain or deterministically reconstruct them from admitted producer records whose canonical identities are already bound to the trace/binding/receipt/GridPlan registries.

`FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT` applies: having the revalidation method in source does not mean a persisted binding has passed it.

## Required negative regressions

At minimum, before source promotion:

- digest-valid correlated `cell_id` relabel -> reject;
- digest-valid correlated `role` relabel -> reject;
- digest-valid correlated model-call/invocation relabel -> reject;
- digest-valid engine identity/artifact relabel -> reject;
- GridPlan transplant with recomputed outer binding digest -> reject;
- exact source-derived binding -> accept;
- source revalidation failure must occur before lower-level compiler row emission;
- non-BASELINE row must still independently satisfy the existing model-input control-delivery closure after source revalidation.

## Evidence boundary

Passing this gate would establish only deterministic source-aware provenance for the serious J-Space dataset compiler. It does **not** establish hidden-state causality, real model execution, HCU runtime acceptance, training benefit, EntityOS whole-runtime PASS, or permission for paid training.

Current credits remain:

- whole EntityOS/HCU runtime: 0
- full HCU runtime: 0
- J-Space model runtime: 0
- training: 0
- whole product PASS: false

## Next exact implementation gate

Integrate the existing source revalidator into the single serious compiler path using admitted exact TrainingTrace + InferenceReceipt/v4 + scheduler GridPlan sources, add the negative regressions above, then execute them only on an admitted exact-source FREE_ONLY surface when quota/auth/upgrade fences permit. Do not invoke a paid/upgrade path and do not infer runtime credit from source tests alone.
