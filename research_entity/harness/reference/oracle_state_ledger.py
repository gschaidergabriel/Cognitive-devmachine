#!/usr/bin/env python3
"""Merged H-WP-02 H1 oracle ledger candidate.

Research-Entity implementation for FRANK H1 Harness.
Combines evidenced invariants from both current state-ledger lineages:
- typed canonical semantic values;
- pure current semantic-state identity;
- separate state-version/history identity;
- separate provenance/execution trace identity;
- domain epochs + global CAS;
- payload-bound idempotency checked under write lock;
- append-only event receipts;
- snapshot/restore and tamper verification.

This is a Harness research candidate, not production-FRANK evidence.
"""
from __future__ import annotations
import copy, hashlib, json, sqlite3, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "h1-oracle-ledger-0.1"
GENESIS_SEMANTIC_CHAIN = hashlib.sha256(b"HWP02:oracle:semantic:genesis").hexdigest()
GENESIS_EXECUTION_CHAIN = hashlib.sha256(b"HWP02:oracle:execution:genesis").hexdigest()
EPI = {"KNOWN","UNKNOWN","CONFLICT","REVOKED","HYPOTHESIS","OBSERVED"}
STATUS = {"CURRENT","RETRACTED","SUPERSEDED","QUARANTINED"}
OPS = {"SET","RETRACT","SUPERSEDE","DELETE"}

class LedgerError(RuntimeError): pass
class StaleEpoch(LedgerError): pass
class IdempotencyConflict(LedgerError): pass
class InvalidOperation(LedgerError): pass
class TamperDetected(LedgerError): pass

def canon(v: Any) -> Any:
    if isinstance(v, dict):
        kind = v.get("$kind")
        if kind in ("set","ordered"):
            items = v.get("items", [])
            if not isinstance(items, list):
                raise InvalidOperation("typed collection items must be list")
            xs = [canon(x) for x in items]
            if kind == "set":
                dedup = {json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",",":")): x for x in xs}
                xs = [dedup[k] for k in sorted(dedup)]
            return {"$kind": kind, "items": xs}
        return {str(k): canon(v[k]) for k in sorted(v, key=str)}
    if isinstance(v, (list, tuple)):
        return [canon(x) for x in v]
    if v is None or isinstance(v, (str, int, bool)):
        return v
    if isinstance(v, float):
        if not (float("-inf") < v < float("inf")):
            raise InvalidOperation("non-finite float")
        return v
    raise InvalidOperation(f"unsupported canonical type {type(v).__name__}")

def cjson(v: Any) -> str:
    return json.dumps(canon(v), ensure_ascii=False, sort_keys=True, separators=(",",":"), allow_nan=False)

