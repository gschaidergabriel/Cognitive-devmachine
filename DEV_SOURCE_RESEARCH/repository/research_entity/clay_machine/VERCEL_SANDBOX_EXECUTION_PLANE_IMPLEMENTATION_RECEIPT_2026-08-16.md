# Vercel Sandbox execution-plane implementation receipt — 2026-08-16

Evidence state: **CANDIDATE / PARTIALLY EXECUTED**
Program: `CLAYVERSE_CLAY_MACHINE_ONLY`
Product: one-file `EntityOS`
Product repo candidate: `gschaidergabriel/Dr.-Unterweger` PR #751, branch `chatgpt/vercel-sandbox-mcp-20260816`

## Implemented candidate mechanisms

The product-repo Vercel lane currently contains:

- Vercel-native stateless MCP transport (`mcp-handler` 2.1.1, MCP SDK v2);
- `/mcp` baseline control plane for one named persistent Sandbox;
- persistent identity, bounded no-expiry snapshots, session history, checkpoint/rollback and offline-on-resume convergence;
- bounded allowlisted package/GitHub bootstrap commands with `deny-all` restoration;
- bounded text/binary transfer and SHA256 file identity;
- `/mcp-lab` execution plane for CLAY-namespaced/tagged fresh non-persistent labs;
- stopped/checkpointed baseline fork creation for controlled counter-reality experiments;
- private exact-commit staging in which `GITHUB_READ_TOKEN` remains in the Vercel Function and only source bytes enter the sandbox;
- explicit archive redirect handling that terminates Authorization before following the expected `codeload.github.com` redirect;
- preserved CM-07 job for exact head `07f0bf7bc19e398f4820cd346a58190f98e596c6` using the historical exact parser/package/resolver test commands and no whole-machine/effect-authority overclaim;
- fresh exact-head `EntityOS` build job using the repository's existing canonical double-PyInstaller builder;
- post-build candidate checks for exactly one output file `EntityOS`, receipt/artifact SHA/size/head binding, frozen self-test, status identity, Pythonless PATH, copy/rename relocation and four parallel status probes;
- lab artifact retrieval restricted to `/vercel/sandbox/output/EntityOS`, <=256 KiB per chunk, whole-file SHA256 bound;
- failure cleanup and explicit success cleanup requirement after artifact download.

These mechanisms are test/build infrastructure only. They do not define ClayCode, ClayVM, ClayOS or EntityOS semantic authority.

## Actually executed evidence

1. Existing pure bearer-auth logic: 4/4 PASS from the prior zero-cost local gate (missing vault secret / missing bearer / wrong bearer fail closed; correct bearer accepted).
2. Lab namespace pure policy was executed locally against the exact Git blob SHA `548c5235759b2e7c146ee8e336311028e2a784e4` and returned PASS for:
   - deterministic normalization;
   - fixed `clay-entityos-lab-*` namespace;
   - rejection of persistent baseline/foreign names;
   - rejection of traversal, whitespace, shell-like IDs, leading/trailing hyphen and empty IDs;
   - rejection of >40-character lab IDs.

These are component/policy tests only. They are **not** evidence that a Vercel Sandbox was started or that EntityOS was built in Vercel.

## Current Vercel account/connector observation

- ChatGPT Vercel connector is installed and team discovery succeeds.
- One team is visible to the connector.
- Project listing currently returns zero projects.
- The exposed `deploy_to_vercel` action is presently schema-inconsistent: its surfaced contract has no arguments, while invoking it returns validation requiring `target`, `name` and `files`.
- No alternate installable Vercel project-create/deploy connector was found.
- Local container outbound DNS remains unavailable, so the user token cannot be used through a local Vercel CLI/REST fallback from this execution environment.

Outcome: `BLOCKED_EXTERNAL_CONNECTOR_PROJECT_BOOTSTRAP`, not code PASS/fail.

## Not executed / must remain UNKNOWN or BLOCKED

- real package-lock generation;
- `npm ci`;
- full `vitest` suite;
- TypeScript compile;
- Next/Vercel build;
- VCR custom Ubuntu image build/digest resolution;
- Vercel project creation/import;
- Preview deployment;
- `/healthz` live request;
- MCP initialize/discover/tools-list live requests;
- real baseline Sandbox lifecycle;
- real lab create/fork/delete;
- private source-stage network request from deployed Vercel Function;
- preserved CM-07 Vercel microVM run;
- fresh current-head EntityOS Vercel build;
- external reconstruction/SHA verification of an EntityOS artifact.

## Promotion discriminator

The smallest high-information next event is **one successfully created Vercel project/Preview for PR #751**. Once this exists, run in order:

1. dependency install/test/typecheck/build;
2. vault variables + immutable image identity;
3. `/healthz` and both MCP auth/initialize/tools-list gates;
4. read-only config/list calls;
5. preserved CM-07 fresh-lab run;
6. fresh exact-current-main EntityOS build;
7. chunk download + external SHA256 match;
8. lab cleanup;
9. only then adjudicate PR #751 and current CM-07 evidence.

No VPS, self-hosted runner, production test, E2B start or final-model training was used by this implementation work.
