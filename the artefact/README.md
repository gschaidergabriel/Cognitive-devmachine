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
- The latest retained execution closure is `f4c91d0129bbcd9d5e83bceb66b44c2e52f517ee` / tree `ff89be29ea79df92edd547b32abce9c7eceb34da`, based on `7b2a31c9defc76bead047823487c4384ee4bef3e`. Exact compare shows only the retained #611 terminal/focused-test deltas plus the #622 execution-relevant Python-lock generator workflow/test deltas. It is an ephemeral execution closure, not a second permanent product lane.
- Dr.-Unterweger draft PR **#810** remains the single retained OCI/Vercel controller. Latest observed head is `f9d5fcb53167545110f9a2eb10c4747c77112333`; its current-target wrapper binds the existing exact-source runner onto `f4c91d…` and does not create a second runner semantics. Its hardened host-side source fetch does not forward `GITHUB_READ_TOKEN` into the Sandbox. Vercel currently blocks the target at deployment admission before build/`Sandbox.create`, so runtime credit is **0**.
- A second-order controller defect was found and repaired on that same #810 lane: the retained runner blob `5d56dd0d7a94289c96211ac467e2398adc958ff4` embeds dpkg `${Package}` / `${Version}` format tokens inside an outer JavaScript template with an unsafe two-backslash shape. A bounded isolated Node mechanism check reproduced `ReferenceError: Package is not defined`. Wrapper commit `5d11386bdb6a8c13d3567c341a717487f588dcad` now requires exactly two such source occurrences and rewrites them to default `dpkg-query -W` before importing the generated runner; regression correction head `f9d5fcb…` guards the generated tmux/ca-certificates commands. This is source/mechanism support only, not Vercel/OCI runtime evidence.
- **Source falsifier remains valid after the `f4c91d…` rebind:** the wrapper changes only Research SHA/tree before importing the same underlying #810 runner. That runner extracts the private Research GitHub archive and requires `the artefact/EntityOS` before source verification/OCI build. `EntityOS` is intentionally not Git-tracked, and the exact `7b2a31c9… → f4c91d…` compare contains only the #611/#622 paths above. If deployment were admitted unchanged, the source stage is therefore predicted to fail closed on the missing `EntityOS` file before OCI build. This is static/source falsification, not an observed Sandbox/test failure.
- Existing canonical recovery evidence defines the correct repair on the **same #810 lane**: rebuild EntityOS inside an authorized isolated Vercel Sandbox from locked source head `79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c` / tree `d55d9d41f5a294a4a692cdee6fa46750652a390d`, require artifact SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586` and size `9181696`, then stage those exact bytes into the `f4c91d…` ClayVerse build context. No exact GitHub Actions artifact is recoverable for that lock.

### Execution admission

- Vercel has previously demonstrated that the bridge can build and reach READY and that an older bounded Sandbox path can really execute, but current #810 execution is deployment-rate-limited **before build and before `Sandbox.create`**. This is admission failure with zero runtime credit, not ClayVerse TEST_FAIL.
- Daytona remains owner-authorized **FREE_ONLY** fallback after Vercel pre-assertion failure. GitHub Actions run `32021241780` on head `e9a50a8325810410b837b1bae85212ef5710fa3f` failed before visible Step 1 on both original job `95361186733` and fresh rerun job `95367346696`; both expose `steps=[]`. No Daytona provider contact, credential use or Sandbox runtime occurred. Daytona provider/account availability remains unobserved and Daytona runtime credit is zero.
- Current testing remains isolated-sandbox-only. VPS, self-hosted VPS runners and production hosts are forbidden for current acceptance evidence. Together remains forbidden.

### Unusual-experiment accounting

- This **18:01** `go` exposes only minute-precision shared trigger identity and no immutable shared request/turn id, so the atomic lease fails closed: **0 valid unusual experiments executed**. The dpkg inventory falsifier/repair is ordinary deterministic source/mechanism work and does not consume an unusual-experiment slot.
- The earlier 17:36 synthetic-second lease was invalid; its already-observed 277-case parser matrix remains only coordination-tainted bounded mechanism history with **0 valid experiment credit**.
- Separate trigger identities must not borrow one another's claims/results.

### Remaining acceptance path

First actually-started authorized isolated current-target run:

`same retained #810 lane → Sandbox.create → exact locked EntityOS source staging/rebuild → require locked EntityOS digest+size → stage exact binary into the f4c91d… ClayVerse source closure → build exact OCI image → capture image digest + APT/tmux + Claude/Python identities → execute the fenced dpkg inventory → run #611 idempotency/fail-closed + full transport-policy attestation on actual in-image tmux for gabriel/andreas → service --once + focused/adjacent regressions → #611 promotion decision → materialize/verify canonical Python hash lock on retained #622 lane → switch Docker to --require-hashes after acceptance → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`

Whole-product PASS requires that complete path. Source inspection, PRs, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 18:10 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; retained PR810 dependency-inventory controller hazard repaired and guarded while provider/runtime gates remain blocked**

- Refreshed shared reality after the current #810 target advanced to main + #611 + #622 execution closure `f4c91d…`; no duplicate OCI lane was created.
- Adversarial source review found that the retained runner's dpkg identity command used `${Package}` / `${Version}` inside an outer JavaScript template with escaping that still permits JavaScript interpolation. A bounded isolated mechanism check reproduced `ReferenceError: Package is not defined`, predicting a late controller failure after an otherwise successful OCI build.
- Repaired the **same retained #810 lane** at `5d11386bdb6a8c13d3567c341a717487f588dcad`: the current-target wrapper requires exactly two unsafe occurrences, fails closed on drift, and rewrites them to deterministic default `dpkg-query -W` package/version output before generated-runner import.
- Added a focused static regression at `f3fdbcba4c80cc4d80bf3fab9730421b17777061`; its first expected-string form over-escaped the generated shell quote and was immediately corrected at current #810 head `f9d5fcb53167545110f9a2eb10c4747c77112333`. Negative evidence is preserved rather than hidden.
- The higher-order source blocker is unchanged: current #810 still needs locked EntityOS reproduction/staging before OCI build can succeed. Vercel remains deployment-admission blocked and Daytona remains pre-provider-contact blocked; exact current OCI runtime credit is **0**.
- No unusual experiment was executed; no VPS/self-hosted/production test path was used; Together remains forbidden.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1810_PR810_DPKG_INVENTORY_INTERPOLATION_FENCE_GPT56SOL.json`.
- Whole-product acceptance remains **IN_PROGRESS**. Next useful executable discriminator is still the same retained #810 lane after the EntityOS staging repair at the first admitted authorized isolated provider run; the dependency-inventory fence removes one downstream false blocker before spending that execution opportunity.

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
