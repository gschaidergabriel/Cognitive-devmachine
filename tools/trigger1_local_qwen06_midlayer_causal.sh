#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# The retained Trigger-1 lane may download the pinned public Hugging Face checkpoint,
# but it must not inherit external LLM-provider credentials or silently attach a
# cached/stored Hugging Face token.  Public model download is transport only; it is
# not provider inference and must remain credential-independent.
unset \
  GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY \
  MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY \
  NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY \
  OPENROUTER_API_KEY OPENROUTER_API_KEYS OPENROUTER2_API_KEY OPENROUTER3_API_KEY \
  TOGETHER_API_KEY TOGETHER_API_KEYS \
  OPENAI_API_KEY OPENAI_API_KEYS \
  ANTHROPIC_API_KEY ANTHROPIC_API_KEYS \
  HF_TOKEN HUGGING_FACE_HUB_TOKEN HUGGINGFACE_HUB_TOKEN || true
while IFS= read -r name; do
  case "$name" in
    GROQ*KEY*|MISTRAL*KEY*|NVIDIA*KEY*|NGC*KEY*|OPENROUTER*KEY*|TOGETHER*KEY*|OPENAI*KEY*|ANTHROPIC*KEY*) unset "$name" || true ;;
  esac
done < <(compgen -v)
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1

OUT_DIR="${1:?usage: trigger1_local_qwen06_midlayer_causal.sh OUTPUT_DIR}"
mkdir -p "$OUT_DIR"
# Redirect the hub token file lookup into this disposable run directory and ensure
# the file is absent.  Together with HF_HUB_DISABLE_IMPLICIT_TOKEN this prevents a
# normal-user cached login from becoming hidden execution provenance.
export HF_TOKEN_PATH="$OUT_DIR/no-hf-token"
rm -f "$HF_TOKEN_PATH"

canonical_path(){
  python3 - "$1" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve(strict=False))
PY
}
OUT_DIR_CANONICAL="$(canonical_path "$OUT_DIR")"

USER_HOME="${HOME:?HOME is required}"
CACHE_ROOT="${CLAY_TRIGGER1_LOCAL_CACHE:-${XDG_CACHE_HOME:-$USER_HOME/.cache}/clay-trigger1-local}"
VENV="$CACHE_ROOT/venv"
HF_HOME="${HF_HOME:-$CACHE_ROOT/huggingface}"
mkdir -p "$CACHE_ROOT" "$HF_HOME"
export HF_HOME
export TOKENIZERS_PARALLELISM=false

available_kb(){ df -Pk "$CACHE_ROOT" | awk 'NR==2 {print $4}'; }
BEFORE_KB="$(available_kb)"
if [[ "$BEFORE_KB" -lt 4000000 ]]; then
  # Bounded cleanup only: disposable Trigger-1 temp dirs, incomplete venv, pip cache.
  # The current run output is evidence-in-progress and must never be deleted by its
  # own low-disk cleanup, even when OUT_DIR is inside RUNNER_TEMP/clay-trigger1-v2-*.
  for candidate in \
    "${RUNNER_TEMP:-/tmp}"/clay-trigger1-v2-* \
    "${RUNNER_TEMP:-/tmp}"/clay-trigger1-qwen06-*; do
    [[ -e "$candidate" ]] || continue
    candidate_canonical="$(canonical_path "$candidate")"
    if [[ "$candidate_canonical" == "$OUT_DIR_CANONICAL" ]]; then
      continue
    fi
    rm -rf -- "$candidate" 2>/dev/null || true
  done
  rm -rf "$VENV.tmp" 2>/dev/null || true
  rm -rf "$USER_HOME/.cache/pip" 2>/dev/null || true
fi
mkdir -p "$OUT_DIR"
if [[ "$(canonical_path "$OUT_DIR")" != "$OUT_DIR_CANONICAL" ]]; then
  echo "BLOCKED_OUTPUT_DIR_IDENTITY_CHANGED_DURING_CLEANUP" >&2
  exit 3
fi
AFTER_KB="$(available_kb)"
printf '{"available_kb_before":%s,"available_kb_after":%s,"current_output_preserved":true}\n' "$BEFORE_KB" "$AFTER_KB" > "$OUT_DIR/disk_preflight.json"
if [[ "$AFTER_KB" -lt 3000000 ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" "$BEFORE_KB" "$AFTER_KB" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1',
  'status':'BLOCKED_INSUFFICIENT_FREE_DISK_AFTER_BOUNDED_CLEANUP',
  'available_kb_before':int(sys.argv[2]),
  'available_kb_after':int(sys.argv[3]),
  'current_output_preserved':True,
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'next_action':'RECLAIM_ADDITIONAL_SANDBOX_CACHE_OR_STORAGE_WITHIN_OWNER_AUTHORITY'
}, indent=2, sort_keys=True)+'\n', encoding='utf-8')
PY
  exit 3
fi

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
import json, pathlib,sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1',
  'status':'BLOCKED_LOCAL_MIDLAYER_FASTPATH',
  'reason':'PYTORCH_TRANSFORMERS_NORMAL_USER_RUNTIME_UNAVAILABLE_AFTER_BOOTSTRAP',
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'next_action':'REPAIR_NOW_OR_ROUTE_AROUND_CURRENT_LOCAL_MIDLAYER_BLOCKER'
}, indent=2, sort_keys=True)+'\n', encoding='utf-8')
PY
  exit 3
fi

# Preserve the single lease-gated compatibility entrypoint while executing the
# strongest current Trigger-1 scientific discriminator behind it: calibration-only
# intermediate residual directions, counterbalanced label maps, six controls,
# wrong-layer, lesion/rescue, and promotion-gate-v4 translation.
exec "$PYTHON" "$ROOT/tools/trigger1_strongest_intermediate_bridge_execute.py" \
  --output-dir "$OUT_DIR" \
  --cache-dir "$HF_HOME"
