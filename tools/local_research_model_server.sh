#!/usr/bin/env bash
set -Eeuo pipefail

# Zero-cost local fallback for Distillery/Forge. Bound to loopback only.
# Execution performs no runtime/model download and reads no provider credentials.
# Both local runtime and GGUF bytes must be explicitly SHA-256 admitted before launch,
# then the started process + server-reported model path are cross-checked after readiness.
USER_HOME="${HOME:?HOME is required for normal-user local model state}"
XDG_CACHE_ROOT="${XDG_CACHE_HOME:-$USER_HOME/.cache}"
XDG_STATE_ROOT="${XDG_STATE_HOME:-$USER_HOME/.local/state}"
CACHE_ROOT="${CLAY_LOCAL_MODEL_CACHE:-$XDG_CACHE_ROOT/clay-local-research-model}"
RUNTIME_BIN="${CLAY_LLAMA_SERVER_BIN:-$CACHE_ROOT/llama.cpp/build/bin/llama-server}"
RUNTIME_SHA256="${CLAY_LLAMA_SERVER_SHA256:-}"
MODEL_FILE="${CLAY_LOCAL_MODEL_FILE:-}"
MODEL_SHA256="${CLAY_LOCAL_MODEL_SHA256:-}"
HOST="127.0.0.1"
PORT="${CLAY_LOCAL_RESEARCH_PORT:-8088}"
THREADS="${CLAY_LOCAL_RESEARCH_THREADS:-4}"
PARALLEL="${CLAY_LOCAL_RESEARCH_PARALLEL:-1}"
CTX="${CLAY_LOCAL_RESEARCH_CTX:-8192}"
READY_TIMEOUT="${CLAY_LOCAL_RESEARCH_READY_TIMEOUT:-3600}"
STATE_ROOT="${CLAY_LOCAL_RESEARCH_STATE_DIR:-$XDG_STATE_ROOT/clay-entityos-swarm}"
LOG="$STATE_ROOT/local-model.log"
STATE="$STATE_ROOT/local-model.json"
PROPS_TMP="$STATE.props.$$"

fail(){ printf 'LOCAL_RESEARCH_MODEL_IDENTITY_GATE:%s\n' "$1" >&2; exit 64; }
valid_sha256(){ [[ "$1" =~ ^[0-9a-fA-F]{64}$ ]]; }
sha256_file(){ sha256sum -- "$1" | awk '{print $1}'; }
canonical_file(){ readlink -f -- "$1"; }

[[ -x "$RUNTIME_BIN" ]] || fail "RUNTIME_BIN_MISSING_OR_NOT_EXECUTABLE"
[[ -n "$MODEL_FILE" && -f "$MODEL_FILE" && -r "$MODEL_FILE" ]] || fail "MODEL_FILE_MISSING_OR_UNREADABLE"
valid_sha256 "$RUNTIME_SHA256" || fail "RUNTIME_SHA256_REQUIRED"
valid_sha256 "$MODEL_SHA256" || fail "MODEL_SHA256_REQUIRED"

RUNTIME_BIN="$(canonical_file "$RUNTIME_BIN")"
MODEL_FILE="$(canonical_file "$MODEL_FILE")"
OBSERVED_RUNTIME_SHA256="$(sha256_file "$RUNTIME_BIN")"
OBSERVED_MODEL_SHA256="$(sha256_file "$MODEL_FILE")"
RUNTIME_SHA256="${RUNTIME_SHA256,,}"
MODEL_SHA256="${MODEL_SHA256,,}"
[[ "${OBSERVED_RUNTIME_SHA256,,}" == "$RUNTIME_SHA256" ]] || fail "RUNTIME_SHA256_MISMATCH"
[[ "${OBSERVED_MODEL_SHA256,,}" == "$MODEL_SHA256" ]] || fail "MODEL_SHA256_MISMATCH"

mkdir -p "$STATE_ROOT"
health(){ curl -fsS --max-time 2 "http://$HOST:$PORT/health" >/dev/null 2>&1; }
fetch_props(){ curl -fsS --max-time 5 "http://$HOST:$PORT/props" >"$PROPS_TMP"; }

# A healthy pre-existing loopback process is not authenticated as the requested runtime/model.
# Never inherit it as evidence for this invocation.
if health; then
  fail "UNVERIFIED_EXISTING_SERVER_ON_TARGET_PORT"
