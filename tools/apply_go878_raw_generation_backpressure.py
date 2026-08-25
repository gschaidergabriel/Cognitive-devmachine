#!/usr/bin/env python3
"""Exact-source Supervisor-8.78 raw-generation backpressure repair.

Supervisor 8.78 requires zero-cost capacity to move away from new raw generation while
historical conversion pressure is above threshold. The current 6000 supervisor applies
BACKLOG_FIRST only inside Forge discovery, yet still unconditionally calls start_6000().
This patcher closes that control-plane gap without increasing any provider concurrency,
reading credentials, or creating another Forge/effect authority.

The patch is deliberately pinned to the exact inspected supervisor blob and fail-closes
on source movement. Applying this file is source work only; runtime credit requires a
later admitted exact-source execution receipt.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

TARGET_REL = "tools/run_6000_free_swarm_supervisor.sh"
EXPECTED_TARGET_BLOB = "cdbe6a4da423b2fb35fe988adc04397407360c3f"


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "hash-object", rel], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_MARKER_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


RAW_GENERATION_GATE = r'''raw_generation_allowed(){
  # Supervisor 8.78 conversion-pressure gate. This process is credential blind:
  # it reads only the local canonical Forge DB and writes one local status record.
  python3 - <<'PY'
import datetime,json,os,sqlite3
from pathlib import Path

threshold=max(1,int(os.getenv('CLAY_SWARM_RAW_GENERATION_BACKPRESSURE_THRESHOLD','64')))
state_root=Path('/artifacts/clay-entityos-swarm')
db=state_root/'forge/forge.sqlite3'
status_path=state_root/'RAW_GENERATION_BACKPRESSURE.json'
status={
 'schema':'CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v1',
 'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'threshold':threshold,
 'source':'FORGE_SQLITE_CANONICAL_LOCAL_STATE',
 'external_provider_calls':0,
 'credentials_read':False,
}
allowed=False
try:
 if not db.exists():
  status.update({'state':'UNKNOWN_FORGE_DB','action':'PAUSE_RAW_GENERATION_FAIL_CLOSED'})
 else:
  con=sqlite3.connect(f'file:{db}?mode=ro',uri=True,timeout=2.0)
  tables={str(r[0]) for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if 'candidates' not in tables:
   status.update({'state':'UNKNOWN_CANDIDATE_TABLE','action':'PAUSE_RAW_GENERATION_FAIL_CLOSED'})
  else:
   ready=int(con.execute("SELECT COUNT(*) FROM candidates WHERE ready=1 AND state='NEW'").fetchone()[0])
   implementation=int(con.execute("SELECT COUNT(*) FROM candidates WHERE state='NEEDS_IMPLEMENTATION'").fetchone()[0])
   pending=0
   if 'historical_chunks' in tables:
    pending=int(con.execute("SELECT COUNT(*) FROM historical_chunks WHERE state='PENDING_EXTRACTION'").fetchone()[0])
   pressure=ready+implementation+pending
   allowed=pressure < threshold
   status.update({
    'state':'OBSERVED',
    'ready_backlog':ready,
    'implementation_backlog':implementation,
    'pending_extraction':pending,
    'conversion_pressure':pressure,
    'action':'ALLOW_RAW_GENERATION' if allowed else 'PAUSE_RAW_GENERATION_BACKPRESSURE',
   })
  con.close()
except Exception as exc:
 status.update({'state':'READ_FAILED','action':'PAUSE_RAW_GENERATION_FAIL_CLOSED','error_class':type(exc).__name__})
tmp=status_path.with_suffix('.json.tmp')
tmp.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n',encoding='utf-8')
tmp.replace(status_path)
raise SystemExit(0 if allowed else 1)
PY
}

'''


def patch(text: str) -> str:
    if "CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v1" in text:
        raise SystemExit("RAW_GENERATION_BACKPRESSURE_ALREADY_PRESENT")
    text = replace_once(text, "start_6000(){\n", RAW_GENERATION_GATE + "start_6000(){\n", "INSERT_GATE")
    text = replace_once(
        text,
        "  reconcile_6000_admission\n  start_6000\n  refresh_root_results",
        "  reconcile_6000_admission\n  if raw_generation_allowed; then\n    start_6000\n  else\n    stop_6000\n  fi\n  refresh_root_results",
        "CONTROL_LOOP_GATE",
    )
    return text


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args=ap.parse_args()
    repo=args.repo.resolve()
    target=repo/TARGET_REL
    observed=git_blob(repo,TARGET_REL)
    if observed != EXPECTED_TARGET_BLOB:
        raise SystemExit(
            f"SWARM_SUPERVISOR_MOVED_FAIL_CLOSED:expected={EXPECTED_TARGET_BLOB}:observed={observed}"
        )
    target.write_text(patch(target.read_text(encoding="utf-8")),encoding="utf-8")
    subprocess.run(["bash","-n",str(target)],check=True)
    print("GO878_RAW_GENERATION_BACKPRESSURE_PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
