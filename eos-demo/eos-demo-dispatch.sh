#!/bin/bash
# Auto-Poller: verarbeitet neue Screenshot-Requests von Zero (Container schreibt sie).
set -u
REQ=/var/lib/clay/eos-demo-requests
[ -d "$REQ" ] || exit 0
shopt -s nullglob
for f in "$REQ"/*.json; do
  case "$f" in *.done.json) continue;; esac
  id=$(basename "$f" .json)
  [ -f "$REQ/$id.done.json" ] && continue
  bash /opt/entityos/eos-demo/eos-screenshot.sh "$id" || true
done
