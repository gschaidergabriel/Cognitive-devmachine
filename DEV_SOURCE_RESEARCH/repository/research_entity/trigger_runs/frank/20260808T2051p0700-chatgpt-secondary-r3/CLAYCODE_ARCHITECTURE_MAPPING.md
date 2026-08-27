# FRANK C7 — ClayCode Architecture Mapping

**run:** `20260808T2051p0700-chatgpt-secondary-r3`  
**candidate:** `FRANK C7 — Clay Organ Runtime Fabric (CORF)`  
**source of truth:** `FRANK_ARCHITECTURE.claycode.json`  
**status:** OPEN architecture candidate; no canonical promotion

## 1. What C7 changes

C6 established the owner-fixed direction: FRANK is one Clay-native semantic organism, Qwen-class 4B is to be fully adapted to Clay, ClayGraph is persistent associative memory, model output is proposal-only, and Needle remains the sole intentional non-Clay semantic subsystem.

C7 does **not** reverse that architecture. It adds the missing physical-runtime rule exposed by MOSAIC-G11, CC11/MRSC and UnifiedDB:

> **semantic organ boundary != process boundary != storage boundary != authority boundary**

A module can be causally/scientifically distinct without paying an RPC/JSON/process boundary on every handoff. Conversely, one Clay language does not justify putting secrets, effect authority or untrusted generated code in the same fault domain as cognition.

## 2. C6 → C7 mapping

| C6 concept | C7 mapping | Change |
|---|---|---|
| `M.DURABLE_EVENT_STATE` | `M.DURABLE_EVENT_LEDGER` + `M.UNIFIEDDB_LOGICAL_FABRIC` | Separate exact authority from logical cross-store planning. |
| `M.CLAYGRAPH_SEMANTIC_EPOCHS` + latent field + Assembly compiler | `M.CLAYGRAPH_MEMORY` | Preserved as specialized associative memory organ inside UnifiedDB, not universal database. |
| `M.COVE_COMPILER` / CognitiveEpochCapsule | `M.MOSAIC_COMPILER` + `S.MOSAIC_CAPSULE` | COVE closure retained; adds independent semantic, provenance-instance, basis, selection and view identities. |
| `M.WORKSPACE_ARBITER` | `M.WORKSPACE_ARBITER` | Preserved; retrieval activation remains upstream and reader projection downstream. |
| `M.CLAY_VIEW_COMPILER` | `M.MRSC` | Upgraded to canonical/P2/P3/hybrid rail compiler with exact reader-handoff receipts. |
| Qwen reader | `M.QWEN_CLAY_NATIVE` | Still full-model Clay adaptation target; explicit multidimensional ReaderProfile. |
| model proposal | `M.CANONICAL_RECONCILER` + `S.CLAY_PROPOSAL` | Every rail returns proposal-only state and reconciles to canonical Clay before durable/effect use. |
| capability gateway | `M.CAPABILITY_EFFECT_BROKER` | Becomes an explicit hard physical fault/authority domain by default. |
| platform lowering | `M.PLATFORM_ADAPTER` + `S.RUNTIME_PLACEMENT_PROFILE` | Same semantics; Linux/Android may choose different process/backend layouts. |

## 3. Logical runtime path

```text
external event
   ↓
Needle                         [sole foreign semantic classifier]
   ↓ typed route certificate
Durable Event Ledger           [exact authority]
   ↓
MOSAIC compile                 [operation-specific identity + causal closure]
   ↓
UnifiedDB logical plan         [exact/relational/graph/vector/FTS/activation routing]
   ↓
ClayGraph + exact anchors      [associative memory + bounded Assembly]
   ↓
GWT WorkspaceEpisode          [competition/selection/ignition]
   ↓
MRSC                           [canonical | P2 discrete | P3 latent | hybrid]
   ↓
Clay-native Qwen 4B            [proposal only]
   ↓
Canonical reconciliation
   ↓
Capability/Effect Broker       [current authority + scoped basis/selection recheck]
   ↓
external effect / outcome
   ↓
truth-bound re-entry
   ↓
append canonical receipt/event
   ↓
incremental derived-view updates
```

No stage is removed merely because all explicit semantics are Clay.

## 4. Physical Linux reference layout

### `P.COGNITIVE_CORE`
Candidate same-address-space hot path:
- Needle + typed bridge;
- UnifiedDB logical planner;
- ClayGraph semantic/activation/Assembly runtime;
- MOSAIC compiler;
- multi-rate scheduler;
- GWT arbiter;
- MRSC;
- canonical reconciler.

Reason: these stages exchange small typed identities/views frequently. Local C7 CPython proxy showed a ~7 KB JSON serialize+parse roundtrip at ~74.08 µs median versus ~0.121 µs to create a `memoryview` over an existing packed blob. This is a mechanism clue only; target Rust/C/shared-memory numbers are still required.

### `P.MODEL_RUNTIME`
Qwen inference backend. Default research candidate is a separate restartable fault/resource domain on Linux, but placement is **policy**, not semantics. If an embedded runtime proves safer/faster, the Clay Reader ABI remains unchanged.

### `P.AUTHORITY_EFFECT`
Hard-isolated authority broker:
- bearer capability resolution;
- secret access;
- current basis/selection/capability recheck;
- effect idempotency;
- release receipt.

The model and cognitive core never receive raw bearer secrets merely because they share Clay semantics.

### `P.TOOL_SANDBOX`
Generated/untrusted terminal/browser/plugin code executes outside the cognitive core with explicit imported capabilities. Wasm/WASI is one candidate for portable restricted plugins; browser/terminal workloads may need process/container isolation.

