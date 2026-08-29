# CLAY EXECUTION AUTHORITY

## Active newest owner authority

The newest explicit user/owner execution authority is:

`governance/CLAY_VPS_SANDBOX_FULL_EXECUTION_AUTHORITY_2026-08-25.md`

It is the current authority for the designated VPS sandbox `clay-direct-dev` and supersedes older statements such as `VPS testing: FORBIDDEN`, `self-hosted VPS test runners: FORBIDDEN`, zero-cost-command-only restrictions, or blanket no-root/no-sudo rules **inside that sandbox**.

The earlier dual-machine authority remains valid where it does not conflict:

`governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md`

Current bridge/access documentation:

`governance/CLAY_VPS_SANDBOX_BRIDGE_CURRENT.md`

External solution discovery/reproduction/adaptation is defined operationally in:

`governance/CLAY_EXTERNAL_SOLUTION_HARVEST_LOOP.md`

Mandatory end-of-`go` collective recursive-improvement measurement is defined in:

`governance/CLAY_GO_COLLECTIVE_RECURSIVE_IMPROVEMENT_METRICS_2026-08-24.md`

All ChatGPT/local/VPS development lanes must resolve this file before coordinated `go`/`zero`/trigger execution.

## FREE_ONLY semantics — owner clarification 2026-08-29

`FREE_ONLY` is a **token/provider/spend policy**, not an owner-infrastructure ban.

The term MUST be interpreted consistently across all Clay, EntityOS, HCU, GRID10 and Frankenstein directives as follows:

- **ALLOWED AND EXPECTED:** owner-provisioned VPS execution through the established VPS Bridge; `clay-direct-dev`; self-hosted builds, tests, benchmarks, local-model work, containers and repo-native/local development on owner infrastructure, subject to active sandbox resource/service-health guards.
- **ALLOWED:** external model/API/provider routes only when the concrete route is admitted and guaranteed zero-monetary-cost under the current provider/economic provenance rules.
- **FORBIDDEN UNDER FREE_ONLY:** paid third-party model/API tokens, paid external cloud/provider compute, subscription/unknown-cost fallback, hidden spend, or any route that can silently become billable.
- The owner VPS, VPS Bridge and `clay-direct-dev` MUST NOT be classified as `external paid compute`, `paid fallback`, `forbidden self-hosted execution`, or a forbidden production surface merely because they are remote from the chat runtime.
- Older cached or historical wording such as `VPS testing: FORBIDDEN`, `self-hosted VPS test runners: FORBIDDEN`, `no VPS/self-hosted testing`, or `AUTHORIZED_ISOLATED_FREE_SANDBOX_ONLY` is superseded wherever it conflicts with the active owner VPS authority.
- When a stale cache conflicts with this file or the active owner authority, **the stale cache loses**. Workers must refresh the current authority instead of failing closed against the owner VPS Bridge.

### Token-policy consequence

`FREE_ONLY` means **free tokens only** for external model/API inference. A directive that previously permitted a model/provider because the owner had a subscription does not by itself authorize use under `FREE_ONLY`. In particular, any older Triggerword-4 text permitting GLM/Z.AI or another provider under a `subscription context` is superseded for token execution unless the exact route used is currently admitted as zero-monetary-cost.

Provider-token policy and compute-surface policy are separate axes:

```text
FREE_ONLY_PROVIDER_POLICY != NO_VPS
FREE_ONLY_PROVIDER_POLICY != NO_SELF_HOSTED_RUNNER
FREE_ONLY_PROVIDER_POLICY != NO_LOCAL_MODEL
OWNER_VPS_COMPUTE + FREE_PROVIDER_TOKENS = ALLOWED
OWNER_VPS_COMPUTE + PAID_OR_UNKNOWN_COST_PROVIDER_TOKENS = FORBIDDEN_UNDER_FREE_ONLY
```

This clarification does not relax unrelated effect, evidence, platform-safety, secret-handling or resource-health boundaries.

## Triggerword-4 VPS/bridge resolution — owner clarification 2026-08-29

For Triggerword 4, the VPS authority question is **resolved**, not pending:

- `clay-direct-dev` is the intended Frankenstein-2.0 build/test/runtime sandbox.
- The established self-hosted runner/VPS Bridge is an ordinary authorized execution transport.
- Absence of a direct chat SSH tool is not `NO_EXECUTOR`; workers must use the prepared bridge/runner path.
- A stale bootstrap, cached supervisor sentence, or historical FREE_ONLY clause must not cause a fresh `VPS_AUTHORITY_AMBIGUOUS`, `VPS_FORBIDDEN`, `SELF_HOSTED_FORBIDDEN`, or equivalent stop when this file and the active VPS authority are reachable.
- No separate supervisor re-authorization is required for ordinary build/test/runtime work that stays inside the already-authorized `clay-direct-dev` sandbox. A newer explicit owner instruction may modify or revoke this; a non-authority cache may not.
- Triggerword-4 owner authorization also permits coordinated useful VPS load up to the currently declared shared envelope of approximately 70% aggregate usable compute capacity, with service-health, memory/I/O and recovery headroom guards. The branch binding `research_entity/global/TRIGGERWORD_4_MAXIMUM_EXECUTION_BUDGET_BINDING.md` carries the detailed coordination law.
- Runtime executed through the bridge is real target-environment execution evidence when exact source/runtime/execution identity and result receipts are captured. It must not be downgraded merely because transport is a self-hosted runner.

Authority resolution order for this question:

```text
NEWEST_EXPLICIT_OWNER_DIRECTION
  > CLAY_EXECUTION_AUTHORITY.md + active owner VPS authority
  > admitted supervisor policy where non-conflicting
  > stale bootstrap/cache/history
```

A supervisor artifact explicitly marked `NON_AUTHORITY` cannot revoke or suspend this owner VPS authorization.

## Current operational meaning

- `clay-direct-dev` is an owner-provisioned isolated VPS development/research sandbox, not a forbidden production surface;
- inside `clay-direct-dev`, development/research commands are broadly authorized, including sandbox root/sudo when available, package installation, compilation, downloads, local-model execution, Qwen experiments, tests, fuzzing, benchmarks, ablations and destructive-to-scratch work;
- the already-established bridge/runner paths should be used rather than declaring `NO_EXECUTOR` merely because a direct chat SSH action is absent;
- bridge/container/sandbox administration required to restore or improve sandbox execution is authorized under the owner authority;
- unrelated host services, unrelated production effects and external provider spending remain separate boundaries;
- platform/system safety rules and canonical evidence/effect laws remain in force;
- source/component/local experiment success never automatically becomes whole EntityOS/HCU PASS.
