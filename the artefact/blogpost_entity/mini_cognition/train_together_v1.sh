#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== CLAYCOG 0.5B V2 PRE-FLIGHT: no billed job ==="
python3 "$HERE/launch_together_v1.py" --corpus v2

echo
echo "If the exact BYOM/template gate and price are acceptable, create exactly once with:"
echo "  python3 $HERE/launch_together_v1.py --corpus v2 --create"
echo "Do not retry create blindly; retrieve the returned Together job id instead."
