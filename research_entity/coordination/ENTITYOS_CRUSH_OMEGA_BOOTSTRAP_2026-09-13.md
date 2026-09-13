# EntityOS powered by Crush — OMEGA Runtime Bootstrap

Date: 2026-09-13
Status: ACTIVE BUILD LANE

## Owner intent

Build EntityOS as a portable Crush-derived runtime. Preserve Crush's external stability, portability, TUI/CLI, provider, tool, MCP, permission and session behavior as far as possible. Deeply embed only the portable OMEGA cognitive architecture: GRID10, TITAN MX, Unified state, LCME/dynamic cognitive compilation, GWT/Reentry, identity, hypotheses/goals/world-model state, module competition and effect gating.

Do **not** bundle the 27B model into the core runtime. Models remain interchangeable organs/providers.

Do **not** require the Frankenstein VM/systemd/host topology for the portable runtime.

## Core architectural cut

```text
Crush UI / CLI / tools / MCP / providers / permissions / sessions
                         |
                         v
                    OMEGA runtime
                         |
       GRID10 / TITAN MX / Unified State / LCME
       GWT / Reentry / Identity / Modules / Effects
                         |
                         v
                 Crush model interface
                         |
               any local/cloud model
```

OMEGA sits between session/event intake and model/tool execution. Crush sessions are conversation surfaces, not entity identity. The persistent OMEGA state must survive session changes, model changes and process restarts.

## Portability law

OMEGA core may depend only on narrow runtime interfaces such as:

- StateStore
- Model
- Tool
- Observation
- Effect
- Clock
- EventBus

The core must not assume systemd, a VM/container, fixed Linux paths, Local Bridge, Avatar, browser/display, voice, or a specific provider.

## UI target

Keep the selected existing modified Crush visual surface as the product-facing baseline: amber/orange retro CRT-style interface shown by the owner on 2026-09-13. Treat the already-running Gabriel `ai-core-node` modified Crush harness as the donor subject; discover and bind its exact repo/path/commit before copying anything. Do not redesign the UI during the initial extraction.

## Migration principle

Extract the cognitive core from the evolving Frankenstein/EntityOS architecture rather than copying host-specific deployment assumptions. Reuse current canonical GRID/TITAN/UnifiedDB/Reentry semantics and preserve provenance. Current architecture is live/evolving; every `CRUSH` reentry must refresh current authority, donor heads, active work and receipts before merging changes.

## Trigger contract

Exact trigger word: `CRUSH`

On an explicit `CRUSH` trigger:
1. Refresh current OMEGA/Frankenstein/EntityOS authority and active work.
2. Refresh the exact Gabriel modified-Crush donor subject.
3. Refresh this EntityOS-Crush build lane and avoid duplicate work.
4. Assimilate only current proven OMEGA architecture changes into the portable core.
5. Work in parallel only on disjoint boundaries; keep one mutation authority per boundary.
6. Preserve Crush external behavior unless a change is required for OMEGA integration.
7. Prefer executable tests/readbacks over architecture prose.
8. Do not bundle a local foundation model into the core runtime.

## Immediate gates

1. Discover exact Gabriel modified Crush repo/path/commit and runtime binary.
2. Discover available VPS sandbox execution route and exact sandbox parent path.
3. Snapshot/fork donor into a dedicated EntityOS project sandbox without mutating Gabriel production.
4. Introduce the minimal `internal/omega/` seam behind tests while keeping Crush behavior byte/interaction-compatible at the UI boundary where practical.
5. Move persistent entity state below Crush sessions.
6. Route pre-model context formation through OMEGA cognitive compilation.
7. Route post-model/tool outcomes through OMEGA uptake/reentry.
8. Add model-swap/restart/state-continuity tests.
