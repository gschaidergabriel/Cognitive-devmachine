# the artefact — ClayVerse single-container candidate

This is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

**Refresh this state in every product-convergent cycle. A stale README means the cycle is incomplete; detailed evidence remains in Git history and bounded receipts.**

### Current product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority. ClayGraph is derived/rebuildable only. MicroClay changes retrieval/accessibility only, never truth, identity, privacy or effect authority.
- Canonical user path: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into the same central entity/global generation.
- Claude Code is runtime cognition, not durable memory/identity authority. Managed hooks bind turns to UnifiedDB.
- Effects remain fail-closed through ClayVerse MCP/EffectGate. Generic host `process.exec` is forbidden. EntityOS is an optional digest-bound internal execution/security substrate, not the product endpoint.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#611** — single retained tmux idempotent-reapply repair. Exact retained blobs: `c185009f8af84e1288747d8352645777a36b2053` + `b6bb645dd07645f21ca2e5574f8392c9f13beafc`.
- **#622** — single retained Python hash-lock generator lane. Current source head: `44ec5e109d40304b152c2fa05ba3e42e690f2820`. `SOURCE_LOCK.json` now declares the `pip-tools==7.5.3` wheel plus seven exact Linux/Python-3.13 bootstrap wheels (`build`, `click`, `packaging`, `pip`, `pyproject-hooks`, `setuptools`, `wheel`) with wheel filenames and SHA-256 values. The workflow materializes that exact set, downloads it with `--only-binary=:all: --require-hashes`, verifies the wheelhouse, then installs offline with `--no-index --find-links=... --require-hashes`. Matching source-contract tests are present at the current head. This remains **SOURCE CANDIDATE / UNEXECUTED**: exact digest-pinned runtime compatibility/no-extra-download closure is not yet observed, no canonical product `requirements.lock.txt` is accepted, and Docker is not yet on product `--require-hashes`.
- **#602** — downstream managed native-Claude process attestation after successful in-image #611 validation.
- **#623** — bounded identity/session-drift fail-closed **SOURCE CANDIDATE**, head `b519ee8b8f4ffa4fe35e7c921bbb314e877ac5a9`. Authenticated `IdentityRouter.resolve()` becomes read/validate-only: exactly one permanent session, canonical terminal name and live global generation; authentication no longer recreates a missing session. Four focused regressions cover normal non-mutating resolution, deleted session, duplicate rows and stale generation. It is unexecuted and remains DRAFT/unmerged.
- Dr.-Unterweger **#810** — the single retained OCI/Vercel controller. Current source-only head last observed before this README refresh: `78d92753d9442c66c3ffcff127c31faa98ffd622`. No parallel OCI controller or second EntityOS staging path is admitted.

### Current OCI execution identity

The strongest actually exercised closure remains:

- Research base at bind time: `f7eb4df7600b0f4de1a6381a04acf5d1057d8f9b`
- exercised closure: `5e5adce0591058608bbd7381ecf570a39b282f0d`
- exercised tree: `1e02285d77b08e6edd86f9017d0ceac5db262cf2`

It is authoritative only for the already-observed Sandbox-admission/credential result and is stale for future compute because retained product bytes moved.

A later prepared execution closure exists on the already-retained closure lane:

- closure: `218b51cad87e3907d1dd45adc7998c736be23cdb`
- tree: `f16c87737cf74ef0703a1fc0a51fd99298450cd1`
- base `main` at construction: `ce60e3544caceda22ae349021c952328cf62692b`
- composition at construction: retained #611 blobs + then-current #622 supply-chain bytes with previous exercised closure ancestry preserved.

That prepared closure is now also **stale for the next execution attempt** because #622 advanced to `44ec5e10…`. It remains source-composition provenance with zero runtime credit. PR810 is intentionally not rebound merely to retrigger compute while the credential prerequisite is absent; refresh/rebind product-relevant bytes exactly once immediately before the next real run.

### Strongest executable evidence / blocker

The strongest actually-started bound run remains Vercel deployment **`dpl_7BkVnngPJUPiVyrqwFarGFZDevAG`** on PR810 controller **`2e5505983172e582a50f4f72bebd561bc650ff5a`**.

Observed:

1. Vercel cloned exact controller source and entered `npm run vercel-build`.
2. Guard v4 admitted the exact retained-runner binding, including Git blob `1298ca8002704414f86cd0c036d44e5b32be2918`.
3. Current-target patch v5 bound the exercised Research closure and a 2,700,000 ms Sandbox lifetime above the retained explicit-step timeout ceiling of 2,490,000 ms.
4. **`Sandbox.create` succeeded** (`sandbox_admission=PASS_CREATED`).
5. Execution then failed closed **before private Research/EntityOS source fetch** because `GITHUB_READ_TOKEN` was absent from the host Vercel Preview build environment: `PRIVATE_SOURCE_STAGE_BLOCKED:GITHUB_READ_TOKEN_MISSING`.
6. The disposable Sandbox stopped successfully. `source_runtime_credit=0`; `oci_runtime_credit=0`.

Classification: **SANDBOX_ADMISSION_PASS_PRIVATE_SOURCE_CREDENTIAL_BLOCK_REPLICATED**. This is a credential prerequisite, not ClayVerse TEST_FAIL.

The immediate external prerequisite is to provision **`GITHUB_READ_TOKEN` as a sensitive Vercel Preview credential for the retained PR810 branch**, without exposing its value and without forwarding it into the Sandbox. Read-only repository contents are sufficient for the private archive operation; only verified archive bytes may cross into the disposable Sandbox. The connected Vercel surface available to this cycle cannot set or recover the secret value.

### Auth/identity architecture delta

