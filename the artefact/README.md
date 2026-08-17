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
- Draft PR **#622** is the **single retained Python hash-lock generator lane**. Fusion commit `eb603ea054a307544de1b8281632a9daa8f830c2` retains generator-only `pip-tools==7.5.3` for the Python 3.13 product base and also absorbs former donor PR #621's deterministic selected-wheel SHA-256/basename provenance. PR #621 is closed **unmerged** as superseded, so no second resolver/generator authority remains. No canonical lock bytes are accepted yet and Docker is not yet on `--require-hashes`.
- Exact fused #622 source blobs are `.github/workflows/clayverse-python-lock-generator.yml` = `ad34476c0092b7e724240c927a7cb14858d1a8dc` and `the artefact/tests/test_python_lock_generator_source_binding.py` = `ed77f5c9446295fa973512ddf7e9d11ea3292010`. The fused workflow preserves exact product-base/requirements binding, double `pip-compile --generate-hashes`, byte-identity diff, binary `pip download --require-hashes`, lock digest/base64 evidence, and deterministic `WHEELHOUSE_SHA256_BEGIN/END` records ordered under `LC_ALL=C`. Supporting isolated source-slice regression is **5/5 PASS** under Python 3.13.5; this is mechanism/source evidence only and carries zero OCI/runtime credit.
- The latest retained execution closure is `f4c91d0129bbcd9d5e83bceb66b44c2e52f517ee` / tree `ff89be29ea79df92edd547b32abce9c7eceb34da`, based on `7b2a31c9defc76bead047823487c4384ee4bef3e`. Exact compare shows only the retained #611 terminal/focused-test deltas plus the then-current #622 execution-relevant Python-lock generator workflow/test deltas. It is an ephemeral execution closure, not a second permanent product lane. Because #622 has since absorbed #621 provenance, the next admitted PR810 execution-time rebind must use the then-current fused #622 bytes rather than silently testing the older partial closure.
- Dr.-Unterweger draft PR **#810** remains the single retained OCI/Vercel controller. Latest observed source lineage has continued on the same lane after the earlier `6971a38d…` state; exact execution-time head must be refreshed immediately before an admitted run. The current-target wrapper preserves the dpkg interpolation fence. Vercel remains blocked at deployment admission before build/`Sandbox.create`, so runtime credit is **0**.
- The dpkg inventory controller hazard remains repaired on the same #810 lane: the wrapper fails closed unless exactly two unsafe `${Package}` / `${Version}` template occurrences are present, then rewrites them to default `dpkg-query -W` before generated-runner import. Supporting bounded mechanism evidence reproduced the former JavaScript interpolation failure; exact Vercel/OCI execution remains unobserved.
- The earlier untracked-`EntityOS` source-stage falsifier is **SOURCE-REPAIRED, NOT RUNTIME-VERIFIED** on the same #810 lineage. The retained runner fetches and verifies locked EntityOS source head `79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c` / tree `d55d9d41f5a294a4a692cdee6fa46750652a390d`, reconstructs the canonical fixed-mtime source archive and attestation, installs hash-locked EntityOS build dependencies, requires reproduced artifact SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586` and size `9181696`, then stages those exact bytes into the ClayVerse build context before source regression/OCI build. Credentials remain host-side; verified archive bytes cross into the disposable Sandbox.
- Follow-on #810 source hardening additionally factors/strengthens the exact EntityOS staging helper: hash-checked build wheels, build-distribution-set verification, canonical fixed-mtime archive attestation and normalized package-name comparison remain fail-closed. This is controller source hardening only; it does not create current runtime credit or a second product authority.
- Inclusion of #622 source bytes in an execution closure is not execution of its hash-lock generator. #622 gets runtime credit only when an authorized isolated executor actually performs the digest-pinned Python-base double compile, byte-identity check and complete binary `--require-hashes` wheelhouse verification; accepted lock bytes must still be materialized before Docker switches to `--require-hashes`.

### Execution admission

