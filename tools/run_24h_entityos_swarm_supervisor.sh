#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
ADMISSION_TOOL="$ROOT/tools/free_swarm_provider_admission.py"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"

# Provider keys may already exist in the parent environment. Before typed
# admission we neither inspect nor forward them to policy/dashboard subprocesses.
# After admission, unadmitted provider variables are dropped without reading them.
drop_unadmitted_provider_env() {
  if ! provider_is_admitted groq; then
    unset GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY || true
  fi
  if ! provider_is_admitted mistral; then
    unset MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY || true
  fi
  if ! provider_is_admitted nvidia; then
    unset NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY || true
  fi
  unset CLAY_FREE_ONLY_ATTESTED CLAY_GROQ_FREE_ATTESTED CLAY_MISTRAL_FREE_ATTESTED CLAY_NVIDIA_FREE_ATTESTED || true
}

load_secret_file() {
  local f="$1"
  [[ -r "$f" ]] || return 0
  set +x
  # shellcheck disable=SC1090
  set -a; source "$f"; set +a
}

provider_is_admitted() {
  local wanted="$1" p
  for p in ${CLAY_TYPED_FREE_PROVIDERS:-}; do
    [[ "$p" == "$wanted" ]] && return 0
  done
  return 1
}

# Only provider-specific sources are eligible after that exact provider received
# typed FREE admission. Legacy mixed clay_provider.env files are intentionally
# not sourced because they can expose UNKNOWN/PAID/SUBSCRIPTION credentials.
load_admitted_secret_sources() {
  if provider_is_admitted groq; then
    load_secret_file /run/secrets/clay_groq.env
    load_secret_file /artifacts/.clay_groq.env
    load_secret_file /cache/clay_groq.env
    load_secret_file "$ROOT/.clay_groq.env"
    load_secret_file "$ROOT/research_entity/private/GROQ_API.env"
  fi
  if provider_is_admitted mistral; then
    load_secret_file /run/secrets/clay_mistral.env
    load_secret_file /artifacts/.clay_mistral.env
    load_secret_file /cache/clay_mistral.env
    load_secret_file "$ROOT/.clay_mistral.env"
    load_secret_file "$ROOT/research_entity/private/MISTRAL_API.env"
  fi
  if provider_is_admitted nvidia; then
    load_secret_file /run/secrets/clay_nvidia.env
    load_secret_file /artifacts/.clay_nvidia.env
    load_secret_file /cache/clay_nvidia.env
    load_secret_file "$ROOT/.clay_nvidia.env"
    load_secret_file "$ROOT/research_entity/private/NVIDIA_API.env"
    load_secret_file "$ROOT/research_entity/private/NGC_API.env"
  fi
}

normalize_admitted_provider_pool() {
  python3 - <<'PY'
import os, shlex
admitted=set(os.getenv('CLAY_TYPED_FREE_PROVIDERS','').split())
families={
 'groq': ('GROQ_API_KEYS',['GROQ_API_KEY','GROQ2_API_KEY','GROQ3_API_KEY']),
 'mistral': ('MISTRAL_API_KEYS',['MISTRAL_API_KEY','MISTRAL2_API_KEY','MISTRAL3_API_KEY']),
 'nvidia': ('NVIDIA_API_KEYS',['NVIDIA_API_KEY','NVIDIA_NIM_API_KEY','NVIDIA2_API_KEY','NVIDIA3_API_KEY','NGC_API_KEY']),
}
for provider,(target,names) in families.items():
    if provider not in admitted:
        continue
    vals=[]
    for name in names:
        value=os.getenv(name,'').strip()
        if value and value not in vals:
            vals.append(value)
    for value in [x.strip() for x in os.getenv(target,'').replace(';',',').split(',') if x.strip()]:
        if value not in vals:
            vals.append(value)
    if vals:
        print('export %s=%s' % (target, shlex.quote(','.join(vals))))
if 'nvidia' in admitted and not os.getenv('NVIDIA_API_KEY') and os.getenv('NVIDIA_NIM_API_KEY'):
    print('export NVIDIA_API_KEY='+shlex.quote(os.environ['NVIDIA_NIM_API_KEY']))
PY
}

set_legacy_compat_attestation() {
  export CLAY_FREE_ONLY_ATTESTED=1
  provider_is_admitted groq && export CLAY_GROQ_FREE_ATTESTED=1 || true
  provider_is_admitted mistral && export CLAY_MISTRAL_FREE_ATTESTED=1 || true
  provider_is_admitted nvidia && export CLAY_NVIDIA_FREE_ATTESTED=1 || true
}