Source review found a separate fail-closed issue at the externally reachable Clerk → session boundary: `IdentityRouter.resolve()` called `UnifiedDB.ensure_session()`. Because `ensure_session()` is a bootstrap helper capable of creating a missing session, post-startup canonical-session drift could be silently repaired during authentication instead of rejected.

Draft **#623** changes only this request-time boundary: it reads and validates the existing UnifiedDB session, canonical terminal name and one global generation. It does not create a new state/identity authority and does not alter startup bootstrap semantics.

Counter-reality retained: `_runtime_ready()` currently projects session rows into a dict keyed by user before checking the canonical set, so duplicate user-session rows can be collapsed in readiness evaluation. #623 fences actual authenticated resolution, but readiness should later require exactly two session rows as well. No broad `terminal_gateway.py` edit was made without executable regression evidence.

The automatically-triggered GitHub workflow for #623 head `b519ee8…` ended before every step (`steps=[]`, `runner_id=0`). A deliberate regression rerun was then requested and accepted; rerun job **`95389126338`** also completed `failure` with **0 steps**. Therefore the four new tests remain **UNEXECUTED**. Both outcomes are runner/admission failures rather than semantic test failures, and #623 is not merged/promoted.

### Browser/frontend evidence

**Current cycle browser test: BLOCKED / NOT REACHED.** The exact private ClayVerse source is blocked before staging, so no accepted current OCI image/service/browser endpoint exists to exercise. A controller deployment or unrelated READY page is not counted as a ClayVerse frontend test. The real browser gate remains Clerk sign-in/JWT → auth-first WebSocket → PTY/tmux → normal interactive Claude Code on the exact accepted image.

### Remaining acceptance path

After approved credential provisioning:

`final product-byte refresh → rebind single #810 controller to then-current main/#611/#622 and any deliberately admitted source-only auth delta → Sandbox.create → host-side exact private Research + EntityOS verification → verified archives into Sandbox → reproduce/attest locked EntityOS → full source regression → exact OCI build → image digest + dependency identities → deny-all network → in-image #611 tmux transport policy → hardened service --once → execute/verify #622 hashed offline generator bootstrap + materialize canonical product hash lock → rebuild with product --require-hashes only after accepted lock evidence → #611 promotion → #602 native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

#623 may enter that closure only after deliberate review; its source-only state must not inherit runtime credit.

Whole-product PASS requires the complete path. Source inspection, PRs, CI definitions, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so **0 valid unusual experiments** were executed.
- Source composition, supply-chain/provenance hardening, credential verification, deterministic regression design and fail-closed architecture hardening are ordinary work.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:36 +07:00 — `NO_CHANGE` canonical ClayVerse product/runtime bytes; #622 generator bootstrap is hash-closed/offline source-side, primary OCI credential blocker unchanged**

- PR **#622** advanced on the existing retained lane to `44ec5e109d40304b152c2fa05ba3e42e690f2820`; no second resolver/dependency authority was created.
- `SOURCE_LOCK.json` now carries the exact `pip-tools==7.5.3` wheel plus seven exact bootstrap wheel identities/hashes for the declared Linux/Python-3.13 generator closure.
- The generator workflow now downloads that declared closure under `--require-hashes`, verifies every expected wheel/hash, then performs installation offline under `--no-index` + `--require-hashes` before deterministic double compilation.
- A matching source-contract test update is present at `44ec5e10…`; no pull-request workflow execution was observed for that head, so **zero runtime/acceptance credit** is awarded.
- Durable fusion receipt already re-entered by the coordinated parallel organ: `the artefact/receipts/2026-08-17_GO_1935_PYTHON_LOCK_OFFLINE_BOOTSTRAP_CLOSURE_FUSION_GPT56SOL.json`. It records the source fusion through workflow head `be61f7af…`; the subsequent `44ec5e10…` commit tightens the matching source-contract test and does not convert the result into runtime evidence.
- Prepared closure `218b51c…` / tree `f16c877…` is now stale for future compute because #622 advanced again; it must not be executed as if exact-current.
- PR810 remains the single OCI controller; strongest actually-started evidence still proves `Sandbox.create=PASS_CREATED` and then fail-closed missing host-side `GITHUB_READ_TOKEN` before private source fetch. No source/OCI runtime credit is awarded.
- Draft #623 remains unexecuted after two GitHub runner-admission failures with zero steps; it receives no semantic test credit.
- Browser/frontend runtime testing remains **not reached** because the accepted product source/image/service path is blocked before private source staging.
- No unusual experiment, VPS, self-hosted/production test or Together path was used.
- Whole-product acceptance remains **IN_PROGRESS**.

### Cycle update rule

1. Refresh current `main`, artefact state, overlapping PRs/receipts and exact execution evidence.
2. Rewrite this living state so stale dynamic claims are removed.
3. Record the concrete latest-cycle delta; use `NO_CHANGE` when canonical product bytes did not change.
4. Never promote source/component/controller/provider evidence into whole-product PASS.
5. Keep detailed evidence in Git history/receipts rather than making this README a competing state database.
6. Rebind fast-moving execution closures immediately before real compute; distinguish product-byte movement from documentation/receipt-only head churn and avoid retry-only or duplicate semantic paths.

## Architecture

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound internal EntityOS substrate. UnifiedDB remains the sole durable canonical cognition/state authority.

The retired custom chat API/headless `claude -p` path and a separate `consciousness_daemon` are not product runtime surfaces.

## Verification

Authorized isolated evidence exists for bounded components, but **whole-product PASS is not claimed**. The OCI path has repeatedly reached Sandbox admission and is currently blocked before private-source staging by the missing host-side read credential. The #622 generator-bootstrap trust root is now substantially narrower source-side but remains unexecuted; the next execution closure must be rebound only when the credential prerequisite is satisfied.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
