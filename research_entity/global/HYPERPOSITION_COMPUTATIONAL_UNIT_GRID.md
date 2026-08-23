# Mini Entity Hyperposition Computational Unit (HCU) Grid

Status: SOURCE CANDIDATE / owner-directed architecture extension  
Date: 2026-08-23  
Scope: Mini Entity / EntityOS integrated cognitive architecture

## Purpose

The HCU turns the mandatory generic ~0.8B ClayCog core into a GPU-like **grid of logical cognition lanes**. It is not a swarm of durable agents and does not create another entity, memory authority, effect path, or recovery ledger.

```text
                         ONE MINI ENTITY
                              |
                       MiniUnifiedDB
                  canonical state/evidence
                              |
                  Unified J-Space / GWT
                              |
                  HCU packet scheduler
          +---------+---------+---------+---------+
          |         |         |         |         |
        lane 0    lane 1    lane 2    lane 3    ... lane N
       ~0.8B      ~0.8B      ~0.8B      ~0.8B
      logical     logical     logical     logical
       state       state       state       state
          |         |         |         |         |
          +---------+---- Hyperposition ---------+
                              |
                       one GWT selection
                              |
                  validation / Effect Gate
                              |
                       MiniUnifiedDB
```

## Key distinction: logical lane != full model copy

A lane is an independently scheduled cognitive state/InferencePacket context. Multiple lanes may share one immutable checkpoint/runtime mapping when the admitted local runtime can safely share model pages/weights. The architecture must not multiply full model bytes merely to create more Hyperposition branches.

Required laws:

- `PERSISTENT_MINI_ENTITY_COUNT = 1`
- `CANONICAL_STATE_AUTHORITY = MiniUnifiedDB`
- `REAL_EFFECT_AUTHORITY = EntityOS/Mini Entity deterministic Effect Gate`
- `HCU_LANE = EPHEMERAL_COGNITIVE_COMPUTE_SLOT`
- `HCU_LANE != PERSISTENT_AGENT`
- `HCU_LANE != DURABLE_MEMORY_AUTHORITY`
- `HCU_LANE != DIRECT_EFFECT_AUTHORITY`
- `PARALLEL_MODEL_OUTPUT = CANDIDATE_ONLY`
- `ONE_GWT_COMMIT_WINNER_PER_ADMITTED_COMMIT_BOUNDARY`

## GPU-like execution model

The HCU borrows the useful structural idea from SIMT/GPU execution without pretending a CPU VPS is a GPU:

1. one packet template can be fanned out across several Hyperposition branches;
2. each lane receives branch-specific evidence/state refs and a common generation fence;
3. lanes run independently or in micro-batches where the runtime supports it;
4. results are collected as candidate tensors/structured packets, not canonical facts;
5. GWT/Thalamus selects or keeps alternatives alive;
6. deterministic validation decides whether anything enters MiniUnifiedDB or the effect path.

The scheduler may time-slice more logical lanes than can execute simultaneously. A shared-weight topology can have one resident checkpoint with many independent lane states.

## Capacity law for the 4-core / 16-GB target

The owner-provided KVM4 target is a deployment target, not current runtime evidence. No fixed lane count is canonical before exact measurement.

The first deployment calibration must measure at least:

- exact checkpoint/tokenizer/runtime identity;
- one-time resident shared-weight RSS;
- incremental RSS per additional logical lane under the chosen context/KV budget;
- CPU tokens/s for admitted concurrent inference lanes;
- latency degradation and scheduler overhead;
- MiniUnifiedDB/J-Space/GWT overhead;
- restart/recovery behavior.

Then compute:

```text
available_ram = host_ram - safety_reserve - measured_shared_weight_rss
logical_lane_capacity = floor(available_ram / measured_incremental_lane_rss)
active_inference = min(logical_lane_capacity, cpu_cores, measured_cpu_parallel_ceiling)
```

The safety reserve is itself measured/configured; it is not silently hardcoded as truth. A replicated-weight topology is allowed only when exact measurements show it is better. Shared immutable weights are preferred because the owner's goal is the maximum useful number of ~0.8B modules under fixed RAM, not the maximum number of duplicate weight copies.

## Hyperposition specialization

Lanes may be assigned temporary cognitive roles such as hypothesis branch, counterhypothesis branch, falsifier search, evidence reconciliation, simulation/world rollout, code-repair candidate, adversarial reviewer, or method-memory candidate. These are **packet roles**, not permanent personalities. Role state belongs to the active turn/episode/generation and is either discarded or explicitly summarized/validated into MiniUnifiedDB.

## Free-LLM/token fundus

Free external LLMs may feed the HCU as bounded candidate research inputs or branch proposals. They do not become HCU modules merely because they are available and they do not gain canonical state/effect authority.

- Together remains forbidden under current control.
- provider 402 is a hard stop;
- provider 429 causes provider-wide backoff, not key rotation;
- secrets remain outside prompts/source/receipts;
- external candidates re-enter through the same validation/provenance boundary.

## Fail-closed capacity claims

A manifest may name the 4-core/16-GB/200-GB/16-TB owner target while leaving lane counts unresolved. It may not assert a numeric resident/active lane count until measured model/runtime memory and CPU evidence are bound.

This blocks the false-green class: "There are 16 GB, therefore N copies of a 0.8B model fit." Parameter count alone does not determine runtime RSS, KV/cache cost, allocator fragmentation, runtime overhead, quantization format, mmap sharing, or useful parallel throughput.

## Acceptance ladder

1. **SOURCE CONTRACT** — validator + profile + package integration.
2. **MECHANISM SUPPORT** — deterministic synthetic allocator tests and poison cases.
3. **EXACT MODEL CALIBRATION** — exact admitted ~0.8B bytes/runtime measured in authorized isolated execution.
4. **HCU RUNTIME EVIDENCE** — measured lane scaling, scheduler behavior, J-Space/GWT integration.
5. **TARGET VPS DEPLOYMENT** — only when separately authorized; deployment data does not retroactively replace sandbox acceptance evidence.

Whole Mini Entity acceptance remains separate.
