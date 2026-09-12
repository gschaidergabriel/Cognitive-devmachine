from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from .unified_store import UnifiedStore, digest, now


class MasterBridgeCarrierError(RuntimeError):
    pass


def _git(repo: Path, *args: str, check: bool = True, timeout: int = 180) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    if check and p.returncode != 0:
        raise MasterBridgeCarrierError(f"git {' '.join(args)} rc={p.returncode}: {p.stderr[-1000:]}")
    return p.stdout


class MasterBridgeCarrier:
    """OMEGA↔ChatGPT mailbox carried by the already-admitted research repository.

    The research repo is transport only. Canonical state remains in OMEGA UnifiedDB.
    Every request carries the exact OMEGA release head and a content digest.
    """

    def __init__(self, *, carrier_repo: Path, runtime_root: Path, store: UnifiedStore,
                 control_branch: str = "omega-master-control", results_branch: str = "omega-master-results-v1") -> None:
        self.carrier_repo = carrier_repo
        self.runtime_root = runtime_root
        self.store = store
        self.control_branch = control_branch
        self.results_branch = results_branch
        self.work_root = runtime_root / "master_bridge" / "carrier_git"
        self.submitted = runtime_root / "master_bridge" / "submitted"
        self.responses = runtime_root / "master_bridge" / "responses"
        for p in (self.work_root,self.submitted,self.responses): p.mkdir(parents=True, exist_ok=True)
        self.remote = _git(carrier_repo,"remote","get-url","origin").strip()
        if not self.remote: raise MasterBridgeCarrierError("carrier repo has no origin")

    def _checkout(self, branch: str) -> Path:
        path = self.work_root / (hashlib.sha256(branch.encode()).hexdigest()[:12] + "-" + branch.replace("/","_"))
        if not (path/".git").exists():
            p = subprocess.run(["git","clone","--single-branch","--branch",branch,self.remote,str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=False)
            if p.returncode != 0: raise MasterBridgeCarrierError(f"clone {branch} failed: {p.stderr[-1000:]}")
            _git(path,"config","user.name","OMEGA Master Bridge")
            _git(path,"config","user.email","omega-master-bridge@localhost")
        return path

    def _refresh(self, repo: Path, branch: str) -> None:
        _git(repo,"fetch","origin",branch)
        _git(repo,"checkout","-B","omega-mailbox","FETCH_HEAD")

    def _publish(self, branch: str, rel: Path, payload: dict[str,Any], message: str) -> str:
        repo=self._checkout(branch); raw=json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+"\n"; h=hashlib.sha256(raw.encode()).hexdigest()
        for attempt in range(4):
            self._refresh(repo,branch); target=repo/rel; target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest()!=h: raise MasterBridgeCarrierError(f"mailbox collision {rel}")
                return h
            target.write_text(raw,encoding="utf-8"); _git(repo,"add",str(rel)); _git(repo,"commit","-m",message)
            p=subprocess.run(["git","-C",str(repo),"push","origin",f"HEAD:{branch}"],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,check=False)
            if p.returncode==0: return h
            if attempt==3: raise MasterBridgeCarrierError(f"push unresolved: {p.stderr[-1000:]}")
            time.sleep(0.5*(attempt+1))
        raise AssertionError("unreachable")

    def _omega_head(self) -> str:
        meta=self.runtime_root.parent/"CURRENT_RELEASE.json"
        if meta.exists():
            try:
                value=json.loads(meta.read_text(encoding="utf-8")).get("omega_head")
                if value: return str(value)
            except Exception: pass
        return os.getenv("OMEGA_SOURCE_HEAD","UNKNOWN")

    def submit(self,payload:dict[str,Any],*,correlation_id:str|None=None)->dict[str,Any]:
        request_id="omega_master_"+uuid.uuid4().hex
        req={"schema":"OMEGA_MASTER_REQUEST/v1","request_id":request_id,"created_at":now(),"sender":"omega-grid","recipient":"chatgpt-master-organ","omega_head":self._omega_head(),"correlation_id":correlation_id,"payload":payload}
        req["request_digest"]=digest(req)
        rel=Path("omega_master_mailbox")/"requests"/f"{request_id}.json"
        blob=self._publish(self.control_branch,rel,req,f"omega master request: {request_id}")
        (self.submitted/f"{request_id}.json").write_text(json.dumps(req,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        self.store.bridge_message(direction="OUT",sender="omega-grid",recipient="chatgpt-master-organ",kind="MASTER_REQUEST",payload=req,correlation_id=correlation_id or request_id)
        return {"request_id":request_id,"request_digest":req["request_digest"],"carrier_digest":blob,"path":str(rel)}

    def poll_response(self,request_id:str)->dict[str,Any]|None:
        repo=self._checkout(self.results_branch); self._refresh(repo,self.results_branch)
        rel=Path("omega_master_mailbox")/"responses"/f"{request_id}.json"; path=repo/rel
        if not path.exists(): return None
        resp=json.loads(path.read_text(encoding="utf-8")); req=json.loads((self.submitted/f"{request_id}.json").read_text(encoding="utf-8"))
        if resp.get("schema")!="OMEGA_MASTER_RESPONSE/v1" or resp.get("request_id")!=request_id or resp.get("request_digest")!=req.get("request_digest"):
            raise MasterBridgeCarrierError("response binding mismatch")
        local=self.responses/f"{request_id}.json"
        if not local.exists():
            local.write_text(json.dumps(resp,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            self.store.bridge_message(direction="IN",sender="chatgpt-master-organ",recipient="omega-grid",kind="MASTER_RESPONSE",payload=resp,correlation_id=str(req.get("correlation_id") or request_id))
            self.store.record_observation(source_id="repo:research",subject_id="omega:master_bridge_response",payload=resp,observed_at=str(resp.get("created_at") or now()),evidence_class="RUNTIME_RECEIPT",source_repo="gschaidergabriel/clay-global-research-entity",source_path=str(rel),raw_locator=f"git:{self.results_branch}:{rel}")
        return resp

    def process_once(self)->dict[str,int]:
        counts={"submitted":0,"responses":0}; outbox=self.runtime_root/"outbox"
        for path in sorted(outbox.glob("*.json")):
            try: item=json.loads(path.read_text(encoding="utf-8"))
            except Exception: continue
            if item.get("schema")!="OMEGA_OUTBOX/v1" or item.get("kind")!="MASTER_COGNITION_UPDATE": continue
            mid=str(item.get("message_id")); marker=self.runtime_root/"master_bridge"/"submitted_messages"/f"{mid}.json"
            if marker.exists(): continue
            res=self.submit(item,correlation_id=mid); marker.parent.mkdir(parents=True,exist_ok=True); marker.write_text(json.dumps(res,indent=2)+"\n"); counts["submitted"]+=1
        for path in sorted(self.submitted.glob("omega_master_*.json")):
            rid=path.stem
            if (self.responses/f"{rid}.json").exists(): continue
            if self.poll_response(rid) is not None: counts["responses"]+=1
        return counts


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--carrier-repo",default=os.getenv("OMEGA_CARRIER_REPO","/workspace/omega_runtime/carrier_repo")); ap.add_argument("--runtime-root",default=os.getenv("OMEGA_RUNTIME_ROOT","/workspace/omega_runtime/state")); ap.add_argument("--repo-root",default=os.getenv("OMEGA_REPO_ROOT","/workspace/omega_runtime/current")); ap.add_argument("--db",default=os.getenv("OMEGA_UNIFIED_DB","/workspace/omega_runtime/data/omega_unified.db")); ap.add_argument("--control-branch",default="omega-master-control"); ap.add_argument("--results-branch",default="omega-master-results-v1"); ap.add_argument("--interval",type=float,default=20.0); ap.add_argument("--once",action="store_true"); a=ap.parse_args()
    store=UnifiedStore(Path(a.db),Path(a.repo_root)/"schema"); bridge=MasterBridgeCarrier(carrier_repo=Path(a.carrier_repo),runtime_root=Path(a.runtime_root),store=store,control_branch=a.control_branch,results_branch=a.results_branch)
    if a.once: print(json.dumps(bridge.process_once(),indent=2)); return 0
    while True:
        try: bridge.process_once()
        except Exception as exc:
            p=Path(a.runtime_root)/"master_bridge"/"LAST_ERROR.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps({"at":now(),"error":f"{type(exc).__name__}:{exc}"},indent=2)+"\n")
        time.sleep(max(2.0,a.interval))

if __name__=="__main__": raise SystemExit(main())
