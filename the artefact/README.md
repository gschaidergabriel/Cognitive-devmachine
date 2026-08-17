# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries the current product state and latest concrete delta.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Final runtime model: **sealed VM-like sandbox/appliance with explicit ingress and egress**.
- UnifiedDB is the sole durable canonical cognition/state authority; ClayGraph is derived/rebuildable.
- Canonical UX: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Managed hooks bind turns to UnifiedDB; effects remain fail-closed through ClayVerse MCP/EffectGate.
- EntityOS is the hardened internal execution/security/runtime substrate, not the product endpoint. **Development/baseline builds may omit it, but the final accepted ClayVerse image MUST contain the complete accepted EntityOS substrate.**
- Internal failures must be contained by the sealed continuum and recovered through known-good logical snapshots, generation fencing and causal re-entry without blind external-effect replay.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#625** tokenless development/baseline packaging — primary current baseline lane; exact head is moving under coordinated parallel hardening and must be rebound before executable claims. Its EntityOS-free mode can never receive whole-product PASS.
- **#611** tmux idempotent-reapply — exact in-image tmux remains the promotion discriminator.
- **#622** Python hash-lock generator — source candidate/unexecuted; no canonical `requirements.lock.txt` accepted yet.
- **#623** auth/identity/readiness/reauth drift — source/mechanism supported only.
- **#602** managed native-Claude process attestation — downstream of exact in-image #611.
- Dr.-Unterweger **#810** remains the confirmed Vercel Sandbox orchestration bridge/controller evidence; its cross-private-repo `GITHUB_READ_TOKEN` source-fetch route is not required by the tokenless development baseline and is not being reintroduced as a baseline prerequisite.

### Tokenless development/baseline contract

PR #625 removes the accidental requirement that a **development/baseline** ClayVerse build fetch/stage private EntityOS bytes before it can build. Such a baseline may omit EntityOS only while execution is disabled. It is useful for packaging, service, auth, persistence and adjacent component validation, but it **cannot** satisfy final ClayVerse acceptance.

The newest owner directive supersedes any interpretation that made the accepted final EntityOS substrate optional. Final PASS requires the complete accepted EntityOS runtime substrate inside the same sealed ClayVerse image.

Dockerfile, Compose, normal runtime and the retained manual OCI workflow converge on a two-level contract without creating two product authorities:

- development baseline: absent EntityOS + disabled execution is admitted, but whole-product PASS is impossible;
- final candidate: complete accepted EntityOS must be embedded in the same image and remain digest/size/source-lock bound;
- unpinned bytes/symlinks fail closed;
- optional development staging is restricted to exact `build-assets/entityos/.keep` and `build-assets/entityos/EntityOS` paths;
- Compose does not require an EntityOS digest for the development baseline while Clerk/auth inputs remain mandatory;
- manual OCI workflow EntityOS inputs are optional for development baseline and must be supplied as a tag+SHA pair for the EntityOS-bearing final-candidate path;
- `github.token` is exposed only to that explicit optional same-repository download step; `GITHUB_READ_TOKEN` is not a baseline requirement;
- the baseline image verification path asserts `/opt/entityos/EntityOS` is absent;
- exactly one canonical ClayVerse OCI workflow remains: `.github/workflows/clayverse-artefact-ci.yml`; the divergent legacy `.github/workflows/clayverse-artifact-ci.yml` path is retired and fenced by regression.

### Testing policy / current execution boundary

Vercel Sandbox execution is confirmed through the retained Dr.-Unterweger #810 Git-preview/OIDC controller; lack of direct ChatGPT `sandbox.create/exec` actions is not evidence of Sandbox unavailability. The retained #810 path has repeatedly reached `Sandbox.create`, but its current cross-private-repo source-fetch design stops before Research source staging when host-side `GITHUB_READ_TOKEN` is absent. That credential blocker earns zero source/OCI runtime credit and is not ClayVerse TEST_FAIL.

For the user-directed tokenless development baseline, do not restore the private EntityOS/read-token prerequisite merely to obtain a baseline run. Continue maximizing source/component evidence while seeking an authorized source-bound OCI surface that can receive exact #625 bytes without creating a second product authority. Final acceptance still requires the complete accepted EntityOS substrate by the newest owner directive.

