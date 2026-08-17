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
- **#623** — single retained auth/identity/readiness drift lane. Semantic product source is `3c6c4d98605d72d902ea36ceabf47a73eab11a54`; latest observed branch head is `0310afaba5543e3dbe76fd9eae83e43ffa1e994b`, carrying the concurrently fused healthcheck-test/receipt state. The same lane fences canonical users/equal rights, canonical permanent session IDs, session cardinality, terminal identity and global generation; `_runtime_ready()` now calls the same read-only canonical-user-state validator used by authenticated resolution before any tmux probe. A bounded exact-source-slice reconstruction exercised canonical control, extra-user drift, rights drift, canonical-session-id drift and duplicate-session drift **5/5 PASS**. Classification is **MECHANISM_SUPPORTED / SOURCE CANDIDATE** only; no full PR-head, OCI, Clerk/tmux/Claude runtime or whole-product PASS is claimed. Adversarial review identified one adjacent unresolved extension boundary: WebSocket `reauth` can extend a verified Clerk lease after same-`sub`/`sid` checks without re-running the current read-only UnifiedDB identity/session/generation contract; #623 should close that gap on the same retained lane before promotion.
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

`refresh current main → refresh retained #611/#622 and deliberately admitted #623 → close/review #623 reauth current-identity extension gap on the same retained lane → rebind the single #810 controller exactly once → Sandbox.create → host-side exact private Research + EntityOS fetch/tree verification → verified archives only into Sandbox → reproduce/attest locked EntityOS → full exact-source regressions including #623 reauth drift → exact ClayVerse OCI build → capture image digest + APT/tmux/Python/Claude identities → deny network → in-image #611 policy/reapply attestation for both canonical users → service/readiness checks → execute repaired #622 offline hashed bootstrap and stable-output double lock generation → accept/materialize canonical product lock → rebuild with --require-hashes → #611 promotion decision → rejoin/revalidate #602 → packaged native Claude → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed lifecycle hooks → persistence/recovery → dual-session concurrency/global-generation fencing`.

Whole-product PASS requires the complete path. Source inspection, PRs, CI definitions, deployment READY, `Sandbox.create`, historical receipts or component PASS do not imply ClayVerse PASS.

### Supply-chain state

The final container still has open acceptance gates until exact isolated OCI evidence closes them. In particular, current main has not yet accepted the #622 generated Python hash lock, and exact resolved package identities must be captured from the admitted image. Source candidates such as the APT snapshot and Claude archive hardening remain bounded until they are fused and executed on the accepted product path.

### Latest cycle delta

**2026-08-17 20:23 +07:00 — `NO_CHANGE` canonical merged ClayVerse product/runtime bytes; #810 retained-controller ref repair and #623 re-entry remain preserved, and #622 was source-repaired so its lock reproducibility discriminator no longer fails solely because the two generated headers contain different output filenames. The Vercel private-source credential blocker remains unchanged.**

- Shared current execution evidence remains Vercel deployment `dpl_DSKkEM6GK2pWmrYXwsguRcu1Ryp8`, which created a real Sandbox, then stopped at missing host-side `GITHUB_READ_TOKEN` before private Research/EntityOS bytes crossed the boundary. Source/OCI runtime credit remains zero; this is not ClayVerse TEST_FAIL.
- #810 remains repaired without force to retained semantic v6 head `78d92753…`; no duplicate controller was created. Append-only correction receipt remains `the artefact/receipts/2026-08-17_GO_2019_PR810_REF_REPAIR_LIVE_REENTRY_GPT56SOL.json`.
- #623 remains on the same retained lane with bounded 5/5 readiness/user-contract mechanism support; the next source frontier remains reauthentication against current UnifiedDB identity/session/generation state.
- #622 source falsifier: predecessor head `44ec5e109d40304b152c2fa05ba3e42e690f2820` compiled to `/tmp/requirements.lock.1` and `/tmp/requirements.lock.2` and diffed the outputs, while generated `pip-compile` headers record the invocation/output path. Distinct `-o` names can therefore create a deterministic false reproducibility failure before dependency bytes differ.
- #622 same-lane repair: `de935824c523a4a4b09cdeecbade3d9fabebeee8` compiles twice independently to one `/tmp/requirements.lock`, copies run 1 aside, deletes the output before run 2, then compares saved run-1 bytes with fresh run-2 bytes. `b6b5a83c390944c9f8c9494d29c1d793ed701dcb` source-fences that stable-path sequence and rejects the old `.lock.1`/`.lock.2` pattern.
- Official PyPI release metadata was checked for the eight declared #622 bootstrap wheels (`pip-tools`, `build`, `click`, `packaging`, `pip`, `pyproject-hooks`, `setuptools`, `wheel`): the declared wheel filenames/SHA-256 values match, and Python-3.13-applicable non-extra dependency edges are covered by the declared set at source-metadata scope. This is source evidence, not runtime closure.
- At the first post-repair refresh no workflow run was observed for #622 semantic head `b6b5a83c…`; #622 remains **SOURCE CANDIDATE / UNEXECUTED** with zero OCI/runtime credit. Durable receipt: `the artefact/receipts/2026-08-17_GO_PR622_LOCK_OUTPUT_PATH_REPRO_FALSIFIER_GPT56SOL.json`.
- A stale README write from this cycle was rejected by GitHub SHA fencing after concurrent living-state advancement; the newer README was re-read and preserved before this delta was applied.
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

Authorized isolated evidence exists for bounded components, but **whole-product PASS is not claimed**. The current OCI path can start a disposable Vercel Sandbox and records its provider/VM-session identity correctly, but private product source still cannot be staged until the sensitive Preview read credential exists. The #622 source candidate now avoids its self-induced output-path reproducibility false failure, but has no exact current isolated execution; no lock bytes are accepted and Docker remains off product `--require-hashes`. The #623 canonical-user readiness alignment has bounded source-slice mechanism support, not full PR/OCI runtime acceptance, and its reauthentication lease-extension path still needs current UnifiedDB identity revalidation plus exact regression evidence. The next accepted runtime claim must bind freshly refreshed product bytes and continue beyond the credential gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
