# KMP — Android R1 -> FRANK feedback

**Status:** CURRENT / ACTIVE / CROSS-BRANCH FEEDBACK  
**Source arm:** Android secondary research arm  
**Target branch:** frank  
**Reference platform:** Linux

## Current feedback

FRANK remains Linux-primary. Android is a secondary edge-runtime laboratory that should expose memory, startup, IPC/copy, lifecycle, quantization, scheduling and resource-pressure constraints before they become hidden architecture costs.

The remote path GitHub Actions -> Firebase auth -> Android APK -> ARM Test Lab device is live. A minimal constructed ClayCode runtime completed deterministic semantic checks on Android. This proves the research lane, not that complete FRANK fits or performs acceptably on Android.

## Retrieval/emit rule

FRANK runs MUST retrieve Android findings that generalize to runtime efficiency or architecture boundaries. Android runs MUST retrieve current FRANK architecture and preserve the Linux-primary boundary. Android observations require Linux replication before becoming general FRANK performance claims.

## Next FRANK-facing experiments

- minimum viable FRANK organ set and memory ceiling on Android;
- cold boot, snapshot reconstruction and process-death recovery;
- target Qwen-class 4B quantized runtime feasibility;
- prefill/decode/total latency and memory rather than tokens/sec alone;
- Linux-vs-Android differential benchmark for any proposed general optimization.
