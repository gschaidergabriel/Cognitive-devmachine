# Hyperposition Computational Unit (HCU)

Status: **ENTITYOS/HCU RETAINED DONOR LANE — SOURCE CANDIDATE, ZERO RUNTIME CREDIT**

HCU is the sole current integrated cognition/compute architecture being co-developed inside EntityOS. The `MicroEntity` directory name is compatibility/provenance only; it is not a second product or persistent entity.

## Current path

The current source candidate is deliberately split into deterministic authority/evidence stages:

`Typed Entry -> typed Entry binding -> HCU route -> verified EngineAdmission -> engine-load lease -> actual loader-read consumption -> VerifiedEngineLoad -> inference receipt v2 -> GRID10 plan`

All current causal identities target `RFC8785_JCS_IJSON/v1`. Historical CBOR, custom typed-canonical, host-Python JSON and v1 inference identities retain only their original bounded scope and must not be silently relabelled as current JCS identities.

Pre-load hashing is necessary but is **not** loader attestation. The current v2 inference path consumes `HCU_VERIFIED_ENGINE_LOAD/v1`, which binds a generation-fenced engine-load lease to evidence reported from the actual loader read path. Matching caller-supplied hashes alone grant zero runtime credit.

## Current source files

- `entry_canonicalization_v1.py` — selected RFC8785/JCS implementation.
- `xeno_entry_fabric_v1.py` — compatibility-named Typed Entry Fabric; current event/admission identity is v2.
- `reactive_event_router_v1.py` — deterministic script-first HCU router using typed Entry-binding v2.
- `engine_admission_v1.py` — exact local engine artifact verification and versioned EngineAdmission receipt.
- `engine_load_lease_v1.py` — generation-fenced load intent plus actual-loader consumption verification.
- `inference_receipt_v2.py` — current JCS downstream inference receipt candidate consuming `VerifiedEngineLoad`.
- `grid10_scheduler_v1.py` — logical GRID10 planning; logical cells are not physical decoders or model calls.
- matching `test_*.py` files — deterministic regression obligations only until executed on an admitted isolated executor.
- `HCU_DATA_INDEX.json` — current package/path selection.
- `receipts/` — bounded non-secret evidence receipts.

`inference_receipt_v1.py`, `physical_engine_lease_v1.py`, custom typed-canonical source and other earlier paths are retained only as historical/noncurrent evidence unless current authority explicitly re-admits them. They must not become a second active inference, canonicalization or loader-authority lane.

## Authority

Canonical durable state/evidence remains deterministic EntityOS authority. HCU vectors, world-model fields, simulations, J-Space/workspace outputs and model outputs remain candidate/projection/measurement evidence. EffectGate/EffectJournal remain the only real-effect authority. Entry data may request routing but may not mint engine identity, capabilities, truth or effects.

## Evidence boundary

Current work is **source/mechanism convergence only**. No exact-current combined Entry -> route -> real loader -> VerifiedEngineLoad -> inference-v2 -> GRID10 execution has been observed on an actually-started authorized isolated executor. No real local ~0.8B model runtime, target-hardware capacity, J-Space causality, VPS, OCI or whole EntityOS/HCU PASS is claimed.

The next executable gate is to bind the real admitted checkpoint/tokenizer/runtime/build bytes to the actual loader-read path, run the combined current chain on the single authorized exact-source isolated executor, and preserve source SHA, environment, commands, exits, logs and resulting receipt identities.
