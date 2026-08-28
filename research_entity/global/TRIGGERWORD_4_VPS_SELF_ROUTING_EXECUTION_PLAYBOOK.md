# TRIGGERWORT 4 — VPS Self-Routing Execution Playbook

Status: **OWNER-DIRECTED MANDATORY OPERATIONS LAW**
Date: 2026-08-28
Purpose: make every Triggerword-4 worker able to reach, repair, use and extend the authorized VPS execution surface without waiting for the owner to explain tools, bridges, permissions or transport again.

This document is mandatory for every `triggerwort 4` run. It supplements the One-Command Autonomous Gate Driver and the Frankenstein-2.0 VPS Assembly directive.

---

## 0. Core owner instruction

Inside the designated development sandbox `clay-direct-dev`, the owner has already granted the project broad development/research execution authority.

Workers must assume **permission, not prohibition**, for ordinary project work whose effects remain inside that sandbox, subject to platform/system safety rules and current provider/economic authority.

Authorized sandbox work includes, when useful:

- arbitrary development/research shell commands;
- root/sudo inside the sandbox when available;
- package/runtime/compiler/library installation and removal;
- repository clone/fetch/build/test;
- local model downloads and execution when current provider/economic rules permit;
- compilation, fuzzing, benchmarks, ablations and failure injection;
- process start/stop/kill/restart;
- scratch DB/filesystem creation, deletion and reset;
- container/runtime repair and sandbox rebuild;
- destructive-to-scratch experiments;
- bridge/container/sandbox administration needed to restore execution.

Canonical authority files to resolve first:

```text
CLAY_EXECUTION_AUTHORITY.md
governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md
governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md
research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
```

The newest exact authority wins over older bootstrap/prose that says VPS, self-hosted execution, root or sudo are forbidden inside `clay-direct-dev`.

**Important separation:** sandbox execution authority does not override current provider/spend authority. At the time this playbook was created, provider routes are HARD_OFF/FREE_ONLY and Together is forbidden. Non-provider local/sandbox work remains allowed.

---

# 1. Mandatory interpretation rules

The following statements are **not valid blockers by themselves**:

```text
NO_DIRECT_SSH_TOOL
NO_CHAT_SSH_BUTTON
NO_REPOSITORY_BOUND_SHELL
NO_AUTHORIZED_VPS_CONNECTOR
SELF_HOSTED_UNKNOWN
SANDBOX_RUNTIME_UNKNOWN
MISSING_PACKAGE
MISSING_TEST_HARNESS
MISSING_WORKFLOW
MISSING_BRIDGE_SCRIPT
STALE_CLEAN_CHECKOUT
SANDBOX_STOPPED
CONTAINER_RUNTIME_NOT_YET_DISCOVERED
```

They mean: **self-route or build the missing route**.

Hard laws:

```text
NO_DIRECT_SSH != NO_VPS_EXECUTOR
MISSING_ROUTE != EXTERNAL_BLOCKER
MISSING_TOOL != OWNER_CONFIRMATION_REQUIRED
BROKEN_BRIDGE -> REPAIR_BRIDGE
BROKEN_SANDBOX -> REPAIR_OR_REBUILD_SANDBOX
MISSING_WORKFLOW -> BUILD_SOURCE_CONTROLLED_WORKFLOW
BLOCKED_GATE != BLOCKED_PROJECT
```

A worker may classify `BLOCKED_EXTERNAL` only after the self-resolution ladder below has been attempted or concretely falsified with evidence.

---

# 2. Execution route map

Use the first working route. Do not stop because one transport is absent.

## Route A — existing direct/local Git/SSH bridge

Current documented topology:

```text
worker/local configured bridge
  -> SSH jump: root@100.71.48.1
  -> VPS: root@72.61.19.188
  -> dedicated bridge user: claylab
  -> /srv/claylab/git-bridge
  -> canonical repo: gschaidergabriel/clay-global-research-entity
  -> sandbox: clay-direct-dev
```

Use already-installed SSH configuration/identity. Never copy private key material into prompts, source, logs or receipts.

If the current worker surface exposes a shell capable of using the configured bridge, use it.

If direct shell/SSH is absent, immediately continue to Route B or C. Absence of a chat SSH tool is not evidence the VPS is unavailable.

---

