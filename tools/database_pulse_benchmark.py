#!/usr/bin/env python3
from __future__ import annotations

"""Reproducible engineering benchmark for FRANK Database Pulse v0.

This measures the Pulse implementation and a same-query SQLite partial-index lesion. It is
NOT a claim that UnifiedDB is universally faster than normal databases and not evidence of
phenomenal consciousness or live-FRANK task quality.
"""

import argparse
import json
import math
import os
from pathlib import Path
import platform
import resource
import sqlite3
import statistics
import sys
import tempfile
import time
from typing import Callable, Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "research_entity" / "runtime"
sys.path.insert(0, str(RUNTIME))
from database_pulse_v0 import DatabasePulseV0  # noqa: E402

U12 = (RUNTIME / "RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(encoding="utf-8")


def quantile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, math.ceil(q * len(ys)) - 1))]


def stats_ms(xs: list[float]) -> dict[str, Any]:
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6) if xs else 0.0,
        "p50_ms": round(statistics.median(xs), 6) if xs else 0.0,
        "p90_ms": round(quantile(xs, 0.90), 6),
        "p95_ms": round(quantile(xs, 0.95), 6),
        "p99_ms": round(quantile(xs, 0.99), 6),
        "max_ms": round(max(xs), 6) if xs else 0.0,
        "mean_ms": round(statistics.mean(xs), 6) if xs else 0.0,
    }


def timed(fn: Callable[[], Any]) -> tuple[Any, float]:
    t0 = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns() - t0) / 1_000_000.0


