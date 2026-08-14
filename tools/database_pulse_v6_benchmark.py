#!/usr/bin/env python3
from __future__ import annotations

"""Matched engineering benchmark for current-main semantic Pulse V5 vs execution-plane V6.

Arms:
1. current semantic DatabasePulseRuntimeV5;
2. V6 with full canonical audit on every Pulse;
3. V6 with the intended layered audit period (default 32).

All arms use the same StateLedger schema, same memory fixture, same score-before-LIMIT rank
semantics and no model/tool/effect calls.  This benchmark measures implementation mechanics,
not live-FRANK cognitive quality or universal DB superiority.
"""

import argparse
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch  # noqa:E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa:E402
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec  # noqa:E402
from research_entity.runtime.database_pulse_execution_plane_v6 import (  # noqa:E402
    DatabasePulseExecutionPlaneV6, PulseSpecV6,
)
from research_entity.runtime.database_pulse_runtime_v5 import DatabasePulseRuntimeV5  # noqa:E402


def quantile(xs, p):
    ys = sorted(xs)
    return ys[min(len(ys)-1, max(0, math.ceil(p*len(ys))-1))] if ys else 0.0


def stats(xs):
    return {
        "n":len(xs),
        "min_ms":round(min(xs),6) if xs else 0.0,
        "p50_ms":round(statistics.median(xs),6) if xs else 0.0,
        "p90_ms":round(quantile(xs,.90),6),
        "p95_ms":round(quantile(xs,.95),6),
        "p99_ms":round(quantile(xs,.99),6),
        "max_ms":round(max(xs),6) if xs else 0.0,
        "mean_ms":round(statistics.mean(xs),6) if xs else 0.0,
    }


def timed(fn):
    t0 = time.perf_counter_ns(); out = fn()
    return out, (time.perf_counter_ns()-t0)/1_000_000.0


def seed(path: str, rows: int) -> StateLedger:
    ledger = StateLedger(path)
    ledger.append_event(
        event_id="scheduler", idem="scheduler", base_epoch=ledger.epoch,
        event_type="DATABASE_PULSE_SCHEDULER_SET", writer="bench",
        ops=[{
            "op":"SET","domain":"pulse_control","key":"scheduler",
            "value":{"enabled":True,"reason":"bench","authority":"PERSISTED_RUNTIME_CONTROL"},
            "epistemic":"KNOWN","status":"CURRENT",
        }], committed_at="2026-08-10T04:30:00Z",
    )
    ops = [{
        "op":"SET","domain":"memory","key":f"k{i:08d}",
        "value":{"i":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0,"payload":"x"*24},
        "epistemic":"KNOWN","status":"CURRENT",
    } for i in range(rows)]
    ops.append({
        "op":"SET","domain":"memory","key":"zzzz-critical",
        "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
        "epistemic":"KNOWN","status":"CURRENT",
    })
    ledger.append_event(
        event_id="seed", idem="seed", base_epoch=ledger.epoch,
        event_type="PULSE_V6_BENCH_SEED", writer="bench", ops=ops,
        committed_at="2026-08-10T04:30:01Z",
    )
    return ledger


def db_bytes(path: str) -> int:
    total = 0
    for suffix in ("", "-wal", "-shm"):
        p = path + suffix
        if os.path.exists(p):
            total += os.path.getsize(p)
    return total


def run_semantic_v5(path: str, rows: int, repeats: int):
    ledger = seed(path, rows)
    try:
        runtime, init_ms = timed(lambda: DatabasePulseRuntimeV5(ledger))
        plane = UnifiedDBQueryPlane(ledger)
        prepared = plane.query(QuerySpec(
            query_id="v5-prepared", domains=("memory",), epistemic=("KNOWN",),
            limit=16, basis_epoch=ledger.epoch,
        ))
        start_epoch = ledger.epoch
        start_hash = ledger.semantic_state_hash
        lat = []
        focuses = []
        for i in range(repeats):
            r, ms = timed(lambda i=i: runtime.run_pulse(PulseSpec(
                pulse_id=f"v5-{i}", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=64, max_focus=1,
                reentry_mode="NO_REENTRY",
            ), committed_at=f"2026-08-10T04:31:{i%60:02d}Z"))
            lat.append(ms); focuses.append(list(r.focus_refs))
        prepared_survived = True
        try:
            plane.select_for_assembly(prepared)
        except StaleEpoch:
            prepared_survived = False
        return {
            "implementation":"CURRENT_MAIN_SEMANTIC_RUNTIME_V5",
            "initialization_ms":round(init_ms,6),
            "pulse_latency":stats(lat),
            "semantic_epoch_delta":ledger.epoch-start_epoch,
            "semantic_hash_changed":ledger.semantic_state_hash != start_hash,
            "prepared_query_receipt_survived":prepared_survived,
            "database_pulse_events":int(ledger.conn.execute(
                "SELECT COUNT(*) FROM events WHERE event_type='DATABASE_PULSE'"
            ).fetchone()[0]),
            "pulse_domain_rows":int(ledger.conn.execute(
                "SELECT COUNT(*) FROM state WHERE domain='pulse'"
            ).fetchone()[0]),
            "last_focus":focuses[-1] if focuses else [],
            "db_bytes":db_bytes(path),
        }
    finally:
        ledger.close()


