# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification plus a Clerk-authenticated web chat boundary, an ephemeral tool-less Claude Code cognition boundary, and a fail-closed inference-intent path into the canonical effect gate. Generic host `process.exec` is forbidden; the current external-effect candidate is a SHA-256-pinned internal EntityOS bridge. EntityOS is an internal substrate candidate, not the product endpoint.

`consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised individual source mechanisms, but **whole-product PASS is not claimed**. The exact current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk-instance verification, authenticated Claude Code runtime verification, accepted external-effect substrate binding, and restart/recovery validation.

The GitHub Actions OCI gate is currently manual because GitHub-hosted runners are blocked before job start by account billing/spending state; its workflow remains available as `.github/workflows/clayverse-artefact-ci.yml`.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. Persistent data is explicitly externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
