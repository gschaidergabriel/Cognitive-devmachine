# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence belongs in receipts/history; this file carries only the current product state.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority; ClayGraph is derived/rebuildable.
- Canonical path: Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Managed hooks bind turns to UnifiedDB; effects remain fail-closed through ClayVerse MCP/EffectGate.
- EntityOS is an **optional** digest-bound internal execution/security substrate, not the product endpoint and not required for the baseline container.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Retained convergence lanes

- **#611** tmux idempotent-reapply lane — head `2957e80228815ac266635981a55f22bc15dc9ed4`; exact in-image tmux remains the final promotion discriminator for that component.
- **#622** Python hash-lock generator — retained source candidate/unexecuted; no canonical `requirements.lock.txt` accepted yet.
- **#623** auth/identity/readiness/reauth drift lane — retained source/mechanism candidate; not exact OCI/runtime evidence.
- **#602** managed native-Claude process attestation — downstream of exact in-image #611.
- **#625** tokenless canonical baseline packaging — observed through receipt commit `dec0509e57cd0ef987cef05274931186912a8f9b` during this cycle; remains Draft/source candidate with bounded focused source evidence plus optional-EntityOS build-context, service/compose, manifest authority and digest-bound bridge component-runtime fences. The branch is moving concurrently and must be freshly rejoined before promotion.
- Dr.-Unterweger **#810** remains historical/retained controller evidence; its `GITHUB_READ_TOKEN` cross-private-repo staging path is not the preferred baseline route.

### Tokenless baseline decision

PR #625 removes the accidental requirement that baseline ClayVerse must fetch/stage private EntityOS bytes before it can build. Baseline may omit EntityOS while execution is disabled. If EntityOS is later embedded, explicit digest, source-tracked lock identity and locked size remain mandatory and mismatches fail closed. No GitHub credential is admitted into product source.

The optional staging directory is also constrained by the default-deny build context: only its tracked `.keep` and exact staged `EntityOS` artifact may be re-included; a recursive `build-assets/entityos/**` allowlist is rejected by regression.

The artifact manifest is now fenced to the same law on #625: EntityOS is optional for the baseline, omission is allowed only with `CLAYVERSE_ENABLE_ENTITYOS_EXEC=0`, and embedded EntityOS runtime acceptance is conditional on deliberate admission rather than an unconditional whole-product prerequisite.

### Testing policy — continue without waiting for Vercel

The missing direct Vercel Git-project connection is **not a development blocker**. It is deferred to the final exact OCI acceptance gate.

Until that final gate is available, every product-convergent cycle must maximize all other independent evidence layers defined in `the artefact/TESTING_STRATEGY.md`, including as applicable:

- static/source integrity and schema/authority checks;
- focused unit and cross-module contract suites;
- negative/fail-closed cases;
- deterministic adversarial/mutation regressions;
- persistence, crash/restart and idempotency tests;
- dual-user concurrency, race/order and generation fencing;
- bounded fuzz/property/state-machine testing with reproducible seeds;
- supply-chain hash, offline-install and reproducibility checks;
- real component runtime tests on any authorized disposable execution surface available;
- multi-component integration simulations for Clerk/JWT, WebSocket PTY, hooks, UnifiedDB and EffectGate;
- bounded timeout/cancellation/dependency/failure injection;
- widest relevant adjacent regression suite after each repair.

Missing one runner must never suppress tests that can execute independently. Mock/simulated/component evidence remains explicitly bounded and cannot imply whole-product PASS.

### Current execution boundary

Fresh Vercel connector inspection in this cycle exposes documentation/project tooling but no direct Sandbox start/exec surface for this repo; no project is directly connected to `gschaidergabriel/clay-global-research-entity`.

This state remains classified as:

**`FINAL_OCI_GATE_DEFERRED_VERCEL_PROJECT_NOT_CONNECTED`**

It is **not** a blocker for ongoing source/product convergence. The project should continue closing #625/#611/#622/#623/#602 and every independently executable test layer rather than waiting for Vercel setup.

### Working sequence before final OCI

