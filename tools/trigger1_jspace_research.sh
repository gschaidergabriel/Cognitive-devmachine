#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# One shared quota DB is mandatory across external-provider research processes.
export CLAY_FREE_PROVIDER_BUDGET_DB="${CLAY_FREE_PROVIDER_BUDGET_DB:-/artifacts/clay-entityos-swarm/provider_budget.sqlite3}"
export CLAY_TRIGGER1_RESEARCH_CONTINGENT="OWNER_AUTHORIZED_ZERO_COST"
export CLAY_PROVIDER_CREDENTIAL_SCOPE="SWARM_CHILD_ONLY/v1"
export CLAY_TRIGGER1_CONVERGENCE_DIRECTIVE="$ROOT/research_entity/continuity/OWNER_DIRECTIVE_2026-08-24_TRIGGER1_CONVERGENCE_V2.json"

# The Trigger-1 orchestrator and local primary path remain credential-blind.
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

# Trigger-1 first attempts the provider-independent exact local API path. The local
# PyTorch path is promoted only through the V3 scientific gate, which rejects a
# final-readout/LM-head-derived vector as circular plumbing evidence.
if [[ "${CLAY_TRIGGER1_LOCAL_FASTPATH:-1}" != "0" ]]; then
  if [[ -d /artifacts && -w /artifacts ]]; then
    TRIGGER1_ROOT="${CLAY_TRIGGER1_ARTIFACT_ROOT:-/artifacts/clay-entityos-trigger1}"
  else
    TRIGGER1_ROOT="${CLAY_TRIGGER1_ARTIFACT_ROOT:-${XDG_STATE_HOME:-${HOME:?}/.local/state}/clay-entityos-trigger1}"
  fi
  mkdir -p "$TRIGGER1_ROOT"
  LOCAL_DIR="$TRIGGER1_ROOT/local-fastpath-$(date -u +%Y%m%dT%H%M%SZ)-$$"
  mkdir -p "$LOCAL_DIR"

  set +e
  bash "$ROOT/tools/trigger1_local_qwen06_activation_api.sh" "$LOCAL_DIR" \
    >"$LOCAL_DIR/launcher.log" 2>&1
  local_rc=$?
  set -e

  export CLAY_TRIGGER1_LOCAL_FASTPATH_RESULT="$LOCAL_DIR/trigger1_local_activation_api_result.json"
  candidate="$LOCAL_DIR/trigger1_direct_steering_candidate.json"
  if [[ $local_rc -eq 0 && -s "$candidate" ]]; then
    python3 "$ROOT/tools/trigger1_jspace_promotion_gate_v3.py" --candidate "$candidate" \
      >"$LOCAL_DIR/promotion_gate.json"
    if python3 - "$LOCAL_DIR/promotion_gate.json" <<'PY'
import json, pathlib, sys
obj=json.loads(pathlib.Path(sys.argv[1]).read_text())
raise SystemExit(0 if obj.get('owner_trigger1_goal_credit_candidate') is True else 1)
PY
    then
      cat "$LOCAL_DIR/promotion_gate.json"
      exit 0
    fi
  fi
fi

# Local path did not yet satisfy the unchanged scientific goal. Continue immediately
# with research/repair slots; do not wait for a blocked dependency or ask the user.
exec python3 tools/run_trigger1_jspace_10x.py "$@"
