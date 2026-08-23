# MINI ENTITY — Hyperposition Computational Unit (HCU)

Status: **CURRENT OWNER-DIRECTED ARCHITECTURE CANDIDATE**
Date: 2026-08-23
Persistent research entity: **Clay**
Product boundary: **Mini Entity / EntityOS integrated cognitive architecture**
Canonical research source: `research_entity/global/MINI_ENTITY_HYPERPOSITION_COMPUTATIONAL_UNIT.md`

## Owner target

Build a second-host computational organ for Mini Entity from as many approximately-0.8B modules as the target VPS can safely sustain, coordinated as a grid rather than as independent agents. The unit is intended to host, among other workloads:

- a permanent causal world-model/simulation substrate;
- dynamic goal proposal and goal-progress evaluation;
- long iterative counterfactual simulation;
- a bounded model of Zero's current cognition/state;
- self-improvement hypothesis generation and falsification;
- temporal state trajectories with uncertainty increasing away from observed time;
- intake of candidate evidence/hypotheses from the configured FREE_ONLY LLM/token pool.

Current owner-supplied deployment profile:

```text
VPS class: KVM 4
CPU:       4 cores
RAM:       16 GiB
Disk:      200 GB
Bandwidth: 16 TB
```

This is a **deployment target profile**, not runtime evidence. Current repository execution law still requires authorized isolated execution for build/test/runtime claims; the VPS does not become an acceptance-test surface merely because it is the intended deployment host.

## Core design decision: logical grid, shared weights

The HCU MUST NOT naïvely load N full independent copies of the same 0.8B weights merely to look parallel. On a 4-core/16-GiB CPU VPS that would waste RAM and usually reduce useful throughput.

Preferred architecture:

```text
one pinned quantized ~0.8B checkpoint/runtime image
              │
              ├── shared read-only/mmap weights when the runtime safely supports it
              │
              └── HCU scheduler
                    ├── active inference lane 0
                    ├── active inference lane 1
                    ├── active inference lane 2
                    ├── active inference lane 3
                    └── many logical module slots
                         ├── role/config/state
                         ├── bounded working context/KV while active
                         └── serialized dormant state when inactive
```

Therefore the unit behaves more like a modular processor array than a set of unrelated chat agents:

- **logical modules** are role/state machines around one generic 0.8B cognition substrate;
- only a measured number of **active inference lanes** are resident concurrently;
- dormant modules preserve compact typed state in MiniUnifiedDB and do not require a private model copy;
- immutable weights should be shared across worker processes/threads where the exact runtime provides safe page sharing/mmap semantics;
- if the runtime cannot prove safe weight sharing, HCU reduces physical concurrency rather than duplicating memory until OOM.

`GPU_LIKE_COORDINATION != GPU_EQUIVALENT_HARDWARE`

The HCU is GPU-like only in the sense of many small scheduled computational modules working on one shared problem fabric. It does not claim GPU execution characteristics.

## Dynamic capacity law

There is deliberately no canonical fixed module count before exact measurement on the target runtime.

At boot the capacity planner derives:

```text
available_ram
- OS / EntityOS / MiniUnifiedDB reserve
- shared checkpoint/runtime footprint
- active-lane KV/context budget
- scheduler/telemetry reserve
= slot/state budget
```

The planner then selects:

- `active_inference_lanes <= measured useful CPU parallelism`;
- `logical_module_slots = AUTO_MAX_SAFE`;
- a minimum memory headroom fence;
- a queueing policy that can increase logical slots without increasing simultaneously resident KV state;
- automatic degradation to fewer active lanes/shorter contexts under memory pressure.

The initial 4-core profile makes **four active CPU lanes a natural upper-bound candidate**, but this remains a measurement target, not a truth claim. Logical module count can be substantially larger because dormant modules can be time-sliced and their typed state serialized.

## Initial logical module grid

The first HCU role map should be application-neutral and replaceable. A useful starting grid is:

1. `world_ingest` — converts admitted observations into candidate state deltas;
2. `causal_extractor` — proposes typed cause/effect relations;
3. `temporal_indexer` — aligns events, valid-time and transaction-time;
4. `world_state_updater` — proposes world-model transitions;
5. `goal_proposer` — proposes bounded goals from canonical state and policy;
6. `goal_critic` — attacks goal utility, feasibility and conflict;
7. `goal_progress` — evaluates evidence for progress/failure;
8. `planner` — proposes multi-step action/simulation plans;
9. `counterfactual_simulator` — explores alternative branches;
10. `failure_simulator` — searches for plan breakage and negative trajectories;
11. `zero_twin` — models Zero's likely state/capability limits without becoming Zero;
12. `hypothesis_generator` — proposes product/cognition improvement hypotheses;
13. `hypothesis_falsifier` — generates discriminating tests/counterexamples;
14. `confidence_calibrator` — tracks uncertainty/forecast decay from measured evidence;
15. `hyperposition_keeper` — preserves unresolved alternatives without premature collapse;
16. `synthesizer` — composes bounded candidate packets for the persistent workspace.

