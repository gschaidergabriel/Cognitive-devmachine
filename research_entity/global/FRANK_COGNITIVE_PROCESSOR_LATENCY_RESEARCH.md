# FRANK COGNITIVE PROCESSOR LATENCY RESEARCH

Status: ACTIVE_RESEARCH_TARGET
Date: 2026-08-09
Actor origin: chatgpt-secondary
Reference: `gschaidergabriel/frankv0.1:architecture/FRANK_COGNITIVE_PROCESSOR_LATENCY_CONTRACT.md`

## Research question

Can Frank shift enough cognition from autoregressive 4B inference into incremental Clay/UnifiedDB computation that interactive latency becomes bounded primarily by relevant-state lookup plus short 4B realization, rather than total memory/world-model complexity?

## Primary hypothesis

For recurrent and structurally answerable tasks, a continuously maintained semantic substrate can reduce end-to-end latency by:

- shrinking model prompt/context;
- reducing generated reasoning tokens;
- bypassing the model for deterministic responses;
- converting repeated remote reasoning into durable local backflow;
- avoiding per-prompt reconstruction of capability/file/dependency/world-model structure.

## Counterhypothesis

Precomputation can worsen latency if affordance closure, graph-like propagation or view invalidation scales combinatorially or causes high write amplification/cache churn.

## Required matched conditions

Benchmark at least:

A. raw-memory/RAG -> 4B reasoning;
B. separate ClayGraph retrieval -> 4B;
C. UnifiedDB dynamic view -> 4B;
D. UnifiedDB Answer Capsule -> 4B realization-only;
E. UnifiedDB deterministic direct response with 4B bypass where valid;
F. remote Claude/ChatGPT execution followed by repeated local query after cognitive backflow.

## Metrics

Per turn record:

- total state size;
- relevant neighborhood size;
- invalidated packet/relation count;
- incremental materialization time;
- query/index time;
- relation/affordance propagation time;
- GWT/view assembly time;
- Answer Capsule byte/token size;
- 4B prompt-eval latency;
- time-to-first-token;
- decode tokens/s;
- generated reasoning/output tokens;
- total end-to-end latency;
- peak RAM;
- CPU/GPU utilization;
- cache hit/miss;
- remote call count/latency;
- correctness/task success;
- missed-affordance rate;
- stale-view failures.

## Scaling experiments

Hold task relevance approximately constant while increasing total UnifiedDB size by orders of magnitude.

Desired property:

`query latency ~ f(relevant neighborhood)`

not

`query latency ~ f(total memory size)`.

Measure median, p95 and p99.

## Update-path experiments

Measure cost of:

- single packet update;
- connector join/leave;
- device join/leave;
- permission change;
- file move/supersession;
- capability verification/revocation;
- large peer cognitive-backflow merge;
- high-fanout semantic correction.

Verify incremental invalidation against full recomputation.

## 4B cognition-ablation experiment

For matched user prompts compare:

1. 4B derives implications from minimally processed memory;
2. 4B receives affordance field only;
3. 4B receives full Answer Capsule;
4. direct deterministic rendering when the answer is fully resolved.

Measure latency and accuracy separately.

## Real Andreas longitudinal benchmark

Cluster real Andreas usecases and repeatedly measure whether frequently recurring workflows migrate from expensive L2/L3 cognition toward L1/L0 through durable semantic learning/backflow.

Important signals:

- repeat-task latency curve over time;
- correction recurrence;
- peer-call avoidance after prior learning;
- answer quality after compression;
- user-visible delay;
- changed capability/body state response time.

## Promotion requirements

Do not promote latency claims until measured on actual project hardware.

Engineering targets such as `<20 ms median / <50 ms p95 pre-4B cognitive preparation` are hypotheses/targets only.

Promotion requires matched reproducible traces and no material accuracy/authority regression.

## Architectural implication

If supported, UnifiedDB should be treated as a cognitive processing substrate with incremental materialized views, while the Clay-native 4B becomes primarily a bounded generative/inference endpoint over preassembled state.
