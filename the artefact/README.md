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
- Live re-entry delivery atomicity: targeted external worker/research delivery now requires a deterministic `route_id`, a canonical manifest compare-and-swap claim **before** the external comment/effect, an exact route marker on delivery, and CAS finalization. Uncertain post-effect state remains `UNKNOWN_DELIVERY` and recovery must scan for the exact marker before any retry. Exact-file deterministic state-machine regression is **5/5 PASS** for blobs `236bf052b66f884e402847f198bdb2fb319e4ff2` + `f4254aa1b79ecd18326df93bc7bf1bb1aa44853e`; real multi-worker GitHub exactly-once delivery remains unverified.
- Minimal boot now carries that coordination law explicitly: `research_entity/continuity/BOOTSTRAP_MINIMAL.json` schema **5.5** names and loads `LIVE_FUSION_HYPOFUSION_WORKER_REENTRY_DIRECTIVE.md` before material work, requires novelty classification plus targeted `ADOPT|CHALLENGE|DEFER|NO_CHANGE` re-entry after material outcomes, and keeps delivery/use/causal-credit states distinct. This is coordination boot wiring only, not a second state authority or product-runtime PASS.
- Runtime readiness on current `main`: `/readyz` requires canonical state and both canonical tmux sessions to be live and pass the managed transport-policy-v3 attestation used by attach admission. This gate is read-only and does not create or repair sessions.
- Clerk/PTY lease boundary: post-attach initial resize, received terminal frames, PTY input writes and PTY output publication are fenced against the verified Clerk lease.
- Effects: generic host `process.exec` is fail-closed; admitted effects must pass the ClayVerse effect boundary. EntityOS remains an optional digest-bound internal execution/security/runtime substrate, not the product endpoint.
- Real terminal evidence: the predecessor reapply mechanism was first falsified under real tmux 3.6a. Authorized Vercel Sandbox deployment `dpl_6z5oXV29Q4TgRonAgs9TaEmxfB5T` then executed terminal blob `c185009f8af84e1288747d8352645777a36b2053` and focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc` at bound old head `ef61bfb85ab59291c3b0b33d024aa098b1f29089` and passed pre-policy upgrade, already-hardened reapply, new-server second source, direct multi-argv fake-Claude launch, plus fail-closed mixed/unknown/empty diagnostic assertions. Network was deny-all during the candidate test. This is strong **component/mechanism PASS at that bound old head**, not exact-current or whole-product PASS; native Claude and the OCI product image were not tested.
- Supporting exact-file regression: after rejecting a first reconstruction with a blob mismatch for zero test credit, a byte-exact isolated reconstruction recomputed the expected terminal/test Git blobs above and ran `tests/test_terminal_tmux_control_timeouts.py` **9/9 PASS**. This is supporting exact-file source regression only; it used a bounded identity stub and is not full-branch, OCI, native-Claude, or whole-product runtime evidence.
- Unusual-experiment coordination incident: a 17:36 `tmux_3_6a_idempotent_diagnostic_mutation_fence` was executed after a claim synthesized `17:36:00.000000` from user-message metadata that was available only at **minute precision**. That claim is invalid under the atomic lease protocol and did not authorize execution. The observed 277-case parser matrix (19 positive controls, 258 negative mutations, zero unexpected acceptances/rejections) is preserved only as coordination-tainted bounded mechanism history. Valid unusual-experiment credit is **0**; real-tmux/OCI/native-Claude/whole-product credit is **0**; no further unusual experiment is permitted for that 17:36 `go`.
- Cross-trigger experiment isolation: the current 17:24 `go` must never borrow a claim/result from the separate 17:36 macro-cycle. One local 26-case parser probe was initiated after that foreign claim was mistakenly associated with the 17:24 trigger; it is preserved only in `the artefact/receipts/2026-08-17_GO_1724_CROSS_TRIGGER_EXPERIMENT_MISBIND_GPT56SOL.json` as an **unauthorized cross-trigger duplicate probe with zero evidence/acceptance credit**. No product code was changed from it. This 17:24 `go` still has no valid unusual-experiment lease.
- Retained repair: draft PR #611 remains the **single retained semantic tmux reapply repair lane**. Its product delta is still exactly the terminal repair blob `c185009f8af84e1288747d8352645777a36b2053` plus focused-test blob `b6bb645dd07645f21ca2e5574f8392c9f13beafc`; duplicate PR #612 is closed unmerged. During a parallel coordination race #611 briefly appeared closed with its branch ref moved to a no-diff shared-state commit; the existing branch was restored byte-identically to preserved head `2957e80228815ac266635981a55f22bc15dc9ed4` and the same draft PR reopened. No new lane or repair semantics were created.
- OCI dependency-version boundary: canonical `Dockerfile` uses digest-pinned `python:3.13.14-slim-trixie` but installs `tmux` through ordinary mutable Trixie APT sources. Official Debian Trixie package metadata observed on 2026-08-17 advertises `tmux 3.5a-3`; therefore a 3.6a-only rerun is not sufficient evidence for the current one-container runtime. The exact built-image version remains **UNOBSERVED** until an admitted OCI build captures APT resolution, image digest and `tmux -V` inside that image. This is consistent with the existing open APT supply-chain gate in `SOURCE_LOCK.json`.
- Python dependency integrity boundary: a source-bound lock generator already exists and is the single retained lane; canonical `requirements.lock.txt` is still absent and the Dockerfile still does not enforce `--require-hashes`. Do not create a duplicate generator. The same next exact OCI batch must materialize/verify the canonical Python hash lock and bind the resolved Python artifacts before product acceptance.
- Python lock-generator compatibility: draft PR #622 retains that same generator lane and repairs generator-only `pip-tools==7.5.0` to `7.5.3`, with a regression rejecting the old pin. Upstream added declared/tested Python 3.13 support after 7.5.0, while the ClayVerse generator intentionally executes inside the digest-pinned Python 3.13 product base. #622 is **source candidate only**: no canonical lock bytes were fabricated, Docker is not yet on `--require-hashes`, and authorized isolated runtime credit is zero.
- Latest retained-lane rejoin attempt: #611 was ancestry-rejoined through `main` `6f274dab83836175145d89e68d2ee28a75c32575` at branch head `2957e80228815ac266635981a55f22bc15dc9ed4`, preserving only the same two product/test blobs. Canonical `main` has since advanced through evidence/status/re-entry work without promoting those repair bytes, so that branch head is intentionally stale until execution admission exists.
- Exact-head admission evidence: product-bearing reconstruction and retained-lane bridge attempts were rejected by Vercel **before build/Sandbox start** with the build-rate limit. Runtime credit for those exact-head attempts is zero, not TEST_FAIL.
- Fresh GitHub Actions admission recheck on retained #611 was accepted by the control plane but again terminated before any visible step (`steps=[]`/no step execution). It contributes zero regression/runtime credit and is classified as runner/pre-step admission failure, not semantic TEST_FAIL.
- Daytona remains the owner-authorized **FREE_ONLY** fallback for Vercel pre-assertion failure. The merged fallback mechanism is connector-independent and fail-closed. A fresh GitHub-hosted controller bridge was staged in `gschaidergabriel/Dr.-Unterweger` at exact commit `e9a50a8325810410b837b1bae85212ef5710fa3f`, requesting fallback only for `RATE_LIMIT` with `vercel_assertion_reached=false`. The exact-head Actions query returned **0 workflow runs**, so no Daytona provider contact, credential use, sandbox creation or runtime command occurred. This narrows the blocker to controller/trigger admission; it is not Daytona TEST_FAIL and gives no provider/account/credit evidence.
- Managed Claude process attestation: draft PR #602 remains the single downstream managed-Claude lane. Live Fusion has now incorporated the #611 idempotent tmux reapply semantics into that branch while retaining the managed pane process/start-argv predicate; exact written source/test blobs passed **15 focused exact-file source/mechanism tests** plus `py_compile`. This is supporting mechanism evidence only. #602 remains Draft/downstream until the exact OCI/in-image tmux gate decides #611 promotion, after which #602 must be rejoined/revalidated against the promoted terminal spine and packaged native Claude representation before any runtime promotion.
- WebSocket queue/compression hardening: the parallel anti-entropy race closed **both** historical candidates #434 and #448 unmerged while receipts briefly encoded opposite retained-lane claims. Neither closed PR is retained product authority. Current `main` remains canonical with the already-admitted simpler WebSocket size bound; any future queue/compression/backend candidate must be freshly adjudicated against then-current source and repository-pinned runtime evidence rather than revived by coordination prose alone.
- Remaining major acceptance gates: on the first actually-startable authorized isolated OCI runner, refresh `main`, rejoin #611 once, rejoin #622 if still needed, build/run the exact ClayVerse image, capture image digest + APT/tmux + Python dependency identities, run the #611 idempotency/fail-closed behavior plus full transport-policy attestation on the image's actual tmux, execute focused + adjacent regressions, materialize/verify the canonical Python hash lock, switch the Docker dependency install to `--require-hashes`, and only then decide repair promotion. After promotion, rejoin/revalidate #602 and advance to packaged native-Claude process attestation, startup/readiness, real Clerk JWT/browser WebSocket PTY, automatic hook lifecycle, persistence/recovery, and live dual-session concurrency/generation fencing.

### Latest cycle delta

**2026-08-17 17:48 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; Python hash-lock generator compatibility candidate fused into the exact OCI frontier**

- Preserved the 17:47 Live Re-entry claim-before-effect repair and its bounded 5/5 deterministic state-machine evidence; real multi-worker exactly-once delivery remains unverified.
- Retained the existing single source-bound Python lock generator and opened draft PR #622 rather than creating a second resolver path.
- Upstream compatibility review found generator pin `pip-tools==7.5.0` predates declared/tested Python 3.13 support, while the generator executes inside ClayVerse's digest-pinned Python 3.13 base. #622 changes generator-only tooling to `pip-tools==7.5.3` and adds a regression rejecting the old pin.
- Existing lock-generation invariants remain intact: product first-`FROM` derivation, requirements SHA binding, double `pip-compile --generate-hashes`, byte-identical diff gate, binary wheelhouse verification under `--require-hashes`, lock SHA and gzip/base64 evidence output.
- Controller-only structural assertions passed with **zero authorized ClayVerse runtime credit**. No `requirements.lock.txt` bytes were fabricated and Docker was not prematurely switched to `--require-hashes`.
- Bounded candidate receipt lives on #622: `the artefact/receipts/2026-08-17_GO_1744_PYTHON_LOCK_GENERATOR_PY313_COMPAT_GPT56SOL.json`.
- Preserved the fail-closed unusual-experiment accounting and started no second unusual experiment.
- Vercel exact-current Sandbox execution remains unavailable at the current admission boundary; the Daytona controller preflight still has no provider-contacting run. No VPS/self-hosted/production fallback was used.
- Next highest-information executable step remains one actually-started authorized isolated OCI batch: refresh `main` → rejoin #611 and #622 once if still needed → build/run exact product base → bind image/APT/tmux/Python identities → execute #611 on actual in-image tmux → generate and verify canonical Python hash lock → switch Docker to `--require-hashes` → promotion decision → rejoin/revalidate #602 → packaged native-Claude/readiness/restart/concurrency gates.
- Whole-product acceptance remains **IN_PROGRESS**.

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

Focused isolated tests have exercised bounded source mechanisms, and real Vercel Sandbox execution has both falsified the predecessor tmux reapply behavior and verified the byte-identical repair component at an older bound head under tmux 3.6a, but **whole-product PASS is not claimed**. Exact current retained repair runtime and the exact current product still require authorized isolated evidence: exact OCI dependency/image binding plus repair rerun, canonical Python hash-lock materialization/enforcement, startup/readiness, real Clerk JWT plus browser WebSocket PTY, authenticated native Claude Code for both user homes, managed hook lifecycle, UnifiedDB persistence/recovery, accepted effect/EntityOS behavior where admitted, and live dual-session concurrency/generation fencing.

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
