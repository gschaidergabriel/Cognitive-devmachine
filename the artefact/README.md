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
- Research coordination: material deltas now use **Live Fusion** for targeted research/worker re-entry, with **Live Hypofusion** automatically opening an adversarial counterhypothesis lane for material contradiction, promotion/merge, shared-ancestry pseudo-replication, persistent blockers, OOD/security results or competing worker semantics. Exact `fusion` and `hypofusion` commands remain full-depth macro-runs. Delivery, reconstruction, plan revalidation, use, local effect and causal credit remain explicitly distinct; this layer creates no second state/effect authority.
- Minimal boot now carries that coordination law explicitly: `research_entity/continuity/BOOTSTRAP_MINIMAL.json` schema **5.5** names and loads `LIVE_FUSION_HYPOFUSION_WORKER_REENTRY_DIRECTIVE.md` before material work, requires novelty classification plus targeted `ADOPT|CHALLENGE|DEFER|NO_CHANGE` re-entry after material outcomes, and keeps delivery/use/causal-credit states distinct. This is coordination boot wiring only, not a second state authority or product-runtime PASS.
- Runtime readiness on current `main`: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission. This gate is read-only and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. Authorized Vercel Sandbox deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` then executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus fail-closed mixed/unknown/empty diagnostic assertions. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Supporting exact-file regression: after rejecting a first reconstruction with a blob mismatch for zero test credit, a byte-exact isolated reconstruction recomputed the expected terminal/test Git blobs above and ran `tests/test_terminal_tmux_control_timeouts.py` **9/9 PASS**. This is supporting exact-file source regression only; it used a bounded identity stub and is not full-branch, OCI, native-Claude, or whole-product runtime evidence.
- Unusual-experiment coordination incident: a 17:36 `tmux_3_6a_idempotent_diagnostic_mutation_fence` was executed after a claim synthesized `17:36:00.000000` from user-message metadata that was available only at **minute precision**. That claim is invalid under the atomic lease protocol and did not authorize execution. The observed 277-case parser matrix (19 positive controls, 258 negative mutations, zero unexpected acceptances/rejections) is preserved only as coordination-tainted bounded mechanism history. Valid unusual-experiment credit is **0**; real-tmux/OCI/native-Claude/whole-product credit is **0**; no further unusual experiment is permitted for this `go`.
- Retained repair: draft PR #611 remains the **single retained semantic tmux reapply repair lane**. Its product delta is still exactly the terminal repair blob `c185009f8af84e1288747d8352645777a36b2053` plus focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`; duplicate PR #612 is closed unmerged. Historical tmux 3.6a evidence remains useful robustness/mechanism evidence, but promotion must bind the tmux version actually resolved into the exact OCI candidate rather than assuming 3.6a is the current product dependency.
- OCI dependency-version boundary: canonical `Dockerfile` uses digest-pinned `python:3.13.14-slim-trixie` but installs `tmux` through ordinary mutable Trixie APT sources. Official Debian Trixie package metadata observed on 2026-08-17 advertises `tmux 3.5a-3`; therefore a 3.6a-only rerun is not sufficient evidence for the current one-container runtime. The exact built-image version remains **UNOBSERVED** until an admitted OCI build captures APT resolution, image digest and `tmux -V` inside that image. This is consistent with the existing open APT supply-chain gate in `SOURCE_LOCK.json`.
- Python dependency integrity boundary: a source-bound lock generator already exists and is the single retained lane; canonical `requirements.lock.txt` is still absent and the Dockerfile still does not enforce `--require-hashes`. Do not create a duplicate generator. The same next exact OCI batch must materialize/verify the canonical Python hash lock and bind the resolved Python artifacts before product acceptance.
- Latest retained-lane rejoin attempt: #611 was ancestry-rejoined through `main` `6f274dab83836175145d89e68d2ee28a75c32575` at branch head `2957e80228815ac266635981a55f22bc15dc9ed4`, preserving only the same two product/test blobs. Canonical `main` has since advanced through evidence/status/re-entry work without promoting those repair bytes, so that branch head is intentionally stale until execution admission exists.
- Exact-head admission evidence: product-bearing reconstruction and retained-lane bridge attempts were rejected by Vercel **before build/Sandbox start** with the build-rate limit. Runtime credit for those exact-head attempts is zero, not TEST_FAIL.
- Fresh GitHub Actions admission recheck on retained #611 was accepted by the control plane but again terminated before any visible step (`steps=[]`/no step execution). It contributes zero regression/runtime credit and is classified as runner/pre-step admission failure, not semantic TEST_FAIL.
- Daytona remains the owner-authorized **FREE_ONLY** fallback for Vercel pre-assertion failure. The merged fallback mechanism is connector-independent and fail-closed. A fresh GitHub-hosted controller bridge was staged in `gschaidergabriel/Dr.-Unterweger` at exact commit `e9a50a8325810410b837b1bae85212ef5710fa3f`, requesting fallback only for `RATE_LIMIT` with `vercel_assertion_reached=false`. The exact-head Actions query returned **0 workflow runs**, so no Daytona provider contact, credential use, sandbox creation or runtime command occurred. This narrows the blocker to controller/trigger admission; it is not Daytona TEST_FAIL and gives no provider/account/credit evidence.
- Managed Claude process attestation: draft PR #602 is the single retained downstream lane, but its current `terminal_sessions.py` does not contain the #611 idempotent reapply repair. Therefore #602 must remain downstream of the exact #611 execution/promotion gate and be rejoined only after that repair is admitted; it must not become an alternate terminal semantics path.
- WebSocket queue/compression hardening: the parallel anti-entropy race closed **both** historical candidates #434 and #448 unmerged while receipts briefly encoded opposite retained-lane claims. Neither closed PR is retained product authority. Current `main` remains canonical with the already-admitted simpler WebSocket size bound; any future queue/compression/backend candidate must be freshly adjudicated against then-current source and repository-pinned runtime evidence rather than revived by coordination prose alone.
- Remaining major acceptance gates: on the first actually-startable authorized isolated OCI runner, refresh `main`, rejoin #611 once, build the exact ClayVerse image, capture image digest + APT/tmux + Python dependency identities, run the #611 idempotency/fail-closed behavior plus full transport-policy attestation on the image's actual tmux, execute focused + adjacent regressions, materialize/enforce the canonical Python hash lock, and only then decide repair promotion. Retain tmux 3.6a as an additional robustness/future-version regression. After promotion, rejoin/revalidate #602 and advance to packaged native-Claude process attestation, startup/readiness, real Clerk JWT/browser WebSocket PTY, automatic hook lifecycle, persistence/recovery, and live dual-session concurrency/generation fencing.

