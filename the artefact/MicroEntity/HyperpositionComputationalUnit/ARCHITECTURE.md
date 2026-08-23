# Hyperposition Computational Unit (HCU)

Status: **SOURCE CANDIDATE / NOT RUNTIME VERIFIED**

The Hyperposition Computational Unit is a Mini Entity subsystem that turns a pool of small
approximately-0.8B cognition cells into a sparse, coordinated compute fabric.

It is deliberately **not** a second entity, truth store, memory authority, effect path, or
consciousness daemon. MiniUnifiedDB remains canonical durable authority. HCU outputs are
candidate cognition/measurement packets. External effects remain behind the existing
Mini Entity / EntityOS gates.

## Target host

Owner-provided current VPS profile:

- plan: KVM 4
- CPU: 4 cores
- RAM: 16 GB
- disk: 200 GB
- bandwidth: 16 TB
- auto-renewal: on
- observed expiration date in the supplied plan screenshot: 2026-09-19

This profile is deployment capacity input only. Current project law still forbids using the
VPS as acceptance-test evidence until a later owner directive explicitly authorizes that.

## Core idea

Do **not** run every 0.8B cell at full decode concurrency. Four CPU cores make that a
throughput collapse even if RAM can hold many quantized copies.

The HCU therefore separates three quantities:

1. **logical cells** — specialized 0.8B roles with their own state, adapter/profile,
   hypothesis lane, calibration history and provenance;
2. **resident cells** — cells whose base weights/runtime are memory-resident or mmap-hot;
3. **active decode slots** — the small number of cells actually generating tokens at once.

The fabric is sparse. A router activates only the cells that add information to the current
problem, combines their candidate states in Hyperposition, and sends only admitted evidence
back into the canonical Mini Entity path.

## Recommended first KVM4 topology

Until exact RSS/latency measurements exist, use three candidate profiles rather than one
claimed optimum:

| Profile | Resident 0.8B cells | Active decode slots | Logical grid | Intent |
|---|---:|---:|---:|---|
| conservative | 6 | 1 | 24 | maximum stability / long context |
| balanced | 8 | 2 | 48 | default first deployment candidate |
| dense | 12 | 2 | 64 | maximize resident specialists, shorter contexts |

The dense value is a **planning hypothesis**, not a measured capacity claim.

For highest density, prefer shared immutable base weights plus small per-cell adapters/state
over N unrelated copies of the same 0.8B checkpoint. With mmap/shared pages, many logical
cells can reuse one base checkpoint while preserving separate adapter/state identities.

## Cell classes

Initial grid classes:

- `causal_world` — maintains candidate causal transitions and counterfactuals;
- `goal_generator` — proposes dynamic goals under bounded utility/risk contracts;
- `long_simulator` — runs long-horizon rollouts in compressed state space;
- `zero_model` — predicts Zero/EntityOS cognitive/action trajectories;
- `hypothesis_lab` — generates competing mechanisms and falsifiers;
- `critic` — attacks preferred hypotheses and detects circular evidence;
- `retrieval_router` — selects MiniUnifiedDB/J-Space entry points;
- `temporal_calibrator` — discounts confidence with temporal distance and model error;
- `teacher_distiller` — converts free-LLM teacher packets into bounded training/evaluation data;
- `synthesizer` — composes candidate coalitions without minting truth.

A logical grid may instantiate several cells of each class with different seeds, adapters,
contexts, or calibration histories.

## Hyperposition fabric

Each cell returns a typed packet:

`CELL_PACKET/v1 = {cell_id, role, generation, causal_id, input_digest, candidate_state,
confidence, uncertainty, evidence_refs, counterevidence_refs, cost, latency, model_identity}`

The coordinator creates a `HYPERPOSITION_PACKET/v1` containing alternatives and weights.
No winner is treated as fact merely because many cells agree. The existing evidence/authority
gates decide what may become durable canonical state.

## Scheduler

The scheduler optimizes:

`information_gain / (cpu_time + memory_pressure + token_cost + duplication_penalty)`

and enforces:

- at most `active_decode_slots` simultaneous local decoders;
- per-cell CPU quotas;
- context/KV budgets;
- generation fencing;
- duplicate-work suppression;
- starvation protection for long simulations;
- thermal/load backoff where host telemetry exists.

This makes the HCU behave more like a sparse accelerator fabric than a conventional agent swarm.

## Free-LLM feed

Free provider/model capacity from the existing token fundus may feed the HCU as
`TEACHER_PACKET/v1` inputs.

Required boundaries:

- `FREE_ONLY=true`;
- provider/model identity and request provenance are recorded;
- rate limits are respected globally per provider;
- HTTP 429 triggers backoff, never key rotation to evade quotas;
- provider output is candidate data, not canonical truth;
- secrets/tokens never enter prompts, source, receipts, ZIPs or MiniUnifiedDB;
- teacher packets are deduplicated and scored for novelty/utility;
- contradictory teacher outputs remain explicit alternatives;
- only admitted/validated derivatives can influence persistent learning.

## Persistent world-model role

The HCU may host the long-lived strategic substrate requested by the owner:

- permanent causal world-model candidates;
- dynamic bounded goal proposals;
- long iterative simulations;
- Zero cognition/action simulation;
- improvement hypotheses returned to Zero;
- complete causal time-line projections with confidence decay.

The word **permanent** refers to durable canonical state held by MiniUnifiedDB and recoverable
HCU state references. It does not create a second durable truth authority.

## Data and packaging law

All HCU-generated project artifacts must live under:

`the artefact/MicroEntity/HyperpositionComputationalUnit/`

including configs, datasets, receipts, benchmarks, planner outputs, calibration results,
adapter manifests and generated code.

`MICROENTITY_CURRENT.zip` is rebuilt recursively from the MicroEntity package root and must
include the HCU subtree. Secrets and credential material are forbidden from the archive.

## First executable gates

1. Measure actual RSS of one exact 0.8B quantized cell at several context sizes.
2. Measure 1/2/4 concurrent decode throughput on the 4-core target **only after VPS execution is authorized**.
3. Compare independent-process copies vs shared-base/adapters.
4. Determine the real resident-cell knee before swap/thrashing.
5. Benchmark sparse routing against monolithic single-cell and always-on swarm baselines.
6. Run causal falsifiers: remove one specialist class, permute routing, inject contradictory teachers.
7. Only then promote a deployment profile.

Until those gates run, resident counts and speed are engineering hypotheses.
