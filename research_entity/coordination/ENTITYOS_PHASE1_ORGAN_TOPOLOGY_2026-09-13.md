# EntityOS / OMEGA Phase-1 Organ Topology

Date: 2026-09-13
Status: ACTIVE AUTHORITY FOR CURRENT BUILD LANE

OMEGA Phase 1 reuses the working Frankenstein 2.0 external cognition topology.

## Active model organs

1. ChatGPT via the existing ChatGPT bridge path.
2. Claude Code via the existing Claude/CLI path.
3. Free Pool via the existing quota-aware Crush provider harness.

These are organs behind OMEGA, not OMEGA itself.

## Active transport/state surfaces

Reuse the currently proven:

- Local Bridge transport and receipts.
- VPS Bridge transport and receipts.
- Crush provider selection and mid-session model switching.
- Crush native session continuation/reentry.
- GRID state/context ingress.
- UnifiedDB knowledge ingress and terminal-session synchronization.
- Existing effect authority and evidence gates.

## Build rule

Native `internal/omega/` integration replaces wrapper mechanisms only when equivalent behavior is covered by executable tests and readback/receipt evidence. Until then, the wrapper/bridge path remains authoritative for that capability.

No duplicate bridge, no second canonical turn loop, no second provider router, and no second persistent truth store.

## Target turn path

```text
user/event
   |
   v
Crush surface
   |
   v
OMEGA Compile / GRID / TITAN / LCME / GWT
   |
   v
organ router
   |----------- ChatGPT bridge
   |----------- Claude Code / CLI
   `----------- Free Pool provider
   |
   v
model/tool outcome
   |
   v
OMEGA Reentry / Unified state / evidence
   |
   v
existing bridges + receipts for external effects
```

## CRUSH trigger

On every explicit `CRUSH` trigger, refresh all four relevant live authorities before mutation:

- current OMEGA/EntityOS architecture,
- Gabriel's modified Crush harness,
- ChatGPT/Claude/Free-Pool bridge/provider topology,
- current build-lane head and active work.

Then port the strongest nonduplicate semantic delta into the native OMEGA core without breaking working Frankenstein 2.0 behavior.
