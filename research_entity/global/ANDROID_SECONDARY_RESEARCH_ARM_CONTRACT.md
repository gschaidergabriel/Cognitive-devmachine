# Android Secondary Research Arm Contract

**Status:** PROJECT-OWNER ARCHITECTURE / RESEARCH DIRECTIVE  
**Applies to:** all FRANK/RAE scientific branches and Android experiments  
**Primary platform:** Linux  
**Secondary research/deployment platform:** Android

## Fixed role

FRANK is designed and evaluated primarily as a Linux-native system. Android does not replace Linux as the reference platform and does not become a peer architecture authority.

Android is a permanent secondary, cross-cutting research arm because Qwen-class 4B execution and compact Clay/ClayCode runtime components are increasingly feasible on capable Android hardware. The arm is used to expose efficiency, memory, latency, portability, thermal, storage, compiler/runtime, security and cognitive-substrate constraints that may be hidden on desktop/server Linux.

The architectural rule is:

> Linux remains the reference target; Android is an adversarial efficiency and edge-runtime projection of the same Clay-native semantics.

## Bidirectional mesh rule

Android MUST NOT become an isolated mobile silo.

Every Android research run MUST retrieve current relevant material from all authoritative scientific branches:

- clay
- frank
- gwt
- emergenz
- claycode
- hyperposition
- claygraph
- unifieddb

Android uses the full-mesh interconnect preflight through `tools/android_research_preflight.py`, which reuses the coverage-first fusion mesh without promoting Android to a ninth peer branch.

Every durable Android result MUST emit explicit feedback to every materially affected scientific branch. For branches with no material delta, write an explicit `NO_CHANGE` receipt when a full Android research run is closed.

Feedback must be materialized as branch-addressed Topic/Knowledge Micro-Packets so existing branch preflights retrieve Android-derived constraints automatically.

## Result classification

Android results are classified into two channels.

### A. Android-specific findings

Examples:
- Android API/ABI compatibility;
- lifecycle/background restrictions;
- device-specific GPU/NPU/Vulkan behavior;
- package/install constraints;
- Android memory pressure;
- mobile thermal throttling;
- battery/energy behavior;
- device fragmentation.

These remain primarily in the Android arm, with cross-links to affected branches.

### B. Generalizable findings

A result MUST be emitted beyond Android when it reveals a mechanism that plausibly applies to FRANK generally, including:

- Clay/ClayCode representation density or parsing cost;
- memory layout or allocation pressure;
- context/KV/cache pressure;
- compiler/lowering defects;
- serialization or IPC overhead;
- graph/query/collection topology effects;
- GWT candidate/projection/re-entry costs;
- latency decomposition;
- deterministic authority/safety boundaries;
- state replay/idempotence problems;
- model/runtime quantization tradeoffs;
- hidden dependencies or resource coupling.

Generalizable findings are routed to all affected branches as normal research evidence with Android provenance. Android evidence does not become Linux evidence merely through routing; target-substrate replication remains required for strong Linux claims.

## Efficiency role

Android is a deliberate constrained-environment laboratory. Constraints are treated as information, not merely deployment problems.

Android experiments should preferentially answer questions such as:

- Which Clay structures are unnecessarily expensive?
- Which runtime boundaries allocate/copy too much?
- Which state can be reconstructed instead of retained?
- Which GWT/ClayGraph/UnifiedDB paths dominate memory or latency?
- Which semantics survive aggressive compression/quantization?
- Which abstractions are expensive only because the implementation is poor versus intrinsically expensive?
- Which optimizations improve both Android and Linux?

When an Android optimization plausibly generalizes, it enters the relevant main research branch as an efficiency hypothesis and must be independently checked on Linux before architecture promotion.

## Quota discipline

Firebase Test Lab and other scarce remote-device quotas are shared research resources.

Android runs MUST maximize information per device invocation:

1. bundle multiple orthogonal assertions/instrumentation tests into one APK/test matrix where causal attribution remains valid;
2. perform build/parser/simulation/fuzz tests in free CI/sandbox first;
3. use virtual Android devices before scarce physical devices unless hardware effects are the target;
4. reserve physical-device quota for thermal, GPU/NPU, real-memory, battery, hardware-driver or device-fragmentation questions;
5. avoid rerunning an unchanged device experiment merely to obtain more samples when cheaper CI controls can diagnose the failure;
6. record consumed/remaining estimated quota in each Android run manifest.

Default per autonomous Android research cycle: consume no more than 2-3 virtual Test Lab device invocations and at most 1 physical device invocation unless a user explicitly authorizes a larger campaign or unused quota would otherwise expire.

## Required Android run outputs

A full Android research run should materialize:

- `INTERCONNECT_MANIFEST.json`
- `ANDROID_EXPERIMENT_PLAN.json`
- `DEVICE_MATRIX.json`
- `EXPERIMENT_RESULTS.json`
- `EFFICIENCY_DELTA.md`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `RUN_MANIFEST.json`
- `FINAL_REPORT.md`

The run manifest must distinguish CI/build evidence, virtual-device evidence, physical-device evidence and inference from each.

## Scientific boundaries

- Android feasibility does not prove Linux optimality.
- Virtual-device performance does not establish physical-device performance.
- One phone model does not establish Android-wide behavior.
- Qwen-class 4B feasibility does not establish that the complete FRANK architecture fits or performs acceptably on-device.
- Better token/sec alone is not sufficient; prefill, decode, end-to-end latency, memory, energy/thermal behavior and task quality must be separated.
- Cross-branch reuse of one Android experiment is shared ancestry, not independent replication.
- Android/GWT/emergence results do not establish phenomenal consciousness.
