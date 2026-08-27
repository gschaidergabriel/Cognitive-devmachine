# Android Secondary Research Protocol

## Role

Android is a permanent secondary cross-cutting research arm of FRANK/RAE. Linux remains the reference platform. Android exists to test edge feasibility and to turn constrained hardware/runtime conditions into general efficiency evidence.

The governing contract is `research_entity/global/ANDROID_SECONDARY_RESEARCH_ARM_CONTRACT.md`.

## Mandatory boot

1. Verify canonical RAE state and actor identity.
2. Run `tools/android_research_preflight.py` to retrieve all eight authoritative scientific branches using the coverage-first mesh.
3. Load the newest Android run, open Android hypotheses, negative results and device evidence.
4. Separate Android-specific questions from potentially generalizable efficiency questions.
5. Build a quota-aware experiment plan before consuming any Firebase Test Lab device invocation.

## Experiment ladder

Use the cheapest layer capable of falsifying the claim:

0. Static/compiler/parser/schema tests in CI.
1. JVM/native host differential tests where semantics are platform-neutral.
2. Android APK build/install/instrumentation on one virtual ARM device.
3. Cross-version/ABI virtual-device differential.
4. On-device model-runtime test with a small model.
5. Target Qwen-class 4B quantized inference.
6. Physical Android device only for hardware-dependent questions such as GPU/NPU/Vulkan, thermals, battery, realistic memory pressure or vendor fragmentation.

Do not spend higher-layer quota when a lower layer already falsifies the hypothesis.

## Core research clusters

### Clay / ClayCode
- semantic equivalence between Linux and Android lowerings;
- typed collection semantics and deterministic rejection behavior;
- parser/interpreter/compiler size, allocation and execution cost;
- serialization density and reader-rail cost;
- safe-effect/authority behavior under mobile lifecycle interruption.

### FRANK runtime
- minimum viable organ set on Android;
- same-process versus IPC costs;
- startup/boot ordering and snapshot restore;
- memory ceilings and low-memory recovery;
- Linux-vs-Android behavioral equivalence.

### GWT
- candidate/WorkspaceEpisode representation cost;
- broadcast/projection/re-entry bandwidth and allocation pressure;
- whether bounded workspace capacity improves edge efficiency without changing task behavior;
- timing changes that could alter causal stage ordering.

### ClayGraph
- sparse activation and Assembly memory cost;
- graph traversal escalation cost;
- immutable epoch/replay behavior under Android process death;
- compact relation/index representations.

### UnifiedDB
- SQLite/embedded-store suitability;
- canonical event replay under process kill/restart;
- query/collection equivalence;
- write amplification, checkpointing and storage pressure;
- derived-sidecar rebuild cost.

### Hyperposition
- topology placement under tight memory/latency budgets;
- colocated versus separated component boundaries;
- higher-order relation representation cost.

### Emergenz
- only functional/causal instrumentation that can be meaningfully reproduced on Android;
- never infer emergence merely from device-local recurrence or persistence.

### General efficiency
- prefill/decode/end-to-end latency decomposition;
- peak and steady-state RAM;
- allocation/copy counts when observable;
- context/KV pressure;
- cold start versus warm state;
- sustained-load thermal behavior on physical devices;
- quantization and quality tradeoffs.

## Quota policy

Default autonomous cycle ceiling:
- virtual Firebase Test Lab invocations: 2-3 maximum;
- physical Firebase Test Lab invocations: 0 by default, at most 1 when hardware dependence is central;
- bundle multiple orthogonal instrumentation assertions per device invocation;
- keep enough quota available for concurrent workers.

A build failure or API/configuration failure that prevents device allocation does not count as scientific device evidence and should be repaired before spending another device invocation.

## Required measurements

Whenever applicable record:
- platform/device/model/Android/API/ABI;
- virtual versus physical;
- runtime/backend and version;
- model identity and quantization;
- input/context size;
- first-token/prefill latency;
- decode throughput;
- total task latency;
- peak/steady memory when measurable;
- correctness/semantic equivalence;
- crash/process-death/replay behavior;
- Test Lab matrix/result identifiers;
- exact code/artifact commit;
- quota consumed.

## Bidirectional write-back

Every full Android run writes `BRANCH_FEEDBACK_MANIFEST.json` with one receipt for each authoritative scientific branch. Each material feedback item must also be compiled into a branch-addressed Knowledge Micro-Packet under the corresponding branch namespace.

Classification:
- `ANDROID_LOCAL`: device/platform-specific; primarily retained in Android.
- `GENERALIZABLE_CANDIDATE`: mechanism plausibly relevant beyond Android; route to affected branches as an OPEN hypothesis/constraint.
- `CROSS_PLATFORM_REPLICATED`: same mechanism reproduced on Linux and Android under matched semantics; stronger portability evidence, still preserving shared implementation ancestry.

No Android result may silently become a canonical Linux architecture claim without the main branch's normal evidence/promotion process.

## Closing rule

Android research succeeds when it either:
1. demonstrates useful edge feasibility, or
2. exposes a constraint that improves the general FRANK architecture.

A negative Android result is valuable if it identifies a representation, runtime boundary or resource assumption that should be changed or explicitly kept Linux-only.
