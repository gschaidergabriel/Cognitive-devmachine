#!/usr/bin/env python3
"""FrankGrid10: noncanonical sandbox-first ChatGPT control organ.

TypedEntry -> 10-cell competition -> selection -> broadcast -> Hyperposition
-> emitted response -> HyperMirror -> uptake/mismatch -> recurrent reentry.
No truth/effect authority is created by this wrapper.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, sqlite3, sys, time, uuid
from pathlib import Path

SCHEMA="FRANKGRID10/v1"
DB_DEFAULT=Path(__file__).with_name("frankgrid10.sqlite3")
CELLS={
 "G1":("EVIDENCE",("beleg","evidence","receipt","quelle","source","prüf","verify","aktuell")),
 "G2":("CAUSALITY",("warum","ursache","kausal","cause","wirkung","effect","reentry","uptake")),
 "G3":("AUTHORITY",("authority","autorität","canonical","kanon","owner","permission","gate","credit")),
 "G4":("CONTINUITY",("reentry","identity","identität","epoch","persist","state","zustand","restart")),
 "G5":("FALSIFIER",("falsch","counter","gegenbeispiel","falsif","mutation","ablation","blind","latent")),
 "G6":("HYPERPOSITION",("alternative","hypoth","unknown","unbekannt","konflikt","world","weltmodell","hyperposition")),
 "G7":("EFFECT_SAFETY",("effect","wirkung","write","mutation","safety","sicher","restart","delete","migration")),
 "G8":("RESOURCE",("kosten","quota","token","latency","latenz","cpu","ram","budget","provider")),
 "G9":("INTEGRATION",("grid","j-space","gwt","hcu","cortex","memory","bridge","integration","frankenstein")),
 "G10":("HYPERMIRROR",("mirror","hypermirror","selbst","self","meta","widerspruch","mismatch","reflection")),
}
TOK=re.compile(r"[\wäöüÄÖÜß.-]+",re.UNICODE)
CITE=re.compile(r"(?:(?:file)?cite|\b[0-9a-f]{7,40}\b|\breceipt\b|\bcommit\b)",re.I)
UNC=re.compile(r"\b(?:unknown|unbekannt|unklar|nicht belegt|nicht bewiesen|wahrscheinlich|vermutlich|kann|dürfte)\b",re.I)
ASS=re.compile(r"\b(?:ist|sind|beweist|zeigt|definitiv|sicher|always|never|immer|nie)\b",re.I)

def ts(): return time.time()
def sha(s): return hashlib.sha256(s.encode("utf-8",errors="replace")).hexdigest()
def tokens(s): return [x.lower() for x in TOK.findall(s or "")]
def bounded_tanh(x): return math.tanh(max(-20.0,min(20.0,x)))

def dbopen(path:Path):
 c=sqlite3.connect(path); c.row_factory=sqlite3.Row
 c.execute("PRAGMA journal_mode=WAL"); c.execute("PRAGMA foreign_keys=ON")
 c.executescript("""
 CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS cell_state(cell_id TEXT PRIMARY KEY,state REAL NOT NULL DEFAULT 0,wins INTEGER NOT NULL DEFAULT 0,updated_at REAL NOT NULL);
 CREATE TABLE IF NOT EXISTS turn(turn_id TEXT PRIMARY KEY,ts REAL NOT NULL,prompt_hash TEXT NOT NULL,prompt TEXT NOT NULL,previous_turn_id TEXT,winner TEXT,broadcast_id TEXT,status TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS competition(turn_id TEXT NOT NULL,cell_id TEXT NOT NULL,role TEXT NOT NULL,signal REAL NOT NULL,state_before REAL NOT NULL,score REAL NOT NULL,rank INTEGER NOT NULL,selected INTEGER NOT NULL,state_after REAL,PRIMARY KEY(turn_id,cell_id));
 CREATE TABLE IF NOT EXISTS mirror(turn_id TEXT PRIMARY KEY,pre_json TEXT NOT NULL,post_json TEXT,mismatch REAL,uptake REAL,closed_at REAL);
 CREATE TABLE IF NOT EXISTS receipt(receipt_id TEXT PRIMARY KEY,turn_id TEXT NOT NULL,kind TEXT NOT NULL,payload_json TEXT NOT NULL,ts REAL NOT NULL);
 """)
 c.execute("INSERT OR IGNORE INTO meta(k,v) VALUES('schema_version',?)",(SCHEMA,))
 for cid in CELLS: c.execute("INSERT OR IGNORE INTO cell_state VALUES(?,?,0,?)",(cid,0.0,ts()))
 c.commit(); return c

def signal(prompt,cid):
 tt=tokens(prompt); joined=" ".join(tt); keys=CELLS[cid][1]
 if not tt:return 0.0
 hits=sum(1 for k in keys if k in joined)
 return round(min(1.0,0.15+0.72*(hits/max(1,len(keys)))+(0.12 if "?" in prompt else 0)+min(0.18,len(tt)/800.0)),6)

def guide(cid):
 return {
  "G1":"Bind claims to fresh executable/file/host evidence; missing evidence stays UNKNOWN.",
  "G2":"Separate correlation from causal uptake/reentry and identify a discriminator.",
  "G3":"Separate candidate, truth authority, effect authority and promotion credit.",
  "G4":"Check identity/state/reentry lineage and restart boundaries.",
  "G5":"Search for the cheapest counterexample, mutation or alternative explanation.",
  "G6":"Preserve unresolved alternatives; majority/consensus cannot mint truth.",
  "G7":"Require deterministic authorization/readback before effects.",
  "G8":"Check quota, cost, latency and bounded execution.",
  "G9":"Trace the real end-to-end seam, not isolated component readiness.",
  "G10":"Compare intended control with observable output; flag self-model mismatch.",
 }[cid]

def latest(c):
 r=c.execute("SELECT turn_id FROM turn ORDER BY ts DESC LIMIT 1").fetchone(); return r[0] if r else None

def pre(c,prompt,ablate=frozenset()):
 tid="fg-"+str(uuid.uuid4()); prev=latest(c); rows=[]
 for cid,(role,_) in CELLS.items():
  old=float(c.execute("SELECT state FROM cell_state WHERE cell_id=?",(cid,)).fetchone()[0])
  sig=0.0 if cid in ablate else signal(prompt,cid); score=sig+0.35*bounded_tanh(old)
  rows.append(dict(cell_id=cid,role=role,signal=sig,state_before=old,score=score))
 rows.sort(key=lambda x:(-round(x["score"],9),x["cell_id"]))
 best=rows[0]["score"]; ties=[r for r in rows if abs(r["score"]-best)<1e-12]; winner=None if len(ties)>1 else rows[0]["cell_id"]
 bid="b-"+str(uuid.uuid4()) if winner else None
 for i,r in enumerate(rows,1): r.update(rank=i,selected=int(r["cell_id"]==winner))
 hp=[{"cell_id":r["cell_id"],"role":r["role"],"score":round(r["score"],6)} for r in rows[:3]]
 mirror={"schema":"HYPERMIRROR/v1","prompt_hash":sha(prompt),"previous_turn_id":prev,"expected_control":CELLS[winner][0] if winner else "AMBIGUOUS","alternatives":hp,"epistemic_rule":"GRID_SIGNAL_NE_CANONICAL_TRUTH"}
 c.execute("BEGIN IMMEDIATE")
 c.execute("INSERT INTO turn VALUES(?,?,?,?,?,?,?,?)",(tid,ts(),sha(prompt),prompt,prev,winner,bid,"AMBIGUOUS" if not winner else "BROADCAST"))
 for r in rows:c.execute("INSERT INTO competition(turn_id,cell_id,role,signal,state_before,score,rank,selected) VALUES(?,?,?,?,?,?,?,?)",(tid,r["cell_id"],r["role"],r["signal"],r["state_before"],r["score"],r["rank"],r["selected"]))
 c.execute("INSERT INTO mirror(turn_id,pre_json) VALUES(?,?)",(tid,json.dumps(mirror,ensure_ascii=False,sort_keys=True)))
 rec={"schema":"FRANKGRID10_PRE_RECEIPT/v1","turn_id":tid,"broadcast_id":bid,"winner":winner,"ambiguous":not bool(winner),"ablate":sorted(ablate),"prompt_sha256":sha(prompt)}
 c.execute("INSERT INTO receipt VALUES(?,?,?,?,?)",("r-"+str(uuid.uuid4()),tid,"PRE",json.dumps(rec,ensure_ascii=False,sort_keys=True),ts())); c.commit()
 return {"schema":SCHEMA,"turn_id":tid,"previous_turn_id":prev,"winner":winner,"winner_role":CELLS[winner][0] if winner else None,"broadcast_id":bid,"ambiguous":not bool(winner),"guidance":guide(winner) if winner else "Fail closed: exact competition tie.","hyperposition":hp,"hypermirror_pre":mirror,"competition":rows}

def post(c,tid,response):
 tr=c.execute("SELECT * FROM turn WHERE turn_id=?",(tid,)).fetchone()
 if not tr: raise SystemExit("unknown turn_id "+tid)
 existing=c.execute("SELECT post_json FROM mirror WHERE turn_id=?",(tid,)).fetchone()[0]
 if existing:return json.loads(existing)
 winner=tr["winner"]; role=CELLS[winner][0] if winner else None; low=response.lower(); keys=CELLS[winner][1] if winner else ()
 hits=sum(1 for k in keys if k in low); uptake=0.0 if not winner else min(1.0,hits/max(1.0,min(3.0,len(keys))))
 citations=len(CITE.findall(response)); uncertainty=len(UNC.findall(response)); assertive=len(ASS.findall(response))
 risk=1.0 if role in {"EVIDENCE","AUTHORITY","FALSIFIER"} and assertive>=3 and citations==0 and uncertainty==0 else 0.0
 mismatch=1.0 if not winner else max(0.0,min(1.0,(1.0-uptake)*0.7+risk*0.3))
 out={"schema":"HYPERMIRROR/v1","turn_id":tid,"winner":winner,"winner_role":role,"response_sha256":sha(response),"uptake":round(uptake,6),"mismatch":round(mismatch,6),"observables":{"citation_markers":citations,"uncertainty_markers":uncertainty,"assertive_markers":assertive},"limitations":["lexical/control-plane measurement only","does not establish truth","does not inspect hidden model scheduler or chain-of-thought"]}
 c.execute("BEGIN IMMEDIATE")
 for r in c.execute("SELECT * FROM competition WHERE turn_id=? ORDER BY cell_id",(tid,)).fetchall():
  cid=r["cell_id"]; old=float(r["state_before"]); delta=(0.45*uptake-0.35*mismatch) if cid==winner else 0.04*float(r["signal"]); after=max(-3.0,min(3.0,0.88*old+delta))
  c.execute("UPDATE cell_state SET state=?,wins=wins+?,updated_at=? WHERE cell_id=?",(after,1 if cid==winner else 0,ts(),cid)); c.execute("UPDATE competition SET state_after=? WHERE turn_id=? AND cell_id=?",(after,tid,cid))
 c.execute("UPDATE mirror SET post_json=?,mismatch=?,uptake=?,closed_at=? WHERE turn_id=?",(json.dumps(out,ensure_ascii=False,sort_keys=True),mismatch,uptake,ts(),tid)); c.execute("UPDATE turn SET status='CLOSED' WHERE turn_id=?",(tid,)); c.execute("INSERT INTO receipt VALUES(?,?,?,?,?)",("r-"+str(uuid.uuid4()),tid,"POST",json.dumps(out,ensure_ascii=False,sort_keys=True),ts())); c.commit(); return out

def status(c):
 return {"schema":SCHEMA,"integrity_check":c.execute("PRAGMA integrity_check").fetchone()[0],"cells":[dict(r) for r in c.execute("SELECT cell_id,state,wins,updated_at FROM cell_state ORDER BY cell_id")],"recent_turns":[dict(r) for r in c.execute("SELECT turn_id,ts,winner,broadcast_id,status,previous_turn_id FROM turn ORDER BY ts DESC LIMIT 10")]}

def selftest(path):
 p=path.with_name("."+path.name+".selftest-"+uuid.uuid4().hex+".sqlite3")
 try:
  c=dbopen(p); a=pre(c,"Prüfe GRID10 Reentry Authority Belege HyperMirror genau."); assert a["winner"] and len(a["competition"])==10 and a["broadcast_id"]
  b=post(c,a["turn_id"],"Receipt geprüft; Authority getrennt; Unknown bleibt unbekannt; HyperMirror meldet Mismatch."); assert b["uptake"]>=0 and status(c)["integrity_check"]=="ok"
  d=pre(c,"Prüfe GRID10 Reentry Authority Belege HyperMirror genau.",{a["winner"]}); assert d["winner"]!=a["winner"] and d["previous_turn_id"]==a["turn_id"]; c.close()
  return {"selftest":"PASS","checks":6,"first_winner":a["winner"],"ablation_winner":d["winner"]}
 finally:
  for suffix in ("","-wal","-shm"):
   try:Path(str(p)+suffix).unlink()
   except FileNotFoundError:pass

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--db",default=str(DB_DEFAULT)); sp=ap.add_subparsers(dest="cmd",required=True)
 q=sp.add_parser("pre"); q.add_argument("--prompt",required=True); q.add_argument("--ablate",default="")
 q=sp.add_parser("post"); q.add_argument("--turn-id",required=True); q.add_argument("--response"); q.add_argument("--response-file")
 sp.add_parser("status"); sp.add_parser("selftest"); ns=ap.parse_args(); path=Path(ns.db)
 if ns.cmd=="selftest":out=selftest(path)
 else:
  c=dbopen(path)
  if ns.cmd=="pre":out=pre(c,ns.prompt,{x.strip() for x in ns.ablate.split(",") if x.strip()})
  elif ns.cmd=="post":
   text=Path(ns.response_file).read_text(encoding="utf-8") if ns.response_file else (ns.response if ns.response is not None else sys.stdin.read()); out=post(c,ns.turn_id,text)
  else:out=status(c)
  c.close()
 print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__":main()
