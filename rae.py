#!/usr/bin/env python3
"""RAE vNext unified command-line runtime.

Canonical truth remains Git/raw source/append-only ledgers. This CLI is the single
operational entry point for workers. Existing tools remain compatibility backends and
must not grow independent policy logic.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
CANON = ROOT / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json"
BOOT = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
DB = ROOT / "research_sources/sources.db"
RUNS = ROOT / "research_entity/runs"
CONTEXTS = ROOT / "research_entity/context_manifests"
TOOLS = ROOT / "tools"

STATUSES = {"CURRENT","OPEN","SUPERSEDED","REFUTED","NEGATIVE_RESULT","CONTEXT_ONLY"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def run_tool(script: str, args: list[str]) -> int:
    p = TOOLS / script
    if not p.exists():
        raise SystemExit(f"missing compatibility tool: {p.relative_to(ROOT)}")
    return subprocess.call([sys.executable, str(p), *args], cwd=ROOT)


def ensure_db(rebuild: bool=False):
    if rebuild or not DB.exists():
        rc = run_tool("build_source_db.py", ["--db", str(DB)])
        if rc:
            raise SystemExit(rc)


def canonical_pair():
    c, b = read_json(CANON), read_json(BOOT)
    problems=[]
    if c.get("entity_version") != b.get("expected_entity_version"): problems.append("entity_version_mismatch")
    if c.get("revision") != b.get("expected_revision"): problems.append("revision_mismatch")
    if c.get("state_hash") != b.get("expected_state_hash"): problems.append("state_hash_mismatch")
    return c,b,problems


def cmd_status(_):
    c,b,problems=canonical_pair()
    op=ROOT/"research_entity/continuity/OPERATIONAL_STATUS.json"
    dump({
      "entity_version":c.get("entity_version"),"revision":c.get("revision"),
      "state_hash":c.get("state_hash"),"scientific_status":c.get("status"),
      "clay_generation":c.get("clay_generation"),"bootstrap_ok":not problems,
      "problems":problems,"operational":read_json(op) if op.exists() else None,
      "db_exists":DB.exists(),"db_bytes":DB.stat().st_size if DB.exists() else 0
    })


def cmd_doctor(_):
    checks=[]
    for name,script,args in [
      ("preflight","session_preflight.py",["--task","RAE doctor","--worker-id","rae-doctor"]),
      ("schemas","validate_research_entity.py",[]),
      ("provenance","check_provenance.py",[]),
    ]:
      rc=run_tool(script,args); checks.append({"check":name,"rc":rc})
    ensure_db(rebuild=True)
    ok=all(x["rc"]==0 for x in checks)
    dump({"ok":ok,"checks":checks,"db":str(DB.relative_to(ROOT))})
    raise SystemExit(0 if ok else 2)


def _fts_quote(q:str)->str:
    return '"'+q.replace('"','""')+'"'


def query_db(q:str, limit:int=12, statuses:list[str]|None=None, experiment:str|None=None, packet:str|None=None):
    ensure_db()
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    out={"query":q,"claims":[],"packets":[],"chunks":[],"relations":[]}
    wanted=set(statuses or [])
    # lexical candidate claims
    if q:
      try:
        rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
          FROM claim_fts f JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
          WHERE claim_fts MATCH ? LIMIT ?''',(_fts_quote(q),limit*4)).fetchall()
      except sqlite3.OperationalError: rows=[]
    else:
      rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
          FROM claims c LEFT JOIN claim_current_status cs USING(claim_id) LIMIT ?''',(limit*4,)).fetchall()
    for r in rows:
      d=dict(r)
      if wanted and d["status"] not in wanted: continue
      out["claims"].append(d)
      if len(out["claims"])>=limit: break
    # explicit relational experiment traversal via claim_evidence refs
    if experiment:
      rel=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ce.evidence_ref
        FROM claim_evidence ce JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
        WHERE ce.evidence_ref LIKE ? ORDER BY status,c.claim_id LIMIT ?''',(f'%{experiment}%',limit*4)).fetchall()
      out["relations"].extend(dict(x) for x in rel if not wanted or x["status"] in wanted)
    if packet:
      rel=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ct.packet_id
        FROM claim_topic ct JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
        WHERE ct.packet_id=? LIMIT ?''',(packet,limit*4)).fetchall()
      out["relations"].extend(dict(x) for x in rel if not wanted or x["status"] in wanted)
    if q:
      like=f'%{q}%'
      out["packets"]=[dict(r) for r in con.execute('''SELECT packet_id,status,title,summary FROM packets
        WHERE title LIKE ? OR summary LIKE ? LIMIT ?''',(like,like,limit)).fetchall()]
      try:
        out["chunks"]=[dict(r) for r in con.execute('''SELECT s.path,f.chunk_id,substr(f.text,1,1400) excerpt
          FROM chunk_fts f JOIN sources s USING(source_id) WHERE chunk_fts MATCH ? LIMIT ?''',(_fts_quote(q),limit)).fetchall()]
      except sqlite3.OperationalError: pass
    con.close(); return out


def cmd_query(args):
    bad=set(args.status or [])-STATUSES
    if bad: raise SystemExit(f"bad status: {sorted(bad)}")
    dump(query_db(args.query,args.limit,args.status,args.experiment,args.packet))


def _score_claim(c, task_words):
    text=(c.get("scope","")+" "+c.get("proposition","")).lower()
    lexical=sum(1 for w in task_words if len(w)>3 and w in text)
    status_bonus={"CURRENT":4,"OPEN":3,"REFUTED":3,"NEGATIVE_RESULT":3,"SUPERSEDED":1,"CONTEXT_ONLY":0}.get(c.get("status"),0)
    return lexical*3+status_bonus


def compile_context(task:str, actor:str, max_claims:int=12, max_packets:int=5, max_chunks:int=5):
    c,b,problems=canonical_pair()
    if problems: raise SystemExit("DEGRADED_UNJOINED: "+",".join(problems))
    result=query_db(task,limit=max(max_claims,max_packets,max_chunks))
    words=set(re.findall(r'[a-zA-ZäöüÄÖÜß0-9_-]+',task.lower()))
    claims=sorted(result["claims"],key=lambda x:_score_claim(x,words),reverse=True)[:max_claims]
    # Always preserve high-value refutations among retrieved candidates.
    negatives=[x for x in result["claims"] if x.get("status") in {"REFUTED","NEGATIVE_RESULT"}]
    for n in negatives:
      if n not in claims and len(claims)<max_claims: claims.append(n)
    return {
      "manifest_version":"1.0","created_at":now(),"manifest_id":"ctx-"+uuid.uuid4().hex[:16],
      "actor_id":actor,"task":task,"task_sha256":hashlib.sha256(task.encode()).hexdigest(),
      "canonical":{"revision":c["revision"],"state_hash":c["state_hash"],"entity_version":c["entity_version"]},
      "budgets":{"max_claims":max_claims,"max_packets":max_packets,"max_chunks":max_chunks,
        "policy":"progressive disclosure; raw evidence only on demand"},
      "claims":claims,"packets":result["packets"][:max_packets],"source_chunks":result["chunks"][:max_chunks],
      "critical_negative_result_ids":b.get("critical_negative_result_ids",[]),
      "active_experiment_ids":b.get("active_experiment_ids",[]),
      "selection_method":"SQLite FTS/relations + deterministic status/lexical rerank; semantic sidecars optional and non-canonical"
    }


def cmd_boot(args):
    manifest=compile_context(args.task,args.actor,args.max_claims,args.max_packets,args.max_chunks)
    CONTEXTS.mkdir(parents=True,exist_ok=True)
    out=CONTEXTS/(manifest["manifest_id"]+".json")
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.out:
      Path(args.out).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    dump(manifest)


RUN_STAGES=["INTAKE","ROUTE","DISCOVERY","FUSION_1","HYPOTHESES","FALSIFIER","PREREGISTRATION","EXPERIMENT","REPLICATION","SYNTHESIS","ADJUDICATION","PROMOTION","METHOD_MEMORY","CLOSED"]

def run_file(run_id): return RUNS/f"{run_id}.json"

def cmd_run(args):
    RUNS.mkdir(parents=True,exist_ok=True)
    if args.run_cmd=="start":
      c,_,problems=canonical_pair()
      if problems: raise SystemExit("cannot start joined run: "+",".join(problems))
      rid=args.run_id or "run-"+uuid.uuid4().hex[:16]
      obj={"run_id":rid,"actor_id":args.actor,"capture_level":args.capture_level,"task":args.task,
        "created_at":now(),"updated_at":now(),"canonical_parent":{"revision":c["revision"],"state_hash":c["state_hash"]},
        "stage":"INTAKE","stage_history":[{"stage":"INTAKE","at":now()}],"status":"ACTIVE","checkpoints":[]}
      run_file(rid).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(obj)
    elif args.run_cmd=="show": dump(read_json(run_file(args.run_id)))
    elif args.run_cmd=="advance":
      p=run_file(args.run_id); obj=read_json(p); cur=obj["stage"]
      target=args.stage or RUN_STAGES[min(RUN_STAGES.index(cur)+1,len(RUN_STAGES)-1)]
      if target not in RUN_STAGES: raise SystemExit("invalid stage")
      if RUN_STAGES.index(target)<RUN_STAGES.index(cur): raise SystemExit("backward transition requires explicit recovery tooling")
      obj["stage"]=target; obj["updated_at"]=now(); obj["stage_history"].append({"stage":target,"at":now(),"note":args.note})
      if target=="CLOSED": obj["status"]="CLOSED"
      p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(obj)
    elif args.run_cmd=="checkpoint":
      p=run_file(args.run_id); obj=read_json(p); cp={"at":now(),"stage":obj["stage"],"note":args.note}
      obj["checkpoints"].append(cp); obj["updated_at"]=now(); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(cp)


def cmd_compat(args):
    mapping={
      "validate":("validate_research_entity.py",[]),"provenance-check":("check_provenance.py",[]),
      "provenance-register":("register_provenance.py",args.rest),"materialize":("materialize_research_views.py",[]),
      "source-ingest":("ingest_source.py",args.rest),"packetize":("topicize_sources.py",[]),
      "preflight":("session_preflight.py",args.rest)
    }
    script,a=mapping[args.compat_cmd]; raise SystemExit(run_tool(script,a))


def cmd_benchmark(args):
    ensure_db()
    cases_path=Path(args.cases)
    cases=json.loads(cases_path.read_text(encoding="utf-8"))
    rows=[]
    for case in cases:
      out=query_db(case["query"],limit=case.get("limit",12),statuses=case.get("status"),experiment=case.get("experiment"),packet=case.get("packet"))
      got={x["claim_id"] for x in out["claims"]}|{x.get("claim_id") for x in out["relations"] if x.get("claim_id")}
      expected=set(case.get("expected_claim_ids",[]))
      tp=len(got&expected); precision=tp/len(got) if got else (1.0 if not expected else 0.0); recall=tp/len(expected) if expected else 1.0
      rows.append({"id":case.get("id"),"precision":precision,"recall":recall,"got":sorted(got),"expected":sorted(expected)})
    summary={"created_at":now(),"cases":len(rows),"mean_precision":sum(x["precision"] for x in rows)/len(rows) if rows else 0,
      "mean_recall":sum(x["recall"] for x in rows)/len(rows) if rows else 0,"results":rows}
    dump(summary)


def parser():
    p=argparse.ArgumentParser(prog="rae",description="FRANK Global Research Entity operational runtime")
    sub=p.add_subparsers(dest="cmd",required=True)
    s=sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    s=sub.add_parser("doctor"); s.set_defaults(fn=cmd_doctor)
    q=sub.add_parser("query"); q.add_argument("query",nargs="?",default=""); q.add_argument("--limit",type=int,default=12); q.add_argument("--status",action="append"); q.add_argument("--experiment"); q.add_argument("--packet"); q.set_defaults(fn=cmd_query)
    b=sub.add_parser("boot"); b.add_argument("--actor",required=True); b.add_argument("--task",required=True); b.add_argument("--max-claims",type=int,default=12); b.add_argument("--max-packets",type=int,default=5); b.add_argument("--max-chunks",type=int,default=5); b.add_argument("--out"); b.set_defaults(fn=cmd_boot)
    r=sub.add_parser("run"); rs=r.add_subparsers(dest="run_cmd",required=True)
    x=rs.add_parser("start"); x.add_argument("--actor",required=True); x.add_argument("--task",required=True); x.add_argument("--capture-level",choices=["L0","L1","L2","L3"],default="L2"); x.add_argument("--run-id"); x.set_defaults(fn=cmd_run)
    x=rs.add_parser("show"); x.add_argument("run_id"); x.set_defaults(fn=cmd_run)
    x=rs.add_parser("advance"); x.add_argument("run_id"); x.add_argument("--stage",choices=RUN_STAGES); x.add_argument("--note",default=""); x.set_defaults(fn=cmd_run)
    x=rs.add_parser("checkpoint"); x.add_argument("run_id"); x.add_argument("--note",default=""); x.set_defaults(fn=cmd_run)
    bm=sub.add_parser("benchmark"); bm.add_argument("--cases",default=str(ROOT/"benchmarks/rae_vnext/cases.json")); bm.set_defaults(fn=cmd_benchmark)
    for name in ["validate","provenance-check","provenance-register","materialize","source-ingest","packetize","preflight"]:
      x=sub.add_parser(name); x.set_defaults(fn=cmd_compat,compat_cmd=name); x.add_argument("rest",nargs=argparse.REMAINDER)
    return p

if __name__=="__main__":
    a=parser().parse_args(); a.fn(a)
