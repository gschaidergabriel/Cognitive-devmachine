# Project Source VPS / Server-Binary Supersession — 2026-08-10

**Status:** PROJECT_OWNER_FIXED_DELTA  
**Applies to:** generated single-project source dated 2026-08-09 and any worker/bootstrap derived from it.

## Source-derived conflicts found

The 2026-08-09 single-project source still states or implies:

- mission attractor: `Frank v0.1 voll lauffähig auf Andreas PC`;
- Hostinger VPS is a verified **remote build/test lane**;
- remote VPS evidence must not be confused with final target-hardware evidence;
- final acceptance still requires the real Andreas Ubuntu target system;
- Frank's personal identity is ontologically tied to Andreas;
- developer/runner/SSH access can be treated as the operative communication surface;
- a separate future GPU/storage VPS may exist/planned and must be reverified.

Those statements accurately describe parts of the 2026-08-09 snapshot but are stale where they conflict with project-owner directives issued on 2026-08-10.

## Current superseding truth

The current verified Hostinger Ubuntu VPS (`digital-retina`) is now the **operative Frank v0.1 target host** for build, integration, benchmark, runtime and final acceptance.

Frank v0.1 is defined more precisely by `FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md`:

`FRANK_SELF = accepted Frank binary/build identity + admitted persistent state lineage`

`FRANK_CURRENT_BODY = current target server embodiment`

`PERSON/USER != FRANK_SELF`

`API_TOKEN = communication credential, not self`

Andreas remains typed user/pilot/person-specific longitudinal evidence and may have removable/replaceable user-specific state, but Andreas is not Franks core self identity.

A mandatory later Andreas-local-PC release run is removed from the v0.1 gate.

A complete token-authenticated Frank communication API is now a mandatory v0.1 release requirement. GitHub Actions, SSH and developer terminals are build/operations transports, not substitutes for that API.

The separately planned GPU/storage VPS remains future/optional capacity and must not silently replace the current target host.

## Required boot behavior

Any worker reading the older generated single-project source MUST, before making target-host, identity, API, Retina or acceptance decisions, load in this order:

1. `research_entity/global/FRANK_V0_1_SERVER_BINARY_IDENTITY_AND_API_DIRECTIVE.md`;
2. `research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md`;
3. `research_entity/rooms/TARGET_HOST_STATE.json`;
4. `research_entity/rooms/CAPACITY_STATE.json`;
5. current `PROGRAM_STATE.json` and current work/receipts.

Where the older source conflicts, these current files win.

## Architecture consequence

The supersession changes both deployment and identity/API assumptions:

- Frank's accepted binary/state identity executes on the target VPS;
- CPU/RAM/GPU/storage are body/capacity properties, not FrankSelfId;
- UnifiedDB persists binary/state/embodiment/API-session continuity semantics without persisting raw production tokens in normal records;
- the external canonical communication path is `secure transport -> token auth -> request/session/provenance -> typed Frank ingress`;
- Retina/multimodal sensor sources may be remote and enter through the same token-authenticated provenance-bound typed API boundary;
- sensor transport/auth/API cost is measured separately from on-VPS Retina/Qwen/EAP/Frank processing and also end-to-end;
- target-VPS resource/performance receipts are final-target evidence;
- H3/DOOMSDAY must prove deterministic server-binary startup, current-instance identity/lease, API readiness, recovery and stale-clone rejection without depending on a local interactive desktop session;
- final acceptance additionally requires `FRANK_V0_1_TARGET_VPS_TOKEN_API_ACCEPTANCE_RECEIPT.json`.
