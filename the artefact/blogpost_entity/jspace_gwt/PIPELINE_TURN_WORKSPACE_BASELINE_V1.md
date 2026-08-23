# MINI_ENTITY_PIPELINE_TASK/v1 + MINI_ENTITY_TEXT_WORKSPACE/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Scope: deterministic source-side material preparation immediately before the canonical Mini Entity Cognitive Fabric admission path.

## Problem closed by this contract

The retained three-argument pipeline runtime has exact DB-resident profile state, live generation, compiled canonical-state/packet hashes and admitted evidence references, but the Cognitive Fabric prepare/admit contract also needs an exact task binding and an admitted workspace identity before inference. Those values must not be invented from wall clock, randomness, output ids, model output, prompt prose or guessed J-Space/GWT measurements.

`MINI_ENTITY_CAUSAL_TURN_ID/v1` (PR #1267) deliberately starts only after complete task/workspace/boot/provenance material already exists. This contract supplies the missing deterministic baseline task/workspace material without creating a second state or cognition authority.

## Deterministic task operation

`MINI_ENTITY_PIPELINE_TASK/v1` is a canonical JSON operation text over:

- exact live `entity_generation`;
- active DB-resident `profile_id`;
- exact active-profile stored-byte hash;
- exact `canonical_state_hash`;
- exact source `packet_hash`;
- a fixed no-truth/no-effect authority statement.

It means only: process this exact active-profile packet at this exact generation. It is not model-authored prompt prose and does not claim semantic truth.

A change in profile bytes, generation, canonical state or source packet changes the task hash.

## Text-only baseline workspace

`MINI_ENTITY_TEXT_WORKSPACE/v1` is the lowest-complexity admitted workspace baseline. It selects a bounded deterministic prefix from the already-admitted `compiled.allowed_evidence_refs` after lexical canonicalization.

The workspace digest binds:

- generation;
- exact pipeline-task hash;
- canonical-state hash;
- source packet hash;
- selected workspace slots;
- explicit contradiction state `UNKNOWN`;
- provenance refs for exact task/state/packet and selected evidence refs;
- required Zero mode `TEXT_ONLY_BASELINE`;
- measurement state `jspace=UNMEASURED`, `gwt=TEXT_ONLY_BASELINE`;
- candidate-only/no-direct-state/no-direct-truth/no-direct-effect authority.

No missing latent/GWT value is guessed. This baseline is intentionally simpler than a measured J-Space/GWT workspace and remains a valid comparison/fallback mechanism until measured fabric evidence exists.

## Same-store composition

`tools/mini_pipeline_turn_workspace_v1.py` creates no table and no durable authority. When binding is requested it:

1. resolves exactly one live-generation boot binding from the existing MiniUnifiedDB cognition tables;
2. asks the existing cognition-store boot validator to reconstruct/validate that binding;
3. delegates causal-turn identity/persistence to `MINI_ENTITY_CAUSAL_TURN_ID/v1` / `miniunifieddb_cognition_store_v1.bind_turn()`;
4. leaves later `ZERO_WORKSPACE_CAPSULE/v1 -> ZERO_INFERENCE_PACKET/v2` compilation and final UCF receipt semantics unchanged.

MiniUnifiedDB remains the only durable cognition/state authority. EffectGate remains the only real-effect authority.

## Fail-closed rules

Preparation fails before inference on malformed/placeholder hashes, boolean/invalid generations, profile-snapshot identity mismatch, duplicate evidence refs, invalid slot budgets, missing/ambiguous boot binding, or downstream causal-turn/store rejection.

The baseline must not be promoted to measured J-Space/GWT merely because it is deterministic or useful.

## Intended canonical integration

```text
pipeline_state_read
-> pipeline_collect
-> pipeline_compile
-> deterministic MINI_ENTITY_PIPELINE_TASK/v1
-> deterministic MINI_ENTITY_TEXT_WORKSPACE/v1
-> resolve exact live boot binding
-> MINI_ENTITY_CAUSAL_TURN_ID/v1 + same-MiniUnifiedDB turn bind
-> pipeline_build_prompt
-> pipeline_cognitive_fabric_admit
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2 exact downstream-context bind
-> inference_generate
-> deterministic gate
-> MiniUnifiedDB CAS commit / explicit no-commit
-> pipeline_cognitive_fabric_finalize
```

The exact source may fuse preparation into the admission handler later, but it must preserve the authority/temporal ordering above.

## Acceptance boundary

Current source/component checks can establish only deterministic mechanism behavior. Runtime credit requires the later retained-runtime handler to invoke this material on exact integrated bytes and then pass authorized isolated execution with stale generation, replay, malformed identity, packet-context and terminal-finalization regressions.

No bundled-0.8B, J-Space, Whole-GWT, Claude-adapter, HCU-capacity or whole Mini Entity runtime credit follows from this contract.