## Route B — existing controller self-hosted GitHub runner

Controller repository:

```text
gschaidergabriel/Dr.-Unterweger
```

Known operational workflow patterns include:

```text
.github/workflows/frank-self-hosted-probe.yml
.github/workflows/clay-grid10-cognitive-envelope-vps.yml
.github/workflows/clay-exact-branch-bridge-vps-v2.yml
```

The important execution property is:

```yaml
runs-on: [self-hosted, Linux, X64]
```

or equivalent `runs-on: self-hosted`.

These workflows demonstrate the intended bridge pattern:

```text
GitHub commit/push/workflow
 -> registered self-hosted Linux/x64 runner
 -> discover clay-direct-dev
 -> enter sandbox
 -> clone/fetch exact source branch/SHA
 -> execute bounded commands/tests
 -> write exact receipt/artifacts
 -> commit receipt back to repository
```

Triggerword-4 workers with GitHub write access may modify/create a dedicated workflow in the controller repo when an existing workflow does not cover the current gate.

Do not wait for the owner to author the workflow.

---

## Route C — self-hosted workflow in the Clay repository

The Clay repository itself contains a working self-hosted sandbox discovery pattern:

```text
.github/workflows/clay-direct-dev-roundtrip.yml
```

It demonstrates:

- owner-authenticated dispatch;
- `runs-on: [self-hosted, Linux, X64]`;
- sandbox runtime discovery;
- execution inside `clay-direct-dev`;
- durable receipt writeback.

The historical generation-0 roundtrip dispatch is quarantined because of prior issue fan-out. Do **not** create duplicate generation-0 issues.

For new work, either:

1. use an existing controller workflow;
2. create a new stable dispatch class/generation with explicit dedupe semantics; or
3. create a dedicated push-triggered workflow for the exact gate.

Prefer push/path-triggered source-controlled workflows when possible because they are easier to make singleton/idempotent than issue fan-out.

---

## Route D — build a new source-controlled bridge yourself

If no existing route exactly fits the gate, Triggerword 4 is explicitly authorized to build one.

Preferred pattern:

```text
1. create/modify one workflow file in gschaidergabriel/Dr.-Unterweger or the Clay repo;
2. trigger only on an exact branch/path or one explicit dispatch key;
3. runs-on self-hosted Linux/x64;
4. checkout/fetch exact source branch;
5. resolve and freeze exact source SHA before execution;
6. discover clay-direct-dev;
7. enter sandbox;
8. run a source-controlled script/test, not untrusted issue-body shell text;
9. persist receipt with source/runtime/exit/output identities;
10. push receipt using retry + rebase;
11. use concurrency/dedupe to prevent stampede.
```

A missing executor bridge is therefore normally an engineering task, not an owner-dialog blocker.

---

# 3. Sandbox discovery and entry

From a self-hosted runner/host, try in this order:

```bash
docker inspect clay-direct-dev
sudo -n docker inspect clay-direct-dev
podman inspect clay-direct-dev
incus info clay-direct-dev
lxc info clay-direct-dev
```

Corresponding execution forms:

```bash
docker exec clay-direct-dev sh -lc '<command>'
sudo -n docker exec clay-direct-dev sh -lc '<command>'
podman exec clay-direct-dev sh -lc '<command>'
incus exec clay-direct-dev -- sh -lc '<command>'
lxc exec clay-direct-dev -- sh -lc '<command>'
```

Do not assume Docker specifically. Existing workflows deliberately probe Docker, sudo-Docker, Podman, Incus and LXC.

If the sandbox exists but is stopped/broken, repair/start/rebuild it under owner authority.

If the container runtime is broken, repair the runtime/bridge on the host as required to restore the designated sandbox, while avoiding unrelated host services.

---

# 4. Exact-source execution law

Never test an unspecified moving checkout and call it target evidence.

Before material execution:

```text
source_repository
source_branch
source_sha
source_tree
working_tree_clean
current authority identity
sandbox identity
transport identity
```

must be known/bound where relevant.

Typical pattern inside the sandbox:

```bash
WORK=/tmp/trigger4-$RUN_ID
rm -rf "$WORK"
git clone --filter=blob:none --no-checkout https://github.com/gschaidergabriel/clay-global-research-entity.git "$WORK"
cd "$WORK"
git fetch --force origin "refs/heads/$SOURCE_BRANCH:refs/remotes/origin/trigger4-target"
git checkout --detach "$SOURCE_SHA"
test "$(git rev-parse HEAD)" = "$SOURCE_SHA"
```

