#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Canonical training input is ClayCog SFT v2. The v1 corpus is retained only as
# historical evidence and must not be uploaded because its random split can contain
# exact duplicate scenarios across train/validation.
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_corpus_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py"

echo
echo "Only if the API Full-FT template gate, BYOM admission and server price are acceptable:"
echo "  python3 $HERE/launch_together_v1.py --create"
echo "Create exactly once; persist and reuse the returned job id."
