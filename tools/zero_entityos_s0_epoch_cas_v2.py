#!/usr/bin/env python3
"""Executable S0 same-generation stale-read discriminator.

Successor component for the EntityOS/HCU canonical-state boundary. A proposal binds
expected_s0_epoch observed when it was created. Admission uses BEGIN IMMEDIATE and
compares the current object epoch before mutation. Same-generation stale proposals
therefore fail closed.

No model/provider/network/effect execution occurs.
"""
from __future__ import annotations
import hashlib, json, sqlite3, tempfile
from pathlib import Path
from typing import Any

SCHEMA = "ENTITYOS_S0_EPOCH_CAS/v2"

class BoundaryError(ValueError): pass

def cj(v: Any) -> str:
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def dg(v: Any) -> str:
    return hashlib.sha256(cj(v).encode()).hexdigest()

class Authority:
    def __init__(self, path: Path):
        self.con=sqlite3.connect(path, isolation_level=None)
        self.con.row_factory=sqlite3.Row
        self.con.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS canonical_state(
          object_key TEXT PRIMARY KEY,value_json TEXT NOT NULL,value_digest TEXT NOT NULL,
          provenance TEXT NOT NULL,generation INTEGER NOT NULL,epoch INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS admission_log(
          admission_id TEXT PRIMARY KEY,proposal_id TEXT NOT NULL,source_result_id TEXT NOT NULL,
          generation INTEGER NOT NULL,object_key TEXT NOT NULL,expected_s0_epoch INTEGER NOT NULL,
          committed_s0_epoch INTEGER NOT NULL,value_digest TEXT NOT NULL);
        """)
    def close(self): self.con.close()
    def seed(self,key,value,*,generation,epoch,provenance="fixture"):
        self.con.execute("INSERT OR REPLACE INTO canonical_state VALUES(?,?,?,?,?,?)",
          (key,cj(value),dg(value),provenance,generation,epoch))
    def get(self,key):
        r=self.con.execute("SELECT * FROM canonical_state WHERE object_key=?",(key,)).fetchone()
        return dict(r) if r else None
    def admit(self,p,*,current_generation,new_epoch):
        if p.get("schema") != "DB_WRITE_PROPOSAL/v2": raise BoundaryError("PROPOSAL_SCHEMA_INVALID")
        if p.get("canonical_commit") is not False: raise BoundaryError("PROPOSAL_SELF_COMMIT_FORBIDDEN")
        if p.get("generation") != current_generation: raise BoundaryError("STALE_GENERATION_WRITE_PROPOSAL_REJECTED")
        if p.get("value_digest") != dg(p.get("value")): raise BoundaryError("PROPOSAL_VALUE_DIGEST_MISMATCH")
        expected=p.get("expected_s0_epoch")
        if isinstance(expected,bool) or not isinstance(expected,int) or expected < 0: raise BoundaryError("EXPECTED_S0_EPOCH_INVALID")
        self.con.execute("BEGIN IMMEDIATE")
        try:
            r=self.con.execute("SELECT epoch FROM canonical_state WHERE object_key=?",(p["object_key"],)).fetchone()
            current = 0 if r is None else int(r["epoch"])
            if current != expected: raise BoundaryError("STALE_S0_EPOCH_WRITE_PROPOSAL_REJECTED")
            if new_epoch <= current: raise BoundaryError("NEW_S0_EPOCH_NOT_MONOTONIC")
            self.con.execute("INSERT OR REPLACE INTO canonical_state VALUES(?,?,?,?,?,?)",
              (p["object_key"],cj(p["value"]),p["value_digest"],f"proposal:{p['proposal_id']}",current_generation,new_epoch))
            aid="dba-"+dg({"proposal_id":p["proposal_id"],"expected":expected,"committed":new_epoch,"value_digest":p["value_digest"]})[:24]
            self.con.execute("INSERT INTO admission_log VALUES(?,?,?,?,?,?,?,?)",
              (aid,p["proposal_id"],p["source_result_id"],current_generation,p["object_key"],expected,new_epoch,p["value_digest"]))
            self.con.execute("COMMIT")
            return aid
        except Exception:
            self.con.execute("ROLLBACK")
            raise

def proposal(pid,key,value,*,generation,expected_s0_epoch):
    p={"schema":"DB_WRITE_PROPOSAL/v2","proposal_id":pid,"source_result_id":"res-"+pid,
       "generation":generation,"object_key":key,"value":value,"value_digest":dg(value),
       "expected_s0_epoch":expected_s0_epoch,"canonical_commit":False}
    return p

def run(path: Path):
    a=Authority(path); generation=3
    try:
        a.seed("memory/admitted",{"v":"base"},generation=generation,epoch=7)
        # A and B read the same epoch before either commits.
        A=proposal("A","memory/admitted",{"v":"A"},generation=generation,expected_s0_epoch=7)
        B=proposal("B","memory/admitted",{"v":"B"},generation=generation,expected_s0_epoch=7)
        aid=a.admit(A,current_generation=generation,new_epoch=8)
        stale_rejected=False
        try: a.admit(B,current_generation=generation,new_epoch=9)
        except BoundaryError as e: stale_rejected=str(e)=="STALE_S0_EPOCH_WRITE_PROPOSAL_REJECTED"
        if not stale_rejected: raise BoundaryError("SAME_GENERATION_STALE_READ_NOT_REJECTED")
        row=a.get("memory/admitted")
        if json.loads(row["value_json"]) != {"v":"A"} or row["epoch"] != 8:
            raise BoundaryError("STALE_REJECTION_DID_NOT_PRESERVE_WINNER")
        # Fresh B rebases to epoch 8 and may then commit.
        B2=proposal("B2","memory/admitted",{"v":"B"},generation=generation,expected_s0_epoch=8)
        aid2=a.admit(B2,current_generation=generation,new_epoch=9)
        row2=a.get("memory/admitted")
        if json.loads(row2["value_json"]) != {"v":"B"} or row2["epoch"] != 9:
            raise BoundaryError("FRESH_REBASE_DID_NOT_COMMIT")
        return {"schema":SCHEMA,"pass":True,"generation":generation,"initial_epoch":7,
          "A_commit_epoch":8,"B_same_generation_stale_rejected":True,"B_rebase_commit_epoch":9,
          "admission_A":aid,"admission_B_rebased":aid2,
          "credit_scope":"S0_EPOCH_CAS_COMPONENT_ONLY_NOT_WHOLE_ENTITYOS_HCU"}
    finally: a.close()

if __name__=="__main__":
    with tempfile.TemporaryDirectory() as td:
        print(json.dumps(run(Path(td)/"s0.sqlite"),sort_keys=True,indent=2))
