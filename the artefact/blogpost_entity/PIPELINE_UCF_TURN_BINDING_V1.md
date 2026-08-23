# Mini Entity Pipeline ↔ Unified Cognitive Fabric Turn Binding v1

Status: **SOURCE CONTRACT / RUNTIME UNVERIFIED**  
Program: `MINI_ENTITY_PIPELINE_ALL_IN_ONE`  
Stage: `MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT`

## Purpose

The canonical `UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1` proves only that one bounded cognitive-fabric receipt is internally admissible. It does **not by itself** prove that the receipt belongs to the same MiniUnifiedDB turn that built the prompt, selected the engine, gated the candidate and committed state.

This contract closes that causal-identity gap without creating a second truth, state, effect, J-Space or receipt authority.

Canonical causal path target:

```text
MiniUnifiedDB generation/profile snapshot
  -> pipeline_compile canonical_state_hash + packet_hash
  -> immutable MINI_ENTITY_INFERENCE_PACKET/v1
  -> Unified Cognitive Fabric execution context
  -> inference_generate -> candidate result digest
  -> deterministic pipeline_gate
  -> atomic MiniUnifiedDB generation CAS / pipeline_commit
  -> final UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1
  -> post-turn MINI_ENTITY_PIPELINE_UCF_TURN_BINDING/v1 validation/persistence
```

The final UCF runtime receipt contains outcome fields such as `canonical_write_committed`.
Therefore the final receipt and this turn-binding validator are **post-turn evidence**, not a
pre-commit authority. The pre-inference causal anchor is the immutable inference-packet digest;
the deterministic gate and MiniUnifiedDB CAS remain the only commit authorities.

## Non-duplication law

`validate_pipeline_ucf_turn_binding_v1.py` MUST delegate UCF semantics to the existing canonical `tools/validate_unified_cognitive_fabric_receipt_v1.py` validator.

It may cross-bind identities. It may **not** create another J-Space/GWT truth/admission authority.

## Required cross-bindings

One admitted turn must bind:

- exact clean source commit;
- `state_authority == MiniUnifiedDB`;
- `generation_before`;
- exact DB-resident profile snapshot digest;
- `canonical_state_hash`;
- event `packet_hash`;
- exact boot-binding receipt digest;
- engine-selection digest;
- canonical digest of `MINI_ENTITY_INFERENCE_PACKET/v1`;
- the same inference-packet digest inside the existing UCF receipt;
- the same UCF runtime generation;
- the same candidate result digest at the deterministic gate;
- the same UCF receipt digest at gate and commit;
- on `ACCEPT`, exactly one MiniUnifiedDB generation advance and the same packet/canonical/UCF identities in the atomic commit.

## Rejection law

A rejected or blocked candidate must not increment generation or leave commit identity fields populated. A UCF receipt that says canonical write happened while the pipeline gate says `REJECT`/`BLOCKED`, or vice versa, is invalid.

## Epistemic and authority law

- `UCF_RECEIPT_VALID != PIPELINE_TURN_BOUND` until this cross-binding passes.
- `JSPACE_MEASURED != FACTUAL_TRUTH`.
- model output remains candidate-only.
- MiniUnifiedDB remains the only durable state/evidence/configuration authority.
- inference engines and the UCF receipt do not gain direct effect authority.
- a valid turn-binding receipt is evidence about causal identity, not proof of model quality or consciousness.

## Current source observation at creation

Current `main@efec8ecff35c28cea6f7445a87aa65ddcc339cab` still has `BLOGPOST_ENTITY.clay` routing directly from `pipeline_build_prompt` to `inference_generate`, and the Python reference runtime still exposes the legacy effect surface. Therefore this contract is intentionally **ahead of runtime implementation** and mints zero runtime credit.

The next implementation gate is to route the immutable inference packet through the canonical Unified Cognitive Fabric before `inference_generate`, carry its digest unchanged through gate/CAS, and emit the final UCF receipt plus this post-turn binding after the commit outcome is known. The existing deterministic gate, MiniUnifiedDB generation CAS, and profile/generation/snapshot/hash authority guards remain unchanged.