- Vercel has previously demonstrated that the bridge can build and reach READY and that an older bounded Sandbox path can really execute, but current retained #810 execution is deployment-rate-limited **before build and before `Sandbox.create`**. This is admission failure with zero runtime credit, not ClayVerse TEST_FAIL.
- Daytona remains owner-authorized **FREE_ONLY** fallback after Vercel pre-assertion failure. GitHub Actions run `32021241780` on head `e9a50a8325810410b837b1bae85212ef5710fa3f` failed before visible Step 1 on both original job `95361186733` and fresh rerun job `95367346696`; both expose `steps=[]`. No Daytona provider contact, credential use or Sandbox runtime occurred. Daytona provider/account availability remains unobserved and Daytona runtime credit is zero.
- Current testing remains isolated-sandbox-only. VPS, self-hosted VPS runners and production hosts are forbidden for current acceptance evidence. Together remains forbidden.

### Unusual-experiment accounting

- This **18:01** `go` exposes only minute-precision shared trigger identity and no immutable shared request/turn id, so the atomic lease fails closed: **0 valid unusual experiments executed**. Controller/source falsifiers, fusion and deterministic regressions are ordinary work and do not consume an unusual-experiment slot.
- The earlier 17:36 synthetic-second lease was invalid; its already-observed parser matrix remains only coordination-tainted bounded mechanism history with **0 valid experiment credit**.
- Separate trigger identities must not borrow one another's claims/results.

### Remaining acceptance path

First actually-started authorized isolated current-target run:

`same retained #810 lane at exact execution-time head → rebind exact Research closure to then-current #611 + fused #622 bytes → Sandbox.create → verify exact Research + locked EntityOS source identities → reconstruct/attest locked EntityOS source → reproduce exact EntityOS bytes → stage exact EntityOS into ClayVerse source closure → full exact source regression → build exact OCI image → capture image digest + APT/tmux + Claude/Python identities → execute fenced dpkg inventory → run #611 idempotency/fail-closed + full transport-policy attestation on actual in-image tmux for gabriel/andreas → service --once + focused/adjacent regressions → execute/materialize/verify canonical #622 Python hash lock including selected-wheel digest manifest → switch Docker to --require-hashes after acceptance → rebuild/rebind exact image → #611 promotion decision → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`

Whole-product PASS requires that complete path. Source inspection, PRs, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 18:01 +07:00 trigger, fused through current evidence — `NO_CHANGE` canonical ClayVerse product/runtime bytes; #621/#622 duplicate Python-lock lanes collapsed, controller source repairs retained, provider admission remains blocking**

- Refreshed current GitHub/Vercel state instead of trusting the bootstrap cache and preserved the single retained #810 execution lane.
- Collapsed overlapping Python-lock drafts: PR **#621** is closed unmerged after its selected-wheel provenance contract was fused into retained draft **#622** at `eb603ea054a307544de1b8281632a9daa8f830c2`. No second resolver path survives.
- Verified the exact fused #622 workflow/test blobs on GitHub (`ad34476c…` / `ed77f5c…`) and ran the focused source contract in an isolated Python 3.13.5 slice: **5/5 PASS**. GitHub Actions currently shows no PR workflow run for that head, so authorized runner/runtime credit remains zero.
- Live-reentered the fusion into retained Dr.-Unterweger PR #810 via route comment `5315286878`: the next admitted execution-time closure must adopt the fused #622 bytes rather than the older partial generator candidate. This is coordination only, not runtime evidence.
- Preserved and incorporated the dpkg JavaScript-template interpolation falsifier and same-lane repair. Current wrapper keeps its fail-closed source fence.
- The earlier EntityOS-staging falsifier is source-repaired on the same #810 lineage: locked source reconstruction, source-attestation verification, hash-locked build dependencies, exact artifact digest/size enforcement and staging are encoded before OCI build. None has established exact current runtime PASS because provider admission remains blocked.
- Daytona fallback evidence remains pre-Step-1/pre-provider-contact with zero runtime credit; it did not provide an executable fallback for this cycle.
- No `requirements.lock.txt` was fabricated; Docker was not prematurely switched to `--require-hashes`. No unusual experiment was executed. No VPS/self-hosted/production test path was used. Together remains forbidden.
- Durable Python-lane evidence: retained PR #622 head `eb603ea054a307544de1b8281632a9daa8f830c2`, closed donor PR #621, and `the artefact/receipts/2026-08-17_GO_1801_PYTHON_LOCK_LANE_FUSION_GPT56SOL.json` on the retained branch.
- Whole-product acceptance remains **IN_PROGRESS**. Current executable frontier is admission to an authorized isolated executor for the exact execution-time #810 head, followed by measured EntityOS reconstruction → exact source regression → OCI build/runtime → #622 lock materialization.

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
