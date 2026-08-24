#!/usr/bin/env bash
set -Eeuo pipefail

# Zero-cost local fallback for Distillery/Forge. Bound to loopback only.
# It deliberately does not read provider credentials and remains usable while
# external LLM provider traffic is quarantined.
CACHE_ROOT="${CLAY_LOCAL_MODEL_CACHE:-/cache/clay-local-research-model}"
SRC="$CACHE_ROOT/llama.cpp"
BUILD="$SRC/build"
HF_HOME="${HF_HOME:-/cache/huggingface}"
MODEL="${CLAY_LOCAL_RESEARCH_MODEL:-Qwen/Qwen3-4B-GGUF:Q4_K_M}"
HOST="127.0.0.1"
PORT="${CLAY_LOCAL_RESEARCH_PORT:-8088}"
THREADS="${CLAY_LOCAL_RESEARCH_THREADS:-4}"
PARALLEL="${CLAY_LOCAL_RESEARCH_PARALLEL:-1}"
CTX="${CLAY_LOCAL_RESEARCH_CTX:-8192}"
LOG="/artifacts/clay-entityos-swarm/local-model.log"
STATE="/artifacts/clay-entityos-swarm/local-model.json"
mkdir -p "$CACHE_ROOT" "$HF_HOME" "$(dirname "$LOG")"
export HF_HOME

health(){ curl -fsS --max-time 2 "http://$HOST:$PORT/health" >/dev/null 2>&1; }
if health; then echo LOCAL_RESEARCH_MODEL_ALREADY_READY; exit 0; fi

if [[ ! -x "$BUILD/bin/llama-server" ]]; then
  rm -rf "$SRC.tmp"
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$SRC.tmp"
  rm -rf "$SRC"
  mv "$SRC.tmp" "$SRC"
  cmake -S "$SRC" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=ON
  cmake --build "$BUILD" -j"$(nproc)" --target llama-server llama-cli
fi

COMMIT="$(git -C "$SRC" rev-parse HEAD 2>/dev/null || echo UNKNOWN)"
python3 - <<PY >"$STATE.tmp"
import json,datetime
print(json.dumps({
  'schema':'CLAY_LOCAL_RESEARCH_MODEL/v1',
  'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'state':'STARTING',
  'backend':'llama.cpp',
  'backend_commit':'$COMMIT',
  'model':'$MODEL',
  'listen':'$HOST:$PORT',
  'threads':int('$THREADS'),
  'parallel':int('$PARALLEL'),
  'context':int('$CTX'),
  'cost_class':'LOCAL_ZERO_PROVIDER_BILLING',
},indent=2))
PY
mv "$STATE.tmp" "$STATE"

exec "$BUILD/bin/llama-server" \
  -hf "$MODEL" \
  --host "$HOST" --port "$PORT" \
  --threads "$THREADS" --threads-batch "$THREADS" \
  --parallel "$PARALLEL" --ctx-size "$CTX" \
  --no-webui
