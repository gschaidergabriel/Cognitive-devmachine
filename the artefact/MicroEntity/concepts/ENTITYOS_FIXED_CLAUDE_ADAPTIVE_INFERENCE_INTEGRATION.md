# ENTITYOS — FIXED CLAUDE CODE + ADAPTIVE INFERENCE INTEGRATION

Status: CURRENT OWNER ARCHITECTURE
Owner direction date: 2026-08-23
Scope: EntityOS + Mini Entity + bundled ~0.8B cognition core + Unified J-Space/GWT + Claude Code + adaptive inference backends + self-hosted MicroEntity dashboard
Supersedes conflicting assumptions in earlier concepts where the approximately-0.8B cognition checkpoint was purely optional or where Claude Code was merely one undifferentiated provider profile.
Related:
- `research_entity/global/ENTITYOS_MINI_ENTITY_ZERO_UNIFIED_COGNITIVE_ARCHITECTURE.md`
- `research_entity/global/MINI_ENTITY_JSPACE_GWT_INSTRUMENTED_COGNITION.md`
- `research_entity/global/AGENT_ZERO_GWT_JSPACE_COUPLING.md`
- `research_entity/global/AGENT_ZERO_JSPACE_IDENTITY_GRF_INJECTION.md`
- `research_entity/global/MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md`

## Canonical owner decision

EntityOS and Mini Entity use one integrated cognition architecture.

The product MUST ship with a **bundled, first-class approximately-0.8B cognition core** whose integration with the Unified J-Space/GWT Cognitive Fabric is fixed, versioned, tested and available without any external API.

EntityOS MUST additionally ship with a **first-class Claude Code integration path** optimized specifically for Claude Code as Zero's preferred high-capability targeted inference engine.

Every other model/API/backend is reached through one **adaptive inference integration layer** that maps backend capabilities into the same Mini Entity scheduler, InferencePacket, workspace, provenance and validation contracts.

Required hierarchy:

```text
ENTITYOS
└── MINI ENTITY
    ├── MiniUnifiedDB authority
    ├── ZERO / runtime identity configuration
    ├── Unified Cognitive Workspace Fabric
    │   ├── J-Space
    │   ├── GWT
    │   ├── Thalamus gating
    │   ├── EPQ telemetry
    │   ├── GRF
    │   ├── Hyperposition
    │   ├── ClayCode
    │   └── omega
    ├── BUNDLED ~0.8B COGNITION CORE
    │   └── FIXED J-SPACE/GWT INTEGRATION CONTRACT
    ├── Inference Scheduler
    │   ├── FIRST-CLASS CLAUDE CODE ADAPTER
    │   └── ADAPTIVE BACKEND FABRIC
    │       ├── local hookable models
    │       ├── local API servers
    │       ├── hosted model APIs
    │       └── generic compatible/custom adapters
    └── MicroEntity self-hosted dashboard
```

Laws:

`MINI_ENTITY_HAS_BUNDLED_COGNITION_CORE = TRUE`

`BUNDLED_COGNITION_CORE_CLASS ~= 0.8B_GENERIC_CLAYCOG`

`JSPACE_GWT_08B_INTEGRATION = FIRST_CLASS_FIXED_CONTRACT`

`CLAUDE_CODE_INTEGRATION = FIRST_CLASS_FIXED_CONTRACT`

`OTHER_INFERENCE_ENGINES = ADAPTIVE_PROFILED_CONTRACT`

`INFERENCE_ENGINE != ENTITY_IDENTITY`

`INFERENCE_ENGINE != CANONICAL_TRUTH_AUTHORITY`

`INFERENCE_ENGINE != DIRECT_EFFECT_AUTHORITY`

## Meaning of "fixed" for the bundled 0.8B core

"Fixed" means the product always has one known local cognition path with a stable integration contract. It does **not** mean that one historical checkpoint byte sequence can never be upgraded.

The bundled cognition core MUST have a pinned versioned manifest containing at least:

