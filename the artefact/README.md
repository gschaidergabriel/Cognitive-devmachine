# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**Refresh this living state in every product-convergent cycle after canonical evidence/code fusion. A stale README means the cycle is incomplete; detailed evidence stays in Git history and bounded receipts.**

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical durable cognition/state authority: **UnifiedDB**. ClayGraph is derived/rebuildable projection only. MicroClay adapts accessibility/routing only, never truth, identity, privacy or effect authority.
- Product path: Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code is runtime cognition, not canonical durable memory/identity.
- Effects remain fail-closed through ClayVerse EffectGate/MCP; generic host `process.exec` is not an admitted product path. EntityOS remains an optional digest-bound internal execution/security substrate, not the product endpoint.

### Coordination integrity

- Compact boot schema **5.5** loads Live Fusion/Hypofusion before material work. Delivery, reconstruction, plan revalidation, use, effect and causal credit remain distinct; coordination creates no second state/effect authority.
- External live re-entry delivery is now **claim-before-effect**: deterministic `route_id` → canonical manifest CAS claim → re-read own claim → external effect with exact route marker → CAS finalization. Unknown post-effect state stays `UNKNOWN_DELIVERY`; recovery scans the route marker before retry. Exact-file deterministic state-machine regression passed **5/5**; real multi-worker GitHub exactly-once delivery remains unverified.
- Concurrent stale README/shared-state writes have repeatedly been rejected by GitHub SHA/CAS fencing rather than overwriting newer state. This is coordination evidence only, not product-runtime evidence.

### Terminal / managed-Claude spine

- Draft PR **#611** remains the single retained tmux reapply repair lane. Its semantic delta remains terminal blob `c185009f8af84e1288747d8352645777a36b2053` plus focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`; preserved branch head is `2957e80228815ac266635981a55f22bc15dc9ed4` until the next admitted execution-time rejoin/promotion decision.
- Historical real Vercel Sandbox evidence under tmux **3.6a** falsified the predecessor and passed the byte-identical repair component at an older bound head under deny-all network. Native Claude and the OCI product image were not tested there; this remains component/mechanism evidence only.
- Supporting byte-exact source reconstruction ran the focused tmux tests **9/9 PASS**.
- Draft PR **#602** remains the single downstream managed-Claude lane. Live Fusion has incorporated #611 idempotent reapply semantics while retaining managed pane process/start-argv attestation; supporting exact-file checks report **15 focused tests PASS + py_compile PASS**. #602 still requires rejoin/revalidation after #611 product promotion and exact packaged native-Claude/in-image evidence.

### Exact OCI dependency gate

- Current source uses digest-pinned Python 3.13 slim Trixie but installs tmux through ordinary mutable Trixie APT resolution. Current Debian Trixie metadata observed this cycle advertises `tmux 3.5a-3`; that is dependency metadata, **not proof of the version in an unbuilt ClayVerse image**.
- Exact in-image tmux/APT package identity and final image digest remain **UNOBSERVED** until an admitted OCI build records them. Historical tmux 3.6a is an additional robustness/future-version regression, not the sole product proxy.
- The existing source-bound Python hash-lock generator remains the single lane. Draft PR **#622** repairs generator-only `pip-tools` compatibility for the Python 3.13 product base (`7.5.0` → `7.5.3`) and adds a regression rejecting the old pin. #622 is source candidate only: no canonical lock bytes have been minted, Docker is not yet on `--require-hashes`, and authorized isolated runtime credit is zero.
- The exact next OCI source closure is now materialized, not hypothetical: integration branch `go/1750-oci-vcr-source-closure-gpt56sol` at `f8e4deebcb2f4b0b2904fddbcb0006600bc45c50` starts from canonical `main` `7b2a31c9defc76bead047823487c4384ee4bef3e` and differs by **exactly two files** — the retained #611 terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`. It is an ephemeral exact product-candidate closure for execution, not a second permanent product lane.
- Dr.-Unterweger draft PR **#810** remains the single retained OCI/VCR execution controller. Its runner is rebound to the exact closure above. The controller first attempts `Sandbox.create`; only after Sandbox admission does the Vercel build host use vault-only `GITHUB_READ_TOKEN` to fetch/verify the exact private commit/tree/archive. Only archive bytes are written into the Sandbox; the GitHub credential is never forwarded. The controller verifies the #611/Dockerfile/.dockerignore blobs and EntityOS digest/size, installs Docker inside the authorized Sandbox, builds the exact image, records image + tmux/Claude/Python/APT identities, switches the Sandbox to deny-all network, then runs #611 double-reapply/full policy attestation for both canonical users and `clayverse.service --once` inside the exact image.
- PR #810's separate fail-closed source guard is aligned to that same exact runner at commit `0edd4e6b6c262daa2c1af95d300f63855f73029e` / guard blob `fb9766042ff753881440cd33568a59d556e5bcaf`: base `7b2a31c9…`, fused source `f8e4deeb…`, tree `a012708e…`, #611 blobs, Dockerfile/.dockerignore blobs and EntityOS digest/size must all match before the controller is admitted. This is controller coherence only; current OCI runtime remains unobserved.
- A dedicated guard↔runner drift regression is now on the same retained #810 branch at `7ffb47212f8cf17ff174d2db2e01b5414eea7ec2`. It requires every exact identity binding, execution-surface marker, `github_secret_forwarded_to_sandbox=false`, zero unusual-experiment accounting and fail-closed drift rejection to remain aligned. The regression is **source-added but not yet executed**, so it carries zero runtime credit.

### Execution admission

