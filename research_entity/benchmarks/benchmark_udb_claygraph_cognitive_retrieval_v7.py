from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
from pathlib import Path
import platform
import random
import sqlite3
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.cognitive_retrieval import (
    CognitiveQueryIntent,
    CognitiveRetrievalIndex,
    GraphEdge,
)


class FixtureLedger:
    def __init__(self, fixture: dict):
        self.epoch = 1
        self.semantic_state_hash = 'fixture:' + fixture['benchmark_id']
        self._rows = []
        self._events = []
        for i, r in enumerate(fixture['records']):
            domain, key = r['record_ref'].split(':', 1)
            self._rows.append({
                'domain': domain,
                'key': key,
                'value': {
                    'title': r['title'],
                    'text': r['text'],
                    'provenance_weight': r.get('provenance_weight', 1.0),
                },
                'epistemic': r['epistemic'],
                'status': r['status'],
                'domain_epoch': 1,
                'semantic_hash': f'fixture-sem-{i:04d}',
            })
            self._events.append({
                'event_id': f'fixture-event-{i:04d}',
                'writer': 'benchmark-fixture',
                'committed_at': '2026-08-10T00:00:00Z',
                'provenance': {'evidence_class': fixture['evidence_class']},
                'source': {'benchmark_id': fixture['benchmark_id']},
                'ops': [{'domain': domain, 'key': key}],
            })

    def materialized(self):
        return [dict(x) for x in self._rows]

    def export_events(self):
        return [dict(x) for x in self._events]


class FixturePlane:
    def __init__(self, ledger):
        self.ledger = ledger


def load_fixture(path: Path):
    if path.suffix == '.b64':
        return json.loads(gzip.decompress(base64.b64decode(path.read_text())).decode())
    return json.loads(path.read_text())


def build_index(fixture: dict):
    ledger = FixtureLedger(fixture)
    edges = [GraphEdge(**e) for e in fixture['edges']]
    return CognitiveRetrievalIndex(
        FixturePlane(ledger),
        graph_edges=edges,
        alias_groups=fixture['alias_groups'],
    )


def dcg_at_5(got, relevant):
    rel = set(relevant)
    return sum((1 if x in rel else 0) / math.log2(i + 2) for i, x in enumerate(got[:5]))


def score_queries(index, fixture, *, graph_enabled: bool):
    rows = []
    for q in fixture['queries']:
        intent = CognitiveQueryIntent(
            query_id=q['query_id'],
            text=q['text'],
            semantic_hints=tuple(q['semantic_hints']),
            anchor_refs=tuple(q['anchor_refs']) if graph_enabled else (),
            target_mode=q['target_mode'] if graph_enabled else 'DIRECT',
            basis_epoch=1,
            limit=5,
        )
        receipt = index.query(intent)
        got = [r.record_ref for r in receipt.results]
        relevant = set(q['relevant'])
        rank = next((i + 1 for i, x in enumerate(got) if x in relevant), None)
        ideal = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), 5)))
        rows.append({
            'query_id': q['query_id'],
            'rank': rank,
            'top5': got,
            'hit1': bool(rank == 1),
            'rr': 0.0 if rank is None else 1.0 / rank,
            'recall3': len(relevant.intersection(got[:3])) / len(relevant),
            'ndcg5': 0.0 if not ideal else dcg_at_5(got, relevant) / ideal,
            'graph_used': receipt.graph_used,
            'top_score_receipt': receipt.results[0].score_receipt if receipt.results else None,
        })
    return rows


def summarize(rows):
    return {
        'n': len(rows),
        'hit1': statistics.mean(r['hit1'] for r in rows),
        'mrr': statistics.mean(r['rr'] for r in rows),
        'recall3': statistics.mean(r['recall3'] for r in rows),
        'ndcg5': statistics.mean(r['ndcg5'] for r in rows),
        'failures': [
            {'query_id': r['query_id'], 'rank': r['rank'], 'top5': r['top5']}
            for r in rows if not r['hit1']
        ],
    }


