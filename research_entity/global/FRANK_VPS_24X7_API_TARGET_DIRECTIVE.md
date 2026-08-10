# FRANK VPS 24x7 API Target Directive

**Status:** PROJECT-OWNER FIXED TARGET
**Owner instruction date:** 2026-08-10
**Scope:** Clay / Research Entity, Frank v0.1 deployment, VPS infrastructure, Harness, MCP/execution tooling, API access, monitoring and acceptance

## Exact target

The sole Frank v0.1 target host is the **persistent VPS**. The former Andreas-PC/Ubuntu-developer-system target is superseded.

The finished Frank must run on the VPS continuously (24/7) and be reachable through an authenticated API token so authorized systems can communicate with Frank programmatically.

Andreas' PC is not a v0.1 release or acceptance target. It may still be used as an ordinary client/development access point where useful.

Everything else in the current Frank/Clay v0.1 programme remains unchanged except this concrete target-host replacement. The authoritative target-host contract is `research_entity/global/FRANK_V0_1_VPS_TARGET_HOST_DIRECTIVE.md`.

## Research Entity VPS authority

The Research Entity and its authorized temporary workers may autonomously perform **non-destructive** work on the VPS in service of this target, including:

- inspect hardware, OS, processes, files, models, repositories and logs;
- build, compile, test and benchmark;
- download/cache models and dependencies;
- create new files/directories, virtual environments, services, containers/processes and reversible configuration;
- start/restart/stop Research-Entity-owned development/test processes and Frank service instances when required for deployment, testing or recovery;
- update project-owned files/configuration only through recoverable writes with provenance/backup/CAS where practical;
- run model inference and multimodal benchmarks;
- communicate with the running Frank API using its configured token;
- collect telemetry/receipts and return results to UnifiedDB/ClayGraph/research mesh.

## Hard destructive boundary

Without a new explicit owner instruction, the VPS authority does **not** include destructive operations such as:

- deleting project/user data or models;
- disk formatting, partition destruction or filesystem destruction;
- destructive database drops/truncates;
- destructive git history rewrites or repository deletion;
- disabling recovery/backup solely to save cost;
- arbitrary root-level destructive changes;
- killing unrelated/user processes;
- replacing an existing file without recoverable prior state when a safer atomic/backup path exists.

Ambiguous operations default to the reversible/non-destructive implementation.

## Frank API contract

The persistent Frank runtime must expose an authenticated API with at least:

1. `health` / readiness;
2. version/build/model identity;
3. conversation/message request and response;
4. request correlation id;
5. explicit timeout/error surface;
6. API-token authentication;
7. bounded request size/rate/resource controls;
8. audit/log provenance without logging secret token values;
9. restart/recovery behavior;
10. stable enough endpoint semantics for MCP and other authorized clients.

The API token itself is secret operational state. Store it only in an environment/secret store or owner-approved secure store; never commit it to GitHub, receipts, logs or model prompts.

## MCP relationship

`infra/clay_vps_mcp` is the preferred controlled Research-Entity execution surface for direct VPS work. It must expose broad non-destructive inspection/build/run/benchmark/process/file/Git/model operations and a bounded Frank-API client tool while enforcing the destructive boundary and producing receipts.

MCP access authority and Frank API authority are distinct tokens/scopes. Compromise of one should not automatically disclose the other.

## Acceptance

This directive is not satisfied by files or a queued workflow. It requires live VPS receipts proving:

- Frank service process is running;
- API health is reachable;
- authenticated message round-trip succeeds;
- restart/reboot recovery succeeds;
- current model/build identity is reported;
- sustained availability monitoring exists;
- secrets do not appear in committed artifacts/logs;
- direct MCP or successor control path is operational where supported.

## Compact invariant

`FINISHED_FRANK = VPS_24X7 + AUTHENTICATED_API + RECOVERY + OBSERVABILITY + NONDESTRUCTIVE_RESEARCH_CONTROL`
