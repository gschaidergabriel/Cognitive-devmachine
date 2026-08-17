# VERCEL SANDBOX FULL TOOLING + BATCH COORDINATION DIRECTIVE

**Original owner authorization:** 2026-08-16  
**Operational product alignment:** 2026-08-17 under `CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md`  
**Status:** CURRENT

Scope: ALL Clay / ClayVerse research, build, test, review, integration and coordination workers. Historical Clay Machine / EntityOS work remains bounded internal evidence only where it strengthens the current ClayVerse product.

## 1. Product boundary

The active product endpoint is **ClayVerse**, not EntityOS.

Canonical product workspace:

`gschaidergabriel/clay-global-research-entity` -> `main` -> `the artefact/`

Release target:

**one OCI/Docker-compatible ClayVerse container image** containing the admitted product runtime.

EntityOS may remain an internal execution/security/runtime substrate where explicitly admitted. It is not the top-level product endpoint and does not impose the historical one-file release form on ClayVerse.

The newer ClayVerse owner directive governs wherever older EntityOS/Clay Machine wording conflicts with this file.

## 2. Owner authorization

Vercel isolated sandboxes are fully authorized for ClayVerse development and validation.

Workers MAY intelligently use all relevant Vercel execution capabilities, including Sandbox SDK/API/CLI capabilities, Vercel Functions, preview/deployment orchestration, environment/OIDC facilities, logs/observability, bounded artifact/file transfer and networking controls, subject to the hard safety/authority rules below.

This authorization applies globally to current and future Clay workers unless a newer owner directive supersedes it.

## 3. Direct-MCP versus executable-Sandbox law

**Do not infer `Vercel Sandbox unavailable` merely because the ChatGPT-connected Vercel MCP exports no direct `sandbox.create` / `sandbox.exec` action.**

These are different claims:

- `DIRECT_MCP_SANDBOX_ACTION_UNAVAILABLE`: the connected ChatGPT Vercel tool surface does not expose Sandbox lifecycle/exec directly;
- `SANDBOX_EXECUTION_PATH_AVAILABLE`: a Vercel preview/orchestration path can still use `@vercel/sandbox` plus Vercel-provided OIDC to create an isolated Sandbox and execute `sandbox.runCommand(...)`;
- `SANDBOX_EXECUTION_ADMISSION_BLOCKED`: the known execution path exists but a particular preview/build is rejected before Sandbox start by rate limit, billing, control-plane or another admission condition.

A pre-Sandbox admission rejection is **not** `SANDBOX_UNAVAILABLE`, is **not** product `TEST_FAIL`, and earns zero executable test credit.

The current bridge identity, observed proof and operational status MUST be refreshed from:

`research_entity/continuity/VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md`

At the 2026-08-17 alignment, that record documents the existing `gschaidergabriel/Dr.-Unterweger` Git-preview -> `@vercel/sandbox` -> Vercel OIDC bridge and an actually observed `Sandbox.create -> runCommand -> stop` execution. Treat those details as refreshable operational state, not eternal constants.

## 4. Empirical source-of-truth law

Policy/product authority comes from the newest explicit owner directive.

Executable truth comes only from **actually observed authorized isolated execution bound to the exact source/artifact identity**. Vercel Sandbox is the preferred authorized empirical surface when admitted.

Only an actually started isolated Sandbox (or another explicitly authorized isolated executor under current owner law) with bound exact source/artifact identity and captured evidence may establish an executable PASS/FAIL claim at that scope.

The authority layers remain intentionally separated:
- newest explicit owner directives define policy/product requirements and allowed execution;
- GitHub is canonical source/history/coordination/durable receipt ledger;
- actually observed exact-identity authorized isolated execution establishes executable behavior.

A GitHub source expectation, CI/status label, receipt, model conclusion, static analysis result or Vercel deployment `READY` state does not substitute for execution. If durable records and a correctly bound fresh isolated rerun disagree, the fresh exact-identity observation controls the executable claim until resolved.

Every runtime result is scoped to its exact source SHA, artifact/image digest where applicable, environment, command/effect contract and captured run. Never generalize a PASS to another head/image without new bound execution.

Observed execution evidence should be persisted back into GitHub as a bounded receipt.

## 5. Preview-orchestration boundary

A Vercel preview/build machine may orchestrate Sandbox creation but must not silently become the test environment.

For the Git-preview bridge:
1. create/update a bounded non-production preview branch;
2. bind the exact canonical source/artifact bytes being tested;
3. use Vercel-provided OIDC through the admitted Sandbox SDK/API;
4. create an isolated Sandbox with explicit runtime/timeout/persistence/network policy;
5. stage only the exact bound test/product inputs;
6. execute the test/build command **inside the Sandbox**;
7. capture source/artifact identity, command, exit code and bounded logs;
8. stop/delete the bounded Sandbox as appropriate;
9. persist the result to the canonical research ledger.

