#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# One shared quota DB is mandatory across all ten parallel experiment processes.
export CLAY_FREE_PROVIDER_BUDGET_DB="${CLAY_FREE_PROVIDER_BUDGET_DB:-/artifacts/clay-entityos-swarm/provider_budget.sqlite3}"
export CLAY_TRIGGER1_RESEARCH_CONTINGENT="OWNER_AUTHORIZED_FREE_ONLY"
export CLAY_PROVIDER_CREDENTIAL_SCOPE="SWARM_CHILD_ONLY/v1"

# Supervisor-8.71 least-capability rule: this Trigger-1 orchestrator stays
# credential-blind. Each actual external-provider lane is wrapped independently
# by free_swarm_exec_with_vault.py inside run_trigger1_jspace_10x.py.
unset \
  GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY \
  MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY \
  NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY \
  OPENROUTER_API_KEY OPENROUTER_API_KEYS OPENROUTER2_API_KEY OPENROUTER3_API_KEY \
  TOGETHER_API_KEY TOGETHER_API_KEYS || true
while IFS= read -r name; do
  case "$name" in
    GROQ*KEY*|MISTRAL*KEY*|NVIDIA*KEY*|NGC*KEY*|OPENROUTER*KEY*|TOGETHER*KEY*) unset "$name" || true ;;
  esac
done < <(compgen -v)

exec python3 tools/run_trigger1_jspace_10x.py "$@"
