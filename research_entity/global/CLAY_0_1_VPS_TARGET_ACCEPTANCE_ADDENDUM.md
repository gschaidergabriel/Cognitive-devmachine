# Clay 0.1 — Target VPS Acceptance Addendum

**Status:** PROJECT_OWNER_FIXED_SUPERSESSION_ADDENDUM  
**Effective:** 2026-08-10  
**Parent:** `research_entity/global/CLAY_0_1_CHIEF_DEVELOPER_ACCEPTANCE_CONTRACT.md`  
**Target host:** `research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md`

## 1. Supersession

Where the parent acceptance contract refers generically to project-controlled hardware or an older workflow assumes a later Andreas-local-PC acceptance run, the current owner-fixed interpretation is:

**the verified Hostinger Ubuntu VPS is the Frank v0.1 / Clay 0.1 final target host.**

No second mandatory Andreas-local-PC execution is required for DOOMSDAY PASS.

## 2. Final hardware receipt

`CLAY_0_1_PROJECT_HARDWARE_BOOT_RECEIPT.json` is now a target-VPS boot/service-start/recovery receipt and must bind at least:

- machine/host identity;
- kernel/OS/arch;
- CPU/RAM/swap/storage facts actually observed;
- model/mmproj/runtime hashes;
- ClayCode/compiler/runtime hash;
- UnifiedDB/state identity;
- service/process configuration;
- network/listener/capability boundary;
- deterministic startup/readiness;
- crash/restart/last-known-good restore;
- resource shadow under representative Frank load.

## 3. Headless target consequence

The final system must not depend on an interactive local desktop session existing on the target VPS.

Visual perception remains mandatory, but sensor sources may be remote. Acceptance therefore distinguishes:

`target-VPS compute/runtime correctness`

from

`remote/local visual sensor ingress correctness`.

For live sensor paths, provenance/authentication/reconnect/replay and sensor-network latency are mandatory. Frozen image/screenshot fixtures remain valid for deterministic on-VPS multimodal differentials.

## 4. Performance truth

Performance viability thresholds for v0.1 are frozen from target-VPS measurements. A faster future GPU/storage host does not retroactively define the current target.

If current target-VPS performance proves unusable, that is a measured architecture/target decision point; do not silently substitute planned hardware.

## 5. Acceptance identity

Changing the target VPS, OS/kernel family, model/runtime identity or defining persistent-state identity after acceptance invalidates the prior target-host acceptance receipt and requires rerun of affected acceptance families.
