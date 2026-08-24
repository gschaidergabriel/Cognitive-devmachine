#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STATE_DIR="/artifacts/clay-entityos-swarm"
mkdir -p "$STATE_DIR"
START="$(date +%s)"
DEADLINE="$((START + 24*3600))"

# IMPORTANT: this supervisor never sources provider secret files and never reads
# provider key variables. Typed admission happens first; the Python admission-safe
# facade may inspect only admitted FREE provider secrets afterwards.

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

admission_json() {
  python3 "$ROOT/tools/free_swarm_provider_admission.py" --json 2>/dev/null || true
}

start_dashboard

while (( $(date +%s) < DEADLINE )); do
  NOW="$(date +%s)"
  REMAINING="$((DEADLINE - NOW))"
  HOURS="$(python3 - <<PY
print(max(0.01, $REMAINING/3600.0))
PY
)"

  ADMISSION="$(admission_json)"
  [[ -n "$ADMISSION" ]] || ADMISSION='{"schema":"ENTITYOS_PROVIDER_ADMISSION_STATUS/v1","admitted":false,"reason":"VALIDATOR_UNAVAILABLE"}'

  ADMISSION="$ADMISSION" REMAINING="$REMAINING" python3 - <<'PY' > "$STATE_DIR/SUPERVISOR.json.tmp"
import datetime, json, os
try:
    admission=json.loads(os.environ["ADMISSION"])
except Exception:
    admission={"schema":"ENTITYOS_PROVIDER_ADMISSION_STATUS/v1","admitted":False,"reason":"INVALID_VALIDATOR_OUTPUT"}
print(json.dumps({
    "schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4",
    "observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "repo_root":os.getcwd(),
    "remaining_seconds":int(os.environ["REMAINING"]),
    "admission":admission,
    "secret_lookup_in_supervisor":False,
    "legacy_env_attestation_authority":False,
    "dashboard_watch":True,
},indent=2))
PY
  mv "$STATE_DIR/SUPERVISOR.json.tmp" "$STATE_DIR/SUPERVISOR.json"

  if ADMISSION="$ADMISSION" python3 - <<'PY'
import json,os,sys
try:
    x=json.loads(os.environ["ADMISSION"])
except Exception:
    sys.exit(1)
sys.exit(0 if x.get("admitted") is True and x.get("admitted_free_providers") else 1)
PY
  then
    exec python3 "$ROOT/tools/run_24h_entityos_swarm.py" \
      --hours "$HOURS" --output-dir "$STATE_DIR/active-$(date -u +%Y%m%dT%H%M%SZ)"
  fi

  sleep 60
done

printf '{"schema":"CLAY_ENTITYOS_SWARM_SUPERVISOR/v4","state":"EXPIRED_WITHOUT_VALID_TYPED_FREE_ADMISSION"}\n' > "$STATE_DIR/SUPERVISOR.json"
