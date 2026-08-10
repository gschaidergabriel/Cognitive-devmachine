from __future__ import annotations

import argparse
import base64
import gzip
import json
import math
from pathlib import Path
import platform
import random
import re
import sqlite3
import statistics
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_entity.runtime.verified_claygraph_ranker import VerifiedClayGraphRanker

_STOP = set(
    ('the a an is are was were be been being of to and or in on at for from by with as it '
     'this that what which who how does do where when after before into same actually der die '
     'das ein eine einer einem einen ist sind war waren sein wird werden von zu und oder im in '
     'am für aus mit als es dies diese dieser was welcher welche welches wer wie wo wann tatsächlich').split()
)


def _norm(value):
    text = unicodedata.normalize('NFKC', str(value)).casefold().replace('v0.1', 'v0_1')
    text = re.sub(r'[_/:\-]+', ' ', text)
    text = re.sub(r'[^\w]+', ' ', text, flags=re.UNICODE)
    return ' '.join(text.split())


def _tokens(value):
    return [x for x in _norm(value).split() if len(x) > 1 and x not in _STOP and not x.isdigit()]


def _variants(term):
    out = {term}
    for suffix in ('ing', 'ed', 'es', 's', 'en', 'ern', 'ungen', 'ung', 'ieren', 'ier', 'ly'):
        if len(term) > len(suffix) + 3 and term.endswith(suffix):
            out.add(term[:-len(suffix)])
    return out


class FixtureEngine:
    """Conventional FTS baseline + verified graph callback for the frozen holdout."""

    def __init__(self, fixture):
        self.fixture = fixture
        self.records = {r['record_ref']: r for r in fixture['records']}
        self.alias = {}
        for group in fixture['alias_groups']:
            terms = {_norm(x) for x in group if _norm(x)}
            for term in terms:
                self.alias.setdefault(term, set()).update(terms - {term})

        self.fts = sqlite3.connect(':memory:')
        self.fts.row_factory = sqlite3.Row
        self.fts.execute(
            "CREATE VIRTUAL TABLE docs USING fts5("
            "ref UNINDEXED,key_text,body_text,tokenize='unicode61 remove_diacritics 2')"
        )
        self.fts.execute("INSERT INTO docs(docs,rank) VALUES('rank','bm25(0.0,3.0,1.0)')")
        for row in fixture['records']:
            self.fts.execute(
                'INSERT INTO docs VALUES(?,?,?)',
                (row['record_ref'], row['record_ref'].replace(':', ' '), row['title'] + ' ' + row['text']),
            )
        self.fts.commit()

        self.graph = sqlite3.connect(':memory:')
        self.graph.row_factory = sqlite3.Row
        self.graph.executescript('''
          CREATE TABLE graph_epochs(graph_epoch INTEGER,source_epoch INTEGER,status TEXT);
          CREATE TABLE graph_head_edges(logical_edge_id TEXT,graph_epoch INTEGER);
          CREATE TABLE graph_current_projection_receipts(
            graph_epoch INTEGER,source_epoch INTEGER,verified_equal INTEGER,created_at TEXT
          );
          CREATE TABLE amb(logical_edge_id TEXT,graph_epoch INTEGER,version_count INTEGER);
          CREATE VIEW v_graph_projection_ambiguous_edge_epochs AS SELECT * FROM amb;
          CREATE TABLE heads(
            logical_edge_id TEXT,source_logical_id TEXT,target_logical_id TEXT,
            relation_type TEXT,weight REAL,confidence REAL,graph_epoch INTEGER
          );
          CREATE VIEW v_graph_current_edges_fast AS SELECT * FROM heads;
        ''')
        self.graph.execute("INSERT INTO graph_epochs VALUES(1,1,'CURRENT')")
        self.graph.execute(
            "INSERT INTO graph_current_projection_receipts VALUES(1,1,1,'fixture')"
        )
        for i, edge in enumerate(fixture['edges']):
            edge_id = f'e{i:03d}'
            self.graph.execute('INSERT INTO graph_head_edges VALUES(?,1)', (edge_id,))
            self.graph.execute(
                'INSERT INTO heads VALUES(?,?,?,?,?,?,1)',
                (edge_id, edge['source_ref'], edge['target_ref'], edge['relation_type'],
                 edge['weight'], edge.get('confidence')),
            )

        self.ranker = VerifiedClayGraphRanker(
            self.graph,
            text_for_ref=lambda ref, epoch: (
                self.records.get(ref, {}).get('title', '') + ' '
                + self.records.get(ref, {}).get('text', '')
            ),
            admissible_ref=lambda ref, epoch: (
                self.records.get(ref, {}).get('status') == 'CURRENT'
                and self.records.get(ref, {}).get('epistemic') == 'KNOWN'
            ),
        )

    def _expand(self, text):
        out = set(_tokens(text))
        for term in list(out):
            for variant in _variants(term):
                out.add(variant)
                out.update(self.alias.get(variant, ()))
        return sorted(out)

    def direct(self, query, limit=5):
        terms = self._expand(query['text'] + ' ' + ' '.join(query['semantic_hints']))
        if not terms:
            return []
        expression = ' OR '.join('"' + x.replace('"', '') + '"' for x in terms)
        rows = self.fts.execute(
            'SELECT ref FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 64',
            (expression,),
        )
        return [
            row['ref'] for row in rows
            if self.records[row['ref']]['status'] == 'CURRENT'
            and self.records[row['ref']]['epistemic'] == 'KNOWN'
        ][:limit]

    def combined(self, query, limit=5):
        if query['target_mode'] != 'CONNECTED_TARGET':
            return self.direct(query, limit), []
        ranked = self.ranker.rank(
            query['anchor_refs'][0],
            query['text'] + ' ' + ' '.join(query['semantic_hints']),
            1,
            1,
            limit,
        )
        return [x.ref for x in ranked], [
            {
                'ref': x.ref,
                'score': x.score,
                'edge_ref': x.edge_ref,
                'direction': x.direction,
                'relation_type': x.relation_type,
            }
            for x in ranked
        ]

    def close(self):
        self.fts.close()
        self.graph.close()


