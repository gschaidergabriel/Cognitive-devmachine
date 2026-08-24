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

provider_admitted(){ python3 "$ADMISSION_TOOL" --provider "$1" >/dev/null 2>&1; }


# Resolve canonical admission before touching provider-secret values. Blocked
# credentials are removed by variable name only, so local model/distillery/forge
# children cannot inherit an unadmitted provider capability accidentally.
clear_unadmitted_provider_secret_env(){
  local name
  if ! provider_admitted groq; then
    unset GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY || true
  fi
  if ! provider_admitted mistral; then
    unset MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY || true
  fi
  if ! provider_admitted nvidia; then
    unset NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NGC_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY || true
  fi
  if ! provider_admitted openrouter; then
    unset OPENROUTER_API_KEY || true
  fi
  # Tavily/Exa are not members of the current typed FREE provider authority.
  unset TAVILY_API_KEY EXA_API_KEY || true
  while IFS= read -r name; do
    case "$name" in
      GROQ_API_KEY_*) provider_admitted groq || unset "$name" || true ;;
      MISTRAL_API_KEY_*) provider_admitted mistral || unset "$name" || true ;;
      NVIDIA_API_KEY_*) provider_admitted nvidia || unset "$name" || true ;;
      OPENROUTER_API_KEY_*) provider_admitted openrouter || unset "$name" || true ;;
    esac
  done < <(compgen -v)
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
provider_secret_name_allowed(){
  local provider="$1" name="$2"
  case "$provider:$name" in
    groq:GROQ_API_KEY|groq:GROQ_API_KEYS|groq:GROQ_API_KEY_*|groq:GROQ2_API_KEY|groq:GROQ3_API_KEY) return 0 ;;
    mistral:MISTRAL_API_KEY|mistral:MISTRAL_API_KEYS|mistral:MISTRAL_API_KEY_*|mistral:MISTRAL2_API_KEY|mistral:MISTRAL3_API_KEY) return 0 ;;
    nvidia:NVIDIA_API_KEY|nvidia:NVIDIA_API_KEYS|nvidia:NVIDIA_API_KEY_*|nvidia:NVIDIA2_API_KEY|nvidia:NVIDIA3_API_KEY|nvidia:NGC_API_KEY|nvidia:NVIDIA_NIM_API_KEY) return 0 ;;
    openrouter:OPENROUTER_API_KEY) return 0 ;;
    *) return 1 ;;
  esac
}

# Secret files are provider-scoped data, never executable shell. The caller must
# have already established typed FREE admission for the exact provider.
load_provider_secret_file(){
  local provider="$1" f="$2" raw name value
  [[ -r "$f" ]] || return 0
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    raw="${raw%$'\r'}"
    [[ -z "$raw" || "$raw" == \#* ]] && continue
    [[ "$raw" == export\ * ]] && raw="${raw#export }"
    [[ "$raw" == *=* ]] || continue
    name="${raw%%=*}"; value="${raw#*=}"
    [[ "$name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    provider_secret_name_allowed "$provider" "$name" || continue
    if [[ ${#value} -ge 2 ]]; then
      if [[ "$value" == \"*\" && "$value" == *\" ]]; then value="${value:1:${#value}-2}";
      elif [[ "$value" == \'*\' && "$value" == *\' ]]; then value="${value:1:${#value}-2}"; fi
    fi
    export "$name=$value"
  done < "$f"
}

# Never open generic mixed-provider bundles: that would materialize secret values
# for providers whose cost/admission class may still be blocked. Existing directly
# inherited values survive only when that provider is canonically admitted.
load_admitted_secret_sources(){
  provider_admitted groq && load_provider_secret_file groq "$ROOT/research_entity/private/GROQ_API.env" || true
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

start_go_swarm_if_admitted(){
  [[ "${CLAY_FREE_ONLY_ATTESTED:-}" == "1" ]] || return 0
  has_admitted_provider_key || return 0
  pgrep -f '[r]un_24h_entityos_swarm.py' >/dev/null 2>&1 && return 0
  local now rem hours out
  now=$(date +%s); rem=$((DEADLINE-now)); (( rem>0 )) || return 0
  hours=$(python3 - <<PY
print(max(0.01,$rem/3600.0))
PY
)
  out="$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  nohup python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$hours" --output-dir "$out" >"$STATE_DIR/swarm.log" 2>&1 </dev/null & echo $! >"$STATE_DIR/swarm.pid"
}

stop_unadmitted_go_swarm(){
  if ! has_admitted_provider_key; then
    pgrep -f '[r]un_24h_entityos_swarm.py' | while read -r pid; do kill "$pid" 2>/dev/null || true; done
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
print(json.dumps({'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v8','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo_root':os.getcwd(),'remaining_seconds':$REMAINING,'provider_admission':snap,'go_swarm_running':running('run_24h_entityos_swarm.py'),'local_research_model_ready':local_health(),'distillery_running':running('run_research_distillery_(local|entry).py'),'forge_running':running('run_free_evidence_forge.py'),'dashboard_running':running('free swarm/evaluate.py.*--watch'),'policy':'EXTERNAL_LLM_SWARM_ONLY_WHEN_TYPED_FREE_ADMITTED; LOOPBACK_4B+PUBLIC_FORGE_CONTINUE_DURING_QUARANTINE'},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
  sleep 30
done
printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v8","state":"EXPIRED"}\n' >"$STATE_DIR/SUPERVISOR.json"
