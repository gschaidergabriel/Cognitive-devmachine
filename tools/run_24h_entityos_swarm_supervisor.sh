#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
STATE_DIR="${CLAY_SWARM_STATE_DIR:-/artifacts/clay-entityos-swarm}"; mkdir -p "$STATE_DIR"
START="$(date +%s)"; DEADLINE="$((START + 24*3600))"
ADMISSION_FILE="${CLAY_PROVIDER_ADMISSION_FILE:-}"

write_blocked() {
  local reason="$1"
  python3 - "$reason" >"$STATE_DIR/SUPERVISOR.json.tmp" <<'PY'
import datetime,json,sys
print(json.dumps({"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4","observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"state":"ADMISSION_BLOCKED_NO_SECRET_LOOKUP_NO_NETWORK","reason":sys.argv[1],"secret_lookup_count":0,"network_attempt_count":0},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
}

resolve_free() {
  [[ -n "$ADMISSION_FILE" ]] || return 3
  python3 "$ROOT/tools/free_swarm_provider_admission.py" --file "$ADMISSION_FILE" --list-free
}

load_provider_secrets() {
  local provider="$1"; shift
  local exports
  exports="$(python3 "$ROOT/tools/free_swarm_secret_loader.py" --admission-file "$ADMISSION_FILE" --provider "$provider" "$@")" || return $?
  eval "$exports"
}

# CRITICAL: resolve typed cost-class admission before any key env lookup or secret-file read.
if ! FREE_PROVIDERS="$(resolve_free 2>/dev/null)" || [[ -z "$FREE_PROVIDERS" ]]; then
  write_blocked "missing_invalid_or_no_effective_FREE_provider_admission"
  exit 3
fi

# Provider-specific secret files only. Legacy mixed secret bundles are deliberately not sourced.
while IFS= read -r provider; do
  case "$provider" in
    groq)
      args=(); [[ -n "${CLAY_GROQ_SECRET_FILE:-}" ]] && args+=(--file "$CLAY_GROQ_SECRET_FILE"); args+=(--file "/run/secrets/clay_groq.env" --file "$ROOT/research_entity/private/GROQ_API.env"); load_provider_secrets groq "${args[@]}" ;;
    mistral)
      args=(); [[ -n "${CLAY_MISTRAL_SECRET_FILE:-}" ]] && args+=(--file "$CLAY_MISTRAL_SECRET_FILE"); args+=(--file "/run/secrets/clay_mistral.env"); load_provider_secrets mistral "${args[@]}" ;;
    nvidia)
      args=(); [[ -n "${CLAY_NVIDIA_SECRET_FILE:-}" ]] && args+=(--file "$CLAY_NVIDIA_SECRET_FILE"); args+=(--file "/run/secrets/clay_nvidia.env"); load_provider_secrets nvidia "${args[@]}" ;;
  esac
done <<< "$FREE_PROVIDERS"

if [[ "${CLAY_SWARM_PREFLIGHT_ONLY:-0}" == "1" ]]; then
  python3 "$ROOT/tools/run_24h_entityos_swarm.py" --provider-admission-file "$ADMISSION_FILE" --inventory-only --timeout 0.01
  exit $?
fi

NOW="$(date +%s)"; REMAINING="$((DEADLINE-NOW))"; HOURS="$(python3 - <<PY
print(max(0.01,$REMAINING/3600.0))
PY
)"
exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --provider-admission-file "$ADMISSION_FILE" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
