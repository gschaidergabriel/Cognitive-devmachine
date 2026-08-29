#!/usr/bin/env python3
"""Read-only Trigger-4 companion discriminator for current Podman/cgroup-v2 telemetry.

It never starts/stops/moves a container or cgroup, never invokes a model/provider/effect,
and never mints runtime/completion/system credit. It classifies only observed scope:
DEDICATED_SUBTREE candidate, SHARED_PARENT_SUPERSET, ROOT, or UNRESOLVED.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "TRIGGER4_CGROUP_RESOURCE_WITNESS_DISCRIMINATOR/v1"
SAFE_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,255}")
MAX_DIRS, MAX_IDS = 4096, 16384


def now() -> str: return datetime.now(timezone.utc).isoformat()
def read(p: Path) -> str | None:
    try: return p.read_text(encoding="utf-8", errors="replace")
    except OSError: return None

def run(a: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(a, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
def ids(text: str | None) -> set[int]:
    out=set()
    for x in (text or "").splitlines():
        try: n=int(x.strip())
        except ValueError: continue
        if n>0: out.add(n)
    return out

def cgv2_path(text: str | None) -> str | None:
    for line in (text or "").splitlines():
        p=line.split(":",2)
        if len(p)==3 and p[0]=="0" and p[1]=="": return p[2] if p[2].startswith("/") else "/"+p[2]
    return None

def starttime(text: str | None) -> int | None:
    if not text or ")" not in text: return None
    tail=text[text.rfind(")")+1:].split()
    try: return int(tail[19])
    except (IndexError,ValueError): return None

def mount_dir(path: str | None) -> tuple[Path|None,str|None]:
    if not path: return None,None
    best=None
    for line in (read(Path("/proc/self/mountinfo")) or "").splitlines():
        if " - cgroup2 " not in line: continue
        f=line.split(" - ",1)[0].split()
        if len(f)<5: continue
        root,mnt=f[3],f[4]
        if root=="/": rel=path.lstrip("/")
        elif path==root: rel=""
        elif path.startswith(root+"/"): rel=path[len(root)+1:]
        else: continue
        cand=(len(root),Path(mnt)/rel,mnt)
        if best is None or cand[0]>best[0]: best=cand
    return (best[1],best[2]) if best else (None,None)
def members(root: Path) -> dict[str,Any]:
    ps,ts=set(),set(); stack=[root]; seen=0; errors=[]
    if not root.is_dir(): return {"complete":False,"process_ids":[],"thread_ids":[],"errors":["MISSING_DIR"]}
    while stack:
        d=stack.pop(); seen+=1
        if seen>MAX_DIRS: errors.append("DIR_CAP"); break
        ps |= ids(read(d/"cgroup.procs")); ts |= ids(read(d/"cgroup.threads"))
        if len(ps)>MAX_IDS or len(ts)>MAX_IDS: errors.append("ID_CAP"); break
        try: stack += [x for x in d.iterdir() if x.is_dir()]
        except OSError as e: errors.append(f"ITER:{type(e).__name__}")
    return {"complete":not errors,"dirs_seen":seen,"process_ids":sorted(ps)[:MAX_IDS],"thread_ids":sorted(ts)[:MAX_IDS],"errors":errors[:16]}
def inspect(ref: str) -> dict[str,Any]:
    r=run(["podman","inspect","--type","container",ref]); o={"rc":r.returncode,"stderr":r.stderr[-2000:]}
    if r.returncode: return o
    try:
        x=json.loads(r.stdout); x=x[0] if isinstance(x,list) else x; s=x.get("State") or {}
        o.update(id=x.get("Id") or x.get("ID"),name=x.get("Name"),running=bool(s.get("Running")),pid=int(s.get("Pid") or 0) or None)
    except Exception as e: o["parse_error"]=f"{type(e).__name__}:{e}"
    return o
def podman_pids(ref: str) -> dict[str,Any]:
    r=run(["podman","top",ref,"hpid"]); ps=set()
    if r.returncode==0:
        for line in r.stdout.splitlines():
            tok=line.strip().split()[0] if line.strip() else ""
            if tok.upper()=="HPID": continue
            try: n=int(tok)
            except ValueError: continue
            if n>0: ps.add(n)
    return {"rc":r.returncode,"available":r.returncode==0 and bool(ps),"host_pids":sorted(ps),"stderr":r.stderr[-2000:]}
def metrics(root: Path) -> list[dict[str,Any]]:
    out=[]
    for name in ["cgroup.type","cgroup.events","cpu.stat","memory.current","memory.peak","memory.events","memory.events.local","io.stat","pids.current"]:
        raw=read(root/name); out.append({"file":name,"path":str(root/name),"present":raw is not None,"raw":raw,"sha256":hashlib.sha256(raw.encode()).hexdigest() if raw is not None else None})
    return out

def classify(path:str|None, root:Path|None, mnt:str|None, typ:str|None, m:dict[str,Any], p:dict[str,Any], stable:bool, host_view:bool)->tuple[str,str,str]:
    if not path or root is None: return "UNRESOLVED","UNKNOWN","NO_HOST_CGROUP_PATH"
    if path=="/" or (mnt and root==Path(mnt)): return "ROOT","UNKNOWN","CGROUP_ROOT"
    if not stable: return "UNRESOLVED","UNKNOWN","LIFECYCLE_CHANGED"
    if not host_view: return "UNRESOLVED","UNKNOWN","HOST_CGROUP_NAMESPACE_NOT_BOUND"
    if (typ or "").strip()!="domain": return "UNRESOLVED","UNKNOWN","CGROUP_TYPE_NOT_PLAIN_DOMAIN"
    if not m.get("complete") or not p.get("available"): return "UNRESOLVED","UNKNOWN","MEMBERSHIP_OR_PODMAN_PID_SET_INCOMPLETE"
    a,b=set(m.get("process_ids") or []),set(p.get("host_pids") or [])
    if a and a==b: return "DEDICATED_SUBTREE","EXACT_CANDIDATE","SUBTREE_EQUALS_INDEPENDENT_PODMAN_HOST_PID_SET"
    if b and b.issubset(a): return "SHARED_PARENT_SUPERSET","SUPERSET","SUBTREE_CONTAINS_UNBOUND_PROCESSES"
    return "UNRESOLVED","UNKNOWN","MEMBERSHIP_DISAGREES"

def witness(ref:str)->dict[str,Any]:
    out={"schema":SCHEMA,"observed_at":now(),"container_ref":ref,"read_only":True,"credits":{"container_resource_attribution":0,"target_runtime":0,"physical_grid10":0,"semantic_gwt_jspace":0,"whole_system":0}}
    if not SAFE_REF.fullmatch(ref): return out|{"status":"UNKNOWN","scope_class":"UNRESOLVED","coverage_status":"UNKNOWN","reason":"INVALID_CONTAINER_REF"}
    self_ns=os.readlink("/proc/self/ns/cgroup") if Path("/proc/self/ns/cgroup").exists() else None
    pid1_ns=os.readlink("/proc/1/ns/cgroup") if Path("/proc/1/ns/cgroup").exists() else None
    host_view=bool(self_ns and pid1_ns and self_ns==pid1_ns)
    b=inspect(ref); out["inspect_before"]=b; pid=b.get("pid")
    if b.get("rc") or not b.get("running") or not pid: return out|{"status":"UNKNOWN","scope_class":"UNRESOLVED","coverage_status":"UNKNOWN","reason":"NO_RUNNING_PAYLOAD_PID"}
    pr=Path("/proc")/str(pid); st1=starttime(read(pr/"stat")); cgraw=read(pr/"cgroup"); path=cgv2_path(cgraw); root,mnt=mount_dir(path)
    if root is None: return out|{"status":"UNKNOWN","scope_class":"UNRESOLVED","coverage_status":"UNKNOWN","reason":"CGROUP2_MOUNT_UNRESOLVED","host_cgroup_path":path}
    typ=read(root/"cgroup.type"); m1=members(root); pp=podman_pids(ref); mets=metrics(root); m2=members(root); a=inspect(ref); st2=starttime(read(pr/"stat")) if pr.exists() else None
    stable=bool(b.get("id") and b.get("id")==a.get("id") and b.get("pid")==a.get("pid") and a.get("running") and st1 is not None and st1==st2 and m1.get("process_ids")==m2.get("process_ids") and m1.get("thread_ids")==m2.get("thread_ids"))
    scope,cov,reason=classify(path,root,mnt,typ,m1,pp,stable,host_view)
    out.update(status="OBSERVED_CANDIDATE" if cov=="EXACT_CANDIDATE" else ("OBSERVED_SUPERSET_ONLY" if cov=="SUPERSET" else "UNKNOWN"),scope_class=scope,coverage_status=cov,reason=reason,namespace={"self":self_ns,"pid1":pid1_ns,"view":"HOST_INITIAL_CANDIDATE" if host_view else "UNKNOWN","credit":0},process_identity={"pid":pid,"starttime_before":st1,"starttime_after":st2,"proc_cgroup_raw":cgraw},host_cgroup_path=path,resolved_cgroup_dir=str(root),cgroup_type=typ.strip() if typ else None,membership_before=m1,membership_after=m2,podman_host_pid_set=pp,metrics=mets,inspect_after=a,lifecycle_stable=stable)
    return out

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--container-ref",required=True); ap.add_argument("--output",default="trigger4_cgroup_resource_witness.json"); a=ap.parse_args()
    r=witness(a.container_ref); Path(a.output).write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps({"status":r.get("status"),"scope":r.get("scope_class"),"coverage":r.get("coverage_status"),"output":a.output},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
