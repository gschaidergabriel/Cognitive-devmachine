#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STATE=/artifacts/clay-entityos-swarm
mkdir -p "$STATE"

# OWNER EMERGENCY STOP — 2026-08-26.
# This entrypoint is intentionally kill-only. It MUST NOT start/restart any
# FreeSwarm, Forge, Distillery, dashboard, or swarm-local-model process.
# Re-enabling requires a later explicit owner instruction and source change.

echo "HEAD=$(git rev-parse HEAD)"
echo '--- FREE SWARM OWNER EMERGENCY STOP: KILL ONLY ---'

python3 - <<'PY'
import json, os, signal, time
from datetime import datetime, timezone
from pathlib import Path

state = Path('/artifacts/clay-entityos-swarm')
state.mkdir(parents=True, exist_ok=True)
# Exact process entrypoints owned/spawned by the FreeSwarm runtime family.
suffixes = {
    'tools/run_24h_entityos_swarm_supervisor.sh',
    'tools/run_24h_entityos_swarm.py',
    'tools/run_6000_free_swarm_supervisor.sh',
    'tools/run_6000_free_swarm_fast.py',
    'tools/run_6000_free_swarm.py',
    'tools/run_6000_free_swarm_v3.py',
    'tools/run_6000_free_swarm_v5.py',
    'tools/run_free_go_swarm.py',
    'tools/run_go_zero_swarm.py',
    'tools/run_research_distillery_local.py',
    'tools/run_research_distillery_entry.py',
    'tools/run_free_evidence_forge.py',
    'tools/run_free_evidence_forge_backfill.py',
    'tools/run_free_evidence_forge_safe.py',
    'tools/run_free_evidence_forge_safe_871.py',
    'tools/run_forge_distillery_bridge_loop.py',
    'tools/local_research_model_server.sh',
    'free swarm/evaluate.py',
    'free swarm/update_fabric_live.py',
}
me = os.getpid()
parent = os.getppid()

def matches(pid: int):
    try:
        raw = Path(f'/proc/{pid}/cmdline').read_bytes()
    except OSError:
        return None
    args = [x.decode('utf-8', 'replace') for x in raw.split(b'\0') if x]
    if any(any(arg.endswith(s) for s in suffixes) for arg in args[:10]):
        return args
    return None

def scan():
    found = []
    for name in os.listdir('/proc'):
        if not name.isdigit():
            continue
        pid = int(name)
        if pid in {me, parent}:
            continue
        args = matches(pid)
        if args:
            found.append((pid, args))
    return found

initial = scan()
for pid, args in initial:
    try:
        os.kill(pid, signal.SIGTERM)
        print('TERM', pid, ' '.join(args[:5]))
    except (ProcessLookupError, PermissionError) as exc:
        print('TERM_FAILED', pid, type(exc).__name__)

time.sleep(4)
remaining = scan()
for pid, args in remaining:
    try:
        os.kill(pid, signal.SIGKILL)
        print('KILL', pid, ' '.join(args[:5]))
    except (ProcessLookupError, PermissionError) as exc:
        print('KILL_FAILED', pid, type(exc).__name__)

time.sleep(1)
survivors = scan()
record = {
    'schema': 'CLAY_FREE_SWARM_OWNER_EMERGENCY_STOP/v1',
    'observed_at': datetime.now(timezone.utc).isoformat(),
    'state': 'OFF' if not survivors else 'STOP_INCOMPLETE',
    'initial_matching_processes': [pid for pid, _ in initial],
    'survivors': [{'pid': pid, 'args': args[:5]} for pid, args in survivors],
    'provider_admission_expected': 'ALL_DISABLED',
    'restart_allowed': False,
    'owner_stop_date': '2026-08-26',
}
(state / 'OWNER_EMERGENCY_STOP.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
(state / 'SUPERVISOR_6000.json').write_text(json.dumps({
    'schema': 'CLAY_6000_SWARM_SUPERVISOR/v4',
    'state': record['state'],
    'owner_emergency_stop': True,
    'restart_allowed': False,
}, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, indent=2))
raise SystemExit(0 if not survivors else 9)
PY

echo 'FREE_SWARM_OFF'
