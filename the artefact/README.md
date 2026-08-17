# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries the current product state and latest concrete delta.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority; ClayGraph is derived/rebuildable.
- Canonical UX: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Managed hooks bind turns to UnifiedDB; effects remain fail-closed through ClayVerse MCP/EffectGate.
- EntityOS is an **optional** digest-bound internal execution/security substrate, not the product endpoint and not required for the baseline container.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#625** tokenless canonical baseline packaging — primary current packaging lane; exact head is moving under coordinated parallel hardening and must be rebound before executable claims.
- **#611** tmux idempotent-reapply — exact in-image tmux remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical `requirements.lock.txt` accepted yet.
- **#623** auth/identity/readiness/reauth drift — source/mechanism supported only.
- **#602** managed native-Claude process attestation — downstream of exact in-image #611.
- Dr.-Unterweger **#810** remains historical/controller evidence; its cross-private-repo `GITHUB_READ_TOKEN` route is not the preferred baseline path.

### Tokenless baseline contract

PR #625 removes the accidental requirement that baseline ClayVerse fetch/stage private EntityOS bytes before it can build. Baseline may omit EntityOS while execution is disabled. If EntityOS is deliberately embedded, tag/digest/source lock/size remain mandatory and mismatches fail closed.

Dockerfile, Compose, normal runtime and the manual OCI workflow now converge on that contract:

- absent EntityOS + disabled execution is admitted;
- unpinned bytes/symlinks fail closed;
- optional staging is restricted to exact `build-assets/entityos/.keep` and `build-assets/entityos/EntityOS` paths;
- Compose does not require an EntityOS digest while Clerk/auth inputs remain mandatory;
- manual OCI workflow EntityOS inputs are optional for baseline and must be supplied as a tag+SHA pair when embedding is requested;
- `github.token` is exposed only to that explicit optional same-repository download step; `GITHUB_READ_TOKEN` is not required by the baseline lane;
- the baseline image verification path asserts `/opt/entityos/EntityOS` is absent.

### Testing policy / current execution boundary

The missing direct Vercel Git-project connection is **not a development blocker**. It is deferred to the final exact OCI acceptance gate. Until then, maximize independent static, unit, negative, adversarial, persistence/restart, concurrency, supply-chain, simulation and disposable component-runtime evidence without upgrading it into OCI/whole-product credit.

The available OpenAI isolated surface has Python/pytest but no Docker, Podman, Buildah or tmux. GitHub Actions runner admission was also rechecked; the rerun failed before observable job/step evidence and job details remain inaccessible through the integration. Therefore exact OCI build/runtime remains unobserved.

The exact `go` unusual-experiment slot remains **COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT** because no immutable shared request/turn ID is exposed. Zero unusual experiments were executed.

### Latest cycle delta

**2026-08-17 21:05 +07:00 — #625 tokenless baseline is now aligned across packaging, Compose, runtime, staging tests and manual OCI-workflow source contracts; bounded component evidence increased, exact OCI remains open.**

- Build-context hardening removed recursive optional-EntityOS sibling admission; focused contract evidence remains green.
- Compose was aligned to an EntityOS-free baseline while preserving mandatory Clerk/auth interpolation.
- `service._entityos_config()` and retained boot/default regressions were aligned to the optional execution-gated contract. Existing bounded slices report **6/6**, **14/14** and **15/15 PASS** at their declared scopes.
- Exact-source Linux component execution of `entityos_bridge.py` exercised real sealed-memfd `run()` behavior: **4/4 PASS**; digest drift and symlink replacement failed closed. This is **COMPONENT_RUNTIME_PASS**, not in-image/OCI acceptance.
- This pass repaired `test_stage_entityos.py` to the bounded staging path and residue checks; converted the manual OCI workflow from mandatory EntityOS inputs to an optional paired/fail-closed path; restricted token exposure to the optional same-repo download step; added baseline image absence verification; and aligned artifact/workflow regression contracts.
- Focused reconstructed contract suite across build-context, packaging, single-container boundary, stager, artifact authority and OCI workflow: **18/18 PASS in 0.10s**. Direct stager checks: valid/uppercase digest PASS with mode `0555`; wrong digest exit `65` with no staged artifact/temp residue; symlink source exit `66` with no staged artifact.
- Commits authored in this pass: `cf9118cc4e2ee5fe96de851d3d64d55b766d93ee`, `ea1a00b6dd8a360673bae4373c2c397ebf2b0cc2`, `714bbfe43fc0eb17335dc886accfe996c0d7bf64`, `78cae34d660124fdb605990afd6bcc3cd7384f60`; bounded receipt commit `4ddc915ce2efc5d7598ad0530941d19f12a3c6cb`.
- New receipt: `the artefact/receipts/2026-08-17_GO_2053_PR625_TOKENLESS_WORKFLOW_CONTRACT_ALIGNMENT_GPT56SOL.json`. Other retained receipts remain authoritative for their narrower runtime/boot/component slices.
- Evidence remains bounded: no full moving-branch pytest, actual Docker build-context transfer, OCI image build/digest, packaged service readiness/runtime or whole-product PASS is claimed.

### Next discriminator

At the first authorized isolated Docker/OCI-capable surface:

`fresh exact #625 head → real build-context membership → EntityOS-free baseline build → verify no EntityOS executable in image → normal baseline service startup/readiness → optional digest-bound EntityOS build + half-input/wrong-digest/extra-file negatives → image digest → continue #611/#622/#602 and full Clerk/PTY/hooks/persistence/recovery/concurrency acceptance`.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound EntityOS substrate.
