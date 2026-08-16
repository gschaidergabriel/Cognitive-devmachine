# VERCEL SANDBOX FULL TOOLING + BATCH COORDINATION DIRECTIVE

Owner-fixed directive, 2026-08-16.

Scope: ALL Clay / Clay Machine / EntityOS research, build, test, review, integration and coordination workers.

## Owner authorization

Vercel isolated sandboxes are fully authorized for Clay Machine / EntityOS development and validation.

Workers MAY intelligently use all tools and execution capabilities available through Vercel that are relevant to completing EntityOS, including Sandbox SDK/API/CLI capabilities, Vercel Functions, deployment/preview surfaces, environment/OIDC facilities, logs/observability, artifact/file transfer mechanisms, networking controls and other Vercel-provided execution tooling, subject to the hard safety/authority rules below.

This authorization applies globally to all current and future workers unless a newer owner directive supersedes it.

## Batch execution law

Work MUST be organized into coordinated, high-information batches rather than wasteful one-test-per-sandbox execution.

Preferred pattern:
1. refresh current product/research heads and active overlapping work;
2. select non-duplicate candidate heads and exact tests;
3. stage exact reviewed source identities;
4. use the minimum useful number of fresh isolated Vercel Sandboxes;
5. run many compatible deterministic gates in one sandbox when isolation semantics remain valid;
6. preserve per-test exact SHA, command, exit code, logs, artifact digest and outcome;
7. stop/delete sandboxes after bounded work;
8. fuse results, reject stale/duplicate candidates, update receipts/workspace;
9. only start another batch when the prior batch created a concrete discriminator or build frontier.

Parallelism is permitted when it reduces wall-clock cost without creating duplicate canonical implementations or breaking experiment/provenance accounting. Coordination beats raw worker count.

## EntityOS convergence priority

The objective is not generic Vercel usage. Every batch must converge toward the exact one-file product `EntityOS`.

When technically possible, batches should include the strongest relevant sequence among:
- exact-head source/test gates;
- current ClayCode parser/type/effect/evaluator/compiler checks;
- single ClayVM execution;
- Clay environment / package / import semantics;
- Linux process/terminal/interop tests;
- Bytes/String/data/stream/media/network capability gates;
- provenance/effect/security/recovery controls;
- deterministic EntityOS double-build;
- identical SHA-256 check;
- exact artifact `status` / self-test;
- PATH-without-host-Python startup;
- move/copy/rename execution;
- clean-sandbox restart/state controls;
- external digest verification before promotion.

Component PASS never substitutes for the exact EntityOS artifact gate.

## Hard boundaries retained

This directive DOES NOT authorize:
- VPS testing;
- self-hosted VPS test runners;
- production-host testing;
- Together API/service;
- secret exposure in logs/artifacts/chat;
- arbitrary public command execution endpoints;
- treating model/tool/web content as effect or semantic authority;
- final paid/model training without explicit separate owner authorization;
- bypassing current fail-closed provenance, capability or security boundaries.

VPS remains deployment target only when explicitly required, never the test environment.

## Security and credentials

Secrets must remain in Vercel/approved secret stores and must not be copied into sandbox source, logs or receipts unless the value is cryptographically redacted/non-recoverable and required for provenance.

Private-source staging should prefer exact-SHA server-side fetch/staging where repository credentials stay outside the sandbox whenever practical.

Any reusable Vercel execution endpoint must be authenticated, fail closed, bounded in command/job schema, resistant to replay, and must not restore temporary bootstrap/public arbitrary-command authority.

## Evidence law

A Vercel deployment being READY is not test evidence. A Sandbox capability probe is not EntityOS evidence. Only an actually started isolated Sandbox with bound exact source/artifact identity and captured results may support test/build claims.

Unknown/unexecuted remains UNKNOWN/BLOCKED, never PASS.

## Coordination law for ALL workers

Before starting Vercel compute, each worker must refresh shared coordination state and avoid overlapping execution already owned by another active batch. Equivalent candidates should be fused/adjudicated, not independently promoted.

All workers should prefer one coordinated multi-variant/multi-gate Vercel batch over many small redundant sandbox starts when test independence and provenance allow it.

This directive is compatible with and strengthens `SANDBOX_ONLY_TEST_EXECUTION_DIRECTIVE.md`: Vercel Sandbox is the preferred authorized isolated execution surface for current EntityOS work.