```text
BundledCognitionManifest {
    engine_id
    model_family
    checkpoint_digest
    tokenizer_digest
    quantization/runtime_identity?
    jspace_profile_digest
    lens_profile_digest
    workspace_calibration_digest
    steering_calibration_digest?
    claycode_contract_version
    grf_contract_version
    hyperposition_contract_version
    compatible_entityos_range
    provenance
}
```

The product integration remains fixed while exact weights may advance only through an explicit versioned migration/update path with regression evidence.

Therefore:

`FIXED_INTEGRATION != IMMUTABLE_MODEL_BYTES_FOREVER`

`MODEL_UPGRADE_REQUIRES_VERSIONED_MIGRATION`

`MODEL_UPGRADE_MUST_NOT_RESET_MINIUNIFIEDDB`

The bundled 0.8B core remains generic. It has no hard-coded application/personality/provider identity and cannot own durable entity truth/state/effects.

## Fixed perfected J-Space/GWT integration around the 0.8B core

The local bundled cognition core is the reference latent substrate of Mini Entity.

Its J-Space/GWT path MUST be engineered as one product subsystem rather than optional research glue:

```text
canonical state / evidence
    -> typed projection
    -> bundled ~0.8B cognition core
    <-> J-Space observer / model-specific latent map
    <-> GWT competition + bounded broadcast
    <-> Thalamus routing / admission
    <-> EPQ trajectory telemetry
    <-> GRF + Hyperposition + ClayCode state
    -> InferencePacket result
    -> deterministic validation / write-back
```

The reference integration owns:

- exact checkpoint/tokenizer/lens binding;
- empirically identified workspace layer/position band;
- GWT slot policy and occupancy calibration;
- Thalamus input/output gating policy;
- EPQ telemetry feature definitions;
- prompt/ClayCode/GRF/Hyperposition projection format;
- optional research steering/ablation profile;
- decoding/logit-control capabilities where the local runtime exposes them;
- generation/turn receipts and stale-profile rejection;
- reproducible regression corpus and calibration fixtures.

No fixed alpha, fixed slot count, fixed layer number or truth threshold is canonical unless measured on the exact bundled checkpoint/runtime.

## One visible Cognitive Module toggle

The normal user-facing product surface SHOULD expose the internal architecture as one module:

```text
COGNITIVE MODULE: [ ON | OFF ]
```

When `ON`:

- the bundled 0.8B cognition core is available;
- Unified J-Space/GWT workspace control is active;
- GRF/Hyperposition/ClayCode/EPQ/Thalamus participate according to policy;
- targeted external inference engines may be used according to selected profiles and permissions.

When `OFF`:

- no latent J-Space/GWT intervention or local cognition scheduling runs;
- deterministic MiniUnifiedDB/state/effect machinery remains available;
- the product MAY permit an explicitly selected direct inference mode only if policy allows and clearly labels the bypass;
- no silent claim of workspace conditioning is allowed.

The one-toggle UX does not erase internal typed components. It hides complexity from ordinary operation while preserving full inspectability in the advanced dashboard.

## EntityOS first-class Claude Code integration

Claude Code is a specially integrated inference engine, not merely a generic HTTP provider preset.

EntityOS MUST maintain a dedicated `ClaudeCodeEngineAdapter` contract that is versioned and regression-tested against the currently supported Claude Code control surfaces.

Conceptual contract:

```text
ClaudeCodeEngineAdapter {
    adapter_version
    capability_profile
    transport_profile
    context_compiler
    tool_mcp_bridge
    workspace_receipt_binding
    zero_identity_binding
    grf_binding
    hyperposition_binding
    inference_packet_binding
    response_parser
    provenance_capture
    failure_classifier
    cost_usage_meter
    validation_return_path
}
```

The adapter receives targeted InferencePackets compiled from the Mini Entity/Zero workspace. It MUST NOT receive implicit ownership of the whole state machine.

Required path:

```text
Unified J-Space/GWT Fabric
    -> Inference Scheduler
    -> Zero Control / InferencePacket compiler
    -> ClaudeCodeEngineAdapter
    -> Claude Code targeted inference
    -> typed candidate result + provenance/receipt
    -> EntityOS validation/reconciliation
    -> MiniUnifiedDB / next workspace cycle
```