If private-clone authentication is unavailable inside the sandbox, use the runner checkout as source and copy/archive the exact bound tree into the sandbox, or use the already-installed Git/SSH bridge identity. Build the smallest reliable transport rather than declaring the project blocked.

---

# 5. VPS control-sync toolbox

A stale checkout is a repair problem, not automatically a blocker.

Existing tools:

```text
tools/vps_control_sync_bootstrap_v2.py
tools/vps_control_sync_refresh_v1.py
tools/vps_control_sync_guard_v1.py
```

## 5.1 Bootstrap v2

Use when the owning checkout may be stale and you need the exact newest refresh tool without mutating the owning worktree.

Conceptual command:

```bash
python3 tools/vps_control_sync_bootstrap_v2.py \
  --repo /path/to/checkout \
  --run-tests \
  --capsule-dir /tmp/trigger4-control-bootstrap \
  --receipt /tmp/trigger4-control-bootstrap.json
```

It fetches current `main` over HTTPS into a namespaced ref, extracts exact current refresh/test bytes outside the owning checkout, can run regression tests in a detached worktree and grants only bootstrap/capsule scope.

## 5.2 Refresh v1

Use on a clean checkout when local HEAD is an ancestor of current remote `main` and current authority validates.

Conceptual command:

```bash
python3 /tmp/trigger4-control-bootstrap/vps_control_sync_refresh_v1.py \
  --repo /path/to/checkout \
  --apply \
  --receipt /tmp/trigger4-control-refresh.json
```

It uses HTTPS Git transport and only fast-forwards after fail-closed authority checks.

## 5.3 Guard v1

Use to prove that an existing checkout is clean, exactly at current GitHub `main`, authority-coherent and source-bound before later runtime work.

Conceptual command:

```bash
python3 tools/vps_control_sync_guard_v1.py \
  --repo /path/to/checkout \
  --receipt /tmp/trigger4-control-guard.json
```

If it fails because the checkout is stale, use bootstrap/refresh instead of reporting `NO_EXECUTION_AUTHORITY` as a terminal project blocker.

---

# 6. GitHub tool/connector toolbox for workers

When a worker has GitHub connector/API access but no shell, GitHub is the control-plane bridge.

Use it to:

- fetch current authority/protocols/checkpoints;
- inspect exact branches/commits/files/workflows;
- create/update source files and test scripts;
- create/update a controller workflow;
- create a branch or PR when isolation is useful;
- inspect commit/workflow results;
- write dispatch/trigger files;
- persist receipts/checkpoints;
- deduplicate concurrent work by current branch/head/content SHA.

The absence of a shell tool in the conversational environment therefore does not prevent source-controlled VPS execution if the self-hosted runner path is operational.

---

# 7. Existing reusable controller examples

## 7.1 Health / sandbox liveness

`gschaidergabriel/Dr.-Unterweger:.github/workflows/frank-self-hosted-probe.yml`

Use its discovery pattern to establish whether the runner can enter `clay-direct-dev`.

## 7.2 GRID10 runtime in clay-direct-dev

`gschaidergabriel/Dr.-Unterweger:.github/workflows/clay-grid10-cognitive-envelope-vps.yml`

This is a direct example of:

```text
exact branch/SHA
 -> self-hosted runner
 -> clay-direct-dev
 -> compile/tests/runtime checks
 -> receipt persistence
```

Adapt it rather than rediscovering the bridge.

## 7.3 Exact branch execution bridge

`gschaidergabriel/Dr.-Unterweger:.github/workflows/clay-exact-branch-bridge-vps-v2.yml`

This is a reusable example for cloning/fetching exact Clay branches and running bounded commands while persisting source identities/results.

When Triggerword 4 needs repository-bound execution of a current gate, this workflow family is usually the closest donor.

---

# 8. Self-repair ladder before BLOCKED_EXTERNAL

A Triggerword-4 worker must walk this ladder automatically:

