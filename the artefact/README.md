# the artefact — ClayVerse single-container candidate

Canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

## Living cycle status

Refresh this file in every product-convergent cycle. Detailed evidence stays in receipts/history; this file carries the newest observed shared state and concrete cycle delta.

### Product contract

- Program: **ClayVerse single-container**
- Stage: **CLAYVERSE_ARTIFACT**
- Acceptance: **IN_PROGRESS** — no whole-product PASS is claimed.
- UnifiedDB is the sole durable canonical cognition/state authority; ClayGraph is derived/rebuildable and MicroClay changes retrieval/accessibility only.
- Canonical UX remains Clerk-authenticated browser → auth-first WebSocket PTY → user-bound persistent tmux → normal interactive Claude Code CLI.
- Gabriel and Andreas are equal-rights perspectives into one central entity/global generation.
- Managed hooks bind turns to UnifiedDB; effects remain fail-closed through ClayVerse MCP/EffectGate.
- EntityOS is an **optional** digest-bound internal execution/security substrate, not the product endpoint and not a baseline-container prerequisite.
- Build/test/runtime validation remains authorized isolated-sandbox-only. VPS/self-hosted/production testing and Together are forbidden.

### Current convergence lanes

- **#625** is the retained tokenless baseline packaging lane. At the latest observed refresh its head had moved to `606f1297da915efb2581f9e013b6c54586874d21`; rebind again before executable claims. It keeps EntityOS optional, removes the stale duplicate OCI workflow, and still lacks exact Docker/OCI runtime evidence.
- **#622** is the single retained Python hash-lock generator lane. This branch is intentionally a focused supply-chain lane and must be fused/rebased with the current tokenless packaging reality before product promotion; branch-local older Docker/EntityOS bytes are not independent product authority.
- **#611** remains the retained tmux idempotent-reapply lane; exact in-image tmux is still required.
- **#602** remains downstream managed native-Claude process attestation.
- **#623** remains auth/identity/readiness/reauth source/mechanism work awaiting exact product-runtime evidence.

### Python supply-chain lane — current source contract

#622 now source-locks the complete declared Linux/Python-3.13 `pip-tools` bootstrap wheel set and uses a binary-only `--require-hashes` download followed by offline `--no-index` installation. The current declared set is `pip-tools==7.5.3`, `build==1.2.2.post1`, `click==8.3.3`, `packaging==24.2`, `pip==26.1.2`, `pyproject-hooks==1.2.0`, `setuptools==83.0.0`, and `wheel==0.46.2`.

The workflow also performs two independent `pip-compile --generate-hashes` runs against one stable output pathname before byte comparison, avoiding the former false reproducibility failure caused by different output filenames.

A new provenance fence now closes an additional source-authority gap: before the first candidate `docker run`, the workflow parses `SOURCE_LOCK.base_image`, validates its reference/digest shapes and requires exact equality with the Dockerfile first `FROM`. A missing, malformed or drifted source-lock base identity fails closed before candidate-image execution.

Current bound source identity at this lane is:

`python:3.13.14-slim-trixie@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91`.

Primary PyPI release metadata was independently rechecked for all eight declared bootstrap wheels in this cycle; filenames and SHA-256 values match `SOURCE_LOCK.json`. This is source verification only, not executable generator credit.

### Current execution boundary

The available OpenAI isolated component surface has Python but no Docker/Podman/Buildah/tmux and no working DNS/Internet egress. A direct hash-checked bootstrap-download attempt therefore stopped before PyPI resolution with DNS failure. This is **EXECUTION_ADMISSION_BLOCKED**, not package/hash TEST_FAIL.

The base-image provenance micro-falsifier passed five bounded cases: exact match accepted; digest drift, missing base identity, `@` reference injection and malformed digest all rejected. This is static/component mechanism evidence, not exact Python-3.13.14 container execution.

Vercel Sandbox itself is not categorically unavailable: the retained Dr.-Unterweger controller has historical/current bounded evidence reaching `Sandbox.create`, but its old cross-private-repository source-fetch route is blocked before Research source staging when the host read credential is absent. The tokenless #625 baseline must not reintroduce that credential requirement merely to satisfy the old controller shape.

### Latest cycle delta

**2026-08-17 21:18 +07:00 — #622 Python-lock provenance hardened; canonical product/runtime acceptance unchanged.**

- Rebound #622 to moving head `84f0f17b42b31bb64ad902e619dd4d26894dcead` and found that parallel work had already repaired the earlier bootstrap flaw: all eight generator wheels are now hash-checked and installed offline.
- Identified the remaining Dockerfile/SOURCE_LOCK semantic drift gap and repaired it in commits `50e9e37c2ced79f47807b802b0ce0ece82364747` and `cd967ed31a04bb4c3d98cd48083ef6c13fcb06e8`.
- Added a regression requiring the equality check to occur before `docker run`.
- Primary PyPI metadata confirms all eight current declared wheel filenames and SHA-256 values.
- Local bounded provenance falsifier: **5/5 mechanisms PASS**. Local bootstrap download: **EXECUTION_ADMISSION_BLOCKED** before package resolution because DNS/Internet is unavailable; no package/hash failure is claimed.
- Receipt: `the artefact/receipts/2026-08-17_GO_2118_PR622_BASE_IMAGE_PROVENANCE_FENCE_GPT56SOL.json`, committed as `bd916736f53541460806434bdb9d0a9eba1e78ed`.
- `requirements.lock.txt` was **not** fabricated or promoted; Docker product dependency install was **not** switched to `--require-hashes` without exact accepted generator output.
- GO unusual experiment remains `COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`; zero unusual experiments were executed because no immutable shared request/turn identifier is available.
- No VPS/self-hosted/production testing, Together API, paid/final training or secret persistence occurred.

### Next discriminator

At the first authorized source-bound Docker/OCI-capable isolated surface:

`fresh exact #625/#622 fusion identity → exact Python 3.13.14 digest-pinned base → bootstrap wheel download under --require-hashes → exact filenames/SHA verification → offline install → pip/pip-tools version assertions → stable-path double compile byte equality → product wheelhouse under --require-hashes → persist accepted requirements.lock.txt → switch product Docker install to --require-hashes → rebuild image/digest → continue #611/#602 and Clerk/PTY/hooks/effects/persistence/recovery/concurrency acceptance`.

Whole-product PASS requires the complete path. Source inspection, primary metadata, static regressions, component runtime, PR state, deployment READY or historical controller evidence do not imply ClayVerse PASS.

## Architecture

Current source direction implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas perspectives, Clerk JWT verification, browser WebSocket PTY, persistent user-bound tmux, normal interactive Claude Code, managed lifecycle hooks, bounded retrieval/workspace coordination, effect-only MCP/EffectGate, restart/recovery and optional digest-bound EntityOS substrate.