The adapter SHOULD exploit Claude Code-specific capabilities when available, including managed context, tools, hooks and MCP/tool state, while remaining fail-closed if a required capability disappears or changes incompatibly.

Laws:

`CLAUDE_CODE = PREFERRED_TARGETED_HIGH_CAPABILITY_ENGINE`

`CLAUDE_CODE != ZERO`

`CLAUDE_CODE_RESULT = CANDIDATE_INFERENCE`

`CLAUDE_CODE_CANNOT_BYPASS_ENTITYOS_AUTHORITY_GATES`

`CLAUDE_CODE_ADAPTER_CAPABILITY_MISMATCH = EXPLICIT_TYPED_FAILURE`

The current public Claude boundary still does not expose Claude's private residual-stream activations. Therefore the J-Space/GWT geometry remains directly measured on the bundled/local hookable model; Claude Code receives a compiled control projection and returns candidate inference.

## Adaptive inference fabric for everything else

All non-Claude engines enter through an adaptive, capability-driven integration fabric.

Every engine is represented by an `InferenceEngineProfile`:

```text
InferenceEngineProfile {
    profile_id
    engine_family
    provider_or_runtime
    endpoint_class
    model_id_or_pattern
    auth_scheme
    secret_ref?
    context_window?
    input_modalities
    output_modalities
    streaming
    tools
    structured_output
    system_instruction_surface
    reasoning_controls
    logprobs
    logit_bias_or_mask
    seed_control
    local_activation_access
    local_gradient_access
    hookable_layers
    tokenizer_access
    jspace_mode
    jspace_adapter_profile?
    rate_limit_policy
    cost_policy
    healthcheck
    provenance
}
```

The runtime MUST negotiate capabilities rather than assume that every model supports the same control surfaces.

### Adaptive J-Space modes

The profile resolves one of these modes:

1. `FULL_LOCAL_LATENT`
   - open/hookable local model;
   - activations available;
   - model-specific J-Space/Lens profile may be fitted and measured;
   - bounded local steering/ablation possible only when calibrated and enabled.

2. `LOCAL_OBSERVE_ONLY`
   - local model exposes activations/readout but intervention is disabled or unsupported;
   - J-Space can observe and GWT can schedule, but no latent steering.

3. `COMPILED_EXTERNAL`
   - hosted/closed API model;
   - no hidden-state access;
   - bundled 0.8B + Unified J-Space/GWT fabric compiles the targeted InferencePacket/context/tool state for the external engine;
   - returned candidate is reintegrated and measured at the system level.

4. `PLAIN_COMPATIBILITY`
   - minimal completion/chat endpoint;
   - only capabilities actually exposed are used;
   - no false claim of latent integration.

Required law:

`ADAPTIVE_JSPACE != PRETEND_HIDDEN_STATE_ACCESS`

`CLOSED_API_JSPACE_MODE = COMPILED_EXTERNAL`

`HOOKABLE_MODEL_MAY_USE_MODEL_SPECIFIC_LATENT_PROFILE`

## Predefined engine/profile catalog

The shipped configuration SHOULD include ready-to-fill templates for common engine families so ordinary setup requires only endpoint/model/token selection where needed.

Initial profile families SHOULD cover at least:

- Claude Code / Anthropic;
- OpenAI-compatible APIs;
- OpenAI native profile family;
- Google Gemini profile family;
- Mistral profile family;
- Groq profile family;
- NVIDIA NIM/profile family;
- OpenRouter profile family;
- Together profile family as configuration only, still subject to current execution/budget policy;
- Ollama;
- llama.cpp server;
- vLLM;
- Hugging Face/TGI-compatible local or remote endpoints;
- generic local executable runner;
- generic custom HTTP/JSON adapter;
- generic OpenAI-compatible endpoint for providers that expose that contract.

The architecture MUST remain extensible. "All APIs" is implemented as **broad native profile coverage plus generic protocol adapters and user-defined profiles**, not as a claim that every future proprietary API is permanently known in advance.

