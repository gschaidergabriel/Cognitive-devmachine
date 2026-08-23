# Hyperposition Computational Unit (HCU)

Status: **ENTITYOS/HCU RETAINED DONOR LANE — SOURCE / TRAINING-READINESS CANDIDATE, ZERO RUNTIME CREDIT**

HCU is the sole current integrated cognition/compute architecture being co-developed inside EntityOS. The `MicroEntity` directory name is compatibility/provenance only; it is not a second product or persistent entity.

## Current path

The current source candidate is deliberately split into deterministic authority/evidence stages:

`Typed Entry -> typed Entry binding -> HCU route -> verified EngineAdmission -> engine-load lease -> actual loader-read consumption -> VerifiedEngineLoad -> inference receipt v3 -> GRID10 plan`

All current causal identities target `RFC8785_JCS_IJSON/v1`. Historical CBOR, custom typed-canonical, host-Python JSON and older inference identities retain only their original bounded scope and must not be silently relabelled as current JCS identities.

Pre-load hashing is necessary but is **not** loader attestation. The current inference path consumes `HCU_VERIFIED_ENGINE_LOAD/v1`, which binds a generation-fenced engine-load lease to evidence reported from the actual loader read path. Matching caller-supplied hashes alone grant zero runtime credit.

## Current source files

- `entry_canonicalization_v1.py` — selected RFC8785/JCS implementation.
- `xeno_entry_fabric_v1.py` — compatibility-named Typed Entry Fabric; current event/admission identity is v2.
- `reactive_event_router_v1.py` — deterministic script-first HCU router using typed Entry-binding v2.
- `engine_admission_v1.py` — exact local engine artifact verification and versioned EngineAdmission receipt.
- `engine_load_lease_v1.py` — generation-fenced load intent plus actual-loader consumption verification.
- `inference_receipt_v1.py` — **single current inference producer**, emitting `HCU_INFERENCE_RECEIPT/v3` and consuming `VerifiedEngineLoad`.
- `grid10_scheduler_v1.py` — `ENTITYOS_HCU_GRID_PLAN/v2`; JCS-bound logical GRID10 planning with typed Entry binding. Logical cells are not physical decoders or model calls.
- `jspace_vector_control_v1.py` — source candidate for `JSPACE_VECTOR_CONTROL_ABI/v1`, a deterministic JCS/hash-bound symmetric-q8 control packet with exact rational scale representation and generation/basis/role/control-condition fences.
- `jspace_gwt_prototype_v1.py` — source candidate for deterministic bounded GWT competition and immutable `JSPACE_GWT_TRANSITION_TRACE/v1` production bound to Entry -> Route -> GRID10 -> model-cell -> vector-control identities.
- matching `test_*.py` files — deterministic regression obligations only until executed on an admitted isolated executor.
- `HCU_DATA_INDEX.json` — current package/path selection.
- `receipts/` — bounded non-secret evidence receipts.

`inference_receipt_v2.py` and its test were removed after convergence to the single current inference producer. `physical_engine_lease_v1.py`, custom typed-canonical source and other earlier overlapping paths are historical/noncurrent evidence unless current authority explicitly re-admits them. They must not become a second active inference, canonicalization or loader-authority lane.

## Global J-Space / GWT training-readiness track

Current owner authority permits exactly one first serious Together fine-tuning run for the selected ~0.8B HCU model, but **only after** a functional instrumented Global J-Space/GWT prototype produces real traces, causal/lesion/control evidence is obtained, `JSPACE_VECTOR_CONTROL_ABI/v1` is frozen, and train/validation/holdout data are compiled and baseline-evaluated.

The current source candidate advances only the pre-training interface:

`measured/controlled vector -> JSPACE_VECTOR_CONTROL_ABI/v1 -> bounded GWT competition -> Entry/Route/GRID10-bound transition trace`

Important boundaries:

- the q8 packet is a deterministic token/byte control interface that Together SFT and the local runtime can both reproduce; it is **not** proof of arbitrary hidden-state or residual-stream injection;
- GWT competition is deterministic and bounded; candidate count/majority does not mint truth;
- transition traces are research telemetry/training evidence only, never canonical EntityOS truth/state or effect authority;
- baseline/null/sign-flip/permutation/role-swap/lesion conditions are explicit controls;
- the current real instrumented model trace count is **0**;
- the one-shot Together authorization remains **unconsumed** until an actual Together fine-tuning job is created and its non-secret job ID is durably recorded;
- training launch is currently **not admitted**.

## Authority

Canonical durable state/evidence remains deterministic EntityOS authority. HCU vectors, world-model fields, simulations, J-Space/workspace outputs and model outputs remain candidate/projection/measurement evidence. EffectGate/EffectJournal remain the only real-effect authority. Entry data may request routing but may not mint engine identity, capabilities, truth or effects.

## Evidence boundary

Current work is **source/mechanism and training-readiness convergence only**. No exact-current combined Entry -> route -> real loader -> VerifiedEngineLoad -> inference-v3 -> GRID10 execution has been observed on an actually-started authorized isolated executor. The new Vector-Control/GWT files have not yet produced a real model/J-Lens trace. No real local ~0.8B model runtime, target-hardware capacity, J-Space causality, VPS, OCI or whole EntityOS/HCU PASS is claimed.

A READY Vercel controller exists for atomic current-main + retained-HCU snapshot execution, but this worker's exposed Vercel connector currently has no arbitrary authenticated POST/Sandbox-run action. An authenticated GET to `/api/go-cycle-v2` returns `405 Method Not Allowed` with `Allow: POST`; therefore READY deployment state receives no semantic runtime credit.

## Next exact gates

1. Execute the exact current Entry -> Route -> EngineAdmission -> actual-loader VerifiedEngineLoad -> inference-v3 -> GRID10 regressions in an admitted isolated executor.
2. Execute `test_jspace_vector_control_v1.py` and `test_jspace_gwt_prototype_v1.py` on the same exact-source snapshot; preserve exact source/artifact identity and negative results.
3. Attach a real admitted ~0.8B model/J-Lens observer to produce the first `MEASURED_INTERPRETABILITY` vector plus matched baseline/lesion/control traces through `JSPACE_GWT_TRANSITION_TRACE/v1`.
4. Measure reconstruction error, basis/role/generation rejection, GWT selector behavior and matched-budget causal sensitivity; do not treat model self-report as J-Space measurement.
5. Only after real trace quality and causal gates survive, freeze `JSPACE_VECTOR_CONTROL_ABI/v1`, compile episode-separated train/validation/holdout data, freeze the exact base-model baseline, and perform Together capability/price preflight.
6. Create the owner-authorized one-shot Together job only if all preconditions are satisfied; job creation, not preflight, consumes the authorization.
