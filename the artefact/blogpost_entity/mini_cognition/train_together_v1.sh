#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Compatibility entry point: v2 is now the sole default training corpus. The launcher
# repeats these checks before provider access, so this first block gives a fast local
# failure without weakening the canonical paid-create gates.
echo "=== LOCAL CORPUS V2 GATES ==="
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_sft_v1.py" "$HERE/train_v2.jsonl"
python3 "$HERE/validate_sft_v1.py" "$HERE/validation_v2.jsonl"
python3 "$HERE/corpus_quality_gate_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

echo "=== TOGETHER PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py"

echo
echo "Only after the provider preflight is acceptable, bind its exact fingerprint and create once:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<fingerprint printed by preflight>"
echo "  python3 $HERE/launch_together_v1.py --create"
