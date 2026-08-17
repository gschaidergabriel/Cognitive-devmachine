# GO Vercel Stage-B execution-admission receipt — 2026-08-17 13:53 +07

Trigger: `go`
Organ: GPT-5.6 Sol temporary Clay organ
Research branch base observed before write: `7f807ffd9ebca43f94b05730825781fbc4fc555b`.

## Scope

This receipt records a bounded execution-admission result for the current Stage-B/MicroClay Vercel Sandbox bridge. It does **not** claim a ClayVerse component PASS/FAIL, runtime PASS, OCI PASS, or whole-product PASS.

Product authority remains unchanged: Clay is the persistent research entity; ClayVerse is the single-container product endpoint; UnifiedDB is canonical durable authority; MicroClay is adaptive retrieval/entry-point only; ClayGraph is rebuildable projection; EntityOS is optional internal substrate.

## Exact observed bridge candidate

Repository: `gschaidergabriel/Dr.-Unterweger`
Branch: `chatgpt/go-stageb-promotion-gate-vercel-20260817-1346`
Observed exact head: `7f3384fe82efe0b99b584c7f2a696a7e26fba802`

At that exact head:

- `mcp/vercel-sandbox-mcp/package.json` binds `vercel-build` to `node scripts/run-stageb-promotion-gate-sandbox.mjs` and uses `@vercel/sandbox` `2.9.2`.
- `run-stageb-promotion-gate-sandbox.mjs` is explicitly `NORMAL_DETERMINISTIC_REGRESSION_ONLY`, adds zero unusual experiments, requires Vercel Preview + OIDC, verifies staged Git blob identities, creates a Python 3.13 Vercel Sandbox, changes network policy to `DENY_ALL`, runs bounded Stage-B gates, stops the Sandbox, and emits a structured summary.
- The staged research candidate is PR #411 head `34de4bea6edb8f1020000277d947e8fd079005db`, with explicit source blob bindings for `store.py` and `method_memory.py`; therefore any future result from this runner is scoped to those exact staged bytes, not automatically to current research `main`.

## Vercel execution-admission result

Vercel project: `dr-unterweger`
Project ID: `prj_ifIgM9X7jqIQS8mNIGllImziePPG`
Team ID: `team_hwPBWKuCJxkfVhCx3WLdcTRx`

Observed exact-head combined status for `7f3384fe82efe0b99b584c7f2a696a7e26fba802`:

- context: `Vercel`
- state: `failure`
- target reason/path: `upgradeToPro=build-rate-limit`

No exact-head Preview build was observed for `7f3384fe...`; therefore `Sandbox.create`, Stage-B probe commands and `Sandbox.stop` did **not** execute for this exact candidate in this run.

The newest inspected `READY` deployments on the same bridge branch were older SHAs only:

- `dpl_3f5Kgeih41yctsrjNYvHrKhsmGPg` -> `1c6d28f65e9db703242d742dfc1b6505b71df045`
- `dpl_9SkXAEjSz9Vv5om8r3nqv562NdsA` -> `1033bc7c5135f9462f36da987c99460bc65dcbdb`
- `dpl_8ndcW87F9tGg3tuu5G23mfn7qLcX` -> `714c279efb60be0a580d96ff31229fed3b112792`

Those READY deployments are stale with respect to the corrected exact head and cannot establish the corrected runner's behavior.

### Classification

`EXECUTION_ADMISSION_BLOCKER`

This is **not** `TEST_FAIL`. The test did not start at the exact bridge head. It is also not a PASS.

## Serverless-path adjudication

The bridge tree also contains `api/sandbox-probe.js`, a fixed authenticated diagnostic which really calls `Sandbox.create()`, `sandbox.runCommand()` and `sandbox.stop()`. Therefore the evidence does **not** support the broader claim that Vercel Sandbox itself is unavailable.

That endpoint is intentionally protected by `CLAY_SANDBOX_PROBE_TOKEN`. The connected Vercel MCP surface available to this organ exposes deployment/team/log/documentation operations but no authenticated arbitrary POST invocation, and this organ was not given the probe bearer token. The unprotected `api/go-cycle-v2.js` is deliberately `BUILD_INTERNAL_ONLY` and returns 404.

So the narrow current blocker is:

1. exact-head Preview build admission is rate-limited; and
2. the alternate deployed runtime probe cannot be safely authenticated from the connected tool surface available to this organ.

No secret was requested, exposed, guessed or bypassed.

## Parallel / unusual-experiment coordination

Current research `main` acquired a separate claim commit `7f807ffd9ebca43f94b05730825781fbc4fc555b` for `tmux_socket_namespace_adversarial_alias_collision` at 13:52 +07. This organ therefore performed no new unusual experiment. All work here is source binding, admission verification and regression/evidence adjudication only.

Because exact trigger identity across concurrent chats is not safely inferable, this receipt does not retroactively claim or modify an experiment lease.

## Outcome and next discriminator

Retain the Stage-B bridge as a **SOURCE CANDIDATE** only. Stage-B Sandbox behavior at exact head remains **UNOBSERVED**.

Next highest-information authorized isolated step:

1. obtain one admitted Vercel Preview build for exact bridge head `7f3384fe...` (or a freshly rebased successor with re-bound staged research blobs);
2. require logs proving the source/blob identities before `Sandbox.create`;
3. require bounded Stage-B gate output, exit codes, Sandbox identity/environment, `DENY_ALL` network policy and successful `Sandbox.stop`;
4. only then classify the Stage-B mechanism result;
5. separately rerun against current ClayVerse source before any current-main or product-level promotion claim.

Do not substitute stale READY deployments, GitHub Actions admission failures, VPS/self-hosted execution, production execution, or source inspection for this executable discriminator.

No Together API. No owner-gated final paid/model training. No whole-product PASS claim.
