#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"

load_secret_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

has_provider_key() {
  [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}" ]]
}

while (( $(date +%s) < DEADLINE )); do
  load_secret_file /run/secrets/clay_provider.env
  load_secret_file /artifacts/.clay_provider.env
  load_secret_file /cache/clay_provider.env
  load_secret_file /workspace/.clay_provider.env

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - <<PY > "$STATE_DIR/SUPERVISOR.json.tmp"
import json,os,datetime
providers={
 'groq': bool(os.getenv('GROQ_API_KEY') or os.getenv('GROQ_API_KEYS')),
 'mistral': bool(os.getenv('MISTRAL_API_KEY') or os.getenv('MISTRAL_API_KEYS')),
 'nvidia': bool(os.getenv('NVIDIA_API_KEY') or os.getenv('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY')),
}
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v1','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remaining_seconds':$REMAINING,'free_only_attested':str(os.getenv('CLAY_FREE_ONLY_ATTESTED','')).lower() in ('1','true','yes','on','attested'),'provider_credentials_present':providers},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if [[ "${CLAY_FREE_ONLY_ATTESTED:-}" =~ ^(1|true|TRUE|yes|YES|on|ON|attested)$ ]] && has_provider_key; then
    exec python3 tools/run_24h_entityos_swarm.py --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v1","state":"EXPIRED_WITHOUT_USABLE_FREE_ONLY_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
