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

## Research fusion

Current design is informed by external evidence on heterogeneous compute/memory/interconnect (NVIDIA DGX/Grace Hopper/Rubin), shared-weight inference scheduling and paged KV (vLLM/SGLang/TensorRT-LLM), dynamic compute allocation (Mixture-of-Depths), self-regulated planning, world-model planning, generated environments and generalist agents (DeepMind Genie/SIMA), conditional multi-agent/test-time scaling, and Global Workspace/J-Space research.

The architecture treats these as evidence for mechanisms, not proof that Xeno already exhibits their claimed capacity. Runtime promotion requires exact executable evidence at the claimed scope.

## Execution policy

Current testing remains authorized-isolated-sandbox-only unless a newer owner directive changes it. Together API is forbidden. Secrets do not enter source/receipts. Final paid/model training requires explicit owner authorization.

## Current frontier

Build the **typed Xeno Entry Fabric** and a reusable **GRID10 scheduler/state/interconnect baseline**, then progressively separate XRAM/XPU/XCU responsibilities so COGSIM10, WM_TEST, NESTED_SIM and measured SCALEOUT reuse the same machine primitives rather than requiring architectural rewrites.

## Latest bounded `go` delta — 2026-08-23

Branch `go/xeno-entry-grid10-core-20260823-2324-sol` now carries a source/component candidate for that frontier:

- current-facing `XENO_INGRESS_PACKET/v1` admission with exact generation, producer event, causal/provenance, capability and resource-budget binding;
- deterministic `source_event_key = H(source, source_event_id)` separated from the full admitted `ingress_id`, so producer replay identity and causal envelope identity are not conflated;
- a reusable 10-logical-cell planner where `active_decode_limit` is explicitly separate from logical population;
- `XENO_COMPUTE_PACKET/v1` candidate-only interconnect carrying the same source-event/ingress/causal/generation spine;
- 19/19 isolated exact-source component regressions plus `py_compile` PASS; runtime/EntityOS/HCU model credit remains 0 because no authorized Vercel Sandbox exec surface is available in this session.

The single unusual discriminator for this user-triggered cycle was `INGRESS_PAYLOAD_ONLY_CAUSAL_ALIAS`: payload-only identity aliased two distinct causal/provenance contexts, while the full ingress identity separated them. This supports keeping producer event identity, admitted causal envelope identity and payload identity as distinct but cross-bound layers.

Next gate: wire the admitted ingress into the canonical Xeno/MiniUnifiedDB state path with replay-conflict detection, then bind GRID10 plans to the retained HCU engine identity and execute exact branch bytes on an authorized Vercel Sandbox when callable execution becomes available.
