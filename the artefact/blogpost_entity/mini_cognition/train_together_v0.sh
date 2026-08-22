#!/usr/bin/env bash
set -euo pipefail

: "${TOGETHER_API_KEY:?TOGETHER_API_KEY must be exported in the shell; never commit it}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

python3 launch_together_v0.py

# After the job is created, retain its exact ft-... ID.
# Inspect before any retry:
#   tg fine-tuning list
#   tg fine-tuning retrieve <FT_ID>
#   tg fine-tuning list-events <FT_ID>
#
# Full fine-tuning produces complete model weights. Download/export them after
# completion, then quantize the text-only artifact and execute the <1 GiB RSS gate.
