#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
ADMISSION_FILE="${CLAY_PROVIDER_ADMISSION_FILE:-$STATE_DIR/provider-admission.json}"
ADMISSION_CHECKER="$ROOT/tools/free_provider_admission.py"
export CLAY_PROVIDER_ADMISSION_FILE="$ADMISSION_FILE"

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

# Broad catch-all token files are intentionally excluded. Provider credentials are
# not sourced until typed EntityOS/HCU control-plane admission has classified every
# configured provider as FREE.
load_admitted_provider_secret_sources() {
  load_secret_file /run/secrets/clay_provider_groq.env
  load_secret_file /artifacts/.clay_provider_groq.env
  load_secret_file /cache/clay_provider_groq.env
  load_secret_file "$ROOT/.clay_provider_groq.env"
  load_secret_file "$ROOT/research_entity/private/GROQ_API.env"

  load_secret_file /run/secrets/clay_provider_mistral.env
  load_secret_file /artifacts/.clay_provider_mistral.env
  load_secret_file /cache/clay_provider_mistral.env
  load_secret_file "$ROOT/.clay_provider_mistral.env"
  load_secret_file "$ROOT/research_entity/private/MISTRAL_API.env"

  load_secret_file /run/secrets/clay_provider_nvidia.env
  load_secret_file /artifacts/.clay_provider_nvidia.env
  load_secret_file /cache/clay_provider_nvidia.env
  load_secret_file "$ROOT/.clay_provider_nvidia.env"
  load_secret_file "$ROOT/research_entity/private/NVIDIA_API.env"
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

typed_free_admission_ready() {
  [[ -r "$ADMISSION_CHECKER" ]] || return 1
  python3 "$ADMISSION_CHECKER" "$ADMISSION_FILE" >/dev/null 2>&1
}

derive_runtime_attestation_from_typed_admission() {
  # Compatibility flags are downstream signals only. They are never authority.
  export CLAY_FREE_ONLY_ATTESTED=1
  export CLAY_GROQ_FREE_ATTESTED=1
  export CLAY_MISTRAL_FREE_ATTESTED=1
  export CLAY_NVIDIA_FREE_ATTESTED=1
}

write_presecret_state() {
  local reason="$1"
  python3 - "$STATE_DIR/SUPERVISOR.json.tmp" "$ADMISSION_FILE" "$reason" <<'PY'
import datetime,json,os,sys
out,admission_file,reason=sys.argv[1:]
payload={
 'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v6',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repo_root':os.getcwd(),
 'state':'WAITING_FOR_TYPED_FREE_PROVIDER_ADMISSION',
 'reason':reason,
 'admission_file':admission_file,
 'secret_lookup_count':0,
 'network_attempt_count':0,
 'provider_credentials_present':'NOT_READ_BEFORE_TYPED_ADMISSION',
 'external_workers_started':0,
 'research_distillery_started':False,
}
open(out,'w',encoding='utf-8').write(json.dumps(payload,indent=2)+'\n')
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
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
  typed_free_admission_ready || return 1
  if ! pgrep -f '[r]un_research_distillery_entry.py' >/dev/null 2>&1; then
    nohup python3 "$runner" --hours 24 --sleep-seconds 3 \
      >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/distillery.pid"
  fi
}

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  if ! typed_free_admission_ready; then
    write_presecret_state "TYPED_CONTROL_PLANE_FREE_ADMISSION_MISSING_INVALID_OR_NONFREE"
    sleep 60
    continue
  fi

  derive_runtime_attestation_from_typed_admission
  load_admitted_provider_secret_sources
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
import json,os,datetime,hashlib,pathlib
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
p=pathlib.Path(os.environ['CLAY_PROVIDER_ADMISSION_FILE'])
digest=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'UNAVAILABLE'
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v6','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'typed_provider_admission':'PASS_ALL_KNOWN_PROVIDERS_COST_CLASS_FREE','admission_sha256':digest,'free_only_attested':True,'provider_credentials_present':providers,'provider_credential_counts':counts,'dashboard_watch':True,'research_distillery':True,'distillery_entrypoint':'run_research_distillery_entry.py'},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  # Revalidate at the last boundary before a process capable of provider network I/O.
  if typed_free_admission_ready && has_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v6","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_ADMISSION_OR_USABLE_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
