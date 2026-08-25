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
HTTP_THREADS="${CLAY_SWARM_HTTP_THREADS:-512}"
ADMISSION_BINDING_FILE="$STATE_DIR/swarm6000.admission.binding"

# Initial probes are deliberately above the old local 12-slot bottleneck for
# empirically healthy NVIDIA, while 429-heavy lanes start lower and ramp by AIMD.
export CLAY_NVIDIA_INITIAL_CONCURRENCY="${CLAY_NVIDIA_INITIAL_CONCURRENCY:-24}"
export CLAY_GROQ_INITIAL_CONCURRENCY="${CLAY_GROQ_INITIAL_CONCURRENCY:-2}"
export CLAY_MISTRAL_INITIAL_CONCURRENCY="${CLAY_MISTRAL_INITIAL_CONCURRENCY:-4}"
export CLAY_OPENROUTER_INITIAL_CONCURRENCY="${CLAY_OPENROUTER_INITIAL_CONCURRENCY:-3}"
export OPENROUTER_SWARM_MODELS="${OPENROUTER_SWARM_MODELS:-openrouter/free}"

provider_admitted(){ python3 "$ADMISSION_TOOL" --provider "$1" >/dev/null 2>&1; }
load_secret_file(){ local f="$1"; [[ -r "$f" ]] || return 0; set +x; set -a; source "$f"; set +a; }

all_llm_providers_admitted(){
  provider_admitted groq &&
  provider_admitted mistral &&
  provider_admitted nvidia &&
  provider_admitted openrouter
}

# Historical/provider-specific helper retained for focused admission regression
# tests. The live supervisor path below no longer calls it to prepare its own
# environment: provider credentials are materialized only inside the dedicated
# Free-Swarm child process.
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
    unset OPENROUTER_API_KEY OPENROUTER_API_KEYS OPENROUTER2_API_KEY OPENROUTER3_API_KEY || true
    while IFS= read -r name; do case "$name" in OPENROUTER_API_KEY_*) unset "$name" || true ;; esac; done < <(compgen -v)
  fi
}

# Stronger control-plane fence: the long-lived supervisor and its local
# model/dashboard/distillery/forge children never retain external LLM secrets,
# even for currently admitted providers. Values are never expanded or logged.
clear_all_provider_secret_env(){
  local name
  unset \
    GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY \
    MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY \
    NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY \
    OPENROUTER_API_KEY OPENROUTER_API_KEYS OPENROUTER2_API_KEY OPENROUTER3_API_KEY \
    TOGETHER_API_KEY TOGETHER_API_KEYS || true
  while IFS= read -r name; do
    case "$name" in
      GROQ*KEY*|MISTRAL*KEY*|NVIDIA*KEY*|NGC*KEY*|OPENROUTER*KEY*|TOGETHER*KEY*) unset "$name" || true ;;
    esac
  done < <(compgen -v)
}

load_admitted_secrets(){
  # Kept as a deterministic compatibility helper for tests/forensics. Shared
  # bundles may contain multiple providers and are only opened under complete
  # provider-level admission. The active supervisor runtime does NOT invoke this
  # helper; the isolated swarm child uses free_swarm_exec_with_vault.py instead.
  if all_llm_providers_admitted; then
    load_secret_file /run/secrets/clay_provider.env
    load_secret_file /artifacts/.clay_provider.env
    load_secret_file /cache/clay_provider.env
    load_secret_file "$ROOT/.clay_provider.env"
    load_secret_file "$ROOT/research_entity/private/API_TOKENS.env"
  fi
  provider_admitted groq && load_secret_file "$ROOT/research_entity/private/GROQ_API.env" || true
}

compat_flags(){
  unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED CLAY_OPENROUTER_FREE_ATTESTED || true
  local any=0
  if provider_admitted groq; then export CLAY_GROQ_FREE_ATTESTED=1; any=1; fi
  if provider_admitted mistral; then export CLAY_MISTRAL_FREE_ATTESTED=1; any=1; fi
  if provider_admitted nvidia; then export CLAY_NVIDIA_FREE_ATTESTED=1; any=1; fi
  if provider_admitted openrouter; then export CLAY_OPENROUTER_FREE_ATTESTED=1; any=1; fi
  (( any )) && export CLAY_FREE_ONLY_ATTESTED=1 || true
}

