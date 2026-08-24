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
LOGICAL_WORKERS="${CLAY_LOGICAL_WORKERS:-6000}"
HTTP_THREADS="${CLAY_SWARM_HTTP_THREADS:-256}"

provider_admitted(){ python3 "$ADMISSION_TOOL" --provider "$1" >/dev/null 2>&1; }
load_secret_file(){ local f="$1"; [[ -r "$f" ]] || return 0; set +x; set -a; source "$f"; set +a; }

load_admitted_secrets(){
  # Only execute after typed provider admission. Values are never logged.
  if provider_admitted groq || provider_admitted mistral || provider_admitted nvidia || provider_admitted openrouter; then
    load_secret_file /run/secrets/clay_provider.env
    load_secret_file /artifacts/.clay_provider.env
    load_secret_file /cache/clay_provider.env
    load_secret_file "$ROOT/.clay_provider.env"
    load_secret_file "$ROOT/research_entity/private/API_TOKENS.env"
    load_secret_file "$ROOT/research_entity/private/GROQ_API.env"
  fi
}

compat_flags(){
  unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
  local any=0
  if provider_admitted groq; then export CLAY_GROQ_FREE_ATTESTED=1; any=1; fi
  if provider_admitted mistral; then export CLAY_MISTRAL_FREE_ATTESTED=1; any=1; fi
  if provider_admitted nvidia; then export CLAY_NVIDIA_FREE_ATTESTED=1; any=1; fi
  if provider_admitted openrouter; then any=1; fi
  (( any )) && export CLAY_FREE_ONLY_ATTESTED=1 || true
}

normalize_provider_pool(){
python3 - <<'PY'
import os,shlex
families={
 'GROQ_API_KEYS':['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY'],
 'MISTRAL_API_KEYS':['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY'],
 'NVIDIA_API_KEYS':['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY']}
for target,names in families.items():
 vals=[]
 for n in names:
  v=os.getenv(n,'').strip()
  if v and v not in vals: vals.append(v)
 for v in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
  if v not in vals: vals.append(v)
 if vals: print('export %s=%s'%(target,shlex.quote(','.join(vals))))
PY
}

raise_shared_quota_ceiling(){
python3 - <<'PY'
import sqlite3
from pathlib import Path
p=Path('/artifacts/clay-entityos-swarm/provider_budget.sqlite3')
if not p.exists(): raise SystemExit(0)
con=sqlite3.connect(p,timeout=20)
for provider,cap in {'groq':128,'mistral':128,'nvidia':256,'openrouter':32}.items():
 con.execute('UPDATE provider_state SET max_inflight=? WHERE provider=?',(cap,provider))
con.commit();con.close()
PY
}

start_local_model(){
  curl -fsS --max-time 2 http://127.0.0.1:8088/health >/dev/null 2>&1 && return 0
  pgrep -f '[l]ocal_research_model_server.sh' >/dev/null 2>&1 && return 0
  [[ -f "$ROOT/tools/local_research_model_server.sh" ]] || return 0
  nohup bash "$ROOT/tools/local_research_model_server.sh" >"$STATE_DIR/local-model-bootstrap.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/local-model-bootstrap.pid"
}

start_dashboard(){
  local x="$ROOT/free swarm/evaluate.py"; [[ -f "$x" ]] || return 0
  pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1 || nohup python3 "$x" --repo "$ROOT" --artifacts "$STATE_DIR" --watch --hours 24 --interval-seconds 30 >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
}

start_distillery(){
  local x="$ROOT/tools/run_research_distillery_local.py"; [[ -f "$x" ]] || return 0
  pgrep -f '[r]un_research_distillery_local.py' >/dev/null 2>&1 || nohup python3 "$x" --hours 24 --sleep-seconds 1 >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
}

start_forge(){
  local x="$ROOT/tools/run_free_evidence_forge.py"; [[ -f "$x" ]] || return 0
  pgrep -f '[r]un_free_evidence_forge.py' >/dev/null 2>&1 || nohup python3 "$x" --hours 24 --sleep-seconds 3 --questions-per-cycle 24 --discovery-parallel 16 --candidates-per-cycle 32 --local-parallel 8 --e2b-parallel 20 >"$STATE_DIR/forge.log" 2>&1 </dev/null &
}

stop_legacy_go_swarm(){
  while IFS= read -r pid; do [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true; done < <(pgrep -f '[r]un_24h_entityos_swarm.py' || true)
}

start_6000(){
  pgrep -f '[r]un_6000_free_swarm_fast.py' >/dev/null 2>&1 && return 0
  local now rem hours out
  now=$(date +%s); rem=$((DEADLINE-now)); (( rem>0 )) || return 0
  hours=$(python3 - <<PY
print(max(0.01,$rem/3600.0))
PY
)
  out="$STATE_DIR/active-fabric6000-$(date -u +%Y%m%dT%H%M%SZ)"
  export CLAY_SWARM_HTTP_THREADS="$HTTP_THREADS"
  nohup python3 "$ROOT/tools/run_6000_free_swarm_fast.py" --logical-workers "$LOGICAL_WORKERS" --hours "$hours" --output-dir "$out" >"$STATE_DIR/swarm6000.log" 2>&1 </dev/null &
  echo $! >"$STATE_DIR/swarm6000.pid"
}

while (( $(date +%s) < DEADLINE )); do
  compat_flags
  load_admitted_secrets
  eval "$(normalize_provider_pool)"
  raise_shared_quota_ceiling || true
  start_local_model
  start_dashboard
  start_distillery
  start_forge
  stop_legacy_go_swarm
  start_6000
  NOW=$(date +%s); REMAINING=$((DEADLINE-NOW))
  python3 - <<PY >"$STATE_DIR/SUPERVISOR_6000.json.tmp"
import datetime,json,subprocess,urllib.request
from free_provider_admission import admission_snapshot
from free_swarm_quota import snapshot

def running(pattern):
 p=subprocess.run(['pgrep','-f',pattern],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);return bool(p.stdout.strip())
def health():
 try:
  with urllib.request.urlopen('http://127.0.0.1:8088/health',timeout=1.0) as r:return 200<=int(r.status)<300
 except Exception:return False
print(json.dumps({'schema':'CLAY_6000_SWARM_SUPERVISOR/v1','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remaining_seconds':$REMAINING,'logical_workers_requested':int('$LOGICAL_WORKERS'),'http_thread_pool':int('$HTTP_THREADS'),'provider_admission':admission_snapshot(),'fabric_running':running('run_6000_free_swarm_fast.py'),'distillery_running':running('run_research_distillery_local.py'),'forge_running':running('run_free_evidence_forge.py'),'dashboard_running':running('free swarm/evaluate.py.*--watch'),'local_model_ready':health(),'shared_quota':snapshot()},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR_6000.json.tmp" "$STATE_DIR/SUPERVISOR_6000.json"
  sleep 15
done
printf '{"schema":"CLAY_6000_SWARM_SUPERVISOR/v1","state":"EXPIRED"}\n' >"$STATE_DIR/SUPERVISOR_6000.json"
