#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Compatibility launcher retained for the single Trigger1 V2 workflow lane.
# The old direct midlayer executor is intentionally superseded here by the stronger
# calibration-only intermediate-residual contrastive protocol and its fail-closed
# promotion bridge. Keeping the launcher path stable avoids creating a second runtime
# authority while moving the retained lane to the stronger scientific discriminator.
unset \
  GROQ_API_KEY GROQ_API_KEYS GROQ2_API_KEY GROQ3_API_KEY \
  MISTRAL_API_KEY MISTRAL_API_KEYS MISTRAL2_API_KEY MISTRAL3_API_KEY \
  NVIDIA_API_KEY NVIDIA_API_KEYS NVIDIA_NIM_API_KEY NVIDIA2_API_KEY NVIDIA3_API_KEY NGC_API_KEY \
  OPENROUTER_API_KEY OPENROUTER_API_KEYS OPENROUTER2_API_KEY OPENROUTER3_API_KEY \
  TOGETHER_API_KEY TOGETHER_API_KEYS OPENAI_API_KEY OPENAI_API_KEYS \
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
  rm -rf "${RUNNER_TEMP:-/tmp}"/clay-trigger1-v2-* \
         "${RUNNER_TEMP:-/tmp}"/clay-trigger1-qwen06-* \
         "$VENV.tmp" 2>/dev/null || true
  rm -rf "$USER_HOME/.cache/pip" 2>/dev/null || true
fi
AFTER_KB="$(available_kb)"
printf '{"available_kb_before":%s,"available_kb_after":%s}\n' "$BEFORE_KB" "$AFTER_KB" > "$OUT_DIR/disk_preflight.json"
if [[ "$AFTER_KB" -lt 3000000 ]]; then
  python3 - "$OUT_DIR/trigger1_local_activation_api_result.json" "$BEFORE_KB" "$AFTER_KB" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_INSUFFICIENT_FREE_DISK_AFTER_BOUNDED_CLEANUP',
  'available_kb_before':int(sys.argv[2]),
  'available_kb_after':int(sys.argv[3]),
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE',
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
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_LOCAL_INTERMEDIATE',
  'reason':'PYTORCH_TRANSFORMERS_NORMAL_USER_RUNTIME_UNAVAILABLE_AFTER_BOOTSTRAP',
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE',
  'next_action':'REPAIR_NOW_OR_ROUTE_AROUND_CURRENT_LOCAL_INTERMEDIATE_BLOCKER'
}, indent=2, sort_keys=True)+'\n', encoding='utf-8')
PY
  exit 3
fi

export PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}"
INTERMEDIATE_RESULT="$OUT_DIR/trigger1_intermediate_result.json"
INTERMEDIATE_CANDIDATE="$OUT_DIR/trigger1_intermediate_candidate.json"
DIRECT_CANDIDATE="$OUT_DIR/trigger1_direct_steering_candidate.json"
COMPAT_RESULT="$OUT_DIR/trigger1_local_activation_api_result.json"
rm -f "$DIRECT_CANDIDATE"

set +e
"$PYTHON" "$ROOT/tools/trigger1_local_qwen06_intermediate_execute.py" \
  --output-dir "$OUT_DIR" \
  --cache-dir "$HF_HOME"
experiment_rc=$?
set -e

if [[ -s "$INTERMEDIATE_RESULT" ]]; then
  cp "$INTERMEDIATE_RESULT" "$COMPAT_RESULT"
else
  python3 - "$COMPAT_RESULT" "$experiment_rc" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({
  'schema':'CLAY_TRIGGER1_LOCAL_QWEN06_INTERMEDIATE_CONTRASTIVE/v1',
  'status':'BLOCKED_BEFORE_RESULT',
  'process_exit_code':int(sys.argv[2]),
  'zero_provider_billing':True,
  'external_provider_credentials_read':False,
  'provider_network_calls':0,
  'credit_scope':'NONE'
}, indent=2, sort_keys=True)+'\n', encoding='utf-8')
PY
  exit 3
fi

# Scientific negatives and blocked local execution are terminal for this invocation.
# Never manufacture a direct candidate from a non-PASS intermediate result.
if [[ "$experiment_rc" -ne 0 ]]; then
  exit "$experiment_rc"
fi
[[ -s "$INTERMEDIATE_CANDIDATE" ]] || {
  echo 'BLOCKED_INTERMEDIATE_PASS_WITHOUT_CANDIDATE' >&2
  exit 4
}

set +e
"$PYTHON" "$ROOT/tools/trigger1_intermediate_promotion_bridge.py" \
  --result "$INTERMEDIATE_RESULT" \
  --candidate "$INTERMEDIATE_CANDIDATE" \
  --output "$DIRECT_CANDIDATE"
bridge_rc=$?
set -e

if [[ "$bridge_rc" -ne 0 || ! -s "$DIRECT_CANDIDATE" ]]; then
  rm -f "$DIRECT_CANDIDATE"
  echo 'BLOCKED_INTERMEDIATE_PROMOTION_BRIDGE' >&2
  exit 4
fi

exit 0