The available OpenAI isolated surface has Python/pytest but no Docker or Podman. Exact OCI build/runtime therefore remains unobserved on that surface.

The authorized Daytona fallback remains blocked from the current ChatGPT orchestrator before provider contact according to the current execution-path notice; that is not evidence that Daytona itself is unavailable and is not ClayVerse TEST_FAIL.

The exact `go` unusual-experiment slot remains **COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT** because no immutable shared request/turn ID is exposed. Zero unusual experiments were executed.

### Latest cycle delta

**2026-08-17 — #625 is now explicitly fenced as a tokenless development/baseline lane below the final mandatory-EntityOS acceptance gate; the duplicate OCI path is removed and exact OCI runtime remains open.**

- Build-context hardening removed recursive optional-EntityOS sibling admission; focused contract evidence remains green.
- Compose was aligned to an EntityOS-free development baseline while preserving mandatory Clerk/auth interpolation.
- `service._entityos_config()` and retained boot/default regressions were aligned to the development-baseline execution-gated contract. Existing bounded slices report **6/6**, **14/14** and **15/15 PASS** at their declared scopes.
- Exact-source Linux component execution of `entityos_bridge.py` exercised real sealed-memfd `run()` behavior: **4/4 PASS**; digest drift and symlink replacement failed closed. This is **COMPONENT_RUNTIME_PASS**, not in-image/OCI acceptance.
- Focused reconstructed contract suite across build-context, packaging, single-container boundary, stager, artifact authority and OCI workflow: **18/18 PASS in 0.10s**. Direct stager checks: valid/uppercase digest PASS with mode `0555`; wrong digest exit `65` with no staged artifact/temp residue; symlink source exit `66` with no staged artifact.
- The stale second OCI workflow `.github/workflows/clayverse-artifact-ci.yml`, which still required top-level `the artefact/EntityOS`, was removed. `test_only_one_canonical_clayverse_oci_workflow_exists` fences reintroduction of that divergent path. Repair commits: `01c994816bd3ad66e6a9a8400e76de03c794ac1c` and `41473e8dcc8df1cadde7aee3cce2bb627c143dd5`.
- Vercel execution-path classification was corrected against current canonical state: PR810 is a confirmed Sandbox bridge, but its host-side private Research fetch remains credential-blocked before product source staging. The development baseline does not regain a `GITHUB_READ_TOKEN` dependency.
- Newer canonical owner authority was then observed on `main`: final accepted ClayVerse is a sealed machine continuum and **must contain complete accepted EntityOS**. The #625 manifest was corrected in `e65a4f1b4c6e0e0eb78f82ea301e8a19477955f8`; `test_entityos_default_optional.py` was converted into a development-vs-final acceptance fence in `3a7b682c82029e79f7bb404077e8c3b86b645663`.
- Anti-entropy receipt: `the artefact/receipts/2026-08-17_GO_2112_PR625_SINGLE_OCI_LANE_FENCE_GPT56SOL.json` (`4793eed9f09e13936218b12a37ac21ce075edb33`). Earlier narrower receipts remain authoritative only at their declared scopes.
- Evidence remains bounded: no full moving-branch pytest, actual Docker build-context transfer, OCI image build/digest, packaged service readiness/runtime, complete accepted EntityOS-in-image runtime, crash/snapshot recovery or whole-product PASS is claimed.

### Next discriminator

At the first authorized isolated Docker/OCI-capable source-bound surface:

`fresh exact #625 head → real build-context membership → EntityOS-free DEVELOPMENT baseline build → prove baseline cannot claim final PASS → normal baseline service startup/readiness → build FINAL-CANDIDATE variant with complete digest-bound EntityOS → half-input/wrong-digest/extra-file negatives → image digest → in-image EntityOS/managed terminal + #611/#622/#602 → sealed-continuum crash/snapshot recovery → Clerk/PTY/hooks/persistence/recovery/concurrency acceptance`.

The preferred path remains Vercel when exact #625 source can be admitted without restoring the retired baseline token dependency; otherwise use an admitted egress-capable Daytona controller. Do not use VPS/self-hosted/production hosts.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and a tokenless development baseline. The final accepted architecture additionally requires the complete accepted EntityOS substrate inside the same sealed container continuum plus automatic known-good snapshot recovery.
