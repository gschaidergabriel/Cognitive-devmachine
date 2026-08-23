# the artefact — Xeno -> EntityOS cognitive computer

`the artefact/` is the canonical product/research workspace for the current **Xeno** bootstrap and its convergence toward **EntityOS + HCU/XCU**.

Current owner/work-selection authority:

- `research_entity/global/XENO_GO_OWNER_DIRECTIVE.md`
- `research_entity/global/XENO_COMPUTATIONAL_UNIT_RESEARCH_FUSION_2026-08-23.md`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json`

Current-facing Xeno root:

- `the artefact/Xeno/`

Historical `MicroEntity`, `Mini Entity`, `mini_*` and `MINI_*` paths/identifiers remain compatibility and provenance surfaces until exact migration. Git history preserves prior ClayVerse/Mini Entity authority states; they are not current work-selection authority.

## Current architecture goal

Xeno is incrementally built as a **multi-mode cognitive computational appliance** rather than a permanent swarm of agents.

```text
new data / event / prompt
          |
          v
   XENO ENTRY FABRIC
          |
          v
   XRAM STATE FABRIC
          |
    +-----+------+
    |            |
    v            v
 XPU CONTROL   XCU ACCELERATOR
 deterministic  shared-weight/vector
 scheduler      inference/function cells
    |            |
    +-----+------+
          |
 typed interconnect / workspace / Hyperposition
          |
  +-------+---------+----------+----------+
  |                 |          |          |
GRID10           COGSIM10    WM_TEST   NESTED_SIM
  |                 |          |          |
  +-------+---------+----------+----------+
          |
      SCALEOUT
          |
 calibrated ActionCandidate
          |
 Effect translator -> EffectGate -> reality
```

EntityOS is the eventual computer/runtime destination. The long-term decomposition is intentionally computer-like:

- **XRAM** — canonical/hot/rebuildable/scratch/paged state tiers;
- **XPU** — deterministic processor/control plane;
- **XCU** — accelerator/vector/inference/J-Space plane;
- **Interconnect** — typed causal packets, workspace and Hyperposition;
- **Entry I/O** — typed ingress for all new data;
- **Effect translation** — candidate to typed effect request, then EffectGate.

These names are architectural roles, not claims of custom silicon.

## Mandatory `go` law

Every explicit `go` has two required coupled tracks:

1. **XENO_EXECUTABLE_CONVERGENCE** — improve the strongest real current Xeno implementation.
2. **XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT** — advance/test/specify/wire/benchmark at least one Computational Unit or Entry primitive.

If track 2 cannot safely advance, record `XCU_NO_CHANGE_WITH_REASON` and the next discriminator. It must not silently disappear from a `go` run.

Material architecture work uses:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST DISCRIMINATOR -> SOURCE/TEST EVIDENCE -> FUSION -> BOUNDED DELTA -> RE-ENTER`

Prefer primitives reusable across multiple Xeno modes.

## Xeno modes

### `XENO_GRID10`

Simple 10 logical-cell shared-worker baseline for scheduler tests, lesions, small parallel reasoning and exact compute-matched baselines.

### `XENO_COGSIM10`

Request-scoped pure cognition simulation. A temporary 10-cell topology forms, explores hypotheses/counterhypotheses/plans/critics and emits only candidates. No simulated action has direct real effects.

### `XENO_WM_TEST`

Bounded experimental world/transition-model mode. Predictions are noncanonical and must be calibrated against later observations.

### `XENO_NESTED_SIM`

Selective high-cost mode:

`observed state -> bounded world model -> virtual computer -> simulated AI cognition -> proposed action -> hypothesis/counterhypothesis comparison -> calibrated candidate -> EffectGate`

It is not the default and does not create a second reality authority.

### `XENO_SCALEOUT`

Scale logical contexts over shared physical workers. Baseline gate sequence:

`10 -> 32 -> 64 -> 128 -> 256 -> ~600 logical contexts`

