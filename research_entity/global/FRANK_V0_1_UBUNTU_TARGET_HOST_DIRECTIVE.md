# FRANK v0.1 — Target VPS Host Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE  
**Scope:** Frank v0.1 / Clay 0.1 staged build program  
**Effective:** 2026-08-10  
**Compatibility path:** this file retains the historical `FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md` filename so all existing references inherit the new target semantics.

## 0. Owner supersession

The previous distinction

`Hostinger VPS = remote build/test lane`
`Andreas local Ubuntu PC = final release target`

is superseded.

For Frank v0.1, the **operative build, integration, benchmark and final acceptance target is the verified Hostinger Ubuntu VPS itself**.

Frank's human/user remains **Dr. Andreas Unterweger**. Changing the deployment/acceptance host does not change Frank's human identity, user-state semantics or Andreas-specific adaptation contracts.

Mission attractor:

**Frank v0.1 voll lauffaehig auf dem Ziel-VPS fuer Andreas.**

## 1. Current target-host identity

Current verified target family:

- resource: `hostinger-vps-github-runner`;
- observed machine/runner host: `digital-retina`;
- OS/runtime family: Ubuntu Linux / x86_64;
- observed kernel: `Linux 6.8.0-117-generic`;
- observed libc: `glibc 2.39`;
- observed Python in current self-hosted receipts: `3.12.3`;
- observed CPU topology in a real Qwen receipt: **4 logical CPUs**;
- self-hosted runner name: `clay`;
- currently observed active runner service is repository-scoped to `gschaidergabriel/Dr.-Unterweger` under the `frankrunner` account.

These facts are current evidence, not eternal hardware constants. Every release/performance run must bind the exact current host/kernel/CPU/RAM/storage/runtime/model/runner identity in its receipt.

## 2. Final-target law

The target VPS is no longer merely proxy evidence.

For v0.1:

1. BASE/H1/H2/H3/UDB/final-model integration should execute on the target VPS whenever the relevant component can run there;
2. target-VPS measurements are the authoritative performance/resource measurements for v0.1;
3. final release/DOOMSDAY acceptance requires an exact target-VPS receipt, not a second mandatory Andreas-local-PC run;
4. a local Andreas PC may remain a client, sensor source, developer console, recovery endpoint or later deployment target, but it is **not a v0.1 release gate** unless the owner explicitly reopens that requirement;
5. do not label target-VPS execution as merely `REMOTE_PROXY` when the exact accepted target identity is being executed;
6. GitHub Actions transport, direct host execution, SSH, service control or another authorized mechanism are execution transports, not separate target systems.

## 3. Runner-scope consequence

The current self-hosted runner has been observed as repository-scoped to `gschaidergabriel/Dr.-Unterweger`.

Therefore:

- runner repository scope is a **transport/integration property**, not evidence that the VPS is the wrong target;
- Clay-repository jobs may use an exact hash-bound bridge through the working Dr.-Unterweger lane where authorized, or a separate/shared Clay-eligible runner registration may be added;
- cross-repository auth/setup failures remain transport failures and must not be misclassified as Frank/ClayCode failures;
- exact source/work/model/runtime hashes remain mandatory so target-host evidence cannot be credited to stale bytes.

## 4. Existing real-model target-host evidence

The target VPS has already executed a real local 4B model through llama.cpp:

- model family in the recorded receipt: `Qwen3-4B-Instruct-2507-Q8_0-GGUF`;
- measured mean decode throughput: about `10.705 tok/s`;
- measured mean prompt throughput: about `39.941 tok/s`;
- four-task pilot accuracy: `3/4`;
- one confidently wrong result is preserved as direct evidence that verbalized confidence is not calibrated correctness.

This proves that the host is a real local-model execution target. It does **not** promote that historical Qwen artifact as the final v0.1 model and does not replace current q23/Qwen3.5/abliterated matched testing.

## 5. Resource-optimization consequence

Because target performance now means **VPS performance**, every architecture optimization claim must measure the full target-VPS path.

Where applicable record:

