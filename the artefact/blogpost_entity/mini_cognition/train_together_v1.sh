#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Canonical paid-training input is SFT v2. V1 is historical only because its
# repeated finite scenario pool contaminates a random held-in split.
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_corpus_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

# Bind the existing canonical BYOM architecture audit to exact Hugging Face revisions
# before Together upload/price/create. This is still only local compatibility evidence.
: "${CLAYCOG_TOGETHER_TEMPLATE:?set an explicitly verified Together full-FT template}"
: "${CLAYCOG_TEMPLATE_HF_REVISION:?set the exact 40-hex Hugging Face revision for the template}"
CLAYCOG_TEMPLATE_HF_MODEL="${CLAYCOG_TEMPLATE_HF_MODEL:-$CLAYCOG_TOGETHER_TEMPLATE}"
python3 "$HERE/audit_together_byom_template_v1.py" \
  --custom-model 'Qwen/Qwen2.5-0.5B' \
  --custom-revision '060db6499f32faf8b98477b0a26969ef7d8b9987' \
  --template-model "$CLAYCOG_TEMPLATE_HF_MODEL" \
  --template-revision "$CLAYCOG_TEMPLATE_HF_REVISION"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py" --template "$CLAYCOG_TOGETHER_TEMPLATE"

echo
echo "If the BYOM/template gate and price are acceptable, bind the exact preflight fingerprint:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<campaign_fingerprint>"
echo "  python3 $HERE/launch_together_v1.py --template \"$CLAYCOG_TOGETHER_TEMPLATE\" --create"
echo "Create exactly once; retrieve the returned job id instead of blind retrying."