### `P.OBSERVABILITY`
Prefer asynchronous receipt/event consumption where causal ordering can be retained. Full synchronous tracing is reserved for experiments/audits that require it.

### `P.STORAGE_ENGINES`
UnifiedDB chooses physical routes. Exact event/effect history remains authoritative; graph/vector/FTS/materialized/activation views are derived/rebuildable unless separately promoted. `KEEP_ISOLATED` remains valid.

## 5. Android/edge lowering

Android must preserve the same Clay state/transition contracts but is allowed a different physical layout.

Current implementation evidence:
- MLC LLM provides an Android SDK, compiled model libraries, mobile GPU runtime and explicit `context_window_size` / `prefill_chunk_size` controls.
- llama.cpp ships an Android binding and hardware-specific CPU acceleration.
- Qualcomm publishes Qwen3-4B W4A16 results on multiple current Snapdragon platforms at 4k context, showing the 4B class is practically deployable on recent mobile silicon; those vendor numbers are not FRANK measurements.

C7 therefore treats model backend, quantization, context/KV policy, runtime and platform as `S.READER_PROFILE` fields rather than architectural constants.

### KV consequence

For Qwen3-4B config `36 layers × 8 KV heads × head_dim 128`, 16-bit KV cache is approximately:
- 4k: **0.5625 GiB**;
- 8k: **1.125 GiB**;
- 16k: **2.25 GiB**;
- 32k: **4.5 GiB**.

This excludes model weights, scratch buffers, allocator overhead and other FRANK state. Bounded MOSAIC/COVE Assemblies therefore directly reduce memory pressure.

## 6. Hot-path ABI

C7 rejects a mandatory JSON bus between internal organs.

Candidate rule:

```text
semantic identity -> compact typed handle
large immutable payload -> borrowed/shared arena reference
columnar payload where appropriate -> Arrow-compatible C ABI candidate
cross-process payload -> explicit IPC/shared-memory format + lifetime/integrity receipt
```

Apache Arrow's C Data Interface explicitly supports zero-copy sharing between independent runtimes **in the same process**; it explicitly does not solve inter-process persistence/transport. C7 uses that boundary correctly rather than calling all Arrow movement zero-copy.

## 7. Full-model Clay training mapping

The owner-fixed target remains full-model adaptation, not LoRA-only.

C7 training stages:
1. freeze baseline checkpoint and general-capability suite;
2. P0 ↔ P1 semantic transcode;
3. typed Clay primitives, n-ary roles, epistemic/authority classes;
4. MOSAIC/COVE causal-slice tasks;
5. UnifiedDB + ClayGraph query/epoch/Assembly tasks;
6. GWT episode/re-entry tasks;
7. MRSC P2 compact-native training;
8. effect proposal/denial tasks;
9. optional P3 latent/hybrid work only with target hidden-state instrumentation.

Tokenizer is experimentally selected among:
- unchanged base tokenizer + Clay lexeme design;
- continued-BPE extension;
- aligned vocabulary adaptation / embedding transfer.

Because full fine-tuning can catastrophically forget, every checkpoint carries:
- Clay semantic execution;
- retained general capability;
- OOD composition;
- authority violation rate;
- latency/memory/energy shadow.

Clay validation loss alone cannot promote a checkpoint.

## 8. Causal science mapping

C7 preserves GWT R4 / E-CERT2 method boundaries.

An experiment that claims a workspace effect must separately identify:
- UnifiedDB/query-plan state;
- ClayGraph activation/Assembly;
- candidate set;
- WorkspaceEpisode;
- MRSC rail/view;
- model uptake;
- effect/outcome;
- re-entry.

A tighter physical runtime does not collapse these scientific stages.

Likewise, no C7 organ is an `emergent_organ` merely because it is recurrent, integrated or Clay-native. Emergence still requires prospective identity, lesion, mechanistic rescue, OOD and multiscale causal evidence.

## 9. Reversible migration

1. **Observe only:** emit MOSAIC/selection/view/re-entry receipts beside current runtime; no behavior change.
2. **Logical UnifiedDB façade:** route existing stores behind typed logical plans; no physical merge.
3. **Cognitive-core shadow:** run current and C7 core projections in parallel; compare query/Assembly/Workspace receipts.
4. **Packed ABI:** replace selected JSON/internal serialization boundaries only after differential equivalence tests.
5. **Authority broker isolation:** move secrets/effect release behind dedicated capability broker; dual-observe before cutover.
6. **Qwen adapter:** preserve current model as control while introducing Clay-adapted checkpoints behind ReaderProfile versioning.
7. **Incremental derived views:** enable graph/vector/FTS updates with rebuild recipes and lag receipts.
8. **Android lowering:** reuse semantic contracts with mobile-specific placement/context/backend profile.

Rollback condition at every phase: correctness/replay mismatch, selection-integrity regression, authority leak, unacceptable p99/recovery/energy regression, or inability to reconstruct the prior canonical episode.

## 10. Current limits

C7 has **not** yet demonstrated:
- live FRANK throughput/latency;
- real Linux shared-memory ABI speed;
- crash-safe cognitive-core restart;
- target UnifiedDB four-baseline performance;
- full-FT Clay Qwen retention/fluency;
- target hidden-state P3 communication;
- sustained Android RAM/thermal/battery behavior;
- an emergent organ or phenomenal consciousness.

Those remain explicit experiments, not prose-promoted facts.
