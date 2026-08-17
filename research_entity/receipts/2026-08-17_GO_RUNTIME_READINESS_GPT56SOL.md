# GO Runtime Readiness fusion receipt — 2026-08-17

Trigger: `go`
Organ: GPT-5.6 Sol temporary Clay organ
Program: ClayVerse single-container
Stage: CLAYVERSE_ARTIFACT

## Authority reset

The uploaded 2026-08-16 fast bootstrap remained useful as a cache only, but current repository authority supersedes its one-file EntityOS endpoint. The active release endpoint for this cycle is the one OCI/Docker-compatible ClayVerse container. EntityOS remains optional internal substrate only.

## Observed gap

At the start of this lane, `the artefact/Dockerfile` used `/healthz` as Docker `HEALTHCHECK`, while `clayverse/terminal_gateway.py` returned a constant HTTP 200 health payload without consulting canonical UnifiedDB state.

Competing interpretations:

- H0: `/healthz` is intentionally shallow liveness and therefore should remain constant.
- H1: using that same shallow endpoint as Docker health creates a false-green product signal when the canonical state spine is unavailable.

The selected repair preserved H0's useful liveness contract while removing H1's false-green Docker-health consequence.

## One bounded unusual experiment

`HEALTHZ_FALSE_GREEN_CANONICAL_STATE_LOSS` was the single unusual experiment in this worker's `go` lane.

The pre-fix health handler was exercised with the canonical state dependency deliberately unavailable in the bounded harness. It still returned HTTP 200 / `status=ok`, supporting the false-green hypothesis for Docker health. Subsequent runs in this lane were regression-only and did not introduce a second unusual intervention.

## Repair

PR #363 was fused and merged into canonical `main` as merge commit:

`e24ed8d21986659fc4eea0618d61146c617ab8de`

The repair:

1. preserves `/healthz` as shallow liveness;
2. adds `/readyz` as a read-only canonical runtime-readiness probe;
3. checks only minimum UnifiedDB invariants required by the terminal surface: schema version, live entity generation, both canonical users, and both canonical terminal sessions;
4. fails closed with HTTP 503 when those invariants cannot be read or do not match;
5. performs no rebuild, checkpoint, generation advance, terminal startup, external effect, or network operation;
6. binds Docker `HEALTHCHECK` to `/readyz` rather than `/healthz`;
7. adds regressions for a closed DB and an incompatible schema marker.

## Live fusion with parallel work

While this branch was active, canonical `main` independently landed the FastAPI WebSocket injection repair that moved `WebSocket` and `WebSocketDisconnect` to module scope. The readiness branch was reset onto that newer canonical state and the readiness patch was reapplied rather than overwriting it.

The fused gateway Git blob is:

`86f518fc0116d1f5e34841b0e70456b347d72694`

A later current-main re-entry check confirmed that exact blob remains canonical and the Dockerfile still points to `/readyz`.

## Scoped executable regression

The exact fused gateway blob was reconstructed and Git-blob verified inside an isolated bounded container harness.

Observed regression result:

- readiness before canonical DB loss: HTTP 200;
- readiness after closing the canonical DB connection: HTTP 503;
- liveness after DB loss remains HTTP 200 by design;
- FastAPI WebSocket endpoint annotation remains resolved as `WebSocket` after fusion.

An earlier harness attempt failed because the harness treated a FastAPI `Mount` route as though every route had an `endpoint` attribute. That was retained as a harness-negative result, corrected, and did not change the product patch.

This is scoped component evidence only. It is not a full OCI/ClayVerse acceptance result and is not a substitute for a real Vercel Sandbox run.

## Current empirical frontier

A separate canonical receipt has already prepared the infrastructure repair for the ClayVerse Docker-in-Vercel-Sandbox gate in `gschaidergabriel/Dr.-Unterweger` commit:

`73ed538995b8427e14f6c64cffec9622d887613f`

That repaired revision is currently unexecuted because the Vercel Git status reports deployment rate limiting and explicitly says to retry in 24 hours. Repeated deployment attempts are therefore not useful while that limiter remains the active discriminator.

## Next exact step

When Vercel accepts another preview build:

1. execute the already-prepared Docker-in-Sandbox repair once;
2. if Docker provisioning/build/run succeeds, promote only that infrastructure result;
3. restage the exact then-current research `main` and `the artefact/` tree;
4. run the coordinated Vercel Sandbox suite including full artifact tests, OCI build/run, `/readyz` container-health behavior, restart continuity, real terminal/browser/auth gates available at scope, and two-user contention/fencing gates;
5. bind exact source SHA/tree, image identity/digest, commands, exit codes, observations, failures and Sandbox stop receipt;
6. never generalize predecessor evidence to a later head.

Outcome: the canonical container health signal now fails closed on loss of its minimum authoritative state spine, while shallow liveness remains separately observable. Whole ClayVerse container acceptance remains in progress and empirically blocked on the current Vercel build-rate-limit discriminator.
