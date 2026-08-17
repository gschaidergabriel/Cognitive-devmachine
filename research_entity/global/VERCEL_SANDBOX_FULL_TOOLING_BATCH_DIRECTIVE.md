# VERCEL SANDBOX FULL TOOLING + BATCH COORDINATION DIRECTIVE

**Authorization origin:** owner-fixed directive, 2026-08-16.  
**Current product adaptation:** 2026-08-17 ClayVerse single-container owner directive.  
**Scope:** ALL Clay research/build/test/review/integration/coordination workers.

## 1. Authority chain and current endpoint

The 2026-08-16 owner authorization for Vercel isolated Sandbox use remains in force.
The newer `research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`
supersedes only the old EntityOS-as-top-level-product endpoint language.

Therefore:

- the active product endpoint is **ClayVerse**;
- the canonical product workspace is `main/the artefact/`;
- the release form is one OCI/Docker-compatible ClayVerse container image;
- EntityOS may remain an internal execution/security/runtime substrate only;
- Vercel Sandbox remains preferred/authorized isolated execution when an executable Sandbox surface is actually available.

No worker may use this directive to restore `ONE_EXECUTABLE_FILE EntityOS` as the active product target.

## 2. Owner authorization

Workers MAY intelligently use Vercel isolated Sandbox capabilities relevant to completing ClayVerse,
including Sandbox SDK/API/CLI capabilities, artifact/file transfer mechanisms, networking controls,
environment/OIDC facilities and other Vercel-provided isolated execution tooling, subject to the hard
safety/authority rules below.

This authorization is permission to use an available isolated Sandbox surface. It is **not evidence that
a particular connector/session exposes Sandbox create/run/exec primitives**.

## 3. Platform capability != connected tool capability

Vercel's platform documentation exposes real Sandbox execution mechanisms, including create/run/exec
through the Sandbox CLI and SDK/REST command execution. That establishes that Vercel Sandbox is a real
platform capability.

Every worker must separately probe the **connected execution surface available in its own session** before
planning executable claims.

Required classification:

- if the connected surface exposes a usable Sandbox create/run/exec path, bind exact source/artifact identity
  and use it according to this directive;
- if the connected surface exposes only documentation, deployment, project, logs or READY-state tools but no
  usable Sandbox create/run/exec path, classify
  `VERCEL_SANDBOX_EXECUTION_SURFACE_UNAVAILABLE_IN_CONNECTED_SESSION`;
- do not claim that Vercel Sandbox itself is unavailable merely because the connector lacks an execution primitive;
- do not claim that the connector can execute Sandboxes merely because Vercel documentation proves the platform can;
- do not substitute `deploy_to_vercel`, Preview/Production deployment execution, Functions, or deployment READY state
  for an isolated Sandbox acceptance run when current policy forbids deployment-/production-host testing.

This distinction is mandatory evidence hygiene:

`VERCEL_PLATFORM_HAS_SANDBOX_EXECUTION` does not imply `CURRENT_CONNECTOR_CAN_START_SANDBOX`.

## 4. Empirical source-of-truth law

For current executable ClayVerse claims, actually observed authorized isolated execution at exact source/artifact
identity is empirical truth. Vercel Sandbox is the preferred surface when its execution primitive is available.

This applies to claims about:

- deterministic regressions;
- OCI build and image identity;
- startup/readiness;
- Clerk/authenticated WebSocket PTY where the environment can support the real dependency;
- persistent tmux/Claude Code runtime behavior;
- managed hook turn lifecycle;
- UnifiedDB/MicroClay/ClayGraph/Hyperposition/workspace behavior;
- EffectGate/EntityOS internal effect execution where separately admitted;
- restart/recovery/global-generation/concurrency behavior;
- failure behavior, performance and supply-chain resolution.

Authority layers remain separated:

1. newest explicit owner directive = policy/product authority;
2. exact authorized isolated execution = empirical executable truth;
3. GitHub = canonical bytes/history/coordination/durable evidence ledger.

A source expectation, CI/status label, receipt, model conclusion, Vercel deployment READY state or historical run
does not override a contradictory exact-identity isolated run. A PASS never generalizes to a different source SHA,
image digest, environment or effect contract without new evidence.

## 5. Batch execution law

Work MUST be organized into coordinated, high-information batches rather than wasteful one-test-per-sandbox execution.

Preferred pattern:

