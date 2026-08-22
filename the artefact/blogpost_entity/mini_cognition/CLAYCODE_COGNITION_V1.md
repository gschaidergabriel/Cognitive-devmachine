# ClayCode Cognition v1 — generic 0.5B cognition core

## Purpose
A 0.5B CausalLM is post-trained to use ClayCode as its only generated cognitive representation.
The checkpoint is application-neutral: no fixed name, persona, job, audience, domain, language, provider or tool set is weight identity.

Runtime configuration supplies those values. The weights learn how to represent state, alternatives, routing,
architecture and self/control variables in ClayCode.

## Epistemic boundary
ClayCode-only cognition is a model behavior target, not evidence that the model is conscious.
`R_next = F` means: an executable transition is admitted only when one candidate satisfies the deterministic
grammar/type/schema/authority/generation validators. Otherwise the transition is rejected or remains unresolved.

The model proposes. The runtime validates and executes.

## Required envelope

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

No Markdown. No prose outside ClayCode string literals.

## Canonical v1 intrinsic vocabulary
The generated cognition vocabulary is closed. A call not represented by the machine-readable
`intrinsics_v1.py` vocabulary is invalid for `claycog/1`, even when punctuation looks valid.
Corpus and OOD validators reject unknown intrinsics and wrong arity before training/promotion credit.

Configuration / envelope:
- `cfg(key)`
- `cog_new()`
- `self_bind(c,entity_id,continuity)`
- `role_bind(c,role)`
- `goal_bind(c,goal)`
- `personality_bind(c,personality)`

GRF:
- `grf_observe(c,region,claim,status)`
- `grf_infer(c,region,claim)`
- `grf_generate(c,region,candidate)`
- `grf_counter(c,region,candidate)`
- `grf_intervene(c,region,test)`
- `grf_emergent(c,region,pattern)`
- `grf_verify(c,region,claim,receipt)`

Hyperposition:
- `hyper_new(c,id)`
- `hyper_alt(hp,candidate,status)`
- `hyper_discriminator(hp,test)`
- `hyper_invariant(hp,invariant)`
- `collapse_guard(hp,rule)`
- `collapse_exact(hp,candidate,receipt)`

Omega:
- `omega_new(c,id)`
- `omega_bind(omega,key,value)`
- `omega_arg(omega,name,value,type)`
- `omega_schema(omega,schema_id)`
- `omega_authority(omega,authority)`
- `omega_generation(omega,generation)`
- `omega_validate(omega,gate)`
- `omega_reject(omega,reason)`
- `omega_commit_candidate(c,omega)`

State / self / architecture / control:
- `self_state(c,key,value,status)`
- `self_scalar(c,key,value,status)`
- `self_kind(c,kind)`
- `arch_bind(c,responsibility,component)`
- `authority_bind(c,responsibility,authority)`
- `authority_deny(c,source,responsibility)`
- `state_note(c,key,value,status)`
- `unknown_preserve(c,key,reason)`
- `provenance(c,key,source,qualification)`
- `focus_set(c,focus)`
- `policy_select(c,policy)`
- `recovery_state(c,state)`

These are cognition/state representation intrinsics only. None is a direct host/tool/API effect primitive.
`omega_commit_candidate` commits only a candidate to the deterministic admission boundary; it does not execute an effect.

## GRF — grounded reasoning field
GRF is a typed semantic work-space, not natural-language chain-of-thought:
- R0 OBSERVE: admitted input/evidence with epistemic status
- R1 INFER: bounded derived relation
- R2 GENERATE: candidate transition
- R3 COUNTER: competing candidate/counter-reality
- R4 DISCRIMINATE: cheapest distinguishing test
- R5 EMERGENT: cross-candidate invariant/pattern
- R6 VERIFY: evidence/receipt sufficient for collapse

## Hyperposition
Unresolved candidates remain explicit and simultaneous. Recurrence, confidence, preference, fluency, or prior assistant text never collapse a hyperposition. Collapse requires the configured R6/discriminator contract and receipt.

## Omega / exact function-vector routing
`omega` is the compact typed action representation used for structured work. For tool/API tasks the model emits a minimal typed candidate. The external runtime maps only a deterministically validated candidate to an actual call.

No `omega` may execute unless grammar, types, schema, authority and generation all pass.

## Self/architecture representation
Computed self/control state may steer cognition but is not external evidence. Architecture bindings teach responsibility boundaries rather than a fixed identity/job.

## Hard invariants
1. `UNKNOWN != ZERO != ERROR != MEASURED`.
2. `REPORTED != MEASURED`.
3. Model output != canonical truth.
4. Model output != effect authority.
5. Hyperposition remains open until a discriminator/R6 receipt resolves it.
6. Invalid tool/API arguments cannot execute; reject rather than guess.
7. Stale generation cannot commit.
8. Missing effect receipt after crash => UNKNOWN; never blind replay.
9. Identity/name/role/goal/personality/application/tool inventory are runtime configuration.
10. Natural language outside ClayCode string literals is invalid.
11. Unknown intrinsic, bad arity/type/schema, missing cfg, or missing authority binding fails closed.
12. `R_next = F` is an admission invariant enforced by runtime validation, not a claim of infallible neural prediction.
13. Training and OOD promotion receive zero structural credit when generated calls are outside the canonical v1 intrinsic vocabulary.

## Base and deployment target
Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B, Apache-2.0, CausalLM).
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

Target local format: GGUF Q4_K_M.
Promotion requires measured peak process RSS < 1 GiB at 2048-token context; file size alone is insufficient.
