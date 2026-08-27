#!/usr/bin/env bash
set -Eeuo pipefail

# Zero-cost local fallback for Distillery/Forge. Bound to loopback only.
# It deliberately does not read provider credentials and remains usable while
# external LLM provider traffic is quarantined.
# Runtime identity is recorded after the server reports the loaded model via /props.
# Defaults are writable by the normal Linux development user; container/VPS paths
# remain explicitly overrideable through CLAY_LOCAL_MODEL_CACHE/HF_HOME/state vars.
USER_HOME="${HOME:?HOME is required for normal-user local model state}"
XDG_CACHE_ROOT="${XDG_CACHE_HOME:-$USER_HOME/.cache}"
XDG_STATE_ROOT="${XDG_STATE_HOME:-$USER_HOME/.local/state}"
CACHE_ROOT="${CLAY_LOCAL_MODEL_CACHE:-$XDG_CACHE_ROOT/clay-local-research-model}"
SRC="$CACHE_ROOT/llama.cpp"
BUILD="$SRC/build"
HF_HOME="${HF_HOME:-$XDG_CACHE_ROOT/huggingface}"
STATE_ROOT="${CLAY_LOCAL_RESEARCH_STATE_DIR:-$XDG_STATE_ROOT/clay-entityos-swarm}"
MODEL="${CLAY_LOCAL_RESEARCH_MODEL:-Qwen/Qwen3-4B-GGUF:Q4_K_M}"
HOST="127.0.0.1"
PORT="${CLAY_LOCAL_RESEARCH_PORT:-8088}"
THREADS="${CLAY_LOCAL_RESEARCH_THREADS:-4}"
PARALLEL="${CLAY_LOCAL_RESEARCH_PARALLEL:-1}"
CTX="${CLAY_LOCAL_RESEARCH_CTX:-8192}"
READY_TIMEOUT="${CLAY_LOCAL_RESEARCH_READY_TIMEOUT:-3600}"
LOG="$STATE_ROOT/local-model.log"
STATE="$STATE_ROOT/local-model.json"
PROPS_TMP="$STATE.props.$$"
MODELS_TMP="$STATE.models.$$"
mkdir -p "$CACHE_ROOT" "$HF_HOME" "$STATE_ROOT"
export HF_HOME

health(){ curl -fsS --max-time 2 "http://$HOST:$PORT/health" >/dev/null 2>&1; }
fetch_props(){ curl -fsS --max-time 5 "http://$HOST:$PORT/props" >"$PROPS_TMP"; }
fetch_models(){ curl -fsS --max-time 5 "http://$HOST:$PORT/v1/models" >"$MODELS_TMP"; }

write_state(){
  local state_value="$1"
  local process_binding="$2"
  local server_pid="${3:-}"
  CLAY_STATE_VALUE="$state_value" \
  CLAY_PROCESS_BINDING="$process_binding" \
  CLAY_SERVER_PID="$server_pid" \
  CLAY_BACKEND_COMMIT="${COMMIT:-UNKNOWN}" \
  CLAY_MODEL_SELECTOR="$MODEL" \
  CLAY_LISTEN="$HOST:$PORT" \
  CLAY_THREADS="$THREADS" \
  CLAY_PARALLEL="$PARALLEL" \
  CLAY_CTX="$CTX" \
  CLAY_BUILD_BIN="$BUILD/bin/llama-server" \
  CLAY_PROPS_PATH="$PROPS_TMP" \
  CLAY_MODELS_PATH="$MODELS_TMP" \
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

live_model_id = None
models_path = Path(os.environ['CLAY_MODELS_PATH'])
if models_path.exists():
    try:
        parsed = json.loads(models_path.read_text(encoding='utf-8'))
        rows = parsed.get('data') if isinstance(parsed, dict) else None
        if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict):
            live_model_id = str(rows[0].get('id') or '').strip() or None
    except Exception:
        live_model_id = None

pid_raw = os.environ.get('CLAY_SERVER_PID', '').strip()
pid = int(pid_raw) if pid_raw.isdigit() else None
reported_model_path = str(props.get('model_path') or '').strip()
resolved_model_path: Path | None = None
if reported_model_path:
    candidate = Path(reported_model_path)
    if candidate.is_absolute():
        resolved_model_path = candidate
    elif pid is not None:
        try:
            cwd = Path(os.readlink(f'/proc/{pid}/cwd'))
            resolved_model_path = (cwd / candidate).resolve()
        except OSError:
            resolved_model_path = None

model_sha = None
model_stat = None
if resolved_model_path is not None and resolved_model_path.is_file():
    st = resolved_model_path.stat()
    model_stat = {'size': st.st_size, 'mtime_ns': st.st_mtime_ns}
    model_sha = sha256_file(resolved_model_path)

runtime_exe_path = None
runtime_exe_sha = None
runtime_process_bound = False
if pid is not None:
    try:
        runtime_exe_path = Path(os.readlink(f'/proc/{pid}/exe')).resolve()
        if runtime_exe_path.is_file():
            runtime_exe_sha = sha256_file(runtime_exe_path)
        build_bin = Path(os.environ['CLAY_BUILD_BIN']).resolve()
        runtime_process_bound = runtime_exe_path == build_bin
    except OSError:
        pass

