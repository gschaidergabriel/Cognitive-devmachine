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
- **#622** — single retained Python hash-lock generator lane. Current source head: `44ec5e109d40304b152c2fa05ba3e42e690f2820`. `SOURCE_LOCK.json` declares the `pip-tools==7.5.3` wheel plus seven exact Linux/Python-3.13 bootstrap wheels (`build`, `click`, `packaging`, `pip`, `pyproject-hooks`, `setuptools`, `wheel`) with wheel filenames and SHA-256 values. The workflow materializes that exact set, downloads it with `--only-binary=:all: --require-hashes`, verifies the wheelhouse, then installs offline with `--no-index --find-links=... --require-hashes`. Matching source-contract tests are present at the current head. This remains **SOURCE CANDIDATE / UNEXECUTED**: exact digest-pinned runtime compatibility/no-extra-download closure is not yet observed, no canonical product `requirements.lock.txt` is accepted, and Docker is not yet on product `--require-hashes`.
- **#602** — downstream managed native-Claude process attestation after successful in-image #611 validation.
- **#623** — single retained identity/readiness-drift fail-closed **SOURCE CANDIDATE**, current semantic head `3a3282ca5bc000b1bf9ecf64219b2367b04ef958`. Authenticated `IdentityRouter.resolve()` is read/validate-only: it requires the complete canonical-user contract (exactly Gabriel/Andreas, expected display names, `rights='equal'`), exactly one permanent session, canonical terminal name and live global generation; it does not silently repair request-time user/session drift. The same lane also requires exact canonical session-row cardinality in runtime readiness before projecting rows by user. Seven focused source regressions cover normal non-mutating resolution, deleted/duplicate/stale sessions, duplicate-session readiness, extra-user drift and equal-rights drift. All remain unexecuted; the PR stays DRAFT/unmerged.
- Dr.-Unterweger **#810** — the single retained OCI/Vercel controller. Current source-only head last observed: `78d92753d9442c66c3ffcff127c31faa98ffd622`. No parallel OCI controller or second EntityOS staging path is admitted.

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

That prepared closure is **stale for the next execution attempt** because #622 and source-only auth bytes advanced. It remains source-composition provenance with zero runtime credit. PR810 is intentionally not rebound merely to retrigger compute while the credential prerequisite is absent; refresh/rebind product-relevant bytes exactly once immediately before the next real run.

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

### Vercel execution-budget audit

A static audit of retained runner blob `1298ca8002704414f86cd0c036d44e5b32be2918` confirms that its 12 explicit sequential command budgets sum to exactly **2,490,000 ms**, matching the wrapper's declared retained-step ceiling. The current Sandbox timeout is **2,700,000 ms**, leaving a nominal **210,000 ms** for Sandbox/controller/source-transfer overhead.

This is internally coherent source-side but remains **UNEXECUTED**. Vercel's current Build Step maximum is also 45 minutes, so the build-time orchestration cannot assume more than that global envelope even where Sandbox plan limits may be longer. The first credential-capable exact run must capture elapsed/remaining-budget evidence across private source staging, Sandbox steps and cleanup. A build-timeout outcome must remain classified as execution-envelope/infrastructure evidence rather than a ClayVerse semantic test failure.

### Auth/identity architecture delta

The retained #623 lane now hardens three related post-startup drift classes at the externally reachable Clerk → session boundary without creating a second identity authority.

1. `IdentityRouter.resolve()` no longer calls bootstrap helper `ensure_session()` and therefore cannot recreate a missing permanent session during authentication. It validates one existing canonical session, terminal identity and live global generation.
2. `_runtime_ready()` requires the raw session-row cardinality to match the two canonical terminal bindings before user-keyed projection, so duplicate canonical sessions cannot be silently collapsed into a false READY state.
3. Request-time authentication now invokes read-only `assert_canonical_user_state()`, requiring UnifiedDB to contain exactly Gabriel and Andreas with expected display names and equal rights. An extra user or rights mutation fails closed and is left visible for diagnosis rather than being repaired by authentication.

The current semantic source head for these changes is `3a3282ca5bc000b1bf9ecf64219b2367b04ef958`. Source diff inspection confirms the helper centralizes the already-existing startup invariant rather than introducing a competing registry. Two new focused tests require extra-user drift and equal-rights drift to be rejected without mutation.

Execution evidence remains absent. Earlier #623 jobs ended before every step; run `32030737590` / job `95389934157` on the prior readiness semantic head completed `failure` with `steps=[]` and `runner_id=0`. At the latest refresh, no workflow run had yet been observed for semantic head `3a3282c…`. Therefore all new #623 behavior remains **SOURCE CANDIDATE / UNEXECUTED**, not PASS or TEST_FAIL.

