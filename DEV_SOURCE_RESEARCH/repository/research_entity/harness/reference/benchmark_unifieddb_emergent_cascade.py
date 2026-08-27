from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import random
import sqlite3
import statistics
import time
from pathlib import Path

from .unifieddb_emergent_cascade import FailClosedEmergentRetrievalCascade, EmergentCascadeSpec
from .unifieddb_emergent_preprocessor import EmergentAssemblyPreprocessor, PossibilitySpec

SOURCE_EPOCH = 7
RESEARCH_ENTITY = Path(__file__).resolve().parents[2]
RUNTIME = RESEARCH_ENTITY / 'runtime'


def _load_resolver_class():
    path = RUNTIME / 'semantic_entity_resolver_v12.py'
    spec = importlib.util.spec_from_file_location('clay_semantic_entity_resolver_v12', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load semantic_entity_resolver_v12.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SemanticEntityResolverV12


def _hash(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()


def _percentile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return values[low]
    return values[low] * (high - pos) + values[high] * (pos - low)


class SyntheticLedger:
    def __init__(self, rows):
        self._rows = rows
        self.epoch = SOURCE_EPOCH
        self.semantic_state_hash = _hash(
            [(row['domain'], row['key'], row['semantic_hash']) for row in rows]
        )

    def materialized(self):
        return self._rows


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
        'domain_epoch': SOURCE_EPOCH,
        'semantic_hash': semantic_hash,
    }


ENTITIES = (
    ('component_pump', 'coolant circulation pump', 'coolant impeller'),
    ('component_valve', 'pressure relief valve', 'safety bypass valve'),
    ('component_sensor', 'thermal inlet sensor', 'temperature intake probe'),
    ('component_router', 'tool routing gate', 'action dispatch gate'),
    ('component_memory', 'episodic memory index', 'experience recall catalog'),
    ('component_graph', 'semantic dependency graph', 'relationship topology map'),
    ('component_workspace', 'global workspace ignition', 'broadcast attention stage'),
    ('component_needler', 'needle routing classifier', 'tool need classifier'),
    ('component_retina', 'digital retina pipeline', 'visual percept pipeline'),
    ('component_reward', 'reward credit signal', 'outcome value signal'),
)


def _build_alias_db():
    connection = sqlite3.connect(':memory:')
    schema = (RUNTIME / 'RAE_UNIFIEDDB_V12_ENTITY_RESOLUTION.sql').read_text(encoding='utf-8')
    connection.executescript(schema)
    rows = []
    for index, (logical_id, canonical, alias) in enumerate(ENTITIES):
        rows.extend([
            (f'canonical-{index}', canonical, logical_id, 'CANONICAL', 1.0, SOURCE_EPOCH, '{}', 'CURRENT', 't'),
            (f'alias-{index}', alias, logical_id, 'DOCUMENT_DERIVED', 0.98, SOURCE_EPOCH, '{}', 'CURRENT', 't'),
        ])
    # Deliberately ambiguous evidence-bound alias; the resolver must abstain.
    rows.extend([
        ('amb-router', 'shared gate', 'component_router', 'DOCUMENT_DERIVED', 0.98, SOURCE_EPOCH, '{}', 'CURRENT', 't'),
        ('amb-needler', 'shared gate', 'component_needler', 'DOCUMENT_DERIVED', 0.98, SOURCE_EPOCH, '{}', 'CURRENT', 't'),
    ])
    connection.executemany(
        'INSERT INTO semantic_entity_aliases VALUES(?,?,?,?,?,?,?,?,?)', rows
    )
    connection.executemany(
        'INSERT INTO semantic_entity_alias_fts VALUES(?,?,?)',
        [(row[0], row[1], row[2]) for row in rows],
    )
    connection.commit()
    return connection


def _build_graph_rows():
    rows = []
    logical_to_ref = {}
    for logical_id, canonical, _alias in ENTITIES:
        root_ref = f'semantic:{logical_id}'
        context_ref = f'semantic:{logical_id}_context'
        logical_to_ref[logical_id] = root_ref
        rows.extend([
            _row('semantic', logical_id, {'label': canonical, 'logical_id': logical_id}),
            _row('semantic', logical_id + '_context', {'context_for': logical_id}),
            _row(
                'dependency',
                logical_id + '_context_edge',
                {
                    'source': root_ref,
                    'target': context_ref,
                    'strength': 1.0,
                    'relation_type': 'CONTEXT',
                },
            ),
        ])
    return rows, logical_to_ref


def _queries():
    rows = []
    for logical_id, canonical, alias in ENTITIES:
        rows.extend([
            (f'inspect the {alias} before the next cycle', logical_id),
            (f'what depends on {alias}', logical_id),
            (f'show context around {canonical}', logical_id),
        ])
    rows.extend([
        ('shared gate', None),
        ('unknown purple subsystem', None),
        ('tool', None),
    ])
    return rows


def _direct_canonical_seed(text):
    query_tokens = set(text.lower().replace('-', ' ').split())
    scored = []
    for logical_id, canonical, _alias in ENTITIES:
        canonical_tokens = set(canonical.lower().split())
        score = len(query_tokens & canonical_tokens) / max(1, len(canonical_tokens))
        if score > 0.0:
            scored.append((score, logical_id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        return None
    if len(scored) > 1 and abs(scored[0][0] - scored[1][0]) < 1e-12:
        return None
    return scored[0][1]


def _assess(name, function, queries, expected_root):
    latencies = []
    correct = 0
    false_open = 0
    known_exact_assembly = 0
    known_count = 0
    details = []
    for query, truth in queries:
        started = time.perf_counter_ns()
        got_logical, refs, mode = function(query)
        latency_ns = time.perf_counter_ns() - started
        latencies.append(latency_ns / 1000.0)
        if truth is None:
            row_correct = got_logical is None and not refs
            false_open += int(got_logical is not None or bool(refs))
        else:
            known_count += 1
            expected_refs = (
                expected_root[truth],
                expected_root[truth] + '_context',
            )
            row_correct = got_logical == truth
            known_exact_assembly += int(tuple(refs) == expected_refs)
        correct += int(row_correct)
        details.append({
            'query': query,
            'truth': truth,
            'got_logical': got_logical,
            'refs': list(refs),
            'mode': mode,
            'correct': row_correct,
        })
    return {
        'name': name,
        'decision_accuracy': correct / len(queries),
        'correct_decisions': correct,
        'queries': len(queries),
        'known_exact_assembly_rate': known_exact_assembly / max(1, known_count),
        'false_open_rate_on_abstention_cases': false_open / max(1, len(queries) - known_count),
        'latency_us': {
            'p50': _percentile(latencies, 0.50),
            'p95': _percentile(latencies, 0.95),
            'p99': _percentile(latencies, 0.99),
            'mean': statistics.mean(latencies),
            'min': min(latencies),
            'max': max(latencies),
        },
        'failures': [detail for detail in details if not detail['correct']],
    }


def main():
    Resolver = _load_resolver_class()
    alias_db = _build_alias_db()
    graph_rows, logical_to_ref = _build_graph_rows()
    ledger = SyntheticLedger(graph_rows)
    preprocessor = EmergentAssemblyPreprocessor(ledger)
    resolver = Resolver(alias_db)
    cascade = FailClosedEmergentRetrievalCascade(
        resolver=resolver,
        preprocessor=preprocessor,
        logical_to_ref=lambda logical_id: logical_to_ref.get(logical_id),
    )

    # Pay topology compilation once and expose it separately from hot query latency.
    cold_started = time.perf_counter_ns()
    preprocessor.compile_active_assembly(
        PossibilitySpec(
            'warm-topology',
            seed_refs=(logical_to_ref['component_pump'],),
            basis_epoch=SOURCE_EPOCH,
            max_items=2,
            max_hops=1,
            min_edge_weight=0.0,
        )
    )
    topology_cold_us = (time.perf_counter_ns() - cold_started) / 1000.0

    queries = _queries()
    random.Random(23).shuffle(queries)

    def direct(query):
        logical_id = _direct_canonical_seed(query)
        if logical_id is None:
            return None, (), 'DIRECT_CANONICAL_ABSTAIN'
        assembly = preprocessor.compile_active_assembly(
            PossibilitySpec(
                'direct-' + _hash(query)[:12],
                seed_refs=(logical_to_ref[logical_id],),
                basis_epoch=SOURCE_EPOCH,
                max_items=2,
                max_hops=1,
                min_edge_weight=0.0,
            )
        )
        return logical_id, tuple(item['ref'] for item in assembly['selected']), 'DIRECT_CANONICAL_TO_EAP'

    def u12_eap(query):
        out = cascade.retrieve(
            EmergentCascadeSpec(
                'u12-' + _hash(query)[:12],
                query,
                SOURCE_EPOCH,
                max_items=2,
                max_hops=1,
                min_edge_weight=0.0,
            )
        )
        if out['blocked']:
            return None, (), out['resolution_class']
        return (
            out['logical_id'],
            tuple(item['ref'] for item in out['assembly']['selected']),
            out['resolution_class'],
        )

    expected_root = logical_to_ref
    baseline = _assess('direct_canonical_lexical_plus_eap', direct, queries, expected_root)
    candidate = _assess('u12_fail_closed_resolver_plus_eap', u12_eap, queries, expected_root)

    output = {
        'schema_version': '1.0',
        'benchmark': 'U12_EAP_HELD_OUT_ALIAS_AND_ABSTENTION',
        'evidence_class': 'SYNTHETIC_EXECUTED_TEST',
        'scope_guard': (
            'Tests synthetic held-out phrasing, evidence aliases and fail-closed seed opening. '
            'It is not repo-native Frank retrieval or universal database superiority.'
        ),
        'dataset': {
            'entities': len(ENTITIES),
            'known_queries': len(ENTITIES) * 3,
            'abstention_queries': 3,
            'total_queries': len(queries),
            'source_epoch': SOURCE_EPOCH,
        },
        'topology_cold_compile_us': topology_cold_us,
        'results': [baseline, candidate],
        'candidate_delta': {
            'decision_accuracy': candidate['decision_accuracy'] - baseline['decision_accuracy'],
            'known_exact_assembly_rate': candidate['known_exact_assembly_rate'] - baseline['known_exact_assembly_rate'],
            'false_open_rate': candidate['false_open_rate_on_abstention_cases'] - baseline['false_open_rate_on_abstention_cases'],
            'p50_latency_us': candidate['latency_us']['p50'] - baseline['latency_us']['p50'],
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
