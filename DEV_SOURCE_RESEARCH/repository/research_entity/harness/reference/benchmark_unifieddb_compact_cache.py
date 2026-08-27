from __future__ import annotations

import math
import random
import statistics
import sys
import time

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane, PossibilitySpec
from .unifieddb_emergent_compact import CompactUnifiedDBEmergentPlane

N_CLUSTERS=120
CLUSTER_SIZE=50
K=12
MAX_HOPS=3


def percentile(values,q):
    values=sorted(values); pos=(len(values)-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
    if lo==hi: return values[lo]
    return values[lo]*(hi-pos)+values[hi]*(pos-lo)


def stats(values):
    return {
        'min':min(values),'p50':percentile(values,.5),'p95':percentile(values,.95),
        'p99':percentile(values,.99),'max':max(values),'mean':statistics.mean(values),
    }


def deep_size_many(*roots):
    seen=set()
    def rec(obj):
        oid=id(obj)
        if oid in seen: return 0
        seen.add(oid)
        total=sys.getsizeof(obj)
        if isinstance(obj,dict):
            total += sum(rec(key)+rec(value) for key,value in obj.items())
        elif isinstance(obj,(list,tuple,set,frozenset)):
            total += sum(rec(value) for value in obj)
        return total
    return sum(rec(root) for root in roots)


def initial_ops():
    ops=[]
    for cluster in range(N_CLUSTERS):
        refs=[f'semantic:c{cluster:03d}_n{index:02d}' for index in range(CLUSTER_SIZE)]
        for ref in refs:
            key=ref.split(':',1)[1]
            ops.append({'op':'SET','domain':'semantic','key':key,'value':{'cluster':cluster,'label':key,'payload':'x'*32},'epistemic':'KNOWN','status':'CURRENT'})
        edge_number=0
        for index in range(CLUSTER_SIZE):
            for ordinal,child in enumerate((3*index+1,3*index+2,3*index+3)):
                if child>=CLUSTER_SIZE: continue
                weight=(0.97,0.91,0.84)[ordinal]
                key=f'c{cluster:03d}_e{edge_number:03d}'; edge_number+=1
                ops.append({'op':'SET','domain':'dependency','key':key,'value':{'source':refs[index],'target':refs[child],'strength':weight,'relation_type':'POSSIBILITY','metadata':'d'*32},'epistemic':'KNOWN','status':'CURRENT'})
    return ops


def signature(out):
    return tuple((item['ref'],item['activation_score'],item['hop'],item['via_ref'],item['dependency_ref'],item['source_semantic_hash']) for item in out['selected'])


def run(plane,seeds,label):
    cold_started=time.perf_counter_ns()
    first=plane.compile_active_assembly(PossibilitySpec(f'{label}-cold',seed_refs=(seeds[0],),basis_epoch=plane.ledger.epoch,max_items=K,max_hops=MAX_HOPS,frontier_budget=512,min_edge_weight=0.0))
    cold_us=(time.perf_counter_ns()-cold_started)/1000.0
    cache_bytes=deep_size_many(
        plane.preprocessor._rows_by_ref,
        plane.preprocessor._adj,
        plane.preprocessor._token_index,
    )
    row_count=len(plane.preprocessor._rows_by_ref)
    edge_count=plane.preprocessor._edge_count
    times=[]; outputs={}
    order=seeds[:]; random.Random(61).shuffle(order)
    for seed in order:
        started=time.perf_counter_ns()
        out=plane.compile_active_assembly(PossibilitySpec(f'{label}-{seed}',seed_refs=(seed,),basis_epoch=plane.ledger.epoch,max_items=K,max_hops=MAX_HOPS,frontier_budget=512,min_edge_weight=0.0))
        times.append((time.perf_counter_ns()-started)/1000.0)
        outputs[seed]=signature(out)
    return {
        'cold_compile_plus_first_assembly_us':cold_us,
        'hot_latency_us':stats(times),
        'cache_bytes':cache_bytes,
        'cache_mib':cache_bytes/(1024*1024),
        'rows_by_ref_count':row_count,
        'edge_count':edge_count,
        'outputs':outputs,
        'first_metadata':{
            'preprocessor_version':first.get('preprocessor_version'),
            'compact_cache_version':first.get('compact_cache_version'),
            'dependency_row_cache':first.get('dependency_row_cache','RETAINED'),
        },
    }


def main():
    ledger=StateLedger(); query_plane=UnifiedDBQueryPlane(ledger)
    receipt=query_plane.transact(event_id='compact-bench-seed',idem='compact-bench-seed',base_epoch=0,event_type='COMPACT_BENCH_SEED',writer='benchmark',ops=initial_ops(),provenance={'benchmark':'EAP_COMPACT_CACHE'})
    if receipt['status']!='COMMITTED': raise AssertionError(receipt)
    base=UnifiedDBEmergentPlane(query_plane)
    compact=CompactUnifiedDBEmergentPlane(query_plane)
    seeds=[f'semantic:c{cluster:03d}_n00' for cluster in range(N_CLUSTERS)]
    base_result=run(base,seeds,'base')
    compact_result=run(compact,seeds,'compact')
    equivalent=base_result['outputs']==compact_result['outputs']
    base_bytes=base_result['cache_bytes']; compact_bytes=compact_result['cache_bytes']
    base_p50=base_result['hot_latency_us']['p50']; compact_p50=compact_result['hot_latency_us']['p50']
    output={
        'schema_version':'1.0',
        'benchmark':'EAP_COMPACT_DEPENDENCY_ROW_CACHE',
        'evidence_class':'EXECUTED_REFERENCE_HARNESS_WHEN_RUN',
        'scope_guard':'Measures Python object graph size reachable from EAP cache structures plus cold/hot latency in the reference harness. It excludes SQLite page cache/native allocator overhead and is not process RSS.',
        'dataset':{'semantic_nodes':N_CLUSTERS*CLUSTER_SIZE,'dependency_edges':N_CLUSTERS*(CLUSTER_SIZE-1),'queries':len(seeds),'k':K,'max_hops':MAX_HOPS},
        'base':{key:value for key,value in base_result.items() if key!='outputs'},
        'compact':{key:value for key,value in compact_result.items() if key!='outputs'},
        'equivalence':{'selected_signatures_exact_all_queries':equivalent},
        'delta':{
            'cache_bytes_saved':base_bytes-compact_bytes,
            'cache_fraction_saved':1.0-(compact_bytes/base_bytes),
            'hot_p50_speedup':base_p50/compact_p50,
            'cold_speedup':base_result['cold_compile_plus_first_assembly_us']/compact_result['cold_compile_plus_first_assembly_us'],
        },
    }
    print(__import__('json').dumps(output,indent=2,sort_keys=True))
    ledger.close()


if __name__=='__main__':
    main()
