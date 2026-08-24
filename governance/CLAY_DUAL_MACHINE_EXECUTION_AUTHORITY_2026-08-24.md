# CLAY DUAL-MACHINE EXECUTION AUTHORITY — 2026-08-24

Status: ACTIVE USER AUTHORITY
Scope: ChatGPT-operated development using (1) the local Linux workstation bridge and (2) the VPS bridge/sandbox.

## Core `go` semantics

A user `go` triggers a coordinated development/research cycle. The cycle is expected to use the available local workstation and VPS sandbox aggressively where useful, rather than waiting for manual terminal copy/paste.

Every `go` MUST begin by checking the VPS bridge/sandbox health. If degraded, repair/extend/improve the sandbox or its minimum bridge/container infrastructure, verify the repair with a real roundtrip receipt, then continue substantive EntityOS/HCU work.

## VPS sandbox authority

Inside `clay-direct-dev`, broad development and research freedom is authorized. This includes installing packages, compiling, running tests, fuzzing, ablations, synthetic experiments, cloning/testing public GitHub tools, downloading/testing models, generating/removing scratch data, benchmarking, and repeated experimental iteration.

The user explicitly authorizes host-side changes that are necessary to repair, rebuild, resize, reconfigure, extend, observe, or otherwise administer the sandbox and its bridge/container/runtime infrastructure.

Do not intentionally exhaust disk, RAM, process tables, or other host resources. Check free space before large downloads and clean obsolete models, caches, builds, snapshots, and scratch data when needed.

## VPS host boundary

Unrelated VPS-host changes outside sandbox/bridge administration require fresh user approval. The standing sandbox authority is not a blanket authorization for unrelated host services, accounts, firewall rules, production systems, or arbitrary host-root changes.

## Local workstation authority

The local bridge may be used as the user's normal Linux development user for programming, files, repositories, builds, tests, shell commands, long-running jobs, persistent tmux sessions, and SSH transit to the VPS where already configured.

The local bridge does not grant automatic root. Actions requiring new sudo/root authority remain subject to the local machine's existing authorization path and any user approval required by that path.

## Coordination

Prefer the VPS sandbox for risky, messy, high-churn, large-download, destructive-to-scratch, or unusual research. Prefer the local workstation for interactive development, persistent tmux workflows, editing/build orchestration, and SSH transit. Use both in the same `go` cycle when that materially improves speed or evidence quality.

## Deployment/effects boundary

Deployment inside the authorized sandbox, to development/test branches, or to already-authorized project infrastructure may proceed as part of a `go` cycle. New external production effects, unrelated external accounts/services, or host-level changes outside the boundaries above still require the relevant explicit authority.

## Evidence/canonical boundary

Sandbox and local experiments are evidence/candidates only until admitted by the project's canonical evidence/authority rules. A successful experiment, model run, component test, or deployment does not by itself mint whole-product/HCU canonical runtime credit.

## Operational objective

On `go`: coordinate, execute, test, break/rebuild scratch environments when useful, compare alternatives, run ablations, deploy development artifacts, collect receipts/evidence, fix recurring infrastructure weaknesses, and keep iterating toward EntityOS + HCU without requiring the user to manually relay routine shell commands.