def h(v: Any) -> str:
    return hashlib.sha256(cjson(v).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class Mutation:
    domain: str
    key: str
    value: Any
    op: str = "SET"
    epistemic: str = "KNOWN"
    status: str = "CURRENT"

    def normalized(self) -> dict[str, Any]:
        op = self.op.upper()
        epi = self.epistemic.upper()
        st = self.status.upper()
        if op not in OPS or epi not in EPI or st not in STATUS:
            raise InvalidOperation("invalid op/epistemic/status")
        if not self.domain.strip() or not self.key.strip():
            raise InvalidOperation("domain/key required")
        if op in ("RETRACT","DELETE"): st = "RETRACTED"
        elif op == "SUPERSEDE": st = "SUPERSEDED"
        value = copy.deepcopy(self.value)
        cjson(value)
        return {"op":op,"domain":self.domain.strip(),"key":self.key.strip(),
                "value":value,"epistemic":epi,"status":st}

SCHEMA = """
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS domain_epochs(domain TEXT PRIMARY KEY, epoch INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS state(
  domain TEXT NOT NULL, k TEXT NOT NULL, value_json TEXT,
  epistemic TEXT NOT NULL, status TEXT NOT NULL, domain_epoch INTEGER NOT NULL,
  semantic_hash TEXT NOT NULL, source_event_id TEXT NOT NULL, provenance_json TEXT NOT NULL,
  PRIMARY KEY(domain,k)
);
CREATE TABLE IF NOT EXISTS events(
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT UNIQUE NOT NULL, idem TEXT UNIQUE NOT NULL,
  base_epoch INTEGER NOT NULL, epoch INTEGER UNIQUE NOT NULL,
  event_type TEXT NOT NULL, writer TEXT NOT NULL,
  mutations_json TEXT NOT NULL, provenance_json TEXT NOT NULL,
  source_json TEXT NOT NULL, execution_json TEXT NOT NULL,
  request_fingerprint TEXT NOT NULL,
  semantic_event_hash TEXT NOT NULL,
  semantic_chain_hash TEXT NOT NULL,
  execution_chain_hash TEXT NOT NULL,
  semantic_state_hash TEXT NOT NULL,
  state_version_hash TEXT NOT NULL,
  trace_root_hash TEXT NOT NULL,
  committed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots(
  id TEXT PRIMARY KEY, epoch INTEGER NOT NULL,
  semantic_state_hash TEXT NOT NULL, state_version_hash TEXT NOT NULL,
  trace_root_hash TEXT NOT NULL, payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
"""

class OracleStateLedger:
    def __init__(self, path=":memory:"):
        self.path = path
        self.conn = sqlite3.connect(str(path), timeout=10, isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA busy_timeout=10000")
        self.conn.executescript(SCHEMA)
        defaults = {
            "global_epoch":"0",
            "semantic_chain_hash":GENESIS_SEMANTIC_CHAIN,
            "execution_chain_hash":GENESIS_EXECUTION_CHAIN,
            "semantic_state_hash":"",
            "state_version_hash":"",
            "trace_root_hash":"",
        }
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            for k,v in defaults.items():
                self.conn.execute("INSERT OR IGNORE INTO meta(k,v) VALUES(?,?)",(k,v))
            if not self._m("semantic_state_hash"):
                ss,sv,tr = self._roots()
                self._set("semantic_state_hash",ss); self._set("state_version_hash",sv); self._set("trace_root_hash",tr)
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK"); raise

    def close(self): self.conn.close()
    def _m(self,k):
        r=self.conn.execute("SELECT v FROM meta WHERE k=?",(k,)).fetchone()
        if not r: raise LedgerError("missing meta "+k)
        return str(r[0])
    def _set(self,k,v): self.conn.execute("INSERT OR REPLACE INTO meta(k,v) VALUES(?,?)",(k,str(v)))
    @property
    def epoch(self): return int(self._m("global_epoch"))
    @property
    def semantic_state_hash(self): return self._m("semantic_state_hash")
    @property
    def state_version_hash(self): return self._m("state_version_hash")
    @property
    def trace_root_hash(self): return self._m("trace_root_hash")

    def domain_epochs(self):
        return {r["domain"]:int(r["epoch"]) for r in self.conn.execute("SELECT domain,epoch FROM domain_epochs ORDER BY domain")}

    def materialized(self, include_provenance=False):
        rows=[]
        q="SELECT domain,k,value_json,epistemic,status,domain_epoch,semantic_hash,source_event_id,provenance_json FROM state ORDER BY domain,k"
        for r in self.conn.execute(q):
            x={"domain":r["domain"],"key":r["k"],"value":json.loads(r["value_json"]) if r["value_json"] is not None else None,
               "epistemic":r["epistemic"],"status":r["status"],"domain_epoch":int(r["domain_epoch"]),
               "semantic_hash":r["semantic_hash"]}
            if include_provenance:
                x["source_event_id"]=r["source_event_id"]; x["provenance"]=json.loads(r["provenance_json"])
            rows.append(x)
        return rows

    def semantic_materialized(self):
        return [{"domain":r["domain"],"key":r["key"],"value":r["value"],
                 "epistemic":r["epistemic"],"status":r["status"]}
                for r in self.materialized(False)]

    def _roots(self):
        ss = h({"schema":SCHEMA_VERSION,"state":self.semantic_materialized()})
        sv = h({"schema":SCHEMA_VERSION,"global_epoch":self.epoch,"domain_epochs":self.domain_epochs(),
                "semantic_state_hash":ss,"semantic_chain_hash":self._m("semantic_chain_hash")})
        tr = h({"state_version_hash":sv,"execution_chain_hash":self._m("execution_chain_hash")})
        return ss,sv,tr

    def _normalize_mutations(self, muts: Iterable[Mutation|dict]) -> list[dict]:
        out=[]
        for m in muts:
            if isinstance(m, Mutation): out.append(m.normalized())
            elif isinstance(m, dict):
                out.append(Mutation(domain=str(m.get("domain","")),key=str(m.get("key","")),
                                    value=copy.deepcopy(m.get("value")),op=str(m.get("op","SET")),
                                    epistemic=str(m.get("epistemic","KNOWN")),
                                    status=str(m.get("status","CURRENT"))).normalized())
            else: raise InvalidOperation("mutation object required")
        if not out: raise InvalidOperation("empty transaction")
        return out

    @staticmethod
    def _request_fingerprint(*, event_id, base_epoch, event_type, mutations, provenance, source):
        return h({"event_id":event_id,"base_epoch":int(base_epoch),"event_type":event_type,
                  "mutations":mutations,"provenance":provenance,"source":source})

    def _idempotent_locked(self, idem, fingerprint):
        row=self.conn.execute("SELECT * FROM events WHERE idem=?",(idem,)).fetchone()
        if not row: return None
        if row["request_fingerprint"] != fingerprint:
            raise IdempotencyConflict(idem)
        return {"status":"IDEMPOTENT_REPLAY","event_id":row["event_id"],"epoch":int(row["epoch"]),
                "semantic_state_hash":row["semantic_state_hash"],"state_version_hash":row["state_version_hash"],
                "trace_root_hash":row["trace_root_hash"]}

    def commit(self, *, event_id, idem, base_epoch, event_type, writer, mutations,
               provenance=None, source=None, execution=None, committed_at=None, fault_after=None):
        if not event_id or not idem or not event_type or not writer:
            raise InvalidOperation("event_id/idem/event_type/writer required")
        muts=self._normalize_mutations(mutations)
        provenance=copy.deepcopy(provenance or {}); source=copy.deepcopy(source or {}); execution=copy.deepcopy(execution or {})
        cjson(provenance); cjson(source); cjson(execution)
        fp=self._request_fingerprint(event_id=event_id,base_epoch=base_epoch,event_type=event_type,
                                     mutations=muts,provenance=provenance,source=source)
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            old=self._idempotent_locked(idem,fp)
            if old:
                self.conn.execute("COMMIT")
                return old
            cur=self.epoch
            if int(base_epoch)!=cur: raise StaleEpoch(f"{base_epoch}!={cur}")
            ne=cur+1
            touched={}
            for d in sorted({m["domain"] for m in muts}):
                r=self.conn.execute("SELECT epoch FROM domain_epochs WHERE domain=?",(d,)).fetchone()
                de=(int(r["epoch"]) if r else 0)+1
                touched[d]=de
                self.conn.execute("INSERT INTO domain_epochs(domain,epoch) VALUES(?,?) ON CONFLICT(domain) DO UPDATE SET epoch=excluded.epoch",(d,de))
            prov_json=cjson(provenance)
            for m in muts:
                rh=h({"domain":m["domain"],"key":m["key"],"value":m["value"],"epistemic":m["epistemic"],"status":m["status"]})
                self.conn.execute("""INSERT INTO state(domain,k,value_json,epistemic,status,domain_epoch,semantic_hash,source_event_id,provenance_json)
                    VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(domain,k) DO UPDATE SET
                    value_json=excluded.value_json,epistemic=excluded.epistemic,status=excluded.status,
                    domain_epoch=excluded.domain_epoch,semantic_hash=excluded.semantic_hash,
                    source_event_id=excluded.source_event_id,provenance_json=excluded.provenance_json""",
                    (m["domain"],m["key"],cjson(m["value"]),m["epistemic"],m["status"],touched[m["domain"]],rh,event_id,prov_json))
            if fault_after=="state": raise RuntimeError("fault_after_state")
            sem_event=h({"event_type":event_type,"mutations":muts})
            sch=h({"prev":self._m("semantic_chain_hash"),"semantic_event_hash":sem_event,"epoch":ne,"domain_epochs":touched})
            exe_hash=h(execution)
            ech=h({"prev":self._m("execution_chain_hash"),"event_id":event_id,"idem":idem,
                   "request_fingerprint":fp,"execution_hash":exe_hash,"writer":writer,"epoch":ne})
            self._set("global_epoch",ne); self._set("semantic_chain_hash",sch); self._set("execution_chain_hash",ech)
            ss,sv,tr=self._roots()
            self._set("semantic_state_hash",ss); self._set("state_version_hash",sv); self._set("trace_root_hash",tr)
            ts=committed_at or time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
            self.conn.execute("""INSERT INTO events(event_id,idem,base_epoch,epoch,event_type,writer,mutations_json,
                provenance_json,source_json,execution_json,request_fingerprint,semantic_event_hash,semantic_chain_hash,
                execution_chain_hash,semantic_state_hash,state_version_hash,trace_root_hash,committed_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (event_id,idem,cur,ne,event_type,writer,cjson(muts),prov_json,cjson(source),cjson(execution),fp,
                 sem_event,sch,ech,ss,sv,tr,ts))
            if fault_after=="event": raise RuntimeError("fault_after_event")
            self.conn.execute("COMMIT")
            return {"status":"COMMITTED","event_id":event_id,"epoch":ne,"domain_epochs":touched,
                    "semantic_state_hash":ss,"state_version_hash":sv,"trace_root_hash":tr}
        except Exception:
            self.conn.execute("ROLLBACK"); raise

    def export_events(self):
        out=[]
        for r in self.conn.execute("SELECT * FROM events ORDER BY seq"):
            out.append({"event_id":r["event_id"],"idem":r["idem"],"base_epoch":int(r["base_epoch"]),
                        "event_type":r["event_type"],"writer":r["writer"],
                        "mutations":json.loads(r["mutations_json"]),"provenance":json.loads(r["provenance_json"]),
                        "source":json.loads(r["source_json"]),"execution":json.loads(r["execution_json"]),
                        "committed_at":r["committed_at"]})
        return out

    @classmethod
    def replay(cls, events, path=":memory:"):
        x=cls(path)
        for e in events: x.commit(**e)
        return x

    def verify(self):
        prev_s=GENESIS_SEMANTIC_CHAIN
        prev_e=GENESIS_EXECUTION_CHAIN
        expected=1
        domain_counts={}
        for r in self.conn.execute("SELECT * FROM events ORDER BY seq"):
            if int(r["epoch"])!=expected or int(r["base_epoch"])!=expected-1:
                raise TamperDetected("non-contiguous epoch")
            muts=json.loads(r["mutations_json"])
            prov=json.loads(r["provenance_json"])
            src=json.loads(r["source_json"])
            exe=json.loads(r["execution_json"])
            fp=self._request_fingerprint(event_id=r["event_id"],base_epoch=r["base_epoch"],event_type=r["event_type"],
                                         mutations=muts,provenance=prov,source=src)
            if fp!=r["request_fingerprint"]:
                raise TamperDetected("request fingerprint mismatch")
            se=h({"event_type":r["event_type"],"mutations":muts})
            if se!=r["semantic_event_hash"]:
                raise TamperDetected("semantic event mismatch")
            touched={}
            for d in sorted({x["domain"] for x in muts}):
                domain_counts[d]=domain_counts.get(d,0)+1
                touched[d]=domain_counts[d]
            sch=h({"prev":prev_s,"semantic_event_hash":se,"epoch":expected,"domain_epochs":touched})
            if sch!=r["semantic_chain_hash"]:
                raise TamperDetected("semantic chain mismatch")
            ech=h({"prev":prev_e,"event_id":r["event_id"],"idem":r["idem"],
                   "request_fingerprint":fp,"execution_hash":h(exe),"writer":r["writer"],"epoch":expected})
            if ech!=r["execution_chain_hash"]:
                raise TamperDetected("execution chain mismatch")
            prev_s=sch; prev_e=ech; expected+=1
        if prev_s!=self._m("semantic_chain_hash") or prev_e!=self._m("execution_chain_hash"):
            raise TamperDetected("head chain mismatch")
        if domain_counts!=self.domain_epochs():
            raise TamperDetected("domain epoch mismatch")
        clone=self.replay(self.export_events())
        try:
            if (clone.semantic_state_hash!=self.semantic_state_hash or
                clone.state_version_hash!=self.state_version_hash or
                clone.trace_root_hash!=self.trace_root_hash or
                clone.domain_epochs()!=self.domain_epochs()):
                raise TamperDetected("replay root mismatch")
        finally:
            clone.close()
        return {"status":"PASS","events":expected-1,"epoch":self.epoch,
                "semantic_state_hash":self.semantic_state_hash,"state_version_hash":self.state_version_hash,
                "trace_root_hash":self.trace_root_hash}

    def snapshot(self, sid, created_at=None):
        v=self.verify()
        payload={"schema":SCHEMA_VERSION,"epoch":self.epoch,"events":self.export_events(),
                 "semantic_state_hash":self.semantic_state_hash,
                 "state_version_hash":self.state_version_hash,"trace_root_hash":self.trace_root_hash,
                 "domain_epochs":self.domain_epochs()}
        ph=h(payload)
        ts=created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        self.conn.execute("""INSERT OR REPLACE INTO snapshots(
            id,epoch,semantic_state_hash,state_version_hash,trace_root_hash,payload_json,payload_hash,created_at)
            VALUES(?,?,?,?,?,?,?,?)""",
            (sid,self.epoch,self.semantic_state_hash,self.state_version_hash,self.trace_root_hash,cjson(payload),ph,ts))
        return {"id":sid,"payload_hash":ph,**v}

    def verify_snapshot(self,sid):
        r=self.conn.execute("SELECT * FROM snapshots WHERE id=?",(sid,)).fetchone()
        if not r:
            return False
        try:
            payload=json.loads(r["payload_json"])
            if h(payload)!=r["payload_hash"]:
                return False
            if payload.get("schema")!=SCHEMA_VERSION or int(payload.get("epoch",-1))!=int(r["epoch"]):
                return False
            clone=self.replay(payload["events"])
            try:
                return (clone.semantic_state_hash==payload["semantic_state_hash"]==r["semantic_state_hash"] and
                        clone.state_version_hash==payload["state_version_hash"]==r["state_version_hash"] and
                        clone.trace_root_hash==payload["trace_root_hash"]==r["trace_root_hash"] and
                        clone.domain_epochs()==payload["domain_epochs"])
            finally:
                clone.close()
        except Exception:
            return False

    def export_snapshot(self,sid,path):
        r=self.conn.execute("SELECT payload_json,payload_hash FROM snapshots WHERE id=?",(sid,)).fetchone()
        if not r:
            raise LedgerError("snapshot not found")
        envelope={"payload":json.loads(r["payload_json"]),"payload_hash":r["payload_hash"]}
        Path(path).write_text(cjson(envelope),encoding="utf-8")
        return Path(path)

    @classmethod
    def restore_snapshot(cls,snapshot_path,db_path=":memory:"):
        envelope=json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
        payload=envelope.get("payload")
        if not isinstance(payload,dict) or h(payload)!=envelope.get("payload_hash"):
            raise TamperDetected("snapshot envelope hash mismatch")
        if payload.get("schema")!=SCHEMA_VERSION:
            raise LedgerError("snapshot schema mismatch")
        ledger=cls.replay(payload.get("events",[]),path=db_path)
        if (ledger.epoch!=int(payload["epoch"]) or
            ledger.semantic_state_hash!=payload["semantic_state_hash"] or
            ledger.state_version_hash!=payload["state_version_hash"] or
            ledger.trace_root_hash!=payload["trace_root_hash"] or
            ledger.domain_epochs()!=payload["domain_epochs"]):
            ledger.close()
            raise TamperDetected("snapshot restore root mismatch")
        return ledger

    def get(self, domain, key):
        r=self.conn.execute("SELECT * FROM state WHERE domain=? AND k=?",(domain,key)).fetchone()
        if not r: return None
        return {"value":json.loads(r["value_json"]) if r["value_json"] is not None else None,
                "epistemic":r["epistemic"],"status":r["status"],"domain_epoch":int(r["domain_epoch"]),
                "semantic_hash":r["semantic_hash"],"source_event_id":r["source_event_id"],
                "provenance":json.loads(r["provenance_json"])}
