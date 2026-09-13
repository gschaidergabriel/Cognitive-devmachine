# EntityOS powered by Crush — OMEGA Runtime Bootstrap

Date: 2026-09-13
Status: ACTIVE BUILD LANE

## Owner intent

Build EntityOS as a portable Crush-derived runtime while preserving the working Frankenstein 2.0 execution topology during the first phase. Crush remains the stable user-facing harness and provider/tool shell. OMEGA becomes the persistent cognitive runtime underneath it.

Initial execution organs are exactly the currently proven external systems:

- ChatGPT through the existing ChatGPT bridge path.
- Claude Code through the existing Claude/CLI path.
- The existing Free Pool provider/model harness.
- Existing Frankenstein/EntityOS Local Bridges, VPS bridge, receipts, provider selection, state synchronization and reentry mechanisms where currently proven.

No separate model architecture is part of this phase. OMEGA coordinates interchangeable external model organs through the same bridge/provider topology already used by Frankenstein 2.0.

Deeply embed the portable OMEGA cognitive architecture: GRID10, TITAN MX, Unified state, LCME/dynamic cognitive compilation, GWT/Reentry, identity, hypotheses/goals/world-model state, module competition and effect gating.

## Core architectural cut

```text
Crush UI / CLI / tools / MCP / permissions / sessions
                         |
                         v
                    OMEGA runtime
                         |
       GRID10 / TITAN MX / Unified State / LCME
       GWT / Reentry / Identity / Modules / Effects
                         |
                         v
                organ/provider router
                 /        |        \
                /         |         \
          ChatGPT     Claude Code   Free Pool
             |             |            |
             +------ existing bridges --+
```

OMEGA sits between session/event intake and model/tool execution. Crush sessions are conversation surfaces, not entity identity. Persistent OMEGA state must survive session changes, provider/model changes and process restarts.

## Phase-1 compatibility law

The first usable EntityOS/OMEGA must behave operationally like the proven Frankenstein 2.0 stack, not replace it all at once.

Keep and reuse:

- ChatGPT bridge behavior and receipts.
- Claude Code/CLI execution path.
- Free Pool model/provider switching and quota-aware selection.
- Existing Local Bridge and VPS Bridge transport semantics.
- Existing GRID/state injection and UnifiedDB synchronization semantics until their equivalent has been moved natively into `internal/omega/`.
- Existing effect authority, provenance and receipt discipline.

Do not create duplicate bridges, duplicate provider routers, duplicate canonical turn loops or a parallel state authority.

## Portability law

The portable OMEGA cognitive core should depend only on narrow interfaces such as:

- StateStore
- ModelOrgan / ProviderOrgan
- Tool
- Observation
- Effect
- Clock
- EventBus
- BridgeAdapter

Host-specific bridges and launchers are adapters around the core, not the identity of the core. The portable runtime must not hard-code Gabriel- or Andreas-specific paths, machine IDs, systemd unit names, display devices, or one provider.

## UI target

Keep the selected existing modified Crush visual surface as the product-facing baseline: amber/orange retro CRT-style interface shown by the owner on 2026-09-13. Treat the already-running Gabriel `ai-core-node` modified Crush harness as the donor subject. Do not redesign the UI during the initial extraction.

The visual CRT wrapper can remain host-specific; the native Crush TUI remains the portable product surface.

## Migration principle

Extract the cognitive core from the evolving Frankenstein/EntityOS architecture while reusing the currently working Frankenstein 2.0 execution organs and bridges. Do not sever working ChatGPT/Claude/Free-Pool paths merely to make the new core look cleaner.

Current architecture is live/evolving; every `CRUSH` reentry must refresh current authority, donor heads, active work, bridge state and receipts before merging changes.

## Trigger contract

Exact trigger word: `CRUSH`

On an explicit `CRUSH` trigger:
1. Refresh current OMEGA/Frankenstein/EntityOS authority and active work.
2. Refresh the exact Gabriel modified-Crush donor subject.
3. Refresh current ChatGPT bridge, Claude Code path, Free Pool harness and bridge receipts relevant to the build.
4. Refresh this EntityOS-Crush build lane and avoid duplicate work.
5. Assimilate only current proven OMEGA architecture changes into the portable core.
6. Preserve the proven Frankenstein 2.0 organ/provider topology unless there is executable evidence for replacing a component.
7. Work in parallel only on disjoint boundaries; keep one mutation authority per boundary.
8. Preserve Crush external behavior unless a change is required for OMEGA integration.
9. Prefer executable tests/readbacks over architecture prose.

## Immediate gates

1. Keep Gabriel's proven Crush harness as the compatibility donor.
2. Keep ChatGPT, Claude Code and Free Pool as the active model-organ set.
3. Keep existing bridge/receipt paths alive while native OMEGA integration advances.
4. Maintain the `internal/omega/` seam behind tests while keeping Crush behavior compatible at the UI boundary.
5. Move persistent entity state below Crush sessions.
6. Route pre-model context formation through OMEGA cognitive compilation.
7. Route post-model/tool outcomes through OMEGA uptake/reentry.
8. Introduce a bridge/provider adapter layer that binds the existing ChatGPT, Claude Code and Free Pool execution paths without duplicating them.
9. Add provider-swap, bridge-reentry, restart and state-continuity tests.
10. Only retire wrapper-era state injection/sync code after native equivalents are proven by receipts and regression tests.
