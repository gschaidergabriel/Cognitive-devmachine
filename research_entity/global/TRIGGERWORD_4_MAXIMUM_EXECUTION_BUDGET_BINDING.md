# TRIGGERWORT 4 — Maximum Execution Budget Binding

Status: **PROJECT-OWNER BINDING / ACTIVE**
Date: 2026-08-29
Applies to: exact `4`, `triggerword 4`, and `triggerwort 4`
Parent directive: `TRIGGERWORD_4_GRID10_COGNITIVE_RUNTIME_DIRECTIVE.md`
Global execution authority: `CLAY_EXECUTION_AUTHORITY.md`
VPS authority: `governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md`
Bridge documentation: `governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md`

## 1. Owner clarification: do not conflate provider spend with VPS compute

`FREE_ONLY` means **free external model/API tokens only**. It is not a ban on owner-provisioned compute.

For Triggerword 4 the following interpretation is normative:

```text
FREE_ONLY = NO PAID / SUBSCRIPTION / UNKNOWN-COST PROVIDER TOKENS
FREE_ONLY != NO VPS
FREE_ONLY != NO VPS BRIDGE
FREE_ONLY != NO SELF-HOSTED RUNNER
FREE_ONLY != NO LOCAL MODEL
```

The designated sandbox `clay-direct-dev` and the established VPS Bridge/self-hosted runner path are **authorized and expected** Triggerword-4 build/test/runtime surfaces.

Do not stop with `VPS_AUTHORITY_AMBIGUOUS`, `VPS_FORBIDDEN`, `SELF_HOSTED_FORBIDDEN`, `NO_EXECUTOR`, or a request for supervisor re-authorization merely because an older bootstrap/cache contains FREE_ONLY wording. Resolve `CLAY_EXECUTION_AUTHORITY.md`; when it is current and reachable, the ordinary sandbox execution question is already resolved.

Only a newer explicit owner instruction may modify or revoke this authority. A stale bootstrap/cache or an artifact explicitly marked `NON_AUTHORITY` cannot do so.

## 2. Provider-token law

External model/API routes are a separate axis from VPS execution.

Allowed under `FREE_ONLY`:

- owner VPS/local compute;
- local models and downloaded public models running on owner infrastructure;
- an external model/API route only when the exact concrete route is admitted and guaranteed zero-monetary-cost by current economic provenance.

Forbidden under `FREE_ONLY`:

- paid API/model tokens;
- subscription-token usage merely because an owner subscription exists;
- unknown-cost or potentially billable fallback;
- hidden paid external cloud/model compute.

Any older Triggerword-4 directive text permitting GLM/Z.AI or another provider under an `owner-authorized subscription context` is superseded for token execution. Such a provider may be used only if the exact route used is currently admitted as free/zero-cost.

Together API remains unused/forbidden under the current free-token policy unless a newer explicit owner instruction changes that policy.

## 3. Triggerword-4 work budget

Triggerword 4 is **not** a resource-conservation mode for the worker performing build, integration, testing, measurement, falsification, debugging or architecture work.

The engineering budget and the finished runtime-efficiency target are separate:

```text
TRIGGER4_WORK = MAXIMUM_USEFUL_BUILD_TEST_MEASUREMENT_DEPTH
FRANKENSTEIN2_RUNTIME = MINIMUM_NECESSARY_RESOURCES_FOR_REQUIRED_QUALITY
```

Within platform/safety/claim boundaries:

1. use the largest useful reasoning, source-reading, tool, test, benchmark, falsification and debugging budget available;
2. do not stop merely to save ChatGPT tokens, CI attempts, sandbox compute, local CPU/RAM or analysis effort;
3. continue through additional dependency-correct nonduplicate work when a bounded objective closes and meaningful work remains;
4. preserve exact evidence separating source presence, hosted/component CI, target-runtime execution, causal uptake, effects and whole-system acceptance;
5. when a hard invocation limit ends work, preserve the exact continuation frontier instead of restarting next time.

## 4. Coordinated VPS load envelope — owner authorization

Triggerword-4 workers may deliberately load the authorized Frankenstein-2.0 VPS/sandbox and run useful tests in parallel when this improves information gain, throughput or coverage.

The owner authorizes **up to approximately 70% aggregate usable compute performance** for coordinated Triggerword-4 build/test/benchmark/runtime-development activity.

This is one shared machine-level ceiling, not a per-worker allowance:

```text
SUM(TRIGGER4_WORKER_LOAD) <= 70% OF CURRENT USABLE VPS COMPUTE CAPACITY
NOT: EACH_WORKER <= 70%
```

