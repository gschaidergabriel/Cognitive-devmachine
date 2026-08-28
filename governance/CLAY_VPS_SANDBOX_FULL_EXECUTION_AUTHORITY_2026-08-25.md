# CLAY VPS SANDBOX FULL EXECUTION AUTHORITY — 2026-08-25

Status: **ACTIVE USER / OWNER AUTHORITY**

This is the newest explicit owner execution authority for the designated VPS development sandbox. It supersedes any older statement that says VPS testing is forbidden, self-hosted VPS execution is forbidden, `clay-direct-dev` is zero-cost-command-only, or root/sudo is categorically forbidden **inside the designated sandbox**.

Where this file conflicts with `governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md`, this file wins. Stable EntityOS/HCU truth, evidence and effect-boundary laws remain unchanged unless explicitly changed here.

## Owner directive

**Everything needed for development, research, testing and experimentation is authorized inside the designated VPS sandbox `clay-direct-dev`.**

Workers must not treat the VPS sandbox as a forbidden self-hosted/production surface. It is an owner-provisioned isolated development and research execution surface intended for direct use by Clay/EntityOS/HCU workers.

## Explicitly authorized inside `clay-direct-dev`

Inside the sandbox workers may, without asking for routine additional approval:

- execute arbitrary development/research shell commands consistent with platform/system safety rules;
- use root/sudo **inside the sandbox** when available;
- install, remove, upgrade and reconfigure packages, runtimes, compilers, libraries and developer tools;
- clone/fetch repositories and download public models, datasets, papers, binaries and artifacts;
- download and run Qwen models, including Qwen3-0.6B or any other model that fits the available resources;
- compile native code and runtimes including llama.cpp-class tooling and model-control/intervention tooling;
- create, modify and delete files, databases, caches, virtualenvs, containers/namespaces subordinate to the sandbox, model stores and scratch workspaces;
- start, stop, kill, restart, freeze, snapshot, clone or replace sandbox processes and synthetic/model instances;
- run tests, fuzzers, benchmarks, profilers, ablations, causal interventions, vector-control experiments, adversarial synthetic-agent/model experiments and destructive-to-scratch trials;
- use outbound network access for ordinary research/development retrieval and already-authorized services;
- persist reusable model/cache/build assets inside the sandbox when useful;
- clean, rebuild, reset or replace the sandbox when that is the fastest reliable route forward.

The default interpretation is **permission, not prohibition**, for operations whose effects remain inside the authorized sandbox.

## Bridge and sandbox administration

Host-side changes that are necessary to reach, repair, rebuild, resize, reconfigure, observe or administer the designated sandbox and its bridge/container/runtime infrastructure remain authorized under the existing dual-machine authority.

This includes repairing the already-established Clay Git/SSH transit, runner-to-sandbox routing, container runtime, mounts/volumes and sandbox lifecycle plumbing when required to restore sandbox execution.

Do not intentionally exhaust host disk, RAM, process tables or network resources. Check headroom before large model/dataset downloads and clean obsolete caches/builds/models/scratch data when useful.

## Access-path rule

Workers must use the already-prepared bridge/sandbox path rather than declaring VPS execution unavailable merely because a direct chat SSH tool is absent.

The current bridge/access documentation is:

`governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md`

A self-hosted GitHub runner is an execution transport, not by itself permission to run destructive research on the bare host. High-churn/destructive work should be routed into `clay-direct-dev` unless the operation is specifically bridge/sandbox administration.

## External-effect and spend boundary

Internal sandbox freedom does **not** automatically authorize unrelated real-world or third-party effects outside the sandbox. Existing platform/system safety rules still apply.

Paid-provider spend, subscriptions, unrelated production changes, attacks on third parties, credential theft/exfiltration and unrelated host services are not made permissible merely because a command originates inside the sandbox. Provider-specific economic/credential rules remain separate unless a newer explicit owner instruction changes them.

Ordinary public downloads and local execution of downloaded models/tools inside the sandbox are authorized.

## Evidence law

Sandbox execution is real executable evidence only at its exact observed source/model/runtime/environment/command/result scope. Preserve exact source SHA, model/checkpoint/tokenizer/runtime/build identity, commands, exit status and receipts where they matter for promotion.

Source presence is not execution. A queued runner job is not a terminal result. A successful local component experiment is not whole EntityOS/HCU PASS unless the canonical acceptance rules promote it.

## `go` / `zero` consequence

On `go` and `zero`, workers should use the VPS sandbox aggressively when it materially improves information gain, speed or reproducibility. Local Qwen/model experimentation, J-Space/vector-control causality work, HCU experiments, compilation and destructive-to-scratch research are first-class intended uses of this sandbox.

Do not stop at `VPS_FORBIDDEN`, `SELF_HOSTED_FORBIDDEN`, `NO_ROOT_IN_SANDBOX` or `NO_EXECUTOR` when the designated sandbox/bridge can perform the work.
