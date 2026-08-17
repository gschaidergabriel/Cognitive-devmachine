# Vercel Sandbox execution path — CURRENT

Status: CURRENT CAPABILITY / CURRENT FREE PREVIEW ADMISSION BLOCKED
Observed: 2026-08-17

## Current truth

Do **not** infer `Vercel Sandbox unavailable` because the connected ChatGPT Vercel MCP does not export direct `sandbox.create` / `sandbox.exec` actions.

The authorized execution bridge is confirmed and has actually started Vercel Sandbox microVMs:

`Dr.-Unterweger Git preview -> Vercel build orchestration -> VERCEL_OIDC_TOKEN -> @vercel/sandbox -> Sandbox.create -> runCommand -> stop`.

The Vercel preview/build machine is orchestration only. Runtime credit exists only for commands observed inside the isolated Sandbox.

Canonical staging project:
- repository: `gschaidergabriel/Dr.-Unterweger`;
- Vercel project: `dr-unterweger`;
- project id: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`.

VPS, self-hosted and production-host testing remain forbidden. Together remains forbidden.

## Direct execution proof

Historical direct bridge proof:
- staging commit `4decb8b44f206653af6c87317dbd26991a5eb71b`;
- deployment `dpl_HU8CECeN9KdYBSUcd5GVzSjApPtR`;
- real Sandbox start/run/stop;
- `PASS_ATTACH_CHILD_REAP_AND_BOUND`, exit 0.

This proves the Git-preview + OIDC + `@vercel/sandbox` path is an executable Sandbox path, not documentation-only evidence.

## 15:05 +07 diagnostic adjudication

Historical v2 MicroClay composition under diagnosis:
- research PR #501 head `c30be49655af196822a24c5bf345dd9588ce80a0`;
- route donor PR #499 head `a0d31cd2fa1c8f856435e9c0527bf583dbc93a2f`;
- exact feedback blob `b293b8c2903eb01ce83523b0d483c3ebbdafee8c`;
- exact retrieval blob `b264802d77917cd5c81ef091bc0a07cdf3b06393`.

First real Sandbox run:
- deployment `dpl_CmQJ5bkaXf4GUxZKJgrMq9QSH3wo`;
- staging head `dc2b524961137c40c427cc6d371d411ee6c4cfac`;
- `execution_surface=VERCEL_SANDBOX_MICROVM`;
- `network_policy=DENY_ALL`;
- both exact Git blobs passed in-Sandbox binding;
- Sandbox stopped cleanly;
- test exit 1;
- original harness persisted stdout only, so the Python traceback was initially lost.

A later deterministic stderr-capturing rerun **was admitted and started another real Sandbox**:
- deployment `dpl_7H6XmBbeCzqXeLBEH6fD9vYc47uG`;
- staging head `e76a8fcf27653504eb9b53b6429832044b93b9bb`;
- same exact two target blobs bound successfully;
- `DENY_ALL` requested;
- Sandbox stopped cleanly;
- test exit 1;
- merged diagnostic output:

`ModuleNotFoundError: No module named '_sqlite3'`

The failure occurs while importing Python `sqlite3`, before the MicroClay probe reaches product assertions.

Current classification:

`SANDBOX_RUNTIME_DEPENDENCY_MISSING_SQLITE3_BEFORE_PRODUCT_ASSERTIONS`

Consequences:
- the historical v2 exit 1 is **not** a MicroClay semantic TEST_FAIL;
- it is also not PASS;
- PR #501 is closed/superseded by current v3 PR #550;
- no v2 executable verdict transfers to v3;
- bare `runtime: 'python3.13'` must not be used for UnifiedDB/SQLite-dependent ClayVerse tests unless `_sqlite3` capability is first established.

Durable receipt:
`the artefact/receipts/2026-08-17_GO_1502_VERCEL_SQLITE_RUNTIME_DIAGNOSTIC_GPT56SOL.json`.

## SQLite-capable next runtime

Current Vercel Sandbox documentation supports image-based creation, including custom or digest-pinned OCI images through `Sandbox.create({ image: ... })` / `vercel sandbox create --image ...`.

Therefore the preferred next exact ClayVerse execution topology is:

`exact current ClayVerse source -> admitted SQLite-capable digest-bound OCI/Sandbox image -> Sandbox.create(image=...) -> DENY_ALL where inputs are prestaged -> exact focused + adjacent regressions -> OCI startup/readiness/restart gates`.

Best convergence target is eventually the exact ClayVerse OCI candidate itself, because it also tests the real Python/runtime dependency closure instead of a synthetic bare language runtime.

Do not weaken network, provenance, effect or state-authority fences merely to obtain a green test.

## Current FREE_ONLY provider admission

Current official Vercel pricing documents recurring included Hobby Sandbox allowance, so Vercel Sandbox is not generally paid-only. Current official included Hobby quantities observed on 2026-08-17 include:
- 5 Active CPU hours/month;
- 420 GB-hours provisioned memory/month;
- 5,000 Sandbox creations/month;
- 20 GB network/month;
- 10 concurrent Sandboxes.

Primary upstream references:
- `https://vercel.com/pricing`;
- `https://vercel.com/sandbox`.

