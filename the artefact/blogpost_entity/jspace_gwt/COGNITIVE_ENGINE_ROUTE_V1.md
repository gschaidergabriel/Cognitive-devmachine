# COGNITIVE_ENGINE_ROUTE/v1

Status: **SOURCE CONTRACT CANDIDATE / RUNTIME UNVERIFIED**

Purpose: close the authority gap between an already-resolved MiniUnifiedDB cognition turn and `ZERO_INFERENCE_PACKET/v2` without guessing engine capability or J-Space semantics from provider/model names.

## Observed gap

The current retained Python reference runtime still has no executable `pipeline_cognitive_fabric_admit` handler. The merged same-MiniUnifiedDB active-turn resolver can provide the exact generation, causal turn, boot/turn digests, workspace, Zero/GRF/Hyperposition, bundled manifest, local model, tokenizer, J-Space profile, Jacobian lens and workspace-calibration identities needed to compile `ZERO_WORKSPACE_CAPSULE/v1`.

`ZERO_INFERENCE_PACKET/v2` additionally requires an explicit `target_engine_class` and `jspace_mode`. Those values must not be inferred from mutable provider/model strings.

## Minimal route contract

The already DB-resident runtime profile may carry one explicit nested route object under `profile.inference.cognitive_engine_route`:

```text
MINI_COGNITIVE_ENGINE_ROUTE_CONFIG/v1 {
    target_engine_class
    jspace_mode
    bundled_manifest_digest
    local_model_digest
    tokenizer_digest
    jspace_profile_digest
    jacobian_lens_digest
    workspace_calibration_digest
}
```

The route object has **configuration authority only through the existing MiniUnifiedDB profile authority**. It creates no second store and grants no truth/effect authority.

`tools/cognitive_engine_route_v1.py::resolve_engine_route(...)` accepts the route only when:

1. the cognition prepare binding is already valid for the exact expected generation;
2. the active DB profile carries an exact runtime profile snapshot/hash;
3. every cognition digest in the route exactly equals the already-resolved MiniUnifiedDB cognition ancestry;
4. the target engine class and J-Space mode are an admitted pair;
5. the resulting route digest binds generation, causal turn, turn/boot/workspace identity, exact profile hash, exact inference configuration and cognition digests.

Provider/model names alone never authorize latent access.

## Current mode constraints

- `CLAUDE_CODE` requires `COMPILED_EXTERNAL`.
- `BUNDLED_LOCAL_08B` requires `FULL_LOCAL_LATENT` or `LOCAL_OBSERVE_ONLY`.
- `ADAPTIVE_BACKEND` may use an admitted packet-v2 J-Space mode, but still requires explicit route configuration and exact cognition ancestry binding.

These constraints mirror the current owner architecture and `ZERO_INFERENCE_PACKET/v2`; they do not prove that a runtime actually exposes the claimed capability. Exact runtime/calibration evidence remains a separate acceptance gate.

## Fail-closed cases

At minimum:

- missing explicit route object;
- malformed/extra route fields;
- stale generation;
- missing profile snapshot/hash;
- profile-id mismatch;
- placeholder/malformed cognition digest;
- any route digest differing from the resolved MiniUnifiedDB cognition binding;
- Claude claiming local latent access;
- bundled 0.8B claiming compiled-external mode;
- unsupported engine class or J-Space mode.

## Causal position

```text
MiniUnifiedDB active bound turn
-> resolve_prepare_binding
-> COGNITIVE_ENGINE_ROUTE/v1
-> ZERO_WORKSPACE_CAPSULE/v1
-> ZERO_INFERENCE_PACKET/v2
-> pre-inference Cognitive Fabric admission receipt
-> inference
-> deterministic gate
-> MiniUnifiedDB terminal commit/no-commit
-> post-terminal UCF runtime finalization
```

The route resolver is deliberately **before** the missing runtime handler. The real `pipeline_cognitive_fabric_admit` implementation should compose this resolver with the existing capsule/packet/UCF chain rather than inventing a second routing table or deriving J-Space capability from backend names.

## Authority

`MiniUnifiedDB = canonical durable state/evidence/configuration authority`

`DB-resident profile route = bounded routing configuration only`

`Zero/J-Space/GWT/model/Claude = candidate or measurement only`

`EffectGate = only real-effect authority`

## Acceptance boundary

This branch is source/architecture work only. The current connected Vercel surface exposes no Sandbox start/exec capability, so no actually-started authorized exact-source execution is claimed. No runtime/model/bundled-0.8B/J-Space/GWT/Claude/HCU/whole-product credit is minted from source presence or unexecuted tests.
