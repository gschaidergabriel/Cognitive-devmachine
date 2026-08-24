#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
GATE="$ROOT/tools/free_provider_admission_gate.py"
ADMISSION="$ROOT/research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
SUPERVISOR="$ROOT/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"

provider_is_admitted() {
  python3 "$GATE" --admission "$ADMISSION" --supervisor "$SUPERVISOR" --provider "$1" >/dev/null 2>&1
}

# Remove inherited credential values without expanding them. Every loop starts
# from a secret-clean environment; only an exact canonical FREE admission can
# enable a subsequent provider-scoped load.
clear_provider_secret_env() {
  local name
  for name in \
    GROQ_API_KEY GROQ_API_KEYS MISTRAL_API_KEY MISTRAL_API_KEYS \
    NVIDIA_API_KEY NVIDIA_API_KEYS NGC_API_KEY NVIDIA_NIM_API_KEY \
    OPENROUTER_API_KEY TAVILY_API_KEY EXA_API_KEY; do
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
    openrouter:OPENROUTER_API_KEY|tavily:TAVILY_API_KEY|exa:EXA_API_KEY) return 0 ;;
    *) return 1 ;;
  esac
}

# Secret files are provider-scoped and parsed as KEY=VALUE data, never sourced
# as shell. Mixed bundles are intentionally excluded because reading one before
# every contained provider is admitted would violate the 8.67 boundary.
load_provider_secret_file() {
  local provider="$1" f="$2" raw name value
  [[ -n "$f" && -r "$f" ]] || return 0
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    raw="${raw%$'\r'}"
    [[ -z "$raw" || "$raw" == \#* ]] && continue
    [[ "$raw" == export\ * ]] && raw="${raw#export }"
    [[ "$raw" == *=* ]] || continue
    name="${raw%%=*}"; value="${raw#*=}"
    [[ "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    provider_name_allowed "$provider" "$name" || continue
    if [[ ${#value} -ge 2 ]]; then
      if [[ "$value" == \"*\" && "$value" == *\" ]]; then value="${value:1:${#value}-2}"
      elif [[ "$value" == \'*\' && "$value" == *\' ]]; then value="${value:1:${#value}-2}"
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
      override="${CLAY_GROQ_SECRET_FILE:-}"; load_provider_secret_file groq "$override"; load_provider_secret_file groq /run/secrets/clay_groq.env; load_provider_secret_file groq /artifacts/.clay_groq.env; load_provider_secret_file groq /cache/clay_groq.env; load_provider_secret_file groq "$ROOT/.clay_groq.env"; load_provider_secret_file groq "$ROOT/research_entity/private/GROQ_API.env" ;;
    mistral)
      override="${CLAY_MISTRAL_SECRET_FILE:-}"; load_provider_secret_file mistral "$override"; load_provider_secret_file mistral /run/secrets/clay_mistral.env; load_provider_secret_file mistral /artifacts/.clay_mistral.env; load_provider_secret_file mistral /cache/clay_mistral.env; load_provider_secret_file mistral "$ROOT/.clay_mistral.env"; load_provider_secret_file mistral "$ROOT/research_entity/private/MISTRAL_API.env" ;;
    nvidia)
      override="${CLAY_NVIDIA_SECRET_FILE:-}"; load_provider_secret_file nvidia "$override"; load_provider_secret_file nvidia /run/secrets/clay_nvidia.env; load_provider_secret_file nvidia /artifacts/.clay_nvidia.env; load_provider_secret_file nvidia /cache/clay_nvidia.env; load_provider_secret_file nvidia "$ROOT/.clay_nvidia.env"; load_provider_secret_file nvidia "$ROOT/research_entity/private/NVIDIA_API.env" ;;
    openrouter)
      override="${CLAY_OPENROUTER_SECRET_FILE:-}"; load_provider_secret_file openrouter "$override"; load_provider_secret_file openrouter /run/secrets/clay_openrouter.env ;;
    tavily)
      override="${CLAY_TAVILY_SECRET_FILE:-}"; load_provider_secret_file tavily "$override"; load_provider_secret_file tavily /run/secrets/clay_tavily.env ;;
    exa)
      override="${CLAY_EXA_SECRET_FILE:-}"; load_provider_secret_file exa "$override"; load_provider_secret_file exa /run/secrets/clay_exa.env ;;
  esac
}

has_admitted_swarm_key() {
  local provider
  for provider in groq mistral nvidia; do
    provider_is_admitted "$provider" || continue
    case "$provider" in
      groq) [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] && return 0 ;;
      mistral) [[ -n "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] && return 0 ;;
      nvidia) [[ -n "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] && return 0 ;;
    esac
  done
  return 1
}

start_dashboard() {
  local evaluator="$ROOT/free swarm/evaluate.py"
  [[ -f "$evaluator" ]] || return 0
  if ! pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1; then
    nohup env -u GROQ_API_KEY -u GROQ_API_KEYS -u MISTRAL_API_KEY -u MISTRAL_API_KEYS -u NVIDIA_API_KEY -u NVIDIA_API_KEYS -u NGC_API_KEY -u NVIDIA_NIM_API_KEY -u OPENROUTER_API_KEY -u TAVILY_API_KEY -u EXA_API_KEY \
      python3 "$evaluator" --repo "$ROOT" --artifacts "$STATE_DIR" --watch --hours 24 --interval-seconds 60 --publish --publish-min-seconds 900 \
      >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/dashboard.pid"
  fi
}

start_distillery() {
  local runner="$ROOT/tools/run_research_distillery_entry.py"
  [[ -f "$runner" ]] || return 0
  if ! pgrep -f '[r]un_research_distillery_entry.py' >/dev/null 2>&1; then
    # Keep inherited environment secret-clean. The distillery entrypoint itself
    # gates any credential lookup against the canonical admission object.
    nohup env -u GROQ_API_KEY -u GROQ_API_KEYS -u MISTRAL_API_KEY -u MISTRAL_API_KEYS -u NVIDIA_API_KEY -u NVIDIA_API_KEYS -u NGC_API_KEY -u NVIDIA_NIM_API_KEY -u OPENROUTER_API_KEY -u TAVILY_API_KEY -u EXA_API_KEY \
      python3 "$runner" --hours 24 --sleep-seconds 3 >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/distillery.pid"
  fi
}

write_supervisor_state() {
  local remaining="$1"
  python3 - "$ADMISSION" "$SUPERVISOR" "$remaining" <<'PY' > "$STATE_DIR/SUPERVISOR.json.tmp"
import datetime,json,pathlib,sys
ap,sp,remaining=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),int(sys.argv[3])
try:a=json.loads(ap.read_text(encoding='utf-8'))
except Exception:a={}
try:s=json.loads(sp.read_text(encoding='utf-8'))
except Exception:s={}
providers=a.get('providers') if isinstance(a,dict) else None
summary={}
for p in ('groq','mistral','nvidia','openrouter','tavily','exa'):
    x=providers.get(p) if isinstance(providers,dict) else None
    summary[p]={'admitted':x.get('admitted') is True,'cost_class':str(x.get('cost_class','UNKNOWN')).upper(),'evidence_ref':str(x.get('evidence_ref',''))} if isinstance(x,dict) else {'admitted':False,'cost_class':'UNKNOWN','evidence_ref':''}
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v6','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remaining_seconds':remaining,'supervisor_epoch':str(s.get('schema_version','')) if isinstance(s,dict) else '','admission_epoch':str(a.get('authority_epoch','')) if isinstance(a,dict) else '','provider_admissions':summary,'credential_policy':'UNREAD_UNLESS_EXACT_CANONICAL_FREE_ADMISSION','dashboard_watch':True,'research_distillery':True,'distillery_credential_gate':'CANONICAL_FREE_PROVIDER_ADMISSION'},indent=2,sort_keys=True))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
}

clear_provider_secret_env
start_dashboard
start_distillery

while (( $(date +%s) < DEADLINE )); do
  clear_provider_secret_env
  for provider in groq mistral nvidia openrouter tavily exa; do load_admitted_provider_secrets "$provider"; done
  start_distillery

  NOW="$(date +%s)"; REMAINING="$((DEADLINE - NOW))"
  write_supervisor_state "$REMAINING"

  if has_admitted_swarm_key; then
    HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"
    set +e
    python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
    RC=$?
    set -e
    case "$RC" in
      0) exit 0 ;;
      4) ;;
      *) printf 'swarm driver exited rc=%s; fail-closed supervisor will retry after refresh\n' "$RC" >&2 ;;
    esac
  fi
  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v6","state":"EXPIRED_WITHOUT_EXECUTABLE_CANONICAL_FREE_PROVIDER_ADMISSION"}\n' > "$STATE_DIR/SUPERVISOR.json"
