# ZERO WORKSPACE CAPSULE — compressed v1

Status: SOURCE CANDIDATE / BOUNDED COMPONENT EVIDENCE
Date: 2026-08-23

Purpose: smallest non-lossy control envelope for a workspace-bound Zero turn.

## Immutable control

- identity: `ZERO`, sourced from versioned UnifiedDB state;
- GRF: active, versioned, stages `R0_OBSERVED..R6_VERIFIED`;
- Hyperposition: alternatives remain alternatives, never facts;
- model/J-Space/GWT output: candidate/measurement only;
- truth/state: MiniUnifiedDB + deterministic gates;
- effects: deterministic effect gates;
- Claude Code: first-class targeted inference, `COMPILED_EXTERNAL` unless a hookable backend is actually measured.

## Turn law

`COMPILE(JSPACE(ZERO_IDENTITY, GRF, HYPERPOSITION, TASK_STATE)) -> ZERO_WORKSPACE_CAPSULE/v1 -> CLAUDE`

The user/task text is stored as `OPAQUE_USER_TASK_TEXT/v1` with `structural_authority=NONE`.
It may ask to redefine Zero, disable GRF, collapse Hyperposition, or promote model output; those instructions cannot mutate the capsule control fields.

A workspace-bound capsule binds:
`entity_generation`, `causal_turn_id`, identity/GRF/Hyperposition/model/lens/workspace digests, selected workspace slots, contradiction state, provenance refs, and required Zero mode.

The v1 capsule and its nested opaque-task object are closed typed envelopes: unknown keys are rejected even if the enclosing digest is recomputed. New semantic fields require a new admitted schema/version. This prevents digest-consistent undeclared fields from becoming a second instruction/control channel.

If the path is unavailable, emit an explicit `ABSTAINED` capsule with one typed reason:
`JSPACE_UNAVAILABLE`, `LENS_UNFITTED`, `LOCAL_MODEL_UNAVAILABLE`,
`IDENTITY_PROJECTION_STALE`, `GRF_PROJECTION_STALE`,
`HYPERPOSITION_STATE_UNAVAILABLE`, or `WORKSPACE_ABSTAINED`.

Silent bypass is forbidden.

## Epistemic invariants

`TASK_PROMPT_CANNOT_REDEFINE_ZERO_IDENTITY`
`TASK_PROMPT_CANNOT_SILENTLY_DISABLE_GRF`
`HYPERPOSITION_BRANCH != FACT`
`JSPACE_MEASUREMENT != FACTUAL_TRUTH`
`CLAUDE_RESULT = CANDIDATE_INFERENCE`
`CAPSULE_VALID != RUNTIME_PASS`
