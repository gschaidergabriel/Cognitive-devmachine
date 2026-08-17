# the artefact — ClayVerse single-container candidate

This directory is the canonical product workspace for the current ClayVerse endpoint: **one OCI/Docker-compatible container image** containing one persistent central ClayVerse entity.

Current source implements the UnifiedDB/ClayGraph continuity core, equal-rights Gabriel/Andreas identity routing, bounded workspace/causal re-entry, Clerk JWT verification, and a Clerk-authenticated browser PTY surface backed by two durable interactive Claude Code terminal perspectives. Claude Code built-in tools are disabled in those product sessions; the ClayVerse MCP bridge owns admitted state/context and effects. The runtime contract requires every human prompt to pass through `begin_turn` and `complete_turn`, with UnifiedDB remaining the durable context/memory authority. Generic host `process.exec` is forbidden; the current external-effect candidate is a SHA-256-pinned internal EntityOS bridge. EntityOS is an internal substrate candidate, not the product endpoint.

`consciousness_daemon` is not part of the target architecture.

## Verification

Focused isolated tests have exercised individual source mechanisms, but **whole-product PASS is not claimed**. The exact current head still requires a full authorized isolated test run, exact OCI build/runtime receipt, real Clerk-instance verification, authenticated permanent Claude Code terminal verification, MCP turn/state/effect round-trip verification, accepted embedded EntityOS runtime evidence, and restart/recovery validation.

The GitHub Actions gates are not current runtime evidence while GitHub-hosted jobs are blocked before execution by the repository account billing/spending state.

## Local isolated source checks

Where an authorized isolated Python environment is available:

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

These source checks do not substitute for an exact container build/runtime gate.

## Container source

`Dockerfile` + `compose.yaml` define the single runtime container. The default-deny Docker build context admits only consumed product inputs, including the runtime Claude contract and the digest-bound staged EntityOS artifact. Persistent ClayVerse state and workspace are explicitly externalized as scoped volumes, while the application image runs non-root with a read-only root filesystem in Compose, `no-new-privileges`, and dropped Linux capabilities.
