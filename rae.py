#!/usr/bin/env python3
"""RAE vNext unified operational runtime.

Canonical truth remains Git/raw sources/append-only ledgers. SQLite and context
manifests are rebuildable projections. This executable is the supported worker-facing
surface; legacy tools are compatibility backends, not independent policy engines.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
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
RUN_STAGES = ["INTAKE","ROUTE","DISCOVERY","FUSION_1","HYPOTHESES","FALSIFIER","PREREGISTRATION","EXPERIMENT","REPLICATION","SYNTHESIS","ADJUDICATION","PROMOTION","METHOD_MEMORY","CLOSED"]
STOP = {"the","and","oder","und","with","from","this","that","eine","einer","einem","einen","der","die","das","den","dem","für","mit","von","zur","zum","wie","was","welche","welcher","welches","into","under","über"}


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


def terms(q: str) -> list[str]:
    xs=[]
    for x in re.findall(r"[A-Za-zÄÖÜäöüß0-9][A-Za-zÄÖÜäöüß0-9_.:/+-]*", q.lower()):
        x=x.strip("._:/+-")
        if len(x)>=3 and x not in STOP and x not in xs:
            xs.append(x)
    return xs[:16]


def fts_expr(q: str) -> str:
    # Candidate generation is deliberately recall-oriented. Deterministic reranking
    # and graph/status relations restore precision after broad lexical retrieval.
    ts=terms(q)
    return " OR ".join('"'+t.replace('"','""')+'"' for t in ts)


def row_claim(r):
    return {"claim_id":r["claim_id"],"status":r["status"],"scope":r["scope"],"proposition":r["proposition"]}


def query_db(q:str, limit:int=12, statuses:list[str]|None=None, experiment:str|None=None, packet:str|None=None):
    ensure_db()
    con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    wanted=set(statuses or [])
    out={"query":q,"terms":terms(q),"claims":[],"packets":[],"chunks":[],"relations":[],"retrieval_channels":[]}
    candidates={}

    def add_claim(r, channel, bonus=0):
        d=row_claim(r)
        if wanted and d["status"] not in wanted: return
        cid=d["claim_id"]
        rec=candidates.setdefault(cid,{**d,"channels":[],"retrieval_score":0})
        if channel not in rec["channels"]: rec["channels"].append(channel)
        rec["retrieval_score"] += bonus

    expr=fts_expr(q)
    if expr:
        try:
            rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
              FROM claim_fts f JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
              WHERE claim_fts MATCH ? LIMIT ?''',(expr,max(limit*8,40))).fetchall()
            for r in rows: add_claim(r,"claim_fts",3)
            out["retrieval_channels"].append("claim_fts")
        except sqlite3.OperationalError: pass

    # Token-wise LIKE fallback catches stemming/punctuation mismatches and keeps the
    # system useful even when FTS query syntax evolves.
    ts=terms(q)
    if ts:
        clauses=[]; params=[]
        for t in ts:
            clauses.append("(lower(c.proposition) LIKE ? OR lower(c.scope) LIKE ?)")
            params.extend([f"%{t}%",f"%{t}%"])
        sql='''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
               FROM claims c LEFT JOIN claim_current_status cs USING(claim_id)
               WHERE '''+" OR ".join(clauses)+" LIMIT ?"
        params.append(max(limit*10,60))
        for r in con.execute(sql,params).fetchall():
            text=(r["scope"]+" "+r["proposition"]).lower()
            overlap=sum(1 for t in ts if t in text)
            add_claim(r,"token_like",overlap*2)
        out["retrieval_channels"].append("token_like")

    # Experiment links are first-class graph relations, not lexical hints.
    if experiment:
        rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ce.evidence_ref
          FROM claim_evidence ce JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
          WHERE ce.evidence_ref LIKE ? LIMIT ?''',(f'%{experiment}%',max(limit*8,40))).fetchall()
        for r in rows:
            add_claim(r,"experiment_relation",12)
            out["relations"].append({**row_claim(r),"relation":"evidence_ref","value":r["evidence_ref"]})
        out["retrieval_channels"].append("experiment_relation")

    if packet:
        rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ct.packet_id
          FROM claim_topic ct JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
          WHERE ct.packet_id=? LIMIT ?''',(packet,max(limit*8,40))).fetchall()
        for r in rows:
            add_claim(r,"packet_relation",10)
            out["relations"].append({**row_claim(r),"relation":"topic_packet","value":r["packet_id"]})
        out["retrieval_channels"].append("packet_relation")

    # Expand from topic packets attached to strong candidates. This is what allows a
    # query about one live experiment to recover its supporting/refuting lineage.
    seed_ids=sorted(candidates,key=lambda cid:candidates[cid]["retrieval_score"],reverse=True)[:max(4,limit//2)]
    if seed_ids:
        marks=','.join('?' for _ in seed_ids)
        packet_rows=con.execute(f'SELECT DISTINCT packet_id FROM claim_topic WHERE claim_id IN ({marks})',seed_ids).fetchall()
        packet_ids=[r["packet_id"] for r in packet_rows]
        if packet_ids:
            marks2=','.join('?' for _ in packet_ids)
            rows=con.execute(f'''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ct.packet_id
              FROM claim_topic ct JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
              WHERE ct.packet_id IN ({marks2}) LIMIT ?''',(*packet_ids,max(limit*12,80))).fetchall()
            for r in rows:
                add_claim(r,"topic_expansion",5)
                out["relations"].append({**row_claim(r),"relation":"shared_topic","value":r["packet_id"]})
            out["retrieval_channels"].append("topic_expansion")

    status_bonus={"CURRENT":5,"OPEN":4,"REFUTED":5,"NEGATIVE_RESULT":5,"SUPERSEDED":2,"CONTEXT_ONLY":0}
    for rec in candidates.values():
        rec["retrieval_score"] += status_bonus.get(rec["status"],0)
        # Reward multi-channel agreement, but do not let it erase refuted alternatives.
        rec["retrieval_score"] += max(0,len(rec["channels"])-1)*2
    out["claims"]=sorted(candidates.values(),key=lambda x:(-x["retrieval_score"],x["claim_id"]))[:limit]

    if q and ts:
        like_args=[]; clauses=[]
        for t in ts[:8]:
            clauses.append("lower(title) LIKE ? OR lower(summary) LIKE ?")
            like_args.extend([f"%{t}%",f"%{t}%"])
        try:
            out["packets"]=[dict(r) for r in con.execute('SELECT packet_id,status,title,summary FROM packets WHERE '+" OR ".join(clauses)+' LIMIT ?',(*like_args,limit)).fetchall()]
        except sqlite3.OperationalError: pass
        if expr:
            try:
                out["chunks"]=[dict(r) for r in con.execute('''SELECT s.path,f.chunk_id,substr(f.text,1,1400) excerpt
                  FROM chunk_fts f JOIN sources s USING(source_id) WHERE chunk_fts MATCH ? LIMIT ?''',(expr,limit)).fetchall()]
            except sqlite3.OperationalError: pass
    con.close(); return out


def cmd_status(_):
    c,b,problems=canonical_pair(); op=ROOT/"research_entity/continuity/OPERATIONAL_STATUS.json"
    dump({"entity_version":c.get("entity_version"),"revision":c.get("revision"),"state_hash":c.get("state_hash"),
      "scientific_status":c.get("status"),"clay_generation":c.get("clay_generation"),"bootstrap_ok":not problems,
      "problems":problems,"operational":read_json(op) if op.exists() else None,"db_exists":DB.exists(),
      "db_bytes":DB.stat().st_size if DB.exists() else 0})


def cmd_doctor(_):
    checks=[]
    for name,script,args in [("preflight","session_preflight.py",["--task","RAE doctor","--worker-id","rae-doctor"]),("schemas","validate_research_entity.py",[]),("provenance","check_provenance.py",[])]:
        rc=run_tool(script,args); checks.append({"check":name,"rc":rc})
    ensure_db(rebuild=True); ok=all(x["rc"]==0 for x in checks)
    dump({"ok":ok,"checks":checks,"db":str(DB.relative_to(ROOT))}); raise SystemExit(0 if ok else 2)


def cmd_query(args):
    bad=set(args.status or [])-STATUSES
    if bad: raise SystemExit(f"bad status: {sorted(bad)}")
    dump(query_db(args.query,args.limit,args.status,args.experiment,args.packet))


def compile_context(task:str, actor:str, max_claims:int=12, max_packets:int=5, max_chunks:int=5):
    c,b,problems=canonical_pair()
    if problems: raise SystemExit("DEGRADED_UNJOINED: "+",".join(problems))
    result=query_db(task,limit=max(max_claims*2,max_packets,max_chunks))
    claims=result["claims"][:max_claims]
    # Preserve critical epistemic shadows when retrieved: current/open/refuted should
    # coexist rather than a high-scoring current claim hiding its counterhistory.
    return {"manifest_version":"1.1","created_at":now(),"manifest_id":"ctx-"+uuid.uuid4().hex[:16],
      "actor_id":actor,"task":task,"task_sha256":hashlib.sha256(task.encode()).hexdigest(),
      "canonical":{"revision":c["revision"],"state_hash":c["state_hash"],"entity_version":c["entity_version"]},
      "budgets":{"max_claims":max_claims,"max_packets":max_packets,"max_chunks":max_chunks,"policy":"progressive disclosure; raw evidence only on demand"},
      "claims":claims,"packets":result["packets"][:max_packets],"source_chunks":result["chunks"][:max_chunks],
      "critical_negative_result_ids":b.get("critical_negative_result_ids",[]),"active_experiment_ids":b.get("active_experiment_ids",[]),
      "retrieval_channels":result.get("retrieval_channels",[]),
      "selection_method":"hybrid SQLite FTS + token overlap + experiment/topic graph expansion + deterministic status-aware rerank; sidecars optional/non-canonical"}


def cmd_boot(args):
    manifest=compile_context(args.task,args.actor,args.max_claims,args.max_packets,args.max_chunks)
    CONTEXTS.mkdir(parents=True,exist_ok=True); out=CONTEXTS/(manifest["manifest_id"]+".json")
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.out: Path(args.out).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    dump(manifest)


def run_file(run_id): return RUNS/f"{run_id}.json"


def cmd_run(args):
    RUNS.mkdir(parents=True,exist_ok=True)
    if args.run_cmd=="start":
        c,_,problems=canonical_pair()
        if problems: raise SystemExit("cannot start joined run: "+",".join(problems))
        rid=args.run_id or "run-"+uuid.uuid4().hex[:16]
        obj={"run_id":rid,"actor_id":args.actor,"capture_level":args.capture_level,"task":args.task,"created_at":now(),"updated_at":now(),
          "canonical_parent":{"revision":c["revision"],"state_hash":c["state_hash"]},"stage":"INTAKE","stage_history":[{"stage":"INTAKE","at":now()}],"status":"ACTIVE","checkpoints":[]}
        run_file(rid).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(obj)
    elif args.run_cmd=="show": dump(read_json(run_file(args.run_id)))
    elif args.run_cmd=="advance":
        p=run_file(args.run_id); obj=read_json(p); cur=obj["stage"]
        target=args.stage or RUN_STAGES[min(RUN_STAGES.index(cur)+1,len(RUN_STAGES)-1)]
        if RUN_STAGES.index(target)<RUN_STAGES.index(cur): raise SystemExit("backward transition requires explicit recovery tooling")
        obj["stage"]=target; obj["updated_at"]=now(); obj["stage_history"].append({"stage":target,"at":now(),"note":args.note})
        if target=="CLOSED": obj["status"]="CLOSED"
        p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(obj)
    elif args.run_cmd=="checkpoint":
        p=run_file(args.run_id); obj=read_json(p); cp={"at":now(),"stage":obj["stage"],"note":args.note}
        obj["checkpoints"].append(cp); obj["updated_at"]=now(); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(cp)


def cmd_compat(args):
    mapping={"validate":("validate_research_entity.py",[]),"provenance-check":("check_provenance.py",[]),"provenance-register":("register_provenance.py",args.rest),
      "materialize":("materialize_research_views.py",[]),"source-ingest":("ingest_source.py",args.rest),"packetize":("topicize_sources.py",[]),"preflight":("session_preflight.py",args.rest)}
    script,a=mapping[args.compat_cmd]; raise SystemExit(run_tool(script,a))


def cmd_benchmark(args):
    ensure_db(); cases=json.loads(Path(args.cases).read_text(encoding="utf-8")); rows=[]
    for case in cases:
        out=query_db(case["query"],limit=case.get("limit",12),statuses=case.get("status"),experiment=case.get("experiment"),packet=case.get("packet"))
        got={x["claim_id"] for x in out["claims"]}; expected=set(case.get("expected_claim_ids",[])); tp=len(got&expected)
        precision=tp/len(got) if got else (1.0 if not expected else 0.0); recall=tp/len(expected) if expected else 1.0
        rows.append({"id":case.get("id"),"precision":precision,"recall":recall,"got":sorted(got),"expected":sorted(expected)})
    summary={"created_at":now(),"cases":len(rows),"mean_precision":sum(x["precision"] for x in rows)/len(rows) if rows else 0,
      "mean_recall":sum(x["recall"] for x in rows)/len(rows) if rows else 0,"results":rows}
    dump(summary)


def parser():
    p=argparse.ArgumentParser(prog="rae",description="FRANK Global Research Entity operational runtime"); sub=p.add_subparsers(dest="cmd",required=True)
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
