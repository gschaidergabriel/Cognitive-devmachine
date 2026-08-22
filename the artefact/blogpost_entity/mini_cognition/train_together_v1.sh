#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_sft_v1.py" "$HERE/train_v2.jsonl"
python3 "$HERE/validate_sft_v1.py" "$HERE/validation_v2.jsonl"
python3 "$HERE/corpus_split_gate_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v2.py"

echo
echo "If the exact BYOM/template gate and price are acceptable, bind the exact preflight fingerprint and create once:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<exact campaign_fingerprint>"
echo "  python3 $HERE/launch_together_v2.py --create"
echo "The adapter reuses the canonical launch_together_v1 paid-create safety path; never blind-retry an ambiguous create."