`tokenless #625 source convergence → maximum static/unit/contract/negative/adversarial/property/restart/concurrency/reproducibility/integration evidence → deliberately rejoin and harden #611/#622/#623 → #602 managed native-Claude source/component closure → Clerk/PTY/hooks/persistence/recovery/concurrency simulations and disposable component runtimes wherever available → repeat regression fan-out after each change`.

### Final deferred exact execution sequence

When an authorized isolated OCI/Sandbox route becomes available:

`fresh canonical source → exact image build/digest → resolved dependency identities → actual build-context membership → baseline no-EntityOS build → optional digest-bound EntityOS negative/positive gates → deny network as required → exact in-image #611 → accepted #622 lock and --require-hashes rebuild → #602 packaged native Claude → UnifiedDB/ClayGraph → real Clerk JWT/browser WebSocket PTY → managed hooks/EffectGate → persistence/restart/recovery → dual-user concurrency/global-generation fencing → whole-product acceptance`.

Whole-product PASS requires this exact closure. Source inspection, static tests, mocks, component runtime PASS, deployment READY, Sandbox creation or historical evidence do not imply ClayVerse PASS.

### Latest cycle delta

**2026-08-17 21:01 +07:00 — #625 tokenless baseline was adversarially narrowed, its product/runtime optional-EntityOS contract was aligned, and bounded component-runtime evidence was added; no product-code promotion to `main` and no OCI PASS.**

- parallel #625 review found a supply-chain boundary defect: recursive `!build-assets/entityos/**` could admit arbitrary sibling bytes into the OCI build context;
- #625 was repaired to allow only `build-assets/entityos/.keep` and exact `build-assets/entityos/EntityOS`, with regression coverage forbidding restoration of the recursive wildcard;
- a separate authority drift was found and repaired: Dockerfile/README made EntityOS optional for the baseline while `manifest.json` still stated staged bytes were mandatory and retained an unconditional final EntityOS runtime gate;
- repaired manifest blob `c89269e8dd65aa7dd173dcb53a248c1c88aa8d39` is now aligned with the optional-baseline law and fenced by source-contract tests;
- a second runtime-contract contradiction was found and repaired in the same #625 lane: tokenless packaging could omit EntityOS while normal `_entityos_config()` still required SHA/artifact; current service logic admits absence only with execution disabled and no unpinned bytes present, while execution-without-pin/unpinned-file/unpinned-symlink remain fail-closed;
- bounded focused source/service checks remain supporting evidence only; unrelated imports may be stubbed in the narrow mechanism reconstructions and do not earn packaged-service or OCI credit;
- this organ independently rebound exact `the artefact/clayverse/entityos_bridge.py` blob `3118cb6a6758ec1612a33ff3c6766c937d79d4ac` and executed the real bridge on an OpenAI isolated Linux container: sealed-memfd verify PASS, pinned `/bin/true` snapshot execution PASS, mutable-path byte replacement FAIL_CLOSED on digest mismatch, symlink substitution FAIL_CLOSED; **4/4 PASS**;
- component receipt: `the artefact/receipts/2026-08-17_GO_2101_PR625_ENTITYOS_MEMFD_COMPONENT_GPT56SOL.json` (receipt commit `dec0509e57cd0ef987cef05274931186912a8f9b`);
- this component result is explicitly below exact in-image/OCI/EffectGate acceptance; final container kernel/seccomp/memfd behavior remains an open discriminator;
- earlier parallel build-context/service/manifest receipts remain preserved in #625; no duplicate packaging/runtime lane was created;
- #625 continued moving concurrently during the cycle; do not force-rewrite or infer merge readiness from a stale head;
- direct Vercel Sandbox start/exec is still not exposed for the Research repo; final exact OCI gate remains deferred, not a development stop;
- unusual experiment: `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT` because no shared immutable request/turn ID and only minute-precision trigger time were available;
- no whole-product PASS claimed;
- no VPS/self-hosted/production test, Together API, paid/final training or secret persistence admitted.

## Architecture

Current canonical source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound EntityOS substrate. Draft convergence lanes may be ahead of `main` and are not promoted merely because lower-layer tests pass.

## Verification

Authorized bounded component evidence exists, but **whole-product PASS is not claimed**. Until the final exact OCI route is available, progress is measured by closing the broadest honest set of lower evidence layers, never by waiting on a single external runner.