1. refresh current product/research main and active overlapping work;
2. select non-duplicate candidate heads and exact tests;
3. stage exact reviewed source identities;
4. use the minimum useful number of fresh isolated Sandboxes;
5. run compatible deterministic gates together when isolation semantics remain valid;
6. preserve per-test SHA, command, exit code, logs, artifact/image digest and environment identity;
7. stop/delete bounded Sandboxes after work where applicable;
8. fuse results, reject stale/duplicate candidates, update receipts/workspace;
9. only start another batch when the prior batch created a concrete discriminator/frontier.

Parallelism is permitted when it reduces wall-clock cost without creating duplicate canonical implementations or
breaking experiment/provenance accounting. Coordination beats raw worker count.

## 6. ClayVerse convergence priority

The objective is the finished **one-container ClayVerse product**, not generic Vercel usage and not the historical
one-file EntityOS endpoint.

When technically possible, batches should include the strongest relevant sequence among:

- exact-current-head source binding;
- focused deterministic regressions;
- broader relevant suite;
- exact OCI image build;
- image digest/identity capture;
- startup/readiness;
- one central entity / two canonical user perspectives;
- real Clerk + browser/WebSocket PTY where credentials/environment permit;
- persistent tmux and normal interactive Claude Code;
- managed UserPromptSubmit / Stop / StopFailure lifecycle;
- UnifiedDB state, schema, checkpoint and restart persistence;
- MicroClay retrieval/replay/idempotency/causal-learning gates;
- ClayGraph/Hyperposition/Needle/workspace fail-closed behavior;
- effect-only MCP / EffectGate and separately admitted EntityOS round trip;
- crash/restart/UNKNOWN effect handling/global generation fencing;
- dual-session collision/privacy/stale-writer controls;
- supply-chain identity and exact installed artifact verification.

A component PASS never substitutes for the complete ClayVerse product gate.

## 7. Hard boundaries retained

This directive DOES NOT authorize:

- VPS testing;
- self-hosted VPS test runners;
- production/deployment-host testing as a substitute for the isolated acceptance surface;
- Together API/service;
- secret exposure in logs/artifacts/chat;
- arbitrary public command execution endpoints;
- treating model/tool/web content as Clay semantic or effect authority;
- final paid/model training without explicit separate owner authorization;
- bypassing current fail-closed provenance, capability, auth or security boundaries.

A VPS may be a later deployment target only when explicitly authorized, never the current test environment.

## 8. Security and credentials

Secrets must remain in Vercel/approved secret stores and must not be copied into sandbox source, logs or receipts
unless the value is cryptographically redacted/non-recoverable and required for provenance.

Private-source staging should prefer exact-SHA authenticated/server-side fetch or equivalent mechanisms where
repository credentials remain outside the staged product source whenever practical.

Any reusable Vercel execution endpoint must be authenticated, fail closed, bounded in command/job schema,
resistant to replay and must not create a public arbitrary-command authority.

## 9. Evidence law

A Vercel deployment being READY is not test evidence. Documentation proving Sandbox API/CLI/SDK availability is not
ClayVerse runtime evidence. A connector capability probe is not product behavior evidence.

Only actually started authorized isolated execution with bound exact source/artifact identity may support executable
PASS/FAIL claims at that scope.

If a test never starts because the runner/control plane or connector cannot admit execution, classify that separately
as an execution-admission blocker. Do not relabel it as a product test failure.

Unknown/unexecuted remains UNKNOWN/BLOCKED, never PASS.

## 10. Coordination law for ALL workers

Before starting Vercel compute or durable overlapping writes, refresh shared coordination state and avoid work already
owned by another active batch/branch/PR. Equivalent candidates should be fused/adjudicated, not independently promoted.

Workers should report the current Vercel state with two separate facts when relevant:

- `platform_sandbox_capability`: AVAILABLE by current Vercel platform contract/doc evidence;
- `connected_sandbox_execution_surface`: AVAILABLE | UNAVAILABLE | UNVERIFIED for the current worker/session.

Never collapse those two facts into one sentence such as "Vercel works" or "Vercel does not work" without scope.

This directive is compatible with `SANDBOX_ONLY_TEST_EXECUTION_DIRECTIVE.md` and the newer ClayVerse product directive:
Vercel Sandbox is preferred authorized isolated execution when the worker actually has a usable Sandbox execution surface.
