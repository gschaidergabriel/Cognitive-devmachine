# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the canonical product/research workspace for the current **EntityOS** system and its integrated **HCU** cognition/compute architecture.

Current work-selection authority:

- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json` — EntityOS is the sole current product/system identity; HCU is the sole current cognition/compute architecture.
- `research_entity/global/XENO_GO_OWNER_DIRECTIVE.md` — retained transitional mechanism/work-selection donor where compatible with the newer supervisor correction.
- `research_entity/global/XENO_COMPUTATIONAL_UNIT_RESEARCH_FUSION_2026-08-23.md` — retained research donor.

`Xeno` is a transitional implementation compatibility codename, not a competing product/system. `XCU` is a transitional/research alias for HCU, not a second compute architecture. Historical `MicroEntity`, `Mini Entity`, `mini_*`, `MINI_*`, ClayVerse and Frank names remain compatibility/provenance surfaces where exact migration would break hashes, receipts, ABI, paths or reproducibility.

Transitional implementation root:

- `the artefact/Xeno/`

## Current architecture goal

EntityOS is incrementally built as a **multi-mode cognitive computational appliance** with one authority path rather than a permanent swarm of agents.

```text
new data / event / prompt
          |
          v
   TYPED ENTRY FABRIC
          |
          v
   XRAM / STATE FABRIC
          |
    +-----+------+
    |            |
    v            v
 XPU CONTROL    HCU ACCELERATOR
 deterministic shared-weight/vector
 scheduler     inference/function cells
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

The long-term decomposition is intentionally computer-like:

- **XRAM / State Fabric** — canonical/hot/rebuildable/scratch/paged state tiers;
- **XPU** — deterministic processor/control plane;
- **HCU** — accelerator/vector/inference/J-Space cognition-compute plane;
- **Interconnect** — typed causal packets, workspace and Hyperposition;
- **Entry I/O** — typed ingress for all new data;
- **Effect translation** — candidate to typed effect request, then EffectGate.

These names describe architectural roles, not custom-silicon claims.

## Mandatory `go` law

Every explicit `go` advances two coupled tracks under the current EntityOS/HCU authority:

1. **ENTITYOS_HCU_EXECUTABLE_CONVERGENCE** — improve the strongest existing executable implementation without forking product/state/effect authority.
2. **HCU_AND_TYPED_ENTRY_CO_DEVELOPMENT** — advance/test/specify/wire/benchmark at least one reusable HCU or typed Entry primitive. Transitional Xeno/XCU identifiers may remain where compatibility requires them.

Material architecture work uses:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST DISCRIMINATOR -> SOURCE/TEST EVIDENCE -> FUSION -> BOUNDED DELTA -> RE-ENTER`

Prefer executable discriminators and reusable primitives over additional authority prose.

## Multi-mode HCU substrate

### `GRID10`

Simple 10 logical-cell shared-worker baseline for scheduler tests, lesions, small parallel reasoning and exact compute-matched baselines.

### `COGSIM10`

Request-scoped pure cognition simulation. A temporary 10-cell topology explores hypotheses/counterhypotheses/plans/critics and emits candidates only. No simulated action has direct real effects.

### `WM_TEST`

Bounded experimental world/transition-model mode. Predictions are noncanonical and must be calibrated against later observations.

### `NESTED_SIM`

Selective high-cost mode:

`observed state -> bounded world model -> virtual computer -> simulated cognition -> proposed action -> hypothesis/counterhypothesis comparison -> calibrated candidate -> EffectGate`

It is not the default and does not create a second reality authority.

### `SCALEOUT`

Scale logical contexts over shared physical workers. Baseline research gate sequence:

`10 -> 32 -> 64 -> 128 -> 256 -> ~600 logical contexts`

The ~600 H100-class target remains a **research hypothesis only**. Logical module count is never reported as resident model count or simultaneous decode streams.

## Authority law

- canonical durable state/evidence remains outside model-generated cognition and simulation;
- world-model state is projection/candidate state;
- HCU/J-Space/workspace outputs cannot mint canonical truth;
- Hyperposition preserves unresolved alternatives; majority vote is not truth;
- stale generation/provenance uncertainty fail closed;
- unknown external effect outcome remains UNKNOWN until verified;
- EffectGate + EffectJournal remain the only real/state-changing effect authority;
- no second persistent identity, truth store, effect path or recovery ledger is admitted.

## Typed Entry Fabric

All new data paths should converge on a typed ingress packet before cognition, binding at least:

- immutable ingress/causal event identity;
- generation;
- source/provenance;
- modality/type;
- observed/received time;
- permissions/capability scope;
- parent/stream relation;
- compute/resource budget;
- payload reference.

If an admitted event activates HCU model cognition, the route must also bind the resolved cognition-engine identity/class. Route-decision identity must commit to **event identity + resolved engine identity + routing result**. A finite external-provider denylist is not positive internal-engine admission.

## Research fusion

Current design is informed by evidence on heterogeneous compute/memory/interconnect, shared-weight inference scheduling and paged KV, dynamic compute allocation, self-regulated planning, world-model planning, generated environments/generalist agents, conditional multi-agent/test-time scaling, and Global Workspace/J-Space research.

These are mechanism evidence, not proof that EntityOS/HCU already exhibits the claimed capacity. Runtime promotion requires exact executable evidence at the claimed scope.

## Execution policy

Current testing remains authorized-isolated-sandbox-only unless a newer owner directive changes it. VPS/self-hosted/production-host testing is not accepted for current evidence. Together API is forbidden. Secrets do not enter source/receipts. Final paid/model training requires explicit owner authorization.

## Latest `go` delta — 2026-08-23 route identity discriminator

A fresh exact-source component discriminator now exists at:

- `research_entity/continuity/tools/verify_hcu_route_identity_contract.py`
- `research_entity/continuity/tests/test_verify_hcu_route_identity_contract.py`

Against retained draft PR #1263 router blob `7c0fee26fd3d8a48b99da7eca7f3bca8fea046ae`, the verifier proves that the current candidate aliases different causal events and different resolved-engine identities to the same route digest, accepts missing engine identity on model routes, and accepts an external engine class. Exact replay of the same event remains deterministic. This is **EXACT_SOURCE_COMPONENT_CONTRACT_FAIL**, not EntityOS/HCU runtime failure or whole-product PASS/FAIL.

## Current frontier

Repair the retained PR #1263 route mechanism in place: positive local-HCU engine admission; immutable event identity; resolved engine identity/class; one route digest `H(event, engine, routing-result)`; downstream receipt echo; deterministic replay; package rebuild; then rerun the exact discriminator in an authorized isolated executor. After that, continue measured HCU runtime/J-Space/Entry-Fabric integration without creating a second product or authority path.
