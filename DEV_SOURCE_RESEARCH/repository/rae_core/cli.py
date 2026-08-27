from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json"
BOOT = ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
ACTORS = ROOT / "research_entity/global/RESEARCH_ACTOR_REGISTRY.json"
CLAIMS = ROOT / "research_entity/ledgers/CLAIMS.jsonl"
CLAIM_STATUS = ROOT / "research_entity/ledgers/CLAIM_STATUS_EVENTS.jsonl"
EVENTS = ROOT / "research_entity/events/RESEARCH_EVENTS.jsonl"
DB = ROOT / "research_sources/sources.db"
RUNS = ROOT / "research_entity/runs"
CONTEXTS = ROOT / "research_entity/context_manifests"
TOOLS = ROOT / "tools"
RUNTIME = ROOT / ".rae_runtime"
LOCK = RUNTIME / "writer.lock"

STATUSES = {"CURRENT","OPEN","SUPERSEDED","REFUTED","NEGATIVE_RESULT","CONTEXT_ONLY"}
RUN_STAGES = ["INTAKE","ROUTE","DISCOVERY","FUSION_1","HYPOTHESES","FALSIFIER","PREREGISTRATION","EXPERIMENT","REPLICATION","SYNTHESIS","ADJUDICATION","PROMOTION","METHOD_MEMORY","CLOSED"]
STOP = {"the","and","oder","und","with","from","this","that","eine","einer","einem","einen","der","die","das","den","dem","für","mit","von","zur","zum","wie","was","welche","welcher","welches","into","under","über"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def dump(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def run_tool(script: str, args: list[str], capture: bool=False):
    p = TOOLS / script
    if not p.exists(): raise RuntimeError(f"missing compatibility tool: {p.relative_to(ROOT)}")
    cp=subprocess.run([sys.executable,str(p),*args],cwd=ROOT,text=True,capture_output=capture)
    return cp


def ensure_db(rebuild: bool=False):
    if rebuild or not DB.exists():
        cp=run_tool("build_source_db.py",["--db",str(DB)],capture=True)
        if cp.returncode: raise RuntimeError(cp.stderr or cp.stdout or "source DB build failed")


def canonical_pair():
    c,b=read_json(CANON),read_json(BOOT); problems=[]
    if c.get("entity_version")!=b.get("expected_entity_version"): problems.append("entity_version_mismatch")
    if c.get("revision")!=b.get("expected_revision"): problems.append("revision_mismatch")
    if c.get("state_hash")!=b.get("expected_state_hash"): problems.append("state_hash_mismatch")
    return c,b,problems


def actor(actor_id:str):
    reg=read_json(ACTORS)
    for x in reg.get("actors",[]):
        if x.get("actor_id")==actor_id: return x
    raise ValueError(f"unknown actor_id: {actor_id}")


def terms(q:str)->list[str]:
    xs=[]
    for x in re.findall(r"[A-Za-zÄÖÜäöüß0-9][A-Za-zÄÖÜäöüß0-9_.:/+-]*",q.lower()):
        x=x.strip("._:/+-")
        if len(x)>=3 and x not in STOP and x not in xs: xs.append(x)
    return xs[:16]


def fts_expr(q:str)->str:
    return " OR ".join('"'+t.replace('"','""')+'"' for t in terms(q))


def row_claim(r):
    return {"claim_id":r["claim_id"],"status":r["status"],"scope":r["scope"],"proposition":r["proposition"]}


def query_db(q:str,limit:int=12,statuses:list[str]|None=None,experiment:str|None=None,packet:str|None=None):
    ensure_db(); con=sqlite3.connect(DB); con.row_factory=sqlite3.Row
    wanted=set(statuses or []); out={"query":q,"terms":terms(q),"claims":[],"packets":[],"chunks":[],"relations":[],"retrieval_channels":[]}; candidates={}; relation_seeds=set()

    def add_claim(r,channel,bonus=0,overlap=0):
        d=row_claim(r)
        if wanted and d["status"] not in wanted:return
        rec=candidates.setdefault(d["claim_id"],{**d,"channels":[],"retrieval_score":0,"query_overlap":0})
        if channel not in rec["channels"]: rec["channels"].append(channel)
        rec["retrieval_score"]+=bonus; rec["query_overlap"]=max(rec["query_overlap"],overlap)

    expr=fts_expr(q); ts=terms(q)
    if expr:
        try:
            rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
              FROM claim_fts f JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
              WHERE claim_fts MATCH ? LIMIT ?''',(expr,max(limit*8,40))).fetchall()
            for r in rows:
                txt=(r["scope"]+" "+r["proposition"]).lower(); ov=sum(1 for t in ts if t in txt); add_claim(r,"claim_fts",3,ov)
            out["retrieval_channels"].append("claim_fts")
        except sqlite3.OperationalError: pass
    if ts:
        clauses=[]; params=[]
        for t in ts:
            clauses.append("(lower(c.proposition) LIKE ? OR lower(c.scope) LIKE ?)"); params.extend([f"%{t}%",f"%{t}%"])
        params.append(max(limit*10,60))
        rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition
            FROM claims c LEFT JOIN claim_current_status cs USING(claim_id) WHERE '''+" OR ".join(clauses)+" LIMIT ?",params).fetchall()
        for r in rows:
            txt=(r["scope"]+" "+r["proposition"]).lower(); ov=sum(1 for t in ts if t in txt); add_claim(r,"token_like",ov*2,ov)
        out["retrieval_channels"].append("token_like")
    if experiment:
        rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ce.evidence_ref
          FROM claim_evidence ce JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
          WHERE ce.evidence_ref LIKE ? LIMIT ?''',(f'%{experiment}%',max(limit*8,40))).fetchall()
        for r in rows:
            add_claim(r,"experiment_relation",12,max(2,len(ts))); relation_seeds.add(r["claim_id"])
            out["relations"].append({**row_claim(r),"relation":"evidence_ref","value":r["evidence_ref"]})
        out["retrieval_channels"].append("experiment_relation")
    if packet:
        rows=con.execute('''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ct.packet_id
          FROM claim_topic ct JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
          WHERE ct.packet_id=? LIMIT ?''',(packet,max(limit*8,40))).fetchall()
        for r in rows:
            add_claim(r,"packet_relation",10,max(2,len(ts))); relation_seeds.add(r["claim_id"])
            out["relations"].append({**row_claim(r),"relation":"topic_packet","value":r["packet_id"]})
        out["retrieval_channels"].append("packet_relation")

    # Explicit graph relations outrank lexical seeds. For plain queries require at least
    # two query terms when possible before expanding a whole topic packet.
    if relation_seeds:
        seed_ids=sorted(relation_seeds)
    else:
        min_overlap=2 if len(ts)>=2 else 1
        strong=[cid for cid,r in candidates.items() if r.get("query_overlap",0)>=min_overlap]
        seed_ids=sorted(strong,key=lambda cid:candidates[cid]["retrieval_score"],reverse=True)[:max(3,limit//3)]
    if seed_ids:
        marks=','.join('?' for _ in seed_ids); packet_ids=[r["packet_id"] for r in con.execute(f'SELECT DISTINCT packet_id FROM claim_topic WHERE claim_id IN ({marks})',seed_ids).fetchall()]
        if packet_ids:
            marks2=','.join('?' for _ in packet_ids)
            rows=con.execute(f'''SELECT c.claim_id,COALESCE(cs.status,c.first_status) status,c.scope,c.proposition,ct.packet_id
              FROM claim_topic ct JOIN claims c USING(claim_id) LEFT JOIN claim_current_status cs USING(claim_id)
              WHERE ct.packet_id IN ({marks2}) LIMIT ?''',(*packet_ids,max(limit*12,80))).fetchall()
            for r in rows:
                add_claim(r,"topic_expansion",5); out["relations"].append({**row_claim(r),"relation":"shared_topic","value":r["packet_id"]})
            out["retrieval_channels"].append("topic_expansion")

    status_bonus={"CURRENT":5,"OPEN":4,"REFUTED":5,"NEGATIVE_RESULT":5,"SUPERSEDED":2,"CONTEXT_ONLY":0}
    for rec in candidates.values():
        rec["retrieval_score"]+=status_bonus.get(rec["status"],0)+max(0,len(rec["channels"])-1)*2
    out["claims"]=sorted(candidates.values(),key=lambda x:(-x["retrieval_score"],-x["query_overlap"],x["claim_id"]))[:limit]

    if q and ts:
        clauses=[]; params=[]
        for t in ts[:8]: clauses.append("lower(title) LIKE ? OR lower(summary) LIKE ?"); params.extend([f"%{t}%",f"%{t}%"])
        try: out["packets"]=[dict(r) for r in con.execute('SELECT packet_id,status,title,summary FROM packets WHERE '+" OR ".join(clauses)+' LIMIT ?',(*params,limit)).fetchall()]
        except sqlite3.OperationalError: pass
        if expr:
            try: out["chunks"]=[dict(r) for r in con.execute('''SELECT s.path,f.chunk_id,substr(f.text,1,1400) excerpt FROM chunk_fts f JOIN sources s USING(source_id) WHERE chunk_fts MATCH ? LIMIT ?''',(expr,limit)).fetchall()]
            except sqlite3.OperationalError: pass
    con.close(); return out


@contextlib.contextmanager
def writer_lock(timeout:float=15.0,stale_after:float=180.0):
    RUNTIME.mkdir(exist_ok=True); start=time.monotonic()
    while True:
        try:
            fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY); os.write(fd,f"pid={os.getpid()} at={now()}\n".encode()); os.close(fd); break
        except FileExistsError:
            try:
                if time.time()-LOCK.stat().st_mtime>stale_after: LOCK.unlink(); continue
            except FileNotFoundError: continue
            if time.monotonic()-start>timeout: raise TimeoutError("RAE writer lock timeout")
            time.sleep(.1)
    try: yield
    finally:
        try: LOCK.unlink()
        except FileNotFoundError: pass


def append_jsonl(path:Path,obj:dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True)+"\n"); f.flush(); os.fsync(f.fileno())


def current_claim_status(claim_id:str):
    claim=None
    for c in read_jsonl(CLAIMS):
        if c.get("claim_id")==claim_id: claim=c
    if not claim:return None
    status=claim.get("first_status","OPEN")
    for e in read_jsonl(CLAIM_STATUS):
        if e.get("claim_id")==claim_id: status=e.get("to",status)
    return status


def validate_write_files():
    cp=run_tool("validate_research_entity.py",[],capture=True)
    if cp.returncode: raise RuntimeError((cp.stdout+"\n"+cp.stderr).strip())


def refresh_after_write():
    for script,args in [("materialize_research_views.py",[]),("build_source_db.py",["--db",str(DB)])]:
        cp=run_tool(script,args,capture=True)
        if cp.returncode: raise RuntimeError((cp.stdout+"\n"+cp.stderr).strip())


def transactional_append(changes:list[tuple[Path,dict]]):
    originals={p:p.read_bytes() if p.exists() else None for p,_ in changes}
    try:
        for p,obj in changes: append_jsonl(p,obj)
        validate_write_files(); refresh_after_write()
    except Exception:
        for p,data in originals.items():
            if data is None:
                try:p.unlink()
                except FileNotFoundError:pass
            else:p.write_bytes(data)
        # Restore derived views after rollback.
        try: refresh_after_write()
        except Exception: pass
        raise


def cmd_claim(args):
    a=actor(args.actor)
    if args.claim_cmd=="add":
        if args.status not in STATUSES: raise ValueError("invalid status")
        if current_claim_status(args.claim_id) is not None: raise ValueError("claim_id already exists")
        obj={"claim_id":args.claim_id,"scope":args.scope,"proposition":args.proposition,"first_status":args.status,
          "domains":args.domain or [],"topic_packets":args.packet or [],"evidence_refs":args.evidence or [],"origin_actor":args.actor,"created_at":now()}
        if args.experiment: obj["experiment_ref"]=args.experiment
        ev={"event_id":"CS-"+uuid.uuid4().hex,"claim_id":args.claim_id,"timestamp":now(),"from":None,"to":args.status,
          "reason":args.reason or "claim created","evidence_refs":args.evidence or [],"actor_id":args.actor}
        with writer_lock(): transactional_append([(CLAIMS,obj),(CLAIM_STATUS,ev)])
        dump({"ok":True,"actor":a["actor_id"],"claim":obj,"status_event":ev})
    elif args.claim_cmd=="transition":
        old=current_claim_status(args.claim_id)
        if old is None: raise ValueError("unknown claim_id")
        if args.to not in STATUSES: raise ValueError("invalid target status")
        if old==args.to: raise ValueError("status transition is a no-op")
        ev={"event_id":"CS-"+uuid.uuid4().hex,"claim_id":args.claim_id,"timestamp":now(),"from":old,"to":args.to,"reason":args.reason,
          "evidence_refs":args.evidence or [],"actor_id":args.actor}
        with writer_lock(): transactional_append([(CLAIM_STATUS,ev)])
        dump({"ok":True,"actor":a["actor_id"],"status_event":ev})


def cmd_event(args):
    a=actor(args.actor); obj={"event_id":"RE-"+uuid.uuid4().hex,"timestamp":now(),"session_id":args.session_id,"prompt_id":args.prompt_id,
      "capture_level":args.capture_level,"event_type":args.event_type,"domains":args.domain or [],"topic_packet_ids":args.packet or [],"source_refs":args.source or [],
      "reasoning_summary":args.summary,"status":args.status,"confidence":args.confidence,"falsifier_or_next_test":args.falsifier,"origin_actor":args.actor,
      "actor_role":a.get("role"),"provider":a.get("organization")}
    with writer_lock():
        original=EVENTS.read_bytes() if EVENTS.exists() else None
        try:
            append_jsonl(EVENTS,obj); validate_write_files(); refresh_after_write()
        except Exception:
            if original is None:
                try:EVENTS.unlink()
                except FileNotFoundError:pass
            else:EVENTS.write_bytes(original)
            raise
    dump({"ok":True,"event":obj})


def cmd_status(_):
    c,b,problems=canonical_pair(); op=ROOT/"research_entity/continuity/OPERATIONAL_STATUS.json"
    dump({"entity_version":c.get("entity_version"),"revision":c.get("revision"),"state_hash":c.get("state_hash"),"scientific_status":c.get("status"),
      "clay_generation":c.get("clay_generation"),"bootstrap_ok":not problems,"problems":problems,"operational":read_json(op) if op.exists() else None,
      "db_exists":DB.exists(),"db_bytes":DB.stat().st_size if DB.exists() else 0})


def cmd_doctor(_):
    checks=[]
    for name,script,args in [("preflight","session_preflight.py",["--task","RAE doctor","--worker-id","rae-doctor"]),("schemas","validate_research_entity.py",[]),("provenance","check_provenance.py",[])]:
        cp=run_tool(script,args,capture=True); checks.append({"check":name,"rc":cp.returncode,"output":(cp.stdout+cp.stderr)[-1200:]})
    try: ensure_db(rebuild=True); checks.append({"check":"source_db","rc":0})
    except Exception as e: checks.append({"check":"source_db","rc":1,"output":str(e)})
    ok=all(x["rc"]==0 for x in checks); dump({"ok":ok,"checks":checks,"db":str(DB.relative_to(ROOT))}); raise SystemExit(0 if ok else 2)


def cmd_query(args):
    bad=set(args.status or [])-STATUSES
    if bad: raise ValueError(f"bad status: {sorted(bad)}")
    dump(query_db(args.query,args.limit,args.status,args.experiment,args.packet))


def compile_context(task:str,actor_id:str,max_claims:int=12,max_packets:int=5,max_chunks:int=5):
    actor(actor_id); c,b,problems=canonical_pair()
    if problems: raise RuntimeError("DEGRADED_UNJOINED: "+",".join(problems))
    result=query_db(task,limit=max(max_claims*2,max_packets,max_chunks))
    return {"manifest_version":"1.2","created_at":now(),"manifest_id":"ctx-"+uuid.uuid4().hex[:16],"actor_id":actor_id,"task":task,
      "task_sha256":hashlib.sha256(task.encode()).hexdigest(),"canonical":{"revision":c["revision"],"state_hash":c["state_hash"],"entity_version":c["entity_version"]},
      "budgets":{"max_claims":max_claims,"max_packets":max_packets,"max_chunks":max_chunks,"policy":"progressive disclosure; raw evidence only on demand"},
      "claims":result["claims"][:max_claims],"packets":result["packets"][:max_packets],"source_chunks":result["chunks"][:max_chunks],
      "critical_negative_result_ids":b.get("critical_negative_result_ids",[]),"active_experiment_ids":b.get("active_experiment_ids",[]),
      "retrieval_channels":result.get("retrieval_channels",[]),"selection_method":"hybrid SQLite lexical + relation/topic expansion + status-aware rerank; sidecars optional/non-canonical"}


def cmd_boot(args):
    manifest=compile_context(args.task,args.actor,args.max_claims,args.max_packets,args.max_chunks); CONTEXTS.mkdir(parents=True,exist_ok=True)
    out=CONTEXTS/(manifest["manifest_id"]+".json"); out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.out: Path(args.out).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    dump(manifest)


def run_file(run_id):return RUNS/f"{run_id}.json"


def cmd_run(args):
    RUNS.mkdir(parents=True,exist_ok=True)
    if args.run_cmd=="start":
        actor(args.actor); c,_,problems=canonical_pair()
        if problems: raise RuntimeError("cannot start joined run: "+",".join(problems))
        rid=args.run_id or "run-"+uuid.uuid4().hex[:16]
        obj={"run_id":rid,"actor_id":args.actor,"capture_level":args.capture_level,"task":args.task,"created_at":now(),"updated_at":now(),
          "canonical_parent":{"revision":c["revision"],"state_hash":c["state_hash"]},"stage":"INTAKE","stage_history":[{"stage":"INTAKE","at":now()}],"status":"ACTIVE","checkpoints":[]}
        run_file(rid).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(obj)
    elif args.run_cmd=="show":dump(read_json(run_file(args.run_id)))
    elif args.run_cmd=="advance":
        p=run_file(args.run_id); obj=read_json(p); cur=obj["stage"]; target=args.stage or RUN_STAGES[min(RUN_STAGES.index(cur)+1,len(RUN_STAGES)-1)]
        if RUN_STAGES.index(target)<RUN_STAGES.index(cur):raise ValueError("backward transition requires explicit recovery tooling")
        obj["stage"]=target; obj["updated_at"]=now(); obj["stage_history"].append({"stage":target,"at":now(),"note":args.note}); obj["status"]="CLOSED" if target=="CLOSED" else obj["status"]
        p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(obj)
    elif args.run_cmd=="checkpoint":
        p=run_file(args.run_id); obj=read_json(p); cp={"at":now(),"stage":obj["stage"],"note":args.note}; obj["checkpoints"].append(cp); obj["updated_at"]=now()
        p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); dump(cp)


def cmd_compat(args):
    mapping={"validate":("validate_research_entity.py",[]),"provenance-check":("check_provenance.py",[]),"provenance-register":("register_provenance.py",args.rest),
      "materialize":("materialize_research_views.py",[]),"source-ingest":("ingest_source.py",args.rest),"packetize":("topicize_sources.py",[]),"preflight":("session_preflight.py",args.rest)}
    script,a=mapping[args.compat_cmd]; cp=run_tool(script,a,capture=False); raise SystemExit(cp.returncode)


def cmd_benchmark(args):
    ensure_db(); cases=json.loads(Path(args.cases).read_text(encoding="utf-8")); rows=[]
    for case in cases:
        out=query_db(case["query"],limit=case.get("limit",12),statuses=case.get("status"),experiment=case.get("experiment"),packet=case.get("packet"))
        got={x["claim_id"] for x in out["claims"]}; expected=set(case.get("expected_claim_ids",[])); tp=len(got&expected)
        precision=tp/len(got) if got else (1.0 if not expected else 0.0); recall=tp/len(expected) if expected else 1.0
        rows.append({"id":case.get("id"),"precision":precision,"recall":recall,"got":sorted(got),"expected":sorted(expected)})
    dump({"created_at":now(),"cases":len(rows),"mean_precision":sum(x["precision"] for x in rows)/len(rows) if rows else 0,"mean_recall":sum(x["recall"] for x in rows)/len(rows) if rows else 0,"results":rows})


def parser():
    p=argparse.ArgumentParser(prog="rae",description="FRANK Global Research Entity operational runtime"); sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status); sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    q=sub.add_parser("query"); q.add_argument("query",nargs="?",default=""); q.add_argument("--limit",type=int,default=12); q.add_argument("--status",action="append"); q.add_argument("--experiment"); q.add_argument("--packet"); q.set_defaults(fn=cmd_query)
    b=sub.add_parser("boot"); b.add_argument("--actor",required=True); b.add_argument("--task",required=True); b.add_argument("--max-claims",type=int,default=12); b.add_argument("--max-packets",type=int,default=5); b.add_argument("--max-chunks",type=int,default=5); b.add_argument("--out"); b.set_defaults(fn=cmd_boot)
    r=sub.add_parser("run"); rs=r.add_subparsers(dest="run_cmd",required=True)
    x=rs.add_parser("start"); x.add_argument("--actor",required=True); x.add_argument("--task",required=True); x.add_argument("--capture-level",choices=["L0","L1","L2","L3"],default="L2"); x.add_argument("--run-id"); x.set_defaults(fn=cmd_run)
    x=rs.add_parser("show"); x.add_argument("run_id"); x.set_defaults(fn=cmd_run)
    x=rs.add_parser("advance"); x.add_argument("run_id"); x.add_argument("--stage",choices=RUN_STAGES); x.add_argument("--note",default=""); x.set_defaults(fn=cmd_run)
    x=rs.add_parser("checkpoint"); x.add_argument("run_id"); x.add_argument("--note",default=""); x.set_defaults(fn=cmd_run)
    cl=sub.add_parser("claim"); cls=cl.add_subparsers(dest="claim_cmd",required=True)
    x=cls.add_parser("add"); x.add_argument("claim_id"); x.add_argument("--actor",required=True); x.add_argument("--status",default="OPEN",choices=sorted(STATUSES)); x.add_argument("--scope",required=True); x.add_argument("--proposition",required=True); x.add_argument("--domain",action="append"); x.add_argument("--packet",action="append"); x.add_argument("--evidence",action="append"); x.add_argument("--experiment"); x.add_argument("--reason",default=""); x.set_defaults(fn=cmd_claim)
    x=cls.add_parser("transition"); x.add_argument("claim_id"); x.add_argument("--actor",required=True); x.add_argument("--to",required=True,choices=sorted(STATUSES)); x.add_argument("--reason",required=True); x.add_argument("--evidence",action="append"); x.set_defaults(fn=cmd_claim)
    e=sub.add_parser("event"); e.add_argument("event_type"); e.add_argument("--actor",required=True); e.add_argument("--summary",required=True); e.add_argument("--capture-level",default="L2",choices=["L0","L1","L2","L3"]); e.add_argument("--status",default="CURRENT"); e.add_argument("--session-id"); e.add_argument("--prompt-id"); e.add_argument("--domain",action="append"); e.add_argument("--packet",action="append"); e.add_argument("--source",action="append"); e.add_argument("--confidence",default=""); e.add_argument("--falsifier",default=""); e.set_defaults(fn=cmd_event)
    bm=sub.add_parser("benchmark"); bm.add_argument("--cases",default=str(ROOT/"benchmarks/rae_vnext/cases.json")); bm.set_defaults(fn=cmd_benchmark)
    for name in ["validate","provenance-check","provenance-register","materialize","source-ingest","packetize","preflight"]:
        x=sub.add_parser(name); x.set_defaults(fn=cmd_compat,compat_cmd=name); x.add_argument("rest",nargs=argparse.REMAINDER)
    return p


def main(argv=None):
    try:
        args=parser().parse_args(argv); args.fn(args)
    except (ValueError,RuntimeError,TimeoutError) as e:
        print(json.dumps({"ok":False,"error":str(e)},ensure_ascii=False),file=sys.stderr); raise SystemExit(2)