Additional logical modules MAY be instantiated automatically when measurement shows useful capacity. Specialization is in role contract/state, not immutable personality or separate identity.

## Hyperposition interconnect

Modules communicate only through typed packets and one shared canonical authority boundary.

```text
ModuleResultPacket {
    packet_id
    module_slot_id
    role
    turn_id?
    episode_id?
    causal_id?
    generation
    input_evidence_refs[]
    assumptions[]
    candidate_claims[]
    candidate_actions[]
    alternatives[]
    uncertainty
    provenance
    runtime_receipt_ref?
}
```

The scheduler collects incompatible candidate packets into a set-valued Hyperposition rather than averaging them into one asserted answer.

Collapse is permitted only through an admitted discriminator/evidence update. Recurrence, majority vote, model confidence or cross-model agreement do not by themselves create truth.

## Permanent world-model substrate

The HCU may run continuously on the deployment VPS, but its persistence remains inside the same Mini Entity authority structure.

The canonical durable world model is represented in MiniUnifiedDB. The HCU owns computation, not a second truth database.

Required separation:

```text
MiniUnifiedDB = canonical durable state/evidence/configuration authority
HCU runtime   = computational organ producing candidate transitions/simulations
Hyperposition = unresolved candidate-set representation
EffectGate    = sole admitted real-effect path
Zero          = runtime identity/configuration inside the same entity
```

The HCU MAY maintain rebuildable caches, queues, mmap files and ephemeral simulation artifacts under its package/runtime data root. Those are projections/caches, not competing durable truth.

## Long simulation and temporal confidence

A simulated trajectory must be explicit about observed versus inferred versus generated state.

```text
SimulationNode {
    simulation_id
    branch_id
    parent_node_id?
    horizon_step
    target_time?
    state_projection
    assumptions[]
    evidence_refs[]
    counterevidence_refs[]
    uncertainty_sources[]
    confidence_interval_or_score?
    model_runtime_receipt
}
```

Confidence MAY decay with temporal distance, branch depth, unresolved assumptions, model disagreement and historical calibration error. No fixed decay curve is canonical before empirical calibration.

`FUTURE_SIMULATION != FUTURE_FACT`

Zero may inspect simulated past/future branches, but they remain typed projections with provenance and uncertainty.

## Dynamic goals

HCU modules may autonomously **propose** goals. Durable admission of a goal is a deterministic EntityOS/MiniUnifiedDB transition, not a free-form model side effect.

```text
GoalCandidate
  -> GoalAdmissionGate
  -> ACCEPTED | REJECTED | DEFERRED | NEEDS_EVIDENCE
  -> canonical goal state in MiniUnifiedDB
```

Goal admission should check at least policy, provenance, conflict, bounded resources, stale generation and whether the proposed goal would require a capability/effect outside the admitted surface.

No module may directly execute a real action merely because it proposed the goal.

## Zero cognitive twin

`zero_twin` is a predictive model of Zero, not a second Zero identity.

It may estimate:

- likely next cognitive/workspace state;
- missing context;
- expected tool/inference needs;
- likely failure modes;
- candidate improvements to prompts, routing, retrieval, J-Space/GWT configuration or EntityOS policy.

Its output is candidate evidence/hypothesis only. It may never overwrite Zero identity, MiniUnifiedDB truth, EffectGate policy or accepted runtime state directly.

## Improvement hypothesis loop

```text
observed Zero/HCU outcome
  -> hypothesis_generator
  -> hypothesis_falsifier
  -> discriminating test specification
  -> authorized isolated execution when available
  -> evidence receipt
  -> RETAIN | REJECT | MERGE | PROMOTE
```

The HCU may generate code/configuration improvement candidates, but self-generated patches are never self-authorizing. Source changes still require the normal repository/evidence/admission path.

## FREE_ONLY LLM/token feed

The configured free-model/token fund is an **input organ**, not authority.

Required path:

