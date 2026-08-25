#!/usr/bin/env python3
"""Deterministic S1 fabric for autonomous Xeno nodes (candidate/workspace state only)."""
from __future__ import annotations
import hashlib, hmac, json, sqlite3, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

S1="XENO_S1_STATE/v1"; ADMISSION="XENO_NODE_ADMISSION/v1"; BOOT="XENO_AUTONOMOUS_BOOT/v1"
RESULT="NODE_RESULT/v1"; LEASE="GRID_COORDINATOR_LEASE/v1"; POLICY="XENO_COORDINATOR_POLICY/v1"

def canon(x:Any)->bytes:return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
def digest(x:Any)->str:return hashlib.sha256(canon(x)).hexdigest()
def req(ok:bool,code:str):
    if not ok: raise ValueError(code)
def hex64(x:Any)->bool:
    try:return isinstance(x,str) and len(x)==64 and int(x,16)>=0
    except ValueError:return False

SQL="""
PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS s1(singleton INTEGER PRIMARY KEY CHECK(singleton=1),epoch INTEGER NOT NULL,payload TEXT NOT NULL,digest TEXT NOT NULL,writer_lease TEXT);
CREATE TABLE IF NOT EXISTS nodes(node_id TEXT PRIMARY KEY,admission_id TEXT UNIQUE NOT NULL,caps TEXT NOT NULL,authority_digest TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS leases(scope TEXT PRIMARY KEY,lease_id TEXT UNIQUE NOT NULL,holder TEXT NOT NULL,generation INTEGER NOT NULL,issued_epoch INTEGER NOT NULL,issued_digest TEXT NOT NULL,expires REAL NOT NULL,policy_digest TEXT NOT NULL,mac TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS results(result_id TEXT PRIMARY KEY,scope TEXT NOT NULL,node_id TEXT NOT NULL,work_id TEXT NOT NULL,epoch INTEGER NOT NULL,state_digest TEXT NOT NULL,payload_digest TEXT NOT NULL,lease_id TEXT NOT NULL);
"""

class StaleState(RuntimeError):pass
class LeaseRejected(RuntimeError):pass
class DuplicateResult(RuntimeError):pass

@dataclass(frozen=True)
class Snapshot:
    fabric_id:str; epoch:int; state_digest:str; payload:dict[str,Any]
@dataclass(frozen=True)
class CoordinatorLease:
    schema:str; lease_id:str; fabric_id:str; scope:str; holder_node_id:str; generation:int
    issued_epoch:int; issued_state_digest:str; expires_at:float; policy_digest:str; token_mac:str

class NodeSession:
    """Ordinary-node interface: read S1 and emit result packets; no S1 mutation API."""
    def __init__(self,fabric:"SharedStateFabric",node_id:str,caps:Sequence[str]):
        self._f=fabric; self.node_id=node_id; self.capabilities=tuple(sorted(set(caps)))
    def snapshot(self)->Snapshot:return self._f.snapshot()
    def autonomous_boot(self)->dict[str,Any]:
        a=self.snapshot(); work=select_work(a.payload.get("work",[]),self.capabilities); b=self.snapshot()
        if (a.epoch,a.state_digest)!=(b.epoch,b.state_digest):raise StaleState("S1_CHANGED_DURING_BOOT")
        return {"schema":BOOT,"node_id":self.node_id,"role":"ORDINARY","fabric_id":a.fabric_id,
                "observed_epoch":a.epoch,"observed_state_digest":a.state_digest,"capabilities":list(self.capabilities),
                "selected_work":work,"s1_access":"READ_ONLY","coordinator_write_authority":False}
    def make_result(self,*,work_id:str,snapshot:Snapshot,payload:Mapping[str,Any])->dict[str,Any]:
        req(work_id!="","WORK_ID_REQUIRED"); req(snapshot.fabric_id==self._f.fabric_id,"FABRIC_MISMATCH")
        p=dict(payload); pd=digest(p); ident={"fabric_id":snapshot.fabric_id,"node_id":self.node_id,"work_id":work_id,
            "observed_epoch":snapshot.epoch,"observed_state_digest":snapshot.state_digest,"payload_digest":pd}
        return {"schema":RESULT,"result_id":"nr:"+digest(ident),**ident,"payload":p,
                "canonical_truth":False,"s1_write":False,"effect_authority":False}

def select_work(items:Any,caps:Sequence[str])->dict[str,Any]|None:
    if not isinstance(items,list):return None
    c=set(caps); out=[]
    for x in items:
        if not isinstance(x,dict) or x.get("status","OPEN") not in {"OPEN","AVAILABLE"}:continue
        wid=x.get("work_id"); r=x.get("required_capabilities",[]); p=x.get("priority",0)
        if not isinstance(wid,str) or not wid or not isinstance(r,list) or not set(map(str,r)).issubset(c):continue
        if not isinstance(p,(int,float)):p=0
        out.append({**x,"priority":p})
    return None if not out else sorted(out,key=lambda x:(-float(x["priority"]),str(x["work_id"])))[0]

