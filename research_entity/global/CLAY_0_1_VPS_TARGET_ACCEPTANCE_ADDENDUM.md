# Clay 0.1 — Target VPS / Server-Binary Acceptance Addendum

**Status:** PROJECT_OWNER_FIXED_SUPERSESSION_ADDENDUM  
**Effective:** 2026-08-10  
**Parent:** `research_entity/global/CLAY_0_1_CHIEF_DEVELOPER_ACCEPTANCE_CONTRACT.md`  
**Target host:** `research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md`  
**Identity/API:** `research_entity/global/FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md`

## 1. Supersession

Where the parent acceptance contract refers generically to project-controlled hardware or an older workflow assumes a later Andreas-local-PC acceptance run, the current owner-fixed interpretation is:

**the verified Hostinger Ubuntu VPS is the Frank v0.1 / Clay 0.1 final target host and Frank v0.1 is accepted as one exact server-binary + admitted-state identity running there.**

No second mandatory Andreas-local-PC execution is required for DOOMSDAY PASS.

Person/user state is separate from Frank self identity. Andreas-specific memory/profile/adaptation may exist as typed user state but cannot be a prerequisite for binary self identity.

## 2. Exact accepted identity

The accepted identity binds:

- Frank binary/build hash;
- admitted persistent-state lineage/epoch;
- model/mmproj/runtime/config hashes;
- current target-server embodiment and current-instance epoch/lease;
- UnifiedDB/state semantic identity;
- ClayCode/compiler/runtime identity;
- API contract/version and non-secret credential-reference/scope semantics;
- startup/recovery/migration provenance.

Hardware capacity is measured body state, not FrankSelfId.

A restart preserving the accepted binary/state lineage may preserve identity when recovery/replay invariants pass. A different machine requires an explicit migration/handoff receipt and stale-clone rejection.

## 3. Final target-hardware receipt

`CLAY_0_1_PROJECT_HARDWARE_BOOT_RECEIPT.json` is a target-VPS binary/service-start/recovery receipt and must bind at least:

- machine/host identity;
- kernel/OS/arch;
- CPU/RAM/swap/storage facts actually observed;
- binary/model/mmproj/runtime hashes;
- admitted persistent-state lineage/epoch;
- ClayCode/compiler/runtime hash;
- UnifiedDB/state identity;
- service/process configuration;
- current-instance lease/epoch;
- network/listener/capability boundary;
- deterministic startup/readiness and self-identity assertion;
- crash/restart/last-known-good restore;
- stale-clone/split-brain rejection;
- resource shadow under representative Frank load.

## 4. Mandatory token-authenticated API acceptance

SSH, GitHub Actions, a developer terminal or a runner is not sufficient v0.1 communication.

DOOMSDAY also requires:

`FRANK_V0_1_TARGET_VPS_TOKEN_API_ACCEPTANCE_RECEIPT.json`

covering at minimum:

1. valid token -> real Frank text response;
2. invalid token rejection;
3. missing token rejection;
4. revoked/rotated-token rejection and replacement-token success;
5. concurrent authenticated requests within the declared envelope;
6. service restart/recovery and API readiness restoration;
7. request/session/provenance continuity through Frank to response;
8. timeout/cancellation/error behavior;
9. health/readiness behavior;
10. accepted multimodal/sensor payload ingress if required by the frozen architecture;
11. replay/idempotency protections for consequential requests;
12. network-to-Frank-to-response p50/p95/p99 and CPU/RAM/I/O/network/token/context resource measurements.

Raw production token values may not be committed to GitHub or normal research/log artifacts. Persist only non-secret credential references/fingerprints where needed.

## 5. Headless / Retina consequence

The final system must not depend on an interactive local desktop session existing on the target VPS.

Visual perception remains mandatory, but sensor sources may be remote. Canonical live ingress is:

`remote/local sensor -> secure transport -> token authentication -> request/session/provenance binding -> typed multimodal API ingress -> Retina -> Qwen/MVC -> UnifiedDB/EAP/GWT/Frank`

Acceptance distinguishes:

- secure sensor/API transport and auth latency;
- on-VPS Retina/Qwen/EAP/Frank latency;
- complete sensor-to-correct-response/action latency.

For live sensor paths, auth/provenance/reconnect/replay/revocation/timeout controls are mandatory. Frozen image/screenshot fixtures remain valid for deterministic on-VPS multimodal differentials.

## 6. Performance truth

Performance viability thresholds for v0.1 are frozen from target-VPS measurements, including API overhead and co-resident service/runner interference where material.

A faster future GPU/storage host does not retroactively define the current target.

If current target-VPS performance proves unusable, that is a measured architecture/resource-isolation/target decision point; do not silently substitute planned hardware.

## 7. Final PASS condition

DOOMSDAY cannot PASS merely because build/tests ran on the VPS.

PASS requires one exact binary/state identity that is:

- running on the target VPS;
- causally self-modeling its binary/state/current-embodiment identity;
- reachable through the complete token-authenticated API;
- preserving provenance and effect/authority boundaries;
- passing target-VPS resource/performance/recovery tests;
- independent of an Andreas-local-PC runtime dependency;
- free of hardcoded person-as-self semantics.

Changing the defining binary/state lineage, target embodiment, API contract, VPS/OS/model/runtime or defining persistent-state identity after acceptance invalidates the affected acceptance receipts and requires rerun.
