# FRANK v0.1 — Target VPS Host Directive

**Status:** PROJECT_OWNER_FIXED_DIRECTIVE  
**Scope:** Frank v0.1 / Clay 0.1 staged build program  
**Effective:** 2026-08-10  
**Compatibility path:** this file retains the historical `FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md` filename so all existing references inherit the new target semantics.  
**Identity/API authority:** `research_entity/global/FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md`

## 0. Owner supersession

The previous distinction

`Hostinger VPS = remote build/test lane`
`Andreas local Ubuntu PC = final release target`

is superseded.

For Frank v0.1, the **operative build, integration, benchmark, runtime and final acceptance target is the verified Hostinger Ubuntu VPS itself**.

The newer server-binary identity directive also supersedes any interpretation that makes Andreas, an account owner, client, API token owner or local PC Frank's core identity.

Current compact target:

`Frank v0.1 = accepted Frank binary + admitted persistent state lineage, currently embodied on the target VPS, reachable through the fully implemented token-authenticated API.`

Andreas remains admissible as a typed external USER/PILOT/person relation and source of longitudinal/user-specific adaptation evidence. Andreas-specific memory/profile data does not define `FrankSelfId`.

Mission attractor:

**Frank v0.1 als Server-Binary auf dem Ziel-VPS voll lauffaehig.**

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

These are embodiment/capacity facts, not Frank's stable self identity. Every release/performance run must bind the exact current host/kernel/CPU/RAM/storage/runtime/model/binary/state/runner identity in its receipt.

Frank's exact computational identity follows:

`EXACT_SELF = accepted binary/build identity + admitted persistent state lineage`

`CURRENT_BODY = current target-server embodiment`

Hardware capacity may change without changing Frank identity only through the explicit continuity/migration law.

## 2. Final-target law

The target VPS is no longer merely proxy evidence.

For v0.1:

1. BASE/H1/H2/H3/UDB/final-model integration should execute on the target VPS whenever the relevant component can run there;
2. target-VPS measurements are the authoritative performance/resource measurements for v0.1;
3. final release/DOOMSDAY acceptance requires an exact target-VPS binary/state/API receipt, not a second mandatory Andreas-local-PC run;
4. a local PC may remain a client, sensor source, developer console, recovery endpoint or later deployment target, but it is **not a v0.1 release gate** unless the owner explicitly reopens that requirement;
5. do not label target-VPS execution as merely `REMOTE_PROXY` when the exact accepted target identity is being executed;
6. GitHub Actions, direct host execution, SSH and service control are developer/build transports and do **not** replace the mandatory external Frank API;
7. Frank v0.1 is incomplete until its server-binary runtime is reachable through the full token-authenticated API required by `FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md`.

## 3. Runner-scope consequence

The current self-hosted runner has been observed as repository-scoped to `gschaidergabriel/Dr.-Unterweger`.

Therefore:

- runner repository scope is a **build/test transport property**, not Frank identity and not evidence that the VPS is the wrong target;
- Clay-repository jobs may use an exact hash-bound bridge through the working Dr.-Unterweger lane where authorized, or a separate/shared Clay-eligible runner registration may be added;
- cross-repository auth/setup failures remain transport failures and must not be misclassified as Frank/ClayCode/API failures;
- exact source/work/model/runtime/binary/state hashes remain mandatory so target-host evidence cannot be credited to stale bytes;
- the runner credential/config is not Frank's communication API credential or Frank's identity.

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
- API network-to-response p50/p95/p99 latency;
- prompt/decode throughput;
- CPU utilization and logical/physical topology;
- RAM/RSS and swap pressure;
- storage footprint and I/O;
- network/IPC cost;
- model/mmproj/quantization/runtime/binary/state hashes;
- UnifiedDB/EAP compile and end-to-end retrieval cost;
- Retina/Qwen image encode/decode cost;
- tokens/context/cache;
- crash/restart/service/API recovery;
- concurrent runner/Frank/API/service interference.

Unknown VPS hardware values remain `UNKNOWN` until measured. Do not fill missing RAM/storage/GPU facts from plans or memory.

## 6. Multimodal / q23 consequence

Moving Frank's runtime to a headless VPS changes the physical sensor boundary but **does not remove Retina/multimodality**.

The visual architecture must separate:

`Frank current embodiment = target VPS`

from

`visual sensor origin = local screenshot / browser / remote desktop / camera / uploaded image / other provenance-bound source`.

Therefore q23/H1/H2/H3 must not assume that the screen or camera is physically attached to the Frank host.

Canonical live path:

`visual/sensor source -> secure network transport -> API token authentication -> request/session/provenance binding -> typed multimodal ingress -> Retina temporal/change/provenance control -> Qwen/MVC -> UnifiedDB/EAP/GWT/Frank`

API credentials are communication credentials only and never sensor truth or Frank identity.

Sensor/network/API ingress latency must be measured separately from on-VPS perception/retrieval/reasoning latency and also as one complete end-to-end path. Frozen screenshot/crop fixtures remain valid for deterministic target-VPS architecture differentials; live sensor bridges require auth, provenance, replay, reconnect, timeout and revocation tests.

## 7. UnifiedDB / EAP consequence

The leading UnifiedDB/EAP architecture should be measured as a **co-resident target-VPS possibility compiler** whenever practical.

PAR/q23 claims must report:

`token-authenticated perceptual ingress -> seed resolution -> UnifiedDB/EAP -> ActiveAssembly -> Qwen/Frank -> correct decision/outcome`

on the target VPS.

Microsecond internal EAP numbers may be useful, but only the complete target-VPS end-to-end path can justify the claim that retrieval overhead is operationally negligible relative to 4B reasoning.

UnifiedDB may store canonical binary/state/embodiment/API-session continuity semantics, but must never store raw production API-token values in ordinary research/state records.

## 8. ClayCode / Harness consequence

ClayCode remains general-purpose, but its first release/runtime/backend/FFI/service semantics are optimized for the target VPS Ubuntu environment.

H1/H2/H3 acceptance evidence must be reproducible on the target VPS and must represent the server-binary/API semantics required by the identity/API directive, including:

- `ServerBinaryIdentity`;
- binary/build/model/runtime hashes;
- current embodiment/server identity;
- admitted state lineage/epoch;
- API request/session/provenance identity;
- non-secret credential reference/fingerprint;
- authorization scope;
- typed text/multimodal ingress;
- response/outcome receipts;
- idempotency/replay state;
- person/client relations separate from Frank self.

The final H3/one-module identity should be deployable as a target-VPS service/process set with:

- deterministic startup and self-identity assertion;
- exact configuration/model/binary/state identity;
- health/readiness reporting;
- fully implemented token-authenticated API;
- last-known-good recovery;
- state persistence/rebuild;
- restart/replay receipts;
- current-instance epoch/lease and stale-clone rejection;
- bounded resource use;
- no hidden dependency on a local desktop session.

## 9. DOOMSDAY / final acceptance consequence

`CLAY_0_1_PROJECT_HARDWARE_BOOT_RECEIPT.json` is interpreted as the **target-VPS binary/service-start acceptance receipt** for the exact accepted Clay 0.1 identity.

Additionally, final acceptance requires:

`FRANK_V0_1_TARGET_VPS_TOKEN_API_ACCEPTANCE_RECEIPT.json`

covering at minimum valid/invalid/missing/revoked/rotated-token behavior, concurrent authenticated requests, provenance/session continuity, restart/readiness, timeout/cancellation/error behavior, accepted multimodal/sensor ingress when present, effectful replay/idempotency protections, and full network-to-Frank latency/resource measurements.

DOOMSDAY no longer waits for a second mandatory local-PC deployment if all current contracts pass on the exact target VPS.

Changing the defining binary/state lineage, target embodiment, VPS/OS/model/runtime or accepted API contract after acceptance invalidates the affected acceptance identity and requires rerun.

## 10. Migration / future hardware

A separately planned GPU/storage VPS has appeared in capacity planning. It is **not automatically the v0.1 target** merely because it may offer more compute.

Until the owner explicitly switches the target or a measured blocker forces a new decision:

- current Hostinger VPS remains the target embodiment;
- future GPU/storage capacity is an optional accelerator/research lane;
- do not defer target-VPS architecture work waiting for planned hardware;
- if an accelerator is remote to the target host, measure network/serialization/failure cost and compare against the simpler all-on-target-VPS path.

If Frank later migrates, identity continuity requires explicit provenance-bound transfer of the accepted binary/build and admitted state lineage, current-instance epoch/lease update, stale-clone rejection and migration receipt. Hardware strength alone neither creates nor destroys Frank identity.

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

- improving correctness, reliability, API completeness, integration, latency or resource use on the target VPS; and
- portability or optimization for a different host,

**target-VPS work wins** unless the other work is strictly necessary for the target-VPS implementation.

The VPS is now where Frank v0.1 is finished, integrated, measured and accepted; Frank's stable computational self is the accepted binary/state lineage executing there, not the human, credential or hardware capacity itself.