- cold/warm p50/p95/p99 latency;
- prompt/decode throughput;
- CPU utilization and logical/physical topology;
- RAM/RSS and swap pressure;
- storage footprint and I/O;
- network/IPC cost;
- model/mmproj/quantization/runtime hashes;
- UnifiedDB/EAP compile and end-to-end retrieval cost;
- Retina/Qwen image encode/decode cost;
- tokens/context/cache;
- crash/restart/service recovery;
- concurrent runner/Frank/service interference.

Unknown VPS hardware values remain `UNKNOWN` until measured. Do not fill missing RAM/storage/GPU facts from plans or memory.

## 6. Multimodal / q23 consequence

Moving Frank's runtime to a headless VPS changes the physical sensor boundary but **does not remove Retina/multimodality**.

The visual architecture must separate:

`Frank compute host = target VPS`

from

`visual sensor origin = local screenshot / browser / remote desktop / camera / uploaded image / other provenance-bound source`.

Therefore q23/H1/H2/H3 must not assume that the screen or camera is physically attached to the Frank host.

Required rule:

`visual source -> authenticated/provenance-bound sensor ingress -> Retina temporal/change/provenance control -> Qwen/MVC -> UnifiedDB/EAP/GWT/Frank`

Sensor transport latency must be measured separately from on-VPS perception/retrieval/reasoning latency. Frozen screenshot/crop fixtures are valid for deterministic target-VPS architecture differentials; live sensor bridges require their own provenance/replay/reconnect tests.

## 7. UnifiedDB / EAP consequence

The leading UnifiedDB/EAP architecture should be measured as a **co-resident target-VPS possibility compiler** whenever practical.

PAR/q23 claims must report:

`visual ingress -> seed resolution -> UnifiedDB/EAP -> ActiveAssembly -> Qwen/Frank -> correct decision/outcome`

on the target VPS.

Microsecond internal EAP numbers may be useful, but only the complete target-VPS end-to-end path can justify the claim that retrieval overhead is operationally negligible relative to 4B reasoning.

## 8. ClayCode / Harness consequence

ClayCode remains general-purpose, but its first release/runtime/backend/FFI/service semantics are optimized for the target VPS Ubuntu environment.

H1/H2/H3 acceptance evidence must be reproducible on the target VPS.

The final H3/one-module identity should be deployable as a target-VPS service/process set with:

- deterministic startup;
- exact configuration/model/state identity;
- health/readiness reporting;
- last-known-good recovery;
- state persistence/rebuild;
- restart/replay receipts;
- bounded resource use;
- no hidden dependency on a local desktop session.

## 9. DOOMSDAY / final acceptance consequence

`CLAY_0_1_PROJECT_HARDWARE_BOOT_RECEIPT.json` should now be interpreted as the **target-VPS boot/service-start acceptance receipt** for the exact accepted Clay 0.1 identity.

DOOMSDAY no longer waits for a second mandatory local-PC deployment if all other contracts pass on the exact target VPS.

Changing the defining VPS/OS/model/runtime/state identity after acceptance invalidates the old acceptance identity and requires a new acceptance run.

## 10. Separate future GPU/storage VPS

A separately planned GPU/storage VPS has appeared in capacity planning. It is **not automatically the v0.1 target** merely because it may offer more compute.

Until the owner explicitly switches the target or a measured blocker forces a new decision:

- current Hostinger VPS remains the target host;
- future GPU/storage capacity is an optional accelerator/research lane;
- do not defer target-VPS architecture work waiting for planned hardware;
- if an accelerator is remote to the target host, measure network/serialization/failure cost and compare against the simpler all-on-target-VPS path.

## 11. Explicit out-of-scope targets for v0.1

Unless explicitly reopened:

- Android;
- mobile platforms;
- generic edge-device deployment;
- Windows;
- macOS;
- BSD;
- mandatory local-PC deployment;
- cross-platform portability work not required to make the target VPS correct and usable.

## 12. Priority law

When a choice exists between:

- improving correctness, reliability, integration, latency or resource use on the target VPS; and
- portability or optimization for a different host,

**target-VPS work wins** unless the other work is strictly necessary for the target-VPS implementation.

The VPS is now where Frank v0.1 is finished, integrated, measured and accepted.