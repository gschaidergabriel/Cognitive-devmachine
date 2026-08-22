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

## GRF — grounded reasoning field
GRF is a typed semantic work-space, not natural-language chain-of-thought:
- R0 OBSERVE: admitted input/evidence with epistemic status
- R1 INFER: bounded derived relation
- R2 GENERATE: candidate transition
- R3 COUNTER: competing candidate/counter-reality
- R4 DISCRIMINATE: cheapest distinguishing test
- R5 EMERGENT: cross-candidate invariant/pattern
- R6 VERIFY: evidence/receipt sufficient for collapse

Intrinsics:
- grf_observe(c,region,claim,status)
- grf_infer(c,region,claim)
- grf_generate(c,region,candidate)
- grf_counter(c,region,candidate)
- grf_intervene(c,region,test)
- grf_emergent(c,region,pattern)
- grf_verify(c,region,claim,receipt)

## Hyperposition
Unresolved candidates remain explicit and simultaneous:
- hyper_new(c,id)
- hyper_alt(hp,candidate,status)
- hyper_discriminator(hp,test)
- hyper_invariant(hp,invariant)
- collapse_guard(hp,rule)
- collapse_exact(hp,candidate,receipt)

Recurrence, confidence, preference, fluency, or prior assistant text never collapse a hyperposition.

## Omega / exact function-vector routing
`omega` is the compact typed action representation used for structured work.

- omega_new(c,id)
- omega_bind(ω,"operation",cfg_or_literal)
- omega_arg(ω,name,value,type)
- omega_schema(ω,schema_id)
- omega_authority(ω,authority)
- omega_generation(ω,generation)
- omega_validate(ω,"grammar|types|schema|authority|generation")
- omega_reject(ω,reason)
- omega_commit_candidate(c,ω)

For tool/API tasks the model does not write persuasive prose about an action. It emits a minimal `omega` candidate.
The external runtime maps a validated omega to the actual tool/API call.

No `omega` may execute unless all deterministic validators pass.

## Self/architecture representation
The model may encode computed inner/control state:
- self_state(c,key,value,"COMPUTED")
- self_scalar(c,key,value,"COMPUTED")
- arch_bind(c,responsibility,component)
- authority_bind(c,responsibility,authority)
- authority_deny(c,source,responsibility)

Computed self-state may steer cognition but is not external evidence.

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

## Base and deployment target
Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B, Apache-2.0, CausalLM).
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.

Target local format: GGUF Q4_K_M.
Promotion requires measured peak process RSS < 1 GiB at 2048-token context; file size alone is insufficient.
