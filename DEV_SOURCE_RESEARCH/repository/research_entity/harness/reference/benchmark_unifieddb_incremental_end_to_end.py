from __future__ import annotations

import json
import math
import random
import statistics
import time

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane, PossibilitySpec
from .unifieddb_emergent_incremental import IncrementalUnifiedDBEmergentPlane

N_CLUSTERS = 60
CLUSTER_SIZE = 50
ITERATIONS = 60
K = 12
MAX_HOPS = 3


def percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return values[low]
    return values[low] * (high - pos) + values[high] * (pos - low)


def initial_ops():
    ops = []
    mutable_keys = []
    for cluster in range(N_CLUSTERS):
        refs = [f'semantic:c{cluster:03d}_n{index:02d}' for index in range(CLUSTER_SIZE)]
        for ref in refs:
            key = ref.split(':', 1)[1]
            ops.append({
                'op': 'SET',
                'domain': 'semantic',
                'key': key,
                'value': {'label': key, 'cluster': cluster},
                'epistemic': 'KNOWN',
                'status': 'CURRENT',
            })
        dependency_number = 0
        for index in range(CLUSTER_SIZE):
            for ordinal, child in enumerate((3 * index + 1, 3 * index + 2, 3 * index + 3)):
                if child >= CLUSTER_SIZE:
                    continue
                weight = (0.97, 0.91, 0.84)[ordinal]
                key = f'c{cluster:03d}_e{dependency_number:03d}'
                dependency_number += 1
                ops.append({
                    'op': 'SET',
                    'domain': 'dependency',
                    'key': key,
                    'value': {
                        'source': refs[index],
                        'target': refs[child],
                        'strength': weight,
                        'relation_type': 'POSSIBILITY',
                    },
                    'epistemic': 'KNOWN',
                    'status': 'CURRENT',
                })
                if index == 0 and ordinal == 0:
                    mutable_keys.append(key)
    return ops, mutable_keys


def stats(values):
    return {
        'min': min(values),
        'p50': percentile(values, 0.50),
        'p95': percentile(values, 0.95),
        'p99': percentile(values, 0.99),
        'max': max(values),
        'mean': statistics.mean(values),
    }


def run(plane_class, ops, mutable_keys, label):
    ledger = StateLedger()
    plane = plane_class(UnifiedDBQueryPlane(ledger))
    seeded = plane.transact(
        event_id=f'{label}-seed',
        idem=f'{label}-seed',
        base_epoch=ledger.epoch,
        event_type='E2E_SEED',
        writer='benchmark',
        ops=ops,
        provenance={'benchmark': 'EAP_INCREMENTAL_END_TO_END'},
    )
    if seeded['status'] != 'COMMITTED':
        raise AssertionError(seeded)

    cold_started = time.perf_counter_ns()
    warm = plane.compile_active_assembly(
        PossibilitySpec(
            f'{label}-warm',
            seed_refs=('semantic:c000_n00',),
            basis_epoch=ledger.epoch,
            max_items=K,
            max_hops=MAX_HOPS,
            frontier_budget=256,
            min_edge_weight=0.0,
        )
    )
    cold_us = (time.perf_counter_ns() - cold_started) / 1000.0
    if len(warm['selected']) != K:
        raise AssertionError('unexpected warm selection size')

    rng = random.Random(41)
    order = [index % len(mutable_keys) for index in range(ITERATIONS)]
    rng.shuffle(order)
    tx_us = []
    assembly_us = []
    total_us = []
    selections = []

    for iteration, cluster_index in enumerate(order):
        key = mutable_keys[cluster_index]
        strength = 0.61 + (iteration % 35) * 0.01
        seed = f'semantic:c{cluster_index:03d}_n00'
        operation = {
            'op': 'SET',
            'domain': 'dependency',
            'key': key,
            'value': {
                'source': seed,
                'target': f'semantic:c{cluster_index:03d}_n01',
                'strength': strength,
                'relation_type': 'POSSIBILITY',
            },
            'epistemic': 'KNOWN',
            'status': 'CURRENT',
        }

        total_started = time.perf_counter_ns()
        tx_started = total_started
        receipt = plane.transact(
            event_id=f'{label}-update-{iteration}',
            idem=f'{label}-update-{iteration}',
            base_epoch=ledger.epoch,
            event_type='DEPENDENCY_WEIGHT_UPDATE',
            writer='benchmark',
            ops=[operation],
            provenance={'iteration': iteration, 'cluster': cluster_index},
        )
        tx_finished = time.perf_counter_ns()
        if receipt['status'] != 'COMMITTED':
            raise AssertionError(receipt)

        assembly_started = tx_finished
        assembly = plane.compile_active_assembly(
            PossibilitySpec(
                f'{label}-assembly-{iteration}',
                seed_refs=(seed,),
                basis_epoch=ledger.epoch,
                max_items=K,
                max_hops=MAX_HOPS,
                frontier_budget=256,
                min_edge_weight=0.0,
            )
        )
        finished = time.perf_counter_ns()
        tx_us.append((tx_finished - tx_started) / 1000.0)
        assembly_us.append((finished - assembly_started) / 1000.0)
        total_us.append((finished - total_started) / 1000.0)
        selections.append(tuple(item['ref'] for item in assembly['selected']))

    result = {
        'cold_first_assembly_us': cold_us,
        'transaction_us': stats(tx_us),
        'next_assembly_us': stats(assembly_us),
        'transaction_plus_next_assembly_us': stats(total_us),
        'iterations': ITERATIONS,
        'final_epoch': ledger.epoch,
        'final_semantic_state_hash': ledger.semantic_state_hash,
        'final_trace_root_hash': ledger.trace_root_hash,
        'selections': selections,
    }
    ledger.close()
    return result


