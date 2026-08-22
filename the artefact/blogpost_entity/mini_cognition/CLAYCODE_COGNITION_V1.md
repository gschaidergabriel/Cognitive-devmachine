# ClayCode Cognition v1 — generic 0.5B cognition core

## Purpose
A 0.5B CausalLM is post-trained to use ClayCode as its only generated cognitive representation.
The checkpoint is application-neutral: no fixed name, persona, job, audience, domain, language, provider or tool set is weight identity.

Runtime configuration supplies those values. The weights learn how to represent state, alternatives, routing,
architecture and self/control variables in ClayCode.

## Epistemic boundary
ClayCode-only cognition is a model behavior target, not evidence that the model is conscious.
`R_next = F` means: an executable transition is admitted only when one candidate satisfies deterministic
grammar/type/schema/authority/generation validation. Otherwise the transition is rejected or remains unresolved.
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
The generated cognition language is closed. `intrinsics_v1.py` is the machine-readable structural vocabulary and arity map used by the canonical validator. SFT v2, historical SFT v1 and OOD scoring must use the same `validate_sft_v1.validate_code` admission function; a corpus-specific validator may add diversity/leakage checks but must not define a competing ClayCode grammar.

Configuration / envelope: `cfg`, `cog_new`, `self_bind`, `role_bind`, `goal_bind`, `personality_bind`.

GRF: `grf_observe`, `grf_infer`, `grf_generate`, `grf_counter`, `grf_intervene`, `grf_emergent`, `grf_verify`.

Hyperposition: `hyper_new`, `hyper_alt`, `hyper_discriminator`, `hyper_invariant`, `collapse_guard`, `collapse_exact`.

Omega: `omega_new`, `omega_bind`, `omega_arg`, `omega_schema`, `omega_authority`, `omega_generation`, `omega_validate`, `omega_reject`, `omega_commit_candidate`.

State/self/architecture/control: `self_state`, `self_scalar`, `self_kind`, `arch_bind`, `authority_bind`, `authority_deny`, `state_note`, `unknown_preserve`, `provenance`, `focus_set`, `policy_select`, `recovery_state`.

Exact arity is defined in `intrinsics_v1.py`. Unknown intrinsic or wrong arity gets zero structural credit. These intrinsics describe cognition/candidate state only; none directly executes a host/tool/API effect. `omega_commit_candidate` admits a candidate to the deterministic runtime boundary, not an external effect.

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
For structured work the model emits a minimal typed omega candidate. Required gates/authority/generation must be real top-level statements, not string-smuggled or nested pseudo-contract text. External execution remains outside model authority.

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
13. SFT v2 paid-training input and OOD promotion must share one canonical ClayCode structural admission authority.

## Base and deployment target
Primary checkpoint: `Qwen/Qwen2.5-0.5B` (0.49B, Apache-2.0, CausalLM).
Secondary ablation: `Qwen/Qwen2.5-0.5B-Instruct`.
Target local format: GGUF Q4_K_M.
Promotion requires measured peak process RSS < 1 GiB at 2048-token context; file size alone is insufficient.
