#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
ADMISSION_TOOL="$ROOT/tools/free_provider_admission.py"

provider_admitted() {
  local provider="$1"
  python3 "$ADMISSION_TOOL" --provider "$provider" >/dev/null 2>&1
}

# Compatibility flags are derived only from canonical typed admission. Inherited
# caller attestations are cleared so they cannot self-admit a provider.
typed_admission_compat_flags() {
  unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
  local any=0
  if provider_admitted groq; then export CLAY_GROQ_FREE_ATTESTED=1; any=1; fi
  if provider_admitted mistral; then export CLAY_MISTRAL_FREE_ATTESTED=1; any=1; fi
  if provider_admitted nvidia; then export CLAY_NVIDIA_FREE_ATTESTED=1; any=1; fi
  if (( any )); then export CLAY_FREE_ONLY_ATTESTED=1; fi
}

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

# Never source aggregate/mixed provider files here. Their provider contents are
# unknowable before reading them, so loading them would violate the 8.67 boundary
# for any UNKNOWN/PAID/SUBSCRIPTION provider (including distillery services such
# as OpenRouter/Tavily/Exa). Only a provider-specific source whose provider has
# already passed canonical typed FREE admission is eligible.
load_admitted_secret_sources() {
  if provider_admitted groq; then
    load_secret_file "$ROOT/research_entity/private/GROQ_API.env"
  fi
}

normalize_provider_pool() {
  python3 - <<'PY'
import os, shlex
from free_provider_admission import load_provider_admission, provider_is_admitted_free, ProviderAdmissionError
try:
    admission=load_provider_admission()
except ProviderAdmissionError:
    raise SystemExit(0)
families={
 'groq':('GROQ_API_KEYS',['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY']),
 'mistral':('MISTRAL_API_KEYS',['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY']),
 'nvidia':('NVIDIA_API_KEYS',['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY']),
}
for provider,(target,names) in families.items():
    if not provider_is_admitted_free(provider, admission):
        continue
    vals=[]
    for n in names:
        v=os.getenv(n,'').strip()
        if v and v not in vals: vals.append(v)
    for v in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
        if v not in vals: vals.append(v)
    if vals: print('export %s=%s' % (target, shlex.quote(','.join(vals))))
if provider_is_admitted_free('nvidia', admission) and not os.getenv('NVIDIA_API_KEY') and os.getenv('NVIDIA_NIM_API_KEY'):
    print('export NVIDIA_API_KEY='+shlex.quote(os.environ['NVIDIA_NIM_API_KEY']))
PY
}

has_admitted_provider_key() {
  if provider_admitted groq && [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]]; then return 0; fi
  if provider_admitted mistral && [[ -n "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]]; then return 0; fi
  if provider_admitted nvidia && [[ -n "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]]; then return 0; fi
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

start_distillery() {
  local runner="$ROOT/tools/run_research_distillery_entry.py"
  [[ -f "$runner" ]] || return 0
  if ! pgrep -f '[r]un_research_distillery_entry.py' >/dev/null 2>&1; then
    nohup python3 "$runner" --hours 24 --sleep-seconds 3 \
      >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/distillery.pid"
  fi
}

typed_admission_compat_flags
load_admitted_secret_sources
# shellcheck disable=SC2046
eval "$(normalize_provider_pool)"
start_dashboard
start_distillery

while (( $(date +%s) < DEADLINE )); do
  typed_admission_compat_flags
  load_admitted_secret_sources
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"
  start_distillery

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - <<PY > "$STATE_DIR/SUPERVISOR.json.tmp"
import json,os,datetime
from free_provider_admission import load_provider_admission, provider_is_admitted_free, ProviderAdmissionError
split=lambda x:[v.strip() for v in os.getenv(x,'').replace(';',',').split(',') if v.strip()]
def nset(*vals): return len(set(v for v in vals if v))
try:
    admission=load_provider_admission()
    admitted={p:provider_is_admitted_free(p,admission) for p in ('groq','mistral','nvidia','openrouter','tavily','exa')}
    epoch=admission.get('authority_epoch')
except ProviderAdmissionError:
    admitted={p:False for p in ('groq','mistral','nvidia','openrouter','tavily','exa')}; epoch=None
providers={
 'groq': bool(admitted['groq'] and (os.getenv('GROQ_API_KEY') or split('GROQ_API_KEYS'))),
 'mistral': bool(admitted['mistral'] and (os.getenv('MISTRAL_API_KEY') or split('MISTRAL_API_KEYS'))),
 'nvidia': bool(admitted['nvidia'] and (os.getenv('NVIDIA_API_KEY') or split('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY'))),
 'openrouter': bool(admitted['openrouter'] and os.getenv('OPENROUTER_API_KEY')),
 'tavily': bool(admitted['tavily'] and os.getenv('TAVILY_API_KEY')),
 'exa': bool(admitted['exa'] and os.getenv('EXA_API_KEY')),
}
counts={
 'groq': nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY')) if admitted['groq'] else 0,
 'mistral': nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY')) if admitted['mistral'] else 0,
 'nvidia': nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY')) if admitted['nvidia'] else 0,
 'openrouter': int(bool(os.getenv('OPENROUTER_API_KEY'))) if admitted['openrouter'] else 0,
 'tavily': int(bool(os.getenv('TAVILY_API_KEY'))) if admitted['tavily'] else 0,
 'exa': int(bool(os.getenv('EXA_API_KEY'))) if admitted['exa'] else 0,
}
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v7','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'typed_provider_admission_epoch':epoch,'providers_admitted_free':admitted,'provider_credentials_present_after_admission':providers,'provider_credential_counts_after_admission':counts,'dashboard_watch':True,'research_distillery':True,'distillery_entrypoint':'run_research_distillery_entry.py'},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if [[ "${CLAY_FREE_ONLY_ATTESTED:-}" == "1" ]] && has_admitted_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v7","state":"EXPIRED_WITHOUT_CANONICALLY_FREE_ADMITTED_PROVIDER"}\n' > "$STATE_DIR/SUPERVISOR.json"
