#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "CLAYCOG_V1_DEPRECATED: routing through train_together_v2.sh" >&2
exec bash "$HERE/train_together_v2.sh" "$@"
