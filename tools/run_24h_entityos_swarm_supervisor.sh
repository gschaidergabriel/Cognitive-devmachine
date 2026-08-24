#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"
STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="${CLAY_SWARM_DEADLINE_EPOCH:-$((START + 24*3600))}"
ADMISSION_TOOL="$ROOT/tools/free_provider_admission.py"
SWARM_ADMISSION_DIGEST_FILE="$STATE_DIR/swarm.provider-admission.sha256"

provider_admitted(){ python3 "$ADMISSION_TOOL" --provider "$1" >/dev/null 2>&1; }

# This is a supervisor-local process-capability fingerprint, not a canonical product
# identity. `free_provider_admission.py --json` resolves successor-dynamic canonical
# admission without secret lookup; hashing its sorted compact snapshot lets the
# supervisor detect partial revocation (A revoked while B remains admitted) as well
# as authority/evidence drift for an already-running credential-bearing child.
current_provider_admission_digest(){
  python3 "$ADMISSION_TOOL" --json 2>/dev/null | sha256sum | awk '{print $1}'
}

# Child processes inherit the supervisor environment. Remove credentials belonging
# to any external LLM provider that is not canonically typed FREE-admitted before
# spawning local-model/distillery/forge/dashboard/swarm children. `unset` and
# `compgen -v` operate on variable names only; blocked credential values are never
# expanded merely to decide whether they should be removed.
clear_unadmitted_provider_secret_env(){
  local name
  if ! provider_admitted groq; then
    unset GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY || true
    while IFS= read -r name; do case "$name" in GROQ_API_KEY_*) unset "$name" || true ;; esac; done < <(compgen -v)
  fi
  if ! provider_admitted mistral; then
    unset MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY || true
    while IFS= read -r name; do case "$name" in MISTRAL_API_KEY_*) unset "$name" || true ;; esac; done < <(compgen -v)
  fi
  if ! provider_admitted nvidia; then
    unset NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY || true
    while IFS= read -r name; do case "$name" in NVIDIA_API_KEY_*) unset "$name" || true ;; esac; done < <(compgen -v)
  fi
  if ! provider_admitted openrouter; then
    unset OPENROUTER_API_KEY OPENROUTER_API_KEYS || true
    while IFS= read -r name; do case "$name" in OPENROUTER_API_KEY_*) unset "$name" || true ;; esac; done < <(compgen -v)
  fi
}

typed_admission_compat_flags(){
  unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
  local any=0
  if provider_admitted groq; then export CLAY_GROQ_FREE_ATTESTED=1; any=1; fi
  if provider_admitted mistral; then export CLAY_MISTRAL_FREE_ATTESTED=1; any=1; fi
  if provider_admitted nvidia; then export CLAY_NVIDIA_FREE_ATTESTED=1; any=1; fi
  if provider_admitted openrouter; then any=1; fi
  (( any )) && export CLAY_FREE_ONLY_ATTESTED=1 || true
}

load_secret_file(){ local f="$1"; [[ -r "$f" ]] || return 0; set +x; set -a; source "$f"; set +a; }
all_llm_providers_admitted(){ provider_admitted groq && provider_admitted mistral && provider_admitted nvidia && provider_admitted openrouter; }

load_admitted_secret_sources(){
  if all_llm_providers_admitted; then
    load_secret_file /run/secrets/clay_provider.env
    load_secret_file /artifacts/.clay_provider.env
    load_secret_file /cache/clay_provider.env
    load_secret_file "$ROOT/.clay_provider.env"
    load_secret_file "$ROOT/research_entity/private/API_TOKENS.env"
  fi
  provider_admitted groq && load_secret_file "$ROOT/research_entity/private/GROQ_API.env" || true
}

normalize_provider_pool(){
python3 - <<'PY'
import os,shlex
from free_provider_admission import load_provider_admission,provider_is_admitted_free,ProviderAdmissionError
try:a=load_provider_admission()
except ProviderAdmissionError:raise SystemExit(0)
families={
 'groq':('GROQ_API_KEYS',['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY']),
 'mistral':('MISTRAL_API_KEYS',['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY']),
 'nvidia':('NVIDIA_API_KEYS',['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY'])}
for provider,(target,names) in families.items():
 if not provider_is_admitted_free(provider,a):continue
 vals=[]
 for n in names:
  v=os.getenv(n,'').strip()
  if v and v not in vals:vals.append(v)
 for v in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
  if v not in vals:vals.append(v)
 if vals:print('export %s=%s'%(target,shlex.quote(','.join(vals))))
PY
}

