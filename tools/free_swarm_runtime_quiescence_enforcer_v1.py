#!/usr/bin/env python3
"""Fail-closed FreeSwarm runtime quiescence enforcer.

Purpose: close the P0 post-stop provider-drift blocker without issuing provider probes.
The tool only terminates exact legacy FreeSwarm/provider-capable process classes and their
process-tree descendants, then delegates the bounded proof to
free_swarm_runtime_quiescence_probe_v1.py.

Safety:
- dry-run unless --apply is passed;
- refuses to act unless canonical FREE_PROVIDER_ADMISSION is HARD_OFF;
- never pattern-kills arbitrary python/shell processes;
- roots are matched only by exact known script basename/path needles;
- descendants are included only by PPID ancestry from a matched root;
- emits a machine-readable receipt.
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
from typing import Any

SCHEMA = "CLAY_FREE_SWARM_RUNTIME_QUIESCENCE_ENFORCER/v1"
REQUIRED_STATE = "OWNER_EMERGENCY_STOP_FREE_SWARM_HARD_OFF"
ROOT_NEEDLES = (
    "run_6000_free_swarm_supervisor.sh",
    "run_24h_entityos_swarm_supervisor.sh",
    "run_24h_entityos_swarm.py",
    "run_free_go_swarm.py",
    "run_free_evidence_forge.py",
    "run_research_distillery_local.py",
    "run_research_distillery_entry.py",
    "free swarm/evaluate.py",
    "free_swarm_exec_with_vault.py",
    "run_6000_free_swarm_fast.py",
    "run_6000_free_swarm_v3.py",
)

class StopError(RuntimeError):
    pass

def read_json(p: Path) -> dict[str, Any]:
    try:
        x = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise StopError(f"cannot read {p}: {e}") from e
    if not isinstance(x, dict):
        raise StopError(f"not object: {p}")
    return x

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def hard_off(repo: Path) -> dict[str, Any]:
    p = repo / "research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json"
    x = read_json(p)
    providers = x.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise StopError("provider admission missing providers")
    admitted = {str(k): bool(v.get("admitted")) for k,v in providers.items() if isinstance(v,dict)}
    ok = x.get("execution_state") == REQUIRED_STATE and len(admitted) == len(providers) and not any(admitted.values())
    return {"path": str(p), "sha256": sha256(p), "execution_state": x.get("execution_state"), "providers": admitted, "hard_off": ok}

def proc_snapshot() -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for d in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(d.name)
            stat = (d / "stat").read_text(errors="replace")
            rpar = stat.rfind(")")
            fields = stat[rpar+2:].split()
            ppid = int(fields[1])
            raw = (d / "cmdline").read_bytes()
            argv = [b.decode("utf-8",errors="replace") for b in raw.split(b"\0") if b]
            cmd = " ".join(argv)
            try:
                cwd = os.readlink(d / "cwd")
            except Exception:
                cwd = None
            out[pid] = {"pid":pid,"ppid":ppid,"argv":argv,"cmdline":cmd,"cwd":cwd}
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
            continue
    return out

def match_roots(procs: dict[int,dict[str,Any]]) -> list[int]:
    roots=[]
    for pid,p in procs.items():
        if pid in (os.getpid(), os.getppid()):
            continue
        cmd=p.get("cmdline") or ""
        hits=[n for n in ROOT_NEEDLES if n in cmd]
        if hits:
            p["matched_root_needles"]=hits
            roots.append(pid)
    return sorted(set(roots))

def descendants(procs: dict[int,dict[str,Any]], roots: list[int]) -> set[int]:
    chosen=set(roots)
    changed=True
    while changed:
        changed=False
        for pid,p in procs.items():
            if pid not in chosen and p.get("ppid") in chosen:
                chosen.add(pid); changed=True
    chosen.discard(os.getpid()); chosen.discard(os.getppid())
    return chosen

def depth(pid:int, procs:dict[int,dict[str,Any]], chosen:set[int]) -> int:
    n=0; seen=set()
    while pid in procs and pid not in seen:
        seen.add(pid); pp=procs[pid].get("ppid")
        if pp not in chosen: break
        n+=1; pid=pp
    return n

def alive(pids:set[int]) -> set[int]:
    out=set()
    for pid in pids:
        try: os.kill(pid,0); out.add(pid)
        except ProcessLookupError: pass
        except PermissionError: out.add(pid)
    return out

def terminate_tree(procs:dict[int,dict[str,Any]], chosen:set[int], grace:float) -> list[dict[str,Any]]:
    events=[]
    order=sorted(chosen,key=lambda p:depth(p,procs,chosen),reverse=True)
    for pid in order:
        try:
            os.kill(pid,signal.SIGTERM); events.append({"pid":pid,"signal":"SIGTERM","status":"SENT"})
        except ProcessLookupError:
            events.append({"pid":pid,"signal":"SIGTERM","status":"ALREADY_EXITED"})
        except PermissionError as e:
            events.append({"pid":pid,"signal":"SIGTERM","status":"PERMISSION_DENIED","error":str(e)})
    end=time.monotonic()+grace
    rem=alive(chosen)
    while rem and time.monotonic()<end:
        time.sleep(0.1); rem=alive(rem)
    for pid in sorted(rem,key=lambda p:depth(p,procs,chosen),reverse=True):
        try:
            os.kill(pid,signal.SIGKILL); events.append({"pid":pid,"signal":"SIGKILL","status":"SENT_AFTER_GRACE"})
        except ProcessLookupError:
            events.append({"pid":pid,"signal":"SIGKILL","status":"EXITED_DURING_GRACE"})
        except PermissionError as e:
            events.append({"pid":pid,"signal":"SIGKILL","status":"PERMISSION_DENIED","error":str(e)})
    return events

def git_identity(repo:Path)->dict[str,Any]:
    def g(*a:str)->str:
        return subprocess.run(["git","-C",str(repo),*a],check=True,text=True,capture_output=True).stdout.strip()
    s=g("status","--porcelain=v1")
    return {"head":g("rev-parse","HEAD"),"tree":g("rev-parse","HEAD^{tree}"),"dirty":bool(s),"status":s}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--grace-seconds",type=float,default=5.0)
    ap.add_argument("--window-seconds",type=float,default=60.0)
    ap.add_argument("--output")
    ns=ap.parse_args()
    repo=Path(ns.repo).resolve()
    receipt:dict[str,Any]={"schema":SCHEMA,"mode":"APPLY" if ns.apply else "DRY_RUN","source":{"path":str(Path(__file__).resolve()),"sha256":sha256(Path(__file__).resolve())},"repository":git_identity(repo)}
    try:
        auth=hard_off(repo); receipt["authority"]=auth
        if not auth["hard_off"]: raise StopError("canonical provider admission is not HARD_OFF")
        before=proc_snapshot(); roots=match_roots(before); chosen=descendants(before,roots)
        receipt["roots"]=[before[p] for p in roots if p in before]
        receipt["selected_tree"]=[before[p] for p in sorted(chosen) if p in before]
        if not ns.apply:
            receipt["decision"]={"status":"DRY_RUN_ONLY","selected_count":len(chosen)}
        else:
            receipt["termination_events"]=terminate_tree(before,chosen,max(0.1,ns.grace_seconds))
            time.sleep(0.2)
            after=proc_snapshot(); after_roots=match_roots(after); after_chosen=descendants(after,after_roots)
            receipt["remaining_matching_tree"]=[after[p] for p in sorted(after_chosen) if p in after]
            if after_chosen:
                raise StopError(f"matching provider-capable process tree remains: {sorted(after_chosen)}")
            probe=repo/"tools/free_swarm_runtime_quiescence_probe_v1.py"
            out=repo/"research_entity/continuity/receipts/FREE_SWARM_RUNTIME_QUIESCENCE_AFTER_ENFORCER.json"
            cp=subprocess.run([sys.executable,str(probe),"--repo",str(repo),"--window-seconds",str(ns.window_seconds),"--output",str(out)],text=True,capture_output=True)
            receipt["probe"]={"returncode":cp.returncode,"stdout":cp.stdout,"stderr":cp.stderr,"receipt_path":str(out),"receipt_sha256":sha256(out) if out.exists() else None}
            if cp.returncode != 0: raise StopError("bounded quiescence probe did not PASS")
            q=read_json(out)
            receipt["decision"]={"status":"PASS_COMPONENT_ONLY","zero_survivors":True,"bounded_quiescence_status":q.get("decision",{}).get("status")}
    except Exception as e:
        receipt["decision"]={"status":"FAIL_CLOSED","error":str(e)}
    text=json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if ns.output: Path(ns.output).write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if receipt.get("decision",{}).get("status") in ("PASS_COMPONENT_ONLY","DRY_RUN_ONLY") else 2

if __name__=="__main__": raise SystemExit(main())