normalize_provider_pool(){
python3 - <<'PY'
import os,shlex
families={
 'GROQ_API_KEYS':['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY'],
 'MISTRAL_API_KEYS':['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY'],
 'NVIDIA_API_KEYS':['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY'],
 'OPENROUTER_API_KEYS':['OPENROUTER_API_KEY','OPENROUTER2_API_KEY','OPENROUTER3_API_KEY'],
}
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

# Bind each external-provider child to the exact canonical provider admission,
# economic-provenance bytes and this credential-scope contract. The extra fields
# deliberately make a child created by the older broad-parent environment fail
# reconciliation on supervisor re-entry without exposing any secret value.
admission_capability_digest(){
python3 - <<'PY_INNER'
import hashlib,json
from pathlib import Path
from free_provider_admission import admission_snapshot, load_provider_admission, ProviderAdmissionError
snap=admission_snapshot()
try:
 admission=load_provider_admission()
except ProviderAdmissionError:
 admission=None
try:
 economic_sha=hashlib.sha256(Path('governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json').read_bytes()).hexdigest()
except OSError:
 economic_sha=None
material={
 "snapshot":snap,
 "validated_admission":admission,
 "economic_provenance_sha256":economic_sha,
 "credential_scope":"SWARM_CHILD_ONLY/v1",
}
raw=json.dumps(material,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
prefix="OK" if bool(snap.get("ok")) and admission is not None and economic_sha else "INVALID"
print(prefix+":"+hashlib.sha256(raw).hexdigest())
PY_INNER
}

prepare_provider_environment(){
  # Control-plane preparation only. Provider credentials are deliberately absent
  # from this process; compatibility flags derive from canonical typed admission
  # and the swarm child obtains candidate keys through the isolated vault loader.
  clear_all_provider_secret_env
  compat_flags
}

raise_shared_quota_ceiling(){
python3 - <<'PY'
import sqlite3
from pathlib import Path
p=Path('/artifacts/clay-entityos-swarm/provider_budget.sqlite3')
if not p.exists(): raise SystemExit(0)
con=sqlite3.connect(p,timeout=20)
for provider,cap in {'groq':128,'mistral':128,'nvidia':256,'openrouter':16}.items():
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
  local x="$ROOT/tools/run_free_evidence_forge_backfill.py"; [[ -f "$x" ]] || return 0
  # Supervisor 8.78 requires one backlog-first Forge authority. Retire both the
  # shell-capable legacy Forge and the pre-backfill safe daemon before starting
  # the backlog-first entrypoint, which delegates evaluation to the existing
  # bubblewrap-gated safe Forge implementation.
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < <(pgrep -f '[r]un_free_evidence_forge.py' || true)
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < <(pgrep -f '[r]un_free_evidence_forge_safe.py' || true)
  pgrep -f '[r]un_free_evidence_forge_backfill.py' >/dev/null 2>&1 && return 0
  nohup python3 "$x" --hours 24 --sleep-seconds 20 --questions-per-cycle 12 --backpressure-questions-per-cycle 0 --backpressure-threshold 64 --discovery-parallel 8 --local-parallel 4 --e2b-parallel 20 >"$STATE_DIR/forge.log" 2>&1 </dev/null &
  echo $! >"$STATE_DIR/forge.pid"
}

refresh_root_results(){
  local x="$ROOT/free swarm/update_root_results.py"; [[ -f "$x" ]] || return 0
  python3 "$x" --repo "$ROOT" --artifacts "$STATE_DIR" >/dev/null 2>&1 || true
}

stop_legacy_go_swarm(){
  while IFS= read -r pid; do [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true; done < <(pgrep -f '[r]un_24h_entityos_swarm.py' || true)
}

stop_6000(){
  local pid
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < <(pgrep -f '[r]un_6000_free_swarm_fast.py' || true)
  rm -f "$STATE_DIR/swarm6000.pid"
}

reconcile_6000_admission(){
  local current bound
  current="$(admission_capability_digest)"
  if pgrep -f '[r]un_6000_free_swarm_fast.py' >/dev/null 2>&1; then
    bound="$(cat "$ADMISSION_BINDING_FILE" 2>/dev/null || true)"
    if [[ -z "$bound" || "$bound" != "$current" || "$current" == INVALID:* ]]; then
      stop_6000
      rm -f "$ADMISSION_BINDING_FILE"
    fi
  elif [[ "$current" == INVALID:* ]]; then
    rm -f "$ADMISSION_BINDING_FILE"
  fi
}

start_6000(){
  pgrep -f '[r]un_6000_free_swarm_fast.py' >/dev/null 2>&1 && return 0
  local before after post now rem hours out pid tmp vault_exec
  before="$(admission_capability_digest)"
  [[ "$before" == OK:* ]] || return 0

  # Rebuild a credential-blind control environment immediately before spawn. If
  # canonical admission/economic provenance moves during preparation, abort and
  # let the next reconciliation cycle retry from the new state.
  prepare_provider_environment
  after="$(admission_capability_digest)"
  [[ "$after" == "$before" && "$after" == OK:* ]] || return 0
  [[ "${CLAY_FREE_ONLY_ATTESTED:-}" == "1" ]] || return 0
  vault_exec="$ROOT/tools/free_swarm_exec_with_vault.py"
  [[ -f "$vault_exec" ]] || return 0

  now=$(date +%s); rem=$((DEADLINE-now)); (( rem>0 )) || return 0
  hours=$(python3 - <<PY
print(max(0.01,$rem/3600.0))
PY
)
  out="$STATE_DIR/active-fabric6000-v2-$(date -u +%Y%m%dT%H%M%SZ)"
  export CLAY_SWARM_HTTP_THREADS="$HTTP_THREADS"
  nohup python3 "$vault_exec" python3 "$ROOT/tools/run_6000_free_swarm_fast.py" --logical-workers "$LOGICAL_WORKERS" --hours "$hours" --output-dir "$out" >"$STATE_DIR/swarm6000.log" 2>&1 </dev/null &
  pid=$!
  echo "$pid" >"$STATE_DIR/swarm6000.pid"
  tmp="$ADMISSION_BINDING_FILE.tmp"
  printf '%s\n' "$after" >"$tmp"
  mv "$tmp" "$ADMISSION_BINDING_FILE"

  # Close the spawn race. The request path independently revalidates concrete
  # route/credential economic authority before provider network I/O; this control
  # plane also removes the child if its admission/provenance binding moved.
  post="$(admission_capability_digest)"
  if [[ "$post" != "$after" || "$post" == INVALID:* ]]; then
    kill "$pid" 2>/dev/null || true
    rm -f "$STATE_DIR/swarm6000.pid" "$ADMISSION_BINDING_FILE"
  fi
}

while (( $(date +%s) < DEADLINE )); do
  prepare_provider_environment
  raise_shared_quota_ceiling || true
  start_local_model
  start_dashboard
  start_distillery
  start_forge
  stop_legacy_go_swarm
  reconcile_6000_admission
  start_6000
  refresh_root_results

  NOW=$(date +%s); REMAINING=$((DEADLINE-NOW))
  python3 - <<PY >"$STATE_DIR/SUPERVISOR_6000.json.tmp"
import datetime,json,subprocess,urllib.request
from pathlib import Path
from free_provider_admission import admission_snapshot
from free_swarm_quota import snapshot

def running(pattern):
 p=subprocess.run(['pgrep','-f',pattern],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 return bool(p.stdout.strip())
def health():
 try:
  with urllib.request.urlopen('http://127.0.0.1:8088/health',timeout=1.0) as r:return 200<=int(r.status)<300
 except Exception:return False
def latest_fabric():
 xs=sorted(Path('$STATE_DIR').glob('active-fabric6000-v2-*/status.json'),key=lambda p:p.stat().st_mtime if p.exists() else 0,reverse=True)
 if not xs:return {}
 try:return json.loads(xs[0].read_text())
 except Exception:return {}
fabric=latest_fabric()
try: admission_binding=Path('$ADMISSION_BINDING_FILE').read_text().strip()
except OSError: admission_binding=None
print(json.dumps({
 'schema':'CLAY_6000_SWARM_SUPERVISOR/v4',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'remaining_seconds':$REMAINING,
 'logical_workers_requested':int('$LOGICAL_WORKERS'),
 'http_thread_pool':int('$HTTP_THREADS'),
 'provider_admission':admission_snapshot(),
 'provider_credential_scope':'SWARM_CHILD_ONLY',
 'fabric_admission_binding':admission_binding,
 'fabric_running':running('run_6000_free_swarm_fast.py'),
 'distillery_running':running('run_research_distillery_local.py'),
 'forge_running':running('run_free_evidence_forge_backfill.py'),
 'legacy_safe_forge_running':running('run_free_evidence_forge_safe.py'),
 'legacy_forge_running':running('run_free_evidence_forge.py'),
 'forge_entrypoint':'tools/run_free_evidence_forge_backfill.py',
 'forge_backpressure_policy':'BACKLOG_FIRST; DISCOVERY_ZERO_WHILE_PRESSURE_GTE_64',
 'forge_execution_policy':'CLAY_FORGE_EXECUTION_ADMISSION/v1',
 'dashboard_running':running('free swarm/evaluate.py.*--watch'),
 'local_model_ready':health(),
 'fabric':fabric,
 'shared_quota':snapshot(),
 'revocation_policy':'CREDENTIAL_BLIND_CONTROL_PARENT; SWARM_CHILD_ONLY_SECRET_SCOPE; RESTART_CHILD_ON_ADMISSION_OR_ECONOMIC_PROVENANCE_BINDING_CHANGE; REQUEST_PATH_REVALIDATES_CURRENT_ROUTE_CREDENTIAL_AUTHORITY_BEFORE_NETWORK; LEGACY_FORGE_TERMINATED; BACKLOG_FIRST_SAFE_FORGE_ONLY'
},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR_6000.json.tmp" "$STATE_DIR/SUPERVISOR_6000.json"
  sleep 15
done
printf '{"schema":"CLAY_6000_SWARM_SUPERVISOR/v4","state":"EXPIRED","provider_credential_scope":"SWARM_CHILD_ONLY"}\n' >"$STATE_DIR/SUPERVISOR_6000.json"