has_admitted_provider_key(){
  provider_admitted groq && [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]] && return 0
  provider_admitted mistral && [[ -n "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]] && return 0
  provider_admitted nvidia && [[ -n "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]] && return 0
  return 1
}

start_local_model(){
  curl -fsS --max-time 2 http://127.0.0.1:8088/health >/dev/null 2>&1 && return 0
  pgrep -f '[l]ocal_research_model_server.sh' >/dev/null 2>&1 && return 0
  [[ -x "$ROOT/tools/local_research_model_server.sh" ]] || chmod +x "$ROOT/tools/local_research_model_server.sh" 2>/dev/null || true
  [[ -f "$ROOT/tools/local_research_model_server.sh" ]] || return 0
  nohup bash "$ROOT/tools/local_research_model_server.sh" >"$STATE_DIR/local-model-bootstrap.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/local-model-bootstrap.pid"
}

start_dashboard(){
  local x="$ROOT/free swarm/evaluate.py"; [[ -f "$x" ]] || return 0
  pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1 || {
    nohup python3 "$x" --repo "$ROOT" --artifacts "$STATE_DIR" --watch --hours 24 --interval-seconds 60 >"$STATE_DIR/dashboard.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/dashboard.pid"; }
}

start_distillery(){
  local x="$ROOT/tools/run_research_distillery_local.py"; [[ -f "$x" ]] || x="$ROOT/tools/run_research_distillery_entry.py"
  pgrep -f '[r]un_research_distillery_(local|entry).py' >/dev/null 2>&1 || {
    nohup python3 "$x" --hours 24 --sleep-seconds 3 >"$STATE_DIR/distillery.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/distillery.pid"; }
}

start_forge(){
  local x="$ROOT/tools/run_free_evidence_forge.py"; [[ -f "$x" ]] || return 0
  pgrep -f '[r]un_free_evidence_forge.py' >/dev/null 2>&1 || {
    nohup python3 "$x" --hours 24 --sleep-seconds 20 --discovery-parallel 8 --local-parallel 4 --e2b-parallel 20 >"$STATE_DIR/forge.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/forge.pid"; }
}

write_provider_revocation_receipt(){
  local reason="$1" previous_digest="$2" current_digest="$3" pids_csv="$4"
  CLAY_REVOCATION_REASON="$reason" \
  CLAY_PREVIOUS_ADMISSION_DIGEST="$previous_digest" \
  CLAY_CURRENT_ADMISSION_DIGEST="$current_digest" \
  CLAY_REVOKED_SWARM_PIDS="$pids_csv" \
  python3 - <<'PY' >"$STATE_DIR/FREE_ONLY_PROVIDER_REVOCATION_RECEIPT.json.tmp"
import datetime,json,os
pids=[]
for raw in os.environ.get('CLAY_REVOKED_SWARM_PIDS','').split(','):
    try:pids.append(int(raw))
    except ValueError:pass
print(json.dumps({
    'schema':'FREE_ONLY_PROVIDER_REVOCATION_RECEIPT/v1',
    'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reason':os.environ.get('CLAY_REVOCATION_REASON','UNKNOWN'),
    'previous_process_admission_digest':os.environ.get('CLAY_PREVIOUS_ADMISSION_DIGEST',''),
    'current_process_admission_digest':os.environ.get('CLAY_CURRENT_ADMISSION_DIGEST',''),
    'terminated_swarm_pids':pids,
    'credential_values_observed':False,
    'action':'TERMINATE_STALE_CREDENTIAL_BEARING_SWARM_BEFORE_RESTART',
    'network_tripwire_scope':'SOURCE_GATE_ONLY_NOT_RUNTIME_MEASURED',
},sort_keys=True,separators=(',',':')))
PY
  mv "$STATE_DIR/FREE_ONLY_PROVIDER_REVOCATION_RECEIPT.json.tmp" "$STATE_DIR/FREE_ONLY_PROVIDER_REVOCATION_RECEIPT.json"
}

terminate_go_swarm(){
  local reason="$1" previous_digest="$2" current_digest="$3" pid pids_csv="" any
  local pids=()
  while IFS= read -r pid; do [[ -n "$pid" ]] && pids+=("$pid"); done < <(pgrep -f '[r]un_24h_entityos_swarm.py' || true)
  if (( ${#pids[@]} == 0 )); then
    rm -f "$SWARM_ADMISSION_DIGEST_FILE"
    return 0
  fi
  for pid in "${pids[@]}"; do
    [[ -z "$pids_csv" ]] || pids_csv+=","; pids_csv+="$pid"
    kill -TERM "$pid" 2>/dev/null || true
  done
  # Give cooperative async workers a bounded chance to exit, then fail closed.
  for _ in {1..20}; do
    any=0
    for pid in "${pids[@]}"; do kill -0 "$pid" 2>/dev/null && any=1 || true; done
    (( any )) || break
    sleep 0.05
  done
  for pid in "${pids[@]}"; do kill -KILL "$pid" 2>/dev/null || true; done
  write_provider_revocation_receipt "$reason" "$previous_digest" "$current_digest" "$pids_csv"
  rm -f "$SWARM_ADMISSION_DIGEST_FILE"
}

# Reconcile the exact admission snapshot that existed when the credential-bearing
# swarm was spawned. Missing provenance is fail-closed: a pre-v9/foreign child is
# terminated once and may be restarted only from the freshly sanitized environment.
# A partial revocation therefore cannot be masked by a different provider remaining
# FREE-admitted and credentialed.
stop_unadmitted_go_swarm(){
  local current_digest="" previous_digest=""
  current_digest="$(current_provider_admission_digest)" || current_digest=""
  [[ -r "$SWARM_ADMISSION_DIGEST_FILE" ]] && read -r previous_digest <"$SWARM_ADMISSION_DIGEST_FILE" || true
  if ! has_admitted_provider_key; then
    terminate_go_swarm "NO_CURRENT_ADMITTED_PROVIDER_CREDENTIAL" "$previous_digest" "$current_digest"
    return 0
  fi
  if [[ -z "$current_digest" ]]; then
    terminate_go_swarm "CURRENT_PROVIDER_ADMISSION_UNAVAILABLE" "$previous_digest" "$current_digest"
    return 0
  fi
  if pgrep -f '[r]un_24h_entityos_swarm.py' >/dev/null 2>&1 && [[ "$previous_digest" != "$current_digest" ]]; then
    terminate_go_swarm "PROVIDER_ADMISSION_CHANGED_OR_SPAWN_PROVENANCE_UNKNOWN" "$previous_digest" "$current_digest"
  fi
}

start_go_swarm_if_admitted(){
  [[ "${CLAY_FREE_ONLY_ATTESTED:-}" == "1" ]] || return 0
  has_admitted_provider_key || return 0
  pgrep -f '[r]un_24h_entityos_swarm.py' >/dev/null 2>&1 && return 0
  local now rem hours out admission_digest post_spawn_digest pid
  admission_digest="$(current_provider_admission_digest)" || return 0
  [[ "$admission_digest" =~ ^[0-9a-f]{64}$ ]] || return 0
  now=$(date +%s); rem=$((DEADLINE-now)); (( rem>0 )) || return 0
  hours=$(python3 - <<PY
print(max(0.01,$rem/3600.0))
PY
)
  out="$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  nohup python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$hours" --output-dir "$out" >"$STATE_DIR/swarm.log" 2>&1 </dev/null & pid=$!
  printf '%s\n' "$pid" >"$STATE_DIR/swarm.pid"
  printf '%s\n' "$admission_digest" >"$SWARM_ADMISSION_DIGEST_FILE"
  # Close the spawn race: if canonical admission moved while the process was being
  # created, do not leave the new child alive until the next 30s reconciliation.
  post_spawn_digest="$(current_provider_admission_digest)" || post_spawn_digest=""
  if [[ "$post_spawn_digest" != "$admission_digest" ]]; then
    terminate_go_swarm "PROVIDER_ADMISSION_CHANGED_DURING_SPAWN" "$admission_digest" "$post_spawn_digest"
  fi
}

while (( $(date +%s) < DEADLINE )); do
  clear_unadmitted_provider_secret_env
  typed_admission_compat_flags
  # Revoke stale inherited capabilities before loading any newly admitted secret
  # material or starting another child in this reconciliation cycle.
  stop_unadmitted_go_swarm
  load_admitted_secret_sources
  eval "$(normalize_provider_pool)"
  start_local_model
  start_dashboard
  start_distillery
  start_forge
  start_go_swarm_if_admitted
  NOW=$(date +%s); REMAINING=$((DEADLINE-NOW))
  python3 - <<PY >"$STATE_DIR/SUPERVISOR.json.tmp"
import datetime,json,os,subprocess,urllib.request
from free_provider_admission import admission_snapshot
snap=admission_snapshot()
def running(pattern):
 p=subprocess.run(['pgrep','-f',pattern],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);return bool(p.stdout.strip())
def local_health():
 try:
  with urllib.request.urlopen('http://127.0.0.1:8088/health',timeout=1.2) as r:return 200<=int(r.status)<300
 except Exception:return False
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v9','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'provider_admission':snap,'go_swarm_running':running('run_24h_entityos_swarm.py'),'local_research_model_ready':local_health(),'distillery_running':running('run_research_distillery_(local|entry).py'),'forge_running':running('run_free_evidence_forge.py'),'dashboard_running':running('free swarm/evaluate.py.*--watch'),'policy':'EXTERNAL_LLM_SWARM_ONLY_WHEN_TYPED_FREE_ADMITTED; BLOCKED_PROVIDER_CREDENTIALS_CLEARED_BY_NAME; CREDENTIAL_BEARING_SWARM_RESTARTED_ON_ANY_ADMISSION_SNAPSHOT_DRIFT; LIVE_PER_REQUEST_ADMISSION_RECHECK_REMAINS_REQUIRED; LOOPBACK_4B+PUBLIC_FORGE_CONTINUE_DURING_QUARANTINE'},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
  sleep 30
done
printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v9","state":"EXPIRED"}\n' >"$STATE_DIR/SUPERVISOR.json"
