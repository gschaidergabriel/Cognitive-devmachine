# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the canonical product/research workspace for the current **EntityOS** product and its integrated **HCU** cognition/compute architecture.

`Xeno` and `XCU` are transitional compatibility/research aliases only. Existing `the artefact/Xeno/`, `the artefact/MicroEntity/`, `mini_*`, `MINI_*`, database schema names and historical receipts remain where exact migration is not yet safe; they do not create competing product, state, identity or effect authority.

Current authority:

- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json`
- `research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md`
- retained Xeno/HCU research directives only where consistent with the authority correction above.

Current compatibility implementation root for newly built Entry/GRID primitives:

- `the artefact/Xeno/`

## Current architecture goal

EntityOS is incrementally built as a **multi-mode cognitive computational appliance** rather than a permanent swarm of agents.

```text
new data / event / prompt
          |
          v
   TYPED ENTRY FABRIC
          |
          v
 canonical state / XRAM compatibility layer
          |
    +-----+------+
    |            |
    v            v
 deterministic   HCU
 control / XPU   shared-weight/vector/
 compatibility  inference/J-Space plane
    |            |
    +-----+------+
          |
 typed causal interconnect / workspace / Hyperposition
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
 typed effect translation -> EffectGate/EffectJournal -> reality
```

The computer-like decomposition is intentional:

- **canonical state / XRAM compatibility layer** — canonical/hot/rebuildable/scratch/paged state tiers without creating a second truth store;
- **deterministic control / XPU compatibility layer** — processor/control scheduling responsibilities;
- **HCU** — shared-weight/vector/inference/J-Space acceleration and specialized function cells;
- **Interconnect** — typed causal packets, workspace and Hyperposition;
- **Entry I/O** — typed ingress for all new data;
- **Effect translation** — candidate to typed effect request, then EffectGate/EffectJournal.

Compatibility names are architectural/path roles, not claims of custom silicon or competing product identities.

## Mandatory `go` law

Every explicit `go` has two required coupled tracks:

1. **ENTITYOS_EXECUTABLE_CONVERGENCE** — improve executable EntityOS now or strengthen the strongest retained implementation directly toward it.
2. **HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT** — advance/test/specify/wire/benchmark at least one HCU or Entry primitive, or record `HCU_NO_CHANGE_WITH_REASON`.

Material architecture work uses:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST DISCRIMINATOR -> SOURCE/TEST EVIDENCE -> FUSION -> BOUNDED DELTA -> RE-ENTER`

Prefer primitives reusable across multiple modes.

## Reference modes

### `GRID10`

Simple 10 logical-cell shared-worker baseline for scheduler tests, lesions, small parallel reasoning and exact compute-matched baselines.

### `COGSIM10`

Request-scoped pure cognition simulation. A temporary logical topology explores hypotheses/counterhypotheses/plans/critics and emits only candidates. No simulated action has direct real effects.

### `WM_TEST`

Bounded experimental world/transition-model mode. Predictions are noncanonical and must be calibrated against later observations.

### `NESTED_SIM`

Selective high-cost mode:

`observed state -> bounded world model -> virtual computer -> simulated AI cognition -> proposed action -> hypothesis/counterhypothesis comparison -> calibrated candidate -> EffectGate`

It is not the default and does not create a second reality authority.

### `SCALEOUT`

Scale logical contexts over shared physical workers. Baseline benchmark ladder:

`10 -> 32 -> 64 -> 128 -> 256 -> ~600 logical contexts`

The ~600 H100-class target is **hypothesis-only**. Logical module count is never reported as the same thing as resident model count or simultaneous decode streams.

## Authority law

- EntityOS is the sole current product/system identity;
- HCU is the sole current integrated cognition/compute architecture;
- canonical durable state/evidence remains outside model-generated cognition and simulation;
- world-model state is projection/candidate state;
- HCU/J-Space/workspace outputs cannot mint canonical truth;
- Hyperposition preserves unresolved alternatives; majority vote is not truth;
- stale generation/provenance uncertainty fail closed;
- unknown external effect outcome remains UNKNOWN until verified;
- EffectGate + EffectJournal remain the real/state-changing effect authority;
- no second persistent identity, truth store, effect path or recovery ledger is admitted.

## Typed Entry Fabric

All new data paths should converge on a typed ingress packet binding before cognition:

- ingress/causal identity;
- generation;
- source/provenance;
- modality/type;
- observed/received time;
- permissions/capability scope;
- parent/stream relation;
- compute/resource budget;
- payload identity/reference.

Inputs may originate from humans, tools, external events, sensor/stream data, canonical database changes or intrinsic system events.

## Current executable candidate

The compatibility implementation path now contains the first bounded common-machine source candidate:

- `Xeno/runtime/entry_fabric_v1.py` — deterministic typed Entry admission and packet identity;
- `Xeno/runtime/grid10_v1.py` — deterministic 10-cell logical scheduler/interconnect and work-packet ancestry;
- `Xeno/tests/test_xeno_entry_grid10_v1.py` — exact-file Entry/GRID10 regressions;
- `Xeno/receipts/2026-08-23_GO_XENO_ENTRY_GRID10_GPT56SOL.json` — exact-file component receipt bound to current EntityOS + HCU authority.

The `XENO_*` schema/path names in this candidate are compatibility identifiers only.

Current bounded evidence: Python compile PASS and 11/11 focused exact-file tests PASS in an isolated Linux/Python environment after local Git blob identities were matched to the candidate GitHub blobs. This is **component/mechanism evidence only** and grants zero integrated EntityOS/HCU model-runtime or whole-product credit.

## Research fusion

Current design is informed by external evidence on heterogeneous compute/memory/interconnect, shared-weight inference scheduling and paged KV, dynamic compute allocation, self-regulated planning, world-model planning, conditional multi-agent/test-time scaling, and Global Workspace/J-Space research.

These are evidence for mechanisms, not proof that EntityOS/HCU already exhibits their claimed capacity. Runtime promotion requires exact executable evidence at the claimed scope.

## Execution policy

Current testing remains authorized-isolated-sandbox-only unless a newer owner directive changes it. VPS/self-hosted/production-host testing is forbidden for current runtime credit. Together API and paid fallback are forbidden. Secrets do not enter source/receipts. Final paid/model training requires explicit owner authorization.

## Current frontier

Integrate the typed EntryPacket into the single canonical UnifiedDB/current MiniUnifiedDB compatibility state substrate, add **positive fail-closed internal HCU engine admission**, and bind both immutable causal-event identity and resolved engine identity into one route/work ancestry. Then drive one HCU function through `Entry -> GRID10 -> HCU -> candidate re-entry` and execute stale-generation/replay/recovery falsifiers in an authorized isolated executor before any integrated runtime promotion.
