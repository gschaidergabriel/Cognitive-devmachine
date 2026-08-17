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
- **#622** — single retained Python hash-lock generator lane. Current branch head after its bounded receipt is `84f0f17b42b31bb64ad902e619dd4d26894dcead`; semantic repair is `b6b5a83c390944c9f8c9494d29c1d793ed701dcb`. Primary PyPI metadata recheck supports the declared eight-package Python-3.13 bootstrap filenames/hashes at source scope. The predecessor reproducibility discriminator wrote the two `pip-compile` generations to different output paths (`.lock.1` / `.lock.2`), which can make generated headers differ by construction. The retained lane now performs two independent compilations at one stable output path and fences the old pattern in the source regression. It remains **SOURCE CANDIDATE / UNEXECUTED**. No canonical accepted `requirements.lock.txt` exists and Docker is not promoted to product `--require-hashes`.
- **#623** — single retained auth/identity/readiness drift lane. Current observed head is `25f86cbf5508c8e3ec07790a4228bc784cd5fb1b`; `terminal_gateway.py` blob `e6e3e3a55d60ea266e5f3c0048f45ac5fe1e2cd9` and reauth-test blob `0783ee3ed71bc2ce3fd3af89e7410f8029147d20`. The same lane fences canonical users/equal rights, canonical permanent session IDs, session cardinality, terminal identity and global generation; `_runtime_ready()` reuses the same read-only canonical-user-state validator used by authenticated resolution before tmux probing. It now also prevents Clerk `reauth` from extending the live socket lease until the already-attached Clerk subject is re-resolved through the existing `IdentityRouter` against current UnifiedDB and still maps to the same canonical user/session. Bounded source-slice evidence observed readiness/user-contract **5/5 PASS** and reauth helper **4/4 PASS**. The latest test head additionally covers live UnifiedDB extra-user, rights and generation drift plus the lease-extension ordering fence, but that exact test commit is unexecuted. Classification remains **MECHANISM_SUPPORTED / SOURCE CANDIDATE** only; no exact PR-head pytest, OCI, real Clerk/browser PTY, tmux/Claude runtime or whole-product PASS is claimed.
- **#602** — downstream managed native-Claude process attestation after successful in-image #611 validation.
- Dr.-Unterweger **#810** — the single retained Vercel OCI controller. Its retained branch has been restored by non-force fast-forward to semantic v6 head `78d92753d9442c66c3ffcff127c31faa98ffd622`. No parallel OCI controller or second source-staging authority is admitted.

### Current OCI execution evidence

The strongest actually-started product-boundary evidence includes Vercel deployment **`dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8`** from trigger-only Dr.-Unterweger commit **`a341eb107f8499f301e730de12680fd2df580fd8`**, whose parent is retained semantic controller `78d92753…`.

Observed in that build:

1. Vercel cloned the private Dr.-Unterweger controller and entered the retained ClayVerse build wrapper.
2. The exact retained-runner guard admitted the bound controller source and TargetPatch **v6** was active.
3. `Sandbox.create` succeeded.
4. The v2 provider-identity hardening emitted both real Sandbox name **`peach-traditional-sparrow-J4uLFC`** and current Sandbox session ID **`sbx_ZBNVvNkCkxdZFs1FmwAIFJcgkoyb`**.
5. Execution then failed closed before any private Research/EntityOS source fetch because host-side Preview variable `GITHUB_READ_TOKEN` was absent: `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`.
6. The disposable Sandbox stopped successfully.
7. `source_runtime_credit=0`; `oci_runtime_credit=0`; this is **not** ClayVerse TEST_FAIL.

The trigger-only `a341eb…` child is bounded execution provenance, not retained branch truth. During this cycle the single retained #810 branch was observed drifted back to ancestor `a86f4355…` while its durable controller contract identified `78d92753…` as the semantic v6 head. The existing branch was repaired by a **non-force fast-forward** through `c40a5099…` to `78d92753…`. No force rewrite, duplicate controller or second source-staging path was created, and the PR body was refreshed to distinguish retained source from transient execution provenance.

### Primary current blocker

The immediate external prerequisite is to provision **`GITHUB_READ_TOKEN` as a sensitive Vercel Preview build credential** for the retained PR810 path.

Security contract:

- the token stays in the Vercel build host;
- the token value is never logged or forwarded into the disposable Sandbox;
- the build host fetches exact private Research and EntityOS commits/trees;
- only verified archive bytes cross into the Sandbox;
- unknown source identity fails closed.

The connected Vercel tools available in the current cycle expose deployment/project/log inspection but do **not** expose environment-secret mutation or secret-value recovery; a plugin search found no installable Vercel secret-management alternative. Re-triggering the same lane without the credential would only reproduce the known infrastructure blocker and earns no product runtime credit.

### Next exact execution sequence