def _score(fixture, engine, *, combined):
    rows = []
    for query in fixture['queries']:
        if combined:
            got, paths = engine.combined(query)
        else:
            got, paths = engine.direct(query), []
        relevant = set(query['relevant'])
        rank = next((i + 1 for i, ref in enumerate(got) if ref in relevant), None)
        ideal = sum(1 / math.log2(i + 2) for i in range(min(len(relevant), 5)))
        dcg = sum(
            (1 if ref in relevant else 0) / math.log2(i + 2)
            for i, ref in enumerate(got[:5])
        )
        rows.append({
            'query_id': query['query_id'],
            'mode': query['target_mode'],
            'rank': rank,
            'top5': got,
            'paths': paths,
            'hit1': rank == 1,
            'rr': 0.0 if rank is None else 1.0 / rank,
            'recall3': len(relevant & set(got[:3])) / len(relevant),
            'ndcg5': 0.0 if not ideal else dcg / ideal,
        })
    return rows


def _summary(rows):
    return {
        'n': len(rows),
        'hit1': statistics.mean(x['hit1'] for x in rows),
        'mrr': statistics.mean(x['rr'] for x in rows),
        'recall3': statistics.mean(x['recall3'] for x in rows),
        'ndcg5': statistics.mean(x['ndcg5'] for x in rows),
        'failures': [
            {'query_id': x['query_id'], 'rank': x['rank'], 'top5': x['top5']}
            for x in rows if not x['hit1']
        ],
    }


def _quantile(samples, p):
    values = sorted(samples)
    pos = (len(values) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    frac = pos - lo
    return values[lo] * (1 - frac) + values[hi] * frac


def _latency(fixture, engine, *, combined, repetitions):
    jobs = fixture['queries'] * repetitions
    random.Random(20260810 + (1 if combined else 0)).shuffle(jobs)
    samples = []
    for query in jobs:
        started = time.perf_counter_ns()
        engine.combined(query) if combined else engine.direct(query)
        samples.append((time.perf_counter_ns() - started) / 1e6)
    return {
        'n': len(samples),
        'p50_ms': _quantile(samples, 0.50),
        'p95_ms': _quantile(samples, 0.95),
        'p99_ms': _quantile(samples, 0.99),
        'mean_ms': statistics.mean(samples),
        'max_ms': max(samples),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--fixture',
        default=str(Path(__file__).with_name(
            'udb_claygraph_cognitive_retrieval_v7_fixture.json.gz.b64')),
    )
    parser.add_argument('--repetitions', type=int, default=50)
    parser.add_argument('--out')
    args = parser.parse_args()
    path = Path(args.fixture)
    fixture = (
        json.loads(gzip.decompress(base64.b64decode(path.read_text())).decode())
        if path.suffix == '.b64' else json.loads(path.read_text())
    )

    started = time.perf_counter_ns()
    engine = FixtureEngine(fixture)
    build_ms = (time.perf_counter_ns() - started) / 1e6

    baseline_rows = _score(fixture, engine, combined=False)
    candidate_rows = _score(fixture, engine, combined=True)
    baseline = _summary(baseline_rows)
    candidate = _summary(candidate_rows)
    connected_baseline = _summary([
        x for x in baseline_rows if x['mode'] == 'CONNECTED_TARGET'
    ])
    connected_candidate = _summary([
        x for x in candidate_rows if x['mode'] == 'CONNECTED_TARGET'
    ])

    result = {
        'schema_version': '2.0',
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
            'connected_target_queries': len([
                q for q in fixture['queries'] if q['target_mode'] == 'CONNECTED_TARGET'
            ]),
        },
        'projection_build_ms': build_ms,
        'baseline_direct_all': baseline,
        'candidate_v14_plus_verified_claygraph_all': candidate,
        'connected_target_baseline': connected_baseline,
        'connected_target_candidate': connected_candidate,
        'delta': {
            'all_hit1_percentage_points': (candidate['hit1'] - baseline['hit1']) * 100.0,
            'connected_hit1_percentage_points': (
                connected_candidate['hit1'] - connected_baseline['hit1']
            ) * 100.0,
        },
        'baseline_query_rows': baseline_rows,
        'candidate_query_rows': candidate_rows,
        'latency_baseline': _latency(
            fixture, engine, combined=False, repetitions=args.repetitions),
        'latency_candidate': _latency(
            fixture, engine, combined=True, repetitions=args.repetitions),
    }
    engine.close()
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text)
    print(text)


if __name__ == '__main__':
    main()
