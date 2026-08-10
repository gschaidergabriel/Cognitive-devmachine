#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import platform
import sqlite3
import statistics
import tempfile
import time

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_path_v5 import AdaptiveAuthoritativeRankPathV5
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime

ROUNDS = 25
BUSY_TIMEOUT_MS = 40


def q(xs, p):
    ys = sorted(xs)
    k = (len(ys) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return ys[lo] if lo == hi else ys[lo] * (hi - k) + ys[hi] * (k - lo)


def stats(xs):
    return {
        "n": len(xs),
        "p50_ms": q(xs, 0.50),
        "p95_ms": q(xs, 0.95),
        "p99_ms": q(xs, 0.99),
        "mean_ms": statistics.fmean(xs),
        "min_ms": min(xs),
        "max_ms": max(xs),
    }


def econ():
    return CompileEconomics(
        build_cost_us=1000.0,
        online_query_us=100.0,
        compiled_query_us=10.0,
        online_quality=1.0,
        compiled_quality=1.0,
        expected_reads_before_invalidation=0.0,
        safety_factor=1.0,
    )


def history():
    return tuple(EpochReadLifetime(i + 1, 200) for i in range(8))


def main():
    fd, path = tempfile.mkstemp(prefix="clay-v5-contention-bench-", suffix=".sqlite3")
    os.close(fd)
    a = b = None
    try:
        a = StateLedger(path)
        a.append_event(
            event_id="seed",
            idem="seed",
            base_epoch=0,
            event_type="SEED",
            writer="benchmark",
            ops=[{
                "op": "SET",
                "domain": "memory",
                "key": "x",
                "value": {"priority": 1.0},
                "epistemic": "KNOWN",
                "status": "CURRENT",
            }],
            committed_at="2026-08-10T01:03:00Z",
        )
        b = StateLedger(path)
        b.conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        rank = AdaptiveAuthoritativeRankPathV5(b)

        failure_ms = []
        recovery_ms = []
        retryable_failures = 0
        false_index_commits = 0
        false_receipts = 0
        recovery_successes = 0
        root_drifts = 0

        for i in range(ROUNDS):
            # Start each round from the ONLINE/no-index state without touching semantic roots.
            if rank.index_exists():
                rank.v3.drop_index()
            if rank.maintenance_receipts():
                b.conn.execute("DELETE FROM pulse_rank_maintenance_receipts_v5")
                b.conn.commit()

            plan = rank.plan_lifecycle(
                basis_epoch=b.epoch,
                economics_without_horizon=econ(),
                pulse_history=history(),
            )
            roots = (b.epoch, b.semantic_state_hash, b.trace_root_hash)

            a.conn.execute("BEGIN IMMEDIATE")
            t0 = time.perf_counter_ns()
            failed = rank.apply_maintenance(plan)
            failure_ms.append((time.perf_counter_ns() - t0) / 1e6)
            retryable_failures += int(failed.status == "FAILED_RETRYABLE_PHYSICAL_MAINTENANCE")
            false_index_commits += int(rank.index_exists())
            false_receipts += int(bool(rank.maintenance_receipts()))
            root_drifts += int((b.epoch, b.semantic_state_hash, b.trace_root_hash) != roots)
            a.conn.rollback()

            # Reobserve after the lock is released; a successful repair must be fresh-plan only.
            fresh = rank.plan_lifecycle(
                basis_epoch=b.epoch,
                economics_without_horizon=econ(),
                pulse_history=history(),
            )
            t0 = time.perf_counter_ns()
            recovered = rank.apply_maintenance(fresh)
            recovery_ms.append((time.perf_counter_ns() - t0) / 1e6)
            recovery_successes += int(
                recovered.status == "BUILT"
                and recovered.persisted
                and rank.index_exists()
                and len(rank.maintenance_receipts()) == 1
            )
            root_drifts += int((b.epoch, b.semantic_state_hash, b.trace_root_hash) != roots)

        result = {
            "schema_version": "1.0",
            "benchmark": "DATABASE_PULSE_RANK_PATH_V5_TWO_CONNECTION_CONTENTION",
            "environment": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "sqlite": sqlite3.sqlite_version,
                "journal_mode": b.conn.execute("PRAGMA journal_mode").fetchone()[0],
                "synchronous": b.conn.execute("PRAGMA synchronous").fetchone()[0],
                "busy_timeout_ms": b.conn.execute("PRAGMA busy_timeout").fetchone()[0],
            },
            "rounds": ROUNDS,
            "contended_failure_latency": stats(failure_ms),
            "recovery_build_latency": stats(recovery_ms),
            "retryable_failure_rate": retryable_failures / ROUNDS,
            "recovery_success_rate": recovery_successes / ROUNDS,
            "false_index_commit_rate": false_index_commits / ROUNDS,
            "false_receipt_rate": false_receipts / ROUNDS,
            "root_drift_events": root_drifts,
            "authority": "BENCHMARK_ONLY_PHYSICAL_MAINTENANCE_NO_SEMANTIC_AUTHORITY",
        }
        result["pass"] = bool(
            retryable_failures == ROUNDS
            and recovery_successes == ROUNDS
            and false_index_commits == 0
            and false_receipts == 0
            and root_drifts == 0
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["pass"] else 2)
    finally:
        if a is not None:
            try: a.conn.rollback()
            except Exception: pass
            a.close()
        if b is not None:
            b.close()
        for suffix in ("", "-wal", "-shm"):
            try: os.unlink(path + suffix)
            except FileNotFoundError: pass


if __name__ == "__main__":
    main()
