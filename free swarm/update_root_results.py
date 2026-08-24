#!/usr/bin/env python3
"""Source-bound hot reload + conversion bridge hook for the live FREE pipeline.

The 6000 supervisor already invokes this path every loop when it exists. This
hook turns that dormant call-site into a deterministic reload boundary so long-
running Distillery/Forge processes cannot keep stale Python bytes for 24 hours.
It also runs the credential-blind Forge->Distillery executable-evidence bridge.
It does not grant provider authority, inspect secrets, or mint runtime credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Iterable


def _digest(repo: Path, paths: Iterable[str]) -> str:
    h=hashlib.sha256()
    for rel in sorted(set(paths)):
        p=repo/rel
        h.update(rel.encode("utf-8"));h.update(b"\0")
        if not p.is_file():
            h.update(b"MISSING\0");continue
        h.update(p.read_bytes());h.update(b"\0")
    return h.hexdigest()


def _pids(pattern: str) -> list[int]:
    p=subprocess.run(["pgrep","-f",pattern],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
    out=[]
    for x in p.stdout.split():
        try:
            pid=int(x)
            if pid!=os.getpid():out.append(pid)
        except ValueError:pass
    return out


def _alive(pid: int) -> bool:
    try:os.kill(pid,0);return True
    except (ProcessLookupError,PermissionError):return False


def _stop(pattern: str, timeout_s: float=5.0) -> int:
    pids=_pids(pattern)
    for pid in pids:
        try:os.kill(pid,signal.SIGTERM)
        except ProcessLookupError:pass
    deadline=time.monotonic()+timeout_s
    while time.monotonic()<deadline and any(_alive(pid) for pid in pids):time.sleep(0.1)
    for pid in pids:
        if _alive(pid):
            try:os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:pass
    return len(pids)


def _read(path: Path) -> str:
    try:return path.read_text(encoding="utf-8").strip()
    except OSError:return ""


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text+"\n",encoding="utf-8");tmp.replace(path)


def _spawn(repo: Path, artifacts: Path, argv: list[str], log_name: str) -> int:
    log=artifacts/log_name;log.parent.mkdir(parents=True,exist_ok=True)
    fh=log.open("ab",buffering=0)
    try:
        p=subprocess.Popen(argv,cwd=repo,env=os.environ.copy(),stdin=subprocess.DEVNULL,
                           stdout=fh,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
        return int(p.pid)
    finally:fh.close()


def _ensure_python_component(*,repo:Path,artifacts:Path,name:str,pattern:str,source_paths:list[str],argv:list[str],log_name:str)->dict:
    digest=_digest(repo,source_paths);binding=artifacts/f"{name}.source.binding";previous=_read(binding)
    running=_pids(pattern);restarted=False;stopped=0;pid=None
    if running and previous!=digest:
        stopped=_stop(pattern);running=[];restarted=True
    if not running:
        pid=_spawn(repo,artifacts,argv,log_name);restarted=True
    _atomic(binding,digest)
    return {"name":name,"source_digest":digest,"previous_digest":previous or None,
            "restarted":restarted,"stopped_processes":stopped,"spawned_pid":pid,
            "running_after":bool(_pids(pattern))}


def _forge_to_distillery(repo: Path, artifacts: Path) -> dict:
    script=repo/"tools/ingest_forge_accepts_to_distillery.py"
    if not script.is_file():return {"state":"BRIDGE_SCRIPT_MISSING"}
    status=artifacts/"FORGE_TO_DISTILLERY_BRIDGE.json"
    try:
        p=subprocess.run(
            [sys.executable,str(script),"--artifacts",str(artifacts),"--status-out",str(status)],
            cwd=repo,env=os.environ.copy(),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=20,check=False,
        )
        if p.returncode!=0:
            return {"state":"BRIDGE_ERROR","rc":p.returncode,"stderr":p.stderr[-500:]}
        try:return json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:return {"state":"BRIDGE_OK_UNPARSED","rc":0}
    except Exception as exc:
        return {"state":"BRIDGE_EXCEPTION","error":type(exc).__name__}


def main() -> int:
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--artifacts",required=True)
    args=ap.parse_args();repo=Path(args.repo).resolve();artifacts=Path(args.artifacts).resolve();artifacts.mkdir(parents=True,exist_ok=True)

    distillery_sources=[
        "tools/run_research_distillery.py","tools/run_research_distillery_entry.py","tools/run_research_distillery_local.py",
    ]
    forge_sources=["tools/run_free_evidence_forge.py","tools/run_free_evidence_forge_v2.py"]
    swarm_sources=[
        "tools/run_6000_free_swarm_fast.py","tools/run_6000_free_swarm_v3.py","tools/run_6000_free_swarm.py",
        "tools/free_swarm_accelerator_v2.py","tools/free_lane_provenance.py",
        "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json",
        "governance/FREE_LANE_ECONOMIC_PROVENANCE_2026-08-24.json",
    ]

    events=[]
    # Distillery remains credential-blind under Supervisor 8.71. Restarting it is
    # purely about loading current local/source fixes; the Forge bridge below can
    # add executable knowledge even while no local model is ready.
    events.append(_ensure_python_component(
        repo=repo,artifacts=artifacts,name="distillery",pattern=r"[r]un_research_distillery_local.py",
        source_paths=distillery_sources,
        argv=[sys.executable,str(repo/"tools/run_research_distillery_local.py"),"--hours","24","--sleep-seconds","1"],
        log_name="distillery.log"))

    # Replace the legacy Forge exactly once. The compatibility argv token keeps
    # the existing shell supervisor's pgrep('[r]un_free_evidence_forge.py') true
    # while v2 is alive, so it will not spawn the legacy process beside v2.
    if _pids(r"[r]un_free_evidence_forge.py") and not _pids(r"[r]un_free_evidence_forge_v2.py"):
        _stop(r"[r]un_free_evidence_forge.py")
    events.append(_ensure_python_component(
        repo=repo,artifacts=artifacts,name="forge",pattern=r"[r]un_free_evidence_forge_v2.py",
        source_paths=forge_sources,
        argv=[sys.executable,str(repo/"tools/run_free_evidence_forge_v2.py"),"--compat-name","run_free_evidence_forge.py",
              "--hours","24","--sleep-seconds","2","--questions-per-cycle","32","--discovery-parallel","24",
              "--candidates-per-cycle","48","--local-parallel","12","--e2b-parallel","20"],
        log_name="forge.log"))

    # 6000 restart stays supervisor-owned because that path materializes provider
    # credentials only inside the isolated vault-backed child. We only terminate
    # a stale source-bound child; the shell supervisor restarts it next loop.
    swarm_digest=_digest(repo,swarm_sources);swarm_binding=artifacts/"swarm6000.source.binding"
    previous=_read(swarm_binding);running=_pids(r"[r]un_6000_free_swarm_fast.py");stopped=0
    if running and previous!=swarm_digest:stopped=_stop(r"[r]un_6000_free_swarm_fast.py")
    _atomic(swarm_binding,swarm_digest)
    events.append({"name":"swarm6000","source_digest":swarm_digest,"previous_digest":previous or None,
                   "restarted":bool(stopped),"stopped_processes":stopped,"restart_owner":"run_6000_free_swarm_supervisor.sh",
                   "running_after":bool(_pids(r"[r]un_6000_free_swarm_fast.py"))})

    bridge=_forge_to_distillery(repo,artifacts)
    state={"schema":"CLAY_CONVERSION_SOURCE_RELOAD/v2","observed_at":time.time(),"events":events,
           "forge_to_distillery":bridge,
           "authority_note":"source reload + executable-evidence bridge only; no provider/runtime/canonical promotion"}
    _atomic(artifacts/"CONVERSION_SOURCE_RELOAD.json",json.dumps(state,sort_keys=True,ensure_ascii=False))
    return 0


if __name__=="__main__":raise SystemExit(main())
