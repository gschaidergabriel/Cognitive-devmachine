#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Canonical paid-training input is SFT v2. V1 is historical only because its
# repeated finite scenario pool contaminates a random held-in split.
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_corpus_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

# BYOM architecture is checked against exact Hugging Face config revisions before any
# Together file upload/price/create path. This is a local compatibility gate only;
# Together provider admission remains authoritative.
: "${CLAYCOG_TOGETHER_TEMPLATE:?set an explicitly verified Together full-FT template}"
: "${CLAYCOG_TEMPLATE_HF_REVISION:?set the exact 40-hex Hugging Face revision for the template}"
CLAYCOG_TEMPLATE_HF_MODEL="${CLAYCOG_TEMPLATE_HF_MODEL:-$CLAYCOG_TOGETHER_TEMPLATE}"
TMP_ARCH="$(mktemp -d)"
trap 'rm -rf "$TMP_ARCH"' EXIT
python3 "$HERE/hf_architecture_attestation_v1.py" fetch \
  --model 'Qwen/Qwen2.5-0.5B' \
  --revision '060db6499f32faf8b98477b0a26969ef7d8b9987' \
  --output "$TMP_ARCH/target.json"
python3 "$HERE/hf_architecture_attestation_v1.py" fetch \
  --model "$CLAYCOG_TEMPLATE_HF_MODEL" \
  --revision "$CLAYCOG_TEMPLATE_HF_REVISION" \
  --output "$TMP_ARCH/template.json"
python3 "$HERE/hf_architecture_attestation_v1.py" compare \
  --target "$TMP_ARCH/target.json" \
  --template "$TMP_ARCH/template.json"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py" --template "$CLAYCOG_TOGETHER_TEMPLATE"

echo
echo "If the BYOM/template gate and price are acceptable, bind the exact preflight fingerprint:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<campaign_fingerprint>"
echo "  python3 $HERE/launch_together_v1.py --template \"$CLAYCOG_TOGETHER_TEMPLATE\" --create"
echo "Create exactly once; retrieve the returned job id instead of blind retrying."
