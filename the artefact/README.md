# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries only the current product state.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority; ClayGraph is derived/rebuildable.
- Canonical path: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Managed hooks bind turns to UnifiedDB; effects remain fail-closed through ClayVerse MCP/EffectGate.
- EntityOS is an **optional** digest-bound internal execution/security substrate, not the product endpoint and not required for the baseline container.
- Build/test/runtime validation is authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#611** tmux idempotent-reapply lane — head `2957e80228815ac266635981a55f22bc15dc9ed4`; exact in-image tmux remains the promotion discriminator.
- **#622** Python hash-lock generator — head `84f0f17b42b31bb64ad902e619dd4d26894dcead`; source candidate/unexecuted; no canonical `requirements.lock.txt` accepted yet.
- **#623** auth/identity/readiness/reauth drift lane — head `daf48f2ccf7b07cb10ea4d397b34b44a4c6895e5`; source/mechanism supported only, not exact OCI/runtime evidence.
- **#602** managed native-Claude process attestation — head `d6f2f40af2e4ff8bc413df139895dd5f2935cb50`; downstream of exact in-image #611.
- **#625** tokenless canonical baseline packaging — head `d1aeff9034395a53526453037a0da10f05b094c8`; **new primary source candidate / unexecuted**.
- Dr.-Unterweger **#810** remains historical/retained controller evidence at `78d92753d9442c66c3ffcff127c31faa98ffd622`, but its `GITHUB_READ_TOKEN` cross-private-repo staging path is no longer the preferred baseline route.

### Tokenless baseline decision

The previous blocker was self-inflicted by packaging: the Dockerfile had `CLAYVERSE_ENABLE_ENTITYOS_EXEC=0` but still required `COPY EntityOS`, forcing the external controller to fetch private EntityOS bytes before even building baseline ClayVerse.

PR #625 removes that requirement without weakening EntityOS admission:

1. baseline build may omit EntityOS entirely while execution remains disabled;
2. optional EntityOS bytes stage under ignored `build-assets/entityos/`;
3. if EntityOS is supplied, its explicit `ENTITYOS_SHA256` must equal the source-tracked lock digest, the locked size must match, and SHA-256 verification must pass;
4. staged bytes without an explicit digest fail closed;
5. the OCI build context remains default-deny/allowlisted and no GitHub credential is admitted into product source.

No Clerk, UnifiedDB, tmux, Claude, EffectGate or identity semantics are changed by this lane.

### Current execution boundary

The Vercel team currently exposes only project **`dr-unterweger`**. There is **no Vercel project connected directly to `gschaidergabriel/clay-global-research-entity`**. The connected Vercel tools can inspect/deploy an already-linked current project but do not expose create/relink-Git-project mutation.

Therefore the primary blocker is now:

**`VERCEL_CANONICAL_RESEARCH_PROJECT_NOT_CONNECTED`**

This replaces `GITHUB_READ_TOKEN_MISSING` as the preferred-path blocker. Re-running #810 without a credential is not useful and earns no product credit.

### Next exact execution sequence

`connect canonical Research repo directly to Vercel → root/build from the artefact source → execute #625 tokenless baseline in authorized Vercel Sandbox/OCI flow → capture image digest + resolved APT/tmux/Python/Claude identities → deny network → rejoin #611/#622/#623 exactly once onto the accepted current product spine → in-image tmux policy/reapply → stable-output Python hash lock + accepted --require-hashes rebuild → #602 packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hooks → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete path. Source inspection, PR creation, static tests, deployment READY, Sandbox creation or old component evidence do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 20:29 +07:00 — canonical merged product/runtime bytes remain `NO_CHANGE`; a fresh tokenless baseline source lane #625 was created from current main and the product blocker was moved from missing GitHub read credential to missing direct Vercel Git-project connection.**

- PR #625 branch: `gpt56sol/go-tokenless-canonical-build-20260817`
- PR #625 head: `d1aeff9034395a53526453037a0da10f05b094c8`
- receipt: `the artefact/receipts/2026-08-17_GO_2029_TOKENLESS_CANONICAL_BUILD_LANE_GPT56SOL.json`
- Vercel projects observed: only `dr-unterweger`
- source runtime credit: 0; OCI runtime credit: 0
- no valid unusual experiment executed because the shared immutable trigger identity required by the coordination lease is unavailable
- no VPS/self-hosted/production test, Together API, paid/final training or secret persistence was used

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound EntityOS substrate.

## Verification

Authorized bounded component evidence exists, but **whole-product PASS is not claimed**. The next accepted runtime evidence must come from the exact canonical Research source through an authorized isolated Vercel execution path and continue through the full OCI/runtime acceptance sequence above.
