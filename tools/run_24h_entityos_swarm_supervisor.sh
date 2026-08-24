#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
ADMISSION="$ROOT/tools/free_provider_admission.py"

provider_is_admitted() {
  python3 "$ADMISSION" --provider "$1" >/dev/null 2>&1
}

# Clear inherited provider credentials without expanding their values. `compgen -v`
# enumerates variable names only; values remain unread until a typed FREE provider
# admission has passed.
clear_provider_secret_env() {
  local name
  for name in \
    GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY \
    MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY \
    NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY NVIDIA_NIM_API_KEY \
    OPENROUTER_API_KEY TAVILY_API_KEY EXA_API_KEY; do
    unset "$name" || true
  done
  while IFS= read -r name; do
    case "$name" in
      GROQ_API_KEY_*|MISTRAL_API_KEY_*|NVIDIA_API_KEY_*) unset "$name" || true ;;
    esac
  done < <(compgen -v)
}

provider_name_allowed() {
  local provider="$1" name="$2"
  case "$provider:$name" in
    groq:GROQ_API_KEY|groq:GROQ_API_KEYS|groq:GROQ_API_KEY_*|groq:GROQ2_API_KEY|groq:GROQ3_API_KEY) return 0 ;;
    mistral:MISTRAL_API_KEY|mistral:MISTRAL_API_KEYS|mistral:MISTRAL_API_KEY_*|mistral:MISTRAL2_API_KEY|mistral:MISTRAL3_API_KEY) return 0 ;;
    nvidia:NVIDIA_API_KEY|nvidia:NVIDIA_API_KEYS|nvidia:NVIDIA_API_KEY_*|nvidia:NVIDIA2_API_KEY|nvidia:NVIDIA3_API_KEY|nvidia:NGC_API_KEY|nvidia:NVIDIA_NIM_API_KEY) return 0 ;;
    *) return 1 ;;
  esac
}

# Provider files are provider-scoped and parsed as dotenv data; arbitrary shell code
# is never sourced/evaled. Generic mixed credential bundles are intentionally excluded.
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

normalize_admitted_provider_pool() {
  # All blocked-provider variables were cleared before this point; only admitted
  # provider variables can be present here.
  eval "$(python3 - <<'PY'
import os, shlex
families={
 'GROQ_API_KEYS':['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY'],
 'MISTRAL_API_KEYS':['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY'],
 'NVIDIA_API_KEYS':['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY'],
}
for target,names in families.items():
    vals=[]
    for n in names:
        v=os.getenv(n,'').strip()
        if v and v not in vals: vals.append(v)
    for v in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
        if v not in vals: vals.append(v)
    if vals: print('export %s=%s' % (target, shlex.quote(','.join(vals))))
if not os.getenv('NVIDIA_API_KEY') and os.getenv('NVIDIA_NIM_API_KEY'):
    print('export NVIDIA_API_KEY='+shlex.quote(os.environ['NVIDIA_NIM_API_KEY']))
PY
)"
}

activate_compat_attestation() {
  unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
  local any=0
  if provider_is_admitted groq; then export CLAY_GROQ_FREE_ATTESTED=1; any=1; fi
  if provider_is_admitted mistral; then export CLAY_MISTRAL_FREE_ATTESTED=1; any=1; fi
  if provider_is_admitted nvidia; then export CLAY_NVIDIA_FREE_ATTESTED=1; any=1; fi
  (( any == 0 )) || export CLAY_FREE_ONLY_ATTESTED=1
}

start_dashboard_local_only() {
  local evaluator="$ROOT/free swarm/evaluate.py"
  [[ -f "$evaluator" ]] || return 0
  if ! pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1; then
    nohup python3 "$evaluator" \
      --repo "$ROOT" --artifacts "$STATE_DIR" \
      --watch --hours 24 --interval-seconds 60 \
      >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/dashboard.pid"
  fi
}

start_distillery() {
  local runner="$ROOT/tools/run_research_distillery_entry.py"
  [[ -f "$runner" ]] || return 0
  if ! pgrep -f '[r]un_research_distillery_entry.py' >/dev/null 2>&1; then
    nohup python3 "$runner" --hours 24 --sleep-seconds 3 \
      >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/distillery.pid"
  fi
}

write_supervisor_state() {
  local remaining="$1"
  python3 "$ADMISSION" --json > "$STATE_DIR/provider_admission.json.tmp" 2>/dev/null || true
  mv "$STATE_DIR/provider_admission.json.tmp" "$STATE_DIR/provider_admission.json" 2>/dev/null || true
  printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v6","remaining_seconds":%s,"admission_boundary":"BEFORE_SECRET_KEY_LOOKUP_AND_PROVIDER_NETWORK_IO","dashboard_publish":false,"distillery_provider_calls":"GATED_BY_ENTRYPOINT"}\n' "$remaining" > "$STATE_DIR/SUPERVISOR.json.tmp"
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
}

clear_provider_secret_env
start_dashboard_local_only
start_distillery

while (( $(date +%s) < DEADLINE )); do
  clear_provider_secret_env
  load_admitted_provider_secrets groq
  load_admitted_provider_secrets mistral
  load_admitted_provider_secrets nvidia
  normalize_admitted_provider_pool
  activate_compat_attestation
  start_distillery

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  write_supervisor_state "$REMAINING"

  if [[ -n "${CLAY_FREE_ONLY_ATTESTED:-}" ]]; then
    HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"
    set +e
    python3 "$ROOT/tools/run_24h_entityos_swarm_entry.py" \
      --hours "$HOURS" \
      --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
    RC=$?
    set -e
    case "$RC" in
      0) exit 0 ;;
      4|5) ;; # fail-closed admission/no-key state; recheck on next loop
      *) printf 'swarm driver exited rc=%s; supervisor will re-enter typed admission\n' "$RC" >&2 ;;
    esac
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v6","state":"EXPIRED_WITHOUT_EXECUTABLE_TYPED_FREE_PROVIDER_ADMISSION"}\n' > "$STATE_DIR/SUPERVISOR.json"
