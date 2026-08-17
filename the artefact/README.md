# the artefact — ClayVerse single-container candidate

This is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**Refresh this state in every product-convergent cycle. A stale README means the cycle is incomplete; detailed evidence remains in Git history and bounded receipts.**

### Current product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority. ClayGraph is derived/rebuildable only. MicroClay changes retrieval/accessibility only, never truth, identity, privacy or effect authority.
- Canonical user path: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into the same central entity/global generation.
- Claude Code is runtime cognition, not durable memory/identity authority. Managed hooks bind turns to UnifiedDB.
- Effects remain fail-closed through ClayVerse MCP/EffectGate. Generic host `process.exec` is forbidden. EntityOS is an optional digest-bound internal execution/security substrate, not the product endpoint.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#611** — single retained tmux idempotent-reapply repair. Promotion still requires the actual tmux resolved inside the exact ClayVerse OCI image.
- **#622** — single retained Python hash-lock generator lane at `44ec5e109d40304b152c2fa05ba3e42e690f2820`; source-defined eight-package pip-tools bootstrap candidate remains **UNEXECUTED**. No canonical accepted `requirements.lock.txt` exists yet and Docker is not promoted to product `--require-hashes`.
- **#623** — single retained auth/identity/readiness drift lane at semantic head `7308bbbf39302e1207bda11d8dd212e7950dca7d`; source-fences canonical users/equal rights, canonical permanent session IDs, session cardinality, terminal identity and global generation. It remains **SOURCE CANDIDATE / UNEXECUTED**.
- **#602** — downstream managed native-Claude process attestation after successful in-image #611 validation.
- Dr.-Unterweger **#810** — the single retained Vercel OCI controller; no parallel OCI controller or second source-staging authority is admitted. The retained branch was re-observed at `a86f4355d02dc34331a3746128b6c3b959977439` after the latest bounded deployment descendant.

### Current OCI execution evidence

The strongest actually-started product-boundary evidence now includes Vercel deployment **`dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8`** from Dr.-Unterweger commit **`a341eb107f8499f301e730de12680fd2df580fd8`**.

Observed in that build:

1. Vercel cloned the private Dr.-Unterweger controller and entered the retained ClayVerse build wrapper.
2. The exact retained-runner guard admitted the bound controller source.
3. `Sandbox.create` succeeded.
4. The v2 provider-identity hardening emitted both real Sandbox name **`peach-traditional-sparrow-J4uLFC`** and current Sandbox session ID **`sbx_ZBNVvNkCkxdZFs1FmwAIFJcgkoyb`**.
5. Execution then failed closed before any private Research/EntityOS source fetch because host-side Preview variable `GITHUB_READ_TOKEN` was absent: `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`.
6. The disposable Sandbox stopped successfully.
7. `source_runtime_credit=0`; `oci_runtime_credit=0`; this is **not** ClayVerse TEST_FAIL.

The executed deployment commit is bounded execution provenance only. It was observed three commits ahead of retained `a86f4355…`, while the retained branch was subsequently observed back at `a86f4355…`; therefore the descendant must not be treated as current branch truth or silently promoted.

### Primary current blocker

The immediate external prerequisite is to provision **`GITHUB_READ_TOKEN` as a sensitive Vercel Preview build credential** for the retained PR810 path.

Security contract:

- the token stays in the Vercel build host;
- the token value is never logged or forwarded into the disposable Sandbox;
- the build host fetches exact private Research and EntityOS commits/trees;
- only verified archive bytes cross into the Sandbox;
- unknown source identity fails closed.

The connected Vercel tools available in the current cycle expose deployment/project/log inspection but do **not** expose environment-secret mutation or secret-value recovery. Re-triggering the same lane without the credential would only reproduce the known infrastructure blocker and earns no product runtime credit.

### Next exact execution sequence

After the Preview credential exists:

`refresh current main → refresh retained #611/#622 and deliberately admitted #623 → rebind the single #810 controller exactly once → Sandbox.create → host-side exact private Research + EntityOS fetch/tree verification → verified archives only into Sandbox → reproduce/attest locked EntityOS → full exact-source regressions → exact ClayVerse OCI build → capture image digest + APT/tmux/Python/Claude identities → deny network → in-image #611 policy/reapply attestation for both canonical users → service/readiness checks → execute #622 offline hashed bootstrap and product lock generation → accept/materialize canonical product lock → rebuild with --require-hashes → #611 promotion decision → rejoin/revalidate #602 → packaged native Claude → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed lifecycle hooks → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete path. Source inspection, PRs, CI definitions, deployment READY, `Sandbox.create`, historical receipts or component PASS do not imply ClayVerse PASS.

### Supply-chain state

The final container still has open acceptance gates until exact isolated OCI evidence closes them. In particular, current main has not yet accepted the #622 generated Python hash lock, and exact resolved package identities must be captured from the admitted image. Source candidates such as the APT snapshot and Claude archive hardening remain bounded until they are fused and executed on the accepted product path.

### Latest cycle delta

**2026-08-17 20:13 +07:00 — `NO_CHANGE` canonical merged ClayVerse product/runtime bytes; Vercel v6 provider identity is now empirically observed, credential blocker unchanged.**

- Fresh current `main` before this cycle write was `a57572431b11aa1759eddf7475c03cbacaa62ae7`.
- Fresh Vercel inspection found deployment `dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8` from controller descendant `a341eb107f8499f301e730de12680fd2df580fd8`.
- The run created a real Sandbox and captured both provider Sandbox name and VM-session ID before private-source staging.
- The strongest counterhypothesis that v2 provider identity might still be purely source-side is therefore weakened at this bounded infrastructure scope.
- The run again stopped at missing host-side `GITHUB_READ_TOKEN` before private Research/EntityOS bytes crossed the boundary; source/OCI runtime credit remains zero.
- The retained PR810 branch is currently `a86f4355d02dc34331a3746128b6c3b959977439`; the executed descendant is preserved only as bounded execution provenance.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_2013_VERCEL_V6_PROVIDER_IDENTITY_CREDENTIAL_BLOCK_GPT56SOL.json`.
- No valid unusual experiment was executed because no shared immutable request/turn identity is exposed for the atomic experiment lease.
- No VPS, self-hosted/production test, Together API, paid/final training, secret exposure or duplicate controller path was used.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

1. Refresh current `main`, artefact state, overlapping PRs/receipts and exact execution evidence.
2. Rewrite this living state so stale dynamic claims are removed.
3. Record the concrete latest-cycle delta; use `NO_CHANGE` when canonical product bytes did not change.
4. Never promote source/component/controller/provider evidence into whole-product PASS.
5. Keep detailed evidence in Git history/receipts rather than making this README a competing state database.
6. Rebind fast-moving execution closures immediately before real compute; distinguish product-byte movement from documentation/receipt-only head churn and avoid retry-only or duplicate semantic paths.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for bounded components, but **whole-product PASS is not claimed**. The current OCI path is empirically capable of starting a disposable Vercel Sandbox and now records its provider/VM-session identity correctly, but private product source still cannot be staged until the sensitive Preview read credential exists. The next accepted runtime claim must bind freshly refreshed product bytes and continue beyond that credential gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
