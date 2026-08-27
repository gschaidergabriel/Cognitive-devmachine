#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# OWNER EMERGENCY STOP — 2026-08-26.
# The FreeSwarm supervisor is disabled. Invoking it performs the same kill-only
# shutdown sweep as the activator and never starts a worker, Forge, Distillery,
# dashboard, local swarm model, or provider route.
exec bash "$ROOT/tools/activate_6000_free_swarm.sh"