```text
free provider scheduler
  -> provider/model capability profile
  -> bounded prompt/task packet
  -> candidate response
  -> secret/leak/provenance gate
  -> EvidenceCandidatePacket
  -> dedupe/conflict/Hyperposition handling
  -> MiniUnifiedDB admission decision
```

Rules:

- FREE_ONLY stays active;
- no paid fallback;
- current Together execution prohibition remains active;
- provider 402 is hard stop;
- provider 429 causes provider-wide backoff, never quota-evasion key rotation;
- secrets are referenced only by opaque secret refs and never enter prompts, receipts, package files or ordinary DB exports;
- model agreement is not factual verification;
- provider/model output cannot directly commit truth or effects.

Useful free-model work includes independent causal extraction, counterhypotheses, factual-source discovery proposals, plan criticism, simulation branch generation and summarization of already-admitted evidence.

## Scheduler

The HCU scheduler is deterministic around nondeterministic inference.

Priority may consider:

- unresolved Hyperposition pressure;
- causal/world-model gaps;
- active goal urgency;
- expected information gain;
- Zero failure probability;
- freshness/valid-time pressure;
- resource cost/latency;
- free-provider availability;
- evidence sensitivity;
- module starvation/age.

Each dispatch and result must carry generation/provenance identifiers. Stale-generation results fail closed or are retained only as explicitly stale research evidence.

## Resource strategy for the 4-core / 16-GiB target

The preferred implementation strategy is:

1. one small quantized 0.8B base checkpoint loaded read-only;
2. shared immutable weight pages where supported;
3. at most the measured useful number of simultaneous CPU inference lanes;
4. many more logical role slots than physical lanes;
5. short bounded active contexts by default;
6. serialize dormant module state rather than retaining every KV cache;
7. use disk for append-only receipts/simulation shards/rebuildable caches, not as slow fake RAM for live weights;
8. preserve several GiB of headroom for OS, DB, EntityOS, page cache and burst behavior;
9. continuously measure RSS, latency, queue time, token throughput, context pressure and swap activity;
10. automatically shrink active lanes/context before swap/OOM.

A real exact-runtime benchmark must determine whether the best operating point is 1, 2, 3 or 4 simultaneous inference lanes and how many dormant logical slots are useful. The architecture intentionally optimizes for **total solved-work throughput and simulation depth**, not the largest impressive process count.

## Package/data law

Everything created specifically for this HCU lane must live in or be mirrored into:

`the artefact/MicroEntity/hcu/`

Product-facing architecture is mirrored at:

`the artefact/MicroEntity/concepts/MINI_ENTITY_HYPERPOSITION_COMPUTATIONAL_UNIT.md`

`MICROENTITY_CURRENT.zip` must contain the HCU architecture/config/code/tests/receipts that are part of the current package snapshot. Secrets, provider tokens, raw credential files and host-private runtime state are excluded.

Runtime-generated durable HCU data should use a package-defined runtime data root and be backed by MiniUnifiedDB/provenance rules; release ZIPs contain schemas/config/templates/receipts, not secret-bearing live databases.

## `go` integration law

The HCU is a first-class Mini Entity workstream. Every exact `go` macrocycle must consider the HCU frontier during work selection and, when non-duplicate useful work exists, advance it alongside the core Mini Entity path rather than treating it as a separate future project.

However:

`HCU != SECOND_ENTITY`

`HCU != SECOND_MINIUNIFIEDDB`

`HCU != SECOND_EFFECT_PATH`

`HCU_MODULE != INDEPENDENT_AGENT_IDENTITY`

The unit is one computational organ inside the same persistent Clay/Mini Entity lineage.

## Acceptance gates

Source architecture is not HCU runtime PASS.

Before deployment credit, exact authorized evidence should cover:

- checkpoint/runtime identity and quantization;
- shared-weight behavior or explicit fallback;
- measured RSS per active lane and per logical dormant slot;
- throughput/latency for 1..N active lanes;
- OOM/swap pressure and automatic degradation;
- scheduler fairness and stale-generation rejection;
- deterministic packet schema validation;
- Hyperposition non-collapse on model agreement alone;
- MiniUnifiedDB single-authority behavior;
- free-provider backoff/402/secret isolation;
- restart/recovery of canonical state without duplicate effects;
- long-simulation uncertainty provenance;
- Zero-twin and hypothesis outputs remaining candidate-only;
- package/ZIP completeness and secret exclusion.

Until those are observed on admitted exact runtime bytes, this document defines the owner-directed architecture candidate and implementation obligations only.