class SharedStateFabric:
    def __init__(self,path:str|Path,*,fabric_id:str,authority_secret:bytes,coordinator_policy:Mapping[str,Any]|None=None):
        req(bool(fabric_id),"FABRIC_ID_REQUIRED"); req(isinstance(authority_secret,(bytes,bytearray)) and len(authority_secret)>=32,"AUTHORITY_SECRET_MIN_32")
        self.fabric_id=fabric_id; self._secret=bytes(authority_secret)
        self.policy=dict(coordinator_policy or {"schema":POLICY,"allowed_scopes":["global"],"required_capabilities":["COORDINATE"],"max_ttl_seconds":300})
        req(self.policy.get("schema")==POLICY,"POLICY_SCHEMA"); self.policy_digest=digest(self.policy)
        self.db=sqlite3.connect(Path(path),isolation_level=None,timeout=30,check_same_thread=False); self.db.row_factory=sqlite3.Row
        self.db.executescript(SQL); self.db.execute("INSERT OR IGNORE INTO meta VALUES('fabric_id',?)",(fabric_id,))
        req(self.db.execute("SELECT v FROM meta WHERE k='fabric_id'").fetchone()[0]==fabric_id,"FABRIC_ID_DB_MISMATCH")
    def close(self):self.db.close()
    def _mac(self,x:Mapping[str,Any])->str:return hmac.new(self._secret,canon(x),hashlib.sha256).hexdigest()
    def initialize_s1(self,payload:Mapping[str,Any])->Snapshot:
        req(self.db.execute("SELECT 1 FROM s1").fetchone() is None,"S1_ALREADY_INITIALIZED")
        p=dict(payload); d=digest({"schema":S1,"fabric_id":self.fabric_id,"epoch":1,"payload":p})
        self.db.execute("INSERT INTO s1 VALUES(1,1,?,?,NULL)",(json.dumps(p,sort_keys=True,separators=(",",":")),d)); return self.snapshot()
    def snapshot(self)->Snapshot:
        r=self.db.execute("SELECT epoch,payload,digest FROM s1 WHERE singleton=1").fetchone()
        if not r:raise RuntimeError("S1_NOT_INITIALIZED")
        p=json.loads(r["payload"]); d=digest({"schema":S1,"fabric_id":self.fabric_id,"epoch":int(r["epoch"]),"payload":p})
        if not hmac.compare_digest(d,r["digest"]):raise RuntimeError("S1_DIGEST_CORRUPTION")
        return Snapshot(self.fabric_id,int(r["epoch"]),r["digest"],p)
    def mint_admission(self,*,node_id:str,admission_id:str,capabilities:Sequence[str],controller_authority_digest:str)->dict[str,Any]:
        req(bool(node_id) and bool(admission_id),"NODE_ID_OR_ADMISSION_ID_REQUIRED"); req(hex64(controller_authority_digest),"AUTHORITY_DIGEST_INVALID")
        core={"schema":ADMISSION,"fabric_id":self.fabric_id,"node_id":node_id,"admission_id":admission_id,
              "capabilities":sorted(set(capabilities)),"controller_authority_digest":controller_authority_digest}
        return {**core,"admission_mac":self._mac({"kind":"NODE_ADMISSION",**core})}
    def admit_node(self,a:Mapping[str,Any])->NodeSession:
        req(a.get("schema")==ADMISSION and a.get("fabric_id")==self.fabric_id,"ADMISSION_SCHEMA_OR_FABRIC")
        core={k:a.get(k) for k in ("schema","fabric_id","node_id","admission_id","capabilities","controller_authority_digest")}
        req(isinstance(core["capabilities"],list) and hex64(core["controller_authority_digest"]),"ADMISSION_FIELDS_INVALID")
        req(hmac.compare_digest(str(a.get("admission_mac","")),self._mac({"kind":"NODE_ADMISSION",**core})),"NODE_ADMISSION_MAC_INVALID")
        caps=json.dumps(sorted(set(core["capabilities"])),separators=(",",":")); r=self.db.execute("SELECT * FROM nodes WHERE node_id=?",(core["node_id"],)).fetchone()
        if r:
            req((r["admission_id"],r["caps"],r["authority_digest"])==(core["admission_id"],caps,core["controller_authority_digest"]),"NODE_ADMISSION_DRIFT")
        else:self.db.execute("INSERT INTO nodes VALUES(?,?,?,?)",(core["node_id"],core["admission_id"],caps,core["controller_authority_digest"]))
        return NodeSession(self,core["node_id"],core["capabilities"])
    def issue_coordinator_lease(self,*,node_id:str,scope:str,ttl_seconds:float)->CoordinatorLease:
        req(scope in set(self.policy.get("allowed_scopes",[])),"LEASE_SCOPE_NOT_ALLOWED"); req(0<float(ttl_seconds)<=float(self.policy.get("max_ttl_seconds",0)),"LEASE_TTL_OUT_OF_RANGE")
        n=self.db.execute("SELECT caps FROM nodes WHERE node_id=?",(node_id,)).fetchone(); req(n is not None,"NODE_NOT_ADMITTED")
        req(set(self.policy.get("required_capabilities",[])).issubset(set(json.loads(n["caps"]))),"COORDINATOR_CAPABILITY_POLICY_REJECTED")
        s=self.snapshot(); old=self.db.execute("SELECT generation FROM leases WHERE scope=?",(scope,)).fetchone(); gen=(int(old[0])+1) if old else 1; exp=time.time()+float(ttl_seconds)
        core={"schema":LEASE,"fabric_id":self.fabric_id,"scope":scope,"holder_node_id":node_id,"generation":gen,
              "issued_epoch":s.epoch,"issued_state_digest":s.state_digest,"expires_at":exp,"policy_digest":self.policy_digest}
        lid="gcl:"+digest(core); mac=self._mac({**core,"lease_id":lid})
        self.db.execute("INSERT INTO leases VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(scope) DO UPDATE SET lease_id=excluded.lease_id,holder=excluded.holder,generation=excluded.generation,issued_epoch=excluded.issued_epoch,issued_digest=excluded.issued_digest,expires=excluded.expires,policy_digest=excluded.policy_digest,mac=excluded.mac",
                        (scope,lid,node_id,gen,s.epoch,s.state_digest,exp,self.policy_digest,mac))
        return CoordinatorLease(LEASE,lid,self.fabric_id,scope,node_id,gen,s.epoch,s.state_digest,exp,self.policy_digest,mac)
    def assert_lease(self,l:CoordinatorLease):
        r=self.db.execute("SELECT * FROM leases WHERE scope=?",(l.scope,)).fetchone()
        if not r:raise LeaseRejected("LEASE_NOT_FOUND")
        core={"schema":l.schema,"fabric_id":l.fabric_id,"scope":l.scope,"holder_node_id":l.holder_node_id,"generation":l.generation,
              "issued_epoch":l.issued_epoch,"issued_state_digest":l.issued_state_digest,"expires_at":l.expires_at,"policy_digest":l.policy_digest,"lease_id":l.lease_id}
        if l.schema!=LEASE or l.fabric_id!=self.fabric_id or not hmac.compare_digest(self._mac(core),l.token_mac):raise LeaseRejected("LEASE_MAC_OR_FABRIC_INVALID")
        if (r["lease_id"],r["holder"],int(r["generation"]),r["mac"])!=(l.lease_id,l.holder_node_id,l.generation,l.token_mac):raise LeaseRejected("LEASE_STALE_OR_REPLACED")
        if min(float(r["expires"]),l.expires_at)<=time.time():raise LeaseRejected("LEASE_EXPIRED")
    def coordinator_commit(self,*,lease:CoordinatorLease,expected_epoch:int,expected_state_digest:str,payload:Mapping[str,Any])->dict[str,Any]:
        self.assert_lease(lease); s=self.snapshot()
        if (s.epoch,s.state_digest)!=(int(expected_epoch),expected_state_digest):raise StaleState("S1_CAS_MISMATCH")
        p=dict(payload); epoch=s.epoch+1; d=digest({"schema":S1,"fabric_id":self.fabric_id,"epoch":epoch,"payload":p})
        cur=self.db.execute("UPDATE s1 SET epoch=?,payload=?,digest=?,writer_lease=? WHERE singleton=1 AND epoch=? AND digest=?",
                            (epoch,json.dumps(p,sort_keys=True,separators=(",",":")),d,lease.lease_id,s.epoch,s.state_digest))
        if cur.rowcount!=1:raise StaleState("S1_CHANGED_BEFORE_COMMIT")
        return {"schema":"XENO_S1_COMMIT/v1","status":"COMMITTED","epoch":epoch,"state_digest":d,"writer_lease_id":lease.lease_id,"canonical_truth":False,"effect_authority":False}
    def admit_result(self,*,lease:CoordinatorLease,result:Mapping[str,Any])->dict[str,Any]:
        self.assert_lease(lease); s=self.snapshot(); req(result.get("schema")==RESULT and result.get("fabric_id")==self.fabric_id,"RESULT_SCHEMA_OR_FABRIC")
        if (result.get("observed_epoch"),result.get("observed_state_digest"))!=(s.epoch,s.state_digest):raise StaleState("RESULT_STALE_S1_BINDING")
        p=result.get("payload"); req(isinstance(p,dict) and digest(p)==result.get("payload_digest"),"RESULT_PAYLOAD_DIGEST")
        ident={k:result.get(k) for k in ("fabric_id","node_id","work_id","observed_epoch","observed_state_digest","payload_digest")}
        req(result.get("result_id")=="nr:"+digest(ident),"RESULT_ID_MISMATCH"); req(result.get("canonical_truth") is False and result.get("s1_write") is False and result.get("effect_authority") is False,"RESULT_AUTHORITY_ESCALATION")
        try:self.db.execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?)",(result["result_id"],lease.scope,result["node_id"],result["work_id"],result["observed_epoch"],result["observed_state_digest"],result["payload_digest"],lease.lease_id))
        except sqlite3.IntegrityError as e:raise DuplicateResult(result["result_id"]) from e
        return {"schema":"NODE_RESULT_ADMISSION/v1","status":"ADMITTED_CANDIDATE_ONLY","result_id":result["result_id"],"canonical_truth":False,"effect_authority":False}
