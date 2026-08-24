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
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

load_all_secret_sources() {
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
  [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]]
}

attest_free_only() {
  has_provider_key || return 0
  export CLAY_FREE_ONLY_ATTESTED="${CLAY_FREE_ONLY_ATTESTED:-1}"
  [[ -z "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] || export CLAY_GROQ_FREE_ATTESTED="${CLAY_GROQ_FREE_ATTESTED:-1}"
  [[ -z "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] || export CLAY_MISTRAL_FREE_ATTESTED="${CLAY_MISTRAL_FREE_ATTESTED:-1}"
  [[ -z "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] || export CLAY_NVIDIA_FREE_ATTESTED="${CLAY_NVIDIA_FREE_ATTESTED:-1}"
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

load_all_secret_sources
# shellcheck disable=SC2046
eval "$(normalize_provider_pool)"
attest_free_only
start_dashboard

while (( $(date +%s) < DEADLINE )); do
  load_all_secret_sources
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"
  attest_free_only

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
}
counts={
 'groq': nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY')),
 'mistral': nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY')),
 'nvidia': nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY')),
}
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v3','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'free_only_attested':str(os.getenv('CLAY_FREE_ONLY_ATTESTED','')).lower() in ('1','true','yes','on','attested'),'provider_credentials_present':providers,'provider_credential_counts':counts,'dashboard_watch':True},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if [[ "${CLAY_FREE_ONLY_ATTESTED:-}" =~ ^(1|true|TRUE|yes|YES|on|ON|attested)$ ]] && has_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v3","state":"EXPIRED_WITHOUT_USABLE_FREE_ONLY_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
