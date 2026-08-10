#!/usr/bin/env python3
from __future__ import annotations

"""Differential benchmark: Database Pulse v1 vs dual-clock/delta v2.

This benchmark is deliberately diagnostic.  It measures the current reference Python/
SQLite candidates, not a final FRANK binary.  It is designed to falsify two hypotheses:

H1: v2 removes semantic self-churn and unrelated QueryReceipt invalidation.
H2: v2 steady-state latency scales mainly with deltas rather than total state size.

If H2 fails while H1 passes, the benchmark points at remaining O(N) work (notably full
integrity/root verification) rather than hiding it.
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

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch  # noqa:E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa:E402
from research_entity.runtime.database_pulse_candidate_v1 import DatabasePulseRuntime, PulseSpec  # noqa:E402
from research_entity.runtime.database_pulse_candidate_v2 import DatabasePulseRuntimeV2, PulseSpecV2  # noqa:E402


def p95(values: list[float]) -> float:
    ys = sorted(values)
    return ys[min(len(ys) - 1, max(0, math.ceil(0.95 * len(ys)) - 1))]


def summarize(values: list[float]) -> dict[str, object]:
    return {
        "median_ms": round(statistics.median(values), 6),
        "p95_ms": round(p95(values), 6),
        "runs_ms": [round(x, 6) for x in values],
    }


def seed(path: str, rows: int, runtime_cls):
    ledger = StateLedger(path)
    ops = []
    for i in range(rows):
        domain = "memory" if i % 2 == 0 else "semantic"
        epi = "UNKNOWN" if i % 997 == 0 else ("CONFLICT" if i % 1543 == 0 else "KNOWN")
        ops.append({
            "op":"SET", "domain":domain, "key":f"k{i:08d}",
            "value":{"i":i, "payload":"x" * 24, "priority": (i % 11) / 10.0},
            "epistemic":epi, "status":"CURRENT",
        })
    ledger.append_event(
        event_id="seed", idem="seed", base_epoch=ledger.epoch,
        event_type="BENCH_SEED", writer="pulse-v2-benchmark", ops=ops,
        committed_at="2026-08-10T00:00:00Z",
    )
    runtime = runtime_cls(ledger)
    runtime.set_scheduler(
        enabled=True,
        event_id="scheduler-on",
        base_epoch=ledger.epoch,
        actor="pulse-v2-benchmark",
        reason="benchmark",
        committed_at="2026-08-10T00:00:01Z",
    )
    return ledger, runtime


def bench_v1(path: str, rows: int, repeat: int) -> dict[str, object]:
    ledger, runtime = seed(path, rows, DatabasePulseRuntime)
    runtime.run_pulse(PulseSpec(
        "bootstrap-v1", basis_epoch=ledger.epoch,
        source_domains=("memory","semantic"), max_candidates=128, max_focus=12,
    ), committed_at="2026-08-10T00:00:02Z")
    plane = UnifiedDBQueryPlane(ledger)
    prepared = plane.query(QuerySpec(
        "prepared-v1", domains=("memory",), basis_epoch=ledger.epoch, limit=32,
    ))
    before_idle_epoch = ledger.epoch
    idle: list[float] = []
    for i in range(repeat):
        t0 = time.perf_counter_ns()
        runtime.run_pulse(PulseSpec(
            f"idle-v1-{i}", basis_epoch=ledger.epoch,
            source_domains=("memory","semantic"), max_candidates=128, max_focus=12,
        ))
        idle.append((time.perf_counter_ns() - t0) / 1_000_000)
    query_survives = True
    try:
        plane.select_for_assembly(prepared)
    except StaleEpoch:
        query_survives = False

    ledger.append_event(
        event_id="delta-v1", idem="delta-v1", base_epoch=ledger.epoch,
        event_type="BENCH_DELTA", writer="pulse-v2-benchmark",
        ops=[{"op":"SET","domain":"memory","key":"hot","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
    )
    t0 = time.perf_counter_ns()
    runtime.run_pulse(PulseSpec(
        "delta-pulse-v1", basis_epoch=ledger.epoch,
        source_domains=("memory","semantic"), max_candidates=128, max_focus=12,
    ))
    delta_ms = (time.perf_counter_ns() - t0) / 1_000_000
    out = {
        "idle": summarize(idle),
        "semantic_epoch_advance_idle": ledger.epoch - before_idle_epoch - 2,
        "prepared_query_survives_idle": query_survives,
        "one_delta_pulse_ms": round(delta_ms, 6),
        "final_semantic_epoch": ledger.epoch,
    }
    ledger.close()
    return out


def bench_v2(path: str, rows: int, repeat: int) -> dict[str, object]:
    ledger, runtime = seed(path, rows, DatabasePulseRuntimeV2)
    runtime.run_pulse_v2(PulseSpecV2(
        "bootstrap-v2", basis_epoch=ledger.epoch,
        source_domains=("memory","semantic"), max_candidates=128, max_focus=12,
        refresh_every_pulses=4096,
    ), committed_at="2026-08-10T00:00:02Z")
    plane = UnifiedDBQueryPlane(ledger)
    prepared = plane.query(QuerySpec(
        "prepared-v2", domains=("memory",), basis_epoch=ledger.epoch, limit=32,
    ))
    before_idle_epoch = ledger.epoch
    idle: list[float] = []
    for i in range(repeat):
        t0 = time.perf_counter_ns()
        runtime.run_pulse_v2(PulseSpecV2(
            f"idle-v2-{i}", basis_epoch=ledger.epoch,
            source_domains=("memory","semantic"), max_candidates=128, max_focus=12,
            refresh_every_pulses=4096,
        ))
        idle.append((time.perf_counter_ns() - t0) / 1_000_000)
    query_survives = True
    try:
        plane.select_for_assembly(prepared)
    except StaleEpoch:
        query_survives = False

    ledger.append_event(
        event_id="delta-v2", idem="delta-v2", base_epoch=ledger.epoch,
        event_type="BENCH_DELTA", writer="pulse-v2-benchmark",
        ops=[{"op":"SET","domain":"memory","key":"hot","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
    )
    t0 = time.perf_counter_ns()
    receipt = runtime.run_pulse_v2(PulseSpecV2(
        "delta-pulse-v2", basis_epoch=ledger.epoch,
        source_domains=("memory","semantic"), max_candidates=128, max_focus=12,
        refresh_every_pulses=4096,
    ))
    delta_ms = (time.perf_counter_ns() - t0) / 1_000_000
    out = {
        "idle": summarize(idle),
        "semantic_epoch_advance_idle": ledger.epoch - before_idle_epoch - 1,
        "prepared_query_survives_idle": query_survives,
        "one_delta_pulse_ms": round(delta_ms, 6),
        "delta_changed_refs": list(receipt.changed_refs),
        "pulse_sequence": runtime.journal.verify_all()["pulse_sequence"],
        "final_semantic_epoch": ledger.epoch,
    }
    ledger.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="100,1000,10000")
    ap.add_argument("--repeat", type=int, default=7)
    ap.add_argument("--output")
    args = ap.parse_args()
    sizes = [int(x) for x in args.rows.split(",") if x.strip()]
    repeat = max(1, min(30, args.repeat))
    results = []
    for rows in sizes:
        with tempfile.TemporaryDirectory() as td:
            v1 = bench_v1(str(Path(td) / "v1.sqlite"), rows, repeat)
            v2 = bench_v2(str(Path(td) / "v2.sqlite"), rows, repeat)
        results.append({
            "rows": rows,
            "v1": v1,
            "v2": v2,
            "v2_idle_vs_v1_ratio": round(
                float(v2["idle"]["median_ms"]) / max(float(v1["idle"]["median_ms"]), 1e-12), 6
            ),
        })
    payload = {
        "schema_version": "0.1",
        "benchmark_class": "CLAY_SELF_USE_ENGINEERING_DIFFERENTIAL",
        "repeat": repeat,
        "hypotheses": {
            "H1": "v2 eliminates semantic self-churn/query-receipt invalidation on idle Pulse",
            "H2": "v2 idle latency becomes substantially less dependent on total semantic state size",
        },
        "results": results,
        "limitations": [
            "Python/SQLite reference candidates only; not final one-module FRANK binary.",
            "v1 and v2 retain v1 full semantic-root integrity verification in this baseline; H2 may therefore fail and motivate the next iteration.",
            "No ClayGraph/GWT/tool/effect path is exercised.",
            "Runner hardware/Python/SQLite metadata must accompany promotion evidence.",
        ],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