After the Preview credential exists:

`refresh current main → refresh retained #611/#622 and deliberately admitted #623 → rebind the single #810 controller exactly once → Sandbox.create → host-side exact private Research + EntityOS fetch/tree verification → verified archives only into Sandbox → reproduce/attest locked EntityOS → full exact-source regressions including #623 reauth drift → exact ClayVerse OCI build → capture image digest + APT/tmux/Python/Claude identities → deny network → in-image #611 policy/reapply attestation for both canonical users → service/readiness checks → execute repaired #622 offline hashed bootstrap and stable-output double lock generation → accept/materialize canonical product lock → rebuild with --require-hashes → #611 promotion decision → rejoin/revalidate #602 → packaged native Claude → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed lifecycle hooks → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete path. Source inspection, PRs, CI definitions, deployment READY, `Sandbox.create`, historical receipts or component PASS do not imply ClayVerse PASS.

### Supply-chain state

The final container still has open acceptance gates until exact isolated OCI evidence closes them. In particular, current main has not yet accepted the #622 generated Python hash lock, and exact resolved package identities must be captured from the admitted image. Source candidates such as the APT snapshot and Claude archive hardening remain bounded until they are fused and executed on the accepted product path.

### Latest cycle delta

**2026-08-17 20:27 +07:00 — `NO_CHANGE` canonical merged ClayVerse product/runtime bytes; retained #623 closes the Clerk-reauth/current-UnifiedDB identity gap on the same lane, and its regression source now also covers live extra-user, rights and generation drift. The Vercel private-source credential blocker remains unchanged.**

- #623 source repair commit `80753efc73be4399d603cb2e7103a517fcffe1d3` added `_assert_reauth_identity_current()`: a refreshed Clerk token may compute a candidate expiry, but `auth_expires_at` is extended only after current `IdentityRouter.resolve(clerk_subject)` still returns the same attached canonical user/session. This reuses UnifiedDB authority and creates no second identity registry.
- Current #623 head `25f86cbf5508c8e3ec07790a4228bc784cd5fb1b` carries reauth-test blob `0783ee3ed71bc2ce3fd3af89e7410f8029147d20`, adding live UnifiedDB extra-user, rights and generation-drift regressions. The source-order regression fences verifier → refreshed expiry calculation → current UnifiedDB identity revalidation → lease extension → `reauthenticated` publication.
- Bounded isolated helper falsifier observed **4/4 PASS**: canonical user/session accepted; user drift, session drift and resolver failure fail closed. Existing readiness/user-contract slice remains **5/5 PASS**. Both are supporting mechanism evidence only; the exact latest PR-head regressions are not executed.
- No pull-request workflow run was returned for the checked #623 semantic/test heads; no exact PR-head or product-runtime credit is awarded. Durable receipt: `the artefact/receipts/2026-08-17_GO_2025_PR623_REAUTH_UNIFIEDDB_FENCE_GPT56SOL.json`.
- Shared current execution evidence remains Vercel deployment `dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8`, which created a real Sandbox, then stopped at missing host-side `GITHUB_READ_TOKEN` before private Research/EntityOS bytes crossed the boundary. Source/OCI runtime credit remains zero; this is not ClayVerse TEST_FAIL.
- #810 remains repaired without force to retained semantic v6 head `78d92753…`; no duplicate controller was created. Append-only correction receipt remains `the artefact/receipts/2026-08-17_GO_2019_PR810_REF_REPAIR_LIVE_REENTRY_GPT56SOL.json`.
- #622 remains a source-repaired but unexecuted stable-output hash-lock lane. No canonical lock bytes are accepted and Docker remains off product `--require-hashes`.
- Daytona remains an authorized fallback but this worker is blocked before provider contact by missing `DAYTONA_API_KEY`/SDK/network path; this is zero runtime credit, not provider/test failure.
- No valid unusual experiment was executed because no shared immutable request/turn identity is exposed for the atomic experiment lease; no uncoordinated duplicate experiment was consumed.
- No VPS, self-hosted/production test, Together API, paid/final training or secret exposure was used.
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

Authorized isolated evidence exists for bounded components, but **whole-product PASS is not claimed**. The current OCI path can start a disposable Vercel Sandbox and records its provider/VM-session identity correctly, but private product source still cannot be staged until the sensitive Preview read credential exists. The #622 source candidate now avoids its self-induced output-path reproducibility false failure, but has no exact current isolated execution; no lock bytes are accepted and Docker remains off product `--require-hashes`. The #623 readiness/auth and reauth/current-UnifiedDB alignment have bounded source-slice mechanism support, not exact full PR/OCI/runtime acceptance; its newest live-UnifiedDB regressions remain unexecuted at the exact branch head. The next accepted runtime claim must bind freshly refreshed product bytes and continue beyond the credential gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.