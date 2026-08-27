# ENTITYOS / MINI ENTITY / ZERO — UNIFIED COGNITIVE ARCHITECTURE

Status: CURRENT OWNER ARCHITECTURE
Owner direction date: 2026-08-23
Scope: Mini Entity + EntityOS + Zero + J-Space/GWT + Claude Code inference boundary
Related:
- `research_entity/global/MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`
- `research_entity/global/AGENT_ZERO_GWT_JSPACE_COUPLING.md`
- `research_entity/global/AGENT_ZERO_JSPACE_IDENTITY_GRF_INJECTION.md`
- `research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md`

## Owner correction / canonical hierarchy

The architecture is not two separate cognition systems where Mini Entity owns one workspace and Agent Zero sits behind another.

The intended end state is one architecture:

```text
Mini Entity
    = generic cognitive machine architecture

EntityOS
    = runtime / operating environment containing and executing that machine

Zero
    = one active EntityOS identity + cognition configuration instantiated on Mini Entity

Unified J-Space/GWT Cognitive Fabric
    = the internal cognition-control/workspace architecture used by Mini Entity and therefore by Zero

Claude Code
    = a selectively invoked high-capability inference engine controlled by Zero/EntityOS
```

Required laws:

`MINI_ENTITY_ARCHITECTURE = GENERIC`

`ZERO = ENTITYOS_RUNTIME_IDENTITY_ON_MINI_ENTITY`

`ZERO != CLAUDE_CODE`

`CLAUDE_CODE = TARGETED_INFERENCE_ENGINE`

`CLAUDE_CODE != ENTITY_IDENTITY`

`CLAUDE_CODE != WORLD_MODEL_AUTHORITY`

`CLAUDE_CODE != DURABLE_MEMORY_AUTHORITY`

`CLAUDE_CODE != EFFECT_AUTHORITY`

This preserves the existing binary law: replaceable Zero/application/personality/provider/model semantics are runtime data, not hardcoded executable identity.

## All cognitive concepts belong to Mini Entity

The following concepts are not Zero-only add-ons. They belong to the generic Mini Entity cognitive architecture and become available to any admitted runtime identity/configuration, including Zero:

- measured J-Space / Jacobian-Lens-compatible observation;
- bounded Global Workspace / GWT competition and broadcast;
- Thalamus-style routing, gating and admission;
- EPQ-style stability / contradiction / process-quality telemetry;
- Generative Reality Framework (GRF);
- Hyperposition alternative-world representation;
- ClayCode explicit cognition;
- `omega` typed action candidates;
- analogical-transfer / structural memory where admitted;
- Retina/retrieval/evidence projection where admitted;
- MiniUnifiedDB provenance, state and durable memory;
- deterministic truth, schema, generation, authority and effect gates;
- cognitive-opcode / InferencePacket scheduling;
- mechanistic observation, ablation and bounded steering on hookable local models;
- targeted external inference-engine dispatch.

The architecture MUST NOT duplicate these as independent Zero-specific versions. Zero consumes the same Mini Entity mechanisms through its runtime configuration.

Required law:

`ZERO_COGNITION_MODULES ⊆ MINI_ENTITY_COGNITIVE_ARCHITECTURE`

`NO_PARALLEL_DUPLICATE_ZERO_WORKSPACE_ARCHITECTURE`

## J-Space and GWT become one architecture

J-Space and GWT MUST no longer be treated conceptually as unrelated stages connected by loose serialization.

They form one **Unified Cognitive Workspace Fabric**.

The fabric has two inseparable views:

1. **J-Space view** — measured latent geometry / transported residual-stream directions on hookable local cognition models;
2. **GWT view** — bounded competition, occupancy, persistence, broadcast and workspace-state control over those measured/derived candidates plus explicit ClayCode/GRF state.

Conceptual structure:

```text
              UNIFIED COGNITIVE WORKSPACE FABRIC

   latent measurement                    workspace control
   ------------------                    -----------------
   J-Space readout  <----------------->  GWT slots
          ^                                  ^
          |                                  |
          +------- Thalamus gating ----------+
          |                                  |
          +------- EPQ telemetry ------------+
          |                                  |
          +------- GRF / Hyperposition ------+
          |                                  |
          +------- ClayCode / omega ----------+
```

