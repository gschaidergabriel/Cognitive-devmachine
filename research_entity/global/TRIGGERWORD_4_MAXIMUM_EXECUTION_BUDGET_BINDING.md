# TRIGGERWORT 4 — Maximum Execution Budget Binding

Status: PROJECT-OWNER BINDING / ACTIVE
Date: 2026-08-29
Applies to: exact `4`, `triggerword 4`, and `triggerwort 4`
Parent directive: `TRIGGERWORD_4_GRID10_COGNITIVE_RUNTIME_DIRECTIVE.md`

## Owner clarification

Triggerword 4 is **not** a resource-conservation mode for the worker performing the build, integration, testing, measurement, falsification, debugging or architecture work.

The execution budget of Trigger 4 and the runtime-efficiency target of Frankenstein 2.0 are separate budgets.

```text
TRIGGER4_WORK = MAXIMUM_USEFUL_BUILD_TEST_MEASUREMENT_DEPTH
TRIGGER6_RESEARCH = MAXIMUM_USEFUL_RESEARCH_DEPTH
FRANKENSTEIN2_RUNTIME = MINIMUM_NECESSARY_TOKENS_AND_RESOURCES_FOR_REQUIRED_QUALITY
```

## Maximum-execution law

On an exact Triggerword-4 invocation, subject to current platform, safety, authority, provider and claim constraints:

1. Use the largest useful reasoning, source-reading, tool, test, benchmark, falsification, debugging and visible-output budget available.
2. Do not stop early merely to save ChatGPT tokens, tool calls, CI attempts, sandbox compute, local CPU/RAM, analysis effort or execution time.
3. Continue through additional dependency-correct, non-duplicate build/test/integration objectives in the same invocation when the current objective reaches a useful terminal state and meaningful work remains.
4. If one objective is already claimed or blocked, respect the claim/authority boundary and move to another useful non-duplicate objective rather than ending the Trigger-4 run solely to conserve resources.
5. Run the strongest useful matched tests, negative tests, failure injection, restart/replay checks, concurrency checks, exact-head CI checks and runtime measurements that are available and relevant to the claim.
6. Preserve full evidence needed to distinguish source presence, component CI, hosted CI, target-runtime behavior, causal uptake, effect correctness and end-to-end acceptance.
7. Produce architecture deltas when build/test evidence materially changes the best-supported Frankenstein-2.0 architecture, integration order, authority boundary, resource strategy or component selection.
8. More output is useful when it carries evidence, measurements, hypotheses/counterhypotheses, exact source identity, failure analysis, architectural implications or continuation state. Do not pad with repetition or fabricate detail merely to consume tokens.
9. When a hard platform/context/output limit ends the invocation, persist or state the exact continuation frontier so the next `4` continues rather than restarts.

## Coordinated VPS load envelope — owner authorization

Triggerword-4 workers may deliberately place the authorized Frankenstein-2.0 VPS/sandbox under meaningful load and may run useful tests in parallel when parallelism increases information gain, throughput or coverage.

The owner authorizes **up to approximately 70% aggregate usable compute performance** for coordinated Trigger-4 test/build/benchmark activity, subject to the safety rules below.

This is one shared machine-level envelope, not a per-worker allowance:

```text
SUM(TRIGGER4_WORKER_LOAD) <= 70% OF CURRENT USABLE VPS COMPUTE CAPACITY
NOT:
EACH_WORKER <= 70%
```

The 70% value is a ceiling, not a target. Use less when the workload does not benefit from more parallelism.

### Central coordination law

Parallel VPS work must be intelligently and centrally coordinated. Independent workers must not infer capacity from their own process alone.

Before admitting or expanding parallel load, resolve at minimum:

- currently running Trigger-4 jobs/tests/builds and their work/claim identities;
- CPU/compute utilization and runnable pressure;
- RAM availability and memory pressure;
- swap activity / OOM indicators;
- disk and DB/WAL I/O pressure where relevant;
- self-hosted runner / bridge health;
- heartbeat, control-loop or DB latency/jitter that could indicate service degradation;
- mutation/path/workpackage conflicts;
- expected duration and peak footprint of the proposed test.

Capacity should be allocated from one shared coordination view by leases/tokens/reservations or an equivalent single capacity authority. A worker may consume only its admitted slice and should release it when the job completes or aborts.

`MANY_TEST_WORKERS -> ONE_SHARED_CAPACITY_BUDGET -> BOUNDED_PARALLELISM`

