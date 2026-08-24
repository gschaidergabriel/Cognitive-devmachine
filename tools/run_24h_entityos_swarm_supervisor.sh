#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"
ADMISSION_CHECKER="$ROOT/tools/free_provider_admission.py"

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

load_provider_secret_sources() {
  local provider="$1"
  case "$provider" in
    groq)
      load_secret_file /run/secrets/clay_provider_groq.env
      load_secret_file /artifacts/.clay_provider_groq.env
      load_secret_file /cache/clay_provider_groq.env
      load_secret_file "$ROOT/.clay_provider_groq.env"
      load_secret_file "$ROOT/research_entity/private/GROQ_API.env"
      ;;
    mistral)
      load_secret_file /run/secrets/clay_provider_mistral.env
      load_secret_file /artifacts/.clay_provider_mistral.env
      load_secret_file /cache/clay_provider_mistral.env
      load_secret_file "$ROOT/.clay_provider_mistral.env"
      load_secret_file "$ROOT/research_entity/private/MISTRAL_API.env"
      ;;
    nvidia)
      load_secret_file /run/secrets/clay_provider_nvidia.env
      load_secret_file /artifacts/.clay_provider_nvidia.env
      load_secret_file /cache/clay_provider_nvidia.env
      load_secret_file "$ROOT/.clay_provider_nvidia.env"
      load_secret_file "$ROOT/research_entity/private/NVIDIA_API.env"
      ;;
    # OpenRouter/Tavily/Exa are consumed through rae_secret_loader inside the
    # distillery. Their entrypoint independently rechecks typed admission before
    # get_secret(), so no catch-all token file is sourced here.
    openrouter|tavily|exa) ;;
    *) return 91 ;;
  esac
}

typed_admitted_providers() {
  PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY'
from free_provider_admission import ProviderAdmissionError, admitted_provider_names, load_provider_admission
try:
    admission = load_provider_admission()
except ProviderAdmissionError:
    raise SystemExit(4)
names = admitted_provider_names(admission)
if not names:
    raise SystemExit(3)
print(",".join(names))
PY
}

provider_is_still_admitted() {
  python3 "$ADMISSION_CHECKER" --provider "$1" >/dev/null 2>&1
}

provider_in_csv() {
  local provider="$1" csv="$2"
  case ",$csv," in
    *",$provider,"*) return 0 ;;
    *) return 1 ;;
  esac
}

unset_provider_environment_without_reading_values() {
  local provider="$1" name
  while IFS= read -r name; do
    case "$provider:$name" in
      groq:GROQ_API_KEY|groq:GROQ_API_KEYS|groq:GROQ_API_KEY_*|groq:GROQ[0-9]*_API_KEY|groq:GROQ[0-9]*_API_KEYS|\
      mistral:MISTRAL_API_KEY|mistral:MISTRAL_API_KEYS|mistral:MISTRAL_API_KEY_*|mistral:MISTRAL[0-9]*_API_KEY|mistral:MISTRAL[0-9]*_API_KEYS|\
      nvidia:NVIDIA_API_KEY|nvidia:NVIDIA_API_KEYS|nvidia:NVIDIA_API_KEY_*|nvidia:NVIDIA[0-9]*_API_KEY|nvidia:NVIDIA[0-9]*_API_KEYS|nvidia:NVIDIA_NIM_API_KEY|nvidia:NGC_API_KEY|\
      openrouter:OPENROUTER_API_KEY|openrouter:OPENROUTER_API_KEYS|openrouter:OPENROUTER_API_KEY_*|\
      tavily:TAVILY_API_KEY|tavily:TAVILY_API_KEYS|tavily:TAVILY_API_KEY_*|\
      exa:EXA_API_KEY|exa:EXA_API_KEYS|exa:EXA_API_KEY_*)
        unset "$name"
        ;;
    esac
  done < <(compgen -v)
}

sanitize_nonadmitted_provider_environment() {
  local admitted_csv="$1" provider
  for provider in groq mistral nvidia openrouter tavily exa; do
    if ! provider_in_csv "$provider" "$admitted_csv"; then
      unset_provider_environment_without_reading_values "$provider"
    fi
  done
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

has_swarm_provider_key() {
  [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]]
}

derive_runtime_attestation_from_typed_admission() {
  local admitted_csv="$1" provider
  unset CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
  export CLAY_FREE_ONLY_ATTESTED=1
  for provider in groq mistral nvidia; do
    if provider_in_csv "$provider" "$admitted_csv"; then
      case "$provider" in
        groq) export CLAY_GROQ_FREE_ATTESTED=1 ;;
        mistral) export CLAY_MISTRAL_FREE_ATTESTED=1 ;;
        nvidia) export CLAY_NVIDIA_FREE_ATTESTED=1 ;;
      esac
    fi
  done
}

