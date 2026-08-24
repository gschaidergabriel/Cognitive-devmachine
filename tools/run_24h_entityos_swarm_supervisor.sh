#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
GATE="$ROOT/tools/free_swarm_admission_gate.py"
POLICY="$ROOT/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"

# No provider key value is read by this supervisor until the canonical typed
# admission gate resolves that exact provider to cost_class=FREE.
provider_is_admitted() {
  python3 "$GATE" --policy "$POLICY" --provider "$1" >/dev/null 2>&1
}

# Drop inherited provider secrets at every control-loop boundary. `unset`
# removes named variables without reading their values. A later provider may
# regain credentials only after a fresh exact typed FREE admission.
clear_provider_secret_env() {
  local name
  for name in \
    GROQ_API_KEY GROQ_API_KEYS MISTRAL_API_KEY MISTRAL_API_KEYS \
    NVIDIA_API_KEY NVIDIA_API_KEYS NGC_API_KEY NVIDIA_NIM_API_KEY; do
    unset "$name" || true
  done
  while IFS='=' read -r name _; do
    case "$name" in
      GROQ_API_KEY_*|MISTRAL_API_KEY_*|NVIDIA_API_KEY_*) unset "$name" || true ;;
    esac
  done < <(env)
}

provider_name_allowed() {
  local provider="$1" name="$2"
  case "$provider:$name" in
    groq:GROQ_API_KEY|groq:GROQ_API_KEYS|groq:GROQ_API_KEY_*) return 0 ;;
    mistral:MISTRAL_API_KEY|mistral:MISTRAL_API_KEYS|mistral:MISTRAL_API_KEY_*) return 0 ;;
    nvidia:NVIDIA_API_KEY|nvidia:NVIDIA_API_KEYS|nvidia:NVIDIA_API_KEY_*|nvidia:NGC_API_KEY|nvidia:NVIDIA_NIM_API_KEY) return 0 ;;
    *) return 1 ;;
  esac
}

