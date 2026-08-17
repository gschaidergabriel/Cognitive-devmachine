# the artefact — ClayVerse candidate

This directory is the canonical reproducible ClayVerse product workspace.

The current candidate implements the central state/continuity/causal architecture and a hardened one-container source shape without using the live VPS. It is **not** a whole-system PASS yet because real Clerk verification, browser terminal/Claude Code integration, the selected EntityOS substrate, and an isolated OCI image build are still external gates.

## Local isolated verification

```bash
python -m pytest -q
PYTHONPATH=. CLAYVERSE_STATE_ROOT=/tmp/clayverse-state python -m clayverse.service --once
```

## Container source

`Dockerfile` + `compose.yaml` define one runtime container with external durable state at `/var/lib/clayverse`, non-root execution, no-new-privileges, and dropped capabilities.
