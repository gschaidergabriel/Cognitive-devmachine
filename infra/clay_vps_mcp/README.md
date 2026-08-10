# Clay VPS MCP

Persistent non-destructive control and observability substrate for the Frank v0.1 VPS target.

## Components

- `clay-vps-mcp` — authenticated Streamable-HTTP MCP at `/mcp` (default localhost `:8765`).
- `clay-vps-history` — append-only local Git ledger at `/srv/clay-history` for material build/run/deploy effects.
- `clay-frank-telemetry` — localhost-only structured telemetry ingest at `:8766/v1/events`.
- `clay-telemetry-query` — surgical indexed/FTS/JSON/state-timeline query CLI used through controlled MCP command execution.
- `clay-unifieddb-backup` — consistent SQLite online snapshots, integrity manifests, tiered retention and recovery candidates.
- `unifieddb-backup.timer` — recurring 15-minute snapshots.

## Target invariant

Frank v0.1 target host is the persistent VPS. Andreas' PC is not a v0.1 release/acceptance target. All other Clay/Frank programme semantics remain unchanged.

## Storage

Telemetry has an explicit default total budget of 10 GiB, with SQLite main DB limited below that and a bounded WAL. Pressure cleanup drops oldest low-retention classes before causal-state/recovery/P0-P1 evidence. Large model/binary artifacts are referenced by SHA-256 rather than copied into Git history.

UnifiedDB backups use a separate bounded retention budget (default 50 GiB) and never overwrite the live DB automatically.

## Secrets

The following are independent secrets and are never committed:

- `CLAY_MCP_TOKEN`
- `FRANK_TELEMETRY_INGEST_TOKEN`
- `FRANK_API_TOKEN`

## Install

From a checked-out release on the VPS:

```bash
sudo bash infra/clay_vps_mcp/deploy/install.sh
```

The installer is release-versioned: prior MCP releases remain under `/opt/clay-vps-mcp/releases`, while `/opt/clay-vps-mcp/current` switches atomically to the new release.

## Telemetry examples

```bash
clay-telemetry-query stats
clay-telemetry-query query --module gwt --category STATE_DELTA --episode-id ep-123 --limit 100
clay-telemetry-query query --fts 'reentry' --build-id build-abc
clay-telemetry-query state-timeline --state-key workspace.focus --entity-id frank --episode-id ep-123
```

## Recovery invariant

Backup creation and recovery are separate. A recovery operation materializes and integrity-checks a new candidate database; it never silently replaces the live UnifiedDB.
