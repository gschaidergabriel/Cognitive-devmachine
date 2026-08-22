#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/generate_sft_v1.py"
python3 "$HERE/validate_sft_v1.py" "$HERE/train_v1.jsonl"
python3 "$HERE/validate_sft_v1.py" "$HERE/validation_v1.jsonl"
python3 "$HERE/generate_eval_ood_v1.py"
python3 "$HERE/generate_eval_ood_v2.py"
PYTHONPATH="$HERE" python3 "$HERE/test_eval_outputs_v1_adversarial.py"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py"

echo
echo "If the BYOM/template gate and price are acceptable, create exactly once with:"
echo "  python3 $HERE/launch_together_v1.py --create"