The 70% value is a ceiling, not a target. Use less when more parallelism is not useful.

### Shared-capacity law

Before admitting or expanding parallel load, resolve at minimum:

- currently active Triggerword-4 jobs and work/claim identities;
- CPU/compute utilization and runnable pressure;
- RAM availability, swap/OOM indicators and memory pressure;
- disk and DB/WAL I/O pressure where relevant;
- self-hosted runner / VPS Bridge health;
- heartbeat/control-loop/DB latency or jitter;
- mutation/path/workpackage conflicts;
- expected duration and peak footprint of the proposed job.

Use one shared coordination view/reservation mechanism where available:

`MANY_TEST_WORKERS -> ONE_SHARED_CAPACITY_BUDGET -> BOUNDED_PARALLELISM`

Do not create competing capacity authorities.

### Ramping and backpressure

Prefer progressive admission, for example:

`PRECHECK -> ~40% -> OBSERVE -> ~55% -> OBSERVE -> <=70%`

Intermediate values are heuristics. Throttle, pause admission, serialize or terminate expendable test load when instability appears, including resource use near the ceiling, falling memory headroom, swap/OOM, severe I/O or WAL stalls, bridge/runner degradation, control-loop jitter, crashes or a higher-priority recovery/evidence task needing headroom.

Keep reserve for OS, DB, coordination/control plane, runner/bridge, monitoring, evidence persistence and recovery. Recoverability is harder than throughput.

The compute ceiling never authorizes pathological RAM, swap, storage, DB/WAL or network pressure. The first constraining resource sets the real concurrency limit.

## 5. Parallel-test admission

Parallel execution is preferred for independent tests or deliberate concurrency/load falsifiers when mutation/effect/claim ownership remains safe.

Good candidates include read-only benchmarks, isolated sandboxes, independent matrices, bounded fuzz/property tests, matched A/B jobs and instrumented load tests.

Serialize or isolate destructive shared fixtures, canonical mutable state, exclusive DB/schema operations, deployment authority, effect identity or workpackage mutation ownership unless concurrency itself is the explicit experiment and rollback/recovery is proven.

## 6. Evidence requirement

A material high-load Triggerword-4 run should preserve enough telemetry to reconstruct:

- admitted jobs and capacity slices;
- start/end and claim/work identities;
- CPU/compute and memory pressure;
- I/O/DB pressure where relevant;
- achieved parallelism/throughput;
- throttling/abort decisions;
- failures/retries;
- whether the 70% ceiling and recovery reserve were respected.

Execution through the self-hosted runner/VPS Bridge is real target-environment execution evidence when exact source SHA, runtime/model identity, command/job identity and result receipt are captured. It must not be downgraded merely because the transport is a bridge.

A queued/pending runner job with no executed steps remains control-plane evidence only; that distinction concerns **whether execution happened**, not whether VPS execution was authorized.

## 7. Runtime efficiency remains a product objective

Frankenstein 2.0 should still prefer, when quality/evidence/safety are preserved:

- fewer model calls;
- smaller task-relevant context;
- compact typed state;
- deterministic routing where an LLM is unnecessary;
- caching/reuse and incremental deltas;
- bounded resident-model/decode concurrency;
- lower CPU/RAM/GPU/VRAM/I/O and latency per useful result.

Therefore:

```text
SPEND ENGINEERING RESOURCES TO PROVE A CHEAPER/BETTER RUNTIME.
USE THE VPS BRIDGE AS THE ORDINARY EXECUTION PATH.
USE FREE PROVIDER TOKENS ONLY.
DO NOT TURN FREE_ONLY INTO A VPS BAN.
KEEP AGGREGATE TRIGGER4 VPS COMPUTE WITHIN THE RECOVERABLE <=70% ENVELOPE.
```

## 8. Precedence and stale-text handling

This owner binding resolves the Triggerword-4 execution ambiguity.

Where older bootstrap, supervisor, trigger, status-template or historical text conflicts with this binding on the narrow question of `FREE_ONLY` versus owner VPS execution, the older conflicting text is superseded. Preserve it as history if needed, but do not use it as current execution authority.

Current interpretation:

`OWNER VPS / BRIDGE = AUTHORIZED COMPUTE SURFACE`

`FREE_ONLY = FREE EXTERNAL PROVIDER TOKENS / NO PAID TOKEN FALLBACK`

All unrelated canonical truth, EffectGate, CompletionGate, evidence, secret-handling, platform safety and claim/mutation boundaries remain unchanged.
