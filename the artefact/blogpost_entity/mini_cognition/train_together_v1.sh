#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export CLAYCOG_CORPUS_VERSION="${CLAYCOG_CORPUS_VERSION:-v2}"
echo "=== CLAYCOG 0.5B ${CLAYCOG_CORPUS_VERSION} PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py"

echo
echo "If BYOM/template admission and the <=USD18 price gate are acceptable:"
echo "  export CLAYCOG_CREATE_FINGERPRINT=<exact fingerprint printed above>"
echo "  python3 $HERE/launch_together_v1.py --create"
echo "Never blind-retry create after an ambiguous transport outcome; list/retrieve the deterministic campaign first."
