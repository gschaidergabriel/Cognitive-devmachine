#!/usr/bin/env python3
"""Deterministic S1 fabric for autonomous Xeno nodes (candidate/workspace state only)."""
from __future__ import annotations
import contextlib, hashlib, hmac, json, sqlite3, time
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
CREATE TABLE IF NOT EXISTS results(result_id TEXT PRIMARY KEY,scope TEXT NOT NULL,node_id TEXT NOT NULL,admission_id TEXT NOT NULL,work_id TEXT NOT NULL,epoch INTEGER NOT NULL,state_digest TEXT NOT NULL,payload_digest TEXT NOT NULL,lease_id TEXT NOT NULL);
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

def _snapshot_from_conn(db:sqlite3.Connection,fabric_id:str)->Snapshot:
    r=db.execute("SELECT epoch,payload,digest FROM s1 WHERE singleton=1").fetchone()
    if not r:raise RuntimeError("S1_NOT_INITIALIZED")
    p=json.loads(r["payload"]); d=digest({"schema":S1,"fabric_id":fabric_id,"epoch":int(r["epoch"]),"payload":p})
    if not hmac.compare_digest(d,r["digest"]):raise RuntimeError("S1_DIGEST_CORRUPTION")
    return Snapshot(fabric_id,int(r["epoch"]),r["digest"],p)

class ReadOnlyS1:
    """SQLite read-only S1 view: ordinary-node code receives no controller handle or authority secret."""
    def __init__(self,path:str|Path,*,fabric_id:str):
        self.fabric_id=fabric_id
        uri=Path(path).resolve().as_uri()+"?mode=ro"
        self.db=sqlite3.connect(uri,uri=True,isolation_level=None,timeout=30,check_same_thread=False)
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA query_only=ON")
        row=self.db.execute("SELECT v FROM meta WHERE k='fabric_id'").fetchone()
        req(row is not None and row[0]==fabric_id,"FABRIC_ID_DB_MISMATCH")
    def snapshot(self)->Snapshot:return _snapshot_from_conn(self.db,self.fabric_id)
    def node_admission(self,node_id:str)->sqlite3.Row:
        row=self.db.execute("SELECT node_id,admission_id,caps,authority_digest FROM nodes WHERE node_id=?",(node_id,)).fetchone()
        if row is None:raise PermissionError("NODE_NOT_ADMITTED")
        return row
    def close(self):self.db.close()

