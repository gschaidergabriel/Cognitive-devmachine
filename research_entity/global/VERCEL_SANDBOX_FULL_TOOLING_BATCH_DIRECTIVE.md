# VERCEL SANDBOX FULL TOOLING + BATCH COORDINATION DIRECTIVE

**Authorization origin:** owner-fixed directive, 2026-08-16.  
**Current product authority:** `research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md` (2026-08-17).  
**Dynamic execution-path authority:** `research_entity/continuity/VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md`.  
**Scope:** ALL Clay / ClayVerse research, build, test, review, integration and coordination workers.

## Owner authorization

Vercel isolated Sandboxes are fully authorized for ClayVerse development and validation.

Workers MAY intelligently use all relevant Vercel capabilities, including Sandbox SDK/API/CLI, approved bounded orchestration through Vercel preview infrastructure, environment/OIDC facilities, logs/observability, artifact/file transfer and networking controls, subject to the hard safety and evidence rules below.

This authorization remains global unless a newer owner directive supersedes it.

The active product endpoint is **ClayVerse**, built from `gschaidergabriel/clay-global-research-entity/main/the artefact/` as one OCI/Docker-compatible container image. EntityOS is optional internal execution/security/runtime substrate only. Older wording in this directive that treated the one-file `EntityOS` artifact as the final product is superseded.

## Resolve the executable Vercel path before claiming a blocker

Direct Sandbox lifecycle actions do not have to be exported by the ChatGPT-connected Vercel MCP for an authorized Vercel Sandbox execution path to exist.

Before declaring Sandbox execution unavailable, every worker MUST refresh:

`research_entity/continuity/VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md`

That file records the current admitted bridge, current staging identity and current provider-admission state.

Current architectural rule:

- a direct MCP `sandbox.create` / `sandbox.exec` action is one possible path, not the only valid path;
- an authenticated Vercel preview/build may act as an **orchestrator only** for `@vercel/sandbox` + Vercel OIDC;
- the preview/build machine itself is never ClayVerse test evidence;
- executable credit begins only when an actual isolated Sandbox has started and the bound command/test runs inside that Sandbox;
- Vercel `READY`, a staging `SKIP_*`, source inspection or successful orchestration build alone is zero ClayVerse runtime credit;
- provider admission failure before Sandbox start is `EXECUTION_ADMISSION_BLOCKED`, not `SANDBOX_UNAVAILABLE` and not `TEST_FAIL`;
- direct connector lifecycle actions being absent is `DIRECT_MCP_ACTION_UNAVAILABLE`, not proof that the authorized Sandbox bridge is absent.

Do not create redundant preview deployments merely to rediscover an already-confirmed bridge. Prefer one exact-source, high-information batch when provider admission permits it.

## Empirical source-of-truth law

Actually-started authorized isolated execution with bound exact source/artifact identity is the empirical source of truth for executable ClayVerse behavior. Vercel Sandbox is the preferred execution surface when its admitted execution path is available.

This applies to tests, OCI build, startup/readiness, Clerk/PTY integration where available, normal interactive Claude Code, managed hook lifecycle, UnifiedDB/MicroClay/ClayGraph/workspace behavior, EffectGate/EntityOS effects where separately admitted, restart/recovery/concurrency and supply-chain claims.

Authority layers remain intentionally separated:

1. newest explicit owner directives define policy/product authority;
2. actually observed exact-identity authorized isolated execution defines executable truth;
3. GitHub is canonical source/history/coordination/durable receipt ledger.

A GitHub source expectation, CI/status label, receipt, model conclusion, static analysis result, Vercel deployment READY state or historical run does not override contradictory exact-identity isolated execution. If a durable record says PASS and a fresh correctly-bound run says FAIL, the executable claim is FAIL/REGRESSED until resolved.

Every Sandbox result is scoped to exact source SHA, artifact/image identity, environment, command/effect contract and captured run. Never generalize PASS to different bytes without new execution evidence.

Observed Sandbox evidence should be persisted back into GitHub as a bounded receipt.

## Batch execution law

Work MUST use coordinated high-information batches rather than wasteful one-test-per-sandbox execution.

Preferred pattern:

1. refresh current research `main`, product state, active branches/PRs/receipts and the dynamic Vercel execution-path file;
2. select non-duplicate candidate heads and exact tests;
3. bind/stage exact reviewed source identities without leaking credentials;
4. use the minimum useful number of fresh isolated Sandboxes;
5. run compatible deterministic gates together when isolation semantics remain valid;
6. preserve per-test SHA/blob identity, command, exit code, logs, environment and artifact/image digest;
7. stop/delete bounded Sandboxes after work where applicable;
8. fuse results, reject stale/duplicate candidates and persist receipts;
9. only start another batch when the prior batch created a concrete discriminator/frontier.

