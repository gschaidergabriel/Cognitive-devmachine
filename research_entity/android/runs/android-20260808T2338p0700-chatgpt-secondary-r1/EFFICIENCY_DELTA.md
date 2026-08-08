# Android R1 — Efficiency Delta

**Run:** `android-20260808T2338p0700-chatgpt-secondary-r1`  
**Role:** secondary constrained-runtime research arm  
**Reference platform:** Linux

## What R1 actually established

The remote Android research loop is operational without the user's local system:

`GitHub Actions -> service-account auth -> Gradle Android build -> Firebase Test Lab ARM virtual device -> instrumentation receipts`.

One Android 35 smoke invocation passed 2/2 tests. A bundled Android 35 + Android 30 matrix then passed 9/9 tests per device, 18/18 total.

This is useful efficiency infrastructure because one device invocation can carry many orthogonal deterministic checks. The R1 campaign deliberately stopped after three virtual device invocations and used zero physical devices.

## Generalizable efficiency candidates

### 1. Constrained-runtime testing can expose architecture cost early

Android should be treated as an adversarial resource envelope. If a Clay/ClayCode/FRANK representation requires excessive retained state, copying, serialization or context, Android is likely to expose it earlier than a roomy Linux server.

This is an OPEN generalizable method claim, not yet a measured Linux/Android performance result.

### 2. Compact semantic surfaces deserve direct cost measurement

The constructed compact Clay-like program used fewer source bytes than the verbose JSON-like control in the test harness. That is only a byte-density sanity check. It does **not** establish lower model tokens, lower parser cost, lower latency or better reasoning.

Required next evidence: matched parser/runtime and later target-Qwen measurements of bytes/tokens, prefill, decode, total latency, allocation/RAM and task correctness.

### 3. Deterministic semantic checks are cheap enough to bundle

Type behavior, rejection behavior, overflow, collection distinctions, replay sanity and authority-boundary controls were bundled into the same two-device matrix. This supports using CI/device quota for discriminating platform effects instead of spending one matrix per invariant.

### 4. Android version changes did not disturb the selected constructed invariants

The same nine tests passed on Android 30 and Android 35 virtual ARM runtimes. This is limited portability evidence for the constructed Java harness only. It is not full ClayCode or FRANK portability evidence.

## Important non-results

R1 did **not** measure:

- Qwen 4B inference;
- first-token/prefill latency;
- decode throughput;
- context/KV memory;
- peak or steady-state RAM;
- IPC/copy counts;
- real SQLite/UnifiedDB persistence;
- ClayGraph traversal;
- GWT stage costs;
- battery or thermal behavior;
- GPU/NPU/Vulkan behavior;
- physical-device fragmentation.

No claim about those quantities is promoted.

## Highest-information next sequence

1. Package a quantized Qwen-class 4B-capable Android runtime in CI without spending a device run.
2. Only after packaging succeeds, use one virtual ARM run to prove model load/inference and collect model/runtime identity.
3. Bundle context-length / bounded-Clay-view conditions into the next device matrix to measure prefill + decode + total latency and memory where observable.
4. Add same corpus on Linux to separate Android-local constraints from general FRANK efficiency mechanisms.
5. Reserve physical-device quota for sustained thermal, real memory pressure, battery and hardware-accelerator questions.

## Routing

Android-local details remain in this arm. Any mechanism that plausibly generalizes is emitted as an OPEN candidate to the affected main branches and requires their normal evidence/promotion process. Shared Android evidence reused by multiple branches remains one ancestry, not independent replication.
