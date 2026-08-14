from __future__ import annotations

import math
import random
import statistics
import time

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane, PossibilitySpec
from .unifieddb_emergent_exact_topk import ExactTopKUnifiedDBEmergentPlane

N_CLUSTERS = 60
CLUSTER_SIZE = 50
K = 12
MAX_HOPS = 3


def percentile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return values[low]
    return values[low] * (high - position) + values[high] * (position - low)


def stats(values):
    return {
        'min': min(values),
        'p50': percentile(values, 0.50),
        'p95': percentile(values, 0.95),
        'p99': percentile(values, 0.99),
        'max': max(values),
        'mean': statistics.mean(values),
    }


def initial_ops():
    ops = []
    for cluster in range(N_CLUSTERS):
        refs = [f'semantic:c{cluster:03d}_n{index:02d}' for index in range(CLUSTER_SIZE)]
        for ref in refs:
            key = ref.split(':', 1)[1]
            ops.append({
                'op':'SET','domain':'semantic','key':key,
                'value':{'label':key,'cluster':cluster},
                'epistemic':'KNOWN','status':'CURRENT',
            })
        edge_number = 0
        for index in range(CLUSTER_SIZE):
            for ordinal, child in enumerate((3*index+1,3*index+2,3*index+3)):
                if child >= CLUSTER_SIZE:
                    continue
                weight = (0.97,0.91,0.84)[ordinal]
                key = f'c{cluster:03d}_e{edge_number:03d}'
                edge_number += 1
                ops.append({
                    'op':'SET','domain':'dependency','key':key,
                    'value':{
                        'source':refs[index],
                        'target':refs[child],
                        'strength':weight,
                        'relation_type':'POSSIBILITY',
                    },
                    'epistemic':'KNOWN','status':'CURRENT',
                })
    return ops


def signature(out):
    return tuple(
        (
            item['ref'],
            item['activation_score'],
            item['hop'],
            item['via_ref'],
            item['relation_type'],
            item['dependency_ref'],
            item['source_semantic_hash'],
        )
        for item in out['selected']
    )


def run_queries(plane, seeds, label):
    times = []
    expansions = []
    outputs = []
    stop_reasons = {}
    order = seeds[:]
    random.Random(53).shuffle(order)
    for seed in order:
        started = time.perf_counter_ns()
        out = plane.compile_active_assembly(PossibilitySpec(
            f'{label}-{seed}',
            seed_refs=(seed,),
            basis_epoch=plane.ledger.epoch,
            max_items=K,
            max_hops=MAX_HOPS,
            frontier_budget=512,
            min_edge_weight=0.0,
        ))
        times.append((time.perf_counter_ns() - started) / 1000.0)
        expansions.append(out['frontier_expansions'])
        outputs.append((seed, signature(out)))
        reason = out.get('frontier_stop_reason', 'BASE_FULL_EXPANSION')
        stop_reasons[reason] = stop_reasons.get(reason, 0) + 1
    return {
        'latency_us': stats(times),
        'frontier_expansions': stats(expansions),
        'stop_reasons': stop_reasons,
        'outputs': dict(outputs),
    }


def main():
    ledger = StateLedger()
    query_plane = UnifiedDBQueryPlane(ledger)
    query_plane.transact(
        event_id='exact-topk-seed',
        idem='exact-topk-seed',
        base_epoch=ledger.epoch,
        event_type='EXACT_TOPK_SEED',
        writer='benchmark',
        ops=initial_ops(),
        provenance={'benchmark':'EXACT_TOPK_FRONTIER_STOP'},
    )
    base = UnifiedDBEmergentPlane(query_plane)
    exact = ExactTopKUnifiedDBEmergentPlane(query_plane)
    seeds = [f'semantic:c{cluster:03d}_n00' for cluster in range(N_CLUSTERS)]

    base_cold_started = time.perf_counter_ns()
    base.compile_active_assembly(PossibilitySpec(
        'base-cold',seed_refs=(seeds[0],),basis_epoch=ledger.epoch,
        max_items=K,max_hops=MAX_HOPS,frontier_budget=512,min_edge_weight=0.0,
    ))
    base_cold_us = (time.perf_counter_ns() - base_cold_started) / 1000.0

    exact_cold_started = time.perf_counter_ns()
    exact.compile_active_assembly(PossibilitySpec(
        'exact-cold',seed_refs=(seeds[0],),basis_epoch=ledger.epoch,
        max_items=K,max_hops=MAX_HOPS,frontier_budget=512,min_edge_weight=0.0,
    ))
    exact_cold_us = (time.perf_counter_ns() - exact_cold_started) / 1000.0

    base_result = run_queries(base, seeds, 'base')
    exact_result = run_queries(exact, seeds, 'exact')
    equivalent = base_result['outputs'] == exact_result['outputs']
    base_latency = base_result['latency_us']['p50']
    exact_latency = exact_result['latency_us']['p50']
    base_expansions = base_result['frontier_expansions']['p50']
    exact_expansions = exact_result['frontier_expansions']['p50']

    output = {
        'schema_version':'1.0',
        'benchmark':'EAP_EXACT_TOPK_SCORE_BOUND',
        'evidence_class':'EXECUTED_REFERENCE_HARNESS_WHEN_RUN',
        'scope_guard':(
            'Tests exact selected-Assembly equivalence for EAP monotone activation ranking '
            'on a deterministic synthetic tree corpus. It does not establish answer-quality '
            'improvement or universal graph-workload speedup.'
        ),
        'dataset':{
            'semantic_nodes':N_CLUSTERS*CLUSTER_SIZE,
            'dependency_edges':N_CLUSTERS*(CLUSTER_SIZE-1),
            'queries':len(seeds),
            'k':K,
            'max_hops':MAX_HOPS,
        },
        'cold_compile_us':{
            'base':base_cold_us,
            'exact_topk':exact_cold_us,
        },
        'base':{key:value for key,value in base_result.items() if key!='outputs'},
        'exact_topk':{key:value for key,value in exact_result.items() if key!='outputs'},
        'equivalence':{
            'selected_signatures_exact_all_queries':equivalent,
        },
        'delta':{
            'p50_latency_speedup':base_latency/exact_latency,
            'p50_latency_saved_us':base_latency-exact_latency,
            'p50_frontier_expansion_reduction_fraction':1.0-(exact_expansions/base_expansions),
        },
    }
    print(__import__('json').dumps(output,indent=2,sort_keys=True))
    ledger.close()


if __name__ == '__main__':
    main()
