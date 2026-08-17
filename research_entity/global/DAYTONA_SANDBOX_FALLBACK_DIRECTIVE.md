# DAYTONA SANDBOX FALLBACK — OWNER DIRECTIVE

**Owner instruction:** 2026-08-17  
**Status:** CURRENT  
**Scope:** all Clay / ClayVerse research, build, test, experiment and runtime-validation workers.

## 1. Authority and intent

This directive records the newest explicit owner instruction that Daytona isolated sandboxes are authorized and should be used as the standard fallback when Vercel Sandbox execution cannot currently admit the required run.

It complements `SANDBOX_ONLY_TEST_EXECUTION_DIRECTIVE.md` and supersedes older provider-selection wording that made Vercel the only preferred operational path.

The product endpoint remains the one-container ClayVerse artifact in `main/the artefact/`. Daytona is an execution provider only. It is not a product component, state authority, memory authority, effect authority, identity authority or deployment target.

## 2. Provider-selection law

For every executable ClayVerse gate:

1. Prefer an actually executable authorized Vercel Sandbox path when it is admitted and satisfies the test's required runtime capabilities.
2. If Vercel is admission-blocked, rate-limited, unavailable to the current worker, or its selected runtime lacks a required capability before product assertions (for example SQLite), use Daytona as the standard isolated-sandbox fallback when Daytona admission is available.
3. If both providers are blocked, record the exact admission blocker and do not fall back to VPS, self-hosted or production execution.
4. A provider control-plane failure before sandbox start earns zero product PASS/FAIL credit.
5. A runtime dependency failure before product assertions is not a ClayVerse semantic TEST_FAIL.

Daytona MAY also be used for deliberate independent replication when that materially increases confidence and does not waste execution budget or duplicate an in-flight canonical batch.

## 3. Daytona execution contract

Daytona execution is authorized only when all of the following hold:

- a real isolated Daytona Sandbox is created;
- exact source/artifact identity is bound before product claims;
- commands execute inside the Sandbox, not on the orchestration host;
- stdout/stderr or equivalent bounded diagnostics, exit code, runtime/provider identity and stop/delete state are captured;
- only the minimum required source/artifact bytes are staged;
- credentials are injected from approved secret storage/environment and never committed, echoed into logs, receipts, prompts or artifacts;
- sandbox lifecycle is bounded and the Sandbox is stopped/deleted when the run is complete where applicable;
- no generic public command endpoint is created;
- network access is minimized to the exact staging/build need and tightened before deterministic product regression where the provider supports that contract;
- exact current GitHub source remains canonical and all executable claims remain scoped to the tested SHA/artifact/image identity.

Daytona API keys are secrets. Repository files and receipts may record only that credential-backed admission was used, never the key value.

## 4. Current upstream capability basis

Current Daytona primary documentation exposes:

- API-key authentication through `DAYTONA_API_KEY`;
- SDK/API/CLI sandbox creation;
- sandbox process execution;
- file upload/staging into a sandbox;
- creation from language runtimes, snapshots and/or container-image based inputs depending on SDK/API path.

Those documentation facts establish a candidate execution mechanism only. They do not establish that this account, this exact key, this source head or this ClayVerse workload has successfully executed. Runtime truth requires an actually observed exact-bound Daytona run.

Operational status must be refreshed from:

`research_entity/continuity/DAYTONA_SANDBOX_EXECUTION_PATH_CURRENT.md`

## 5. Batch and convergence law

Use the same high-information batch discipline as Vercel:

`refresh exact main / target PR heads`
-> `bind exact source/artifact bytes`
-> `focused discriminating regressions`
-> `adjacent canonical regressions`
-> `broader suite when justified`
-> `exact OCI build/image identity when supported`
-> `startup/readiness/restart/concurrency gates`
-> `bounded receipt`
-> `stop/delete sandbox`.

Do not create a permanent Daytona-specific product implementation merely to test ClayVerse. Provider adapters belong to research/execution tooling only.

## 6. Hard boundaries

This directive does NOT authorize:

- VPS testing;
- self-hosted VPS runners;
- production-host testing;
- Together API/service;
- final paid/model training without separate owner authorization;
- secret disclosure;
- weakening Clerk/auth, UnifiedDB, MicroClay, EffectGate, recovery, generation, provenance or supply-chain gates to get green;
- treating Daytona/Vercel success as whole ClayVerse PASS without the complete acceptance vector.

## 7. `go`

For exact `go`, provider choice is now:

`AUTHORIZED VERCEL IF ADMITTED AND CAPABLE -> DAYTONA FALLBACK IF VERCEL BLOCKED/INCAPABLE -> EXPLICIT EXECUTION BLOCKER`.

The global one-unusual-experiment atomic lease protocol remains unchanged. Provider fallback does not create a second experiment budget.
