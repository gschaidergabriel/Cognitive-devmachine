#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
ADMISSION_FILE="${CLAY_PROVIDER_ADMISSION_FILE:-$STATE_DIR/provider_admission.json}"

# Supervisor 8.67: typed FREE admission MUST resolve before any provider secret
# file is sourced, any provider key env is read, or any provider network I/O.
admit_provider_pool() {
  local exports
  if ! exports="$(python3 "$ROOT/tools/provider_admission_v1.py" --file "$ADMISSION_FILE" --emit-shell)"; then
    return 1
  fi
  eval "$exports"
}

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

load_all_secret_sources_after_admission() {
  [[ "${CLAY_TYPED_PROVIDER_ADMISSION_VERIFIED:-}" == "1" ]] || return 78
  load_secret_file /run/secrets/clay_provider.env
  load_secret_file /artifacts/.clay_provider.env
  load_secret_file /cache/clay_provider.env
  load_secret_file "$ROOT/.clay_provider.env"
  load_secret_file "$ROOT/research_entity/private/API_TOKENS.env"
  load_secret_file "$ROOT/research_entity/private/GROQ_API.env"
}

normalize_provider_pool() {
  python3 - <<'PY'
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
}

has_provider_key() {
  [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}${OPENROUTER_API_KEY:-}" ]]
}

start_dashboard() {
  local evaluator="$ROOT/free swarm/evaluate.py"
  [[ -f "$evaluator" ]] || return 0
  if ! pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1; then
    nohup python3 "$evaluator" \
      --repo "$ROOT" --artifacts "$STATE_DIR" \
      --watch --hours 24 --interval-seconds 60 --publish --publish-min-seconds 900 \
      >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/dashboard.pid"
  fi
}

start_distillery() {
  local runner="$ROOT/tools/run_research_distillery.py"
  [[ -f "$runner" ]] || return 0
  if ! pgrep -f '[r]un_research_distillery.py' >/dev/null 2>&1; then
    nohup python3 "$runner" --hours 24 --sleep-seconds 3 \
      >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/distillery.pid"
  fi
}

while (( $(date +%s) < DEADLINE )); do
  if ! admit_provider_pool; then
    printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v5","state":"WAITING_FOR_TYPED_FREE_PROVIDER_ADMISSION","secret_lookup_count":0,"network_attempt_count":0}\n' > "$STATE_DIR/SUPERVISOR.json"
    sleep 60
    continue
  fi

  load_all_secret_sources_after_admission
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"
  start_dashboard
  start_distillery

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - <<PY > "$STATE_DIR/SUPERVISOR.json.tmp"
import json,os,datetime
split=lambda x:[v.strip() for v in os.getenv(x,'').replace(';',',').split(',') if v.strip()]
def nset(*vals): return len(set(v for v in vals if v))
providers={
 'groq': bool(os.getenv('GROQ_API_KEY') or split('GROQ_API_KEYS')),
 'mistral': bool(os.getenv('MISTRAL_API_KEY') or split('MISTRAL_API_KEYS')),
 'nvidia': bool(os.getenv('NVIDIA_API_KEY') or split('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY')),
 'openrouter': bool(os.getenv('OPENROUTER_API_KEY')),
 'tavily': bool(os.getenv('TAVILY_API_KEY')),
 'exa': bool(os.getenv('EXA_API_KEY')),
}
counts={
 'groq': nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY')),
 'mistral': nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY')),
 'nvidia': nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY')),
}
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v5','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'typed_provider_admission_verified':True,'admission_set_id':os.getenv('CLAY_PROVIDER_ADMISSION_SET_ID',''),'provider_credentials_present':providers,'provider_credential_counts':counts,'dashboard_watch':True,'research_distillery':True},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if has_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v5","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_ADMISSION"}\n' > "$STATE_DIR/SUPERVISOR.json"
