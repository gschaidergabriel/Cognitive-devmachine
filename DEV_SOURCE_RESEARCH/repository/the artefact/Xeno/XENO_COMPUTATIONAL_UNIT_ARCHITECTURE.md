# Xeno Computational Unit Architecture

Status: **CURRENT TARGET ARCHITECTURE / INCREMENTAL BUILD CONTRACT**
Date: 2026-08-23

## 1. One machine, several modes

Xeno is a single evolving computational appliance. It does not fork into separate agent, world-model and simulator products. The shared substrate is reused with different topologies and budgets.

```text
                         XENO
                          |
          +---------------+---------------+
          |               |               |
       ENTRY            XRAM            XPU
      Fabric         State Fabric    Control Plane
          |               |               |
          +---------------+---------------+
                          |
                    XCU ACCELERATOR
                 shared-weight workers
                          |
                 typed interconnect
               workspace / Hyperposition
                          |
     +---------+----------+----------+----------+
     |         |                     |          |
  GRID10   COGSIM10              WM_TEST   NESTED_SIM
     |         |                     |          |
     +---------+----------+----------+----------+
                          |
                    Action Candidate
                          |
                    Effect Translator
                          |
                      EffectGate
```

## 2. Xeno Entry Fabric

All new data should converge on one typed ingress boundary before cognition.

```text
XenoIngressPacket {
    ingress_id
    causal_id
    generation
    source
    provenance
    modality
    observed_at
    received_at
    permissions
    capability_scope
    parent_or_stream_id?
    resource_budget
    payload_ref
}
```

Sources include humans, external events, tool results, sensor/stream inputs, canonical DB changes and intrinsic system events.

The Entry Fabric performs deterministic admission/binding. It does not decide truth from semantics.

## 3. XRAM — memory/state hierarchy

Xeno progressively separates memory classes:

```text
L0 canonical durable state/evidence
L1 hot admitted working set
L2 rebuildable indexes/projections
L3 simulation scratch / branch state
L4 paged/offloaded suspended context
```

Only L0 can be canonical authority. L1-L4 are caches, projections or simulation state unless explicitly promoted through existing authority rules.

## 4. XPU — deterministic processor/control plane

XPU is processor-like control, not an LLM persona.

Responsibilities:

- route requests to modes;
- allocate logical cells and budgets;
- lease physical workers;
- maintain generation/causal fences;
- schedule suspend/resume;
- enforce resource ceilings;
- collect metrics;
- recover after crash;
- reject stale/unauthorized effects.

## 5. XCU — accelerator/vector plane

XCU is the specialization plane for:

- shared ~0.8B model workers;
- tensor/vector transforms;
- embedding/retrieval kernels;
- local J-Space measurement where technically available;
- batched function-cell inference;
- verifier/critic calls;
- simulation rollouts.

Logical cells do not own model weights. They bind context/function/branch state to shared workers.

## 6. Interconnect / packet fabric

Every internal packet is typed and causally bound.

```text
XenoComputePacket {
    packet_id
    cycle_id
    causal_id
    generation
    mode
    producer_function
    parent_packet_ids[]
    assumptions[]
    evidence_refs[]
    counterevidence_refs[]
    branch_id?
    workspace_class
    confidence_class
    payload_ref
}
```

The interconnect carries candidates and measurements, never implicit authority.

## 7. Reference modes

### XENO_GRID10

Purpose: cheap baseline, lesions, scheduler tests, simple multi-function work.

```text
10 logical cells
shared workers
no required world model
bounded workspace
Hyperposition reducer
```

### XENO_COGSIM10

Purpose: simulate only cognition/action-selection for one request.

```text
canonical snapshot
 -> dynamic 10-cell topology
 -> hypotheses / counterhypotheses / planning / critics
 -> simulated action candidates
 -> calibration
 -> external EffectGate
```

### XENO_WM_TEST

Purpose: bounded experimental transition/world prediction.

World-model state is noncanonical. Every prediction should bind falsifiers and later observed outcome where possible.

### XENO_NESTED_SIM

Purpose: high-cost experimental mode.

```text
canonical observations
       |
       v
bounded world-model state
       |
       v
virtual computer state
       |
       v
simulated AI/Xeno cognition
       |
       v
simulated/proposed action
       |
       v
hypothesis/counterhypothesis comparison
       |
       v
calibrated ActionCandidate
       |
       v
EffectGate
```

Nothing inside the nesting has direct real-effect authority.

### XENO_SCALEOUT

Purpose: increase logical search/simulation population while retaining shared physical workers.

Scale gates:

`10 -> 32 -> 64 -> 128 -> 256 -> ~600 logical contexts`

~600 is not an acceptance target until exact model/hardware tests demonstrate value and feasibility.

## 8. Scheduler model

```text
N_logical = N_active + N_suspended + N_queued

M_total =
    M_weights
  + N_active * M_KV_active
  + N_suspended * M_branch_state
  + M_workspace
  + M_runtime
  + M_headroom
```

The scheduler maximizes useful information gain subject to latency, memory and safety budgets.

It may:

- batch compatible cells;
- reuse prefixes/KV where causally safe;
- page/offload suspended branches;
- collapse unproductive branches;
- allocate more cells to hard requests;
- route trivial requests around simulation entirely.

## 9. Mode router

A request receives a mode based on expected value of compute.

```text
trivial / deterministic
    -> DIRECT

small ambiguity / parallel check
    -> GRID10

reasoning-heavy but environment-light
    -> COGSIM10

environment dynamics materially affect choice
    -> WM_TEST

high-value long-horizon interaction where cheaper modes remain ambiguous
    -> NESTED_SIM

large search population justified by hardware and task
    -> SCALEOUT
```

The router itself must be evaluated against always-direct and always-simulate baselines.

## 10. Computerization acceptance

Xeno becomes more computer-like only when responsibilities become simpler and more reusable:

- one ingress contract;
- one state hierarchy;
- one control plane;
- one accelerator abstraction;
- one interconnect packet law;
- one effect boundary;
- many temporary topologies.

The target is not to hide complexity. It is to move task-specific complexity from durable source architecture into bounded runtime topology while keeping invariants small and testable.

## 11. GO obligation

Every `go` must report/advance:

1. Xeno executable delta or blocker;
2. XCU/Entry/computerization delta or `XCU_NO_CHANGE_WITH_REASON`;
3. hypothesis + counterhypothesis for material architecture claims;
4. cheapest discriminator/test;
5. cross-mode reuse impact;
6. exact evidence boundary.
