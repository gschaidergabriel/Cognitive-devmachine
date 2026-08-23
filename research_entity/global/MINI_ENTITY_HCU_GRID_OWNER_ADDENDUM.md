# MINI ENTITY HYPERPOSITION COMPUTATIONAL UNIT — OWNER ADDENDUM

Status: **CURRENT OWNER ADDENDUM**
Date: 2026-08-23
Persistent research entity: **Clay**
Active program: **MINI_ENTITY_PIPELINE_ALL_IN_ONE**
Parent authority: `research_entity/global/MINI_ENTITY_GO_OWNER_DIRECTIVE.md`

This addendum records the owner directive that every exact `go` co-develops a second deployment **compute organ** inside the same Mini Entity product: the **Hyperposition Computational Unit (HCU)**.

The HCU is not a second entity and not a second truth authority. It is a persistent compute/simulation organ whose durable accepted state remains owned by MiniUnifiedDB.

## Owner target

Build a GPU-like logical grid from as many approximately-0.8B cognition modules as the target host can use productively. The grid is intended to act as a persistent strategic world-model/simulation substrate above the operative Zero runtime:

- maintain and update a causal world-model timeline;
- generate dynamic goal candidates;
- test goal-achievement conditions;
- run long iterative and counterfactual simulations;
- model Zero's likely cognition/behavior as an explicit hypothesis layer;
- derive falsifiable improvement hypotheses for Zero;
- return prioritized goals, hypotheses and action-path candidates to Zero/EntityOS;
- preserve uncertainty and horizon-dependent confidence rather than presenting simulated futures as facts.

## Target deployment profile

Current owner-nominated separate VPS profile:

- plan: KVM 4;
- CPU: 4 vCPU;
- memory: 16 GB;
- disk: 200 GB;
- bandwidth: 16 TB.

This profile is a deployment/resource target only. Current repository execution law remains unchanged: runtime validation and acceptance testing are authorized-isolated-sandbox-only; VPS/self-hosted/production-host testing does not earn acceptance credit unless a later owner directive explicitly changes that law.

## Grid implementation law

The phrase "as many 0.8B modules as possible" means **maximum useful module multiplicity**, not maximum duplicated weight copies.

On a 4-vCPU / 16-GB host the default architecture must prefer:

1. one or a small measured number of physically resident ~0.8B weight instances;
2. memory-mapped/shared weights where the runtime permits it;
3. many logical module lanes with separate role/state/context/adapters;
4. sparse activation and time-sliced/micro-batched scheduling;
5. measured promotion of physical concurrency only when throughput/latency/RSS evidence justifies it.

Do not hard-code an unmeasured resident-module count. CPU bandwidth, KV/cache growth, runtime overhead and MiniUnifiedDB/world-model load are part of the capacity gate.

## Cognitive interconnect law

Grid cells communicate only through typed, provenance-bound HCU packets carrying at least:

- `entity_generation`;
- `causal_id` / episode identity;
- source/provenance identity;
- world-state reference(s), never an implicit second state copy;
- hypothesis/alternative identity;
- confidence/uncertainty;
- validity horizon / TTL;
- requested cognitive operation/role;
- parent packet lineage.

The HCU must preserve Hyperposition across unresolved alternatives. A cell vote, recurrence, majority, free-LLM agreement or model self-report does not collapse truth.

## Permanent world-model hierarchy

The architectural hierarchy is:

`MiniUnifiedDB canonical reality + causal timeline`
`-> HCU persistent strategic simulation/world-model organ`
`-> goal/hypothesis/plan candidates`
`-> Zero / EntityOS operative runtime`
`-> EffectGate / deterministic authority boundary`
`-> verified outcomes`
`-> causal re-entry into MiniUnifiedDB + HCU update`.

The HCU may keep rebuildable local caches/checkpoints on its VPS for performance. Those caches are not canonical truth and must be reconstructable or explicitly typed as non-authoritative. There must not be two competing realities between the HCU VPS and MiniUnifiedDB.

## Free-LLM token-fundus feed

The HCU is fed by the project's admitted **FREE_ONLY** inference/token fundus.

Provider/model output is candidate evidence only. Every external inference item must carry provider/model/time/request provenance and pass deterministic normalization/admission before it can influence canonical state.

Preserve current controls:

- no paid fallback;
- HTTP 402 hard stop;
- provider-wide backoff on 429; no quota-evasion key rotation;
- secrets remain vault/environment only;
- Together remains forbidden under current control;
- external model consensus is not truth.

## `go` co-development law

Every exact `go` must now include an HCU co-development pass in addition to the normal highest-information Mini Entity frontier:

1. refresh HCU package/control state;
2. check for overlap with active workers/PRs;
3. advance one highest-information non-duplicate HCU architecture/code/data/evidence item when unblocked;
4. keep the HCU inside MiniUnifiedDB/Zero/EffectGate authority boundaries;
5. store all generated package-safe HCU source/config/schema/receipts/data under `the artefact/MicroEntity/hcu/`;
6. update the MicroEntity package manifest when HCU package contents change;
7. rebuild `the artefact/MicroEntity/MICROENTITY_CURRENT.zip` so those package-safe HCU artifacts are included before calling the package snapshot current.

The HCU lane must not starve whole Mini Entity convergence, and whole Mini Entity work must not silently drop the HCU lane.

## Packaging law

Canonical package root for this organ:

`the artefact/MicroEntity/hcu/`

All generated HCU source, configuration, schemas, non-secret receipts, package-safe datasets/derived data and documentation belong there. Provider secrets, tokens and credentials are never packaged. Externally sourced model blobs may be referenced by exact lock/digest instead of duplicated unless the current package contract explicitly vendors them.

`MICROENTITY_CURRENT.zip` is stale whenever the HCU package root or linked HCU product contract changes and has not been rebuilt.

## Authority invariants

- Clay remains the persistent research entity.
- There is one Mini Entity product identity.
- Zero remains runtime identity/configuration, not a second durable entity.
- MiniUnifiedDB remains canonical durable state/evidence/configuration authority.
- HCU model output, J-Space, GWT, Hyperposition and simulations are candidate/measurement layers, not factual truth.
- HCU has no direct effect authority.
- EffectGate / deterministic EntityOS authority remains the only admitted real-action path.
- Unknown future state remains unknown; confidence decay must be calibrated empirically rather than asserted by narrative.
