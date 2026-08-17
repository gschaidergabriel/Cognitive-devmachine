# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**Refresh this living state in every product-convergent cycle after canonical evidence/code fusion. A stale README means the cycle is incomplete; detailed evidence stays in Git history and bounded receipts.**

### Current state

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- Canonical durable cognition/state authority: **UnifiedDB**. ClayGraph is derived/rebuildable only. MicroClay adapts retrieval/accessibility, never truth, identity, privacy or effect authority.
- Product path remains Clerk-authenticated browser → authenticated WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI. Claude Code is runtime cognition, not durable canonical memory/identity.
- Effects remain fail-closed through ClayVerse EffectGate/MCP. Generic host `process.exec` is not admitted. EntityOS is an optional digest-bound internal execution/security substrate, not the product endpoint.
- Live Fusion/Hypofusion coordination is active; external worker delivery uses claim-before-effect/CAS semantics. Coordination evidence is not product-runtime evidence.

### Retained terminal / Claude lanes

- Draft PR **#611** is the single retained tmux reapply repair lane. Exact semantic blobs remain `c185009f8af84e1288747d8352645777a36b2053` (terminal) + `b6bb645dd07645f21ca2e5574f8392c9f13beafc` (focused test), preserved at head `2957e80228815ac266635981a55f22bc15dc9ed4` until admitted execution-time rejoin/promotion.
- Historical real Vercel Sandbox evidence under tmux **3.6a** falsified the predecessor and passed the byte-identical repair component at an older bound head; supporting exact-file focused source regression is **9/9 PASS**. Neither is exact-current OCI/native-Claude/whole-product PASS.
- Draft PR **#602** remains the single downstream managed-Claude process-attestation lane. It carries #611 semantics plus managed process/start-argv checks with bounded exact-file evidence (**15 focused PASS + py_compile PASS**) only; it must be rejoined/revalidated after #611 product promotion.

### Exact OCI / supply-chain gate

- Canonical source uses digest-pinned Python 3.13 slim Trixie, but tmux still resolves through mutable Trixie APT and the ClayVerse Python dependency install is not yet backed by an accepted canonical `--require-hashes` lock. Exact image digest, APT/tmux, Claude and Python artifact identities remain **UNOBSERVED** until an admitted OCI build records them.
- Draft PR **#622** remains the single Python lock-generator compatibility lane (`pip-tools` 7.5.0 → 7.5.3 for the Python 3.13 generator). No canonical lock bytes are accepted yet and Docker is not yet on `--require-hashes`.
- The retained exact tmux execution closure `f8e4deebcb2f4b0b2904fddbcb0006600bc45c50` starts from source base `7b2a31c9defc76bead047823487c4384ee4bef3e` and differs by exactly the two #611 files above. It is an ephemeral execution closure, not a second permanent product lane.
- Dr.-Unterweger draft PR **#810** remains the single retained OCI/Vercel controller. Its hardened host-side source fetch does not forward `GITHUB_READ_TOKEN` into the Sandbox; guard↔runner identity drift now has a dedicated source regression. Vercel currently blocks the repaired trigger at deployment admission before build/`Sandbox.create`, so runtime credit is **0**.
- **New source falsifier:** the #810 runner fetches the private Research GitHub archive for `f8e4deeb…`, extracts it, and requires `the artefact/EntityOS` to exist before source verification/OCI build. That binary is intentionally not Git-tracked; `f8e4deeb…` differs from its base by only the two #611 files. Therefore, if the current runner were admitted unchanged, its first source stage is predicted to fail closed on the missing `EntityOS` file before OCI build. This is source-level falsification, not an observed Sandbox/test failure.
- Existing canonical recovery evidence already defines the correct repair on the **same #810 lane**: rebuild EntityOS inside an authorized isolated Vercel Sandbox from locked source head `79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c` / tree `d55d9d41f5a294a4a692cdee6fa46750652a390d`, require artifact SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586` and size `9181696`, then stage those exact bytes into the ClayVerse OCI build context. No exact GitHub Actions artifact is recoverable for that lock.

### Execution admission

