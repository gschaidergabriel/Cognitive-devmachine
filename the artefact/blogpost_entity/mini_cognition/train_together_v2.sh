#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_sft_v1.py" "$HERE/train_v2.jsonl"
python3 "$HERE/validate_sft_v1.py" "$HERE/validation_v2.jsonl"
python3 "$HERE/corpus_diversity_gate_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"
python3 "$HERE/generate_eval_ood_v2.py"
echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v2.py" "$@"
