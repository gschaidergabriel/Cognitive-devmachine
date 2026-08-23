# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the canonical product/research workspace for the current **EntityOS** system and its single integrated **HCU** cognition/compute architecture.

Current owner/work-selection authority:

- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json`
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/rooms/PROGRAM_STATE.json`

`Xeno` and `XCU` are transitional compatibility/research aliases only. Existing `the artefact/Xeno/`, `MicroEntity`, `Mini Entity`, `mini_*`, `MINI_*`, ClayVerse and Frank names may remain where exact paths, hashes, ABI, receipts or provenance require them; they are not competing current product identities or compute architectures.

## Current architecture goal

EntityOS is incrementally converging toward a **multi-mode cognitive computer** rather than a permanent swarm of agents. HCU is the one integrated cognition/compute architecture inside that system.

```text
new data / event / prompt
          |
          v
   TYPED ENTRY FABRIC
          |
          v
 canonical state / XRAM-compatible state tiers
          |
    +-----+------+
    |            |
    v            v
 deterministic   HCU
 control plane   shared-weight/vector inference
 (XPU compat)    J-Space/function cells
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
 Effect translator -> EffectGate -> reality
```

The computer-like decomposition is intentionally functional:

- **canonical/XRAM-compatible state tiers** — durable authority plus hot/rebuildable/scratch/paged state;
- **deterministic/XPU-compatible control** — routing, scheduling, budgets, leases and generation fences;
- **HCU** — shared-weight vector/inference/J-Space/function-cell plane;
- **Interconnect** — typed causal packets, workspace and Hyperposition;
- **Entry I/O** — typed ingress for all new data;
- **Effect translation** — candidate to typed effect request, then EffectGate/EffectJournal.

`XRAM`, `XPU` and `XCU` remain compatibility/decomposition terms where useful; they do not create separate current architectures.

## Mandatory `go` law

Every explicit `go` has two required coupled tracks:

1. **ENTITYOS_EXECUTABLE_CONVERGENCE** — improve the strongest existing implementation toward EntityOS.
2. **HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT** — advance, test, specify, wire or benchmark at least one HCU or Entry primitive.

If track 2 cannot safely advance, record `HCU_NO_CHANGE_WITH_REASON` and the next discriminator. It must not silently disappear from a `go` run.

Material architecture work uses:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST DISCRIMINATOR -> SOURCE/TEST EVIDENCE -> FUSION -> BOUNDED DELTA -> RE-ENTER`

Prefer primitives reusable across multiple HCU modes.

## HCU modes

### `GRID10`

Simple 10 logical-cell shared-worker baseline for scheduler tests, lesions, small parallel reasoning and exact compute-matched baselines.

### `COGSIM10`

Request-scoped pure cognition simulation. A temporary 10-cell topology explores hypotheses/counterhypotheses/plans/critics and emits only candidates. No simulated action has direct real effects.

### `WM_TEST`

Bounded experimental world/transition-model mode. Predictions are noncanonical and must be calibrated against later observations.

### `NESTED_SIM`

Selective high-cost mode:

`observed state -> bounded world model -> virtual computer -> simulated cognition -> proposed action -> hypothesis/counterhypothesis comparison -> calibrated candidate -> EffectGate`

It is not the default and does not create a second reality authority.

### `SCALEOUT`

Scale logical contexts over shared physical workers. Baseline gate sequence:

`10 -> 32 -> 64 -> 128 -> 256 -> ~600 logical contexts`

The ~600 H100-class target is a **research hypothesis only**. Logical module count is never reported as resident model count or simultaneous decode streams.

## Authority law

- EntityOS is the only current product/system identity;
- HCU is the only current integrated cognition/compute architecture;
- canonical durable state/evidence remains outside model-generated cognition and simulation;
- world-model state is projection/candidate state;
- HCU/J-Space/workspace outputs cannot mint canonical truth;
- Hyperposition preserves unresolved alternatives; majority vote is not truth;
- stale generation/provenance uncertainty fails closed;
- unknown external effect outcome remains UNKNOWN until verified;
- EffectGate + EffectJournal remain the real/state-changing effect authority;
- no second persistent identity, truth store, effect path or recovery ledger is admitted;
- `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.

## Typed Entry Fabric

All new data paths should converge on one typed ingress boundary before HCU cognition. The current source candidate is:

- `entityos_hcu_entry_fabric_v1.py`
- `test_entityos_hcu_entry_fabric_v1.py`

The v1 candidate binds:

- causal identity and exact live entity generation;
- positive-admission source and modality classes;
- provenance digest and payload content reference;
- normalized observed/received timestamps;
- carried permission/capability claims without granting authority;
- an exact GRID10 resource-budget envelope;
- immutable semantic `event_sha256` separately from admission-specific `ingress_id`.

The identity split is deliberate: two different observed events must not alias merely because HCU later selects the same lanes, while the same observed event re-admitted under a different resource/policy envelope keeps its event identity but receives a distinct admission identity.

**Evidence boundary:** these files are source candidates only until the exact bytes execute in an actually-started authorized isolated sandbox. Source coherence does not grant HCU runtime, J-Space, EntityOS runtime or whole-product acceptance credit.

## Research fusion

Current design is informed by external evidence on heterogeneous compute/memory/interconnect, shared-weight inference scheduling and paged KV, dynamic compute allocation, self-regulated planning, world-model planning, generated environments, conditional multi-agent/test-time scaling, and Global Workspace/J-Space research.

These are evidence for mechanisms, not proof that EntityOS/HCU already exhibits the claimed capacity. Runtime promotion requires exact executable evidence at the claimed scope.

## Execution policy

Current testing remains authorized-isolated-sandbox-only unless a newer owner directive changes it. VPS, self-hosted and production-host testing are forbidden for current evidence. Together API and paid fallback are forbidden. Secrets do not enter source/receipts. Final paid/model training requires explicit owner authorization.

## Current frontier

Close remaining control-plane authority drift; bind positive local/internal cognition-engine admission plus immutable causal event identity into one HCU route decision identity; re-enter that mechanism through the typed Entry Fabric; then obtain exact isolated runtime evidence before promotion.
