#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# One shared quota DB is mandatory across all ten parallel experiment processes.
export CLAY_FREE_PROVIDER_BUDGET_DB="${CLAY_FREE_PROVIDER_BUDGET_DB:-/artifacts/clay-entityos-swarm/provider_budget.sqlite3}"
export CLAY_TRIGGER1_RESEARCH_CONTINGENT="OWNER_AUTHORIZED_FREE_ONLY"

# Vault loader never prints secret values; children inherit admitted credentials.
exec python3 tools/free_swarm_exec_with_vault.py \
  python3 tools/run_trigger1_jspace_10x.py "$@"
