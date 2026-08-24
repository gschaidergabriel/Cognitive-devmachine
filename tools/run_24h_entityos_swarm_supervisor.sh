#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
ADMISSION_TOOL="$ROOT/tools/free_provider_admission_v1.py"

provider_free_admitted() {
  local provider="$1"
  python3 "$ADMISSION_TOOL" --provider "$provider" --check >/dev/null 2>&1
}

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

load_provider_secret_sources() {
  local provider="$1"
  provider_free_admitted "$provider" || return 0
  case "$provider" in
    groq)
      load_secret_file /run/secrets/clay_groq.env
      load_secret_file /artifacts/.clay_groq.env
      load_secret_file /cache/clay_groq.env
      load_secret_file "$ROOT/.clay_groq.env"
      load_secret_file "$ROOT/research_entity/private/GROQ_API.env"
      ;;
    mistral)
      load_secret_file /run/secrets/clay_mistral.env
      load_secret_file /artifacts/.clay_mistral.env
      load_secret_file /cache/clay_mistral.env
      load_secret_file "$ROOT/.clay_mistral.env"
      load_secret_file "$ROOT/research_entity/private/MISTRAL_API.env"
      ;;
    nvidia)
      load_secret_file /run/secrets/clay_nvidia.env
      load_secret_file /artifacts/.clay_nvidia.env
      load_secret_file /cache/clay_nvidia.env
      load_secret_file "$ROOT/.clay_nvidia.env"
      load_secret_file "$ROOT/research_entity/private/NVIDIA_API.env"
      ;;
    *)
      return 0
      ;;
  esac
}

normalize_provider_pool() {
  local provider="$1"
  provider_free_admitted "$provider" || return 0
  PROVIDER="$provider" python3 - <<'PY'
import os, shlex
provider=os.environ["PROVIDER"]
families={
 'groq':('GROQ_API_KEYS',['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY']),
 'mistral':('MISTRAL_API_KEYS',['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY']),
 'nvidia':('NVIDIA_API_KEYS',['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY']),
}
target,names=families[provider]
vals=[]
for n in names:
    v=os.getenv(n,'').strip()
    if v and v not in vals:
        vals.append(v)
for v in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
    if v not in vals:
        vals.append(v)
if vals:
    print('export %s=%s' % (target, shlex.quote(','.join(vals))))
if provider == 'nvidia' and not os.getenv('NVIDIA_API_KEY') and os.getenv('NVIDIA_NIM_API_KEY'):
    print('export NVIDIA_API_KEY='+shlex.quote(os.environ['NVIDIA_NIM_API_KEY']))
PY
}

has_provider_key() {
  local provider="$1"
  provider_free_admitted "$provider" || return 1
  case "$provider" in
    groq) [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] ;;
    mistral) [[ -n "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] ;;
    nvidia) [[ -n "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] ;;
    *) return 1 ;;
  esac
}

refresh_typed_admission() {
  local free
  free="$(python3 "$ADMISSION_TOOL" --list-free)"
  export CLAY_FREE_PROVIDER_LIST="$free"

  unset CLAY_FREE_ONLY_ATTESTED
  unset CLAY_GROQ_FREE_ATTESTED
  unset CLAY_MISTRAL_FREE_ATTESTED
  unset CLAY_NVIDIA_FREE_ATTESTED

  [[ -n "$free" ]] || return 0
  export CLAY_FREE_ONLY_ATTESTED=1

  local provider
  for provider in $free; do
    case "$provider" in
      groq) export CLAY_GROQ_FREE_ATTESTED=1 ;;
      mistral) export CLAY_MISTRAL_FREE_ATTESTED=1 ;;
      nvidia) export CLAY_NVIDIA_FREE_ATTESTED=1 ;;
    esac
  done
}

prepare_admitted_provider() {
  local provider="$1"
  provider_free_admitted "$provider" || return 0
  load_provider_secret_sources "$provider"
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool "$provider")"
}

has_any_admitted_provider_key() {
  local provider
  for provider in ${CLAY_FREE_PROVIDER_LIST:-}; do
    if has_provider_key "$provider"; then
      return 0
    fi
  done
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

refresh_typed_admission
for provider in ${CLAY_FREE_PROVIDER_LIST:-}; do
  prepare_admitted_provider "$provider"
done
start_dashboard

while (( $(date +%s) < DEADLINE )); do
  refresh_typed_admission
  for provider in ${CLAY_FREE_PROVIDER_LIST:-}; do
    prepare_admitted_provider "$provider"
  done

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - <<PY > "$STATE_DIR/SUPERVISOR.json.tmp"
import json,os,datetime
free=set(os.getenv('CLAY_FREE_PROVIDER_LIST','').split())
split=lambda x:[v.strip() for v in os.getenv(x,'').replace(';',',').split(',') if v.strip()]
def nset(*vals): return len(set(v for v in vals if v))
providers={}
counts={}
if 'groq' in free:
    providers['groq']=bool(os.getenv('GROQ_API_KEY') or split('GROQ_API_KEYS'))
    counts['groq']=nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY'))
else:
    providers['groq']='NOT_READ_NOT_ADMITTED'
    counts['groq']='NOT_READ_NOT_ADMITTED'
if 'mistral' in free:
    providers['mistral']=bool(os.getenv('MISTRAL_API_KEY') or split('MISTRAL_API_KEYS'))
    counts['mistral']=nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY'))
else:
    providers['mistral']='NOT_READ_NOT_ADMITTED'
    counts['mistral']='NOT_READ_NOT_ADMITTED'
if 'nvidia' in free:
    providers['nvidia']=bool(os.getenv('NVIDIA_API_KEY') or split('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY'))
    counts['nvidia']=nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY'))
else:
    providers['nvidia']='NOT_READ_NOT_ADMITTED'
    counts['nvidia']='NOT_READ_NOT_ADMITTED'
print(json.dumps({
  'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v4',
  'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'repo_root':os.getcwd(),
  'remaining_seconds':$REMAINING,
  'typed_free_providers':sorted(free),
  'free_only_attested':bool(free),
  'provider_credentials_present':providers,
  'provider_credential_counts':counts,
  'admission_boundary':'TYPED_COST_CLASS_FREE_BEFORE_SECRET_LOOKUP_AND_NETWORK_IO',
  'dashboard_watch':True,
},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if has_any_admitted_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