# Provider secret files are provider-scoped by contract. Generic/mixed secret
# bundles are intentionally not loaded: they cannot prove that blocked-provider
# secrets remain unread. The parser accepts KEY=VALUE dotenv lines only and
# never evals/sources shell code.
load_provider_secret_file() {
  local provider="$1" f="$2" raw name value
  [[ -n "$f" && -r "$f" ]] || return 0
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    raw="${raw%$'\r'}"
    [[ -z "$raw" || "$raw" == \#* ]] && continue
    [[ "$raw" == export\ * ]] && raw="${raw#export }"
    [[ "$raw" == *=* ]] || continue
    name="${raw%%=*}"
    value="${raw#*=}"
    [[ "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    provider_name_allowed "$provider" "$name" || continue
    if [[ ${#value} -ge 2 ]]; then
      if [[ "$value" == \"*\" && "$value" == *\" ]]; then
        value="${value:1:${#value}-2}"
      elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
        value="${value:1:${#value}-2}"
      fi
    fi
    export "$name=$value"
  done < "$f"
}

load_admitted_provider_secrets() {
  local provider="$1" override=""
  provider_is_admitted "$provider" || return 0
  case "$provider" in
    groq)
      override="${CLAY_GROQ_SECRET_FILE:-}"
      load_provider_secret_file groq "$override"
      load_provider_secret_file groq /run/secrets/clay_groq.env
      load_provider_secret_file groq /artifacts/.clay_groq.env
      load_provider_secret_file groq /cache/clay_groq.env
      load_provider_secret_file groq "$ROOT/.clay_groq.env"
      load_provider_secret_file groq "$ROOT/research_entity/private/GROQ_API.env"
      ;;
    mistral)
      override="${CLAY_MISTRAL_SECRET_FILE:-}"
      load_provider_secret_file mistral "$override"
      load_provider_secret_file mistral /run/secrets/clay_mistral.env
      load_provider_secret_file mistral /artifacts/.clay_mistral.env
      load_provider_secret_file mistral /cache/clay_mistral.env
      load_provider_secret_file mistral "$ROOT/.clay_mistral.env"
      load_provider_secret_file mistral "$ROOT/research_entity/private/MISTRAL_API.env"
      ;;
    nvidia)
      override="${CLAY_NVIDIA_SECRET_FILE:-}"
      load_provider_secret_file nvidia "$override"
      load_provider_secret_file nvidia /run/secrets/clay_nvidia.env
      load_provider_secret_file nvidia /artifacts/.clay_nvidia.env
      load_provider_secret_file nvidia /cache/clay_nvidia.env
      load_provider_secret_file nvidia "$ROOT/.clay_nvidia.env"
      load_provider_secret_file nvidia "$ROOT/research_entity/private/NVIDIA_API.env"
      ;;
  esac
}

start_dashboard() {
  local evaluator="$ROOT/free swarm/evaluate.py"
  [[ -f "$evaluator" ]] || return 0
  if ! pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1; then
    # Start before admitted provider secrets are loaded so the dashboard does
    # not inherit credentials from this supervisor process.
    nohup python3 "$evaluator" \
      --repo "$ROOT" --artifacts "$STATE_DIR" \
      --watch --hours 24 --interval-seconds 60 --publish --publish-min-seconds 900 \
      >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/dashboard.pid"
  fi
}

write_supervisor_state() {
  local remaining="$1"
  python3 - "$POLICY" "$remaining" <<'PY' > "$STATE_DIR/SUPERVISOR.json.tmp"
import datetime, json, pathlib, sys
policy_path=pathlib.Path(sys.argv[1])
remaining=int(sys.argv[2])
try:
    policy=json.loads(policy_path.read_text(encoding='utf-8'))
except Exception:
    policy={}
free=policy.get('free_only') if isinstance(policy,dict) else None
admissions=free.get('provider_admissions') if isinstance(free,dict) else None
summary={}
for provider in ('groq','mistral','nvidia'):
    item=admissions.get(provider) if isinstance(admissions,dict) else None
    if isinstance(item,dict):
        summary[provider]={
            'cost_class':str(item.get('cost_class','UNKNOWN')).upper(),
            'admission_id':str(item.get('admission_id','')),
            'authority_epoch':str(item.get('authority_epoch','')),
            'secret_lookup_allowed':item.get('secret_lookup_allowed') is True,
            'network_allowed':item.get('network_allowed') is True,
        }
    else:
        summary[provider]={'cost_class':'UNKNOWN','admission_id':'','authority_epoch':'','secret_lookup_allowed':False,'network_allowed':False}
print(json.dumps({
    'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v4',
    'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'remaining_seconds':remaining,
    'policy_epoch':str(policy.get('schema_version','')) if isinstance(policy,dict) else '',
    'provider_admissions':summary,
    'provider_credentials':'UNREAD_UNLESS_EXACT_PROVIDER_ADMISSION_IS_FREE',
    'provider_network':'BLOCKED_UNLESS_EXACT_PROVIDER_ADMISSION_IS_FREE',
    'dashboard_watch':True,
},indent=2,sort_keys=True))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
}

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  clear_provider_secret_env
  load_admitted_provider_secrets groq
  load_admitted_provider_secrets mistral
  load_admitted_provider_secrets nvidia

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  write_supervisor_state "$REMAINING"

  if python3 "$GATE" --policy "$POLICY" --list-admitted | grep -q '"providers": \[[^]]'; then
    HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"
    set +e
    python3 "$ROOT/tools/run_24h_entityos_swarm.py" \
      --hours "$HOURS" \
      --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
    RC=$?
    set -e
    case "$RC" in
      0) exit 0 ;;
      4) ;; # Exact FREE admission exists but no provider credentials are currently present.
      *) printf 'swarm driver exited rc=%s; fail-closed supervisor will retry after policy/credential refresh\n' "$RC" >&2 ;;
    esac
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4","state":"EXPIRED_WITHOUT_EXECUTABLE_TYPED_FREE_PROVIDER_ADMISSION"}\n' > "$STATE_DIR/SUPERVISOR.json"
