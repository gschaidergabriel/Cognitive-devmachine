#!/usr/bin/env python3
"""Measure fallback-channel receipt accuracy after the U11 provenance fix."""
from __future__ import annotations
import json, sqlite3, statistics, time
from pathlib import Path
from semantic_retrieval_runtime_v11 import SemanticRetrievalFabricV11

HERE=Path(__file__).resolve().parent
U10=(HERE/'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql').read_text()
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text()
CASES=(
    ('LEXICAL_ONLY',dict(lexical_ranking=['l1','l2']),('LEXICAL_FALLBACK',('LEXICAL',))),
    ('GRAPH_ONLY',dict(graph_fallback_ranking=['g1','g2']),('GRAPH_FALLBACK',('GRAPH',))),
    ('HYBRID',dict(lexical_ranking=['a','b'],graph_fallback_ranking=['b','c']),('HYBRID_RRF_FALLBACK',('LEXICAL','GRAPH'))),
    ('MISS',dict(),('MISS',())),
)

def legacy_mode(kwargs):
    rankings=[r for r in (kwargs.get('lexical_ranking'),kwargs.get('graph_fallback_ranking')) if r]
    if len(rankings)>=2:return 'HYBRID_RRF_FALLBACK'
    if rankings:return 'LEXICAL_FALLBACK'
    return 'MISS'

def main():
    con=sqlite3.connect(':memory:'); con.executescript(U10); con.executescript(U11); f=SemanticRetrievalFabricV11(con)
    details=[]; legacy_correct=0; new_correct=0; all_lat=[]
    for name,kwargs,expected in CASES:
        expected_mode,expected_channels=expected
        legacy=legacy_mode(kwargs); legacy_ok=legacy==expected_mode; legacy_correct+=legacy_ok
        lat=[]; result=None
        for _ in range(5000):
            t=time.perf_counter_ns(); result=f.query('unseen fallback case',source_epoch=1,graph_epoch=1,**kwargs); lat.append((time.perf_counter_ns()-t)/1000)
        ok=(result.mode==expected_mode and result.fallback_channels==expected_channels); new_correct+=ok; all_lat.extend(lat); lat.sort()
        details.append({'case':name,'expected_mode':expected_mode,'legacy_mode':legacy,'legacy_correct':legacy_ok,'new_mode':result.mode,'new_channels':list(result.fallback_channels),'new_correct':ok,'p50_us':statistics.median(lat),'p95_us':lat[int(.95*(len(lat)-1))]})
    all_lat.sort()
    out={'schema':'clay.fallback_receipt_accuracy.v1','scope':'deterministic four-state fallback provenance classification; no retrieval-quality claim','cases':details,'legacy_mode_accuracy':legacy_correct/len(CASES),'new_mode_and_channel_accuracy':new_correct/len(CASES),'operations':len(all_lat),'overall_p50_us':statistics.median(all_lat),'overall_p95_us':all_lat[int(.95*(len(all_lat)-1))]}
    print(json.dumps(out,indent=2,sort_keys=True))
    if new_correct!=len(CASES):raise SystemExit(2)
if __name__=='__main__':main()