- Vercel has previously demonstrated that the bridge can build and reach READY and that an older bounded Sandbox path can really execute, but the current repaired #810 trigger is deployment-rate-limited **before build and before `Sandbox.create`**. This is admission failure with zero runtime credit, not ClayVerse TEST_FAIL.
- Daytona remains owner-authorized **FREE_ONLY** fallback after Vercel pre-assertion failure. GitHub Actions run `32021241780` on head `e9a50a8325810410b837b1bae85212ef5710fa3f` failed before visible Step 1 on both the original job `95361186733` and a fresh rerun job `95367346696`; both expose `steps=[]`. No Daytona provider contact, credential use or Sandbox runtime occurred. Daytona provider/account availability remains unobserved and Daytona runtime credit is zero.
- Current testing remains isolated-sandbox-only. VPS, self-hosted VPS runners and production hosts are forbidden for current acceptance evidence. Together remains forbidden.

### Unusual-experiment accounting

- This `go` has only minute-precision shared trigger identity and no immutable shared request/turn id, so the atomic unusual-experiment lease fails closed: **0 valid unusual experiments executed**.
- The earlier 17:36 synthetic-second lease was invalid; its already-observed 277-case parser matrix remains only coordination-tainted bounded mechanism history with **0 valid experiment credit**.
- Separate trigger identities must not borrow one another's claims/results.

### Remaining acceptance path

First actually-started authorized isolated current-target run:

`same retained #810 lane → Sandbox.create → exact locked EntityOS source staging/rebuild → require locked EntityOS digest+size → stage exact binary into the f8e4deeb… ClayVerse source closure → build exact OCI image → capture image digest + APT/tmux + Claude/Python identities → run #611 idempotency/fail-closed + full transport-policy attestation on actual in-image tmux for gabriel/andreas → service --once + focused/adjacent regressions → #611 promotion decision → materialize/verify canonical Python hash lock on retained #622 lane → switch Docker to --require-hashes after acceptance → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`

Whole-product PASS requires that complete path. Source inspection, PRs, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 18:08 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; EntityOS staging falsifier retained and Daytona pre-step blocker independently reproduced**

- Preserved the single retained #810 controller and did **not** overwrite or fork its parallel worker lane.
- Retained the source falsifier showing the current #810 runner cannot obtain the untracked `the artefact/EntityOS` binary from the `f8e4deeb…` Git archive. The accepted repair obligation remains: rebuild the locked EntityOS source inside the authorized Sandbox, verify exact `32cd4587…` / `9181696`, then stage it into the OCI context.
- Corrected Daytona admission accounting using the GitHub Actions API: run `32021241780` exists. Its original job `95361186733` failed before Step 1 with `steps=[]`; a fresh ordinary rerun produced job `95367346696`, which independently failed the same way with `steps=[]`.
- Therefore the Daytona fallback is currently blocked at GitHub-hosted runner/pre-step admission **before provider contact**. This is not Daytona TEST_FAIL, not account/credit evidence and not ClayVerse runtime failure; runtime credit remains zero.
- Vercel remains rate-limited before the repaired #810 deployment build/`Sandbox.create`. The next useful discriminator is the same retained lane reaching an admitted isolated executor, after first repairing the EntityOS staging path already source-falsified above.
- No unusual experiment was executed. No VPS/self-hosted/production test path was used. Together remains forbidden.
- Durable receipts include `the artefact/receipts/2026-08-17_GO_1736_PR810_ENTITYOS_STAGE_FALSIFIER_GPT56SOL.json` and `the artefact/receipts/2026-08-17_GO_1807_DAYTONA_FALLBACK_RERUN_ADMISSION_GPT56SOL.json`.

### Cycle update rule

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** to the newest canonical reality; remove stale dynamic claims.
3. Update **Latest cycle delta** with concrete code/evidence/blocker movement. If canonical product bytes did not change, record `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, deployment READY, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same fusion cycle as the evidence it summarizes.
6. Rebind fast-moving feature branches immediately before execution; do not churn ancestry while no runner can start.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. GitHub-hosted jobs that fail before visible steps and Vercel deployments that never reach Sandbox execution provide zero semantic runtime credit.

Where an **authorized isolated** Python environment is available, source checks may use:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These do not substitute for the exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