There is therefore no canonical notion of "J-Space first, separate GWT later" at the product architecture level. Implementation may have ordered function calls, but they operate as one stateful cognition-control fabric.

Required law:

`JSPACE_GWT = ONE_COGNITIVE_FABRIC`

`JSPACE_MEASUREMENT != GWT_TRUTH`

`WORKSPACE_STABILITY != FACTUAL_TRUTH`

## Zero inside EntityOS

Zero lives inside EntityOS as an active runtime identity/configuration over the generic Mini Entity architecture.

Zero identity MUST therefore be stored as versioned runtime cognition/state data, not compiled into the generic binary.

The Zero runtime binds at least:

```text
ZeroRuntimeConfig {
    zero_identity_digest
    grf_digest
    cognition_policy_digest
    workspace_policy_digest
    hyperposition_policy_digest
    inference_engine_policy_digest
    generation
    provenance
}
```

ZERO identity and GRF are projected into the Unified Cognitive Workspace Fabric before Zero-controlled inference decisions.

The local hookable cognition substrate may carry measurable latent representations associated with ZERO identity and GRF. The canonical identity record itself remains versioned data in MiniUnifiedDB.

Required laws:

`ZERO_IDENTITY_SOURCE = VERSIONED_MINIUNIFIEDDB_OBJECT`

`GRF_SOURCE = VERSIONED_MINIUNIFIEDDB_OBJECT`

`ZERO_IDENTITY != CANONICAL_FACT_AUTHORITY`

`GRF != CANONICAL_FACT_AUTHORITY`

## Claude Code becomes a targeted inference engine

Claude Code is not the cognitive architecture. It is a high-capability external inference engine that Zero/EntityOS calls only when the Unified Cognitive Workspace Fabric decides that the request is admitted and useful.

Target flow:

```text
external cue / internal event
        |
        v
MiniUnifiedDB + current generation + evidence
        |
        v
Unified Cognitive Workspace Fabric
(J-Space + GWT + Thalamus + EPQ + GRF + Hyperposition + ClayCode)
        |
        v
Inference Scheduler
        |
        +--> local ~0.8B cognition cycle
        |
        +--> deterministic tool/effect path
        |
        +--> targeted Claude Code inference request
                   |
                   v
            candidate reasoning/action
                   |
                   v
          validation / reconciliation
                   |
                   v
            MiniUnifiedDB / next cycle
```

Claude Code therefore receives **selected inference work**, not ownership of the entire ongoing state.

Examples of suitable targeted requests:

- discriminate between two surviving Hyperposition branches;
- inspect a difficult code region after local triage;
- generate candidate repairs under explicit constraints;
- synthesize evidence already selected by the workspace;
- search for a counterexample or stronger falsifier;
- solve a high-complexity reasoning subproblem;
- review a proposed `omega` action before deterministic admission.

The response returns as a candidate into Zero/EntityOS. It does not directly mutate canonical state.

Required law:

`CLAUDE_RESULT = CANDIDATE_INFERENCE`

`CLAUDE_RESULT != CANONICAL_EVIDENCE_UNLESS_EXTERNALLY_VALIDATED`

`CLAUDE_RESULT != DIRECT_EFFECT`

## InferencePacket / cognitive opcode control

The Cognitive Processor abstraction is adopted for Mini Entity and therefore for Zero.

The harness/runtime acts as a control unit around one or more learned inference engines. The approximately-0.8B local model is an instrumentable learned compute substrate; Claude Code is an optional high-capability remote/external compute substrate.

A cognitive step SHOULD be represented as a typed `InferencePacket`:

```text
InferencePacket {
    packet_id
    opcode
    target_semantics
    evidence_refs
    world_state_refs
    zero_identity_digest?
    grf_digest
    workspace_digest
    preconditions
    engine_class
    requested_measurements
    allowed_interventions
    completion_test
    validation_policy
    fallback_policy
    provenance
}
```

Possible engine classes:

