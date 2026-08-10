#!/usr/bin/env python3
from __future__ import annotations

"""Engineering benchmark for the delta-aware Database Pulse reference kernel.

The lesion baseline intentionally materializes the complete current StateLedger. The
candidate measures idle and one-source-delta Pulses after a full bootstrap. The narrow
claim under test is scaling: steady Pulse work should be driven mainly by semantic delta,
not total materialized state size, while idle execution receipts must not mutate the
semantic epoch/hash. This is not a universal database benchmark or live FRANK cognition.
"""

import argparse
import json
import math
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.database_pulse import DatabasePulse, PulseConfig  # noqa: E402
from research_entity.harness.reference.state_ledger import StateLedger  # noqa: E402


def p95(xs: list[float]) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, math.ceil(0.95 * len(ys)) - 1))]


def timing(fn, repeat: int) -> dict[str, object]:
    vals: list[float] = []
    for _ in range(repeat):
        t0 = time.perf_counter_ns()
        fn()
        vals.append((time.perf_counter_ns() - t0) / 1_000_000)
    return {
        'median_ms': round(statistics.median(vals), 6),
        'p95_ms': round(p95(vals), 6),
        'runs_ms': [round(x, 6) for x in vals],
    }


def build_ledger(path: str, rows: int) -> StateLedger:
    ledger = StateLedger(path)
    batch = []
    for i in range(rows):
        epi = 'UNKNOWN' if i % 997 == 0 else ('CONFLICT' if i % 1543 == 0 else 'KNOWN')
        domain = 'memory' if i % 5 == 0 else 'semantic'
        batch.append({
            'op': 'SET', 'domain': domain, 'key': f'k{i:08d}',
            'value': {'i': i, 'payload': 'x' * 24},
            'epistemic': epi, 'status': 'CURRENT',
        })
    ledger.append_event(
        event_id='seed', idem='seed', base_epoch=ledger.epoch,
        event_type='BENCH_SEED', writer='database-pulse-benchmark', ops=batch,
    )
    return ledger


def bench_size(rows: int, repeat: int) -> dict[str, object]:
    if rows <= 0 or rows > 100_000:
        raise ValueError('rows must be 1..100000 for the reference benchmark')
    with tempfile.TemporaryDirectory() as td:
        db = str(Path(td) / 'pulse.db')
        ledger = build_ledger(db, rows)
        pulse = DatabasePulse(
            ledger,
            PulseConfig(
                bootstrap_scan_limit=max(4096, rows),
                max_active_refs=24,
                max_delta_events=4096,
            ),
        )
        bootstrap = pulse.run('bootstrap')
        if bootstrap['model_call_count'] != 0:
            raise AssertionError('zero-model invariant violated')
        if bootstrap['bootstrap_truncated']:
            raise AssertionError('benchmark bootstrap unexpectedly truncated')

        full = timing(lambda: ledger.materialized(), repeat)

        semantic_epoch_before_idle = ledger.epoch
        semantic_hash_before_idle = ledger.semantic_state_hash
        idle_counter = 0

        def idle():
            nonlocal idle_counter
            idle_counter += 1
            out = pulse.run(f'idle-{idle_counter}')
            if out['observed_change_count'] != 0 or out['delta_event_count'] != 0:
                raise AssertionError('idle pulse self-excited')
            if out['semantic_state_transition_count'] != 0:
                raise AssertionError('idle pulse claimed semantic transition')
            if out['model_call_count'] != 0 or out['tool_call_count'] != 0 or out['effect_count'] != 0:
                raise AssertionError('zero-model/tool/effect invariant violated')
            if ledger.epoch != semantic_epoch_before_idle or ledger.semantic_state_hash != semantic_hash_before_idle:
                raise AssertionError('idle pulse mutated semantic state')

        idle_t = timing(idle, repeat)

        delta_counter = 0
        delta_lat: list[float] = []
        for _ in range(repeat):
            delta_counter += 1
            ledger.append_event(
                event_id=f'delta-{delta_counter}', idem=f'delta-{delta_counter}',
                base_epoch=ledger.epoch, event_type='BENCH_DELTA', writer='database-pulse-benchmark',
                ops=[{
                    'op':'SET','domain':'memory','key':'hot',
                    'value':{'n':delta_counter},'epistemic':'KNOWN','status':'CURRENT',
                }],
            )
            semantic_epoch = ledger.epoch
            semantic_hash = ledger.semantic_state_hash
            t0 = time.perf_counter_ns()
            out = pulse.run(f'delta-pulse-{delta_counter}')
            delta_lat.append((time.perf_counter_ns() - t0) / 1_000_000)
            if out['observed_change_count'] != 1 or out['delta_event_count'] != 1:
                raise AssertionError(
                    f"expected one semantic event/ref delta, got events={out['delta_event_count']} refs={out['observed_change_count']}"
                )
            if ledger.epoch != semantic_epoch or ledger.semantic_state_hash != semantic_hash:
                raise AssertionError('Pulse receipt mutated source semantic state after delta processing')
        delta_t = {
            'median_ms': round(statistics.median(delta_lat), 6),
            'p95_ms': round(p95(delta_lat), 6),
            'runs_ms': [round(x, 6) for x in delta_lat],
        }

        verify = pulse.journal.verify_all()
        out = {
            'rows': rows,
            'bootstrap': {
                'census_count': bootstrap['census_count'],
                'bootstrap_truncated': bootstrap['bootstrap_truncated'],
                'active_ref_count': len(bootstrap['active_refs']),
            },
            'full_census_lesion': full,
            'idle_delta_pulse': idle_t,
            'one_source_delta_pulse': delta_t,
            'idle_vs_full_median_ratio': round(float(idle_t['median_ms']) / max(float(full['median_ms']), 1e-12), 6),
            'delta_vs_full_median_ratio': round(float(delta_t['median_ms']) / max(float(full['median_ms']), 1e-12), 6),
            'semantic_epoch_after': ledger.epoch,
            'pulse_count_after': verify['pulse_count'],
            'pulse_chain_hash': verify['pulse_chain_hash'],
        }
        ledger.close()
        return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--rows', default='100,1000,10000')
    ap.add_argument('--repeat', type=int, default=10)
    ap.add_argument('--output')
    args = ap.parse_args()
    sizes = [int(x) for x in args.rows.split(',') if x.strip()]
    repeat = max(1, min(args.repeat, 100))
    results = [bench_size(n, repeat) for n in sizes]
    payload = {
        'schema_version': '0.2',
        'benchmark_class': 'CLAY_SELF_USE_ENGINEERING_PROXY',
        'hypothesis': 'steady Database Pulse cost should be driven by semantic delta, not total materialized state size, without semantic self-churn',
        'repeat': repeat,
        'results': results,
        'limitations': [
            'StateLedger reference harness and Python overhead are measured; this is not the final one-module Frank binary.',
            'The full-census comparator is intentionally the architectural lesion being removed, not a claim against every database engine.',
            'No ClayGraph propagation, GWT competition, model inference, tool invocation or external effects are included in this zero-model reference benchmark.',
            'The Pulse journal is hash chained but not yet folded into StateLedger trace_root/execution_chain; integration must preserve the no-semantic-churn property.',
            'Runner hardware, filesystem, Python and SQLite versions must accompany promotion evidence.',
        ],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