`NEW_ENGINE_INTEGRATION = PROFILE_OR_ADAPTER_ADD`, not a MiniUnifiedDB migration or entity reset.

## Automatic profile adaptation

When a profile is created or activated, EntityOS SHOULD run a non-destructive capability probe where the backend permits it.

The probe may determine:

- endpoint reachability;
- authentication validity without exposing the secret;
- advertised model list where supported;
- structured-output support;
- tool/function-call support;
- streaming;
- context/limits where discoverable;
- logprob/logit controls;
- local activation/hook access;
- tokenizer compatibility;
- local model architecture and candidate layer map;
- whether a fitted J-Space profile exists and matches exact model/tokenizer digest.

The result becomes a versioned `CapabilityReceipt`.

No capability is inferred merely from a provider name when an exact runtime probe or manifest can resolve it.

## Model-specific adaptive J-Space profiles

For hookable local models, EntityOS SHOULD support one model-specific `JSpaceAdapterProfile` per exact model family/checkpoint/runtime identity where required:

```text
JSpaceAdapterProfile {
    profile_id
    model_digest
    tokenizer_digest
    architecture_family
    layer_map
    candidate_workspace_band
    lens_digest?
    lens_fit_manifest?
    projection_rules
    normalization_rules
    gwt_calibration
    epq_calibration
    intervention_capabilities
    collapse_guards
    validation_corpus_digest
    provenance
}
```

A profile may be prepackaged only when it was measured on matching bytes/runtime. Otherwise the UI reports `JSPACE_PROFILE_UNCALIBRATED` and may offer observe-only or profile-fit/calibration workflows rather than silently reuse another model's vector geometry.

## Secrets and API tokens

The dashboard MUST allow users to attach API tokens/credentials to engine profiles without putting secrets into prompts, logs, receipts, exported MiniUnifiedDB rows or source control.

Secrets SHOULD be held through an OS-backed secret store or an encrypted local secret vault referenced by opaque `secret_ref` values.

Required laws:

`PROFILE_STORES_SECRET_REF_NOT_PLAINTEXT_SECRET`

`SECRET_NEVER_ENTERS_JSPACE_TELEMETRY`

`SECRET_NEVER_ENTERS_MODEL_CONTEXT`

`SECRET_NEVER_EXPORTED_WITH_ORDINARY_PROFILE_BACKUP`

The profile UI may show only metadata such as configured/not configured, last validation time and masked identifier fragments where safe.

## MicroEntity self-hosted web dashboard

Mini Entity / EntityOS MUST provide a self-hosted web application for configuration and live cognition inspection.

After first activation the dashboard SHOULD autostart with EntityOS and expose a stable local name.

Preferred local addresses:

```text
http://microentity/
http://microentity.local/
```

Implementation rule:

- first activation registers a local service/autostart entry;
- where permissions and host OS allow, register the `microentity` hostname/alias through an approved local mechanism;
- advertise `microentity.local` through local-network discovery where supported;
- always retain a deterministic loopback fallback such as `http://127.0.0.1:<configured-port>/`;
- never claim the bare hostname works if local name registration failed;
- expose the resolved URL in the activation receipt and launcher output.

The dashboard SHOULD include:

- master Cognitive Module ON/OFF;
- bundled 0.8B status and exact manifest/digest;
- Unified J-Space/GWT live workspace visualization;
- GWT slots and transitions;
- EPQ/contradiction telemetry;
- GRF/Hyperposition active state;
- Zero identity/runtime profile;
- Claude Code first-class adapter status;
- inference engine/profile selector;
- precreated provider/local-engine profiles;
- API token/secret-ref configuration;
- local model attachment and capability scan;
- per-engine J-Space mode (`FULL_LOCAL_LATENT`, `LOCAL_OBSERVE_ONLY`, `COMPILED_EXTERNAL`, `PLAIN_COMPATIBILITY`);
- model-specific J-Space profile/calibration status;
- health, latency, usage/cost and rate-limit telemetry;
- InferencePacket trace and engine-selection reason;
- provenance/conditioning receipts;
- deterministic authority/effect gate results;
- advanced calibration/research controls gated separately from normal operation.

