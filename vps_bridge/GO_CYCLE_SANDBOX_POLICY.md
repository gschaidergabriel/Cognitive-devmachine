# GO cycle sandbox policy

Status: ACTIVE USER AUTHORITY
Scope: ChatGPT-controlled VPS development sandbox `clay-direct-dev` and its bridge infrastructure.

## Mandatory preflight on every `go`

Before doing substantive EntityOS/HCU work, ChatGPT must inspect the VPS bridge and sandbox health. At minimum inspect:

- return-channel freshness / latest `LIVE.json`
- sandbox process/execution proof
- free disk space and workspace/cache growth
- available memory and load
- current canonical workspace Git state / staleness
- bridge daemon responsiveness
- outbound network availability when relevant

A `go` cycle may not silently assume the sandbox is healthy merely because a previous cycle passed.

## Repair / improvement authority

The user explicitly authorizes ChatGPT to repair, rebuild, restart, extend, reconfigure, resize, replace, or improve the VPS sandbox and the minimum host-side bridge/container infrastructure needed to operate that sandbox, without asking again each time.

This standing authorization includes changes such as:

- container image/toolchain changes
- rootless Podman/runtime/cgroup/network/storage configuration needed for the sandbox
- bridge daemon/service repair
- sandbox mounts, caches and workspace organization
- telemetry and observability improvements
- experimental tooling installed in the sandbox

This authorization does **not** extend to unrelated host-level changes outside sandbox/bridge administration. Any unrelated action on the VPS host requires fresh user approval.

## Experimental freedom inside the sandbox

Inside `clay-direct-dev`, broad research/development freedom is authorized. ChatGPT may run ordinary or unusual experiments and ablations, clone/test public GitHub tools, download/test models, compile projects, install packages, fuzz/probe software, create/remove scratch data, and iterate aggressively.

Experiments remain non-canonical evidence until separately admitted by the project's canonical evidence/authority rules.

## Storage guardrail

The sandbox must actively watch disk consumption. Prefer keeping a substantial reserve rather than filling the host. Before large model/tool downloads, inspect free space; clean obsolete model copies, build artifacts, caches, snapshots and scratch data when needed. Do not intentionally exhaust disk, RAM, process tables, or other host resources.

## Failure behavior

If the sandbox or bridge is degraded during a `go` cycle:

1. diagnose the failure;
2. repair it using the standing sandbox/bridge authority;
3. verify the repair with an actual command/receipt roundtrip;
4. improve observability or robustness when a recurring failure mode is discovered;
5. only then continue the substantive `go` research/development cycle.

If repair would require an unrelated host-level action outside the standing sandbox/bridge scope, stop and request user approval for that specific action.