def quantile(xs, p):
    xs = sorted(xs)
    pos = (len(xs) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    f = pos - lo
    return xs[lo] * (1 - f) + xs[hi] * f


def latency(index, fixture, *, graph_enabled: bool, repetitions: int):
    jobs = fixture['queries'] * repetitions
    random.Random(20260810).shuffle(jobs)
    samples = []
    for q in jobs:
        intent = CognitiveQueryIntent(
            query_id=q['query_id'],
            text=q['text'],
            semantic_hints=tuple(q['semantic_hints']),
            anchor_refs=tuple(q['anchor_refs']) if graph_enabled else (),
            target_mode=q['target_mode'] if graph_enabled else 'DIRECT',
            basis_epoch=1,
            limit=5,
        )
        t0 = time.perf_counter_ns()
        index.query(intent)
        samples.append((time.perf_counter_ns() - t0) / 1e6)
    return {
        'n': len(samples),
        'p50_ms': quantile(samples, 0.50),
        'p95_ms': quantile(samples, 0.95),
        'p99_ms': quantile(samples, 0.99),
        'mean_ms': statistics.mean(samples),
        'max_ms': max(samples),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        '--fixture',
        default=str(Path(__file__).with_name('udb_claygraph_cognitive_retrieval_v7_fixture.json.gz.b64')),
    )
    ap.add_argument('--repetitions', type=int, default=50)
    ap.add_argument('--noise-rows', type=int, default=0)
    ap.add_argument('--out')
    args = ap.parse_args()
    fixture = load_fixture(Path(args.fixture))
    if args.noise_rows:
        for i in range(args.noise_rows):
            fixture['records'].append({
                'record_ref': f'noise:item{i:06d}',
                'title': f'Noise item {i}',
                'text': f'synthetic unrelated benchmark payload shard {i} alpha beta gamma storage queue worker metric',
                'epistemic': 'KNOWN',
                'status': 'CURRENT',
                'provenance_weight': 0.5,
            })
    idx = build_index(fixture)

    t0 = time.perf_counter_ns()
    q0 = fixture['queries'][0]
    idx.query(CognitiveQueryIntent(
        q0['query_id'], q0['text'], tuple(q0['semantic_hints']),
        tuple(q0['anchor_refs']), q0['target_mode'], limit=5, basis_epoch=1,
    ))
    first_query_ms = (time.perf_counter_ns() - t0) / 1e6

    direct_rows = score_queries(idx, fixture, graph_enabled=False)
    graph_rows = score_queries(idx, fixture, graph_enabled=True)
    direct = summarize(direct_rows)
    graph = summarize(graph_rows)

    result = {
        'schema_version': '1.0',
        'benchmark_id': fixture['benchmark_id'],
        'evidence_class': fixture['evidence_class'],
        'claim_boundary': fixture['claim_boundary'],
        'environment': {
            'python': platform.python_version(),
            'sqlite': sqlite3.sqlite_version,
            'platform': platform.platform(),
            'machine': platform.machine(),
        },
        'corpus': {
            'records': len(fixture['records']),
            'edges': len(fixture['edges']),
            'queries': len(fixture['queries']),
            'synthetic_noise_rows': args.noise_rows,
        },
        'first_query_including_index_build_ms': first_query_ms,
        'baseline_direct_no_graph': direct,
        'candidate_typed_anchor_graph': graph,
        'delta': {
            'hit1_percentage_points': (graph['hit1'] - direct['hit1']) * 100.0,
            'mrr_percentage_points': (graph['mrr'] - direct['mrr']) * 100.0,
            'recall3_percentage_points': (graph['recall3'] - direct['recall3']) * 100.0,
            'ndcg5_percentage_points': (graph['ndcg5'] - direct['ndcg5']) * 100.0,
        },
        'latency_direct': latency(idx, fixture, graph_enabled=False, repetitions=args.repetitions),
        'latency_graph': latency(idx, fixture, graph_enabled=True, repetitions=args.repetitions),
    }
    idx.close()
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text)
    print(text)


if __name__ == '__main__':
    main()
