# GRID exchange — compact transport, not a second brain

This directory contains a **Git-friendly delta event format** and a local SQLite materialized view. It is **not** a replacement for the canonical GRID10 S1 lease/CAS state or TITAN/UnifiedDB.

## Components
- `grid_exchange.py`: stdlib-only event validation, SHA-256 content IDs, owner/host binding, revision+parent CAS, idempotent apply, local SQLite projection.
- Git carries **one immutable JSON packet per event** under a machine-scoped path; never commit the live SQLite WAL/database.
- Store indexes and larger memory in the existing UnifiedDB. Emit only IDs, changed fields, hashes, revisions, references and optional bounded summaries. **Near-token-neutral is a design goal, not zero token usage**: only model-visible summaries consume inference tokens.

## Command examples
```sh
printf '{"signal":"candidate","ref":"titan:123"}' > /tmp/packet.json
python3 grid_exchange/grid_exchange.py --db /var/lib/omega/grid-exchange.sqlite propose gabriel grid10 task-17 merge /tmp/packet.json --at 2026-10-29T01:00:00Z > /tmp/event.json
python3 grid_exchange/grid_exchange.py --db /var/lib/omega/grid-exchange.sqlite apply /tmp/event.json
python3 grid_exchange/grid_exchange.py --db /var/lib/omega/grid-exchange.sqlite get gabriel grid10 task-17
```

## Transport contract
- Existing GitHub repository: `gschaidergabriel/clay-global-research-entity`.
- Gabriel: `chatgpt-local-ai-core-node-control` -> `chatgpt-local-ai-core-node-results`; `ai-core-node/gabriel`.
- Andreas has a **distinct** branch pair and DB; cross-owner packets are rejected by binding.
- Existing `tools/omega_grid_relay.py` and `tools/omega_chatgpt_mcp.py` retain effect authority and receipt verification. This package only transports/cache-projects **data proposals**, not shell commands.
- For GRID integration: the canonical GRID coordinator must explicitly validate, authorize, and commit candidate updates through its existing CAS mechanism before they count as cognitive state.
- `delete_proposal` never deletes projected state. Keep secrets, raw private data, and tokens out of Git.
- Concurrency: one writer/coordinator per entity scope; git commits can conflict and need explicit retry/read; the SQLite materializer CAS rejects out-of-order events. Branch upload integration and live GRID hooks are **not yet deployed**.
