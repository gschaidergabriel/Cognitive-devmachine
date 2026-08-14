#!/usr/bin/env python3
from __future__ import annotations

"""Falsify V4 rank-index retention economics after a regime change.

The semantic candidate order is not under test here. The experiment asks a narrower physical
question: once V4 has economically admitted the rebuildable StateLedger expression index,
what happens when subsequent Pulse lifetime history collapses and the controller routes
ONLINE again?

Matched arms measure authoritative StateLedger append-event latency with no index, with the
rank index, and after explicitly dropping that index. A V4 stable->churn sequence separately
records whether ONLINE_NO_COMPILE actually retires the already-present accelerator.
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

from research_entity.harness.reference.state_ledger import StateLedger  # noqa:E402
from research_entity.runtime.database_pulse_rank_index_v3 import (  # noqa:E402
    AuthoritativeRankIndexV3,
    INDEX_NAME,
)
from research_entity.runtime.database_pulse_rank_path_v4 import (  # noqa:E402
    AdaptiveAuthoritativeRankPathV4,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics  # noqa:E402
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime  # noqa:E402


def q(xs, p):
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, math.ceil(p * len(ys)) - 1))]


def stats(xs):
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6),
        "p50_ms": round(statistics.median(xs), 6),
        "p90_ms": round(q(xs, 0.90), 6),
        "p95_ms": round(q(xs, 0.95), 6),
        "p99_ms": round(q(xs, 0.99), 6),
        "max_ms": round(max(xs), 6),
        "mean_ms": round(statistics.mean(xs), 6),
    }


def timed(fn):
    t = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns() - t) / 1_000_000.0


def seed(path: Path, rows: int):
    ledger = StateLedger(path)
    ops = []
    for i in range(rows):
        ops.append({
            "op": "SET",
            "domain": "memory",
            "key": f"k{i:06d}",
            "value": {
                "priority": (i % 11) / 10.0,
                "urgency": (i % 7) / 6.0,
                "salience": (i % 5) / 4.0,
                "novelty": (i % 3) / 2.0,
                "fact": i,
            },
            "epistemic": "KNOWN",
            "status": "CURRENT",
        })
    ledger.append_event(
        event_id="seed",
        idem="seed",
        base_epoch=ledger.epoch,
        event_type="RANK_RETENTION_SEED",
        writer="benchmark",
        ops=ops,
        committed_at="2026-08-10T03:00:00Z",
    )
    ledger.close()


def update_series(path: Path, updates: int, *, ensure_index: bool, drop_after_build: bool = False):
    ledger = StateLedger(path)
    rank = AuthoritativeRankIndexV3(ledger)
    try:
        build_ms = 0.0
        drop_ms = 0.0
        if ensure_index:
            _, build_ms = timed(rank.ensure_index)
        if drop_after_build:
            _, drop_ms = timed(rank.drop_index)
        present = ledger.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?", (INDEX_NAME,)
        ).fetchone() is not None
        lat = []
        for n in range(updates):
            k = f"k{n % 97:06d}"
            value = {
                "priority": ((n + 3) % 11) / 10.0,
                "urgency": ((n + 5) % 7) / 6.0,
                "salience": ((n + 2) % 5) / 4.0,
                "novelty": ((n + 1) % 3) / 2.0,
                "fact": n,
            }
            _, ms = timed(lambda n=n, k=k, value=value: ledger.append_event(
                event_id=f"u{n}",
                idem=f"u{n}",
                base_epoch=ledger.epoch,
                event_type="RANK_RETENTION_UPDATE",
                writer="benchmark",
                ops=[{
                    "op": "SET", "domain": "memory", "key": k, "value": value,
                    "epistemic": "KNOWN", "status": "CURRENT",
                }],
                committed_at=f"2026-08-10T03:{(n // 60) % 60:02d}:{n % 60:02d}Z",
            ))
            lat.append(ms)
        return {
            "index_present_during_updates": present,
            "build_ms": round(build_ms, 6),
            "drop_ms": round(drop_ms, 6),
            "append_event": stats(lat),
            "final_epoch": ledger.epoch,
            "semantic_state_hash": ledger.semantic_state_hash,
        }
    finally:
        ledger.close()


def adaptive_retention_probe(path: Path):
    ledger = StateLedger(path)
    route = AdaptiveAuthoritativeRankPathV4(ledger)
    econ = CompileEconomics(
        build_cost_us=1000.0,
        online_query_us=100.0,
        compiled_query_us=1.0,
        online_quality=1.0,
        compiled_quality=1.0,
        expected_reads_before_invalidation=0.0,
        safety_factor=1.2,
    )
    stable = tuple(EpochReadLifetime(i, 1000) for i in range(8))
    churn = tuple(
        [EpochReadLifetime(i, 1000) for i in range(5)]
        + [EpochReadLifetime(5, 2), EpochReadLifetime(6, 1), EpochReadLifetime(7, 1)]
    )
    try:
        compiled = route.select(
            source_domains=("memory",), basis_epoch=ledger.epoch,
            max_candidates=64, max_focus=4,
            economics_without_horizon=econ, pulse_history=stable,
        )
        after_compile = route.index_exists()
        online_after_churn = route.select(
            source_domains=("memory",), basis_epoch=ledger.epoch,
            max_candidates=64, max_focus=4,
            economics_without_horizon=econ, pulse_history=churn,
        )
        after_churn = route.index_exists()
        return {
            "stable": {
                "physical_mode": compiled.physical_mode,
                "horizon_status": compiled.horizon_status,
                "horizon_reads_lower_bound": compiled.horizon_reads_lower_bound,
                "compile_reason": compiled.compile_reason,
                "index_present_after": after_compile,
            },
            "churn": {
                "physical_mode": online_after_churn.physical_mode,
                "horizon_status": online_after_churn.horizon_status,
                "horizon_reads_lower_bound": online_after_churn.horizon_reads_lower_bound,
                "compile_reason": online_after_churn.compile_reason,
                "index_present_before": online_after_churn.index_present_before,
                "index_present_after": after_churn,
                "query_plan": list(online_after_churn.query_plan),
            },
            "retained_after_online_decision": bool(after_churn and online_after_churn.physical_mode == "ONLINE_NO_COMPILE"),
        }
    finally:
        ledger.close()


def bench(rows: int, updates: int):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        p0 = root / "online.sqlite"
        p1 = root / "indexed.sqlite"
        p2 = root / "dropped.sqlite"
        p3 = root / "probe.sqlite"
        for p in (p0, p1, p2, p3):
            seed(p, rows)
        online = update_series(p0, updates, ensure_index=False)
        indexed = update_series(p1, updates, ensure_index=True)
        dropped = update_series(p2, updates, ensure_index=True, drop_after_build=True)
        probe = adaptive_retention_probe(p3)
        p50_online = online["append_event"]["p50_ms"]
        p50_indexed = indexed["append_event"]["p50_ms"]
        p50_dropped = dropped["append_event"]["p50_ms"]
        return {
            "schema_version": "1.0",
            "benchmark_class": "DATABASE_PULSE_RANK_RETENTION_V4_FALSIFIER",
            "fixture": {"authoritative_rows": rows, "updates": updates, "storage": "FILE_BACKED_SQLITE_WAL"},
            "arms": {"online_no_index": online, "index_retained": indexed, "index_built_then_dropped": dropped},
            "adaptive_retention_probe": probe,
            "derived": {
                "indexed_vs_online_write_p50_ratio": round(p50_indexed / max(1e-12, p50_online), 6),
                "indexed_vs_dropped_write_p50_ratio": round(p50_indexed / max(1e-12, p50_dropped), 6),
                "write_p50_delta_ms_indexed_minus_online": round(p50_indexed - p50_online, 6),
                "write_p50_delta_ms_indexed_minus_dropped": round(p50_indexed - p50_dropped, 6),
            },
            "hypothesis": "V4 can retain an economically stale accelerator after a churn-driven ONLINE decision; if index write overhead is material, a separately measured RETAIN-vs-RETIRE policy is required.",
            "counterhypothesis": "Retaining the index has negligible write/resource cost, so automatic retirement would add churn and complexity without material benefit.",
            "authority_boundary": "Physical-performance falsifier only; StateLedger semantic authority and Pulse effect authority are unchanged.",
            "limitations": [
                "Synthetic file-backed StateLedger workload; not Andreas target hardware.",
                "Single-writer update stream; concurrent-write cost is a separate experiment.",
                "Does not authorize automatic DROP INDEX; it supplies measurements needed to justify or reject that policy.",
            ],
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=5000)
    ap.add_argument("--updates", type=int, default=250)
    ap.add_argument("--output")
    a = ap.parse_args()
    out = bench(max(200, a.rows), max(20, a.updates))
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if a.output:
        p = Path(a.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
