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
echo "If the BYOM/template gate and price are acceptable, create exactly once with:"
echo "  python3 $HERE/launch_together_v2.py --create"
echo "The v2 create guard is written before the API create call; if a create attempt becomes uncertain, inspect Together jobs instead of retrying blindly."
