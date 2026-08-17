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

### Live Stage-B head drift

After the bridge was inspected, research PR #411 was refreshed and its actual GitHub PR head was observed at `9790c692de4d71ea39fbf79fef83c1a98e110317`.

Therefore the bridge at `7f3384fe...` is already **stale with respect to the live Stage-B candidate**: even if its blocked Preview were later admitted unchanged and all its gates passed, that would test the older staged PR #411 bytes at `34de4bea...`, not the live PR #411 head `9790c692...`.

This is a separate provenance gate from Vercel admission and must fail closed.

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

Those READY deployments are stale with respect to the corrected bridge head and cannot establish the corrected runner's behavior.

### Classification

`EXECUTION_ADMISSION_BLOCKER + STALE_TARGET_BINDING`

This is **not** `TEST_FAIL`. The exact corrected bridge test did not start, and that bridge no longer targets the live Stage-B head. It is also not a PASS.

## Serverless-path adjudication

The bridge tree also contains `api/sandbox-probe.js`, a fixed authenticated diagnostic which really calls `Sandbox.create()`, `sandbox.runCommand()` and `sandbox.stop()`. Therefore the evidence does **not** support the broader claim that Vercel Sandbox itself is unavailable.

That endpoint is intentionally protected by `CLAY_SANDBOX_PROBE_TOKEN`. The connected Vercel MCP surface available to this organ exposes deployment/team/log/documentation operations but no authenticated arbitrary POST invocation, and this organ was not given the probe bearer token. The unprotected `api/go-cycle-v2.js` is deliberately `BUILD_INTERNAL_ONLY` and returns 404.

So the narrow current blocker is:

1. live Stage-B source must first be rebound into a fresh bridge successor;
2. Preview build admission is currently rate-limited; and
3. the alternate deployed runtime probe cannot be safely authenticated from the connected tool surface available to this organ.

No secret was requested, exposed, guessed or bypassed.

## Parallel / unusual-experiment coordination

Current research `main` acquired a separate claim commit `7f807ffd9ebca43f94b05730825781fbc4fc555b` for `tmux_socket_namespace_adversarial_alias_collision` at 13:52 +07. This organ therefore performed no new unusual experiment. All work here is source binding, admission verification and regression/evidence adjudication only.

Because exact trigger identity across concurrent chats is not safely inferable, this receipt does not retroactively claim or modify an experiment lease.

## Outcome and next discriminator

Retain the inspected Stage-B bridge as a **STALE SOURCE CANDIDATE / NO CURRENT EXECUTION CLAIM**. Its exact Sandbox behavior remains **UNOBSERVED**, and its target is no longer the live Stage-B candidate.

Next highest-information authorized isolated step:

1. refresh the canonical/live Stage-B candidate head and re-bind every staged source blob in a fresh Vercel bridge successor;
2. obtain one admitted Vercel Preview build for that freshly bound bridge head;
3. require logs proving the bridge SHA plus staged research SHA/blob identities before `Sandbox.create`;
4. require bounded Stage-B gate output, exit codes, Sandbox identity/environment, `DENY_ALL` network policy and successful `Sandbox.stop`;
5. only then classify the Stage-B mechanism result;
6. separately rerun against current ClayVerse `main` before any current-main or product-level promotion claim.

Do not substitute stale READY deployments, a successful run against the older `34de4bea...` target, GitHub Actions admission failures, VPS/self-hosted execution, production execution, or source inspection for this executable discriminator.

No Together API. No owner-gated final paid/model training. No whole-product PASS claim.