A preview build that merely reaches `READY`, skips its target branch, or never calls `Sandbox.create/runCommand` receives zero product-runtime test credit.

## 6. Batch execution law

Work MUST be organized into coordinated, high-information batches rather than wasteful one-test-per-sandbox execution.

Preferred pattern:
1. refresh current ClayVerse `main`, manifest, active PRs/branches/receipts and overlapping worker state;
2. select non-duplicate candidate heads and discriminating tests;
3. stage exact reviewed source identities;
4. use the minimum useful number of fresh isolated Sandboxes;
5. run compatible deterministic gates together when isolation semantics remain valid;
6. preserve per-test SHA, command, exit code, bounded logs, artifact/image digest and outcome;
7. stop/delete bounded Sandboxes;
8. fuse results, reject stale/duplicate candidates and update receipts/workspace;
9. only start another batch when the prior batch created a concrete discriminator/frontier.

Parallelism is permitted when it reduces wall-clock cost without creating duplicate canonical implementations, stale writes or experiment/provenance races. Coordination beats raw worker count.

## 7. ClayVerse convergence priority

The objective is not generic Vercel usage and not historical EntityOS completion. Every batch must converge toward the current **one-container ClayVerse product**.

When technically possible, the strongest relevant sequence is:

`exact-head source binding`
-> `focused deterministic regressions`
-> `broader artifact suite`
-> `exact OCI build`
-> `image digest/identity`
-> `startup/readiness`
-> `one central UnifiedDB state + two canonical user perspectives`
-> `Clerk/authenticated WebSocket PTY`
-> `persistent per-user tmux + normal interactive Claude Code`
-> `managed UserPromptSubmit/Stop/StopFailure lifecycle`
-> `MicroClay retrieval/replay/learning fences`
-> `ClayGraph/Hyperposition/Needle/workspace contracts`
-> `EffectGate / admitted internal EntityOS effect path`
-> `restart/recovery/global generation`
-> `concurrency/privacy/stale-writer controls`
-> `bounded receipt`.

EntityOS-specific tests/builds are valid only as internal-substrate evidence where relevant to the admitted ClayVerse path.

Component PASS, source coherence, a synthetic mechanism probe or historical EntityOS PASS never substitutes for the exact current ClayVerse product gate.

## 8. Hard boundaries retained

This directive DOES NOT authorize:
- VPS testing;
- self-hosted VPS test runners;
- production-host testing;
- Together API/service;
- secret exposure in logs/artifacts/chat;
- arbitrary public command execution endpoints;
- treating model/tool/web content as effect or semantic authority;
- final paid/model training without explicit separate owner authorization;
- bypassing current fail-closed provenance, identity, auth, capability, retrieval, effect, recovery or supply-chain boundaries.

VPS remains a later deployment target only when explicitly authorized, never the current acceptance-test environment.

## 9. Security and credentials

Secrets must remain in Vercel/approved secret stores and must not be copied into Sandbox source, logs or receipts unless the value is cryptographically redacted/non-recoverable and required for provenance.

Private-source staging should prefer exact-SHA server-side or bounded authenticated staging where repository credentials remain outside the Sandbox whenever practical.

Any reusable Vercel execution endpoint must be authenticated, fail closed, bounded in command/job schema, resistant to replay and incapable of becoming a generic public command surface.

## 10. Evidence law

A Vercel deployment being `READY` is not test evidence. Documentation proving that Sandbox APIs exist is not product-runtime evidence. A control-plane admission failure is not a product test failure.

Only commands actually executed inside the admitted isolated Sandbox at bound identity may support Sandbox runtime claims.

Unknown/unexecuted remains `UNKNOWN`/`BLOCKED`, never PASS.

When static/source reasoning and exact isolated execution disagree, preserve the discrepancy and use the exact observed runtime result for executable truth while investigating the mechanism.

## 11. Coordination law for ALL workers

Before Vercel compute or durable writes:
- refresh current canonical research `main`;
- inspect active overlapping branches/PRs/receipts and the current Sandbox execution-path record;
- do not duplicate a live batch another worker already owns;
- prefer fusion/adjudication over a second permanent implementation;
- respect the current `GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md` for exact `go` unusual-experiment accounting;
- if exact trigger identity is not safely reproducible, run ordinary deterministic work only and execute no unusual experiment.

All workers should prefer one coordinated multi-gate Vercel batch over many redundant Sandbox starts where evidence independence permits.

This directive is compatible with and strengthens `SANDBOX_ONLY_TEST_EXECUTION_DIRECTIVE.md` under the newer ClayVerse product boundary. The operative rule is:

**Vercel Sandbox execution path CONFIRMED where the current bridge is admitted; direct ChatGPT-MCP lifecycle actions are not required for that path. Current execution admission must still be checked per exact preview/deployment.**