## One-time activation and autostart

On first activation, EntityOS MAY request the permissions required for its configured local operating mode, including autostart/service registration, local listening port, local hostname registration, optional LAN exposure, local model access and secret-store integration.

The activation transaction MUST be explicit and produce a durable receipt. After accepted activation:

- EntityOS service starts automatically according to the chosen local policy;
- MicroEntity dashboard autostarts with the service;
- the selected stable local URL is re-advertised;
- engine/profile configuration persists in MiniUnifiedDB;
- secrets remain in the secret store/vault;
- switching backend/model does not reset the entity.

LAN exposure MUST be separately controllable from loopback-only access. Default deployment SHOULD prefer local-only binding unless the owner explicitly enables network exposure.

## Scheduler policy

The Unified Cognitive Workspace Fabric decides whether to use:

- bundled 0.8B only;
- Claude Code;
- another external API;
- another local LLM;
- deterministic tools only;
- no model at all.

Selection factors MAY include:

- task complexity;
- need for latent observability;
- context size;
- modalities;
- tool requirements;
- local resource availability;
- latency;
- configured cost/budget;
- rate limits;
- privacy policy;
- evidence sensitivity;
- EPQ/workspace state;
- explicit user engine preference.

Claude Code may be the preferred high-capability path for Zero, but the scheduler remains authoritative and must preserve exact receipts for why an engine was selected.

## Fail-closed integration laws

A targeted inference request MUST NOT silently downgrade its guarantees.

Examples:

- requested `FULL_LOCAL_LATENT` but no matching exact J-Space profile -> `JSPACE_PROFILE_MISSING_OR_STALE`;
- Claude Code adapter requires a control surface no longer available -> `CLAUDE_ADAPTER_CAPABILITY_MISMATCH`;
- secret missing -> `ENGINE_SECRET_UNAVAILABLE`;
- remote API does not support required tools/schema -> `ENGINE_CAPABILITY_UNSATISFIED`;
- profile belongs to another model digest -> `ENGINE_PROFILE_IDENTITY_MISMATCH`;
- dashboard hostname registration failed -> service remains reachable through resolved fallback and records `LOCAL_ALIAS_UNAVAILABLE`.

No fallback may pretend that hidden-state/J-Space control occurred when it did not.

## Product acceptance tests

Before calling this integration product-ready, test at least:

1. fresh install -> one-time activation -> autostart -> dashboard reachable through resolved local URL;
2. master Cognitive Module OFF/ON transition without MiniUnifiedDB reset;
3. bundled 0.8B exact manifest + J-Space/GWT profile identity validation;
4. stale/wrong lens/profile fails closed;
5. Claude Code adapter consumes a generation-bound targeted InferencePacket and returns a typed candidate receipt;
6. Claude Code cannot directly commit canonical state/effects;
7. generic OpenAI-compatible remote profile works through `COMPILED_EXTERNAL` without fake latent claims;
8. hookable local model receives or fits the correct model-specific J-Space profile;
9. switching among Claude Code, remote API and local LLM preserves entity continuity;
10. secrets never appear in prompts/logs/telemetry/export;
11. capability probe detects unsupported tools/structured output and scheduler routes or abstains correctly;
12. bare `microentity` name failure cleanly exposes loopback/mDNS fallback rather than breaking service;
13. dashboard accurately labels measured latent data versus compiled external control versus canonical truth.

## Final product law

The product target is now stronger and simpler from the user's perspective:

**Mini Entity always contains one tightly integrated approximately-0.8B local cognition core and one unified J-Space/GWT Cognitive Module. EntityOS exposes that architecture through one master module switch and a self-hosted MicroEntity dashboard. EntityOS has a fixed first-class Claude Code integration for Zero's targeted high-capability inference, while every other local model or API is attached through an adaptive capability/profile layer with model-specific J-Space integration only where real latent access exists.**

The integration may be deep, but authority remains explicit:

`MINIUNIFIEDDB + DETERMINISTIC_GATES > ALL_MODEL_OUTPUT`
