#!/usr/bin/env python3
"""Repository-native retrieval falsifier: SQLite FTS5/BM25 vs explicit Clay repo refs."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sqlite3, statistics, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOK=re.compile(r"[A-Za-z0-9_\-]+")
REF=re.compile(r"research_entity/[A-Za-z0-9_./\-]+")
EXT={'.md','.json','.clay','.sql','.py','.txt','.yml','.yaml'}

CASES=[
("identity-boundary","Which contract says the current model is only a temporary Clay research worker and must never become Frank?","research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md","COUNTEREVIDENCE"),
("organ-baseline","Before replacing a historical Frank organ, which contract requires measuring original latency accuracy reliability resources and metadata?","research_entity/global/FRANK_ORGAN_MODULE_BASELINE_BENCHMARK_CONTRACT.md","DIRECT"),
("live-web","Which protocol requires refreshing current external knowledge repeatedly during long research instead of doing one web search only at the start?","research_entity/global/LIVE_KNOWLEDGE_REFRESH_PROTOCOL.md","DIRECT"),
("go-cycle","Which protocol defines go as recursive research build Ubuntu VPS test measurement fusion and one bounded out-of-box experiment?","research_entity/triggers/GO_RECURSIVE_SWARM_CYCLE_PROTOCOL.md","DIRECT"),
("status-footer","Which contract requires every substantive visible project response to end with one plain text status fence and nothing visible afterward?","research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md","DIRECT"),
("clay-native","Where is the rule that ClayCode remains semantic authority and no independent Python Rust JSON or SQL semantic architecture may emerge?","research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md","COUNTEREVIDENCE"),
("loop-of-loops","Which directive defines the recurrent observation self world memory possibility control workspace outcome causal credit learning and re-entry cycle?","research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md","DIRECT"),
("program-state","Which current file determines the dynamic Clay program stage and should be read instead of hardcoding progress percentages?","research_entity/rooms/PROGRAM_STATE.json","DIRECT"),
("claygraph-schema","Which runtime schema defines graph epochs graph nodes graph edges provenance and the derived latest graph projection?","research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql","DIRECT"),
("u11-generation","Which UnifiedDB runtime layer stages verifies and atomically publishes coherent semantic access generations through a single current head?","research_entity/runtime/RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql","DIRECT"),
("v4-plan","Which ClayGraph layer separates access-plan staging verification receipts counterevidence coverage and publication?","research_entity/runtime/RAE_CLAYGRAPH_V4_VERIFIED_ACCESS_PLANS.sql","DIRECT"),
("database-pulse","Which schema makes Frank database pulse delta driven with receipts checkpoints stale generation rejection and no external effect authority?","research_entity/runtime/RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql","COUNTEREVIDENCE"),
]

def files():
    for p in sorted((ROOT/'research_entity').rglob('*')):
        if not p.is_file() or p.suffix.lower() not in EXT or p.stat().st_size>1_000_000: continue
        try: text=p.read_text(encoding='utf-8')
        except (UnicodeDecodeError,OSError): continue
        yield p.relative_to(ROOT).as_posix(),text

def build():
    con=sqlite3.connect(':memory:')
    con.execute('CREATE TABLE docs(path TEXT PRIMARY KEY,body TEXT NOT NULL,body_hash TEXT NOT NULL)')
    con.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(path UNINDEXED,body,tokenize='unicode61 remove_diacritics 2',prefix='2 3')")
    con.execute('CREATE TABLE refs(src TEXT NOT NULL,dst TEXT NOT NULL,PRIMARY KEY(src,dst))')
    docs=dict(files())
    for p,t in docs.items():
        con.execute('INSERT INTO docs VALUES(?,?,?)',(p,t,hashlib.sha256(t.encode()).hexdigest())); con.execute('INSERT INTO docs_fts VALUES(?,?)',(p,t))
    known=set(docs)
    for src,text in docs.items():
        for raw in REF.findall(text):
            dst=raw.rstrip(".,;:)]}\"'")
            if dst in known and dst!=src: con.execute('INSERT OR IGNORE INTO refs VALUES(?,?)',(src,dst))
    con.commit(); return con,docs

def ftsq(q):
    ts=[t.lower() for t in TOK.findall(q) if len(t)>2]
    return ' OR '.join('"'+t+'"' for t in ts[:32]) or '"__none__"'

def lexical(con,q,k=20):
    return [r[0] for r in con.execute('SELECT path FROM docs_fts WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts,0.0,1.0),path LIMIT ?',(ftsq(q),k))]

def neighbours(con,src,mode):
    xs=[r[0] for r in con.execute('SELECT dst FROM refs WHERE src=?',(src,))]+[r[0] for r in con.execute('SELECT src FROM refs WHERE dst=?',(src,))]
    if mode=='missing': return []
    if mode=='shuffled' and xs:
        allp=[r[0] for r in con.execute('SELECT path FROM docs ORDER BY path')]
        return [allp[int(hashlib.sha256((src+'|'+x).encode()).hexdigest()[:12],16)%len(allp)] for x in xs]
    return xs

def hybrid(con,q,k=20,mode='truthful'):
    lex=lexical(con,q,64); score={p:1/(60+i) for i,p in enumerate(lex,1)}
    structural=bool({t.lower() for t in TOK.findall(q)} & {'which','where','contract','protocol','directive','schema','layer','file','defines','requires'})
    gain=1.15 if structural else .45
    for i,seed in enumerate(lex[:10],1):
        for n in neighbours(con,seed,mode): score[n]=score.get(n,0)+gain/(60+i)
    for p in list(score):
        if '/archive/' in p or '/historical/' in p: score[p]*=.55
    return [p for p,_ in sorted(score.items(),key=lambda x:(-x[1],x[0]))[:k]]

def assess(retriever):
    rows=[]
    for cid,q,expected,klass in CASES:
        t=time.perf_counter_ns(); got=retriever(q); us=(time.perf_counter_ns()-t)/1000
        rank=(got.index(expected)+1) if expected in got else None
        rows.append({'id':cid,'class':klass,'expected':expected,'rank':rank,'top5':got[:5],'latency_us':us})
    lat=sorted(x['latency_us'] for x in rows); counter=[x for x in rows if x['class']=='COUNTEREVIDENCE']
    m={'hit_at_1':sum(x['rank']==1 for x in rows)/len(rows),'recall_at_5':sum(x['rank'] is not None and x['rank']<=5 for x in rows)/len(rows),'mrr':statistics.fmean(0 if x['rank'] is None else 1/x['rank'] for x in rows),'counterevidence_recall_at_5':sum(x['rank'] is not None and x['rank']<=5 for x in counter)/len(counter),'p50_us':statistics.median(lat),'p95_us':lat[int(.95*(len(lat)-1))]}
    return rows,m

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output'); a=ap.parse_args(); con,docs=build()
    missing=[e for _,_,e,_ in CASES if e not in docs]
    if missing: raise SystemExit('missing benchmark fixtures: '+', '.join(missing))
    variants={'sqlite_fts5_bm25':lambda q:lexical(con,q),'udb_claygraph_repo_refs':lambda q:hybrid(con,q,mode='truthful'),'missing_graph_control':lambda q:hybrid(con,q,mode='missing'),'shuffled_graph_control':lambda q:hybrid(con,q,mode='shuffled')}
    cases={}; metrics={}
    for name,fn in variants.items(): cases[name],metrics[name]=assess(fn)
    out={'schema':'clay.repo_native_semantic_retrieval.v1','scope':'checked-out Clay repository; 12 paraphrase/counterevidence cases; component evidence only','timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'environment':{'python':os.sys.version,'sqlite':sqlite3.sqlite_version},'corpus':{'documents':len(docs),'explicit_reference_edges':con.execute('SELECT COUNT(*) FROM refs').fetchone()[0]},'metrics':metrics,'cases':cases,'promotion_note':'No universal-superiority claim. Truthful graph must improve or preserve quality; shuffled/missing controls expose graph-caused harm.'}
    text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).write_text(text+'\n',encoding='utf-8')
if __name__=='__main__': main()