### Latest cycle delta

**2026-08-17 17:44 +07:00 — `NO_CHANGE` product/runtime code; exact OCI dependency gate + Daytona admission discriminator fused**

- Preserved the canonical fail-closed adjudication of the invalid 17:36 unusual-experiment lease: the 277-case parser observation remains coordination-tainted mechanism history only; valid unusual-experiment credit is **0**, no real-tmux/OCI/native-Claude credit exists, and no further unusual experiment is permitted for this `go`.
- Fused the parallel tmux/OCI and Python-lock frontier rather than duplicating either path. Historical tmux 3.6a remains robustness evidence, while product promotion now binds the exact in-image tmux/APT/Python artifacts and image digest.
- Live Fusion/Hypofusion boot wiring is present in compact boot schema 5.5; targeted re-entry remains coordination only, never a second truth/effect authority.
- Verified that the latest visible READY Vercel tmux bridge is statically bound to an older accepted component identity. Later exact-current attempts remain blocked before Sandbox start; READY cannot be retrofitted into current runtime evidence.
- Tested the already-merged **FREE_ONLY Daytona fallback route at the controller boundary** without exposing secrets: bridge base `03851eae330fc889d30d1d10bf68f029beb80381`, branch `chatgpt/go-daytona-admission-preflight-20260817-1736`, commit `e9a50a8325810410b837b1bae85212ef5710fa3f`. Exact Actions lookup returned **0 runs**. Classification: controller/trigger nonexecution before Daytona provider contact; runtime/test credit remains zero. Durable receipt: `the artefact/receipts/2026-08-17_GO_1743_DAYTONA_ACTIONS_ADMISSION_PREFLIGHT_GPT56SOL.json`.
- Duplicate live-reentry comments created during a fast parallel handoff were immediately marked anti-entropy/no-semantic-delta after the canonical deliveries were observed; no second worker authority was created.
- `NO_CHANGE` to ClayVerse product/runtime bytes and whole-product acceptance. Whole-product status remains **IN_PROGRESS**.
- Next highest-information executable step is one coordinated actually-started authorized isolated OCI batch: refresh `main` → rejoin #611 once → build exact image → capture image digest + resolved tmux/APT/Python identities → exercise #611 against actual in-image tmux + focused/adjacent regressions → enforce canonical Python hash lock → promotion decision → rejoin #602 → native-Claude/readiness/restart/concurrency gates.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current retained repair runtime and the exact current product still require authorized isolated evidence: exact OCI dependency/image binding plus repair rerun, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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