def hot_index_lesion(*, rows: int, repeats: int, limit: int) -> dict[str, Any]:
    con = sqlite3.connect(":memory:")
    con.executescript(U12)
    con.execute("BEGIN")
    for i in range(rows):
        applied = "old" if i < int(rows * 0.95) else None
        con.execute(
            """INSERT INTO frank_database_pulse_delta_queue
               (delta_id,changed_ref,reason_class,payload_clay,payload_hash,source_epoch,
                graph_epoch,admitted_at,applied_pulse_id)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (f"q{i}", f"r{i}", "SYNTHETIC", "{}", "h", 1, 1, "t", applied),
        )
    con.commit()
    sql = """SELECT seq,delta_id FROM frank_database_pulse_delta_queue
             WHERE applied_pulse_id IS NULL AND seq>? ORDER BY seq LIMIT ?"""

    def sample() -> list[float]:
        lat = []
        for _ in range(repeats):
            _, ms = timed(lambda: con.execute(sql, (0, limit)).fetchall())
            lat.append(ms)
        return lat

    plan_index = [tuple(r) for r in con.execute("EXPLAIN QUERY PLAN " + sql, (0, limit)).fetchall()]
    with_index = sample()
    con.execute("DROP INDEX idx_frank_pulse_delta_unapplied")
    plan_lesion = [tuple(r) for r in con.execute("EXPLAIN QUERY PLAN " + sql, (0, limit)).fetchall()]
    without_index = sample()
    con.close()
    s_index = stats_ms(with_index)
    s_lesion = stats_ms(without_index)
    ratio = (
        s_lesion["p50_ms"] / s_index["p50_ms"]
        if s_index["p50_ms"] > 0 else None
    )
    return {
        "class": "SAME_SQL_PARTIAL_INDEX_LESION_SYNTHETIC",
        "rows": rows,
        "applied_fraction": 0.95,
        "limit": limit,
        "repeats": repeats,
        "with_partial_index": s_index,
        "without_partial_index": s_lesion,
        "median_speedup_ratio": round(ratio, 4) if ratio is not None else None,
        "query_plan_with_index": plan_index,
        "query_plan_without_index": plan_lesion,
    }


def benchmark(*, deltas: int, batch: int, idle: int, hot_rows: int, hot_repeats: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "pulse.db"
        con = sqlite3.connect(db_path)
        journal_mode = con.execute("PRAGMA journal_mode=WAL").fetchone()[0]
        con.executescript(U12)
        con.execute("PRAGMA optimize=0x10002")
        pulse = DatabasePulseV0(con)
        pulse.bootstrap(
            entity_id="dr-unterweger-frank-personal-entity",
            lineage_id="benchmark-lineage",
            now="boot",
        )

        admit_lat = []
        for i in range(deltas):
            _, ms = timed(
                lambda i=i: pulse.admit_delta(
                    delta_id=f"d{i}",
                    changed_ref=f"memory:{i % 257}",
                    reason_class="MEMORY_UPDATE",
                    payload={"value": i, "bucket": i % 17},
                    source_epoch=1,
                    graph_epoch=1,
                    now=f"a{i}",
                )
            )
            admit_lat.append(ms)

        active_lat = []
        active_receipts = []
        while True:
            backlog = con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_delta_queue WHERE applied_pulse_id IS NULL"
            ).fetchone()[0]
            if backlog == 0:
                break
            receipt, ms = timed(
                lambda: pulse.pulse(max_deltas=batch, now=f"pulse-{len(active_lat)}")
            )
            active_lat.append(ms)
            active_receipts.append(receipt)

        idle_lat = []
        for i in range(idle):
            receipt, ms = timed(lambda i=i: pulse.pulse(max_deltas=batch, now=f"idle-{i}"))
            assert receipt.applied_delta_count == 0
            assert receipt.model_call_count == 0
            idle_lat.append(ms)

        # Real rollback/recovery probes are part of the benchmark receipt, not just unit tests.
        pulse.admit_delta(
            delta_id="fault-probe",
            changed_ref="goal:fault",
            reason_class="GOAL_UPDATE",
            payload={"fault": True},
            source_epoch=2,
            graph_epoch=2,
            now="fault-admit",
        )
        state_before = tuple(
            con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone()
        )
        rollback_ok = False
        try:
            pulse.pulse(now="fault", fault_after_apply=True)
        except RuntimeError:
            state_after = tuple(
                con.execute(
                    "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
                ).fetchone()
            )
            rollback_ok = state_before == state_after and con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue WHERE delta_id='fault-probe'"
            ).fetchone()[0] is None

        final_receipt = pulse.pulse(now="fault-retry")
        con.close()

        sizes = {}
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(db_path) + suffix)
            sizes[p.name] = p.stat().st_size if p.exists() else 0

    index_lesion = hot_index_lesion(rows=hot_rows, repeats=hot_repeats, limit=batch)
    return {
        "schema_version": "1.0",
        "benchmark_class": "DATABASE_PULSE_ENGINEERING_PROXY",
        "implementation": "database_pulse_v0",
        "configuration": {
            "deltas": deltas,
            "batch": batch,
            "idle_pulses": idle,
            "journal_mode": journal_mode,
            "synchronous": "sqlite-default-for-WAL",
        },
        "results": {
            "delta_admission": stats_ms(admit_lat),
            "active_pulse": stats_ms(active_lat),
            "idle_zero_model_pulse": stats_ms(idle_lat),
            "active_pulse_count": len(active_receipts),
            "applied_delta_total": sum(r.applied_delta_count for r in active_receipts),
            "model_call_total_active": sum(r.model_call_count for r in active_receipts),
            "transaction_fault_rollback_pass": rollback_ok,
            "fault_retry_applied": final_receipt.applied_delta_count,
            "hot_queue_partial_index_lesion": index_lesion,
        },
        "runtime_metadata": {
            "python": sys.version,
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "pid": os.getpid(),
            "maxrss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "db_sizes_bytes": sizes,
        },
        "limitations": [
            "This is an engineering proxy on synthetic deltas, not live-FRANK cognitive quality.",
            "The partial-index lesion compares the same SQLite query with/without one Pulse-specific hot index; it is not a general database comparison.",
            "Remote VPS evidence is preliminary and cannot substitute for Andreas' final Ubuntu target acceptance.",
            "A Database Pulse runtime did not previously exist, so there is no executable historical Pulse baseline to claim replacement superiority against.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deltas", type=int, default=4096)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--idle", type=int, default=500)
    ap.add_argument("--hot-rows", type=int, default=20000)
    ap.add_argument("--hot-repeats", type=int, default=400)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = benchmark(
        deltas=max(1, args.deltas),
        batch=max(1, args.batch),
        idle=max(1, args.idle),
        hot_rows=max(100, args.hot_rows),
        hot_repeats=max(10, args.hot_repeats),
    )
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
