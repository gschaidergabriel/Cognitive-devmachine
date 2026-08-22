#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Canonical paid-training input is SFT v2. V1 is historical only because its
# repeated finite scenario pool contaminates a random held-in split.
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_corpus_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

# The launcher itself now runs the canonical exact-revision BYOM architecture audit and
# binds its provenance into the campaign fingerprint/create-intent before Together calls.
: "${CLAYCOG_TOGETHER_TEMPLATE:?set an explicitly verified Together full-FT template}"
: "${CLAYCOG_TEMPLATE_HF_REVISION:?set the exact 40-hex Hugging Face revision for the template}"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py" --template "$CLAYCOG_TOGETHER_TEMPLATE"

echo
echo "If the BYOM/template gate and price are acceptable, bind the exact preflight fingerprint:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<campaign_fingerprint>"
echo "  python3 $HERE/launch_together_v1.py --template \"$CLAYCOG_TOGETHER_TEMPLATE\" --create"
echo "Create exactly once; the launcher re-runs and re-binds the exact architecture audit before create."
echo "Retrieve the returned job id instead of blind retrying."
