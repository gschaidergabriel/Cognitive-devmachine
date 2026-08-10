#!/usr/bin/env python3
from __future__ import annotations

import json
import platform
import statistics
import time

from research_entity.experiments.unifieddb_claygraph_colocation.adaptive_semantic_backend_router_v1 import (
    AdaptiveSemanticBackendRouterV1, BackendEvidence, QueryClass, QueryEnvelope,
)


def ev(name,*classes,p50=10.0,hit=1.0,recall=1.0,all5=1.0,ndcg=1.0,ann=None,prod=False):
    return BackendEvidence(name,frozenset(classes),7,True,True,'FROZEN_BENCH',p50,recall,all5,ndcg,hit,ann,prod)


def main():
    router=AdaptiveSemanticBackendRouterV1()
    evidence=[
        ev('SQL_KEYED',QueryClass.DIRECT_KEYED,p50=4),
        ev('FTS',QueryClass.LEXICAL,p50=7,recall=.95,ndcg=.95),
        ev('VECTOR_EXACT',QueryClass.VECTOR_SEMANTIC,p50=20,recall=.98,ann=None,prod=True),
        ev('VECTOR_HNSW',QueryClass.VECTOR_SEMANTIC,p50=8,recall=.98,ann=.98,prod=True),
        ev('RECURSIVE_SQL',QueryClass.RELATIONAL_MULTIHOP,QueryClass.COUNTEREVIDENCE_CLOSURE,p50=30,recall=.95,all5=.95,ndcg=.92),
        ev('CLAY_GRAPH',QueryClass.RELATIONAL_MULTIHOP,QueryClass.COUNTEREVIDENCE_CLOSURE,p50=40,recall=1,all5=1,ndcg=1),
    ]
    cases=[
        (QueryEnvelope('direct',QueryClass.DIRECT_KEYED,7,7),'SQL_KEYED'),
        (QueryEnvelope('lexical',QueryClass.LEXICAL,7,7),'FTS'),
        (QueryEnvelope('vector',QueryClass.VECTOR_SEMANTIC,7,7,requires_production_embedding=True),'VECTOR_HNSW'),
        (QueryEnvelope('multi',QueryClass.RELATIONAL_MULTIHOP,7,7),'CLAY_GRAPH'),
        (QueryEnvelope('counter',QueryClass.COUNTEREVIDENCE_CLOSURE,7,7),'CLAY_GRAPH'),
    ]
    timings=[]; correct=0; iterations=20000
    for i in range(iterations):
        q,expected=cases[i%len(cases)]
        t=time.perf_counter_ns(); d=router.route(q,evidence); timings.append((time.perf_counter_ns()-t)/1000)
        correct+=int(d.selected_backend==expected)
    timings.sort()
    blocked=router.route(QueryEnvelope('conflict',QueryClass.RELATIONAL_MULTIHOP,7,7,conflict=True),evidence)
    proxy=router.route(QueryEnvelope('prod-vector',QueryClass.VECTOR_SEMANTIC,7,7,requires_production_embedding=True),[
        ev('PROXY',QueryClass.VECTOR_SEMANTIC,p50=1,recall=1,ann=1,prod=False)])
    out={
        'schema':'clay.adaptive_semantic_backend_router.v1',
        'environment':{'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine()},
        'iterations':iterations,
        'route_accuracy':correct/iterations,
        'p50_us':statistics.median(timings),
        'p95_us':timings[int(.95*(len(timings)-1))],
        'p99_us':timings[int(.99*(len(timings)-1))],
        'conflict_fail_closed':blocked.selected_backend is None,
        'production_vector_proxy_rejected':proxy.selected_backend is None,
        'authority':'PHYSICAL_EXECUTOR_SELECTION_ONLY_NO_EFFECT_AUTHORITY',
    }
    print(json.dumps(out,indent=2,sort_keys=True))
    if out['route_accuracy']!=1.0 or not out['conflict_fail_closed'] or not out['production_vector_proxy_rejected']:
        raise SystemExit(2)

if __name__=='__main__': main()