- Earlier exact-current Vercel preview attempts were rejected before Sandbox start by the free deployment-rate limit. Those attempts have zero test/runtime credit and are not TEST_FAIL.
- Vercel deployment `dpl_62R4EoLGtLoi8FqXZAyNXDFaUHeq` was admitted, built and reached READY with OIDC present, but its older hard-coded target guard emitted `SKIP_NON_TARGET_PREVIEW` before `Sandbox.create`. That established build admission at that instant only; it did not establish current ClayVerse Sandbox/OCI runtime behavior.
- The first recomposed #810 preview, deployment `dpl_BH8m9HTYUXWNSPQTDzURrJy5QmuE` at Dr.-Unterweger commit `fd12feb34caa10707e5c94f1c6dcf3d3a11fdce0`, failed closed in the stale `VCR_RUNNER_SOURCE_BINDING_UNRECOGNIZED_FAIL_CLOSED` guard **before `Sandbox.create`**. This is bridge-preflight failure with zero product-runtime credit, not ClayVerse TEST_FAIL.
- The hardened runner at `21e2d1386573a5e054ecafc34371b082d26d5806` was triggered at `7ee72a8489533325d1fe44a73ba8834733a92ea0`, but Vercel rejected that trigger before build with **`Deployment rate limited — retry in 24 hours.`**
- The stale guard/runner binding mismatch was then repaired on the same retained #810 branch at `0edd4e6b6c262daa2c1af95d300f63855f73029e`. Vercel immediately applied the same deployment-rate limit to that repaired exact head before build/Sandbox start. Therefore the controller defect is source-localized and repaired, but **no repaired deployment build, `Sandbox.create`, private-source fetch, OCI build or in-image assertion has executed**. Runtime credit remains **0**; classification is deployment-admission blocker, not TEST_FAIL.
- Daytona remains the owner-authorized **FREE_ONLY** fallback for Vercel pre-assertion failure. The current documented controller state still has no admitted Daytona credential/provider-contact path from this worker, so Daytona provider/account availability remains unobserved and Daytona runtime credit remains zero.
- No VPS, self-hosted runner or production host may substitute for current acceptance execution.

### Unusual-experiment accounting

- This `go` exposes only minute-precision trigger identity and no immutable shared request/turn id, so the atomic unusual-experiment lease fails closed: **0 valid unusual experiments executed**.
- The earlier 17:36 synthetic-second experiment lease was invalid because shared trigger metadata had only minute precision. Its already-executed 277-case parser matrix remains only coordination-tainted bounded mechanism history and provides no current macro-cycle experiment credit.
- Separate macro-cycle trigger identities must never borrow experiment claims/results from one another.

### Remaining acceptance path

First actually-started authorized isolated **current-target OCI** run:

`execute the already-staged exact-source #810 controller without creating a parallel OCI lane → run guard↔runner alignment regression → Sandbox admission → host-side exact private source binding without secret forwarding → build exact OCI image → capture image digest + resolved APT/tmux + Claude/Python artifact identities → run #611 idempotency/fail-closed + full transport-policy attestation on actual in-image tmux for gabriel/andreas → service --once + focused/adjacent regressions → promotion decision → materialize/verify canonical Python hash lock via the retained #622 lane → switch Docker to --require-hashes after exact lock acceptance → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`

Whole-product PASS requires the complete path. Source inspection, PRs, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 18:05 +07:00 — `NO_CHANGE` canonical product/runtime bytes; retained PR810 guard↔runner seam now has a dedicated drift regression; execution remains admission-blocked**

- Refreshed canonical shared reality after the parallel guard-repair cycle; no canonical ClayVerse product/runtime bytes changed and whole-product acceptance remains **IN_PROGRESS**.
- Preserved the single retained #810 OCI controller and the exact `main + #611` execution closure; no second OCI lane, state authority or semantic product path was created.
- Added `tests/test_clayverse_current_oci_guard_runner_alignment.py` on #810 at `7ffb47212f8cf17ff174d2db2e01b5414eea7ec2`. The test binds every guard identity field to the corresponding runner constant and also fences execution-surface, no-secret-forwarding, zero unusual-experiment and fail-closed drift semantics.
- This regression directly covers the seam that previously allowed the stale guard to reject the intentionally recomposed exact runner. It is currently **UNEXECUTED source hardening**, not PASS; runtime credit remains zero.
- Vercel remains deployment-rate-limited before repaired controller build/Sandbox start. Daytona remains authorized but the current controller lacks an admitted credential/provider-contact path. Neither provider state is rewritten as a ClayVerse TEST_FAIL.
- No unusual experiment was executed because the shared trigger identity is minute-precision only. No VPS/self-hosted/production test path was used. Together remains forbidden.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1805_PR810_GUARD_RUNNER_ALIGNMENT_REGRESSION_GPT56SOL.json`.
- Next discriminator: execute the **same** repaired #810 controller plus this guard↔runner regression at the first admitted isolated deployment, then proceed through Sandbox admission → exact source bind → OCI build → in-image dependency/PR611/service evidence.

### Cycle update rule

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** to the newest canonical reality; remove stale dynamic claims.
3. Update **Latest cycle delta** with concrete code/evidence/blocker movement. If canonical product bytes did not change, record `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment READY, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same fusion cycle as the evidence it summarizes.
6. For fast-moving feature branches, rebind branch SHA immediately before execution rather than continuously churning ancestry while no runner can start.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, including historical real-tmux evidence, but **whole-product PASS is not claimed**. Exact current product evidence still requires the current-target OCI/image/dependency gate and all downstream auth/Claude/lifecycle/recovery/concurrency gates above.

GitHub-hosted jobs that fail before visible steps and Vercel deployments that never reach Sandbox execution provide zero semantic runtime credit.

## Local isolated source checks

Where an **authorized isolated** Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for the exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