has_admitted_provider_key() {
  if provider_is_admitted groq && [[ -n "${GROQ_API_KEY:-}${GROQ_API_KEYS:-}" ]]; then return 0; fi
  if provider_is_admitted mistral && [[ -n "${MISTRAL_API_KEY:-}${MISTRAL_API_KEYS:-}" ]]; then return 0; fi
  if provider_is_admitted nvidia && [[ -n "${NVIDIA_API_KEY:-}${NVIDIA_API_KEYS:-}${NGC_API_KEY:-}${NVIDIA_NIM_API_KEY:-}" ]]; then return 0; fi
  return 1
}

resolve_typed_admission() {
  local admitted
  # Run admission resolution in a clean environment so provider secrets are not
  # even inherited by the pre-admission policy process.
  if [[ -n "${CLAY_PROVIDER_ADMISSION_FILE:-}" ]]; then
    admitted="$(env -i PATH="$PATH" CLAY_PROVIDER_ADMISSION_FILE="$CLAY_PROVIDER_ADMISSION_FILE" \
      python3 "$ADMISSION_TOOL" runtime-admitted-providers 2>/dev/null)" || return 1
  else
    admitted="$(env -i PATH="$PATH" python3 "$ADMISSION_TOOL" runtime-admitted-providers 2>/dev/null)" || return 1
  fi
  [[ -n "$admitted" ]] || return 1
  export CLAY_TYPED_FREE_PROVIDERS="$(printf '%s\n' "$admitted" | tr '\n' ' ' | xargs)"
  return 0
}

start_dashboard() {
  local evaluator="$ROOT/free swarm/evaluate.py"
  [[ -f "$evaluator" ]] || return 0
  if ! pgrep -f '[f]ree swarm/evaluate.py.*--watch' >/dev/null 2>&1; then
    env -i PATH="$PATH" HOME="${HOME:-/tmp}" nohup python3 "$evaluator" \
      --repo "$ROOT" --artifacts "$STATE_DIR" \
      --watch --hours 24 --interval-seconds 60 --publish --publish-min-seconds 900 \
      >"$STATE_DIR/dashboard.log" 2>&1 </dev/null &
    echo "$!" > "$STATE_DIR/dashboard.pid"
  fi
}

write_blocked_state() {
  local reason="$1"
  env -i PATH="$PATH" python3 - "$reason" > "$STATE_DIR/SUPERVISOR.json.tmp" <<'PY'
import datetime,json,sys
print(json.dumps({
  'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v4',
  'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'state':'WAITING_FOR_TYPED_FREE_PROVIDER_ADMISSION',
  'reason':sys.argv[1],
  'secret_lookup_count_for_blocked_paths':0,
  'network_attempt_count_for_blocked_paths':0,
  'provider_runtime_credit':0,
}, indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
}

write_ready_state() {
  python3 - > "$STATE_DIR/SUPERVISOR.json.tmp" <<'PY'
import datetime,json,os
providers=os.getenv('CLAY_TYPED_FREE_PROVIDERS','').split()
def present(provider):
    if provider=='groq': return bool(os.getenv('GROQ_API_KEY') or os.getenv('GROQ_API_KEYS'))
    if provider=='mistral': return bool(os.getenv('MISTRAL_API_KEY') or os.getenv('MISTRAL_API_KEYS'))
    if provider=='nvidia': return bool(os.getenv('NVIDIA_API_KEY') or os.getenv('NVIDIA_API_KEYS') or os.getenv('NGC_API_KEY') or os.getenv('NVIDIA_NIM_API_KEY'))
    return False
print(json.dumps({
  'schema':'CLAY_ENTITYOS_SWARM_SUPERVISOR/v4',
  'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'state':'TYPED_FREE_ADMISSION_ACTIVE',
  'admitted_providers':providers,
  'credential_presence_for_admitted_providers':{p:present(p) for p in providers},
  'unadmitted_provider_credentials':'UNOBSERVED_BY_POLICY',
  'dashboard_watch':True,
}, indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"
}

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  unset CLAY_TYPED_FREE_PROVIDERS || true

  # This is the first provider-policy action. It reads only the non-secret
  # control-plane admission object and current supervisor authority.
  if ! resolve_typed_admission; then
    write_blocked_state "MISSING_MALFORMED_STALE_OR_NONFREE_TYPED_ADMISSION"
    sleep 60
    continue
  fi

  # Only now can the parent environment be narrowed and admitted credentials read.
  drop_unadmitted_provider_env
  load_admitted_secret_sources
  # shellcheck disable=SC2046
  eval "$(normalize_admitted_provider_pool)"
  set_legacy_compat_attestation
  write_ready_state

  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  if has_admitted_provider_key; then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4","state":"EXPIRED_WITHOUT_TYPED_FREE_PROVIDER_CREDENTIALS"}\n' > "$STATE_DIR/SUPERVISOR.json"
