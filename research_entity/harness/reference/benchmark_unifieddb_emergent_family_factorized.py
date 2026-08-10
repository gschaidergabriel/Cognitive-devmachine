from __future__ import annotations

import json
import math
import sqlite3
import statistics
import time

from .state_ledger import h
from .unifieddb_emergent_incremental import IncrementalEmergentAssemblyPreprocessor
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .unifieddb_emergent_family_factorized import (
    FamilyFactorizedEmergentAssemblyPreprocessor,
)


EPOCH = 17
K = 12


class SyntheticLedger:
    def __init__(self, rows):
        self._rows = rows
        self.epoch = EPOCH
        self.semantic_state_hash = h(
            [(r['domain'], r['key'], r['semantic_hash']) for r in rows]
        )

    def materialized(self):
        return self._rows


def row(domain, key, value):
    return {
        'domain': domain,
        'key': key,
        'value': value,
        'epistemic': 'KNOWN',
        'status': 'CURRENT',
        'domain_epoch': EPOCH,
        'semantic_hash': h((domain, key, value)),
    }


def fixture(bindings_per_family: int, families: int = 120):
    rows = [row('semantic', 'root', {'label': 'root'})]
    sql_rows = []
    for family_index in range(families):
        family_id = f'family:{family_index:03d}'
        # All bindings for family N outrank all bindings for family N+1.
        family_score = 0.999 - family_index * 0.005
        for binding_index in range(bindings_per_family):
            score = family_score - binding_index * 0.00001
            key = f'f{family_index:03d}_b{binding_index:02d}'
            ref = f'possibility:{key}'
            rows.append(
                row(
                    'possibility',
                    key,
                    {
                        'possibility_family_id': family_id,
                        'binding_id': key,
                        'synthetic_score': score,
                    },
                )
            )
            rows.append(
                row(
                    'dependency',
                    f'edge_{key}',
                    {
                        'source': 'semantic:root',
                        'target': ref,
                        'strength': score,
                        'relation_type': 'POSSIBILITY_BINDING',
                    },
                )
            )
            sql_rows.append((family_id, ref, score))
    return rows, sql_rows


def spec(tag):
    return PossibilitySpec(
        assembly_id=tag,
        seed_refs=('semantic:root',),
        allowed_domains=('possibility',),
        max_items=K,
        max_hops=1,
        frontier_budget=10000,
        min_edge_weight=0.0,
        basis_epoch=EPOCH,
    )


def family_ids(assembly):
    result = []
    for item in assembly['selected']:
        value = item.get('value')
        family = value.get('possibility_family_id') if isinstance(value, dict) else None
        if family is not None and family not in result:
            result.append(family)
    return result


def percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return values[low]
    return values[low] * (high - pos) + values[high] * (pos - low)


def latency_us(fn, repetitions=25):
    values = []
    last = None
    for index in range(repetitions):
        started = time.perf_counter_ns()
        last = fn(index)
        values.append((time.perf_counter_ns() - started) / 1000.0)
    return {
        'p50': statistics.median(values),
        'p95': percentile(values, 0.95),
        'mean': statistics.mean(values),
        'last': last,
    }


def sql_family_baseline(sql_rows):
    con = sqlite3.connect(':memory:')
    con.execute('CREATE TABLE candidate(family_id TEXT, ref TEXT, score REAL)')
    con.executemany('INSERT INTO candidate VALUES(?,?,?)', sql_rows)
    con.execute('CREATE INDEX idx_candidate_family_score ON candidate(family_id,score DESC,ref)')
    con.commit()
    sql = '''
        WITH ranked AS (
          SELECT family_id,ref,score,
                 row_number() OVER(PARTITION BY family_id ORDER BY score DESC,ref) AS rn
          FROM candidate
        )
        SELECT family_id,ref,score
        FROM ranked
        WHERE rn=1
        ORDER BY score DESC,ref
        LIMIT ?
    '''
    def run(_index):
        return list(con.execute(sql, (K,)))
    out = latency_us(run)
    families = [r[0] for r in out.pop('last')]
    con.close()
    out['family_ids'] = families
    return out


def one(bindings_per_family):
    rows, sql_rows = fixture(bindings_per_family)
    ledger = SyntheticLedger(rows)
    baseline = IncrementalEmergentAssemblyPreprocessor(ledger)
    factorized = FamilyFactorizedEmergentAssemblyPreprocessor(
        ledger, oversample_factor=4
    )
    baseline.compile_active_assembly(spec('warm-base'))
    factorized.compile_active_assembly(spec('warm-factor'))

    base_latency = latency_us(
        lambda i: baseline.compile_active_assembly(spec(f'base-{i}'))
    )
    factor_latency = latency_us(
        lambda i: factorized.compile_active_assembly(spec(f'factor-{i}'))
    )
    base_assembly = base_latency.pop('last')
    factor_assembly = factor_latency.pop('last')
    sql = sql_family_baseline(sql_rows)

    gold = [f'family:{i:03d}' for i in range(K)]
    base_families = family_ids(base_assembly)
    factor_families = family_ids(factor_assembly)
    sql_families = sql.pop('family_ids')

    def recall(got):
        return len(set(got) & set(gold)) / len(gold)

    return {
        'bindings_per_family': bindings_per_family,
        'candidate_nodes': len(sql_rows),
        'gold_families': gold,
        'baseline_eap': {
            'family_recall_at_12': recall(base_families),
            'unique_families': len(base_families),
            'top1_ref': base_assembly['selected'][0]['ref'],
            'latency_us': base_latency,
        },
        'factorized_eap_f1': {
            'family_recall_at_12': recall(factor_families),
            'unique_families': len(factor_families),
            'top1_ref': factor_assembly['selected'][0]['ref'],
            'candidate_pool_items': factor_assembly['candidate_pool_items'],
            'family_suppressed': len(factor_assembly['family_suppressed']),
            'latency_us': factor_latency,
        },
        'sqlite_family_window_baseline': {
            'family_recall_at_12': recall(sql_families),
            'unique_families': len(sql_families),
            'latency_us': sql,
            'scope': 'FLAT_PRECOMPUTED_CANDIDATE_ROWS_ONLY_NOT_EQUIVALENT_GRAPH_ASSEMBLY',
        },
        'top1_invariant': (
            base_assembly['selected'][0]['ref'] == factor_assembly['selected'][0]['ref']
        ),
    }


def main():
    results = [one(value) for value in (1, 2, 3, 4, 6, 8)]
    output = {
        'schema_version': '1.0',
        'experiment': 'EAP_FAMILY_FACTORIZATION_F1_MULTIPLICITY_SWEEP',
        'evidence_class': 'SYNTHETIC_EXECUTED_MECHANISM_TEST',
        'k': K,
        'factorized_oversample_factor': 4,
        'scope_guard': (
            'Measures explicit possibility-family coverage and hot selection latency. '
            'SQLite window baseline operates on already-flat candidate rows and is not an '
            'equivalent provenance-bearing graph Assembly. Universal DB superiority is not claimed.'
        ),
        'results': results,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