The ~600 H100-class target is a **research hypothesis only**. Logical module count is never reported as the same thing as resident model count or simultaneous decode streams.

## Authority law

- canonical durable state/evidence remains outside model-generated cognition and simulation;
- world-model state is projection/candidate state;
- HCU/XCU/J-Space/workspace outputs cannot mint canonical truth;
- Hyperposition preserves unresolved alternatives; majority vote is not truth;
- stale generation/provenance uncertainty fail closed;
- unknown external effect outcome remains UNKNOWN until verified;
- EffectGate + EffectJournal remain the real/state-changing effect authority;
- no second persistent identity, truth store, effect path or recovery ledger is admitted.

## Entry Fabric

All new data paths should converge on a typed ingress packet binding before cognition:

- ingress/causal identity;
- generation;
- source/provenance;
- modality/type;
- observed/received time;
- permissions/capability scope;
- parent/stream relation;
- compute/resource budget;
- payload reference.

Inputs may originate from humans, tools, external events, sensor/stream data, canonical database changes or intrinsic system events.

## Current executable delta — Entry Fabric + GRID10 v1

`the artefact/Xeno/runtime/` now contains the first current-facing executable Xeno path:

`stdin JSON -> typed Xeno ingress packet -> immutable event_sha256 -> deterministic XPU-like route -> logical function cells -> candidate-only result`.

The v1 path binds provenance, causal identity, generation, permissions, capability scope, time and resource budget before cognition. Route identity commits to immutable event identity, so two different events cannot alias merely because they select the same route. Transport replay of the same observed event may receive a new ingress receipt while preserving the same causal event and route identity.

The GRID10 baseline exposes 10 logical function cells while keeping physical worker budget as a separate measured quantity. This directly preserves `logical_module_count != physical_concurrent_decode_count`.

Exact component branch bytes were exercised in an isolated container: 10/10 regressions PASS plus CLI smoke PASS. The one unusual experiment for this `go`, `PROVENANCE_COLLISION_LESION`, falsified payload-only identity as sufficient: identical payloads from distinct provenance sources collided under the weak lesion but not under the Xeno event identity.

Evidence is bounded: no ~0.8B XCU inference, UnifiedDB/MiniUnifiedDB integration, EffectGate execution, world model, nested simulation, Vercel Sandbox runtime or whole EntityOS acceptance is claimed.

Receipt:

- `the artefact/Xeno/receipts/2026-08-23_GO_XENO_ENTRY_GRID10_GPT56SOL.json`

## Research fusion

Current design is informed by external evidence on heterogeneous compute/memory/interconnect (NVIDIA DGX/Grace Hopper/Rubin), shared-weight inference scheduling and paged KV (vLLM/SGLang/TensorRT-LLM), dynamic compute allocation (Mixture-of-Depths), self-regulated planning, world-model planning, generated environments and generalist agents (DeepMind Genie/SIMA), conditional multi-agent/test-time scaling, and Global Workspace/J-Space research.

The architecture treats these as evidence for mechanisms, not proof that Xeno already exhibits their claimed capacity. Runtime promotion requires exact executable evidence at the claimed scope.

## Execution policy

Current testing remains authorized-isolated-sandbox-only unless a newer owner directive changes it. Together API is forbidden. Secrets do not enter source/receipts. Final paid/model training requires explicit owner authorization.

## Current frontier

Wire the new **XenoIngressPacket/event_sha256** into the retained HCU reactive-router candidate so route decisions bind causal event identity and resolved engine identity in one formula; then bind admitted Entry events into the canonical MiniUnifiedDB/UnifiedDB state path. After that, execute exact integration regressions before promoting PR #1263 or any provider-independence/causal-route runtime claim. In parallel, retain the GRID10 primitives as the common substrate for COGSIM10, WM_TEST, NESTED_SIM and later measured SCALEOUT rather than introducing mode-specific authority stacks.
