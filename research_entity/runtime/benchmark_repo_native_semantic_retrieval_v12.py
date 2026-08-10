#!/usr/bin/env python3
"""Repository-native retrieval benchmark for UnifiedDB/ClayGraph research.

Unlike the synthetic topic fixtures, this benchmark indexes the checked-out Clay repository
itself. SQLite FTS5/BM25 is the conventional baseline. The hybrid candidate adds only the
repository's explicit file-reference graph (research_entity/... links) with bounded RRF-like
activation. No expected answer text is inserted into the index.

This is still a component benchmark, not proof of universal DB superiority. It is designed to
falsify overfitting to synthetic semantic seeds and to expose graph harm under missing/shuffled
references.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sqlite3
import statistics
import time

ROOT=Path(__file__).resolve().parents[2]
TOKEN_RE=re.compile(r"[A-Za-z0-9_\-]+")
REF_RE=re.compile(r"research_entity/[A-Za-z0-9_./\-]+")
ALLOWED_EXT={'.md','.json','.clay','.sql','.py','.txt','.yml','.yaml'}
SKIP_PARTS={'.git','__pycache__'}
MAX_FILE_BYTES=1_000_000

CASES=[
  {"id":"identity-boundary","query":"Which contract says the current model is only a temporary Clay research worker and must never become Frank?","expected":"research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md","class":"COUNTEREVIDENCE"},
  {"id":"organ-baseline","query":"Before replacing a historical Frank organ, which contract requires measuring original latency accuracy reliability resources and metadata?","expected":"research_entity/global/FRANK_ORGAN_MODULE_BASELINE_BENCHMARK_CONTRACT.md","class":"DIRECT"},
  {"id":"live-web","query":"Which protocol requires refreshing current external knowledge repeatedly during long research instead of doing one web search only at the start?","expected":"research_entity/global/LIVE_KNOWLEDGE_REFRESH_PROTOCOL.md","class":"DIRECT"},
  {"id":"go-cycle","query":"Which protocol defines go as recursive research build Ubuntu VPS test measurement fusion and one bounded out-of-box experiment?","expected":"research_entity/triggers/GO_RECURSIVE_SWARM_CYCLE_PROTOCOL.md","class":"DIRECT"},
  {"id":"status-footer","query":"Which contract requires every substantive visible project response to end with one plain text status fence and nothing visible afterward?","expected":"research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md","class":"DIRECT"},
  {"id":"clay-native","query":"Where is the rule that ClayCode remains semantic authority and no independent Python Rust JSON or SQL semantic architecture may emerge?","expected":"research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md","class":"COUNTEREVIDENCE"},
  {"id":"loop-of-loops","query":"Which directive defines the recurrent observation self world memory possibility control workspace outcome causal credit learning and re-entry cycle?","expected":"research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md","class":"DIRECT"},
  {"id":"program-state","query":"Which current file determines the dynamic Clay program stage and should be read instead of hardcoding progress percentages?","expected":"research_entity/rooms/PROGRAM_STATE.json","class":"DIRECT"},
  {"id":"claygraph-schema","query":"Which runtime schema defines graph epochs graph nodes graph edges provenance and the derived latest graph projection?","expected":"research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql","class":"DIRECT"},
  {"id":"u11-generation","query":"Which UnifiedDB runtime layer stages verifies and atomically publishes coherent semantic access generations through a single current head?","expected":"research_entity/runtime/RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql","class":"DIRECT"},
  {"id":"v4-plan","query":"Which ClayGraph layer separates access-plan staging verification receipts counterevidence coverage and publication?","expected":"research_entity/runtime/RAE_CLAYGRAPH_V4_VERIFIED_ACCESS_PLANS.sql","class":"DIRECT"},
  {"id":"database-pulse","query":"Which schema makes Frank database pulse delta driven with receipts checkpoints stale generation rejection and no external effect authority?","expected":"research_entity/runtime/RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql","class":"COUNTEREVIDENCE"},
]


def norm_ref(raw:str)->str:
    return raw.rstrip('.,;:)]}\"\'')


def corpus_files():
    base=ROOT/'research_entity'
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXT: continue
        rel=p.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts): continue
        try: size=p.stat().st_size
        except OSError: continue
        if size<=0 or size>MAX_FILE_BYTES: continue
        try: text=p.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        yield rel.as_posix(),text


def build_db():
    con=sqlite3.connect(':memory:')
    con.execute("CREATE TABLE docs(path TEXT PRIMARY KEY, body TEXT NOT NULL, body_hash TEXT NOT NULL)")
    con.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(path UNINDEXED,body,tokenize='unicode61 remove_diacritics 2',prefix='2 3')")
    con.execute("CREATE TABLE refs(src TEXT NOT NULL,dst TEXT NOT NULL,PRIMARY KEY(src,dst))")
    docs={}
    for path,text in corpus_files():
        docs[path]=text
        con.execute('INSERT INTO docs VALUES(?,?,?)',(path,text,hashlib.sha256(text.encode()).hexdigest()))
        con.execute('INSERT INTO docs_fts VALUES(?,?)',(path,text))
    edges=[]
    known=set(docs)
    for src,text in docs.items():
        for raw in REF_RE.findall(text):
            dst=norm_ref(raw)
            if dst in known and dst!=src:
                edges.append((src,dst))
    con.executemany('INSERT OR IGNORE INTO refs VALUES(?,?)',edges)
    con.commit()
    return con,docs


def fts_query(text:str)->str:
    tokens=[t.lower() for t in TOKEN_RE.findall(text) if len(t)>2]
    # OR is intentionally broad: FTS5/BM25 remains a strong lexical candidate generator.
    return ' OR '.join('"'+t.replace('"','')+'"' for t in tokens[:32]) or '"__none__"'


def lexical(con,q,k=20):
    rows=con.execute("SELECT path,bm25(docs_fts,0.0,1.0) score FROM docs_fts WHERE docs_fts MATCH ? ORDER BY score,path LIMIT ?",(fts_query(q),k)).fetchall()
    return [r[0] for r in rows]


def neighbors(con,src,mode='truthful'):
    rows=[r[0] for r in con.execute('SELECT dst FROM refs WHERE src=? ORDER BY dst',(src,))]
    rows += [r[0] for r in con.execute('SELECT src FROM refs WHERE dst=? ORDER BY src',(src,))]
    if mode=='missing': return []
    if mode=='shuffled' and rows:
        all_paths=[r[0] for r in con.execute('SELECT path FROM docs ORDER BY path')]
        return [all_paths[int(hashlib.sha256((src+'|'+x).encode()).hexdigest()[:12],16)%len(all_paths)] for x in rows]
    return rows


def hybrid(con,q,k=20,mode='truthful'):
    lex=lexical(con,q,64)
    score={}
    for rank,path in enumerate(lex,1):
        score[path]=score.get(path,0.0)+1.0/(60+rank)
    structural=bool(set(t.lower() for t in TOKEN_RE.findall(q)) & {'which','where','contract','protocol','directive','schema','layer','file','defines','requires'})
    graph_gain=1.15 if structural else 0.45
    for rank,seed in enumerate(lex[:10],1):
        seed_strength=graph_gain/(60+rank)
        for n in neighbors(con,seed,mode):
            score[n]=score.get(n,0.0)+seed_strength
    # Archived/history artifacts remain searchable but should not outrank active paths merely
    # because they are referenced frequently. This is a status prior, not truth authority.
    for p in list(score):
        if '/archive/' in p or '/historical/' in p:
            score[p]*=.55
    return [p for p,_ in sorted(score.items(),key=lambda kv:(-kv[1],kv[0]))[:k]]


def metrics(rows):
    hit1=sum(1 for x in rows if x['rank']==1)/len(rows)
    recall5=sum(1 for x in rows if x['rank'] is not None and x['rank']<=5)/len(rows)
    mrr=statistics.fmean(0 if x['rank'] is None else 1/x['rank'] for x in rows)
    counter=[x for x in rows if x['class']=='COUNTEREVIDENCE']
    counter5=sum(1 for x in counter if x['rank'] is not None and x['rank']<=5)/len(counter)
    lat=sorted(x['latency_us'] for x in rows)
    return {'hit_at_1':hit1,'recall_at_5':recall5,'mrr':mrr,'counterevidence_recall_at_5':counter5,'p50_us':statistics.median(lat),'p95_us':lat[int(.95*(len(lat)-1))]}


def assess(con,retriever):
    rows=[]
    for case in CASES:
        t=time.perf_counter_ns(); got=retriever(case['query']); elapsed=(time.perf_counter_ns()-t)/1000.0
        try: rank=got.index(case['expected'])+1
        except ValueError: rank=None
        rows.append({'id':case['id'],'class':case['class'],'expected':case['expected'],'rank':rank,'top5':got[:5],'latency_us':elapsed})
    return rows,metrics(rows)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output'); a=ap.parse_args()
    con,docs=build_db()
    missing=[c['expected'] for c in CASES if c['expected'] not in docs]
    if missing:
        raise SystemExit('benchmark fixture paths missing from current repo: '+', '.join(missing))
    lex_rows,lex_m=assess(con,lambda q:lexical(con,q,20))
    hy_rows,hy_m=assess(con,lambda q:hybrid(con,q,20,'truthful'))
    miss_rows,miss_m=assess(con,lambda q:hybrid(con,q,20,'missing'))
    shuf_rows,shuf_m=assess(con,lambda q:hybrid(con,q,20,'shuffled'))
    out={
      'schema':'clay.repo_native_semantic_retrieval.v1',
      'scope':'checked-out Clay repository text corpus; 12 hand-authored paraphrase/counterevidence retrieval cases; component evidence only',
      'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
      'environment':{'python':os.sys.version,'sqlite':sqlite3.sqlite_version},
      'corpus':{'documents':len(docs),'explicit_reference_edges':con.execute('SELECT COUNT(*) FROM refs').fetchone()[0]},
      'metrics':{'sqlite_fts5_bm25':lex_m,'udb_claygraph_repo_refs':hy_m,'missing_graph_control':miss_m,'shuffled_graph_control':shuf_m},
      'cases':{'sqlite_fts5_bm25':lex_rows,'udb_claygraph_repo_refs':hy_rows,'missing_graph_control':miss_rows,'shuffled_graph_control':shuf_rows},
      'promotion_note':'No universal-superiority claim. Hybrid graph is supportable only if truthful repository references improve or preserve quality and shuffled references do not produce an unexplained gain.'
    }
    text=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True); print(text)
    if a.output: Path(a.output).write_text(text+'\n',encoding='utf-8')

if __name__=='__main__': main()