fi

write_state(){
  local requested_state="$1"
  local process_binding="$2"
  local server_pid="${3:-}"
  CLAY_REQUESTED_STATE="$requested_state" \
  CLAY_PROCESS_BINDING="$process_binding" \
  CLAY_SERVER_PID="$server_pid" \
  CLAY_EXPECTED_RUNTIME_PATH="$RUNTIME_BIN" \
  CLAY_EXPECTED_RUNTIME_SHA256="$RUNTIME_SHA256" \
  CLAY_EXPECTED_MODEL_PATH="$MODEL_FILE" \
  CLAY_EXPECTED_MODEL_SHA256="$MODEL_SHA256" \
  CLAY_LISTEN="$HOST:$PORT" \
  CLAY_THREADS="$THREADS" \
  CLAY_PARALLEL="$PARALLEL" \
  CLAY_CTX="$CTX" \
  CLAY_PROPS_PATH="$PROPS_TMP" \
  CLAY_STATE_PATH="$STATE.tmp" \
  CLAY_CACHE_ROOT="$CACHE_ROOT" \
  CLAY_STATE_ROOT="$STATE_ROOT" \
  python3 - <<'PY'
from __future__ import annotations
import datetime, hashlib, json, os
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_int(name: str) -> int | None:
    try:
        return int(os.environ[name])
    except (KeyError, ValueError):
        return None

props = {}
props_path = Path(os.environ['CLAY_PROPS_PATH'])
if props_path.exists():
    try:
        parsed = json.loads(props_path.read_text(encoding='utf-8'))
        if isinstance(parsed, dict):
            props = parsed
    except Exception:
        props = {}

expected_runtime = Path(os.environ['CLAY_EXPECTED_RUNTIME_PATH']).resolve()
expected_runtime_sha = os.environ['CLAY_EXPECTED_RUNTIME_SHA256'].lower()
expected_model = Path(os.environ['CLAY_EXPECTED_MODEL_PATH']).resolve()
expected_model_sha = os.environ['CLAY_EXPECTED_MODEL_SHA256'].lower()
pid_raw = os.environ.get('CLAY_SERVER_PID', '').strip()
pid = int(pid_raw) if pid_raw.isdigit() else None

runtime_exe_path = None
runtime_exe_sha = None
if pid is not None:
    try:
        runtime_exe_path = Path(os.readlink(f'/proc/{pid}/exe')).resolve()
        if runtime_exe_path.is_file():
            runtime_exe_sha = sha256_file(runtime_exe_path)
    except OSError:
        pass
runtime_path_match = runtime_exe_path == expected_runtime
runtime_sha_match = runtime_exe_sha == expected_runtime_sha

reported_model_path = str(props.get('model_path') or '').strip()
resolved_model_path = None
if reported_model_path:
    candidate = Path(reported_model_path)
    if candidate.is_absolute():
        resolved_model_path = candidate.resolve()
    elif pid is not None:
        try:
            cwd = Path(os.readlink(f'/proc/{pid}/cwd'))
            resolved_model_path = (cwd / candidate).resolve()
        except OSError:
            pass
model_post_sha = None
model_stat = None
if resolved_model_path is not None and resolved_model_path.is_file():
    st = resolved_model_path.stat()
    model_stat = {'size': st.st_size, 'mtime_ns': st.st_mtime_ns}
    model_post_sha = sha256_file(resolved_model_path)
model_path_match = resolved_model_path == expected_model
model_sha_match = model_post_sha == expected_model_sha

requested_state = os.environ['CLAY_REQUESTED_STATE']
identity_admitted = bool(
    requested_state == 'READY_AFTER_PROPS'
    and os.environ['CLAY_PROCESS_BINDING'] == 'STARTED_BY_THIS_SCRIPT'
    and runtime_path_match
    and runtime_sha_match
    and model_path_match
    and model_sha_match
)
if requested_state == 'READY_AFTER_PROPS':
    state = 'READY_IDENTITY_OBSERVED' if identity_admitted else 'READY_IDENTITY_REJECTED'
else:
    state = requested_state

payload = {
    'schema': 'CLAY_LOCAL_RESEARCH_MODEL/v3',
    'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'state': state,
    'backend': 'llama.cpp',
    'runtime_process_binding': os.environ['CLAY_PROCESS_BINDING'],
    'server_pid': pid,
    'expected_runtime_path': str(expected_runtime),
    'expected_runtime_sha256': expected_runtime_sha,
    'server_exe_path': str(runtime_exe_path) if runtime_exe_path else None,
    'server_exe_sha256': runtime_exe_sha,
    'runtime_process_bound_to_expected_path': runtime_path_match,
    'runtime_post_start_sha256_matches_expected': runtime_sha_match,
    'expected_model_path': str(expected_model),
    'expected_model_sha256': expected_model_sha,
    'model_path_reported_by_server': reported_model_path or None,
    'model_path_resolved': str(resolved_model_path) if resolved_model_path else None,
    'model_sha256_post_load_path': model_post_sha,
    'model_path_matches_expected': model_path_match,
    'model_post_load_sha256_matches_expected': model_sha_match,
    'model_file_stat': model_stat,
    'tokenizer_identity': 'EMBEDDED_IN_GGUF_SAME_FILE_DIGEST_ONLY' if model_post_sha else 'UNKNOWN',
    'runtime_build_info': props.get('build_info'),
    'listen': os.environ['CLAY_LISTEN'],
    'threads': safe_int('CLAY_THREADS'),
    'parallel': safe_int('CLAY_PARALLEL'),
    'context': safe_int('CLAY_CTX'),
    'cache_root': os.environ['CLAY_CACHE_ROOT'],
    'state_root': os.environ['CLAY_STATE_ROOT'],
    'cost_class': 'LOCAL_ZERO_PROVIDER_BILLING',
    'remote_download_performed_by_execution_path': False,
    'provider_secret_lookup_performed_by_execution_path': False,
    'identity_admitted_prerequisite': identity_admitted,
    'identity_evidence_scope': 'PRELOAD_EXACT_HASH_PLUS_POSTLOAD_PROCESS_AND_SERVER_REPORTED_PATH_CROSSCHECK',
    'loader_consumption_attestation': False,
    'loader_consumption_note': 'Exact pre-load hashes plus post-load process/path/hash cross-check are prerequisites only; they do not prove exact bytes consumed by the loader or close post-check mutation risk.',
    'jspace_intervention_capable': False,
    'whole_entityos_runtime_credit': 0,
    'whole_hcu_runtime_credit': 0,
    'jspace_model_runtime_credit': 0,
    'training_credit': 0,
}
Path(os.environ['CLAY_STATE_PATH']).write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY
  mv "$STATE.tmp" "$STATE"
}