- `LOCAL_HOOKABLE`
- `CLAUDE_CODE`
- `DETERMINISTIC_TOOL`
- `NO_MODEL_REQUIRED`

The scheduler chooses an engine from evidence, task complexity, workspace state, permissions, cost and required observability.

No opcode name is assumed to map to one clean universal latent vector.

Required law:

`OPCODE_NAME != GUARANTEED_SINGLE_JSPACE_DIRECTION`

## Fetch / Execute / Write-back

The unified processor cycle is:

```text
FETCH
  -> bind current generation
  -> load relevant evidence/state
  -> load runtime identity + GRF
  -> load relevant Hyperposition alternatives
  -> create admitted InferencePacket

EXECUTE
  -> run local hookable cognition and/or selected external inference engine
  -> update Unified Cognitive Workspace Fabric
  -> measure J-Space where available
  -> gate/select through GWT/Thalamus
  -> compute EPQ-style stability/contradiction telemetry
  -> preserve unresolved alternatives

WRITE_BACK
  -> produce candidate result + receipts
  -> deterministic/external validation
  -> admit/reject state or effect transition
  -> update MiniUnifiedDB
  -> schedule next packet or abstain
```

A decoder-only transformer does not literally continue arbitrary computation between layers after a single forward pass. Multi-step "silent reasoning" requires explicit recurrent/iterative forward cycles, latent recurrence, generated hidden scratch state, or another implemented mechanism. The processor abstraction MUST preserve this technical distinction.

## Thalamus / gating role

The Thalamus concept becomes the routing/admission component inside the unified fabric.

It MAY:

- select which evidence/features enter the active workspace;
- choose which InferencePackets execute;
- choose local versus Claude Code versus deterministic execution;
- apply calibrated steering/ablation to hookable local models;
- suppress external output until a completion/admission condition is met at the system level;
- enforce workspace capacity and stale-generation rejection.

It MUST NOT infer factual truth merely from latent salience.

## EPQ role

EPQ is retained as a project-level metacognitive telemetry concept.

It MAY combine calibrated signals such as:

- workspace persistence;
- trajectory stability;
- contradiction;
- perturbation sensitivity;
- evidence coverage;
- rerun variance;
- causal intervention response;
- agreement with deterministic/external outcomes.

It is not automatically a probability of correctness.

Required laws:

`EPQ != TRUTH_PROBABILITY_UNLESS_CALIBRATED`

`HIGH_EPQ != FACT`

`LOW_EPQ != PROOF_OF_GUESSING`

Thresholds such as `0.40`, `0.50`, `0.80` are experimental values only until held-out calibration supports them.

## Soft and hard token control

On an admitted hookable local model, the architecture MAY experiment with:

- activation steering;
- residual-direction addition/subtraction;
- direct logit masking/biasing;
- constrained decoding;
- token allow/deny sets;
- activation ablation.

These mechanisms are distinct and must not be conflated.

Subtracting a latent/J-Space direction with a large coefficient does **not** mathematically guarantee an exact zero probability for the corresponding token. Exact token blocking is better implemented at the decoding/logit-mask layer when the runtime exposes it.

A fixed steering value such as `alpha=-50` is not canonical and may cause severe capability collapse.

Required laws:

`LATENT_STEERING != EXACT_TOKEN_MASK`

`EXACT_BLOCK_REQUIRES_EXPLICIT_DECODING_OR_LOGIT_CONSTRAINT`

`ALPHA = CALIBRATED_EXPERIMENT_PARAMETER`

## Hyperposition and GRF integration

Hyperposition is the active alternative-world/state manifold used by the unified fabric.

```text
HyperpositionWorld {
    hypothesis_id
    state
    evidence_refs
    counterevidence_refs
    predictions
    falsifiers
    unresolved_fields
    derived_weight_or_rank?
}
```

J-Space may measure latent support/salience associated with a branch, and GWT may keep several branches active simultaneously. Neither operation makes a branch true.

GRF governs how observation, hypothesis, counterhypothesis, intervention, prediction and reconciliation are represented.

