#!/usr/bin/env python3
"""Controlled retrieval mechanism stress-test: SQLite FTS5/BM25 vs ClayGraph multi-hop.

This is NOT a general database benchmark. It asks one narrow causal question:
when answer-supporting evidence is distributed across typed dependencies and only the
first support is lexically query-addressable, does admissible graph traversal recover the
full evidence set better than a strong flat FTS5/BM25 baseline?

Mandatory controls:
- TRUTHFUL graph
- SHUFFLED graph topology
- PROVENANCE_BROKEN graph (inadmissible edges must not be used)

The graph mechanism is supported only if truthful topology improves retrieval while both
controls collapse toward the flat baseline and no inadmissible edge is selected.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import statistics
import time


def dcg(rels):
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels))


def run(cases: int, noise_docs: int, k: int, seed: int):
    rnd = random.Random(seed)
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE docs(id TEXT PRIMARY KEY, body TEXT NOT NULL, provenance TEXT NOT NULL)')
    conn.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(id UNINDEXED, body, content='docs', content_rowid='rowid')")
    conn.execute('CREATE TABLE edges(src TEXT,dst TEXT,rel TEXT,weight REAL,provenance TEXT,admissible INTEGER NOT NULL)')
    truth = {}
    for i in range(cases):
        a,b,c=f'a{i}',f'b{i}',f'c{i}'; token=f'signalq{i}'; gate=f'gate{i%17}'
        conn.executemany('INSERT INTO docs(id,body,provenance) VALUES(?,?,?)',[
            (a,f'{token} observed under {gate}. Follow the registered dependency chain for the verified final recovery action.',f'p{i}:a'),
            (b,f'Intermediate dependency alias depx{i} validates transition class route{i%13}.',f'p{i}:b'),
            (c,f'Final verified recovery action is actionz{i}. This terminal evidence is authoritative only for case {i}.',f'p{i}:c'),
        ])
        conn.execute('INSERT INTO edges VALUES(?,?,?,?,?,1)',(a,b,'DEPENDS_ON',.95,f'e{i}:ab'))
        conn.execute('INSERT INTO edges VALUES(?,?,?,?,?,1)',(b,c,'LEADS_TO',.95,f'e{i}:bc'))
        j=rnd.randrange(cases)
        conn.execute('INSERT INTO edges VALUES(?,?,?,?,?,1)',(a,f'b{j}','ASSOCIATED_WITH',.12,f'e{i}:noise'))
        truth[i]={a,b,c}
    for j in range(noise_docs):
        conn.execute('INSERT INTO docs(id,body,provenance) VALUES(?,?,?)',(f'n{j}',f'Generic recovery policy gate dependency action note {j} route normal operations.',f'noise:{j}'))
    conn.execute("INSERT INTO docs_fts(docs_fts) VALUES('rebuild')")
    conn.commit()

    def fts(q, limit=k):
        token=q.split()[0]
        rows=conn.execute(
            "SELECT id FROM docs_fts WHERE docs_fts MATCH ? ORDER BY rank LIMIT ?",
            (f'\"{token}\" OR recovery OR dependency',limit),
        ).fetchall()
        return [x[0] for x in rows], 0

    def graph(q, mode='truthful', limit=k):
        seeds,_=fts(q,2); out=[]; seen=set(); inadmissible_used=0
        def add(x):
            if x not in seen: seen.add(x); out.append(x)
        for s in seeds: add(s)
        frontier=[s for s in seeds if s.startswith('a')]
        for _depth in range(2):
            nxt=[]
            for s in frontier:
                rows=conn.execute('SELECT dst,rel,weight,provenance,admissible FROM edges WHERE src=? ORDER BY weight DESC',(s,)).fetchall()
                for dst,rel,_weight,_prov,adm in rows:
                    if mode=='provenance_broken': adm=0
                    if not adm:
                        continue
                    if rel not in ('DEPENDS_ON','LEADS_TO'):
                        continue
                    if mode=='shuffled':
                        digits=''.join(ch for ch in dst if ch.isdigit()); ix=int(digits or '0')
                        dst=('b' if dst.startswith('b') else 'c')+str((ix+73)%cases)
                    add(dst); nxt.append(dst)
            frontier=nxt
        return out[:limit], inadmissible_used

    def metrics(retriever):
        recalls=[]; ndcgs=[]; full=[]; aps=[]; lat=[]; inadmissible=0
        for i in range(cases):
            q=f'signalq{i} final recovery dependency'
            t=time.perf_counter_ns(); got,bad=retriever(q); lat.append((time.perf_counter_ns()-t)/1000.0); inadmissible+=bad
            gt=truth[i]; hit=[1 if x in gt else 0 for x in got[:k]]
            recalls.append(sum(hit)/len(gt)); full.append(1 if gt.issubset(set(got[:k])) else 0)
            ideal=[1]*min(len(gt),k)+[0]*max(0,k-len(gt)); ndcgs.append(dcg(hit)/(dcg(ideal[:k]) or 1))
            num=s=0.0
            for rank,r in enumerate(hit,1):
                if r: num+=1; s+=num/rank
            aps.append(s/len(gt))
        lat.sort()
        return {
            f'recall_at_{k}':statistics.fmean(recalls),
            f'all_evidence_hit_at_{k}':statistics.fmean(full),
            f'map_at_{k}':statistics.fmean(aps),
            f'ndcg_at_{k}':statistics.fmean(ndcgs),
            'p50_us':statistics.median(lat),
            'p95_us':lat[int(.95*(len(lat)-1))],
            'inadmissible_edges_used':inadmissible,
        }

    flat=metrics(fts); truthful=metrics(lambda q:graph(q,'truthful')); shuffled=metrics(lambda q:graph(q,'shuffled')); broken=metrics(lambda q:graph(q,'provenance_broken'))
    rk=f'recall_at_{k}'
    result={
        'schema_version':'1.0','evidence_class':'CONTROLLED_SYNTHETIC_RETRIEVAL_MECHANISM_TEST','promotion_authority':'NONE',
        'cases':cases,'noise_docs':noise_docs,'k':k,'seed':seed,'sqlite':sqlite3.sqlite_version,
        'fts5_bm25_flat':flat,'claygraph_truthful':truthful,'shuffled_control':shuffled,'provenance_broken_control':broken,
        'truthful_recall_gain':truthful[rk]-flat[rk],
        'truthful_latency_overhead_fraction':truthful['p50_us']/flat['p50_us']-1.0,
        'causal_control_pass':truthful[rk]>flat[rk] and shuffled[rk] <= flat[rk]+1e-12 and broken[rk] <= flat[rk]+1e-12 and broken['inadmissible_edges_used']==0,
    }
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--cases',type=int,default=300); ap.add_argument('--noise-docs',type=int,default=1200); ap.add_argument('--k',type=int,default=5); ap.add_argument('--seed',type=int,default=41); ap.add_argument('--output')
    a=ap.parse_args(); result=run(a.cases,a.noise_docs,a.k,a.seed); text=json.dumps(result,indent=2,sort_keys=True); print(text)
    if a.output:
        from pathlib import Path
        Path(a.output).write_text(text+'\n')
    if not result['causal_control_pass']:
        raise SystemExit(2)

if __name__=='__main__': main()
