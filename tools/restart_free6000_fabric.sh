#!/usr/bin/env bash
set -Eeuo pipefail
STATE=/artifacts/clay-entityos-swarm
for pid in $(pgrep -f '[r]un_6000_free_swarm_fast.py' || true); do
  kill "$pid" 2>/dev/null || true
done
for _ in $(seq 1 30); do
  sleep 1
  if pgrep -f '[r]un_6000_free_swarm_fast.py' >/dev/null 2>&1; then
    echo FABRIC_RESTARTED
    pgrep -af '[r]un_6000_free_swarm_fast.py'
    exit 0
  fi
done
echo FABRIC_RESTART_PENDING_SUPERVISOR
cat "$STATE/SUPERVISOR_6000.json" 2>/dev/null || true
exit 1
