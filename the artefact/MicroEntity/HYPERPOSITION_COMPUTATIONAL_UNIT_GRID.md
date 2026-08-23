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

The HCU borrows the useful structural idea from SIMT/GPU execution without pretending a CPU VPS is a GPU. One packet template may fan out across Hyperposition branches; each lane is generation-fenced; results are candidate-only; GWT/Thalamus selects or preserves alternatives; deterministic validation controls MiniUnifiedDB/effect admission.

The scheduler may time-slice more logical lanes than can execute simultaneously. A shared-weight topology can have one resident checkpoint with many independent lane states.

## Capacity law for the 4-core / 16-GB target

The owner-provided KVM4 target is a deployment target, not current runtime evidence. No fixed lane count is canonical before exact measurement. Measure exact model/runtime RSS, incremental lane/KV cost and CPU scaling, then compute maximum safe logical lanes and active inference parallelism. Shared immutable weights are preferred; replicated weights require measured evidence.

## Hyperposition specialization

Lanes may temporarily represent hypothesis, counterhypothesis, falsifier, simulation, reconciliation, code-repair, adversarial-review or method-memory branches. These are packet roles, not permanent personalities; durable results require explicit validation into MiniUnifiedDB.

## Free-LLM/token fundus

Free external LLMs may feed bounded candidate research inputs. They gain no canonical state/effect authority. Together remains forbidden; 402 hard-stops; 429 triggers provider-wide backoff; secrets stay outside prompts/source/receipts.

## Fail-closed capacity claims

A manifest may name the 4-core/16-GB/200-GB/16-TB owner target while keeping lane counts unresolved. Numeric resident/active capacity is forbidden until exact measurements are bound. Parameter count alone does not establish runtime RSS, KV/cache cost, quantization overhead or useful parallel throughput.

## Acceptance ladder

1. source contract;
2. deterministic mechanism support;
3. exact ~0.8B model/runtime calibration in authorized isolated execution;
4. HCU runtime evidence with J-Space/GWT;
5. target VPS deployment only when separately authorized.

Whole Mini Entity acceptance remains separate.
