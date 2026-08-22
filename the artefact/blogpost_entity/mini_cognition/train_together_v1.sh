#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Compatibility entry point: v2 is now the default training corpus. The launcher
# regenerates the data, runs structural validation, and fails closed on the v2
# leakage/diversity gate before any provider upload or billed create.
echo "=== LOCAL CORPUS V2 GATES ==="
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_sft_v1.py" "$HERE/train_v2.jsonl"
python3 "$HERE/validate_sft_v1.py" "$HERE/validation_v2.jsonl"
python3 "$HERE/corpus_quality_gate_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

echo "=== TOGETHER PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py" --corpus v2

echo
echo "Only after the provider preflight is acceptable, create exactly once with:"
echo "  python3 $HERE/launch_together_v1.py --corpus v2 --create"
