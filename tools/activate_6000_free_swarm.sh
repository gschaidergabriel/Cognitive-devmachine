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
  tools/forge_execution_admission_871.py \
  tools/run_free_evidence_forge_safe_871.py \
  tools/run_free_evidence_forge_safe.py \
  tools/forge_evidence_credit_871.py \
  tools/ingest_forge_accepts_into_distillery.py \
  tools/run_forge_distillery_bridge_loop.py \
  tools/run_24h_entityos_swarm.py \
  tools/run_free_go_swarm.py \
  "free swarm/update_fabric_live.py"
bash -n tools/run_6000_free_swarm_supervisor.sh
echo COMPILE_PASS

echo '--- STOP EXACT LEGACY/FABRIC PROCESSES ---'
python3 - <<'PY'
import os,signal
suffixes={
 'tools/run_24h_entityos_swarm_supervisor.sh',
 'tools/run_24h_entityos_swarm.py',
 'tools/run_6000_free_swarm_supervisor.sh',
 'tools/run_6000_free_swarm_fast.py',
 'tools/run_free_evidence_forge.py',
 'tools/run_free_evidence_forge_safe.py',
 'tools/run_forge_distillery_bridge_loop.py',
 'free swarm/update_fabric_live.py',
}
me=os.getpid(); parent=os.getppid()
for name in os.listdir('/proc'):
 if not name.isdigit(): continue
 pid=int(name)
 if pid in {me,parent}: continue
 try: args=[x.decode('utf-8','replace') for x in open(f'/proc/{pid}/cmdline','rb').read().split(b'\0') if x]
 except OSError: continue
 if any(any(arg.endswith(s) for s in suffixes) for arg in args[1:5]):
  try: os.kill(pid,signal.SIGTERM); print('TERM',pid,' '.join(args[:4]))
  except (ProcessLookupError,PermissionError): pass
PY
sleep 4
# Fabric workers can spend minutes draining in-flight HTTP after SIGTERM. For an
# explicit operator restart, bound that drain so the replacement high-throughput
# fabric is not blocked by the old PID.
python3 - <<'PY'
import os,signal
suffixes={
 'tools/run_24h_entityos_swarm_supervisor.sh',
 'tools/run_24h_entityos_swarm.py',
 'tools/run_6000_free_swarm_fast.py',
 'tools/run_free_evidence_forge.py',
 'tools/run_free_evidence_forge_safe.py',
 'tools/run_forge_distillery_bridge_loop.py',
 'free swarm/update_fabric_live.py',
}
me=os.getpid(); parent=os.getppid()
for name in os.listdir('/proc'):
 if not name.isdigit(): continue
 pid=int(name)
 if pid in {me,parent}: continue
 try: args=[x.decode('utf-8','replace') for x in open(f'/proc/{pid}/cmdline','rb').read().split(b'\0') if x]
 except OSError: continue
 if any(any(arg.endswith(s) for s in suffixes) for arg in args[1:5]):
  try: os.kill(pid,signal.SIGKILL); print('KILL',pid,' '.join(args[:4]))
  except (ProcessLookupError,PermissionError): pass
PY

echo '--- START CREDENTIAL-BLIND 6000 SUPERVISOR ---'
export CLAY_LOGICAL_WORKERS="${CLAY_LOGICAL_WORKERS:-6000}"
export CLAY_SWARM_HTTP_THREADS="${CLAY_SWARM_HTTP_THREADS:-512}"
nohup bash tools/run_6000_free_swarm_supervisor.sh >"$STATE/supervisor6000.log" 2>&1 </dev/null &
echo $! >"$STATE/supervisor6000.pid"
echo "SUPERVISOR_PID=$!"

# Dataset reconciliation is deliberately separate from the provider-bearing
# swarm child. It is credential-blind, network-free and delegates admission to
# the exact current Forge evidence-credit discriminator.
nohup python3 tools/run_forge_distillery_bridge_loop.py \
  --sleep-seconds "${CLAY_FORGE_DISTILLERY_BRIDGE_SLEEP_SECONDS:-2}" \
  --reconcile-seconds "${CLAY_FORGE_DISTILLERY_BRIDGE_RECONCILE_SECONDS:-15}" \
  >"$STATE/forge-distillery-bridge.log" 2>&1 </dev/null &
echo $! >"$STATE/forge-distillery-bridge.pid"
echo "FORGE_DISTILLERY_BRIDGE_PID=$!"

nohup python3 "free swarm/update_fabric_live.py" --repo "$ROOT" --artifacts "$STATE" --watch --interval-seconds 20 >"$STATE/fabric-dashboard.log" 2>&1 </dev/null &
echo $! >"$STATE/fabric-dashboard.pid"

for _ in $(seq 1 30); do
  sleep 2
  if [[ -s "$STATE/SUPERVISOR_6000.json" ]] && grep -q '"fabric_running": true' "$STATE/SUPERVISOR_6000.json"; then break; fi
done

echo '--- CREDENTIAL POOL (SWARM CHILD RECEIPT ONLY) ---'
cat "$STATE/CREDENTIAL_POOL.json" 2>/dev/null || true

echo '--- PROCESSES ---'
ps -eo pid,etime,%cpu,%mem,args | grep -E 'run_6000_free_swarm_supervisor|run_6000_free_swarm_fast|run_forge_distillery_bridge_loop|run_research_distillery|run_free_evidence_forge|free swarm/evaluate.py|update_fabric_live.py' | grep -v grep | head -60 || true

echo '--- FORGE→DISTILLERY EVIDENCE-QUALIFIED BRIDGE ---'
cat "$STATE/distillery/forge_execution_ingest_status.json" 2>/dev/null || true

echo '--- SUPERVISOR STATUS ---'
cat "$STATE/SUPERVISOR_6000.json" 2>/dev/null || true

echo '--- SWARM LOG ---'
tail -120 "$STATE/swarm6000.log" 2>/dev/null || true
