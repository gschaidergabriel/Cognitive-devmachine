# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries only the current product state and latest concrete delta.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority; ClayGraph is derived/rebuildable.
- Canonical path: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Managed hooks bind turns to UnifiedDB; effects remain fail-closed through ClayVerse MCP/EffectGate.
- EntityOS is an **optional** digest-bound internal execution/security substrate, not the product endpoint and not required for the baseline container.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#625** tokenless canonical baseline packaging — primary current packaging lane; exact head is moving under coordinated parallel hardening and must be rebound immediately before executable claims.
- **#611** tmux idempotent-reapply lane — exact in-image tmux remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical `requirements.lock.txt` accepted yet.
- **#623** auth/identity/readiness/reauth drift lane — source/mechanism supported only, not exact OCI/runtime evidence.
- **#602** managed native-Claude process attestation — downstream of exact in-image #611.
- Dr.-Unterweger **#810** remains retained/historical controller evidence. Its cross-private-repo `GITHUB_READ_TOKEN` staging path is not the preferred baseline packaging route.

### Tokenless baseline decision

PR #625 removes the accidental requirement that baseline ClayVerse must fetch/stage private EntityOS bytes before it can build. Baseline may omit EntityOS while execution is disabled. If EntityOS is later embedded, explicit digest, source-tracked lock identity and locked size remain mandatory and mismatches fail closed. No GitHub credential is admitted into product source.

The runtime and Compose contracts now match that packaging contract:

- absent EntityOS + execution disabled is an admitted baseline state;
- the hardened Compose baseline no longer marks `CLAYVERSE_ENTITYOS_SHA256` as `:?required`; absent digest resolves to the baseline empty value, while Clerk/auth variables remain mandatory;
- enabling EntityOS execution without an embedded SHA-256 pin fails closed;
- unpinned bytes at the configured EntityOS path fail closed even when execution is disabled;
- unpinned symlinks fail closed;
- a configured pin still requires the normal absolute-path verification path before any execution bridge can be returned;
- a verified pinned EntityOS remains staged/verified but is not exposed as an execution bridge until execution is explicitly enabled.

The default-deny Docker build context is also hardened so optional EntityOS staging re-includes only the exact admitted `.keep`/`EntityOS` paths rather than a recursive sibling wildcard.

### Testing policy — continue without waiting for Vercel

The missing direct Vercel Git-project connection is **not a development blocker**. It is deferred to the final exact OCI acceptance gate.

Until that final gate is available, every product-convergent cycle must maximize all other independent evidence layers defined in `the artefact/TESTING_STRATEGY.md`, including static/source integrity, focused unit/contract tests, negative/fail-closed cases, deterministic adversarial regressions, persistence/restart/idempotency, dual-user concurrency/generation fencing, reproducibility/supply-chain checks, integration simulations and any real component runtime available on an authorized disposable surface.

Missing one runner must never suppress independent tests. Mock/simulated/component evidence remains explicitly bounded and cannot imply whole-product PASS.

### Current execution boundary

The connected Vercel surface still does not provide a directly linked `clay-global-research-entity` Git project or a connector mutation to create/relink that project. Exact whole-container OCI acceptance therefore remains deferred.

The historical GitHub Actions run `31995291479` was re-run once as a runner-admission probe. GitHub accepted the re-run request, but attempt 2 started at `2026-08-17T14:04:16Z` and was already `failure` by `14:04:22Z`; job/step visibility remains blocked by `403 Resource not accessible by integration`. Because no test/build step execution is observable, this receives **zero executable product credit** and is not promoted to either ClayVerse TEST_FAIL or PASS. The exact current #625 head was not executed by that probe.

The exact `go` unusual-experiment slot is **COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT** because no immutable shared request/turn ID is exposed to this worker. Zero unusual experiments were executed in this macro-cycle.

### Working sequence before final OCI

`tokenless #625 source/runtime/Compose convergence → maximum static/unit/contract/negative/adversarial/property/restart/concurrency/reproducibility/integration evidence → deliberately rejoin and harden #611/#622/#623 → #602 managed native-Claude source/component closure → Clerk/PTY/hooks/persistence/recovery/concurrency simulations and disposable component runtimes wherever available → repeat regression fan-out after each change`.

### Final deferred exact execution sequence

When an authorized isolated OCI/Sandbox route is available:

`fresh canonical source → docker compose config with no EntityOS digest → inspect actual Docker build-context membership → baseline build with EntityOS absent → normal baseline service start/readiness with EntityOS absent → optional digest-bound EntityOS build and negative cases → exact image digest → resolved APT/tmux/Python/Claude identities → deny network where required → exact in-image #611 → accepted #622 lock and --require-hashes rebuild → #602 packaged native Claude → UnifiedDB/ClayGraph → real Clerk JWT/browser WebSocket PTY → managed hooks/EffectGate → persistence/restart/recovery → dual-user concurrency/global-generation fencing → whole-product acceptance`.

Whole-product PASS requires this exact closure. Source inspection, static tests, mocks, component runtime PASS, deployment READY, Sandbox creation or historical evidence do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 21:04 +07:00 — #625 tokenless baseline gained bounded runtime-component evidence and the GitHub runner admission blocker was freshly rechecked.**

