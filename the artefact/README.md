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
- The last bound execution closure is `f4c91d0129bbcd9d5e83bceb66b44c2e52f517ee` / tree `ff89be29ea79df92edd547b32abce9c7eceb34da`, based on `7b2a31c9defc76bead047823487c4384ee4bef3e`. Exact compare showed only the retained #611 terminal/focused-test deltas plus the then-current #622 execution-relevant Python-lock generator workflow/test deltas. It is an ephemeral execution closure, not a second permanent product lane. Because #622 subsequently absorbed #621 provenance, the next admitted PR810 execution-time rebind must use the then-current fused #622 bytes rather than silently testing the older partial closure.
- Dr.-Unterweger draft PR **#810** remains the single retained OCI/Vercel controller. Current head re-observed in this cycle is `1c96b76184d95a9357b24fde5dcb4c884319f19e`. Its fail-closed guard v3 precedes the current-target wrapper; the wrapper keeps only current Research-closure rebinding plus the dpkg interpolation fence, while the retained base runner owns the single locked EntityOS source/reproduction/staging path. Runtime credit remains **0**.
- Guard v3 is now bound to the complete retained EntityOS provenance: source head/tree, canonical source-archive digest, source-attestation digest, exact reproduced binary digest/size, exact-reproduction marker, two-private-archives/no-secret-forwarding marker, execution surface and zero unusual-experiment accounting. Regression `test_clayverse_current_oci_guard_runner_alignment.py` mirrors those bindings and keeps the guard fail-closed.
- The dpkg inventory controller hazard remains repaired on the same #810 lane: the wrapper fails closed unless exactly two unsafe `${Package}` / `${Version}` template occurrences are present, then rewrites them to default `dpkg-query -W` before generated-runner import. Supporting bounded mechanism evidence reproduced the former JavaScript interpolation failure; exact OCI execution remains unobserved.
- The earlier untracked-`EntityOS` source-stage falsifier is **SOURCE-REPAIRED, NOT RUNTIME-VERIFIED** on the same #810 lineage. The retained runner fetches and verifies locked EntityOS source head `79dc06eb4cba7aa3e3f4d1944bf3c2609ca0d21c` / tree `d55d9d41f5a294a4a692cdee6fa46750652a390d`, binds canonical source archive SHA-256 `4daf761a56164e43d332082e9357865a06d88035c54902f5adf99c204d773b8c` and source-attestation SHA-256 `4e08e2ea96420d1671451af09601509013018807bdcd5b321be5b6620a0a3ce4`, installs hash-locked EntityOS build dependencies, requires reproduced artifact SHA-256 `32cd4587adbb45292c964b45f5efd4c38873ccd578792557fbf909f1953e1586` and size `9181696`, then stages those exact bytes into the ClayVerse build context before source regression/OCI build. Credentials remain host-side; verified archive bytes cross into the disposable Sandbox.
- A transient duplicate EntityOS helper introduced during concurrent repair was deliberately collapsed back into the retained base runner. Current wrapper marker `RETAINED_RUNNER_SINGLE_PATH` plus the current guard/runner regressions fence against recreating a second staging implementation. This is controller source hardening only; it does not establish runtime PASS.
- Inclusion of #622 source bytes in an execution closure is not execution of its hash-lock generator. #622 gets runtime credit only when an authorized isolated executor actually performs the digest-pinned Python-base double compile, byte-identity check and complete binary `--require-hashes` wheelhouse verification; accepted lock bytes must still be materialized before Docker switches to `--require-hashes`.

### Execution admission

- Vercel deployment `dpl_6uKu7KsYM3XazJX4K4dwG7Rd5GqY` on PR810 commit `c98a68ff16794c086db7932744b9853ac53969fb` **did start a real Vercel build**: checkout and dependency installation completed and `npm run vercel-build` began. The current-target wrapper then failed closed with `CURRENT_TARGET_PATCH_IDENTITY_MISMATCH:private_archive_signature` before `Sandbox.create`. Therefore build admission was available at that instant, but no Sandbox, private-source staging, OCI build or ClayVerse semantic assertion ran; runtime credit is **0** and this is controller-preflight failure, not ClayVerse TEST_FAIL.
- The failure was traced to concurrent source progress: the retained base runner had already generalized the private-archive signature and incorporated the single locked EntityOS staging path while the transient wrapper still expected the predecessor signature. Fusion kept the newer base runner, removed the duplicate helper and rebound guard/tests to the single retained path.
- Fresh anti-entropy at this 19:20 cycle still shows **no Vercel deployment for current PR810 head `1c96b76184d95a9357b24fde5dcb4c884319f19e`**. Therefore exact-current-head Sandbox admission, exact source regression, OCI build/image identity and in-image tmux/service behavior remain **UNOBSERVED**.
- PR810 explicitly forbids retry-only commits to chase provider compute. This cycle therefore did **not** mint a no-op/retry commit or a parallel OCI/EntityOS staging lane merely to force another Preview.
- Daytona remains owner-authorized **FREE_ONLY** fallback after Vercel pre-assertion failure. GitHub Actions run `32021241780` on head `e9a50a8325810410b837b1bae85212ef5710fa3f` failed before visible Step 1 on both original job `95361186733` and fresh rerun job `95367346696`; both expose `steps=[]`. No Daytona provider contact, credential use or Sandbox runtime occurred. Daytona provider/account availability remains unobserved and Daytona runtime credit is zero.
- Current testing remains isolated-sandbox-only. VPS, self-hosted VPS runners and production hosts are forbidden for current acceptance evidence. Together remains forbidden.

