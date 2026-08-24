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
  # Never echo or trace secret-bearing files.
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

# Authorized sandbox secret ingress plus repo-owned private provider material if
# it is actually present in the runtime checkout. Values are never printed.
load_all_secret_sources() {
  load_secret_file /run/secrets/clay_provider.env
  load_secret_file /artifacts/.clay_provider.env
  load_secret_file /cache/clay_provider.env
  load_secret_file /workspace/.clay_provider.env
  load_secret_file /workspace/research_entity/private/API_TOKENS.env
  load_secret_file /workspace/research_entity/private/GROQ_API.env
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
    existing=[x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]
    for v in existing:
        if v not in vals: vals.append(v)
    if vals:
        print('export %s=%s' % (target, shlex.quote(','.join(vals))))
# NVIDIA_NIM_API_KEY is a valid NVIDIA credential alias for the swarm client.
if not os.getenv('NVIDIA_API_KEY') and os.getenv('NVIDIA_NIM_API_KEY'):
    print('export NVIDIA_API_KEY='+shlex.quote(os.environ['NVIDIA_NIM_API_KEY']))
PY
}

has_provider_key() {
  [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]]
}

start_dashboard() {
  [[ -f "/workspace/free swarm/evaluate.py" ]] || return 0
  if ! pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1; then
    nohup python3 "/workspace/free swarm/evaluate.py" \
      --repo /workspace \
      --artifacts "$STATE_DIR" \
      --watch --hours 24 --interval-seconds 60 --publish --publish-min-seconds 900 \
      >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/dashboard.pid"
  fi
}

load_all_secret_sources
# shellcheck disable=SC2046
eval "$(normalize_provider_pool)"

# Current owner directive: these provider credentials are to be used only on
# the FREE_ONLY lane. Never infer a paid fallback from credential presence.
if has_provider_key; then
  export CLAY_FREE_ONLY_ATTESTED="${CLAY_FREE_ONLY_ATTESTED:-1}"
  [[ -z "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] || export CLAY_GROQ_FREE_ATTESTED="${CLAY_GROQ_FREE_ATTESTED:-1}"
  [[ -z "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] || export CLAY_MISTRAL_FREE_ATTESTED="${CLAY_MISTRAL_FREE_ATTESTED:-1}"
  [[ -z "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] || export CLAY_NVIDIA_FREE_ATTESTED="${CLAY_NVIDIA_FREE_ATTESTED:-1}"
fi

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  load_all_secret_sources
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"
  if has_provider_key; then
    export CLAY_FREE_ONLY_ATTESTED="${CLAY_FREE_ONLY_ATTESTED:-1}"
    [[ -z "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] || export CLAY_GROQ_FREE_ATTESTED="${CLAY_GROQ_FREE_ATTESTED:-1}"
    [[ -z "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] || export CLAY_MISTRAL_FREE_ATTESTED="${CLAY_MISTRAL_FREE_ATTESTED:-1}"
    [[ -z "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] || export CLAY_NVIDIA_FREE_ATTESTED="${CLAY_NVIDIA_FREE_ATTESTED:-1}"
  fi

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - <<PY > "$STATE_DIR/SUPERVISOR.json.tmp"
import json,os,datetime
split=lambda x:[v for v in (os.getenv(x,'').replace(';',',').split(',')) if v.strip()]
providers={
 'groq': bool(os.getenv('GROQ_API_KEY') or split('GROQ_API_KEYS')),
 'mistral': bool(os.getenv('MISTRAL_API_KEY') or split('MISTRAL_API_KEYS')),
 'nvidia': bool(os.getenv('NVIDIA_API_KEY') or split('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY')),
}
counts={
 'groq': len(set(split('GROQ_API_KEYS') + ([os.getenv('GROQ_API_KEY')] if os.getenv('GROQ_API_KEY') else []))),
 'mistral': len(set(split('MISTRAL_API_KEYS') + ([os.getenv('MISTRAL_API_KEY')] if os.getenv('MISTRAL_API_KEY') else []))),
 'nvidia': len(set(split('NVIDIA_API_KEYS') + [v for v in [os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY')] if v])),
}
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v2','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remaining_seconds':$REMAINING,'free_only_attested':str(os.getenv('CLAY_FREE_ONLY_ATTESTED','')).lower() in ('1','true','yes','on','attested'),'provider_credentials_present':providers,'provider_credential_counts':counts,'dashboard_watch':True},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if [[ "${CLAY_FREE_ONLY_ATTESTED:-}" =~ ^(1|true|TRUE|yes|YES|on|ON|attested)$ ]] && has_provider_key; then
    exec python3 tools/run_24h_entityos_swarm.py --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v2","state":"EXPIRED_WITHOUT_USABLE_FREE_ONLY_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
