#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_sft_v2.py" "$HERE/train_v2.jsonl" --against "$HERE/validation_v2.jsonl"
python3 "$HERE/validate_sft_v2.py" "$HERE/validation_v2.jsonl" --against "$HERE/train_v2.jsonl"
python3 "$HERE/generate_eval_ood_v2.py"
echo "=== TOGETHER PREFLIGHT ONLY; requires explicit current Qwen2-compatible template ==="
python3 "$HERE/launch_together_v2.py"
