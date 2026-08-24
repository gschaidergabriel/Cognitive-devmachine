#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Trigger-1 V2 primary fast path: normal-user, zero-provider-billing, loopback-only.
# Do not materialize or consume any external LLM provider credential here.
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

OUT_DIR="${1:?usage: trigger1_local_qwen06_activation_api.sh OUTPUT_DIR}"
mkdir -p "$OUT_DIR"

USER_HOME="${HOME:?HOME is required}"
CACHE_ROOT="${CLAY_TRIGGER1_LOCAL_CACHE:-${XDG_CACHE_HOME:-$USER_HOME/.cache}/clay-trigger1-local}"
VENV="$CACHE_ROOT/venv"
HF_HOME="${HF_HOME:-$CACHE_ROOT/huggingface}"
mkdir -p "$CACHE_ROOT" "$HF_HOME"
export HF_HOME
export TOKENIZERS_PARALLELISM=false

has_runtime(){
  "$1" - <<'PY' >/dev/null 2>&1
import torch, transformers, huggingface_hub, safetensors
assert tuple(int(x) for x in transformers.__version__.split('.')[:2]) >= (4, 51)
PY
}

PYTHON="python3"
if ! has_runtime "$PYTHON"; then
  if [[ ! -x "$VENV/bin/python" ]]; then
    rm -rf "$VENV.tmp"
    python3 -m venv "$VENV.tmp"
    mv "$VENV.tmp" "$VENV"
  fi
  PYTHON="$VENV/bin/python"
  if ! has_runtime "$PYTHON"; then
    "$PYTHON" -m pip install --disable-pip-version-check --upgrade pip wheel
    "$PYTHON" -m pip install --disable-pip-version-check --index-url https://download.pytorch.org/whl/cpu torch
    "$PYTHON" -m pip install --disable-pip-version-check 'transformers>=4.51,<6' 'huggingface_hub>=0.30' safetensors
  fi
fi

if ! has_runtime "$PYTHON"; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v2',
  'status':'BLOCKED_LOCAL_FASTPATH',
  'reason':'PYTORCH_TRANSFORMERS_NORMAL_USER_RUNTIME_UNAVAILABLE_AFTER_BOOTSTRAP',
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'next_action':'ROUTE_AROUND_OR_REPAIR_NOW_WITHOUT_WAITING_FOR_EXTERNAL_PROVIDER'
}, indent=2, sort_keys=True)+'\n', encoding='utf-8')
PY
  exit 3
fi

exec "$PYTHON" "$ROOT/tools/trigger1_local_qwen06_activation_api_execute_v2.py" \
  --output-dir "$OUT_DIR" \
  --cache-dir "$HF_HOME"
