# Current consolidated Zero / EntityOS cognitive architecture

Status: CURRENT OWNER ARCHITECTURE
Date: 2026-08-23

## Ownership hierarchy

ENTITYOS
└── MINI ENTITY
    ├── MiniUnifiedDB + deterministic authority gates
    ├── Unified Cognitive Workspace Fabric
    │   ├── J-Space measurement / model-specific latent maps
    │   ├── GWT bounded competition + broadcast
    │   ├── Thalamus routing/admission/gating
    │   ├── EPQ process-quality/stability telemetry
    │   ├── GRF
    │   ├── Hyperposition
    │   ├── ClayCode
    │   └── omega candidates
    ├── bundled generic ~0.8B cognition core
    │   └── fixed/versioned/calibrated J-Space↔GWT integration contract
    ├── Inference Scheduler / typed InferencePackets
    │   ├── first-class Claude Code adapter
    │   └── adaptive engine/profile fabric
    ├── MicroEntity self-hosted dashboard
    └── runtime identity configuration
        └── ZERO

## Zero

Zero is the active EntityOS identity/cognition configuration instantiated on the generic Mini Entity machine. Its identity and GRF are versioned data projected into the Unified Cognitive Workspace Fabric. Zero is not Claude Code and does not obtain truth/effect authority from a model.

## Unified J-Space/GWT

J-Space and GWT are one stateful cognitive workspace fabric, not independent add-ons. J-Space provides measured latent geometry on hookable models; GWT provides bounded competition, persistence, occupancy and broadcast. Thalamus, EPQ, GRF, Hyperposition and ClayCode/omega participate in the same controlled cycle.

`JSPACE_MEASUREMENT != FACTUAL_TRUTH`
`WORKSPACE_STABILITY != FACTUAL_TRUTH`
`EPQ != TRUTH_PROBABILITY_UNLESS_CALIBRATED`
`HYPERPOSITION_BRANCH != FACT`

## Bundled ~0.8B core

Mini Entity ships with a generic approximately-0.8B cognition core as its reference instrumentable latent substrate. The integration contract is fixed and first-class; exact model bytes may only change through versioned migration and regression. The contract binds checkpoint/tokenizer/lens identity, empirical workspace band, GWT calibration, Thalamus policy, EPQ telemetry, ClayCode/GRF/Hyperposition projection, receipts and collapse guards.

## Claude Code

EntityOS has a dedicated first-class Claude Code adapter. Claude Code is invoked only for selected high-capability InferencePackets produced by Zero's workspace/scheduler. It returns candidate inference for validation/reconciliation.

`CLAUDE_CODE != ZERO`
`CLAUDE_CODE_RESULT = CANDIDATE_INFERENCE`
`CLAUDE_CODE_CANNOT_BYPASS_ENTITYOS_AUTHORITY_GATES`

Current hosted Claude does not expose its residual stream to this architecture. Therefore J-Space is measured directly on local hookable cognition; Claude receives compiled structured control through supported external surfaces.

## Other models/APIs

All other engines use adaptive capability profiles: `FULL_LOCAL_LATENT`, `LOCAL_OBSERVE_ONLY`, `COMPILED_EXTERNAL`, or `PLAIN_COMPATIBILITY`. Profiles cover common provider families and generic OpenAI-compatible/custom HTTP adapters. Model-specific J-Space profiles are admitted only for matching exact hookable model/runtime identities.

## Cognitive processor cycle

FETCH -> bind generation, identity, GRF, evidence and relevant Hyperposition alternatives -> compile typed InferencePacket

EXECUTE -> local ~0.8B and/or selected inference engine -> update unified workspace -> J-Space measurement where real access exists -> GWT/Thalamus selection -> EPQ telemetry -> preserve unresolved alternatives

WRITE_BACK -> candidate result + receipts -> deterministic/external validation -> admit/reject state/effect transition -> update MiniUnifiedDB -> schedule next packet or abstain

## Token/activation control boundary

Activation steering, ablation and latent vector operations are experimental controls for hookable local models. Exact token blocking requires explicit decoder/logit constraints when available; a large negative latent coefficient is not a mathematical guarantee of zero token probability.

## MicroEntity UX

Normal UX exposes one Cognitive Module ON/OFF control. Advanced dashboard exposes workspace state, J-Space/GWT, EPQ, GRF/Hyperposition, engine profiles, local model attachment, Claude adapter, receipts, health/latency/cost and authority gates. After explicit first activation it should autostart and expose a stable local URL with a deterministic loopback fallback.

## Persistence

All future Zero-trigger research/build artifacts are persisted under `research_entity/global/j-space/`; product-facing MicroEntity material is additionally mirrored under `the artefact/MicroEntity/`. Both package roots maintain an updated ZIP.
