# Daytona Sandbox execution path — CURRENT

Status: AUTHORIZED FALLBACK / DIRECT API MECHANISM CONFIRMED BY PRIMARY DOCS / BOUNDED RUNNER CONTROL-FLOW SUPPORTED / EXACT CLAYVERSE DAYTONA RUNTIME UNOBSERVED
Observed: 2026-08-17

## Current truth

The owner has explicitly authorized Daytona isolated sandboxes as the standard fallback when Vercel cannot admit the required run.

Current provider-selection law is:

`VERCEL WHEN ADMITTED + CAPABLE -> DAYTONA FALLBACK -> EXPLICIT BLOCKER`.

VPS, self-hosted and production-host testing remain forbidden. Together remains forbidden.

A native ChatGPT Daytona plugin/connector is **not** a requirement for Daytona eligibility. Daytona's documented HTTPS API/SDK/CLI is the canonical provider interface. Absence of a ChatGPT-native connector is only a property of the current orchestration surface; it must never be promoted into a provider-availability, account-credit or sandbox-capability claim.

## Primary capability evidence

Current Daytona primary documentation exposes:

- API-key authentication using `DAYTONA_API_KEY`;
- default API base `https://app.daytona.io/api`;
- direct HTTPS API, SDK and CLI sandbox creation;
- sandbox process/code execution;
- file upload/staging into the sandbox;
- bounded execution timeouts;
- sandbox lifecycle operations;
- runtime network-policy mutation including outbound blocking.

This confirms that Daytona has a suitable candidate isolated-execution API surface. It does NOT by itself establish account admission, remaining free credit, exact ClayVerse source execution or product PASS.

Primary documentation refreshed 2026-08-17:
- `https://www.daytona.io/docs/en/api-keys/`
- `https://www.daytona.io/docs/en/`
- `https://www.daytona.io/docs/en/sandboxes/`
- `https://www.daytona.io/docs/en/typescript-sdk/`

## Connector-independent dispatch law

Daytona fallback must be classified in three independent layers:

1. **Provider mechanism** — Daytona exposes a documented API/SDK/CLI capable of creating and controlling sandboxes.
2. **Orchestrator admission** — the current worker/controller must have outbound DNS/HTTPS plus an approved secret path for `DAYTONA_API_KEY` (and any required account configuration).
3. **Sandbox runtime evidence** — only an actually created Daytona sandbox that runs the bound command can mint Daytona runtime credit.

Therefore:

- `NO_CHATGPT_DAYTONA_CONNECTOR` != `DAYTONA_UNAVAILABLE`;
- `NO_CHATGPT_DAYTONA_CONNECTOR` != `NO_DAYTONA_ACCOUNT_CREDIT`;
- `ORCHESTRATOR_NO_EGRESS` != `DAYTONA_PROVIDER_FAILURE`;
- `DAYTONA_API_KEY_NOT_PRESENT_IN_THIS_WORKER` != `DAYTONA_ACCOUNT_NOT_CONFIGURED`;
- zero runtime credit means only that no accepted Daytona sandbox command has executed at the required bound identity.

Fallback implementations should call Daytona directly through the documented API/SDK from an authorized egress-capable controller. Do not add a permanent second application runtime merely to obtain provider access.

## Bounded research runner

Canonical research tooling includes:

`research_entity/execution/daytona_sandbox_batch.py`

Current runner contract:
- locally verifies the exact staged bundle SHA-256;
- reads Daytona credentials only from environment/provider configuration and never emits their values;
- creates one bounded sandbox and applies a TTL;
- uploads the bundle and re-verifies its SHA-256 inside the sandbox before extraction;
- can request outbound network blocking after staging and fails closed if that requested tightening cannot be applied;
- records target command identity by SHA-256 rather than writing the raw command into structured receipt events;
- bounds stdout volume;
- stops and deletes the sandbox in `finally` where provider lifecycle calls are available.

A deterministic fake-provider control-flow regression of this exact runner path passed after one corrected harness-only shell-cwd mistake. The passing regression exercised local+remote bundle-hash agreement, requested network block, two successful target commands including a SQLite import/version probe, PASS emission, stop, delete, and absence of the test credential value from output.

Classification:

`BOUNDED_RUNNER_CONTROL_FLOW_SUPPORTED_FAKE_PROVIDER_NOT_DAYTONA_RUNTIME_PASS`

This evidence supports the orchestration mechanism only. No Daytona sandbox/provider runtime was contacted by that regression and it contributes zero ClayVerse runtime acceptance credit.

## Current ChatGPT-controller observation

A fresh 2026-08-17 recheck of the current non-production ChatGPT controller observed:

- no native/installable Daytona ChatGPT plugin/connector;
- `DAYTONA_API_KEY` not present in this worker environment;
- Daytona Python SDK not installed;
- DNS resolution failure from this worker for `app.daytona.io`, `api.daytona.io` and `pypi.org`.

Classification:

`CURRENT_CHATGPT_ORCHESTRATOR_BLOCKED_BEFORE_DAYTONA_PROVIDER_CONTACT`

Consequences:
- this is NOT `DAYTONA_SANDBOX_UNAVAILABLE`;
- this is NOT evidence about the user's Daytona account balance or free-credit entitlement;
- this is NOT ClayVerse TEST_FAIL;
- no Daytona provider contact occurred from this worker;
- Daytona runtime test credit remains zero because no Daytona sandbox command was executed;
- the next authorized egress-capable controller should use the documented direct API/SDK with credentials from approved secret storage/environment, never source control.

## Required first live Daytona gate

When Daytona fallback is actually needed and an egress-capable authorized controller exists:

1. refresh current research `main` and target PR heads;
2. verify account-specific FREE_ONLY/no-paid-use admission without exposing credentials or balance secrets;
3. create one ephemeral Daytona Sandbox through the documented API/SDK;
4. record sandbox/provider/runtime identity without exposing credentials;
5. establish required base capabilities for ClayVerse (`python`, `_sqlite3`, `git`; container/OCI tooling only if needed by the selected gate);
6. stage exact source bytes without embedding repository/API credentials inside the sandbox when avoidable;
7. re-hash staged bytes against GitHub identities;
8. tighten network policy after staging when the selected gate permits it;
9. execute a focused deterministic regression batch;
10. capture exit code + bounded stdout/stderr;
11. stop/delete the Sandbox;
12. persist a bounded receipt to GitHub.

If base capability is missing before product assertions, classify it as provider/runtime substrate evidence and choose a Daytona snapshot/image/runtime that supplies the required dependency rather than weakening ClayVerse.

## Security contract

- `DAYTONA_API_KEY` is secret and never committed or echoed.
- Prefer environment/secret-store injection.
- No generic public command endpoint.
- No product/state authority is delegated to Daytona.
- Exact execution truth remains scoped to exact source/artifact/environment identity.
- Provider admission/control-plane failure before Sandbox start earns zero product PASS/FAIL credit.

## GO coordination

The current exact `go` trigger exposes only minute-precision shared timestamp metadata, so `GO_EXPERIMENT_ATOMIC_LEASE_PROTOCOL.md` requires `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`. Ordinary deterministic provider integration, source work and future exact tests remain allowed; provider fallback does not mint another unusual-experiment slot.
