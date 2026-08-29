# Execution Surface Resolution — CURRENT

For any execution/capability/VPS/sandbox/tooling question, resolve in this order:

1. `CLAY_EXECUTION_AUTHORITY.md`
2. `governance/EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1.md`
3. `governance/EXECUTION_SURFACE_REGISTRY_V1.json`
4. fresh direct-session capability discovery
5. fresh registered-route health/reachability observations

Invariant:

`DIRECT_TOOL_NOT_OBSERVED != PROJECT_CAPABILITY_ABSENT`

Do not emit global `NO_EXECUTOR`/`NO_SHELL`/`VPS_UNAVAILABLE` from a local surface observation. Unknown bridge health is `DISCOVERY_REQUIRED`; queued/offline/rate-limited transport is `TRANSIENTLY_UNREACHABLE`; provider/economic denial is a separate axis. Revalidate authority generation before effectful or runtime-credit-bearing use.

Deep evidence: `research_entity/reports/2026-08-29_EXECUTION_SURFACE_ROOT_CAUSE_DEEP_RESEARCH_GPT56SOL.md`.
