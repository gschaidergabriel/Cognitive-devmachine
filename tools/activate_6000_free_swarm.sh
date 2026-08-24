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
python3 -m py_compile tools/run_6000_free_swarm.py tools/run_6000_free_swarm_fast.py tools/run_24h_entityos_swarm.py tools/run_free_go_swarm.py
bash -n tools/run_6000_free_swarm_supervisor.sh
echo COMPILE_PASS

echo '--- STOP EXACT LEGACY PROCESSES ---'
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
 try:
  raw=open(f'/proc/{pid}/cmdline','rb').read().split(b'\0')
 except OSError: continue
 args=[x.decode('utf-8','replace') for x in raw if x]
 if not args: continue
 hit=False
 for arg in args[1:3]:
  if any(arg.endswith(s) for s in exact_suffixes): hit=True
 if hit:
  try:
   os.kill(pid,signal.SIGTERM); print('TERM',pid,' '.join(args[:3]))
  except (ProcessLookupError,PermissionError): pass
PY
sleep 2

echo '--- START 6000 SUPERVISOR ---'
export CLAY_LOGICAL_WORKERS="${CLAY_LOGICAL_WORKERS:-6000}"
export CLAY_SWARM_HTTP_THREADS="${CLAY_SWARM_HTTP_THREADS:-256}"
nohup bash tools/run_6000_free_swarm_supervisor.sh >"$STATE/supervisor6000.log" 2>&1 </dev/null &
echo $! >"$STATE/supervisor6000.pid"
echo "SUPERVISOR_PID=$!"

for _ in $(seq 1 20); do
  sleep 2
  if [[ -s "$STATE/SUPERVISOR_6000.json" ]]; then break; fi
done

echo '--- PROCESSES ---'
ps -eo pid,etime,%cpu,%mem,args | grep -E 'run_6000_free_swarm_supervisor|run_6000_free_swarm_fast|run_research_distillery|run_free_evidence_forge|free swarm/evaluate.py' | grep -v grep | head -60 || true

echo '--- SUPERVISOR STATUS ---'
cat "$STATE/SUPERVISOR_6000.json" 2>/dev/null || true

echo '--- FABRIC STATUS ---'
latest="$(find "$STATE" -maxdepth 2 -path '*active-fabric6000-*/status.json' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-)"
[[ -n "$latest" ]] && cat "$latest" || true

echo '--- SWARM LOG ---'
tail -120 "$STATE/swarm6000.log" 2>/dev/null || true
