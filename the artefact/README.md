# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**This section is mandatory living state. It must be refreshed in every product-convergent work cycle after canonical code/evidence fusion and before that cycle is considered complete.** A stale README means the cycle is incomplete; detailed evidence remains in Git history and bounded receipts.

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical state authority: **UnifiedDB**; ClayGraph remains derived/rebuildable projection only.
- User/runtime path: Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Runtime cognition: Claude Code is inference/cognition only; it is not canonical durable memory or identity.
- Runtime readiness on current `main`: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission. This gate is read-only and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. Authorized Vercel Sandbox deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` then executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus fail-closed mixed/unknown/empty diagnostic assertions. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Supporting exact-file regression: after rejecting a first reconstruction with a blob mismatch for zero test credit, a byte-exact isolated reconstruction recomputed the expected terminal/test Git blobs above and ran `tests/test_terminal_tmux_control_timeouts.py` **9/9 PASS**. This is supporting exact-file source regression only; it used a bounded identity stub and is not full-branch, OCI, native-Claude, or whole-product runtime evidence.
- Retained repair: draft PR #611 remains the **single retained semantic tmux-3.6a repair lane**. Its product delta is still exactly the terminal repair blob `c185009f8af84e1288747d8352645777a36b2053` plus focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`; duplicate PR #612 is closed unmerged. Branch-head ancestry is deliberately treated as an execution-time property rather than durable truth: immediately before an admitted exact run, refresh `main`, rejoin #611 once, bind that resulting exact head, and execute. Do not repeatedly churn ancestry while no authorized runner can start.
- Latest retained-lane rejoin attempt: #611 was ancestry-rejoined through `main` `6f274dab83836175145d89e68d2ee28a75c32575` at branch head `2957e80228815ac266635981a55f22bc15dc9ed4`, preserving only the same two product/test blobs. Canonical `main` then advanced to `88863af99d133f7f84ffc7f44ef17306e43225b2` through evidence/README-only fusion, so that branch head is again intentionally stale until execution admission exists.
- Exact-head admission evidence: a temporary product-bearing reconstruction and subsequent retained-lane bridge bindings were rejected by Vercel **before build/Sandbox start** with `Deployment rate limited — retry in 24 hours.` The latest retained bridge commit observed in this cycle is `4310f2ef3fef7fa9680158ff53a7978e18fdc622`, bound to #611 head `2957e80228815ac266635981a55f22bc15dc9ed4`; Vercel reports `upgradeToPro=build-rate-limit`. Runtime credit for these exact-head attempts is zero, not TEST_FAIL.
- GitHub Actions on the retained repair also ended before visible step execution (`steps=null`), so they provide zero regression/runtime credit.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is connector-independent, but this ChatGPT controller currently has no admitted provider-contact path/credential injection for Daytona; plugin discovery also exposes no Daytona connector. No Daytona runtime command executed, so Daytona runtime credit is zero.
- Remaining major acceptance gates: on the first actually-startable authorized isolated runner, perform one fresh #611 current-main rejoin + exact-head real-tmux 3.6a rerun, then focused + adjacent regressions and only then consider repair promotion. After that advance to managed native-Claude process attestation, exact OCI build/image identity, startup/readiness, real Clerk JWT/browser WebSocket PTY, automatic hook lifecycle, persistence/recovery, and live dual-session concurrency/generation fencing.

### Latest cycle delta

**2026-08-17 17:31 +07:00 — `NO_CHANGE` product code; retained lane stabilized for rejoin-on-admission and execution blocker exhausted**

- Refreshed canonical `main` through `88863af99d133f7f84ffc7f44ef17306e43225b2`, whose newest merged evidence records the byte-exact focused tmux regression **9/9 PASS** and an exact-head Vercel admission failure before Sandbox start.
- Closed duplicate PR #612 unmerged so #611 remains the only permanent semantic tmux repair lane.
- Rejoined #611 once against then-current `main` `6f274dab83836175145d89e68d2ee28a75c32575`, producing head `2957e80228815ac266635981a55f22bc15dc9ed4`; comparison at that point was `behind_by=0` with exactly the same two intended product/test paths.
- Rebound retained execution bridge PR #846 via commit `4310f2ef3fef7fa9680158ff53a7978e18fdc622` to that exact #611 head. Vercel immediately returned the build-rate-limit status before Sandbox start; no product assertion ran.
- Rechecked GitHub-hosted execution on #611: the available job ended with `steps=null`, so it receives zero test credit.
- Rechecked the authorized Daytona fallback from this controller: no installable Daytona plugin/connector was exposed and no admitted credential/provider-contact path is available here. No provider contact and no runtime credit.
- Canonical `main` then advanced again through evidence/status-only work without touching the two repair blobs. Repeatedly rejoining #611 while all authorized execution is admission-blocked would create ancestry churn without new information, so the durable operating rule is now **rejoin exactly once at execution admission**, not continuously on every status-only `main` movement.
- No unusual experiment was consumed; this remained deterministic regression, adversarial falsifier, execution-admission and coordination work.
- Whole-product acceptance remains **IN_PROGRESS**. Next executable discriminator: first admitted isolated runner → refresh `main` → rejoin #611 → bind exact resulting head → real tmux 3.6a discriminator → focused + adjacent regressions → promotion decision. Only after that proceed to native-Claude/OCI/readiness/restart/concurrency acceptance.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes.
6. For fast-moving noncanonical feature branches, keep exact branch SHA in the cycle delta/receipt and refresh it immediately before execution; do not make continuous ancestry chasing a substitute for executable evidence.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the terminal surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current retained repair runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

GitHub-hosted Actions are not runtime evidence when jobs fail before visible execution. Vercel deployment state alone is likewise not runtime PASS; only an actually started Sandbox command/assertion path is executable evidence at its exact source/environment scope.

## Local isolated source checks

Where an **authorized** isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
