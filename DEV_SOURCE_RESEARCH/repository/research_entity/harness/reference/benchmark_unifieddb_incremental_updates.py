from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import time

from .unifieddb_emergent_preprocessor import EmergentAssemblyPreprocessor, PossibilitySpec
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor

N_CLUSTERS = 120
CLUSTER_SIZE = 50
ITERATIONS = 120
K = 12
MAX_HOPS = 3


def _hash(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()


def _percentile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return values[low]
    return values[low] * (high - position) + values[high] * (position - low)


def _row(domain, key, value, epistemic='KNOWN', status='CURRENT'):
    semantic_hash = _hash({
        'domain': domain,
        'key': key,
        'value': value,
        'epistemic': epistemic,
        'status': status,
    })
    return {
        'domain': domain,
        'key': key,
        'value': value,
        'epistemic': epistemic,
        'status': status,
        'domain_epoch': 1,
        'semantic_hash': semantic_hash,
    }


def _dataset():
    rows = []
    mutable_dependency_keys = []
    for cluster in range(N_CLUSTERS):
        refs = [f'semantic:c{cluster:03d}_n{index:02d}' for index in range(CLUSTER_SIZE)]
        for ref in refs:
            key = ref.split(':', 1)[1]
            rows.append(_row('semantic', key, {'label': key, 'cluster': cluster}))
        dependency_number = 0
        for index in range(CLUSTER_SIZE):
            for ordinal, child in enumerate((3 * index + 1, 3 * index + 2, 3 * index + 3)):
                if child >= CLUSTER_SIZE:
                    continue
                weight = (0.97, 0.91, 0.84)[ordinal]
                key = f'c{cluster:03d}_e{dependency_number:03d}'
                dependency_number += 1
                rows.append(
                    _row(
                        'dependency',
                        key,
                        {
                            'source': refs[index],
                            'target': refs[child],
                            'strength': weight,
                            'relation_type': 'POSSIBILITY',
                        },
                    )
                )
                if index == 0 and ordinal == 0:
                    mutable_dependency_keys.append(key)
    return rows, mutable_dependency_keys


class MutableSyntheticLedger:
    def __init__(self, rows):
        self._rows = {(row['domain'], row['key']): dict(row) for row in rows}
        self.epoch = 1
        self.semantic_state_hash = _hash(('genesis', len(rows)))

    def materialized(self):
        return [
            dict(self._rows[key])
            for key in sorted(self._rows)
        ]

    def get(self, domain, key):
        row = self._rows.get((domain, key))
        if row is None:
            return None
        return {
            'value': row['value'],
            'epistemic': row['epistemic'],
            'status': row['status'],
            'domain_epoch': row['domain_epoch'],
            'semantic_hash': row['semantic_hash'],
        }

    def update_dependency(self, key, strength):
        row = self._rows[('dependency', key)]
        value = dict(row['value'])
        value['strength'] = float(strength)
        self.epoch += 1
        row['value'] = value
        row['domain_epoch'] += 1
        row['semantic_hash'] = _hash({
            'domain': 'dependency',
            'key': key,
            'value': value,
            'epistemic': row['epistemic'],
            'status': row['status'],
        })
        self.semantic_state_hash = _hash(
            (self.semantic_state_hash, self.epoch, key, row['semantic_hash'])
        )
        return {
            'op': 'SET',
            'domain': 'dependency',
            'key': key,
            'value': value,
            'epistemic': row['epistemic'],
            'status': row['status'],
        }


def _run(preprocessor_class, rows, mutable_keys):
    ledger = MutableSyntheticLedger(rows)
    preprocessor = preprocessor_class(ledger)
    cold_started = time.perf_counter_ns()
    preprocessor.compile_active_assembly(
        PossibilitySpec(
            'cold',
            seed_refs=('semantic:c000_n00',),
            basis_epoch=ledger.epoch,
            max_items=K,
            max_hops=MAX_HOPS,
            frontier_budget=256,
            min_edge_weight=0.0,
        )
    )
    cold_us = (time.perf_counter_ns() - cold_started) / 1000.0

    timings = []
    selections = []
    refresh_results = []
    rng = random.Random(37)
    order = [index % len(mutable_keys) for index in range(ITERATIONS)]
    rng.shuffle(order)

    for iteration, cluster_index in enumerate(order):
        dependency_key = mutable_keys[cluster_index]
        strength = 0.61 + (iteration % 35) * 0.01
        old_epoch = ledger.epoch
        old_hash = ledger.semantic_state_hash
        op = ledger.update_dependency(dependency_key, strength)
        seed = f'semantic:c{cluster_index:03d}_n00'
        started = time.perf_counter_ns()
        refreshed = preprocessor.refresh_after_committed_ops(
            [op], old_epoch=old_epoch, old_semantic_state_hash=old_hash
        )
        assembly = preprocessor.compile_active_assembly(
            PossibilitySpec(
                f'iter-{iteration}',
                seed_refs=(seed,),
                basis_epoch=ledger.epoch,
                max_items=K,
                max_hops=MAX_HOPS,
                frontier_budget=256,
                min_edge_weight=0.0,
            )
        )
        timings.append((time.perf_counter_ns() - started) / 1000.0)
        refresh_results.append(bool(refreshed))
        selections.append(tuple(item['ref'] for item in assembly['selected']))

    return {
        'cold_compile_us': cold_us,
        'update_plus_query_latency_us': {
            'p50': _percentile(timings, 0.50),
            'p95': _percentile(timings, 0.95),
            'p99': _percentile(timings, 0.99),
            'mean': statistics.mean(timings),
            'min': min(timings),
            'max': max(timings),
        },
        'incremental_refresh_true_count': sum(refresh_results),
        'iterations': len(timings),
        'selections': selections,
    }


def main():
    rows, mutable_keys = _dataset()
    base = _run(EmergentAssemblyPreprocessor, rows, mutable_keys)
    incremental = _run(IncrementalEmergentAssemblyPreprocessor, rows, mutable_keys)
    exact_equivalence = base['selections'] == incremental['selections']
    base_p50 = base['update_plus_query_latency_us']['p50']
    inc_p50 = incremental['update_plus_query_latency_us']['p50']
    output = {
        'schema_version': '1.0',
        'benchmark': 'EAP_DEPENDENCY_DELTA_VS_FULL_REBUILD',
        'evidence_class': 'SYNTHETIC_EXECUTED_TEST',
        'scope_guard': (
            'Measures transient topology maintenance plus next Assembly after one dependency '
            'mutation. Ledger commit cost is intentionally outside timing and must be measured '
            'separately on real UnifiedDB workloads.'
        ),
        'dataset': {
            'semantic_nodes': N_CLUSTERS * CLUSTER_SIZE,
            'dependency_edges': N_CLUSTERS * (CLUSTER_SIZE - 1),
            'iterations': ITERATIONS,
            'mutated_dependency_keys': len(mutable_keys),
            'k': K,
            'max_hops': MAX_HOPS,
        },
        'base_eap_1_3': {key: value for key, value in base.items() if key != 'selections'},
        'incremental_eap_1_4': {key: value for key, value in incremental.items() if key != 'selections'},
        'equivalence': {
            'selected_refs_exact_all_iterations': exact_equivalence,
        },
        'delta': {
            'p50_speedup': base_p50 / inc_p50,
            'p50_saved_us': base_p50 - inc_p50,
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