However, current account-level **Preview deployment admission** is separately exhausted for this cycle. Exact durable receipt:
`the artefact/receipts/2026-08-17_GO_1502_VERCEL_ADMISSION_DAILY_CAP_GPT56SOL.json`.

Observed provider error on an additional corrected Preview attempt:

`Resource is limited - try again in 24 hours (more than 100, code: api-deployments-free-per-day).`

Current classification:

`FREE_DAILY_PREVIEW_DEPLOYMENT_CAP_REACHED_NOT_TEST_FAIL_NOT_SANDBOX_UNAVAILABLE`

Therefore:
- do not launch additional Vercel Preview attempts while this free daily cap is active;
- READY previews that emit `SKIP_NON_TARGET_PREVIEW` earn zero runtime credit;
- provider rejection before Sandbox start earns zero test PASS/FAIL credit;
- once free admission returns, refresh current research `main`, target PR heads and exact blobs before executing anything.

## Surviving execution targets

For MicroClay, the surviving line is:
- PR #484: Schema-8 / policy-v3 integration;
- PR #550: provenance-bound explicit retrieval-miss correction stacked on #484.

Historical #501/#499 v2 runtime evidence is harness/runtime evidence only.

The next admitted MicroClay batch must use an SQLite-capable image and bind exact current #484/#550 source plus adjacent UnifiedDB/replay/privacy/restart/Stage-B tests before any promotion.

Whole-product priority remains higher than any one subsystem: after focused source gates, continue toward exact ClayVerse OCI build, startup/readiness, Clerk/browser/PTY, native Claude lifecycle, persistence/restart, effect/recovery and dual-session concurrency.

## Worker law

For every Clay/ClayVerse worker:
- `DIRECT_CHATGPT_MCP_SANDBOX_LIFECYCLE_NOT_EXPORTED` != `VERCEL_SANDBOX_UNAVAILABLE`;
- the Git-preview + `@vercel/sandbox` + OIDC bridge is confirmed by actual microVM execution;
- distinguish provider/Preview admission failures from Sandbox/runtime failures;
- distinguish runtime dependency failure before assertions from product semantic test failure;
- bind exact source/artifact/image identity, command, exit code, stdout+stderr (or equivalent merged bounded diagnostics), network policy and Sandbox stop state;
- prefer an admitted digest-pinned SQLite-capable image for UnifiedDB-dependent tests;
- never infer whole ClayVerse PASS from deployment READY, source coherence, one component result or historical v2 evidence;
- stop bounded Sandboxes after use;
- no VPS/self-hosted/production testing;
- Together forbidden.

## Preferred operational wording

`Vercel Sandbox execution path CONFIRMED via Git-preview orchestration + @vercel/sandbox/OIDC; direct ChatGPT-MCP Sandbox lifecycle actions are not exported. Real DENY_ALL microVMs have started and executed exact-bound commands. The historical MicroClay v2 exit-1 is adjudicated as the selected Vercel Python 3.13 runtime missing _sqlite3 before product assertions, not a MicroClay semantic failure. Current free Preview admission is separately blocked by api-deployments-free-per-day; do not burn more Preview attempts. When free admission returns, use an admitted SQLite-capable/digest-bound image, refresh exact current source, and run one coordinated high-information batch. READY/SKIP and pre-start provider rejections mint zero runtime credit.`
