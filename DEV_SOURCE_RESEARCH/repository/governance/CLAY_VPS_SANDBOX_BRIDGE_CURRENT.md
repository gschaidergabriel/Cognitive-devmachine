# CLAY VPS SANDBOX BRIDGE — CURRENT ACCESS MAP

Status: **CURRENT OPERATIONAL ACCESS DOCUMENTATION**

Purpose: prevent workers from incorrectly declaring the owner-provisioned VPS sandbox unavailable when the already-established transit/runner infrastructure exists.

## Designated sandbox

Primary development/research sandbox:

`clay-direct-dev`

Owner authority for operations inside it:

`governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md`

## Established access path A — Clay Git/SSH bridge

The retained Clay Git Bridge setup establishes SSH transit through the configured jump host to the VPS and performs work as the dedicated `claylab` user for the Git bridge path.

Retained setup route:

```text
local configured bridge
  -> SSH jump: root@100.71.48.1
  -> VPS: root@72.61.19.188
  -> dedicated bridge user: claylab
  -> /srv/claylab/git-bridge
  -> canonical repository: gschaidergabriel/clay-global-research-entity
```

The retained setup scripts configure the `claylab` GitHub SSH identity, verify repository access with `git ls-remote`, run `/root/gitbridge/scripts/install.sh`, and run `/srv/claylab/git-bridge/scripts/selftest.sh`.

Do not copy private key material into prompts, source, receipts or logs. Use the already-installed SSH configuration/identity.

## Established access path B — self-hosted GitHub runner

The controller repository `gschaidergabriel/Dr.-Unterweger` retains a self-hosted GitHub Actions execution path. Historical/current runner identity is `clay` on Linux/x64, registered under the dedicated runner account/workspace.

The retained probe workflow is:

`.github/workflows/frank-self-hosted-probe.yml`

It is `workflow_dispatch` capable and executes on `runs-on: self-hosted`.

A self-hosted runner is a transport. Destructive/high-churn research should be routed into the designated `clay-direct-dev` sandbox rather than run directly on the bare VPS host, except for operations specifically required to repair/administer the bridge/container/sandbox infrastructure.

## Worker access rule

Before claiming `NO_VPS_EXECUTOR`, `NO_SELF_HOSTED_SURFACE`, `VPS_FORBIDDEN` or equivalent:

1. resolve the newest owner authority via `CLAY_EXECUTION_AUTHORITY.md`;
2. check the existing local SSH/Clay Git Bridge path;
3. check the existing self-hosted runner path;
4. locate/enter `clay-direct-dev` through the already-configured host/container routing;
5. if the bridge/container/sandbox route is degraded, repair it under owner authority and verify a real roundtrip;
6. only then classify a concrete access failure, with exact observed evidence.

The absence of a direct SSH button/tool in one chat surface is not evidence that the configured bridge or runner does not exist.

## Intended workloads

The sandbox is intended for builds, package installation, local models/Qwen, llama.cpp-class runtimes, J-Space/vector-control work, HCU experiments, fuzzing, ablations, benchmarks, model downloads, repository cloning, scratch data and destructive-to-scratch experiments.

## Evidence boundary

Document the exact transport used, repository/source SHA, sandbox identity, command, runtime/model identity, exit status and relevant output when a result is promoted as executable evidence.

Queued workflow state is not terminal execution evidence. Bridge source/config presence is not a successful roundtrip. A successful sandbox component result is not automatically whole-product PASS.
