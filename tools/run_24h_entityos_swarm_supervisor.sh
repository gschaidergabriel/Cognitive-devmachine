#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
ADMISSION_TOOL="$ROOT/tools/free_swarm_provider_admission.py"
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

refresh_typed_free_admission() {
  local exports
  if ! exports="$(python3 "$ADMISSION_TOOL" shell-exports)"; then
    export CLAY_FREE_ONLY_ATTESTED=0
    export CLAY_GROQ_FREE_ATTESTED=0
    export CLAY_MISTRAL_FREE_ATTESTED=0
    export CLAY_NVIDIA_FREE_ATTESTED=0
    return 1
  fi
  # free_swarm_provider_admission.py emits only fixed CLAY_* 0/1 assignments.
  eval "$exports"
}

load_admitted_secret_sources() {
  local provider source
  while IFS=$'\t' read -r provider source; do
    [[ -n "$provider" && -n "$source" ]] || continue
    load_secret_file "$source"
  done < <(python3 "$ADMISSION_TOOL" secret-sources)
}

normalize_provider_pool() {
  python3 - <<'PY'
import os, shlex
truthy=lambda x:(x or '').strip().lower() in {'1','true','yes','on','attested'}
families={
 'groq':('CLAY_GROQ_FREE_ATTESTED','GROQ_API_KEYS',['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY']),
 'mistral':('CLAY_MISTRAL_FREE_ATTESTED','MISTRAL_API_KEYS',['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY']),
 'nvidia':('CLAY_NVIDIA_FREE_ATTESTED','NVIDIA_API_KEYS',['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY']),
}
for _provider,(gate,target,names) in families.items():
    if not truthy(os.getenv(gate)):
        continue
    vals=[]
    for n in names:
        v=os.getenv(n,'').strip()
        if v and v not in vals: vals.append(v)
    for v in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
        if v not in vals: vals.append(v)
    if vals: print('export %s=%s' % (target, shlex.quote(','.join(vals))))
if truthy(os.getenv('CLAY_NVIDIA_FREE_ATTESTED')) and not os.getenv('NVIDIA_API_KEY') and os.getenv('NVIDIA_NIM_API_KEY'):
    print('export NVIDIA_API_KEY='+shlex.quote(os.environ['NVIDIA_NIM_API_KEY']))
PY
}

has_provider_key() {
  if [[ "${CLAY_GROQ_FREE_ATTESTED:-0}" == "1" ]]; then
    [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] && return 0
  fi
  if [[ "${CLAY_MISTRAL_FREE_ATTESTED:-0}" == "1" ]]; then
    [[ -n "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] && return 0
  fi
  if [[ "${CLAY_NVIDIA_FREE_ATTESTED:-0}" == "1" ]]; then
    [[ -n "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] && return 0
  fi
  return 1
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

refresh_typed_free_admission || true
if [[ "${CLAY_FREE_ONLY_ATTESTED:-0}" == "1" ]]; then
  load_admitted_secret_sources
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"
fi
start_dashboard

while (( $(date +%s) < DEADLINE )); do
  refresh_typed_free_admission || true
  if [[ "${CLAY_FREE_ONLY_ATTESTED:-0}" == "1" ]]; then
    load_admitted_secret_sources
    # shellcheck disable=SC2046
    eval "$(normalize_provider_pool)"
  fi

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - <<PY > "$STATE_DIR/SUPERVISOR.json.tmp"
import json,os,datetime
truthy=lambda x:(x or '').strip().lower() in ('1','true','yes','on','attested')
split=lambda x:[v.strip() for v in os.getenv(x,'').replace(';',',').split(',') if v.strip()]
def admitted(name): return truthy(os.getenv(f'CLAY_{name.upper()}_FREE_ATTESTED'))
def nset(*vals): return len(set(v for v in vals if v))
providers={'groq':False,'mistral':False,'nvidia':False}
counts={'groq':0,'mistral':0,'nvidia':0}
if admitted('groq'):
    providers['groq']=bool(os.getenv('GROQ_API_KEY') or split('GROQ_API_KEYS'))
    counts['groq']=nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY'))
if admitted('mistral'):
    providers['mistral']=bool(os.getenv('MISTRAL_API_KEY') or split('MISTRAL_API_KEYS'))
    counts['mistral']=nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY'))
if admitted('nvidia'):
    providers['nvidia']=bool(os.getenv('NVIDIA_API_KEY') or split('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY'))
    counts['nvidia']=nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY'))
print(json.dumps({
 'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v4',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repo_root':os.getcwd(),
 'remaining_seconds':$REMAINING,
 'typed_free_admission':{p:admitted(p) for p in ('groq','mistral','nvidia')},
 'free_only_attested':truthy(os.getenv('CLAY_FREE_ONLY_ATTESTED')),
 'provider_credentials_present':providers,
 'provider_credential_counts':counts,
 'provider_runtime_credit':0,
 'dashboard_watch':True
},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if [[ "${CLAY_FREE_ONLY_ATTESTED:-0}" == "1" ]] && has_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_AND_USABLE_CREDENTIALS","provider_runtime_credit":0}\n' > "$STATE_DIR/SUPERVISOR.json"