write_presecret_state() {
  local reason="$1"
  python3 - "$STATE_DIR/SUPERVISOR.json.tmp" "$reason" <<'PY'
import datetime,json,os,sys
out,reason=sys.argv[1:]
payload={
 'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v7',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repo_root':os.getcwd(),
 'state':'WAITING_FOR_TYPED_FREE_PROVIDER_ADMISSION',
 'reason':reason,
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
  if ! pgrep -f '[r]un_research_distillery_entry.py' >/dev/null 2>&1; then
    nohup python3 "$runner" --hours 24 --sleep-seconds 3 \
      >"$STATE_DIR/distillery.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/distillery.pid"
  fi
}

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  if ! ADMITTED_PROVIDERS="$(typed_admitted_providers 2>/dev/null)"; then
    sanitize_nonadmitted_provider_environment ""
    unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
    write_presecret_state "TYPED_CONTROL_PLANE_FREE_ADMISSION_MISSING_INVALID_OR_ZERO_ADMITTED"
    sleep 60
    continue
  fi

  sanitize_nonadmitted_provider_environment "$ADMITTED_PROVIDERS"
  derive_runtime_attestation_from_typed_admission "$ADMITTED_PROVIDERS"

  IFS=',' read -r -a admitted_array <<< "$ADMITTED_PROVIDERS"
  for provider in "${admitted_array[@]}"; do
    # Recheck immediately before crossing that provider's secret-file boundary.
    if provider_is_still_admitted "$provider"; then
      load_provider_secret_sources "$provider"
    fi
  done

  # If authority changed during secret loading, remove any now-nonadmitted provider
  # variables before any value normalization or downstream process launch.
  if ! CURRENT_ADMITTED="$(typed_admitted_providers 2>/dev/null)"; then
    sanitize_nonadmitted_provider_environment ""
    write_presecret_state "TYPED_CONTROL_PLANE_FREE_ADMISSION_REVOKED_DURING_SECRET_STAGE"
    sleep 60
    continue
  fi
  ADMITTED_PROVIDERS="$CURRENT_ADMITTED"
  sanitize_nonadmitted_provider_environment "$ADMITTED_PROVIDERS"
  derive_runtime_attestation_from_typed_admission "$ADMITTED_PROVIDERS"

  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"
  start_distillery

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  python3 - "$STATE_DIR/SUPERVISOR.json.tmp" "$ADMITTED_PROVIDERS" "$REMAINING" <<'PY'
import datetime,json,os,sys
out,admitted_csv,remaining=sys.argv[1:]
admitted=set(x for x in admitted_csv.split(',') if x)
split=lambda x:[v.strip() for v in os.getenv(x,'').replace(';',',').split(',') if v.strip()]
def nset(*vals): return len(set(v for v in vals if v))
def present(provider):
    if provider not in admitted: return False
    if provider=='groq': return bool(os.getenv('GROQ_API_KEY') or split('GROQ_API_KEYS'))
    if provider=='mistral': return bool(os.getenv('MISTRAL_API_KEY') or split('MISTRAL_API_KEYS'))
    if provider=='nvidia': return bool(os.getenv('NVIDIA_API_KEY') or split('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY'))
    if provider=='openrouter': return bool(os.getenv('OPENROUTER_API_KEY'))
    if provider=='tavily': return bool(os.getenv('TAVILY_API_KEY'))
    if provider=='exa': return bool(os.getenv('EXA_API_KEY'))
    return False
providers={p:present(p) for p in ('groq','mistral','nvidia','openrouter','tavily','exa')}
counts={
 'groq': nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY')) if 'groq' in admitted else 0,
 'mistral': nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY')) if 'mistral' in admitted else 0,
 'nvidia': nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY')) if 'nvidia' in admitted else 0,
}
print(json.dumps({
 'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v7',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repo_root':os.getcwd(),
 'remaining_seconds':int(remaining),
 'typed_provider_admission':'PASS_PROVIDER_SCOPED_FREE',
 'admitted_providers':sorted(admitted),
 'free_only_attested':True,
 'provider_credentials_present':providers,
 'provider_credential_counts':counts,
 'dashboard_watch':True,
 'research_distillery':True,
 'distillery_entrypoint':'run_research_distillery_entry.py'
},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  # The Python driver/controller independently revalidates typed admission before
  # collect_keys(), catalog I/O and chat I/O.
  if has_swarm_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v7","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_ADMISSION_OR_USABLE_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