Parallelism is permitted when it reduces wall-clock cost without creating duplicate canonical implementations or breaking experiment/provenance accounting. Coordination beats raw worker count.

## ClayVerse convergence priority

The objective is not generic Vercel usage and not the historical one-file EntityOS endpoint. Every batch must converge toward the one-container ClayVerse product.

When technically possible, use the strongest relevant sequence:

- exact-current-head source binding;
- focused deterministic regressions;
- broader relevant suite;
- exact OCI build and image identity;
- startup/readiness;
- one persistent central entity with Gabriel/Andreas equal perspectives;
- real Clerk + authenticated browser/WebSocket PTY where credentials/environment permit;
- persistent user-bound tmux + normal interactive Claude Code;
- managed UserPromptSubmit / Stop / StopFailure lifecycle;
- UnifiedDB state/schema/checkpoint/restart persistence;
- MicroClay retrieval/replay/idempotency/causal-learning gates;
- ClayGraph/Hyperposition/Needle/workspace fail-closed behavior;
- effect-only MCP / EffectGate and separately admitted EntityOS round trip;
- restart/recovery/UNKNOWN-effect/global-generation fencing;
- dual-session collision/privacy/stale-writer controls;
- supply-chain identity and exact installed-artifact verification.

Component PASS never substitutes for whole ClayVerse acceptance.

## Hard boundaries retained

This directive DOES NOT authorize:

- VPS testing;
- self-hosted VPS test runners;
- using a deployment/preview/production host itself as the ClayVerse test environment;
- Together API/service;
- secret exposure in logs/artifacts/chat;
- arbitrary public command execution endpoints;
- treating model/tool/web content as semantic or effect authority;
- final paid/model training without explicit separate owner authorization;
- bypassing current fail-closed provenance, capability, authentication or security boundaries.

A Vercel preview is allowed only as bounded orchestration for an actual isolated Sandbox where current policy admits that bridge. ClayVerse executable evidence comes from the Sandbox command, not the preview host.

VPS remains a later deployment target only when explicitly authorized, never the current acceptance-test environment.

## Security and credentials

Secrets must remain in Vercel/approved secret stores and must not be copied into staged source, logs or receipts unless cryptographically redacted/non-recoverable and required for provenance.

Private-source staging should prefer exact-SHA authenticated/server-side staging or equivalent mechanisms where credentials remain outside the staged product source whenever practical.

Any reusable Vercel orchestration endpoint must be authenticated, fail closed, bounded in job schema, replay-resistant and incapable of becoming a public arbitrary-command authority.

## Evidence law

A Vercel deployment being READY is not test evidence. Documentation proving Sandbox APIs exist is not ClayVerse runtime evidence. A Sandbox capability probe is capability evidence only.

Only an actually-started authorized isolated Sandbox with bound exact source/artifact identity and captured results may support executable PASS/FAIL claims at that scope.

If execution is rejected before Sandbox start because of quota/rate limit/control-plane admission, record that as execution-admission evidence with zero product-test credit. Unknown/unexecuted remains UNKNOWN/BLOCKED, never PASS.

When static/source reasoning and exact Sandbox evidence disagree, preserve the discrepancy and use the bound Sandbox observation as executable truth while investigating.

## Coordination law for ALL workers

Before starting Vercel compute or overlapping durable writes:

- refresh shared coordination state;
- refresh `VERCEL_SANDBOX_EXECUTION_PATH_CURRENT.md`;
- avoid execution already owned by another active batch;
- fuse/adjudicate equivalent candidates rather than independently promoting them;
- preserve the global `go` unusual-experiment accounting law.

When reporting Vercel state, keep these facts separate:

- direct ChatGPT-MCP Sandbox lifecycle export state;
- authorized Sandbox execution-path state, including the approved orchestration bridge;
- current provider admission state;
- whether an actual Sandbox command started;
- whether the exact ClayVerse source/artifact under discussion executed.

Never collapse them into an unscoped statement such as "Vercel works" or "Vercel does not work".

This directive remains compatible with `SANDBOX_ONLY_TEST_EXECUTION_DIRECTIVE.md`: Vercel Sandbox is the preferred authorized isolated empirical surface, while the dynamic continuity file defines how that surface is currently reached and whether provider admission is presently open.