payload = {
    'schema': 'CLAY_LOCAL_RESEARCH_MODEL/v2',
    'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'state': os.environ['CLAY_STATE_VALUE'],
    'backend': 'llama.cpp',
    'backend_commit': os.environ.get('CLAY_BACKEND_COMMIT', 'UNKNOWN'),
    'runtime_build_info': props.get('build_info'),
    'runtime_process_binding': os.environ['CLAY_PROCESS_BINDING'],
    'runtime_process_bound_to_build_path': runtime_process_bound,
    'server_pid': pid,
    'server_exe_path': str(runtime_exe_path) if runtime_exe_path else None,
    'server_exe_sha256': runtime_exe_sha,
    'model_selector': os.environ['CLAY_MODEL_SELECTOR'],
    'live_model_id': live_model_id,
    'model_alias': props.get('model_alias') or props.get('model'),
    'model_path_reported_by_server': reported_model_path or None,
    'model_path_resolved': str(resolved_model_path) if resolved_model_path else None,
    'model_sha256_post_load_path': model_sha,
    'model_file_stat': model_stat,
    'tokenizer_identity': 'EMBEDDED_IN_GGUF_SAME_FILE_DIGEST_ONLY' if model_sha else 'UNKNOWN',
    'listen': os.environ['CLAY_LISTEN'],
    'threads': safe_int('CLAY_THREADS'),
    'parallel': safe_int('CLAY_PARALLEL'),
    'context': safe_int('CLAY_CTX'),
    'cache_root': os.environ['CLAY_CACHE_ROOT'],
    'state_root': os.environ['CLAY_STATE_ROOT'],
    'cost_class': 'LOCAL_ZERO_PROVIDER_BILLING',
    'identity_evidence_scope': 'POST_LOAD_SERVER_REPORTED_MODEL_PATH_PLUS_RUNTIME_BINARY_HASH_PREREQUISITE_ONLY',
    'loader_consumption_attestation': False,
    'loader_consumption_note': 'llama-server /props model_path is observed after load, but this is not consumed-byte attestation and does not close post-load mutation risk.',
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

existing_identity_matches(){
  local commit="$1"
  CLAY_EXPECTED_COMMIT="$commit" \
  CLAY_EXPECTED_MODEL="$MODEL" \
  CLAY_BUILD_BIN="$BUILD/bin/llama-server" \
  CLAY_STATE_PATH="$STATE" \
  CLAY_MODELS_PATH="$MODELS_TMP" \
  python3 - <<'PY'
from __future__ import annotations
import hashlib, json, os
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

try:
    state = json.loads(Path(os.environ['CLAY_STATE_PATH']).read_text(encoding='utf-8'))
    models = json.loads(Path(os.environ['CLAY_MODELS_PATH']).read_text(encoding='utf-8'))
except Exception:
    raise SystemExit(1)
rows = models.get('data') if isinstance(models, dict) else None
live_id = rows[0].get('id') if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict) else None
expected_model = os.environ['CLAY_EXPECTED_MODEL']
expected_commit = os.environ['CLAY_EXPECTED_COMMIT']
if not (
    state.get('schema') == 'CLAY_LOCAL_RESEARCH_MODEL/v2'
    and state.get('state') == 'READY_IDENTITY_OBSERVED'
    and state.get('backend') == 'llama.cpp'
    and state.get('backend_commit') == expected_commit
    and state.get('model_selector') == expected_model
    and state.get('live_model_id') == expected_model
    and live_id == expected_model
    and state.get('runtime_process_bound_to_build_path') is True
    and isinstance(state.get('model_sha256_post_load_path'), str)
    and len(state['model_sha256_post_load_path']) == 64
):
    raise SystemExit(1)
pid = state.get('server_pid')
if not isinstance(pid, int) or pid <= 0:
    raise SystemExit(1)
try:
    os.kill(pid, 0)
    exe = Path(os.readlink(f'/proc/{pid}/exe')).resolve()
except OSError:
    raise SystemExit(1)
build_bin = Path(os.environ['CLAY_BUILD_BIN']).resolve()
if exe != build_bin or not exe.is_file():
    raise SystemExit(1)
observed_sha = sha256_file(exe)
if observed_sha != state.get('server_exe_sha256'):
    raise SystemExit(1)
raise SystemExit(0)
PY
}

cleanup_tmp(){ rm -f "$PROPS_TMP" "$MODELS_TMP"; }
trap cleanup_tmp EXIT

COMMIT="$(git -C "$SRC" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
if health; then
  if fetch_models && [[ "$COMMIT" =~ ^[0-9a-f]{40}$ ]] && existing_identity_matches "$COMMIT"; then
    echo LOCAL_RESEARCH_MODEL_ALREADY_READY_IDENTITY_BOUND
    exit 0
  fi
  echo LOCAL_RESEARCH_MODEL_HEALTHY_BUT_IDENTITY_UNVERIFIED >&2
  exit 21
fi

if [[ ! -x "$BUILD/bin/llama-server" ]]; then
  rm -rf "$SRC.tmp"
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC.tmp"
  rm -rf "$SRC"
  mv "$SRC.tmp" "$SRC"
  cmake -S "$SRC" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=ON
  cmake --build "$BUILD" -j"$(nproc)" --target llama-server llama-cli
fi
COMMIT="$(git -C "$SRC" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
write_state "STARTING" "NOT_YET_RUNNING" ""

"$BUILD/bin/llama-server" \
  -hf "$MODEL" \
  --alias "$MODEL" \
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
  sleep 2
done

if fetch_props && fetch_models; then
  write_state "READY_IDENTITY_OBSERVED" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
  if ! existing_identity_matches "$COMMIT"; then
    write_state "READY_IDENTITY_MISMATCH" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
    kill -TERM "$SERVER_PID" 2>/dev/null || true
    exit 7
  fi
else
  write_state "READY_IDENTITY_ENDPOINT_UNAVAILABLE" "STARTED_BY_THIS_SCRIPT" "$SERVER_PID"
  kill -TERM "$SERVER_PID" 2>/dev/null || true
  exit 7
fi

set +e
wait "$SERVER_PID"
code=$?
set -e
exit "$code"