def run_v6(path: str, rows: int, repeats: int, audit_every: int, label: str):
    ledger = seed(path, rows)
    try:
        runtime, init_ms = timed(lambda: DatabasePulseExecutionPlaneV6(ledger, now="init"))
        plane = UnifiedDBQueryPlane(ledger)
        prepared = plane.query(QuerySpec(
            query_id=f"{label}-prepared", domains=("memory",), epistemic=("KNOWN",),
            limit=16, basis_epoch=ledger.epoch,
        ))
        start_epoch = ledger.epoch
        start_hash = ledger.semantic_state_hash
        start_trace = ledger.trace_root_hash
        lat = []
        integrity_modes = []
        focuses = []
        for i in range(repeats):
            r, ms = timed(lambda i=i: runtime.run_pulse(PulseSpecV6(
                invocation_id=f"{label}-{i}", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=64, max_focus=1,
                max_source_events=32, reentry_mode="NO_REENTRY",
                full_audit_every=audit_every,
            ), now=f"{label}-{i}"))
            lat.append(ms); integrity_modes.append(r.integrity_mode); focuses.append(list(r.focus_refs))
        prepared_survived = bool(plane.select_for_assembly(prepared)["selected"])
        return {
            "implementation":label,
            "audit_every":audit_every,
            "initialization_ms":round(init_ms,6),
            "pulse_latency":stats(lat),
            "semantic_epoch_delta":ledger.epoch-start_epoch,
            "semantic_hash_changed":ledger.semantic_state_hash != start_hash,
            "trace_root_changed":ledger.trace_root_hash != start_trace,
            "prepared_query_receipt_survived":prepared_survived,
            "database_pulse_events":int(ledger.conn.execute(
                "SELECT COUNT(*) FROM events WHERE event_type='DATABASE_PULSE'"
            ).fetchone()[0]),
            "pulse_domain_rows":int(ledger.conn.execute(
                "SELECT COUNT(*) FROM state WHERE domain='pulse'"
            ).fetchone()[0]),
            "execution_receipts":int(ledger.conn.execute(
                "SELECT COUNT(*) FROM pulse_execution_receipts_v6"
            ).fetchone()[0]),
            "integrity_mode_counts":{m:integrity_modes.count(m) for m in sorted(set(integrity_modes))},
            "last_focus":focuses[-1] if focuses else [],
            "db_bytes":db_bytes(path),
            "wal_multiwriter_gate":runtime.sqlite_wal_multiwriter_safety(),
        }
    finally:
        ledger.close()


def benchmark(rows: int, repeats: int):
    with tempfile.TemporaryDirectory() as td:
        base = str(Path(td)/"v5.sqlite")
        strict = str(Path(td)/"v6-strict.sqlite")
        layered = str(Path(td)/"v6-layered.sqlite")
        return {
            "rows":rows,
            "repeats":repeats,
            "semantic_v5":run_semantic_v5(base, rows, repeats),
            "v6_full_audit_each_pulse":run_v6(strict, rows, repeats, 1, "V6_FULL_AUDIT_EACH_PULSE"),
            "v6_layered_audit":run_v6(layered, rows, repeats, 32, "V6_LAYERED_AUDIT"),
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="100,1000,5000")
    ap.add_argument("--repeats", type=int, default=12)
    ap.add_argument("--output")
    a = ap.parse_args()
    sizes = [max(8, int(x)) for x in a.rows.split(",") if x.strip()]
    repeats = max(3, min(100, a.repeats))
    out = {
        "schema_version":"1.0",
        "benchmark_class":"MATCHED_PULSE_EXECUTION_TOPOLOGY_DIFFERENTIAL",
        "results":[benchmark(n, repeats) for n in sizes],
        "runtime_metadata":{
            "python":sys.version,
            "sqlite":__import__("sqlite3").sqlite_version,
            "platform":platform.platform(),
            "machine":platform.machine(),
        },
        "interpretation_rules":[
            "V6 must preserve semantic epoch/hash/trace root during idle endogenous Pulses.",
            "V5 semantic self-write is a measured topology difference, not by itself a cognitive-quality loss.",
            "Compare V5 against V6 full-audit-each-pulse before attributing latency changes to layered auditing.",
            "Layered V6 may claim lower hot cost only while focus-use verification and periodic/global audit gates remain intact.",
        ],
        "limitations":[
            "Synthetic memory fixture; not live-FRANK downstream answer/tool quality.",
            "No PostgreSQL/search-engine comparison in this benchmark.",
            "Filesystem/WAL byte counts are platform and checkpoint-state dependent.",
            "Final multiwriter acceptance requires a SQLite family with the WAL-reset bug fix and exact target-host execution.",
        ],
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if a.output:
        p = Path(a.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
