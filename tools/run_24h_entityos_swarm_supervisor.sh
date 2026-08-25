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
SWARM_ADMISSION_BINDING_FILE="$STATE_DIR/swarm-admission-binding.sha256"
FORGE_DISTILLERY_STATUS="$STATE_DIR/forge-distillery-ingest.json"

provider_admitted(){ python3 "$ADMISSION_TOOL" --provider "$1" >/dev/null 2>&1; }

current_provider_admission_binding(){
  local snapshot
  snapshot="$(python3 "$ADMISSION_TOOL" --json 2>/dev/null)" || return 1
  [[ -n "$snapshot" ]] || return 1
  printf '%s' "$snapshot" | sha256sum | awk '{print $1}'
}

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
  # Supervisor 8.78: make the already-existing historical backlog-first entrypoint
  # the single active Forge authority instead of running a second evaluator.
  local x="$ROOT/tools/run_free_evidence_forge_backfill.py"; [[ -f "$x" ]] || return 0
  pgrep -f '[r]un_free_evidence_forge_backfill.py' >/dev/null 2>&1 && return 0
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < <(pgrep -f '[r]un_free_evidence_forge_safe(_871)?\.py' || true)
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < <(pgrep -f '[r]un_free_evidence_forge.py' || true)
  nohup python3 "$x" --hours 24 --sleep-seconds 20 --discovery-parallel 8 --local-parallel 4 --e2b-parallel 20 >"$STATE_DIR/forge.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/forge.pid"
}

run_forge_distillery_bridge(){
  local x="$ROOT/tools/ingest_forge_accepts_into_distillery.py"
  local evaluations="$STATE_DIR/forge/architecture_delta_evaluations.jsonl"
  local db="$STATE_DIR/distillery/distillery.sqlite3"
  local tmp="${FORGE_DISTILLERY_STATUS}.tmp"
  [[ -f "$x" && -f "$evaluations" && -f "$db" ]] || return 0
  if python3 "$x" --forge-evaluations "$evaluations" --distillery-db "$db" >"$tmp" 2>"$STATE_DIR/forge-distillery-ingest.err"; then
    mv "$tmp" "$FORGE_DISTILLERY_STATUS"
  else
    rm -f "$tmp"
  fi
}

start_go_swarm_if_admitted(){
  [[ "${CLAY_FREE_ONLY_ATTESTED:-}" == "1" ]] || return 0
  has_admitted_provider_key || return 0
  pgrep -f '[r]un_24h_entityos_swarm.py' >/dev/null 2>&1 && return 0
  local now rem hours out admission_binding child_pid swarm_entry
  swarm_entry="$ROOT/tools/run_24h_entityos_swarm_backpressured.py"
  [[ -f "$swarm_entry" ]] || return 0
  admission_binding="$(current_provider_admission_binding)" || return 0
  now=$(date +%s); rem=$((DEADLINE-now)); (( rem>0 )) || return 0
  hours=$(python3 - <<PY
print(max(0.01,$rem/3600.0))
PY
)
  out="$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  nohup python3 "$swarm_entry" --hours "$hours" --output-dir "$out" >"$STATE_DIR/swarm.log" 2>&1 </dev/null &
  child_pid=$!
  printf '%s\n' "$child_pid" >"$STATE_DIR/swarm.pid"
  printf '%s\n' "$admission_binding" >"${SWARM_ADMISSION_BINDING_FILE}.tmp"
  mv "${SWARM_ADMISSION_BINDING_FILE}.tmp" "$SWARM_ADMISSION_BINDING_FILE"
}

stop_unadmitted_go_swarm(){
  local current_binding="" spawned_binding="" must_stop=0
  if has_admitted_provider_key; then
    current_binding="$(current_provider_admission_binding)" || must_stop=1
    if (( ! must_stop )); then
      if [[ -r "$SWARM_ADMISSION_BINDING_FILE" ]]; then
        IFS= read -r spawned_binding < "$SWARM_ADMISSION_BINDING_FILE" || true
        [[ -n "$spawned_binding" && "$spawned_binding" == "$current_binding" ]] || must_stop=1
      else
        must_stop=1
      fi
    fi
  else
    must_stop=1
  fi
  if (( must_stop )); then
    while IFS= read -r pid; do
      [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
    done < <(pgrep -f '[r]un_24h_entityos_swarm.py' || true)
    rm -f "$SWARM_ADMISSION_BINDING_FILE" "${SWARM_ADMISSION_BINDING_FILE}.tmp"
  fi
}

while (( $(date +%s) < DEADLINE )); do
  clear_unadmitted_provider_secret_env
  typed_admission_compat_flags
  load_admitted_secret_sources
  eval "$(normalize_provider_pool)"
  start_local_model
  start_dashboard
  start_distillery
  start_forge
  run_forge_distillery_bridge
  stop_unadmitted_go_swarm
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
def load_json(path):
 try:
  with open(path,'r',encoding='utf-8') as f:return json.load(f)
 except Exception:return None
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v8','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'provider_admission':snap,'go_swarm_running':running('run_24h_entityos_swarm.py'),'local_research_model_ready':local_health(),'distillery_running':running('run_research_distillery_(local|entry).py'),'forge_running':running('run_free_evidence_forge_backfill.py'),'forge_distillery_bridge':load_json('$FORGE_DISTILLERY_STATUS'),'conversion_backpressure':load_json('$STATE_DIR/control/conversion_backpressure.json'),'dashboard_running':running('free swarm/evaluate.py.*--watch'),'policy':'EXTERNAL_LLM_SWARM_ONLY_WHEN_TYPED_FREE_ADMITTED; BLOCKED_PROVIDER_CREDENTIALS_CLEARED_BY_NAME_BEFORE_CHILD_START; RUNNING_SWARM_BOUND_TO_EXACT_VALIDATED_ADMISSION_AND_RESTARTED_ON_DRIFT; CONVERSION_BEFORE_SCALE_BACKPRESSURE_REQUIRED; BACKLOG_FIRST_HISTORICAL_FORGE_IS_SINGLE_ACTIVE_FORGE; SAFE_FORGE_REQUIRES_NO_SHELL_SECRET_FREE_ISOLATED_EXECUTOR; LOOPBACK_4B+PUBLIC_FORGE_CONTINUE_DURING_QUARANTINE'},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
  sleep 30
done
printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v8","state":"EXPIRED"}\n' >"$STATE_DIR/SUPERVISOR.json"