### Browser/frontend evidence

**Current cycle browser test: BLOCKED / NOT REACHED.** The exact private ClayVerse source is blocked before staging, so no accepted current OCI image/service/browser endpoint exists to exercise. A controller deployment or unrelated READY page is not counted as a ClayVerse frontend test. The real browser gate remains Clerk sign-in/JWT → auth-first WebSocket → PTY/tmux → normal interactive Claude Code on the exact accepted image.

### Remaining acceptance path

After approved credential provisioning:

`final product-byte refresh → rebind single #810 controller to then-current main/#611/#622 and any deliberately admitted source-only auth delta → Sandbox.create → host-side exact private Research + EntityOS verification → verified archives into Sandbox → reproduce/attest locked EntityOS → full source regression → exact OCI build → image digest + dependency identities → deny-all network → in-image #611 tmux transport policy → hardened service --once → execute/verify #622 hashed offline generator bootstrap + materialize canonical product hash lock → rebuild with product --require-hashes only after accepted lock evidence → #611 promotion → #602 native-Claude attestation → startup/readiness → real Clerk JWT/browser WebSocket PTY → managed hook lifecycle → persistence/recovery → dual-session concurrency/global-generation fencing`.

#623 may enter that closure only after deliberate review and actually-started regression evidence; its source-only state must not inherit runtime credit.

Whole-product PASS requires the complete path. Source inspection, PRs, CI definitions, `Sandbox.create`, deployment READY, historical evidence or component PASS do not imply ClayVerse PASS.

### Unusual-experiment accounting

- This `go` has no safely shared immutable request/turn identity for an atomic unusual-experiment lease, so **0 valid unusual experiments** were executed.
- Source/provenance hardening, deterministic regression design and fail-closed architecture work are ordinary work.
- No VPS/self-hosted/production test path and no Together API were used.

### Latest cycle delta

**2026-08-17 19:42 +07:00 — `NO_CHANGE` canonical merged ClayVerse product/runtime bytes; #623 now also fences canonical-user/equal-rights drift source-side, primary OCI credential blocker unchanged**

- PR **#623** semantic head advanced to `3a3282ca5bc000b1bf9ecf64219b2367b04ef958` on the existing retained lane; no second identity/readiness authority was created.
- Request-time auth now revalidates the complete canonical UnifiedDB user contract: exactly Gabriel and Andreas, expected display names, and `rights='equal'`, in addition to the already-added permanent-session, terminal and global-generation checks.
- Two new source regressions require an extra user and an equal-rights mutation to fail closed **without authentication repairing the drift**.
- Static patch review confirms the validation is read-only and reuses the startup identity invariant. No workflow run was yet observed for `3a3282c…`, so this is **zero runtime credit / UNEXECUTED**.
- The prior readiness cardinality hardening remains on the same lane. Its last observed workflow run failed before all steps (`steps=[]`, `runner_id=0`), which remains execution-admission evidence rather than semantic TEST_FAIL.
- Durable receipt: `the artefact/receipts/2026-08-17_GO_1942_PR623_CANONICAL_USER_RIGHTS_DRIFT_GPT56SOL.json`.
- PR **#622** remains at `44ec5e109d40304b152c2fa05ba3e42e690f2820`, SOURCE CANDIDATE / UNEXECUTED.
- PR810 remains the single OCI controller. Strongest actually-started evidence still proves `Sandbox.create=PASS_CREATED`, then fail-closed missing host-side `GITHUB_READ_TOKEN` before private source fetch, with zero source/OCI runtime credit.
- Browser/frontend runtime testing remains **not reached** because the accepted private source/image/service path is blocked before staging.
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

Authorized isolated evidence exists for bounded components, but **whole-product PASS is not claimed**. The OCI path has repeatedly reached Sandbox admission and is currently blocked before private-source staging by the missing host-side read credential. #622 remains source-hardened but unexecuted. #623 now source-fences session duplication, stale generation and canonical-user/equal-rights drift at the authenticated boundary, plus duplicate-session readiness, but all current semantic regressions remain unexecuted. The next OCI execution closure must be rebound only when the credential prerequisite is satisfied, with build-budget telemetry included.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The build context is default-deny/allowlisted; persistent state/workspace live in scoped volumes. The admitted Compose profile runs non-root with a read-only root filesystem, `no-new-privileges` and dropped Linux capabilities. Supply-chain acceptance remains open until exact build identities and current APT/Python integrity gates are closed.
