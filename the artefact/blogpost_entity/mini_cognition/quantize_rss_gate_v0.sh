#!/usr/bin/env bash
set -euo pipefail

: "${LLAMA_CPP_DIR:?set LLAMA_CPP_DIR to an exact pinned llama.cpp checkout}"
: "${HF_MODEL_DIR:?set HF_MODEL_DIR to the downloaded full fine-tuned model directory}"

OUT_DIR="${OUT_DIR:-$(pwd)/quantized_v0}"
CONTEXT="${CLAYCOG_CONTEXT:-2048}"
MAX_RSS_KIB="${CLAYCOG_MAX_RSS_KIB:-1048575}"
MAX_MODEL_BYTES="${CLAYCOG_MAX_MODEL_BYTES:-734003200}"
mkdir -p "$OUT_DIR"
F16="$OUT_DIR/claycog-generic-v0-f16.gguf"
Q4="$OUT_DIR/claycog-generic-v0-Q4_K_M.gguf"
TIME_LOG="$OUT_DIR/rss-Q4_K_M-c${CONTEXT}.txt"
STDOUT_LOG="$OUT_DIR/probe-Q4_K_M-c${CONTEXT}.txt"

python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" "$HF_MODEL_DIR" --outfile "$F16"
"$LLAMA_CPP_DIR/build/bin/llama-quantize" "$F16" "$Q4" Q4_K_M
bytes="$(stat -c '%s' "$Q4")"
if (( bytes >= 1073741824 )); then echo "FAIL: quantized artifact is not <1 GiB: $bytes bytes" >&2; exit 21; fi
if (( bytes > MAX_MODEL_BYTES )); then echo "WARN: Q4_K_M artifact exceeds preferred 700 MiB: $bytes bytes" >&2; fi

# Text-only baseline: no vision/mmproj projector.
/usr/bin/time -v \
  "$LLAMA_CPP_DIR/build/bin/llama-cli" \
  -m "$Q4" -c "$CONTEXT" -n 64 --temp 0 \
  -p 'Represent the observation UNKNOWN safely in ClayCode.' \
  >"$STDOUT_LOG" 2>"$TIME_LOG"

rss_kib="$(awk -F: '/Maximum resident set size \(kbytes\)/ {gsub(/^[ \t]+/,"",$2); print $2}' "$TIME_LOG")"
if [[ -z "$rss_kib" ]]; then echo "FAIL: could not parse peak RSS" >&2; exit 22; fi
if (( rss_kib > MAX_RSS_KIB )); then echo "FAIL: peak RSS ${rss_kib} KiB is not <1 GiB" >&2; exit 23; fi

sha256sum "$Q4" > "$OUT_DIR/Q4_K_M.sha256"
cat > "$OUT_DIR/acceptance.json" <<EOF
{
  "schema": "claycog-quant-rss/v0",
  "quant": "Q4_K_M",
  "text_only": true,
  "context_tokens": $CONTEXT,
  "artifact_bytes": $bytes,
  "peak_rss_kib": $rss_kib,
  "artifact_under_1gib": true,
  "runtime_peak_rss_under_1gib": true
}
EOF
cat "$OUT_DIR/acceptance.json"
