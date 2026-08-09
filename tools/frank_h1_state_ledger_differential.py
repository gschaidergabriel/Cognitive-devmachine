#!/usr/bin/env python3
"""FRANK H1 H-WP-02 three-lineage ledger differential.

Research-Entity/Harness experiment only; never a production or promotion oracle.
Runs one fixture family against the three current ledger lineages and emits a receipt.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, platform, sqlite3, tempfile, threading, traceback
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
PATHS={
 "A":ROOT/"research_entity/harness/reference_state_ledger.py",
 "B":ROOT/"research_entity/harness/reference/state_ledger.py",
 "O":ROOT/"research_entity/harness/reference/oracle_state_ledger.py",
}
OUT=ROOT/"research_entity/harness/receipts/HWP02_THREE_LINEAGE_DIFFERENTIAL_RECEIPT.json"
T="2026-08-09T12:00:00Z"

def load(name,p):
 s=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def hfile(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def cj(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)

class L:
 def __init__(self,k,m,p): self.k,self.m,self.path=k,m,p
 def new(self,p): return (self.m.OracleStateLedger if self.k=="O" else self.m.StateLedger)(p)
 def close(self,x): x.close()
 def epoch(self,x): return int(x.head()["epoch"] if self.k=="A" else x.epoch)
 def sem(self,x): return str(x.head()["root_hash"] if self.k=="A" else x.semantic_state_hash)
 def ver(self,x): return str(x.state_version_hash) if self.k=="O" else None
 def trace(self,x): return str(x.head()["event_hash"] if self.k=="A" else x.trace_root_hash)
 def count(self,x):
  q="SELECT COUNT(*) FROM ledger_events" if self.k=="A" else "SELECT COUNT(*) FROM events"
  c=x.db if self.k=="A" else x.conn; return int(c.execute(q).fetchone()[0])
 def get(self,x,d,k):
  r=x.read(d,k) if self.k=="A" else x.get(d,k); return None if r is None else r.get("value")
 def domains(self,x): return None if self.k=="A" else dict(x.domain_epochs())
 def commit(self,x,e,i,b,muts,writer="chatgpt-secondary",exe=None):
  prov={"fixture":"HWP02_THREE_LINEAGE"}; src={"source":"shared_fixture"}; exe=exe or {}
  if self.k=="A":
   mm=[self.m.Mutation(z["domain"],z["key"],z.get("value"),z.get("epistemic","KNOWN")) for z in muts]
   return x.commit(event_id=e,idempotency_key=i,base_epoch=b,event_type="TEST",mutations=mm,
                   provenance=prov,committed_at=T,writer_node=writer)
  if self.k=="B":
   ops=[{"op":z.get("op","SET"),"domain":z["domain"],"key":z["key"],"value":z.get("value"),
         "epistemic":z.get("epistemic","KNOWN"),"status":z.get("status","CURRENT")} for z in muts]
   return x.append_event(event_id=e,idem=i,base_epoch=b,event_type="TEST",writer=writer,ops=ops,
                         provenance=prov,source=src,execution=exe,committed_at=T)
  mm=[self.m.Mutation(z["domain"],z["key"],z.get("value"),z.get("op","SET"),
                      z.get("epistemic","KNOWN"),z.get("status","CURRENT")) for z in muts]
  return x.commit(event_id=e,idem=i,base_epoch=b,event_type="TEST",writer=writer,mutations=mm,
                  provenance=prov,source=src,execution=exe,committed_at=T)
 def abort_event_insert(self,x):
  table="ledger_events" if self.k=="A" else "events"; c=x.db if self.k=="A" else x.conn
  c.execute(f"CREATE TRIGGER diff_abort BEFORE INSERT ON {table} BEGIN SELECT RAISE(ABORT,'diff_fault'); END")

def rec(name,fn):
 try:
  ok,detail=fn(); return {"name":name,"status":"PASS" if ok else "FAIL","detail":detail}
 except NotImplementedError as e: return {"name":name,"status":"UNSUPPORTED","detail":str(e)}
 except Exception as e: return {"name":name,"status":"ERROR","detail":{"type":type(e).__name__,"message":str(e),"trace":traceback.format_exc(limit=4)}}

def pair(a,td,n): return a.new(Path(td)/f"{a.k}.{n}.1.db"),a.new(Path(td)/f"{a.k}.{n}.2.db")

def run_one(a):
 R=[]
 with tempfile.TemporaryDirectory(prefix=f"frank-hwp02-{a.k}-") as td:
  def history():
   x,y=pair(a,td,"hist")
   try:
    a.commit(x,"x1","x1",0,[{"domain":"w","key":"x","value":1},{"domain":"w","key":"y","value":2}])
    a.commit(y,"y1","y1",0,[{"domain":"w","key":"x","value":1}]); a.commit(y,"y2","y2",1,[{"domain":"w","key":"y","value":2}])
    same=a.sem(x)==a.sem(y); vd=None if a.ver(x) is None else a.ver(x)!=a.ver(y)
    return same,{"semantic_equal":same,"version_distinguishes_history":vd,"epochs":[a.epoch(x),a.epoch(y)]}
   finally:a.close(x);a.close(y)
  R.append(rec("same_semantic_state_commutes_across_history",history))

  def collection(kind,expect_equal):
   x,y=pair(a,td,kind)
   try:
    v1={"$kind":kind,"items":[3,1,1,2] if kind=="set" else [1,2]}; v2={"$kind":kind,"items":[2,3,1] if kind=="set" else [2,1]}
    a.commit(x,"c1","c1",0,[{"domain":"gwt","key":"v","value":v1}]); a.commit(y,"c2","c2",0,[{"domain":"gwt","key":"v","value":v2}])
    eq=a.sem(x)==a.sem(y); return eq==expect_equal,{"semantic_equal":eq}
   finally:a.close(x);a.close(y)
  R.append(rec("typed_set_permutation_invariant",lambda:collection("set",True)))
  R.append(rec("typed_ordered_permutation_sensitive",lambda:collection("ordered",False)))

  def execution():
   x,y=pair(a,td,"exec")
   try:
    m=[{"domain":"effect","key":"intent","value":"same"}]
    a.commit(x,"e","i",0,m,writer="A",exe={"attempt":1}); a.commit(y,"e","i",0,m,writer="B",exe={"attempt":2})
    se=a.sem(x)==a.sem(y); tdif=a.trace(x)!=a.trace(y); return se and tdif,{"semantic_equal":se,"trace_distinct":tdif}
   finally:a.close(x);a.close(y)
  R.append(rec("execution_changes_trace_not_semantic_state",execution))

  def stale():
   x=a.new(Path(td)/f"{a.k}.stale.db")
   try:
    a.commit(x,"e1","e1",0,[{"domain":"w","key":"x","value":1}]); before=(a.epoch(x),a.sem(x),a.trace(x),a.count(x)); rejected=False
    try:a.commit(x,"bad","bad",0,[{"domain":"w","key":"y","value":2}])
    except Exception:rejected=True
    after=(a.epoch(x),a.sem(x),a.trace(x),a.count(x)); return rejected and before==after and a.get(x,"w","y") is None,{"rejected":rejected,"unchanged":before==after}
   finally:a.close(x)
  R.append(rec("stale_epoch_fails_closed",stale))

  def idem():
   x=a.new(Path(td)/f"{a.k}.idem.db")
   try:
    m=[{"domain":"w","key":"x","value":1}]; a.commit(x,"e","i",0,m); rp=a.commit(x,"e","i",0,m,writer="retry",exe={"attempt":2}); bad=False
    try:a.commit(x,"e","i",0,[{"domain":"w","key":"x","value":9}])
    except Exception:bad=True
    return bad and a.count(x)==1 and a.get(x,"w","x")==1,{"replay":rp.get("status"),"collision_rejected":bad,"events":a.count(x)}
   finally:a.close(x)
  R.append(rec("idempotency_payload_bound",idem))

  def race():
   db=Path(td)/f"{a.k}.race.db"; z=a.new(db);a.close(z);bar=threading.Barrier(2);out=[];err=[];mu=threading.Lock()
   def w(n):
    x=a.new(db)
    try:
     bar.wait(5); r=a.commit(x,"race","race",0,[{"domain":"w","key":"r","value":1}],writer=n,exe={"worker":n});
     with mu:out.append(str(r.get("status")))
    except Exception as e:
     with mu:err.append(type(e).__name__+":"+str(e))
    finally:a.close(x)
   ts=[threading.Thread(target=w,args=(f"w{i}",),daemon=True) for i in range(2)];[t.start() for t in ts];[t.join(12) for t in ts]
   x=a.new(db)
   try: cnt=a.count(x);val=a.get(x,"w","r")
   finally:a.close(x)
   hung=any(t.is_alive() for t in ts); return (not hung and not err and cnt==1 and val==1 and len(out)==2),{"statuses":sorted(out),"errors":err,"hung":hung,"events":cnt}
  R.append(rec("concurrent_same_idem_converges_without_error",race))

  def fault():
   x=a.new(Path(td)/f"{a.k}.fault.db")
   try:
    before=(a.epoch(x),a.sem(x),a.trace(x),a.count(x));a.abort_event_insert(x);rej=False
    try:a.commit(x,"f","f",0,[{"domain":"w","key":"f","value":9}])
    except Exception:rej=True
    after=(a.epoch(x),a.sem(x),a.trace(x),a.count(x));return rej and before==after and a.get(x,"w","f") is None,{"rejected":rej,"unchanged":before==after}
   finally:a.close(x)
  R.append(rec("event_insert_fault_rolls_back_atomically",fault))

  def domains():
   if a.k=="A":raise NotImplementedError("no domain-epoch surface")
   x=a.new(Path(td)/f"{a.k}.domains.db")
   try:
    a.commit(x,"d1","d1",0,[{"domain":"world","key":"x","value":1},{"domain":"memory","key":"m","value":1}]);a.commit(x,"d2","d2",1,[{"domain":"world","key":"x","value":2}]);d=a.domains(x) or {}
    return d.get("world")==2 and d.get("memory")==1,d
   finally:a.close(x)
  R.append(rec("domain_epochs_only_advance_touched_domains",domains))

  def replay():
   x=a.new(Path(td)/f"{a.k}.replay.db")
   try:
    for i in range(8):a.commit(x,f"r{i}",f"r{i}",i,[{"domain":["world","gwt","memory"][i%3],"key":f"k{i%4}","value":{"i":i}}],exe={"attempt":i})
    if a.k=="A":
     x.snapshot(snapshot_id="s",created_at=T,created_by="chatgpt-secondary");p=Path(td)/"a.snap";x.export_snapshot("s",p);y=a.m.StateLedger.restore_snapshot(p,Path(td)/"a.restore.db")
     try:return a.sem(x)==a.sem(y),{"mode":"snapshot_restore","semantic_equal":a.sem(x)==a.sem(y)}
     finally:y.close()
    ev=x.export_events();cls=a.m.StateLedger if a.k=="B" else a.m.OracleStateLedger;y=cls.replay(ev,Path(td)/f"{a.k}.replayed.db")
    try:return a.sem(x)==a.sem(y) and a.trace(x)==a.trace(y),{"mode":"event_replay","semantic_equal":a.sem(x)==a.sem(y),"trace_equal":a.trace(x)==a.trace(y)}
    finally:y.close()
   finally:a.close(x)
  R.append(rec("replay_or_recovery_reconstructs_identity",replay))

  def tamper():
   x=a.new(Path(td)/f"{a.k}.snap.db")
   try:
    a.commit(x,"s","s",0,[{"domain":"w","key":"x","value":{"v":1}}])
    if a.k=="B":
     x.snapshot("s");r=x.conn.execute("SELECT state_json FROM snapshots WHERE id='s'").fetchone();v=json.loads(r[0]);v[0]["value"]={"tampered":True};x.conn.execute("UPDATE snapshots SET state_json=? WHERE id='s'",(cj(v),));x.conn.commit();ok=not bool(x.verify_snapshot("s"));return ok,{"verify_snapshot":not ok}
    if a.k=="A": x.snapshot(snapshot_id="s",created_at=T,created_by="chatgpt-secondary");p=Path(td)/"a.tamper";x.export_snapshot("s",p);env=json.loads(p.read_text());env["state"][0]["value"]={"tampered":True};p.write_text(cj(env));restore=lambda:a.m.StateLedger.restore_snapshot(p,Path(td)/"bad.db")
    else: x.snapshot("s",created_at=T);p=Path(td)/"o.tamper";x.export_snapshot("s",p);env=json.loads(p.read_text());env["payload"]["events"][0]["mutations"][0]["value"]={"tampered":True};p.write_text(cj(env));restore=lambda:a.m.OracleStateLedger.restore_snapshot(p,Path(td)/"bad.db")
    try:restore()
    except Exception as e:return True,{"rejected_as":type(e).__name__}
    return False,"tampered snapshot restored"
   finally:a.close(x)
  R.append(rec("snapshot_tamper_rejected",tamper))

 C={s:sum(r["status"]==s for r in R) for s in ["PASS","FAIL","ERROR","UNSUPPORTED"]}
 return {"lineage":a.k,"source_path":str(a.path.relative_to(ROOT)),"source_sha256":hfile(a.path),"checks":R,"counts":C}

def run():
 mods={k:load("frank_hwp02_"+k,p) for k,p in PATHS.items()};lines=[run_one(L(k,mods[k],PATHS[k])) for k in ["A","B","O"]];o=next(x for x in lines if x["lineage"]=="O");bad=[c["name"] for c in o["checks"] if c["status"]!="PASS"]
 names=[c["name"] for c in o["checks"]];div=[]
 for n in names:
  s={x["lineage"]:next(c["status"] for c in x["checks"] if c["name"]==n) for x in lines}
  if len(set(s.values()))>1:div.append({"check":n,"statuses":s})
 r={"schema_version":"1.0","experiment":"FRANK_H1_HWP02_THREE_LINEAGE_DIFFERENTIAL","promotion":"NONE","actor":{"actor_id":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol"},"environment":{"platform":platform.platform(),"python":platform.python_version(),"sqlite":sqlite3.sqlite_version,"pid":os.getpid()},"lineages":lines,"synthesis":{"authority":"DIFFERENTIAL_ONLY_NOT_PROMOTION","target_ubuntu_required":True,"recommendation":"ORACLE_THREE_ROOT_REMAINS_DIFFERENTIAL_CANDIDATE" if not bad else "NO_SELECTION_ORACLE_FAILED","oracle_nonpass":bad,"discriminating_checks":div,"identity_contract":{"semantic_state":"current meaning only","state_version":"history/epoch identity","trace_root":"execution/provenance identity"}}}
 r["receipt_sha256"]=hashlib.sha256(cj(r).encode()).hexdigest();return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,default=OUT);ap.add_argument("--strict-oracle",action="store_true");a=ap.parse_args();r=run();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False,sort_keys=True)+"\n");print(json.dumps({"output":str(a.output),"sha256":r["receipt_sha256"],"recommendation":r["synthesis"]["recommendation"],"counts":{x["lineage"]:x["counts"] for x in r["lineages"]}},indent=2));return 2 if a.strict_oracle and r["synthesis"]["oracle_nonpass"] else 0
if __name__=="__main__":raise SystemExit(main())