```text
A. resolve newest authority
B. re-enter current branch/checkpoint
C. try local/direct bridge if shell exists
D. inspect/reuse controller self-hosted workflows
E. inspect/reuse Clay self-hosted workflow path
F. discover docker/sudo-docker/podman/incus/lxc sandbox route
G. repair/start/rebuild sandbox/runtime if needed
H. bootstrap/refresh stale checkout
I. install missing packages/tools inside sandbox
J. create missing test harness/script
K. build a new dedicated source-controlled self-hosted workflow if needed
L. persist exact failure evidence and try alternate route
M. only then consider BLOCKED_EXTERNAL
```

A worker must not stop at steps C–K merely because the route is inconvenient or undocumented in its immediate context.

---

# 9. What counts as a genuine external blocker

Only classify a blocker as truly external after the self-resolution ladder is exhausted.

Examples:

- registered self-hosted runner is unavailable/offline **and** the configured Git/SSH bridge cannot be reached/repaired from any available authorized tool;
- required credential/account permission is absent and no authorized secret/connector/route can provide it;
- physical microphone/camera/device action is required and no test seam can substitute;
- a new irreversible real-world/production effect lies outside standing authority;
- owner intent is genuinely ambiguous between mutually exclusive product outcomes.

Even then, continue all independent work and persist the exact unblock condition.

---

# 10. Receipt requirements for VPS/runner evidence

A promoted execution receipt should bind as applicable:

```text
transport
controller repo/workflow/run id
runner name/os/arch/hostname
sandbox = clay-direct-dev
container runtime
source repository
source branch
source SHA/tree
working-tree state
current authority identity/hash
command/test identity or script digest
runtime/toolchain identity
start/end timestamp
exit code
stdout/stderr or digest + useful bounded tail
secret_values_recorded = false
provider_calls/spend scope
exact evidence scope
```

Queued workflow != execution.

Workflow failure with `runner_id=0` or zero executed steps != product/test failure.

Component PASS != whole EntityOS/HCU PASS.

---

# 11. Anti-stampede / concurrency law

Because many Triggerword-4/5 workers can run concurrently:

- use stable gate/job identities;
- use workflow concurrency groups;
- do not create repeated issue-trigger fan-out;
- dedupe against existing receipt paths;
- use create-only claims where useful;
- refresh before write;
- if a CAS/write conflict occurs, refetch and semantically merge;
- do not overwrite a newer checkpoint with stale state;
- if another worker already built the bridge/job, reuse it.

`REPEATED_TRIGGER4_MUST_CONVERGE_NOT_STAMPEDE`.

---

# 12. Triggerword-4 worker behavioral mandate

When a worker reads `triggerwort 4`, the expected mental model is:

```text
I already have permission for ordinary project work inside clay-direct-dev.
I do not need the owner to tell me how to reach the VPS.
If direct SSH is absent, GitHub + self-hosted runner is a bridge.
If an existing bridge does not fit, I can build a source-controlled bridge.
If the sandbox/runtime is broken, I can repair/rebuild it.
If the checkout is stale, I can bootstrap/refresh it.
If a tool/package/test is missing, I can install/build it.
I preserve provider/spend and external-effect boundaries.
I only ask the owner after all reasonable self-resolution routes are exhausted.
```

---

# 13. Correction to stale Triggerword-4 checkpoints

Any checkpoint field equivalent to:

```text
BLOCKED_NO_REPOSITORY_BOUND_SHELL_OR_AUTHORIZED_VPS_CONNECTOR
```

is now interpreted as **STALE / SELF-RESOLUTION REQUIRED**, unless it contains concrete evidence that all routes in this playbook were attempted/falsified after this playbook became current.

Therefore the active GRID10 repository-bound SIGKILL gate must be routed through the existing/self-built VPS execution path rather than left parked merely because the current chat surface lacks a shell.

---

# 14. Final law

```text
TRIGGERWORT_4_VPS_EXECUTION =
  RESOLVE_AUTHORITY
  -> SELECT_EXISTING_ROUTE
  -> OR_BUILD_ROUTE
  -> REPAIR_TRANSPORT_IF_NEEDED
  -> ENTER_CLAY_DIRECT_DEV
  -> BIND_EXACT_SOURCE
  -> EXECUTE
  -> VERIFY
  -> PERSIST_RECEIPT
  -> PROMOTE_OR_REPAIR
  -> CONTINUE
```

The owner should not need to repeat these instructions again.
