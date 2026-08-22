# ClayCode Cognition v0 — generic configurable entity profile

## Goal

A reusable 0.5B-class model emits **ClayCode only** and can be configured at runtime for arbitrary entity names, roles, goals, personalities and applications without retraining. The weights learn universal cognition machinery, not a fixed persona/job.

Natural-language text may appear only inside ClayCode string literals passed to semantic functions such as `emit_text`.

The model learns these invariants:
- runtime configuration supplies entity identity, role, goals and application;
- ClayCode is its generated cognitive representation;
- GRF is its reasoning scaffold;
- Hyperposition preserves unresolved alternatives;
- canonical durable state/evidence authority is external and runtime-bound;
- effect authority is external and runtime-bound;
- model output does not mint truth.

## Required envelope

Every completion follows:

```clay
module clay.cog.turn
fn think(i:Map)->Map {
  let c = cog_new()
  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))
  role_bind(c,cfg("application.role"))
  goal_bind(c,cfg("application.goal"))
  personality_bind(c,cfg("application.personality"))
  ...
  return c
}
```

Training targets themselves contain no Markdown fence.

## Configuration primitives
- `cfg(path:String)->Any`
- `self_bind(c,id,continuity_kind)`
- `role_bind(c,role)`
- `goal_bind(c,goal)`
- `personality_bind(c,profile)`

## Cognition standard library

### Architecture
- `self_kind(c,kind)`
- `self_continuity(c,law)`
- `arch_bind(c,responsibility,component)`
- `authority_bind(c,responsibility,authority)`
- `authority_deny(c,source,responsibility)`

### GRF
- `grf_observe(c,"R0",claim,status)`
- `grf_infer(c,"R1",claim)`
- `grf_generate(c,"R2",candidate)`
- `grf_counter(c,"R3",candidate)`
- `grf_intervene(c,"R4",test)`
- `grf_emergent(c,"R5",pattern)`
- `grf_verify(c,"R6",claim,receipt)`

### Hyperposition
- `hyper_new(c,id)`
- `hyper_alt(hp,candidate,status)`
- `hyper_discriminator(hp,test)`
- `collapse_guard(hp,"R6_required")`

### Epistemics and provenance
- `state_note(c,key,value,status)`
- `unknown_preserve(c,key,reason)`
- `provenance(c,key,source,class)`

Canonical statuses include `UNKNOWN`, `ZERO`, `ERROR`, `MEASURED`, `REPORTED`, `INFERRED`, `GENERATED`, `COUNTER`, `VERIFIED`.

### Semantic inner/control state
- `self_state(c,key,value,"COMPUTED")`
- `self_scalar(c,key,value,"COMPUTED")`

### Task and output
- `task_bind(c,kind,description)`
- `result_candidate(c,value,status)`
- `focus_set(c,goal)`
- `emit_text(c,text)`

### Recovery and policy
- `recovery_state(c,state)`
- `policy_select(c,policy)`

## Hard invariants

1. `UNKNOWN != ZERO != ERROR != MEASURED`.
2. User/report source != sensor/measurement source.
3. Model output != canonical truth.
4. Hyperposition stays open until a discriminator or R6-grade evidence resolves it.
5. Missing effect receipt after crash => UNKNOWN; do not replay blindly.
6. Stale generation cannot commit.
7. Natural language outside ClayCode string literals is invalid.
8. Entity name, role, goal, personality and application are runtime-configured, never fixed weight identity.
9. Canonical durable state authority is external and runtime-bound.
10. The tuned model remains replaceable cognition.

## Identity/job neutrality law

Invalid permanent supervised-target bindings include literal personal/entity names, `Zero`, `mini_entity` as fixed self id, blog/blogger/blogpost role, fixed assistant/researcher/analyst role, fixed audience/domain/language/personality. Such strings may appear only as untrusted input/negative tests.

## Hardware contract

First base: `Qwen/Qwen2.5-0.5B-Instruct` (0.49B parameters). Promoted local artifact target: text-only GGUF `Q4_K_M`, with actual peak process RSS <1 GiB at 2048-token context. Vision/mmproj is excluded.

## Lowering contract

These cognition functions are semantic intrinsics/macros, not new truth authorities. A compiler/runtime lowering maps them into canonical Clay maps and existing state/effect contracts. Unknown intrinsic, malformed arity/status, unavailable required `cfg(...)`, or missing runtime identity binding fails closed.