def main():
    ops, mutable_keys = initial_ops()
    base = run(UnifiedDBEmergentPlane, ops, mutable_keys, 'base')
    incremental = run(IncrementalUnifiedDBEmergentPlane, ops, mutable_keys, 'incremental')
    exact_selection_equivalence = base['selections'] == incremental['selections']
    base_total = base['transaction_plus_next_assembly_us']['p50']
    incremental_total = incremental['transaction_plus_next_assembly_us']['p50']
    base_assembly = base['next_assembly_us']['p50']
    incremental_assembly = incremental['next_assembly_us']['p50']

    output = {
        'schema_version': '1.0',
        'benchmark': 'UNIFIEDDB_LEDGER_COMMIT_PLUS_EAP_DEPENDENCY_UPDATE',
        'evidence_class': 'EXECUTED_REFERENCE_HARNESS_WHEN_RUN',
        'scope_guard': (
            'Uses the reference StateLedger and real UnifiedDBEmergentPlane classes in one '
            'process. It measures in-memory SQLite commit + preprocessor maintenance + next '
            'Assembly. It is not disk-backed production storage, concurrent load, or final '
            'Andreas target acceptance.'
        ),
        'dataset': {
            'semantic_nodes': N_CLUSTERS * CLUSTER_SIZE,
            'dependency_edges': N_CLUSTERS * (CLUSTER_SIZE - 1),
            'iterations': ITERATIONS,
            'mutated_dependency_keys': len(mutable_keys),
            'initial_ops': len(ops),
            'k': K,
            'max_hops': MAX_HOPS,
        },
        'base_eap_1_3': {key: value for key, value in base.items() if key != 'selections'},
        'incremental_eap_1_4': {key: value for key, value in incremental.items() if key != 'selections'},
        'equivalence': {
            'selected_refs_exact_all_iterations': exact_selection_equivalence,
            'final_semantic_state_hash_equal': base['final_semantic_state_hash'] == incremental['final_semantic_state_hash'],
            'final_trace_root_hash_equal': base['final_trace_root_hash'] == incremental['final_trace_root_hash'],
        },
        'delta': {
            'end_to_end_p50_speedup': base_total / incremental_total,
            'end_to_end_p50_saved_us': base_total - incremental_total,
            'next_assembly_p50_speedup': base_assembly / incremental_assembly,
            'next_assembly_p50_saved_us': base_assembly - incremental_assembly,
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
