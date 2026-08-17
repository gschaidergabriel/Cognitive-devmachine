# Daytona Sandbox execution path — CURRENT

Status: AUTHORIZED FALLBACK / API MECHANISM CONFIRMED BY PRIMARY DOCS / EXACT CLAYVERSE RUNTIME UNOBSERVED
Observed: 2026-08-17

## Current truth

The owner has explicitly authorized Daytona isolated sandboxes as the standard fallback when Vercel cannot admit the required run.

Current provider-selection law is:

`VERCEL WHEN ADMITTED + CAPABLE -> DAYTONA FALLBACK -> EXPLICIT BLOCKER`.

VPS, self-hosted and production-host testing remain forbidden. Together remains forbidden.

## Primary capability evidence

Current Daytona primary documentation exposes:

- API-key authentication using `DAYTONA_API_KEY`;
- SDK/API/CLI sandbox creation;
- `sandbox.process.exec(...)` / equivalent command execution;
- file upload/staging into the sandbox;
- bounded execution timeouts;
- sandbox lifecycle operations.

This confirms that Daytona has a suitable candidate isolated-execution API surface. It does NOT by itself establish account admission, exact ClayVerse source execution or product PASS.

Primary documentation refreshed 2026-08-17:
- `https://www.daytona.io/docs/en/api-keys/`
- `https://www.daytona.io/docs/en/python-sdk/`
- `https://www.daytona.io/docs/en/process-code-execution/`
- `https://www.daytona.io/docs/en/python-sdk/sync/file-system/`

## Current session execution observation

A deterministic attempt from the current ChatGPT non-production container to install the Daytona Python SDK did not reach the provider because the orchestration container could not resolve the package index hostname. The observed failure was local DNS/network admission before Daytona authentication or Sandbox creation.

Classification:

`ORCHESTRATION_NETWORK_BLOCKED_BEFORE_DAYTONA_PROVIDER_CONTACT`

Consequences:
- this is NOT `DAYTONA_SANDBOX_UNAVAILABLE`;
- this is NOT ClayVerse TEST_FAIL;
- zero Daytona runtime test credit is minted;
- no API key value is recorded in repository source, logs or receipts;
- the next worker with provider egress should use the secret from approved secret storage/environment, never source control.

## Required first live Daytona gate

The next actually-connected worker should run one bounded admission/capability batch before moving product tests:

1. refresh current research `main` and target PR heads;
2. create one ephemeral Daytona Sandbox;
3. record sandbox/provider/runtime identity without exposing credentials;
4. establish required base capabilities for ClayVerse (`python`, `_sqlite3`, `git`; container/OCI tooling only if needed by the selected gate);
5. stage exact source bytes without embedding repository/API credentials inside the sandbox when avoidable;
6. re-hash staged bytes against GitHub identities;
7. execute a focused deterministic regression batch;
8. capture exit code + bounded stdout/stderr;
9. stop/delete the Sandbox;
10. persist a bounded receipt to GitHub.

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
