<!-- RAE_META
{"packet_id":"KMP-ANDROID-R1-FEEDBACK-FRANK","title":"KMP — Android R1 -> FRANK feedback","domains":["frank"],"claim_status_hint":"CURRENT"}
RAE_META -->

# KMP — Android R1 -> FRANK feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** frank  
**Reference platform:** Linux  
**Evidence class:** live Firebase Test Lab virtual ARM + constructed semantic harness

## R1 evidence receipt

The remote lane `GitHub Actions -> Firebase auth -> APK build -> ARM Test Lab` is live. R1 consumed three virtual device invocations and zero physical devices, then stopped at its quota boundary. Android 35 passed 2/2 smoke checks; a bundled Android 35 + Android 30 matrix passed 18/18 controls total. Across R1 there were 20/20 successful instrumentation test executions.

This demonstrates a usable edge research substrate and selected deterministic semantics only. It does **not** establish that complete FRANK or Qwen-class 4B fits or performs acceptably on Android.

## Generalizable candidate

FRANK remains Linux-primary. Android should expose memory, startup, IPC/copy, lifecycle, quantization, scheduling and resource-pressure assumptions before they become hidden architecture costs. Any optimization inferred from Android remains OPEN until matched Linux testing.

## Retrieval/emit rule

FRANK runs MUST retrieve this Android feedback. Android runs MUST retrieve current FRANK architecture and preserve the Linux-primary boundary. Shared R1 evidence routed into other branches is not independent replication.

## Next FRANK-facing experiments

- package and load a quantized target Qwen-class 4B runtime after CI-only integration succeeds;
- minimum viable FRANK organ set and memory ceiling;
- cold boot, snapshot reconstruction and process-death recovery;
- prefill, decode, total latency and memory separately rather than tokens/sec alone;
- matched Linux-vs-Android differential for each proposed general optimization.