### Unusual-experiment accounting

- This **19:20** `go` exposes only minute-precision shared trigger identity and no immutable shared request/turn id, so the atomic lease fails closed: **0 valid unusual experiments executed**. Deterministic anti-entropy, source inspection and provider-state verification are ordinary work and do not consume an unusual-experiment slot.
- The earlier 17:36 synthetic-second lease was invalid; its already-observed parser matrix remains only coordination-tainted bounded mechanism history with **0 valid experiment credit**.
- Separate trigger identities must not borrow one another's claims/results.

### Remaining acceptance path

First actually-started authorized isolated current-target run:

`same retained #810 lane at exact execution-time head → refresh/rebind once to then-current #611 + fused #622 bytes → fail-closed guard + current wrapper → Sandbox.create → verify exact Research + locked EntityOS source identities → reconstruct/attest/reproduce exact EntityOS bytes → stage exact EntityOS into ClayVerse source closure → full exact source regression → build exact OCI image → capture image digest + APT/tmux + Claude/Python identities → execute fenced dpkg inventory → run #611 idempotency/fail-closed + full transport-policy attestation on actual in-image tmux for gabriel/andreas → service --once + focused/adjacent regressions → execute/materialize/verify canonical #622 Python hash lock including selected-wheel digest manifest → switch Docker to --require-hashes after acceptance → rebuild/rebind exact image → #611 promotion decision → rejoin/revalidate #602 → packaged native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`

Whole-product PASS requires that complete path. Source inspection, PRs, Vercel build admission, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 19:20 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; current PR810 head rebound in durable anti-entropy, exact-current execution still unobserved**

- Rejoined canonical Research `main` at `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b` before this cycle's write and re-observed retained PR810 as Draft/mergeable at exact head `1c96b76184d95a9357b24fde5dcb4c884319f19e`.
- Re-read the live Vercel deployment set for `dr-unterweger`: newest observed PR810 deployment remains `dpl_6uKu7KsYM3XazJX4K4dwG7Rd5GqY` on older controller commit `c98a68ff16794c086db7932744b9853ac53969fb`; no deployment for `1c96b761…` is present.
- Re-read that deployment's actual build logs. Vercel completed checkout, installed dependencies and began `npm run vercel-build`, then the fail-closed wrapper raised `CURRENT_TARGET_PATCH_IDENTITY_MISMATCH:private_archive_signature` before `Sandbox.create`. Classification remains **controller pre-Sandbox failure, not ClayVerse TEST_FAIL**, with runtime credit **0**.
- Because the retained controller source has already repaired that drift and the PR explicitly forbids retry-only churn, this cycle did not fabricate another controller/product path just to trigger compute. The next discriminator remains a naturally admitted/current-head Vercel deployment or another authorized isolated executor with real provider contact.
- Exact-current Sandbox admission, Research/EntityOS source staging, EntityOS reproduction, full source regression, OCI build/image digest, dependency inventory, in-image #611 behavior and #622 canonical lock materialization are all still **UNOBSERVED**.
- No unusual experiment was executed because the shared trigger identity is minute-precision only. No VPS/self-hosted/production test path was used. Together remains forbidden.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1920_PR810_CURRENT_HEAD_ANTI_ENTROPY_GPT56SOL.json`.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

1. Refresh current `main`, canonical artefact state, relevant receipts and observed execution evidence.
2. Rewrite **Current state** to the newest canonical reality; remove stale dynamic claims.
3. Update **Latest cycle delta** with concrete code/evidence/blocker movement. If canonical product bytes did not change, record `NO_CHANGE` and why.
4. Never promote source inspection, a PR, CI configuration, Vercel build admission, deployment READY, component evidence or historical evidence into whole-product PASS.
5. Persist the README update in the same fusion cycle as the evidence it summarizes.
6. Rebind fast-moving feature branches immediately before execution; do not churn ancestry while no runner can start.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for multiple bounded source/components, but **whole-product PASS is not claimed**. GitHub-hosted jobs that fail before visible steps and Vercel controller failures that never reach Sandbox execution provide zero semantic ClayVerse runtime credit.

Where an **authorized isolated** Python environment is available, source checks may use:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These do not substitute for the exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
