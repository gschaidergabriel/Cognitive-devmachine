# Vercel Sandbox execution path — CURRENT

Status: CURRENT CAPABILITY / EXECUTION-ADMISSION MAY VARY
Observed: 2026-08-17

## Correction

Do **not** infer `Vercel Sandbox unavailable` merely because the ChatGPT-connected Vercel MCP does not expose a direct `sandbox.create` / `sandbox.exec` action.

The connected Vercel MCP currently exposes project/deployment/log/documentation actions, and its documentation surface confirms current Vercel Sandbox CLI, SDK and REST execution capabilities. Direct Sandbox lifecycle actions are not exported by this connector, but a working authorized execution bridge already exists through the Vercel Git-preview staging project.

## Working execution bridge

Staging repository/project:
- GitHub: `gschaidergabriel/Dr.-Unterweger`
- Vercel project: `dr-unterweger`
- project id: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`
- staging root used by prior runs: `mcp/vercel-sandbox-mcp/`
- package dependency observed on main: `@vercel/sandbox` `2.9.2`

Execution pattern:
1. create/update a bounded preview branch in `Dr.-Unterweger`;
2. make the preview build script orchestration-only;
3. use the Vercel-provided `VERCEL_OIDC_TOKEN` implicitly through `@vercel/sandbox`;
4. call `Sandbox.create(...)` with explicit runtime/timeout/persistence/network policy;
5. stage or inline the exact bound test source into the Sandbox;
6. execute tests/build commands with `sandbox.runCommand(...)` **inside the isolated Sandbox microVM**;
7. capture source SHA/blob/artifact identity, command, exit code and output;
8. call `sandbox.stop()` in `finally`;
9. read Vercel build logs through the connected MCP and persist the bounded result back to the canonical research repository.

The Vercel preview/build machine is only an orchestration surface. It must not itself become the test environment. Executable claims require the command to have run inside the started Sandbox.

## Direct observed proof

Git commit in the staging repository:
`4decb8b44f206653af6c87317dbd26991a5eb71b`
message: `test(vercel): verify ClayVerse attach child reaping in Sandbox`

That commit used:
- `import { Sandbox } from '@vercel/sandbox'`;
- required `VERCEL_OIDC_TOKEN`;
- `Sandbox.create({ runtime: 'python3.13', timeout: 120000, persistent: false, networkPolicy: 'deny-all' })`;
- `sandbox.runCommand(...)`;
- `sandbox.stop()`.

Observed Vercel deployment:
`dpl_HU8CECeN9KdYBSUcd5GVzSjApPtR`

Observed build log result contained:
- `status: PASS_ATTACH_CHILD_REAP_AND_BOUND`;
- `ok: true`;
- `exit_code: 0`;
- executable Python output from the isolated sandbox;
- `sandbox_stopped: true`.

This proves the bridge can actually create and execute a Vercel Sandbox. It is not merely documentation or deployment READY evidence.

## Fresh 2026-08-17 capability re-check

A new bounded capability-only branch was created:
`chatgpt/vercel-sandbox-capability-proof-20260817-1350`
head: `87237ab4544b21aea011c3ab396bbd9593c21875`
PR: `gschaidergabriel/Dr.-Unterweger#815`

It contains a fresh `Sandbox.create -> runCommand -> stop` probe with Python 3.13, non-persistent mode and `networkPolicy: deny-all`.

Current result: Vercel rejected the preview **before build/Sandbox start** with the Vercel status target `upgradeToPro=build-rate-limit`.

Classification:
`EXECUTION_ADMISSION_BLOCKED_BY_VERCEL_BUILD_RATE_LIMIT`

This is **not** evidence that Sandbox is unavailable and is not a test failure. It means the known working execution path is currently admission-blocked for this particular fresh preview attempt.

## Worker law

For all Clay/ClayVerse workers:
- absence of direct Sandbox actions in the ChatGPT Vercel MCP != absence of Vercel Sandbox execution;
- inspect/use the existing `Dr.-Unterweger` Git-preview + `@vercel/sandbox` bridge before declaring Vercel Sandbox unavailable;
- distinguish `DIRECT_MCP_ACTION_UNAVAILABLE` from `SANDBOX_EXECUTION_PATH_UNAVAILABLE`;
- distinguish `BUILD_RATE_LIMIT / PREVIEW_ADMISSION_BLOCKED` from code/test failure;
- never treat Vercel deployment READY as executable evidence;
- only commands actually run in the isolated Sandbox may establish executable behavior;
- bind exact source/artifact identity and persist receipts;
- stop/delete bounded Sandboxes after use;
- VPS/self-hosted/production-host testing remains forbidden;
- Together remains forbidden.

## Current operational wording

Preferred status wording when the direct connector lacks lifecycle tools but the staging bridge exists:

`Vercel Sandbox execution path CONFIRMED via Git-preview orchestration + @vercel/sandbox/OIDC; direct ChatGPT-MCP lifecycle actions are not exported. Current execution admission must be checked from the target preview/deployment. A rate-limit/control-plane rejection before Sandbox start is ADMISSION_BLOCKED, not SANDBOX_UNAVAILABLE and not TEST_FAIL.`
