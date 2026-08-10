#!/usr/bin/env python3
from __future__ import annotations

"""Engineering benchmark for the delta-aware Database Pulse reference kernel.

The baseline intentionally materializes the complete current StateLedger. The candidate
measures idle and one-source-delta pulses after a bootstrap pulse. This tests the narrow
architectural claim that steady Pulse work can scale with semantic delta rather than total
state size. It is not a general database benchmark and not live FRANK cognitive evidence.
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

from research_entity.harness.reference.database_pulse import DatabasePulse  # noqa: E402
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
    with tempfile.TemporaryDirectory() as td:
        db = str(Path(td) / 'pulse.db')
        ledger = build_ledger(db, rows)
        pulse = DatabasePulse(ledger)
        bootstrap = pulse.run('bootstrap')
        if bootstrap['model_call_count'] != 0:
            raise AssertionError('zero-model invariant violated')

        full = timing(lambda: ledger.materialized(), repeat)

        idle_counter = 0
        def idle():
            nonlocal idle_counter
            idle_counter += 1
            out = pulse.run(f'idle-{idle_counter}')
            if out['observed_change_count'] != 0:
                raise AssertionError('idle pulse self-excited')
            if out['model_call_count'] != 0 or out['tool_call_count'] != 0 or out['effect_count'] != 0:
                raise AssertionError('zero-model/tool/effect invariant violated')
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
            t0 = time.perf_counter_ns()
            out = pulse.run(f'delta-pulse-{delta_counter}')
            delta_lat.append((time.perf_counter_ns() - t0) / 1_000_000)
            if out['observed_change_count'] != 1:
                raise AssertionError(f"expected one source delta, got {out['observed_change_count']}")
        delta_t = {
            'median_ms': round(statistics.median(delta_lat), 6),
            'p95_ms': round(p95(delta_lat), 6),
            'runs_ms': [round(x, 6) for x in delta_lat],
        }

        out = {
            'rows': rows,
            'bootstrap': {
                'census_count': bootstrap['census_count'],
                'bootstrap_truncated': bootstrap['bootstrap_truncated'],
                'active_ref_count': len(bootstrap['active_refs']),
            },
            'full_census': full,
            'idle_delta_pulse': idle_t,
            'one_source_delta_pulse': delta_t,
            'idle_vs_full_median_ratio': round(float(idle_t['median_ms']) / max(float(full['median_ms']), 1e-12), 6),
            'delta_vs_full_median_ratio': round(float(delta_t['median_ms']) / max(float(full['median_ms']), 1e-12), 6),
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
        'schema_version': '0.1',
        'benchmark_class': 'CLAY_SELF_USE_ENGINEERING_PROXY',
        'hypothesis': 'steady Database Pulse cost should be driven by semantic delta, not total materialized state size',
        'repeat': repeat,
        'results': results,
        'limitations': [
            'StateLedger reference harness and Python overhead are measured; this is not the final one-module Frank binary.',
            'The full-census comparator is intentionally the architectural lesion being removed, not a claim against every database engine.',
            'No ClayGraph propagation, model inference, tool invocation or external effects are included in this zero-model reference benchmark.',
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
