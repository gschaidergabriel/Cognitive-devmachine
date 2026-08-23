# MINI_COGNITIVE_ROUTE_CAPABILITY/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Purpose: resolve the previously explicit engine/J-Space semantic gap in the canonical pre-inference Cognitive Fabric path without introducing a second router, state authority, effect path or provider-name heuristic.

## Placement

The capability is embedded as `cognitive_route_capability` inside the already versioned, generation-admitted `JSPACE_PROFILE` cognition object in MiniUnifiedDB.

This placement is deliberate:

- the boot binding already carries the exact `jspace_profile_digest`;
- `mini_cognition_object_admissions` already generation-fences that exact object;
- the object payload is already digest-bound and read-integrity checked;
- no new durable table or second configuration authority is needed;
- changing route capability bytes therefore changes the admitted J-Space profile payload identity/receipt rather than silently changing routing under a stable authority name.

The active DB profile still supplies the replaceable inference configuration. The route capability does **not** replace it. It states which engine class and J-Space mode that exact inference configuration is allowed to use.

## Exact payload

```text
JSPACE_PROFILE payload {
    ... other versioned J-Space material ...
    cognitive_route_capability: {
        schema: "MINI_COGNITIVE_ROUTE_CAPABILITY/v1"
        target_engine_class: CLAUDE_CODE | BUNDLED_LOCAL_08B | ADAPTIVE_BACKEND
        jspace_mode: FULL_LOCAL_LATENT | LOCAL_OBSERVE_ONLY | COMPILED_EXTERNAL | PLAIN_COMPATIBILITY
        inference_config_digest: sha256(canonical active profile inference object)
        allowed_inference_kinds: [nonempty exact profile inference.kind values]
        candidate_only: true
        direct_state_authority: false
        direct_effect_authority: false
    }
}
```

The exact field set is closed in v1. Extra capability fields fail closed instead of acquiring accidental semantics.

## Route constraints

`CLAUDE_CODE` requires `COMPILED_EXTERNAL`.

`BUNDLED_LOCAL_08B` requires `FULL_LOCAL_LATENT` or `LOCAL_OBSERVE_ONLY`.

`ADAPTIVE_BACKEND` may use any packet-v2-admitted J-Space mode, but the exact downstream inference configuration must still match `inference_config_digest` and its `kind` must appear in `allowed_inference_kinds`.

`NO_MODEL_REQUIRED` is not an executable route capability. Existing ZERO abstention remains a separate fail-closed path and must not be passed to `inference_generate` as successful admission.

## Anti-guessing law

The runtime MUST NOT infer any of the following from provider name, model name, endpoint URL, adapter label or user text:

- hidden-state access;
- local activation access;
- J-Space mode;
- engine class;
- model capability;
- truth confidence;
- effect authority.

If the exact generation-admitted JSPACE_PROFILE lacks this capability, has a stale/mutated payload, has an ambiguous object version, or does not bind the exact active inference configuration, pre-inference admission fails closed.

## Canonical pre-inference sequence

```text
bounded MINI_COGNITIVE_INVOCATION/v1
-> live generation check
-> read-only active-turn resolution
-> reconstructed turn + boot binding verification
-> exact generation-admitted JSPACE_PROFILE lookup
-> MINI_COGNITIVE_ROUTE_CAPABILITY/v1 validation
-> exact active profile inference digest match
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> exact downstream context validation
-> MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION/v1
-> inference_generate
```

The admission receipt binds the turn, boot binding, active-turn activation, active profile hash, canonical-state hash, source packet hash, workspace capsule digest, packet-v2 digest, route-capability digest and admitted JSPACE_PROFILE object receipt.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`Active profile inference = replaceable runtime inference configuration`

`JSPACE_PROFILE route capability = generation-bound permission/capability description only`

`ZERO/J-Space/GWT/model output = candidate or measurement only`

`EffectGate = only real-effect authority`

The capability cannot write canonical state, execute effects, promote model output to truth or mutate the bound causal turn.

## Falsifiers

At minimum the v1 admission compiler must reject:

- caller selector with extra workspace/model/J-Space fields;
- selector that disagrees with the current active bound turn;
- stale generation;
- mutated JSPACE_PROFILE payload retaining an old payload digest;
- multiple admitted JSPACE_PROFILE object versions for one exact digest/generation;
- missing capability;
- capability field drift;
- unsupported engine/J-Space pair;
- inference kind outside the allowlist;
- exact inference config digest mismatch;
- capability requesting direct state/effect authority;
- ABSTAIN route presented as executable inference.

## Implementation candidate

`tools/mini_cognitive_admission_v1.py` implements this source-level compiler and composes the existing:

- `miniunifieddb_active_turn_v1.resolve_active_prepare`;
- MiniUnifiedDB cognition object/admission tables;
- `ZERO_WORKSPACE_CAPSULE/v1` compiler;
- `ZERO_INFERENCE_PACKET/v2` compiler.

`tests/test_mini_cognitive_admission_v1.py` supplies deterministic happy-path and poison regressions.

## Acceptance boundary

This contract and compiler execute no model and no external effect. A source/unit PASS is **not** reference-runtime, bundled-0.8B, J-Space, Whole-GWT, Claude, HCU or whole Mini Entity runtime acceptance.

The next integration gate is to make `ProfilePipelineRuntime._pipeline_init` install the cognition + active-turn schemas atomically with foreign keys enabled, then wire exactly one `pipeline_cognitive_fabric_admit` handler to this compiler and a post-terminal finalizer that never creates a second commit/effect path. Exact runtime credit still requires actually-started authorized isolated execution on exact bytes.