cleanup_props(){ rm -f "$PROPS_TMP"; }
trap cleanup_props EXIT
write_state "STARTING_EXACT_IDENTITY_PREVERIFIED" "NOT_YET_RUNNING" ""

"$RUNTIME_BIN" \
  -m "$MODEL_FILE" \
  --host "$HOST" --port "$PORT" \
  --threads "$THREADS" --threads-batch "$THREADS" \
  --parallel "$PARALLEL" --ctx-size "$CTX" \
  --no-webui >>"$LOG" 2>&1 &
SERVER_PID=$!

forward_term(){ kill -TERM "$SERVER_PID" 2>/dev/null || true; }
forward_int(){ kill -INT "$SERVER_PID" 2>/dev/null || true; }
trap 'forward_term' TERM
trap 'forward_int' INT

DEADLINE=$((SECONDS + READY_TIMEOUT))
while ! health; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    set +e
    wait "$SERVER_PID"
    code=$?
    set -e
    write_state "FAILED_BEFORE_READY_EXIT_${code}" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
    exit "$code"
  fi
  if (( SECONDS >= DEADLINE )); then
    write_state "READY_TIMEOUT" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    exit 6
  fi
  sleep 1
done

if ! fetch_props; then
  write_state "READY_PROPS_UNAVAILABLE" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
  kill -TERM "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  exit 65
fi
write_state "READY_AFTER_PROPS" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
if ! python3 - "$STATE" <<'PY'
import json,sys
payload=json.load(open(sys.argv[1],encoding='utf-8'))
raise SystemExit(0 if payload.get('identity_admitted_prerequisite') is True else 1)
PY
then
  kill -TERM "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  exit 65
fi

set +e
wait "$SERVER_PID"
code=$?
set -e
exit "$code"
