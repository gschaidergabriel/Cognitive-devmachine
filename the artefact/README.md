# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**This section is mandatory living state. It must be refreshed in every product-convergent work cycle after canonical code/evidence fusion and before that cycle is considered complete.** It records both the newest known state and what changed in the just-finished cycle. A stale README means the cycle is not complete.

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical state authority: **UnifiedDB**; ClayGraph remains derived/rebuildable projection only.
- User/runtime path: Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Runtime cognition: Claude Code is inference/cognition only; it is not canonical durable memory or identity.
- Canonical `main` observed for this cycle: `a9e08309ceefb441f38f2bdcf89af1a335e8dfd0`. Current `main` still requires canonical state plus both live canonical tmux sessions and transport-policy-v3 attestation; PR #611 remains the single retained tmux-3.6a reapply repair lane and must receive an exact admitted real-tmux rerun before promotion.
- This retained PR #602 lane adds the next discriminator: exactly one live pane whose foreground process and recorded start argv match the exact sanitized managed Claude launch contract. It now also preserves the exact fail-closed tmux-3.6a idempotent reapply semantics from #611 so later process-attestation work cannot silently reintroduce the already-falsified predecessor behavior.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must go through the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Current execution admission: the exact retained #611 rerun remains Vercel build-rate-limited before Sandbox start. Older READY Vercel evidence is old-head component evidence only. Daytona remains an authorized fallback but this controller has no admitted provider-contact/credential path, so Daytona runtime credit is zero.
- Remaining major acceptance gates: exact #611 real-tmux rerun and promotion decision; then current-main rejoin of this process-attestation lane, focused + adjacent regressions, exact OCI build/image identity, live native-Claude process representation, startup/readiness, real Clerk JWT/browser WebSocket PTY, automatic hook lifecycle, persistence/recovery, and live dual-session concurrency/generation fencing.

### Latest cycle delta

**2026-08-17 17:35 +07:00 — fused tmux-3.6a repair semantics into the retained managed-Claude process-attestation lane**

- Refreshed live `main` to `a9e08309ceefb441f38f2bdcf89af1a335e8dfd0`, retained tmux repair PR #611 at observed head `2957e80228815ac266635981a55f22bc15dc9ed4`, and process-attestation PR #602 before this repair at head `84d459622aa8b0e94339b0498ba352b6be17ac97`.
- Adversarial review found a downstream regression risk: #602 also modifies `terminal_sessions.py` but still carried the pre-#611 `_enforce_tmux_policy()` semantics, so promoting it later without semantic fusion could restore the real-tmux-3.6a failure.
- Fused the #611 fail-closed idempotency contract into #602 without creating a second terminal path: only exact missing-table diagnostics for `prefix`, `root`, `copy-mode`, and `copy-mode-vi` are tolerated on nonzero re-source; mixed/unknown/empty diagnostics remain fatal; independent transport-policy-v3 attestation remains mandatory.
- Repaired two lower-layer timeout/order tests so they stub only the new process-attestation predicate and continue testing the transport contract rather than accidentally failing on an unrelated pane probe.
- Exact written Git blobs were rebound before credit: `terminal_sessions.py` `13b895d06d6f99b367e9e6b014a48155d6356095`, timeout regression `08c30cca4452f789aedfc39606d71e3bf058013e`, process-attestation regression `6bfc5cb5a208e85357492ffadff578b1f9f5527d`.
- Authorized isolated supporting exact-file execution on those byte identities: `15 passed in 0.06s`; `py_compile` PASS; exit 0. A prior semantically-equivalent but byte-mismatched local timeout-test reconstruction received zero exact-blob credit and was rerun only after exact Git-blob equality was established.
- Evidence class remains **MECHANISM_SUPPORTED_SUPPORTING_EXACT_FILE_EXECUTION**. This is not a full PR #602 checkout/runtime PASS, not the exact #611 real-tmux rerun, not native-Claude process evidence, not OCI acceptance, and not whole-product PASS.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1735_MANAGED_CLAUDE_TMUX36A_FUSION_GPT56SOL.json`.
- No unusual experiment was consumed: the shared trigger identity available to this organ has minute precision only and no immutable request id, so the atomic lease protocol remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

At the end of every product-convergent cycle:

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** so it reflects the newest canonical reality, removing stale claims.
3. Add or replace **Latest cycle delta** with the concrete changes from that cycle, including code, tests, evidence, blockers and acceptance movement. If nothing canonical changed, write `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment `READY`, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same branch/PR/fusion cycle as the artefact/evidence it describes. A cycle is not complete while the README is stale.

Git history and bounded receipts remain the detailed audit trail; this README stays compact and reflects the **latest** state rather than becoming a second canonical database.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and the current terminal-pivot surface: browser → Clerk → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code built-in tools are disabled in product terminals; a strict local stdio ClayVerse MCP is the admitted state/context/effect bridge. The runtime contract requires each human prompt to enter canonical ClayVerse state through the managed lifecycle and to re-enter through the same causal identity; UnifiedDB remains the durable state/memory authority. Generic host `process.exec` remains fail-closed. EntityOS is a digest-bound internal execution/security/runtime substrate candidate, not the product endpoint, and its external-effect execution remains separately gated.

The previous custom chat API and headless `claude -p` path are retired as product runtime surfaces. `consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised bounded source mechanisms, including the exact written tmux/process-attestation source/test blobs recorded above, but **whole-product PASS is not claimed**. The exact current product still requires the admitted real-tmux repair rerun, a current-main/full-checkout process-attestation batch, exact OCI build/runtime receipt, real Clerk JWT plus browser WebSocket PTY verification, authenticated interactive Claude Code runtime verification for both user homes, managed hook lifecycle, accepted effect/EntityOS behavior where admitted, restart/recovery and live dual-session concurrency/generation fencing.

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