class NodeSession:
    """Ordinary-node interface backed only by a read-only DB handle + node-scoped result signer."""
    def __init__(self,path:str|Path,*,fabric_id:str,node_id:str,result_signing_key:bytes):
        self._reader=ReadOnlyS1(path,fabric_id=fabric_id)
        row=self._reader.node_admission(node_id)
        self.fabric_id=fabric_id; self.node_id=node_id; self.admission_id=row["admission_id"]
        self.capabilities=tuple(json.loads(row["caps"])); self._result_key=bytes(result_signing_key)
    def close(self):self._reader.close()
    def snapshot(self)->Snapshot:return self._reader.snapshot()
    def autonomous_boot(self)->dict[str,Any]:
        a=self.snapshot(); work=select_work(a.payload.get("work",[]),self.capabilities); b=self.snapshot()
        if (a.epoch,a.state_digest)!=(b.epoch,b.state_digest):raise StaleState("S1_CHANGED_DURING_BOOT")
        return {"schema":BOOT,"node_id":self.node_id,"admission_id":self.admission_id,"role":"ORDINARY","fabric_id":a.fabric_id,
                "observed_epoch":a.epoch,"observed_state_digest":a.state_digest,"capabilities":list(self.capabilities),
                "selected_work":work,"s1_access":"READ_ONLY","coordinator_write_authority":False}
    def make_result(self,*,work_id:str,snapshot:Snapshot,payload:Mapping[str,Any])->dict[str,Any]:
        req(work_id!="","WORK_ID_REQUIRED"); req(snapshot.fabric_id==self.fabric_id,"FABRIC_MISMATCH")
        p=dict(payload); pd=digest(p); ident={"fabric_id":snapshot.fabric_id,"node_id":self.node_id,"admission_id":self.admission_id,
            "work_id":work_id,"observed_epoch":snapshot.epoch,"observed_state_digest":snapshot.state_digest,"payload_digest":pd}
        rid="nr:"+digest(ident); core={"schema":RESULT,"result_id":rid,**ident,"payload":p,
                "canonical_truth":False,"s1_write":False,"effect_authority":False}
        return {**core,"result_auth_mac":hmac.new(self._result_key,canon(core),hashlib.sha256).hexdigest()}

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
    """Trusted deterministic shell/controller authority for S1 admission, leases and writes."""
    def __init__(self,path:str|Path,*,fabric_id:str,authority_secret:bytes,coordinator_policy:Mapping[str,Any]|None=None):
        req(bool(fabric_id),"FABRIC_ID_REQUIRED"); req(isinstance(authority_secret,(bytes,bytearray)) and len(authority_secret)>=32,"AUTHORITY_SECRET_MIN_32")
        self.path=Path(path); self.fabric_id=fabric_id; self._secret=bytes(authority_secret)
        self.policy=dict(coordinator_policy or {"schema":POLICY,"allowed_scopes":["global"],"required_capabilities":["COORDINATE"],"max_ttl_seconds":300})
        req(self.policy.get("schema")==POLICY,"POLICY_SCHEMA"); self.policy_digest=digest(self.policy)
        self.db=sqlite3.connect(self.path,isolation_level=None,timeout=30,check_same_thread=False); self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000"); self.db.executescript(SQL)
        self.db.execute("INSERT OR IGNORE INTO meta VALUES('fabric_id',?)",(fabric_id,))
        req(self.db.execute("SELECT v FROM meta WHERE k='fabric_id'").fetchone()[0]==fabric_id,"FABRIC_ID_DB_MISMATCH")
    def close(self):self.db.close()
    @contextlib.contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:yield self.db
        except Exception:self.db.execute("ROLLBACK");raise
        else:self.db.execute("COMMIT")
    def _mac(self,x:Mapping[str,Any])->str:return hmac.new(self._secret,canon(x),hashlib.sha256).hexdigest()
    def _result_key(self,node_id:str,admission_id:str)->bytes:
        return hmac.new(self._secret,canon({"kind":"NODE_RESULT_KEY/v1","fabric_id":self.fabric_id,"node_id":node_id,"admission_id":admission_id}),hashlib.sha256).digest()
    def initialize_s1(self,payload:Mapping[str,Any])->Snapshot:
        req(self.db.execute("SELECT 1 FROM s1").fetchone() is None,"S1_ALREADY_INITIALIZED")
        p=dict(payload); d=digest({"schema":S1,"fabric_id":self.fabric_id,"epoch":1,"payload":p})
        self.db.execute("INSERT INTO s1 VALUES(1,1,?,?,NULL)",(json.dumps(p,sort_keys=True,separators=(",",":")),d)); return self.snapshot()
    def snapshot(self)->Snapshot:return _snapshot_from_conn(self.db,self.fabric_id)
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
        caps=json.dumps(sorted(set(core["capabilities"])),separators=(",",":"))
        with self.tx() as db:
            r=db.execute("SELECT * FROM nodes WHERE node_id=?",(core["node_id"],)).fetchone()
            if r:req((r["admission_id"],r["caps"],r["authority_digest"])==(core["admission_id"],caps,core["controller_authority_digest"]),"NODE_ADMISSION_DRIFT")
            else:db.execute("INSERT INTO nodes VALUES(?,?,?,?)",(core["node_id"],core["admission_id"],caps,core["controller_authority_digest"]))
        return NodeSession(self.path,fabric_id=self.fabric_id,node_id=core["node_id"],result_signing_key=self._result_key(core["node_id"],core["admission_id"]))
    def issue_coordinator_lease(self,*,node_id:str,scope:str,ttl_seconds:float)->CoordinatorLease:
        req(scope in set(self.policy.get("allowed_scopes",[])),"LEASE_SCOPE_NOT_ALLOWED"); req(0<float(ttl_seconds)<=float(self.policy.get("max_ttl_seconds",0)),"LEASE_TTL_OUT_OF_RANGE")
        with self.tx() as db:
            n=db.execute("SELECT caps FROM nodes WHERE node_id=?",(node_id,)).fetchone(); req(n is not None,"NODE_NOT_ADMITTED")
            req(set(self.policy.get("required_capabilities",[])).issubset(set(json.loads(n["caps"]))),"COORDINATOR_CAPABILITY_POLICY_REJECTED")
            s=_snapshot_from_conn(db,self.fabric_id); old=db.execute("SELECT generation FROM leases WHERE scope=?",(scope,)).fetchone()
            gen=(int(old[0])+1) if old else 1; exp=time.time()+float(ttl_seconds)
            core={"schema":LEASE,"fabric_id":self.fabric_id,"scope":scope,"holder_node_id":node_id,"generation":gen,
                  "issued_epoch":s.epoch,"issued_state_digest":s.state_digest,"expires_at":exp,"policy_digest":self.policy_digest}
            lid="gcl:"+digest(core); mac=self._mac({**core,"lease_id":lid})
            db.execute("INSERT INTO leases VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(scope) DO UPDATE SET lease_id=excluded.lease_id,holder=excluded.holder,generation=excluded.generation,issued_epoch=excluded.issued_epoch,issued_digest=excluded.issued_digest,expires=excluded.expires,policy_digest=excluded.policy_digest,mac=excluded.mac",
                       (scope,lid,node_id,gen,s.epoch,s.state_digest,exp,self.policy_digest,mac))
        return CoordinatorLease(LEASE,lid,self.fabric_id,scope,node_id,gen,s.epoch,s.state_digest,exp,self.policy_digest,mac)
    def _assert_lease_db(self,db:sqlite3.Connection,l:CoordinatorLease)->None:
        r=db.execute("SELECT * FROM leases WHERE scope=?",(l.scope,)).fetchone()
        if not r:raise LeaseRejected("LEASE_NOT_FOUND")
        core={"schema":l.schema,"fabric_id":l.fabric_id,"scope":l.scope,"holder_node_id":l.holder_node_id,"generation":l.generation,
              "issued_epoch":l.issued_epoch,"issued_state_digest":l.issued_state_digest,"expires_at":l.expires_at,"policy_digest":l.policy_digest,"lease_id":l.lease_id}
        if l.schema!=LEASE or l.fabric_id!=self.fabric_id or not hmac.compare_digest(self._mac(core),l.token_mac):raise LeaseRejected("LEASE_MAC_OR_FABRIC_INVALID")
        if (r["lease_id"],r["holder"],int(r["generation"]),r["mac"])!=(l.lease_id,l.holder_node_id,l.generation,l.token_mac):raise LeaseRejected("LEASE_STALE_OR_REPLACED")
        if min(float(r["expires"]),l.expires_at)<=time.time():raise LeaseRejected("LEASE_EXPIRED")
    def assert_lease(self,l:CoordinatorLease):self._assert_lease_db(self.db,l)
    def coordinator_commit(self,*,lease:CoordinatorLease,expected_epoch:int,expected_state_digest:str,payload:Mapping[str,Any])->dict[str,Any]:
        with self.tx() as db:
            self._assert_lease_db(db,lease); s=_snapshot_from_conn(db,self.fabric_id)
            if (s.epoch,s.state_digest)!=(int(expected_epoch),expected_state_digest):raise StaleState("S1_CAS_MISMATCH")
            p=dict(payload); epoch=s.epoch+1; d=digest({"schema":S1,"fabric_id":self.fabric_id,"epoch":epoch,"payload":p})
            cur=db.execute("UPDATE s1 SET epoch=?,payload=?,digest=?,writer_lease=? WHERE singleton=1 AND epoch=? AND digest=?",
                           (epoch,json.dumps(p,sort_keys=True,separators=(",",":")),d,lease.lease_id,s.epoch,s.state_digest))
            if cur.rowcount!=1:raise StaleState("S1_CHANGED_BEFORE_COMMIT")
        return {"schema":"XENO_S1_COMMIT/v1","status":"COMMITTED","epoch":epoch,"state_digest":d,"writer_lease_id":lease.lease_id,"canonical_truth":False,"effect_authority":False}
    def admit_result(self,*,lease:CoordinatorLease,result:Mapping[str,Any])->dict[str,Any]:
        with self.tx() as db:
            self._assert_lease_db(db,lease); s=_snapshot_from_conn(db,self.fabric_id)
            req(result.get("schema")==RESULT and result.get("fabric_id")==self.fabric_id,"RESULT_SCHEMA_OR_FABRIC")
            if (result.get("observed_epoch"),result.get("observed_state_digest"))!=(s.epoch,s.state_digest):raise StaleState("RESULT_STALE_S1_BINDING")
            p=result.get("payload"); req(isinstance(p,dict) and digest(p)==result.get("payload_digest"),"RESULT_PAYLOAD_DIGEST")
            ident={k:result.get(k) for k in ("fabric_id","node_id","admission_id","work_id","observed_epoch","observed_state_digest","payload_digest")}
            req(result.get("result_id")=="nr:"+digest(ident),"RESULT_ID_MISMATCH")
            req(result.get("canonical_truth") is False and result.get("s1_write") is False and result.get("effect_authority") is False,"RESULT_AUTHORITY_ESCALATION")
            n=db.execute("SELECT admission_id FROM nodes WHERE node_id=?",(result.get("node_id"),)).fetchone()
            req(n is not None and n["admission_id"]==result.get("admission_id"),"RESULT_NODE_ADMISSION_MISMATCH")
            core={k:result.get(k) for k in ("schema","result_id","fabric_id","node_id","admission_id","work_id","observed_epoch","observed_state_digest","payload_digest","payload","canonical_truth","s1_write","effect_authority")}
            key=self._result_key(result["node_id"],result["admission_id"])
            req(hmac.compare_digest(str(result.get("result_auth_mac","")),hmac.new(key,canon(core),hashlib.sha256).hexdigest()),"RESULT_AUTH_MAC_INVALID")
            try:db.execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?)",(result["result_id"],lease.scope,result["node_id"],result["admission_id"],result["work_id"],result["observed_epoch"],result["observed_state_digest"],result["payload_digest"],lease.lease_id))
            except sqlite3.IntegrityError as e:raise DuplicateResult(result["result_id"]) from e
        return {"schema":"NODE_RESULT_ADMISSION/v1","status":"ADMITTED_CANDIDATE_ONLY","result_id":result["result_id"],"canonical_truth":False,"effect_authority":False}
