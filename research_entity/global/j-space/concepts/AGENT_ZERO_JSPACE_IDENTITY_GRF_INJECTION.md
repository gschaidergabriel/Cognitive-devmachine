# AGENT ZERO — J-SPACE IDENTITY + GENERATIVE REALITY INJECTION

Status: CURRENT CONCEPT
Owner direction: 2026-08-23
Program: Mini Entity pipeline all-in-one
Related: `research_entity/global/AGENT_ZERO_GWT_JSPACE_COUPLING.md`
Related: `research_entity/global/MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`

## Core decision

Agent Zero / Claude Code MUST receive both the ZERO identity and the Generative Reality Framework through the J-Space-side cognition-control path before every workspace-bound Zero turn.

This is not merely a text prompt convention. ZERO identity and the Generative Reality Framework are versioned cognition-control objects rooted in UnifiedDB and projected through the hookable local open-weight cognition substrate into measured J-Space / GWT state. Claude Code then receives a typed, generation-bound projection of that state through admitted external control surfaces.

Current Claude-backed Zero does not expose its own residual stream, weights, Jacobians, or hidden-state hooks. Therefore the system MUST distinguish real latent injection into the local open-weight cognition substrate from typed external injection into Claude Code.

Laws:

`ZERO_IDENTITY_SOURCE = UNIFIEDDB`

`GRF_SOURCE = UNIFIEDDB`

`ZERO_IDENTITY_AND_GRF_MUST_BIND_EVERY_WORKSPACE_ZERO_TURN`

`ZERO_JSPACE_PROJECTION != DIRECT_CLAUDE_HIDDEN_STATE_INJECTION`

`DIRECT_CLAUDE_HIDDEN_STATE_INJECTION = UNAVAILABLE_UNLESS_BACKEND_EXPOSES_HOOKABLE_MODEL`

## Required control path

```text
UnifiedDB
  -> ZERO identity object
  -> Generative Reality Framework object
  -> Hyperposition world-model state
  -> other admitted cognition modules
  -> local open-weight cognition substrate
  -> J-Space measurement / Jacobian Lens
  -> Thalamus gating
  -> bounded GWT workspace
  -> ZERO CONTROL CAPSULE
  -> managed Zero admission boundary
  -> Claude Code
  -> proposed reasoning/actions
  -> deterministic validation / authority gates
  -> UnifiedDB feedback
```

## ZERO identity as a J-Space attractor

ZERO identity is not defined by a mutable application prompt. It is a persistent, versioned identity object whose projection is refreshed into the local cognition substrate before each workspace-bound turn.

The identity object may contain only generic, program-level identity invariants and cognition policy. Application, task, provider, model, personality, and transient role semantics remain replaceable runtime data unless explicitly elevated by owner authority.

The local J-Space layer measures whether the active cognition state remains aligned with the projected ZERO identity manifold. Alignment is telemetry and control evidence, not truth.

Laws:

`ZERO_ALIGNMENT != FACTUAL_CORRECTNESS`

`ZERO_ALIGNMENT != CANONICAL_TRUTH`

`ZERO_IDENTITY != APPLICATION_PERSONA`

## Generative Reality Framework as an ontology/control manifold

The Generative Reality Framework is projected into the same local J-Space cognition cycle as ZERO identity. Its role is not to inject fixed answers but to constrain how candidate realities, hypotheses, causal models, interventions, evidence, and counterfactuals are represented and selected.

At minimum the GRF projection should make available typed primitives for:

- observed evidence
- unknown state
- hypotheses
- counter-hypotheses
- causal links
- interventions
- predicted outcomes
- contradiction
- falsification/discrimination tests
- uncertainty
- alternative world states
- state transition expectations

GRF remains an inference/cognition framework. It does not acquire authority to mint canonical facts merely because a latent direction is strong or stable.

Laws:

`GRF_LATENT_STABILITY != WORLD_TRUTH`

`GRF_HYPOTHESIS != EVIDENCE`

`GRF_PROJECTION_MUST_PRESERVE_UNKNOWN != ZERO != ERROR != MEASURED`

## Hyperposition coupling

Hyperposition is the world-model counterpart to the J-Space cognition layer. It SHOULD be coupled bidirectionally where the stored state has clear provenance and semantics.

The system should expose an active set of alternative world states rather than collapse uncertainty prematurely. J-Space/GWT may rank, compare, gate, or request discrimination between those states, but canonical state changes remain deterministic and evidence-bound.

Conceptual cycle:

