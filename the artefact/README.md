# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**This section is mandatory living state. It must be refreshed in every product-convergent work cycle after canonical code/evidence fusion and before that cycle is considered complete.** A stale README means the cycle is incomplete; detailed exact identities and evidence remain in Git history, PRs and bounded receipts.

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
- Real terminal evidence: the predecessor tmux reapply mechanism was falsified under real tmux 3.6a. A later authorized Vercel Sandbox run verified the byte-identical repair component at its bound older source identity, including pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, and fail-closed mixed/unknown/empty diagnostics. This is strong **component/mechanism PASS at that bound older identity only**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested by that run.
- Retained repair: draft PR #611 is the single retained tmux 3.6a idempotent-reapply lane. Its semantic identity is the terminal blob `c185009f8af84e1288747d8352645777a36b2053` plus focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`. Exact runtime of the **then-current ancestry-rejoined PR head** remains required before promotion. Volatile PR/base/head SHAs belong in the PR and bounded receipts rather than this long-lived current-state paragraph.
- Execution bridge: the repository-owned Dr.-Unterweger Git-preview → `@vercel/sandbox`/OIDC mechanism is established, but the latest exact-head trigger is still blocked before Sandbox start by the Vercel build-rate limit. Deployment/control-plane state earns zero runtime credit unless the bound Sandbox command actually starts.
- Daytona remains the owner-authorized fallback when Vercel is blocked before assertions. The fallback is **connector-independent**: Daytona's documented HTTPS API/SDK/CLI is the provider interface, so absence of a native ChatGPT plugin/connector is not evidence that Daytona itself is unavailable or that the account has no credit. The current ChatGPT controller has no injected Daytona credential path and no direct Daytona/PyPI DNS egress, so it is blocked before provider contact and contributes zero Daytona runtime credit.
- Remaining major acceptance gates include the exact retained-repair real-tmux rerun, exact OCI build/runtime receipt, real Clerk JWT + browser WebSocket PTY verification, authenticated interactive native Claude Code verification for both canonical user homes, automatic hook lifecycle integration, persistence/recovery, managed-Claude process identity in live tmux, and live dual-session concurrency/fencing.

### Latest cycle delta

**2026-08-17 17:24 +07:00 — NO_CHANGE product semantics; execution-admission recheck + anti-stale state repair**

- Rejoined canonical research `main` at `2fefc099a65da5c275eaa1468abef87f4e9b245c` before this cycle's durable write.
- Refreshed PR #611 and confirmed its retained repair still differs from canonical `main` only by the intended terminal runtime file and focused tmux regression; canonical `main` still carries predecessor terminal blob `185a748f80011b324b2c4786644ad42ff369203e`.
- Fresh controller capability recheck: the connected Vercel tool exposes documentation/deployment surfaces but no direct Sandbox lifecycle primitive; plugin discovery returned no installable Daytona/sandbox plugin; the local isolated controller has Python/pytest but no tmux binary and cannot resolve external package/provider DNS. These are **execution-admission/controller limits**, not ClayVerse test failures and not evidence that Daytona itself is unavailable.
- A stricter local real-tmux rerun was attempted only to establish admission: tmux was absent, package-network admission did not become available, so no tmux command or ClayVerse assertion executed and runtime credit is **zero**.
- Hardened the living-state representation against self-induced staleness: exact volatile PR/head/base identities remain in PRs/receipts; the durable README current-state paragraph tracks the retained repair by semantic blob identity and requires a fresh ancestry-rejoined head at execution time.
- `NO_CHANGE` to ClayVerse product/runtime semantics, whole-product acceptance, and the repair contract. No unusual experiment was consumed because this trigger lacks a uniquely claimable shared atomic experiment lease.
- Next executable discriminator: ancestry-rejoin PR #611 to the newest canonical `main`, bind that exact head into the first admitted Vercel or Daytona isolated Sandbox, reproduce all tmux 3.6a idempotency/fail-closed markers, then run focused + adjacent regressions before any merge/promotion.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Keep volatile exact execution/head identities in bounded receipts/PRs when embedding them in the long-lived current-state text would make it stale after unrelated commits.
5. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
6. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes.

Git history, PRs and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the terminal surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound identity under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current retained-repair runtime and the exact current product still require authorized isolated evidence: exact repair rerun, OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