- Adversarial build-context review removed recursive optional-EntityOS sibling admission and added focused source-contract coverage; the parallel retained-lane receipt reports **5 focused tests PASS** plus valid/wrong-digest/symlink staging checks on an isolated non-production surface. This remains bounded source-contract evidence, not Docker/OCI runtime credit.
- Compose integration review found that `compose.yaml` still required `CLAYVERSE_ENTITYOS_SHA256` even though the Dockerfile baseline made EntityOS optional. The same #625 lane now permits an absent digest in Compose while retaining execution-disabled baseline and mandatory Clerk/auth interpolation. Exact Git blobs used for the focused rerun: Compose `de5766a950bec7dc7768b5944d6fa4b5aced2f9b`, regression `4adc5944be46c7a216223560e7260ecc7a625697`, Dockerfile `2ee2fe84f1fd7219869380ce3c864cade90c6c31`, `.gitignore` `8bdddac545b4b691f2c74a164d53261fbe64438d`. Exact reconstructed focused regression: **3/3 PASS**; YAML parse PASS. No Docker/Podman binary was available, so resolved Compose/OCI behavior remains unobserved. Receipt: `the artefact/receipts/2026-08-17_GO_2053_PR625_COMPOSE_TOKENLESS_ENTITYOS_FENCE_GPT56SOL.json`.
- A separate adversarial check found a product contradiction: the Dockerfile allowed an EntityOS-free baseline, while normal `service._entityos_config()` still required an EntityOS SHA/artifact. That would make the new baseline build but fail normal startup.
- The same #625 lane now admits the absent-EntityOS state only with execution disabled and no unpinned bytes present, while preserving fail-closed execution/pin/path verification.
- Expanded `tests/test_service_entityos_optional_baseline.py` covers absent baseline, execution-without-pin, unpinned regular bytes, unpinned symlink, pinned-but-exec-disabled verification, and pinned+exec-enabled bridge exposure.
- Exact Git blobs observed after the runtime write: `service.py` `c9151e339c0ec4b23a454ee7684a6bd9255bf229`; expanded optional-runtime regression `a9bc8e2941800591bb38a7becac1e2ea81e1652b`.
- Bounded exact-function/test-slice check on an isolated non-production container: `py_compile` PASS and **6/6 pytest PASS in 0.06s**. This is not full-branch pytest, OCI build or packaged service runtime evidence.
- The retained `tests/test_entityos_boot_binding.py` still asserted the retired `CLAYVERSE_REQUIRE_ENTITYOS` contract. It was synchronized in commit `96ccdc6ec66ddd90cdd35d7a6f824907bdeabdd1` to the current execution-gated optional-EntityOS contract; exact Git blob `e672c112a8c14445cbc387f36786290a9f5c3f82`.
- A bounded combined boot/runtime contract reconstruction exercised the updated boot regression together with the expanded optional-runtime slice: **14/14 PASS in 0.04s**. This evidence is explicitly not a byte-for-byte full-branch checkout, full pytest, OCI build or packaged service runtime result.
- A further exact-file check found one stale retained regression: `tests/test_entityos_default_optional.py` still expected the retired `{"required": false, "bound": false}` status shape. The exact pre-repair test failed **1/1** on that mismatch. Commit `424eead7300e4857db5415da9a52b77851031e08` updates only the expectation to the current `staged/verified/execution_enabled` status contract; product semantics were unchanged. Repaired blob: `c5e9ea7a156e05665236403ce9c1bae0abb549d0`.
- The repaired default regression was then combined with exact current Git blobs for `service.py` `c9151e33…`, `entityos_bridge.py` `3118cb6a…`, expanded optional-runtime test `a9bc8e29…` and boot-binding test `e672c112…`: **15/15 PASS in 0.05s**. Unrelated `service.py` import-time modules were deterministic stubs; the exercised EntityOS paths did not call them. This is adjacent exact-file source/component evidence, not full moving-PR-head or OCI evidence.
- Exact-source Linux component execution of `entityos_bridge.py` blob `3118cb6a6758ec1612a33ff3c6766c937d79d4ac` exercised `verify()` plus the real sealed-memfd `run()` boundary with a pinned executable fixture: **4/4 PASS**. Mutable-path replacement produced digest mismatch before execution and symlink replacement failed at the `O_NOFOLLOW` open boundary. Receipt: `the artefact/receipts/2026-08-17_GO_2101_PR625_ENTITYOS_MEMFD_COMPONENT_GPT56SOL.json`. This is **COMPONENT_RUNTIME_PASS**, not in-image/OCI acceptance.
- GitHub Actions runner admission was rechecked by re-running historical run `31995291479`. Attempt 2 again completed `failure` within six seconds, while jobs/steps remain inaccessible through the integration (`403`). No executable ClayVerse step is observed, so runtime credit remains zero and cause remains unresolved. Receipt: `the artefact/receipts/2026-08-17_GO_2104_GITHUB_RUNNER_ADMISSION_RECHECK_GPT56SOL.json`.
- Durable adjacent-regression receipt: `the artefact/receipts/2026-08-17_GO_2103_PR625_ENTITYOS_OPTIONAL_ADJACENT_REGRESSION_GPT56SOL.json`.
- Runtime/boot receipts: `the artefact/receipts/2026-08-17_GO_2058_PR625_OPTIONAL_ENTITYOS_RUNTIME_FENCE_GPT56SOL.json` and `the artefact/receipts/2026-08-17_GO_2101_PR625_ENTITYOS_BOOT_REGRESSION_SYNC_GPT56SOL.json`.
- No duplicate packaging/runtime lane was created; parallel #625 hardening was adopted into the same retained branch.
- GO unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; zero unusual experiments executed.
- No whole-product PASS, VPS/self-hosted/production testing, Together API, paid/final training or secret persistence is claimed.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound EntityOS substrate.

## Verification

Authorized bounded component/source evidence exists, but **whole-product PASS is not claimed**. The strongest next discriminator for #625 is exact isolated Docker/OCI execution proving Compose resolution, actual build-context membership and normal service startup/readiness of the EntityOS-free baseline before optional EntityOS embedding is accepted.
