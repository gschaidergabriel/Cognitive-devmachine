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
SWARM_ENTRY="$ROOT/tools/run_24h_entityos_swarm_entry.py"
export CLAY_PROVIDER_ADMISSION_FILE="$ADMISSION_FILE"

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

provider_in_csv() {
  local provider="$1" admitted_csv="$2"
  case ",$admitted_csv," in
    *",$provider,"*) return 0 ;;
    *) return 1 ;;
  esac
}

provider_still_admitted() {
  local provider="$1"
  python3 "$ADMISSION_CHECKER" "$ADMISSION_FILE" --provider "$provider" >/dev/null 2>&1
}

load_provider_secret_sources() {
  local provider="$1"
  # Last deterministic control-plane check before touching this provider's secret files.
  provider_still_admitted "$provider" || return 92
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
    *) return 91 ;;
  esac
}

# Preserve the historical function name because deterministic source-fence tests use it,
# but make the behavior provider-scoped. Only providers already admitted FREE may source
# their corresponding secret family.
load_admitted_provider_secret_sources() {
  local admitted_csv="$1" provider
  IFS=',' read -r -a providers <<< "$admitted_csv"
  for provider in "${providers[@]}"; do
    [[ -n "$provider" ]] || continue
    load_provider_secret_sources "$provider"
  done
}

# Remove inherited credential variables for blocked providers by NAME only. This occurs
# before any value expansion, so a parent shell cannot bypass typed admission by exporting
# a key in advance.
unset_nonadmitted_provider_environment() {
  local admitted_csv="$1" provider prefix name
  for provider in groq mistral nvidia; do
    provider_in_csv "$provider" "$admitted_csv" && continue
    case "$provider" in
      groq) prefix="GROQ" ;;
      mistral) prefix="MISTRAL" ;;
      nvidia) prefix="NVIDIA" ;;
    esac
    while IFS= read -r name; do
      case "$name" in
        ${prefix}_API_KEY|${prefix}_API_KEYS|${prefix}_API_KEY_*|${prefix}[0-9]*_API_KEY|${prefix}[0-9]*_API_KEYS)
          unset "$name" ;;
      esac
    done < <(compgen -v)
    if [[ "$provider" == "nvidia" ]]; then
      unset NGC_API_KEY NVIDIA_NIM_API_KEY || true
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

has_provider_key() {
  [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]]
}

typed_admitted_providers() {
  [[ -r "$ADMISSION_CHECKER" ]] || return 1
  python3 "$ADMISSION_CHECKER" "$ADMISSION_FILE"
}

typed_free_admission_ready() {
  typed_admitted_providers >/dev/null 2>&1
}

derive_runtime_attestation_from_typed_admission() {
  local admitted_csv="$1"
  unset CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
  export CLAY_FREE_ONLY_ATTESTED=1
  provider_in_csv groq "$admitted_csv" && export CLAY_GROQ_FREE_ATTESTED=1
  provider_in_csv mistral "$admitted_csv" && export CLAY_MISTRAL_FREE_ATTESTED=1
  provider_in_csv nvidia "$admitted_csv" && export CLAY_NVIDIA_FREE_ATTESTED=1
}

write_presecret_state() {
  local reason="$1"
  python3 - "$STATE_DIR/SUPERVISOR.json.tmp" "$ADMISSION_FILE" "$reason" <<'PY'
import datetime,json,os,sys
out,admission_file,reason=sys.argv[1:]
payload={
 'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v7',
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
 'distillery_reason':'FENCED_UNTIL_ITS_OPENROUTER_AND_OTHER_PROVIDER_PATHS_HAVE_TYPED_FREE_ADMISSION',
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

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  if ! ADMITTED_PROVIDERS="$(typed_admitted_providers 2>/dev/null)"; then
    write_presecret_state "TYPED_CONTROL_PLANE_FREE_ADMISSION_MISSING_INVALID_OR_NONFREE"
    sleep 60
    continue
  fi

  unset_nonadmitted_provider_environment "$ADMITTED_PROVIDERS"
  derive_runtime_attestation_from_typed_admission "$ADMITTED_PROVIDERS"
  if ! load_admitted_provider_secret_sources "$ADMITTED_PROVIDERS"; then
    write_presecret_state "TYPED_PROVIDER_ADMISSION_CHANGED_BEFORE_SECRET_LOOKUP"
    sleep 60
    continue
  fi
  # shellcheck disable=SC2046
  eval "$(normalize_provider_pool)"

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
}
counts={
 'groq': nset(*split('GROQ_API_KEYS'),os.getenv('GROQ_API_KEY')),
 'mistral': nset(*split('MISTRAL_API_KEYS'),os.getenv('MISTRAL_API_KEY')),
 'nvidia': nset(*split('NVIDIA_API_KEYS'),os.getenv('NVIDIA_API_KEY'),os.getenv('NGC_API_KEY'),os.getenv('NVIDIA_NIM_API_KEY')),
}
p=pathlib.Path(os.environ['CLAY_PROVIDER_ADMISSION_FILE'])
digest=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else 'UNAVAILABLE'
print(json.dumps({
 'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v7',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'repo_root':os.getcwd(),
 'remaining_seconds':$REMAINING,
 'typed_provider_admission':'PASS_PROVIDER_SCOPED_FREE_SUBSET',
 'admitted_providers':'$ADMITTED_PROVIDERS'.split(','),
 'admission_sha256':digest,
 'free_only_attested':True,
 'provider_credentials_present':providers,
 'provider_credential_counts':counts,
 'dashboard_watch':True,
 'research_distillery':False,
 'distillery_reason':'FENCED_UNTIL_ITS_OPENROUTER_AND_OTHER_PROVIDER_PATHS_HAVE_TYPED_FREE_ADMISSION',
 'swarm_entry':'run_24h_entityos_swarm_entry.py'
},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  CURRENT_ADMITTED="$(typed_admitted_providers 2>/dev/null || true)"
  if [[ "$CURRENT_ADMITTED" == "$ADMITTED_PROVIDERS" ]] && has_provider_key; then
    exec python3 "$SWARM_ENTRY" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v7","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_ADMISSION_OR_USABLE_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
