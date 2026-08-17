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

## Resumed executable proof — 15:18 +07

Connected Vercel build logs were refreshed for deployment:
`dpl_CmQJ5bkaXf4GUxZKJgrMq9QSH3wo`

Bound staging identity:
- repository: `gschaidergabriel/Dr.-Unterweger`;
- branch: `chatgpt/go-microclay-explicit-feedback-pr501-vercel-20260817-1418`;
- staging head: `dc2b524961137c40c427cc6d371d411ee6c4cfac`;
- exact MicroClay feedback blob: `b293b8c2903eb01ce83523b0d483c3ebbdafee8c`;
- exact MicroClay retrieval blob: `b264802d77917cd5c81ef091bc0a07cdf3b06393`.

Observed isolated execution facts from the Vercel build log:
- `execution_surface="VERCEL_SANDBOX_MICROVM"`;
- `network_policy="DENY_ALL"`;
- exact blob binding passed for both target files;
- `sandbox_stopped=true`;
- `test_exit_code=1`;
- recorded `test_output` was empty;
- build then exited nonzero because the regression result was false.

Classification:
`EXECUTED_CROSS_BRANCH_COUNTEREVIDENCE_UNADJUDICATED`.

This is important in two directions:
1. Vercel Sandbox execution is **currently not uniformly admission-blocked**; a real microVM did start and run the exact-bound test command.
2. The MicroClay result is **not yet a semantic TEST_FAIL attribution** because the staging harness persisted only `stdout` for the test command while Python assertion/import failures normally appear on `stderr`. The exact failing assertion/error identity is therefore not bound by this receipt.

The staging script at that exact head confirms the observability gap: it assigns `summary.test_output = String(await cmd.stdout())...` and does not persist `cmd.stderr()` for the failing test command. The next diagnostic execution must bind both stdout and stderr (or a merged bounded diagnostic stream) before interpreting the exit-1 result.

Do not rerun merely to prove the bridge works. Rerun only as one coordinated discriminator after FREE_ONLY eligibility is established and after the harness captures the failing assertion identity.

## Current official free-tier facts

Current official Vercel pricing documents Vercel Sandbox as available with recurring included Hobby usage, including:
- 5 hours Active CPU per month;
- 420 GB-hours provisioned memory per month;
- 5,000 Sandbox creations per month;
- 20 GB network per month;
- 10 concurrent Sandboxes on Hobby.

Primary current references:
- `https://vercel.com/pricing`
- `https://vercel.com/sandbox`

Therefore:
- `VERCEL_SANDBOX_REQUIRES_PAID_PLAN = FALSE` as a general product claim;
- `HOBBY_HAS_RECURRING_INCLUDED_SANDBOX_ALLOWANCE = TRUE`;
- `THIS_ACCOUNT_REMAINING_INCLUDED_ALLOWANCE = UNVERIFIED` because the connected MCP currently does not expose the account's billing/usage balance;
- FREE_ONLY still forbids assuming remaining quota or silently crossing into paid overage.

A non-starting account-specific usage/free-allocation check is still preferred before launching another Sandbox. If such usage state becomes directly observable, bind it before execution. If it remains unobservable, do not misstate the platform as unavailable or paid-only; state the narrower remaining-quota uncertainty.

## Historical fresh capability re-check

A bounded capability-only branch was created earlier:
`chatgpt/vercel-sandbox-capability-proof-20260817-1350`
head: `87237ab4544b21aea011c3ab396bbd9593c21875`
PR: `gschaidergabriel/Dr.-Unterweger#815`

It contained a fresh `Sandbox.create -> runCommand -> stop` probe with Python 3.13, non-persistent mode and `networkPolicy: deny-all`.

That specific preview was rejected **before build/Sandbox start** with the Vercel status target `upgradeToPro=build-rate-limit`.

Classification for that attempt:
`EXECUTION_ADMISSION_BLOCKED_BY_VERCEL_BUILD_RATE_LIMIT`.

This remains valid bounded history for that attempt only. It must not be generalized into a current claim that Vercel Sandbox cannot start, because the later `dpl_CmQJ5bkaXf4GUxZKJgrMq9QSH3wo` microVM actually started and executed.

## Historical Live GO re-check — 13:53 +07

The connected Vercel surface still did **not** export direct Sandbox lifecycle actions, while Vercel documentation confirmed `sandbox run`, `sandbox exec`, the Sandbox SDK `runCommand`, and Sandbox REST/CLI lifecycle support.

During that earlier re-check, three READY `dr-unterweger` previews on branch `chatgpt/go-stageb-promotion-gate-vercel-20260817-1346` were inspected. Their build logs did **not** establish Stage-B execution because those deployed commits still invoked inherited `run-microclay-pr383-sandbox.mjs` and emitted `SKIP_NON_TARGET_PREVIEW`.

The same staging branch later advanced to head:
`bbf1ad778045420afb4103335a8afd8cc1e7d625`

At that head, `mcp/vercel-sandbox-mcp/package.json` was correctly wired to:
`node scripts/run-stageb-promotion-gate-sandbox.mjs`

That exact head was rejected by Vercel before build at `2026-08-17T06:55:21Z` with:
`Deployment rate limited — retry in 24 hours.`

Preserve these as exact-attempt admission facts only. READY previews that skipped are not execution evidence, and a rate-limited attempt does not negate later successful Sandbox admission.

## Worker law

For all Clay/ClayVerse workers:
- absence of direct Sandbox actions in the ChatGPT Vercel MCP != absence of Vercel Sandbox execution;
- inspect/use the existing `Dr.-Unterweger` Git-preview + `@vercel/sandbox` bridge before declaring Vercel Sandbox unavailable;
- Vercel Sandbox is not generally paid-only: current official Hobby pricing includes recurring Sandbox allowance;
- remaining account-specific included quota may still be unknown and must not be invented;
- distinguish `DIRECT_MCP_ACTION_UNAVAILABLE` from `SANDBOX_EXECUTION_PATH_UNAVAILABLE`;
- distinguish `BUILD_RATE_LIMIT / PREVIEW_ADMISSION_BLOCKED` from code/test failure;
- distinguish a READY preview that only emits a staging `SKIP_*` result from actual Sandbox execution;
- distinguish `exit_code != 0 with missing stderr/assertion identity` from a fully adjudicated semantic test failure;
- never treat Vercel deployment READY as executable evidence;
- only commands actually run in the isolated Sandbox may establish executable behavior;
- bind exact source/artifact identity, stdout/stderr or equivalent bounded diagnostics, command, exit code, network policy and stop state;
- stop/delete bounded Sandboxes after use;
- VPS/self-hosted/production-host testing remains forbidden;
- Together remains forbidden.

## Current operational wording

Preferred current status wording:

`Vercel Sandbox execution path CONFIRMED via Git-preview orchestration + @vercel/sandbox/OIDC; direct ChatGPT-MCP lifecycle actions are not exported. A current 2026-08-17 MicroClay staging deployment actually started a DENY_ALL Vercel Sandbox, bound exact target blobs, executed the test command and stopped cleanly; its exit 1 remains UNADJUDICATED because the staging harness persisted stdout but not stderr/assertion identity. Official Vercel Hobby pricing includes recurring Sandbox allowance, so Sandbox is not paid-only; only this account's remaining included quota is currently unverified. READY/SKIP previews and pre-Sandbox rate-limit rejections mint zero runtime credit.`
