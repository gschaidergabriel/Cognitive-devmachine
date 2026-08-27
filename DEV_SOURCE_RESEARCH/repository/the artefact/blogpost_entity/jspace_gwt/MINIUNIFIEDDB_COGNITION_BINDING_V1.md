# MiniUnifiedDB Cognition Binding v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

This contract closes the authority gap between the canonical Mini Entity pipeline and the existing `ZERO_WORKSPACE_CAPSULE/v1 -> ZERO_INFERENCE_PACKET/v1 -> Unified Cognitive Fabric` chain.

## Problem

`pipeline_cognitive_fabric_prepare` cannot safely obtain ZERO, GRF, Hyperposition, bundled-model, tokenizer, J-Space/lens, workspace-calibration, boot-source-lock, or policy identities from mutable profile fields, placeholders, chat memory, or sidecar files. Those identities affect whether cognition is admitted and therefore must come from the same canonical durable MiniUnifiedDB authority as the live entity generation.

A final UCF runtime receipt cannot be minted before inference or before the deterministic gate/commit outcome because it contains execution/result/epistemic/authority fields including the terminal canonical-write/effect state. The causal shape is therefore:

`build_prompt -> cognitive_fabric_prepare/admit -> inference_generate -> gate -> commit-or-explicit-no-commit -> cognitive_fabric_finalize_runtime_receipt -> post_turn_causal_binding`

The pre-inference admission receipt and final `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` are distinct identities and MUST NOT share one schema/digest identity.

## One-store law

`tools/miniunifieddb_cognition_store_v1.py` adds three bounded table families **inside the existing MiniUnifiedDB SQLite database**:

1. immutable cognition-object identities and metadata;
2. explicit generation-bound object admissions plus one boot binding per entity generation;
3. exact causal-turn bindings for task/workspace/provenance identity.

It is not a second database, memory authority, effect path, truth ledger, or model authority.

## Admission rules

- every cognition object has a version, SHA-256 identity, digest basis, metadata payload, payload digest and provenance refs;
- `CANONICAL_JSON` objects must hash exactly to the registered canonical JSON payload;
- `EXTERNAL_BYTES` identities are never inferred from metadata; admission requires a separate exact admission-receipt digest;
- an object may be used in a boot binding only after explicit admission at the current or earlier generation;
- a new boot binding is allowed only at the exact live `entity_state.generation`;
- exactly one boot binding may exist for a generation; a conflicting replacement fails closed;
- every causal turn binds the live generation, boot binding, task hash, workspace digest, selected workspace slots, contradiction state, provenance and required Zero mode;
- reusing a turn id with different material fails closed;
- resolving a turn with a stale generation or different task text fails closed.

## Required boot identities

The v1 boot binding requires admitted identities for:

- ZERO identity;
- GRF;
- Hyperposition;
- bundled manifest;
- local model checkpoint;
- tokenizer;
- J-Space profile;
- Jacobian/lens profile;
- workspace calibration;
- boot source lock;
- policy authority.

This is deliberately strict. The current intentionally `UNBOUND` boot/model state therefore remains unavailable rather than being replaced by placeholder digests.

## Runtime integration target

`pipeline_cognitive_fabric_prepare` should call the same-store resolver using the exact live generation, causal turn id and task text. Only a successful exact binding may feed the existing ZERO workspace capsule and inference-packet compilers. Missing/stale/conflicting bindings must `BLOCK` or typed-`ABSTAIN` before model execution.

After candidate inference, the existing deterministic gate/CAS path decides commit or explicit no-commit. Only then may `pipeline_cognitive_fabric_finalize_runtime_receipt` emit the canonical final `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1`, reusing the same turn/boot/packet ancestry and binding the observed terminal outcome. Post-turn causal binding follows that final receipt. Finalization itself does not become a second truth/effect authority.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`Cognition binding = identity/provenance admission only`

`Model/J-Space/GWT output = candidate/measurement only`

`EffectGate = only real-effect authority`

No source-level success from this contract grants bundled-0.8B, J-Space, GWT, Claude-adapter, HCU, or whole-product runtime credit.
