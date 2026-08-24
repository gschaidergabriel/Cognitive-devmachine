#!/usr/bin/env bash
set -Eeuo pipefail

# Zero-cost local model execution boundary for Distillery/Forge.
# External provider traffic may remain quarantined; this path is loopback-only and
# deliberately performs no model/runtime download, provider secret lookup, or remote
# model resolution. Runtime + GGUF bytes must already exist locally and must match
# explicit SHA-256 identities before execution.
CACHE_ROOT="${CLAY_LOCAL_MODEL_CACHE:-/cache/clay-local-research-model}"
RUNTIME_BIN="${CLAY_LLAMA_SERVER_BIN:-$CACHE_ROOT/llama.cpp/build/bin/llama-server}"
RUNTIME_SHA256="${CLAY_LLAMA_SERVER_SHA256:-}"
MODEL_FILE="${CLAY_LOCAL_MODEL_FILE:-}"
MODEL_SHA256="${CLAY_LOCAL_MODEL_SHA256:-}"
HOST="127.0.0.1"
PORT="${CLAY_LOCAL_RESEARCH_PORT:-8088}"
THREADS="${CLAY_LOCAL_RESEARCH_THREADS:-4}"
PARALLEL="${CLAY_LOCAL_RESEARCH_PARALLEL:-1}"
CTX="${CLAY_LOCAL_RESEARCH_CTX:-8192}"
ARTIFACT_ROOT="${CLAY_LOCAL_RESEARCH_ARTIFACT_ROOT:-/artifacts/clay-entityos-swarm}"
STATE="$ARTIFACT_ROOT/local-model.json"

fail(){ printf 'LOCAL_RESEARCH_MODEL_IDENTITY_GATE:%s\n' "$1" >&2; exit 64; }
valid_sha256(){ [[ "$1" =~ ^[0-9a-fA-F]{64}$ ]]; }
sha256_file(){ sha256sum -- "$1" | awk '{print $1}'; }

[[ -x "$RUNTIME_BIN" ]] || fail "RUNTIME_BIN_MISSING_OR_NOT_EXECUTABLE"
[[ -n "$MODEL_FILE" && -f "$MODEL_FILE" && -r "$MODEL_FILE" ]] || fail "MODEL_FILE_MISSING_OR_UNREADABLE"
valid_sha256 "$RUNTIME_SHA256" || fail "RUNTIME_SHA256_REQUIRED"
valid_sha256 "$MODEL_SHA256" || fail "MODEL_SHA256_REQUIRED"

OBSERVED_RUNTIME_SHA256="$(sha256_file "$RUNTIME_BIN")"
OBSERVED_MODEL_SHA256="$(sha256_file "$MODEL_FILE")"
[[ "${OBSERVED_RUNTIME_SHA256,,}" == "${RUNTIME_SHA256,,}" ]] || fail "RUNTIME_SHA256_MISMATCH"
[[ "${OBSERVED_MODEL_SHA256,,}" == "${MODEL_SHA256,,}" ]] || fail "MODEL_SHA256_MISMATCH"

# Never inherit a previously running loopback server as evidence for these bytes. A health
# response cannot prove the resident process/model identity. Fail closed instead.
if [[ "${CLAY_LOCAL_RESEARCH_DISABLE_PORT_PROBE:-0}" != "1" ]]; then
  if curl -fsS --max-time 1 "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    fail "UNVERIFIED_EXISTING_SERVER_ON_TARGET_PORT"
  fi
fi

mkdir -p "$ARTIFACT_ROOT"
export CLAY_LOCAL_RESEARCH_STATE="$STATE"
export CLAY_LOCAL_RESEARCH_RUNTIME_BIN="$RUNTIME_BIN"
export CLAY_LOCAL_RESEARCH_RUNTIME_SHA256="${OBSERVED_RUNTIME_SHA256,,}"
export CLAY_LOCAL_RESEARCH_MODEL_FILE="$MODEL_FILE"
export CLAY_LOCAL_RESEARCH_MODEL_SHA256="${OBSERVED_MODEL_SHA256,,}"
export CLAY_LOCAL_RESEARCH_HOST="$HOST"
export CLAY_LOCAL_RESEARCH_PORT="$PORT"
export CLAY_LOCAL_RESEARCH_THREADS="$THREADS"
export CLAY_LOCAL_RESEARCH_PARALLEL="$PARALLEL"
export CLAY_LOCAL_RESEARCH_CTX="$CTX"
python3 - <<'PY' >"$STATE.tmp"
import datetime
import json
import os

print(json.dumps({
    "schema": "CLAY_LOCAL_RESEARCH_MODEL/v2",
    "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "state": "STARTING",
    "backend": "llama.cpp",
    "runtime_path": os.environ["CLAY_LOCAL_RESEARCH_RUNTIME_BIN"],
    "runtime_sha256": os.environ["CLAY_LOCAL_RESEARCH_RUNTIME_SHA256"],
    "model_path": os.environ["CLAY_LOCAL_RESEARCH_MODEL_FILE"],
    "model_sha256": os.environ["CLAY_LOCAL_RESEARCH_MODEL_SHA256"],
    "listen": f'{os.environ["CLAY_LOCAL_RESEARCH_HOST"]}:{os.environ["CLAY_LOCAL_RESEARCH_PORT"]}',
    "threads": int(os.environ["CLAY_LOCAL_RESEARCH_THREADS"]),
    "parallel": int(os.environ["CLAY_LOCAL_RESEARCH_PARALLEL"]),
    "context": int(os.environ["CLAY_LOCAL_RESEARCH_CTX"]),
    "cost_class": "LOCAL_ZERO_PROVIDER_BILLING",
    "remote_download_performed_by_execution_path": False,
    "provider_secret_lookup_performed_by_execution_path": False,
    "identity_scope": "PRELOAD_RUNTIME_AND_MODEL_BYTES_VERIFIED",
    "loader_consumption_evidence": "PENDING_RUNTIME_RECEIPT",
    "runtime_credit": 0,
    "jspace_model_runtime_credit": 0,
    "training_credit": 0,
}, indent=2, sort_keys=True))
PY
mv "$STATE.tmp" "$STATE"

exec "$RUNTIME_BIN" \
  -m "$MODEL_FILE" \
  --host "$HOST" --port "$PORT" \
  --threads "$THREADS" --threads-batch "$THREADS" \
  --parallel "$PARALLEL" --ctx-size "$CTX" \
  --no-webui