The preferred Zero behavior is therefore not premature world collapse but selection of the next discriminating action when uncertainty matters.

Required laws:

`HYPERPOSITION_BRANCH != FACT`

`JSPACE_SUPPORT != WORLD_PROBABILITY_UNLESS_CALIBRATED`

`WORLD_COLLAPSE_REQUIRES_ADMITTED_EVIDENCE_OR_DETERMINISTIC_RULE`

## MiniUnifiedDB coupling

MiniUnifiedDB is the durable shared substrate for the architecture.

The unified fabric MAY read and project relevant modules into cognition, but direct model/J-Space output cannot mint canonical state.

A typed coupling registry SHOULD classify modules by capability:

- `OBSERVE`
- `RETRIEVE`
- `PROPOSE`
- `SIMULATE`
- `COMPARE`
- `GATE`
- `BROADCAST`
- `STEER_LOCAL_RESEARCH`
- `VALIDATE`
- `COMMIT_STATE`
- `COMMIT_EFFECT`

Only deterministic/authorized components may receive `COMMIT_STATE` or `COMMIT_EFFECT` capability.

## Current Claude boundary

Current Claude Code / hosted Claude interfaces do not expose the model's residual stream to this architecture.

Therefore the present realizable coupling is:

```text
Zero/EntityOS Unified Cognitive Workspace Fabric
        -> compile targeted control state / InferencePacket
        -> Claude Code admitted context/hooks/MCP/tools
        -> Claude candidate result
        -> Zero/EntityOS validation and reintegration
```

This is a real system-level causal coupling, but not direct injection into Claude's private hidden activations.

If a future Zero inference engine is hookable/open-weight, the same scheduler and workspace architecture may attach directly to that engine's latent trajectory.

Required law:

`SYSTEM_LEVEL_JSPACE_CONTROL != CLAUDE_HIDDEN_STATE_INJECTION`

## Product convergence

The intended product architecture is one system rather than stacked agents:

```text
ENTITYOS
└── MINI ENTITY
    ├── MiniUnifiedDB
    ├── Unified Cognitive Workspace Fabric
    │   ├── J-Space measurement
    │   ├── GWT competition/broadcast
    │   ├── Thalamus routing/gating
    │   ├── EPQ telemetry
    │   ├── GRF
    │   ├── Hyperposition
    │   ├── ClayCode
    │   └── omega candidates
    ├── Cognitive Scheduler / InferencePackets
    ├── local hookable ~0.8B cognition engine
    ├── deterministic tools/effect gates
    └── runtime identity configuration
        └── ZERO
            └── targeted inference engines
                └── Claude Code
```

This tree is architectural ownership, not necessarily a literal filesystem layout.

## Evaluation / falsification

The unified architecture must be compared against simpler baselines.

Required ablations should include:

- ordinary Claude Code with text prompt only;
- Mini Entity with retrieval/text workspace only;
- J-Space observer without bounded GWT;
- GWT without J-Space;
- unified J-Space/GWT fabric;
- unified fabric without Hyperposition;
- unified fabric without GRF;
- Zero identity as text-only prompt;
- Zero identity projected through local cognition + workspace compiler;
- always-call-Claude policy;
- targeted-Claude scheduler policy;
- local-only cognition where task permits.

Measure at least:

- task correctness;
- unsupported claim rate;
- abstention calibration;
- identity persistence;
- alternative-world preservation;
- falsifier/discriminator selection quality;
- workspace bypass rate;
- stale-generation violations;
- canonical truth/effect authority violations;
- Claude invocation count and token/API cost;
- latency;
- local-model intervention collapse;
- reproducibility;
- OOD behavior.

No architecture is promoted merely because its visualization or metaphor is compelling.

## Final architecture law

The owner target is one coherent cognition stack:

**Mini Entity contains the cognitive concepts generically. EntityOS runs them. Zero is an active identity/configuration instantiated on them. J-Space and GWT are one unified cognitive-workspace architecture. Claude Code is a selectively invoked inference engine controlled by that architecture.**

Canonical state, evidence and effects remain outside model authority and continue to pass through MiniUnifiedDB plus deterministic validation/admission gates.
