#!/usr/bin/env bash
set -euo pipefail
: "${TOGETHER_API_KEY:?TOGETHER_API_KEY must be exported in the shell; never commit it}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
python3 launch_together_v0.py

# Before any manual retry:
#   tg fine-tuning list
#   tg fine-tuning retrieve <FT_ID>
#   tg fine-tuning list-events <FT_ID>