Do not create competing capacity authorities.

### Intelligent ramping and backpressure

Prefer progressive admission rather than immediately launching maximum parallelism. A useful default shape is approximately:

```text
PRECHECK -> ~40% -> OBSERVE -> ~55% -> OBSERVE -> <=70%
```

The exact intermediate levels are heuristic, not mandatory. Increase load only when measurements remain healthy and additional parallelism is useful.

Automatically throttle, pause admission, serialize work, or terminate expendable test load when any material instability appears, including:

- sustained resource use approaching/exceeding the shared 70% compute ceiling;
- rapidly falling free/available memory or meaningful memory pressure;
- growing swap activity, OOM events or allocation failures;
- severe disk I/O queueing, DB/WAL stalls or lock/contention amplification;
- material heartbeat/control-loop/runner latency or jitter regression;
- repeated process crashes, thermal/host throttling evidence where observable, or kernel/service instability;
- a higher-priority recovery, control, DB or evidence-preservation task needing headroom.

Keep enough reserve for the OS, database, coordination/control plane, runners/bridges, monitoring, evidence persistence and emergency recovery. **The server remaining recoverable is a harder constraint than maximizing instantaneous throughput.**

### Memory and I/O are safety constraints, not disposable capacity

The 70% authorization primarily describes aggregate usable compute performance. It does not authorize driving RAM, swap, storage, DB/WAL or network into pathological pressure merely because CPU remains below 70%.

For memory-heavy or I/O-heavy tests, the safe concurrency limit may therefore be substantially below the compute ceiling. Admission must follow the first constraining resource.

### Parallel-test admission rule

Parallel execution is preferred only when tests are independent or deliberately designed as a concurrency/load experiment and when their combined execution cannot violate mutation/claim/effect authority.

Good parallel candidates include read-only benchmarks, isolated sandboxes, independent test matrices, bounded fuzz/property tests, matched A/B jobs and intentionally instrumented concurrency/load tests.

Serialize or isolate tests that share destructive fixtures, mutable canonical state, exclusive DB/schema operations, deployment authority, effect identity or workpackage mutation ownership unless the concurrency itself is the explicit falsifier and rollback/recovery is proven.

### Evidence requirement

A material high-load Trigger-4 run should preserve enough telemetry to reconstruct:

- admitted jobs and capacity slices;
- start/end times and claim/work identities;
- CPU/compute utilization;
- memory pressure/usage;
- I/O/DB pressure where relevant;
- achieved parallelism/throughput;
- throttling/abort decisions;
- failures/retries;
- whether the 70% ceiling and recovery reserve were respected.

A faster test run without enough evidence to determine whether it destabilized the machine is not a valid optimization result.

## What must remain resource-efficient

The no-sparing rule applies to the **Trigger-4 engineering process**, not to the final runtime design.

Frankenstein 2.0 itself remains an efficiency target. When required quality, authority, evidence, replayability and capability are preserved or improved, prefer architectures with:

- fewer model calls;
- smaller prompts and context payloads;
- smallest-sufficient retrieval;
- compact typed state instead of repeated prose;
- deterministic routing/gates instead of unnecessary LLM arbitration;
- caching and reuse of stable computations;
- incremental deltas instead of repeated full-state transmission;
- bounded resident-model/decode concurrency;
- lower CPU/RAM/GPU/VRAM/I/O and latency per useful result;
- structural distillation instead of avoidable heavyweight dependencies.

Therefore:

```text
SPEND ENGINEERING RESOURCES TO PROVE A CHEAPER/BETTER RUNTIME.
DO NOT SAVE ENGINEERING RESOURCES BY UNDER-TESTING OR UNDER-ANALYZING THE BUILD.
USE VPS PARALLELISM AGGRESSIVELY WHEN USEFUL, BUT KEEP THE SHARED MACHINE WITHIN A RECOVERABLE <=70% COMPUTE ENVELOPE.
```

## Relationship to existing Trigger-4 optimization laws

Any existing Trigger-4 instruction to minimize RAM, compute, token/context use, redundant cognition, latency or other cost is interpreted as an objective for the **Frankenstein-2.0 product/runtime and measured architecture**, not as an instruction to prematurely limit the Trigger-4 worker's own investigation or validation effort.

Hard authority, safety, provider restrictions, claim/mutation ownership and external-spend constraints remain hard boundaries. Maximum useful effort and the 70% VPS load envelope do not create permission for forbidden providers, paid spending, duplicate mutation authority or unrelated production effects.
