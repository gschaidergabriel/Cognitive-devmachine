#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STATE=/artifacts/clay-entityos-swarm
mkdir -p "$STATE"

echo "HEAD=$(git rev-parse HEAD)"
echo '--- PREFLIGHT ---'
df -h /workspace /cache /artifacts
free -h

echo '--- ADMISSION ---'
python3 tools/free_provider_admission.py --json

echo '--- COMPILE ---'
python3 -m py_compile \
  tools/free_swarm_exec_with_vault.py \
  tools/free_swarm_accelerator_v2.py \
  tools/run_6000_free_swarm.py \
  tools/run_6000_free_swarm_v3.py \
  tools/run_6000_free_swarm_fast.py \
  tools/run_24h_entityos_swarm.py \
  tools/run_free_go_swarm.py
bash -n tools/run_6000_free_swarm_supervisor.sh
echo COMPILE_PASS

echo '--- STOP EXACT LEGACY/FABRIC PROCESSES ---'
python3 - <<'PY'
import os,signal
exact_suffixes={
 'tools/run_24h_entityos_swarm_supervisor.sh',
 'tools/run_24h_entityos_swarm.py',
 'tools/run_6000_free_swarm_supervisor.sh',
 'tools/run_6000_free_swarm_fast.py',
}
me=os.getpid(); parent=os.getppid()
for name in os.listdir('/proc'):
 if not name.isdigit(): continue
 pid=int(name)
 if pid in {me,parent}: continue
 try: raw=open(f'/proc/{pid}/cmdline','rb').read().split(b'\0')
 except OSError: continue
 args=[x.decode('utf-8','replace') for x in raw if x]
 if not args: continue
 if any(any(arg.endswith(s) for s in exact_suffixes) for arg in args[1:4]):
  try: os.kill(pid,signal.SIGTERM); print('TERM',pid,' '.join(args[:4]))
  except (ProcessLookupError,PermissionError): pass
PY
sleep 3

echo '--- START CREDENTIAL-BLIND 6000 SUPERVISOR ---'
export CLAY_LOGICAL_WORKERS="${CLAY_LOGICAL_WORKERS:-6000}"
export CLAY_SWARM_HTTP_THREADS="${CLAY_SWARM_HTTP_THREADS:-512}"
# Do not wrap the long-lived supervisor in the vault loader. The supervisor
# starts local/non-provider children credential-blind and launches only the
# dedicated external-provider fabric child through free_swarm_exec_with_vault.py.
nohup bash tools/run_6000_free_swarm_supervisor.sh >"$STATE/supervisor6000.log" 2>&1 </dev/null &
echo $! >"$STATE/supervisor6000.pid"
echo "SUPERVISOR_PID=$!"

for _ in $(seq 1 30); do
  sleep 2
  if [[ -s "$STATE/SUPERVISOR_6000.json" ]] && grep -q '"fabric_running": true' "$STATE/SUPERVISOR_6000.json"; then break; fi
done

echo '--- CREDENTIAL POOL (SWARM CHILD RECEIPT ONLY) ---'
cat "$STATE/CREDENTIAL_POOL.json" 2>/dev/null || true

echo '--- PROCESSES ---'
ps -eo pid,etime,%cpu,%mem,args | grep -E 'run_6000_free_swarm_supervisor|run_6000_free_swarm_fast|run_research_distillery|run_free_evidence_forge|free swarm/evaluate.py' | grep -v grep | head -60 || true

echo '--- SUPERVISOR STATUS ---'
cat "$STATE/SUPERVISOR_6000.json" 2>/dev/null || true

echo '--- SWARM LOG ---'
tail -120 "$STATE/swarm6000.log" 2>/dev/null || true
