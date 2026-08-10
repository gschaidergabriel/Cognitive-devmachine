# Project Source VPS Target Supersession — 2026-08-10

**Status:** PROJECT_OWNER_FIXED_DELTA  
**Applies to:** generated single-project source dated 2026-08-09 and any worker/bootstrap derived from it.

## Source-derived conflict found

The 2026-08-09 single-project source still states:

- mission attractor: `Frank v0.1 voll lauffähig auf Andreas PC`;
- Hostinger VPS is a verified **remote build/test lane**;
- remote VPS evidence must not be confused with final target-hardware evidence;
- final acceptance still requires the real Andreas Ubuntu target system;
- a separate future GPU/storage VPS may exist/planned and must be reverified.

Those statements accurately describe the 2026-08-09 snapshot but are stale after the project-owner instruction on 2026-08-10.

## Current superseding truth

The current verified Hostinger Ubuntu VPS (`digital-retina`) is now the **operative Frank v0.1 target host** for build, integration, benchmark, runtime and final acceptance.

Frank's human/user remains Dr. Andreas Unterweger.

A mandatory later Andreas-local-PC release run is removed from the v0.1 gate.

The separately planned GPU/storage VPS remains future/optional capacity and must not silently replace the current target host.

## Required boot behavior

Any worker reading the older generated single-project source MUST, before making target-host decisions, load:

1. `research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md`;
2. `research_entity/rooms/TARGET_HOST_STATE.json`;
3. `research_entity/rooms/CAPACITY_STATE.json`;
4. current `PROGRAM_STATE.json` and current work/receipts.

Where the older source conflicts, these current files win.

## Architecture consequence

The target-host switch changes physical deployment assumptions, not Frank's human identity or semantic architecture:

- Frank/Qwen/UnifiedDB/EAP/GWT/Clay runtime executes on the target VPS;
- Retina/multimodal sensor sources may be remote and enter through provenance-bound ingress;
- sensor transport cost is measured separately from on-VPS perception/retrieval/reasoning;
- target-VPS resource/performance receipts are now final-target evidence;
- H3/DOOMSDAY must prove deterministic service startup/recovery without depending on a local interactive desktop session.
