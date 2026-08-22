#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Canonical paid-training input is SFT v2. V1 is historical only because its
# repeated finite scenario pool contaminates a random held-in split.
python3 "$HERE/generate_sft_v2.py"
python3 "$HERE/validate_corpus_v2.py" "$HERE/train_v2.jsonl" "$HERE/validation_v2.jsonl"

# Promotion evidence is prepared before provider interaction. Keep the canonical
# 200-case OOD gate and add a separate training-disjoint novel-schema gate rather
# than replacing #802 exact-omega semantics.
python3 "$HERE/generate_eval_ood_v1.py"
python3 "$HERE/generate_eval_novel_schema_v1.py"
python3 "$HERE/validate_eval_novel_schema_v1.py" "$HERE/eval_novel_schema_v1.jsonl"
python3 "$HERE/test_eval_novel_schema_v1.py"

echo "=== PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py"

echo
echo "If every provider/provenance gate and price are acceptable, bind the exact preflight fingerprint:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<campaign_fingerprint>"
echo "  python3 $HERE/launch_together_v1.py --create"
echo "Create exactly once; reconcile the durable local intent/provider job instead of blind retrying."