```text
Hyperposition alternatives
  -> projected candidate-world features
  -> J-Space / GWT competition
  -> EPQ / stability / contradiction telemetry
  -> selected discrimination or intervention request
  -> Zero execution
  -> observed outcome
  -> UnifiedDB evidence update
  -> Hyperposition posterior/state transition update
```

Laws:

`HYPERPOSITION_WORLD != CANONICAL_WORLD`

`MOST_SALIENT_WORLD != TRUE_WORLD`

`WORLD_COLLAPSE_REQUIRES_ADMITTED_EVIDENCE_OR_DETERMINISTIC_RULE`

## UnifiedDB module coupling law

UnifiedDB modules are not all blindly injected on every turn. Each module is classified as one of:

- `CORE_ALWAYS`: required every workspace-bound Zero turn
- `CONTEXTUAL`: admitted when task/state relevance crosses a deterministic gate
- `RESEARCH_ONLY`: available only in explicit research/evaluation mode
- `AUTHORITY_ONLY`: may validate or commit state but may not be steered by model output
- `ARCHIVE_ONLY`: retrievable evidence/history, never a live cognition controller

Initial mandatory `CORE_ALWAYS` set:

- ZERO identity
- Generative Reality Framework
- Hyperposition world-model summary/state
- truth-state distinctions and provenance handles
- current generation / causal identity

Likely contextual set:

- Thalamus routing signals
- GWT workspace slots
- EPQ telemetry
- analogical-transfer structures
- Retina / retrieval-derived observation summaries
- task-specific memory and candidate cards

The exact module list must be derived from the current UnifiedDB schema and measured usefulness; no module becomes canonical merely because it exists in the database.

## ZERO CONTROL CAPSULE

Before a workspace-bound Claude Code call, the local cognition layer emits one typed capsule. Minimum fields:

```text
zero_control_capsule {
  schema_version
  capsule_id
  entity_generation
  causal_turn_id
  zero_identity_digest
  grf_digest
  hyperposition_digest
  local_model_digest
  jacobian_lens_digest
  workspace_digest
  identity_alignment_telemetry
  grf_active_primitives
  hyperposition_active_worlds
  selected_workspace_slots
  contradiction_state
  epistemic_telemetry
  provenance_refs
  required_zero_mode
  forbidden_modes
  abstention_reason?
}
```

The capsule MUST be bound to the current generation and turn. A stale or missing identity/GRF projection fails closed when J-Space workspace mode is enabled.

Allowed explicit unavailability states include:

- `JSPACE_UNAVAILABLE`
- `LENS_UNFITTED`
- `LOCAL_MODEL_UNAVAILABLE`
- `IDENTITY_PROJECTION_STALE`
- `GRF_PROJECTION_STALE`
- `HYPERPOSITION_STATE_UNAVAILABLE`
- `WORKSPACE_ABSTAINED`

Silent bypass is forbidden.

## Claude Code delivery boundary

For the current Claude-backed Zero implementation, the capsule is delivered through admitted external surfaces such as managed system/context injection, hooks, MCP state, or tool-mediated control state. The implementation goal is that Zero cannot begin a workspace-bound turn without consuming a fresh capsule or an explicit typed fail-closed receipt.

This makes the SYSTEM EXECUTION PATH identity/GRF-bound without falsely claiming that Claude's proprietary hidden-state trajectory has been directly modified.

Future hookable Zero backends may receive the same ZERO and GRF objects as actual residual-stream steering vectors, subject to calibration, ablation, alpha sweep, and collapse guards.

## Evaluation

Required comparisons:

1. Claude Code / Zero without J-Space identity/GRF binding
2. text-only identity + GRF prompt
3. UnifiedDB identity/GRF -> typed capsule without local J-Space
4. local J-Space + GWT + ZERO/GRF capsule-bound Zero
5. future hookable open-weight Zero with direct latent ZERO/GRF steering

Metrics:

- identity-policy adherence
- GRF primitive usage quality
- unsupported-claim rate
- unknown/abstention calibration
- Hyperposition alternative preservation
- discrimination-test selection quality
- authority violations
- stale/bypass rate
- task correctness
- latency / external API cost
- reproducibility
- intervention dose-response for hookable local models

## Acceptance rule

ZERO identity and Generative Reality Framework are considered successfully coupled only when:

- their canonical UnifiedDB objects have explicit schema/version/digests,
- their projections are deterministically bound to each workspace Zero turn,
- missing/stale projections fail closed or produce explicit abstention,
- J-Space telemetry remains separate from canonical truth,
- Hyperposition alternatives remain distinguishable from measured reality,
- and controlled evaluation shows benefit over text-only prompting without unacceptable degradation.

Until then this is architecture and research direction, not proof of hidden-state identity transfer into Claude.
