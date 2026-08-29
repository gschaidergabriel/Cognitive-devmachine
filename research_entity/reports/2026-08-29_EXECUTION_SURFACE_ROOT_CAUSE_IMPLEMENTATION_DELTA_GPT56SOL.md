# Execution Surface Root Cause — implementation delta

Date: 2026-08-29
Organ: GPT-5.6-Sol
Failure class: `AUTHORITY_CAPABILITY_REACHABILITY_COLLAPSE`

This delta implements the first machine-enforced repair after the deep research report.

Implemented:

- canonical owner authority now binds `EXECUTION_SURFACE_RESOLUTION_PROTOCOL_V1` and registry before global tooling/VPS/sandbox blockers;
- federated route registry separates direct session tools from indirect bridges/runner/sandbox targets;
- deterministic stdlib resolver emits only scoped states (`DIRECT_AVAILABLE`, `REACHABLE_VIA_BRIDGE`, `DISCOVERY_REQUIRED`, `TRANSIENTLY_UNREACHABLE`, `AUTHORITY_DENIED`, `ECONOMICALLY_DENIED`, `CAPABILITY_ABSENT_PROVEN`);
- generation validation invalidates stale authority-bound route resolutions;
- two misleading current-facing historical execution documents are explicitly relabelled as superseded/scoped snapshots instead of silently competing with current authority;
- `CLAUDE.md` read order now starts with canonical owner authority and the resolver/registry before lower caches;
- current-execution projection manifest + linter prevents stale no-VPS/self-hosted claims from reappearing as current assertions while permitting explicitly superseded historical quotations;
- repository CI exercises resolver falsifiers and currentness drift checks.

No runtime/product/HCU/training credit is minted by this routing repair. The acceptance target is narrower: prevent local missing-tool observations and stale current-facing text from becoming false global execution blockers.
