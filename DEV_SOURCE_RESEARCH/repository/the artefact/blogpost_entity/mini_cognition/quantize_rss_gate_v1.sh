#!/usr/bin/env bash
set -euo pipefail
: "${LLAMA_CPP_DIR:?set LLAMA_CPP_DIR to pinned llama.cpp checkout}"
: "${HF_MODEL_DIR:?set HF_MODEL_DIR to downloaded fine-tuned HF checkpoint}"
OUT_DIR="${CLAYCOG_OUT_DIR:-$PWD/claycog-05b-gguf}"
CTX="${CLAYCOG_CTX:-2048}"
mkdir -p "$OUT_DIR"
F16="$OUT_DIR/claycog-05b-f16.gguf"
Q4="$OUT_DIR/claycog-05b-q4_k_m.gguf"
RECEIPT="$OUT_DIR/rss_receipt.json"

python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" "$HF_MODEL_DIR" --outfile "$F16" --outtype f16
"$LLAMA_CPP_DIR/build/bin/llama-quantize" "$F16" "$Q4" Q4_K_M

bytes="$(stat -c %s "$Q4")"
if [ "$bytes" -ge 1073741824 ]; then
  echo "FAIL: GGUF >= 1 GiB" >&2; exit 21
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
/usr/bin/time -v "$LLAMA_CPP_DIR/build/bin/llama-cli" \
  -m "$Q4" -c "$CTX" -n 32 -p 'Represent UNKNOWN sensor state in ClayCode only.' \
  >/dev/null 2>"$TMP"
rss_kb="$(awk -F: '/Maximum resident set size/{gsub(/^[ \t]+/,"",$2); print $2}' "$TMP")"
if [ -z "$rss_kb" ]; then echo "FAIL: RSS not measured" >&2; exit 22; fi
if [ "$rss_kb" -ge 1048576 ]; then echo "FAIL: peak RSS ${rss_kb} KiB >= 1 GiB" >&2; exit 23; fi
sha="$(sha256sum "$Q4" | awk '{print $1}')"
python3 - "$RECEIPT" "$Q4" "$sha" "$bytes" "$rss_kb" "$CTX" <<'PY'
import json,sys
p,model,sha,b,rss,ctx=sys.argv[1:]
json.dump({
 "schema":"claycog-rss-gate/v1","model":model,"sha256":sha,
 "bytes":int(b),"context":int(ctx),"peak_rss_kib":int(rss),
 "artifact_under_1gib":int(b)<1073741824,
 "peak_rss_under_1gib":int(rss)<1048576
},open(p,"w"),indent=2)
PY
cat "$RECEIPT"
