#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Canonical paid-training input is SFT v2. V1 is historical only because its
# repeated finite scenario pool contaminates a random held-in split.
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_corpus_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

# Promotion must be falsifiable before money is spent. OOD v2 uses operation/schema
# families that are disjoint from the six training operations and checks fail-closed
# Hyperposition, identity-neutrality and recovery/epistemic contracts.
python3 "$HERE/generate_eval_ood_v2.py"
python3 "$HERE/validate_eval_ood_v2.py" "$HERE/eval_ood_v2.jsonl"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py"

echo
echo "If the BYOM/template gate and price are acceptable, bind the exact preflight fingerprint:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<campaign_fingerprint>"
echo "  python3 $HERE/launch_together_v1.py --create"
echo "Create exactly once; retrieve/reconcile the exact campaign instead of blind retrying."
