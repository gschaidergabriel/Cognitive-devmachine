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
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Live research coordination: current owner law requires material observations to re-enter through live fusion/hypofusion and targeted worker revalidation; delivery alone is not use or causal credit.
- Canonical `main` refreshed for this cycle at `5fbf5b74a65db52d069fb7e0afc4d5e6e11005b9` before the new bounded receipt/README branch delta.
- Retained real-tmux repair: draft PR #611 is the single semantic tmux-3.6a repair lane. Its actual current GitHub head is `2957e80228815ac266635981a55f22bc15dc9ed4`, with exactly two changed files and semantic blobs `c185009f8af84e1288747d8352645777a36b2053` (terminal repair) and `b6bb645dd07645f21ca2e5574f8392c9f13beafc` (focused test).
- Real terminal evidence remains bounded: an older exact-head Vercel Sandbox run verified the byte-identical repair component under real tmux 3.6a with deny-all network. That is component/mechanism evidence only, not exact-current PR #611 runtime PASS, native-Claude PASS, OCI PASS, or whole-product PASS.
- Exact-current execution bridge: `gschaidergabriel/Dr.-Unterweger` draft PR #846 head `4310f2ef3fef7fa9680158ff53a7978e18fdc622` uses its bridge-fix layer to bind runtime receipt identity to PR #611 head `2957e80228815ac266635981a55f22bc15dc9ed4` while retaining independent Git-blob checks for the reconstructed terminal bytes.
- Execution admission remains the blocker. The exact-current bridge attempt was rejected before Sandbox start by the Vercel build-rate limit. The connected ChatGPT Vercel surface exposes deployment/project inspection but no direct Sandbox lifecycle primitive. Daytona remains authorized fallback, but this controller has no admitted provider-contact/credential path. These conditions earn **zero runtime credit**, not TEST_FAIL.
- The currently available isolated controller was rechecked in this cycle: Python 3.13.5 and pytest 9.0.2 are present; `tmux`, Docker and Podman are absent. Therefore no real-tmux or OCI assertion executed locally and runtime credit is zero.
- Managed Claude process attestation remains retained in draft PR #602; managed hook prompt-identity work remains retained in draft PR #454; MicroClay/Stage-B remains on its retained fusion lane #484 with related bounded donors. No duplicate canonical implementation was created in this cycle.
- Remaining major acceptance gates: first admitted exact-current real-tmux rerun and adjacent regressions; then managed native-Claude process attestation, exact OCI build/image identity, startup/readiness, real Clerk JWT/browser WebSocket PTY, automatic hook lifecycle, UnifiedDB persistence/recovery, accepted effects/EntityOS behavior where admitted, and live dual-session concurrency/global-generation fencing.

### Latest cycle delta

**2026-08-17 17:35 +07:00 — `NO_CHANGE` product/runtime code; live-fusion provenance repair and execution-admission revalidation**

- Refreshed canonical research `main` to `5fbf5b74a65db52d069fb7e0afc4d5e6e11005b9` and observed the newly active live fusion/hypofusion worker-reentry owner directive.
- Detected a material coordination drift: `PROGRAM_STATE.json` still referenced an older retained PR #611 head (`6a27ddab...`) in dynamic execution text, while GitHub currently reports PR #611 head `2957e80228815ac266635981a55f22bc15dc9ed4`.
- Independently inspected the Vercel bridge PR #846 and confirmed that its current bridge-fix source binds runtime identity to `2957e80228815ac266635981a55f22bc15dc9ed4`; the runner still enforces the expected terminal Git blob before Sandbox creation.
- Rechecked local isolated execution admission: Python/pytest available, but `tmux`, Docker and Podman are missing. No ClayVerse runtime assertion executed; runtime credit remains zero.
- Did not burn another Vercel Preview merely to reprobe the already-observed build-rate-limit blocker before Sandbox start.
- Added a bounded `ResearchReentryReceipt/v1` under `research_entity/mesh_feedback/20260817T1735p0700-go-pr611-head-drift/` to route the corrected execution identity and counterhypothesis back to affected research/worker lanes.
- Strongest counterhypothesis: a head-marker bridge rebind could still execute stale reconstructed bytes or a different provider build path. Cheapest falsifier remains one actually-started authorized isolated run of PR #846 head `4310f2ef...` requiring current candidate-head marker, exact blob checks, real tmux 3.6a pass markers, deny-all tested network, and Sandbox stop receipt.
- Unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; only minute-precision trigger identity is exposed, so no globally unique experiment lease was minted.
- `NO_CHANGE` to ClayVerse product/runtime code, semantic authority, or whole-product acceptance.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with concrete code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes.
6. For fast-moving noncanonical feature branches, keep exact branch SHA in the cycle delta/receipt and refresh it immediately before execution; do not make continuous ancestry chasing a substitute for executable evidence.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the terminal surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has verified the byte-identical tmux repair component at an older bound head under tmux 3.6a. **Whole-product PASS is not claimed.** Exact-current retained repair runtime and the exact current product still require authorized isolated evidence across OCI build/image identity, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

GitHub-hosted Actions are not runtime evidence when jobs fail before visible execution. Vercel deployment state alone is likewise not runtime PASS; only an actually-started Sandbox command/assertion path is executable evidence at its exact source/environment scope.

## Local isolated source checks

Where an **authorized** isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The Docker build context is default-deny and allowlists only consumed product inputs, including the runtime Claude contract and digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
