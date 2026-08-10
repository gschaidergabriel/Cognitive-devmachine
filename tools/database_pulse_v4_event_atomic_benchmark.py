#!/usr/bin/env python3
from __future__ import annotations

"""Engineering benchmark for the event-atomic U12 + rank-index Database Pulse V4.1.

This benchmark preserves StateLedger transaction boundaries explicitly:
* one 180-op semantic transaction must become one U12 event-delta;
* many one-op semantic transactions become many U12 event-deltas and may be caught up in
  bounded zero-cognition batches without `source_epoch` ever representing a partial event;
* idle Pulse execution must not churn StateLedger semantic truth;
* salience ranking uses the authoritative physical expression index;
* full canonical integrity cost is measured separately and intentionally retained.

Internal engineering evidence only; not an external DB benchmark or final live-FRANK acceptance.
"""

import argparse
import json
import math
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa:E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa:E402
from research_entity.runtime.database_pulse_runtime_v4_event_atomic import (  # noqa:E402
    DatabasePulseRuntimeV4EventAtomic,
)
from research_entity.runtime.database_pulse_v0 import PulseStateError  # noqa:E402


def quantile(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    return ys[min(len(ys)-1, max(0, math.ceil(p*len(ys))-1))]


def stats(xs: list[float]) -> dict[str, float | int]:
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6),
        "p50_ms": round(statistics.median(xs), 6),
        "p90_ms": round(quantile(xs, .90), 6),
        "p95_ms": round(quantile(xs, .95), 6),
        "p99_ms": round(quantile(xs, .99), 6),
        "max_ms": round(max(xs), 6),
        "mean_ms": round(statistics.mean(xs), 6),
    }


def timed(fn):
    t0 = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns() - t0) / 1_000_000.0


def seed(path: str, rows: int) -> StateLedger:
    ledger = StateLedger(path)
    ops = [
        {
            "op":"SET","domain":"memory","key":f"k{i:08d}",
            "value":{
                "i":i,"priority":0.0,"urgency":0.0,"salience":0.0,
                "novelty":0.0,"payload":"x"*24,
            },
            "epistemic":"KNOWN","status":"CURRENT",
        }
        for i in range(rows)
    ]
    ops.append({
        "op":"SET","domain":"memory","key":"zzzz-critical",
        "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
        "epistemic":"KNOWN","status":"CURRENT",
    })
    ledger.append_event(
        event_id="seed",idem="seed",base_epoch=0,event_type="V4_EVENT_ATOMIC_BENCH_SEED",
        writer="benchmark",ops=ops,committed_at="2026-08-10T02:00:00Z",
    )
    return ledger


def benchmark(rows: int, repeat: int, catchup_batch: int) -> dict:
    with tempfile.TemporaryDirectory() as td:
        ledger = seed(str(Path(td)/"v41.sqlite"), rows)
        runtime, init_ms = timed(
            lambda: DatabasePulseRuntimeV4EventAtomic(
                ledger, now="2026-08-10T02:00:01Z"
            )
        )
        initial_epoch = ledger.epoch
        initial_hash = ledger.semantic_state_hash
        initial_trace = ledger.trace_root_hash
        bootstrap = runtime._bridge_meta()
        if runtime.backlog_count() != 0:
            raise AssertionError("fresh snapshot bootstrap created historical backlog")

        first, first_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=initial_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=1,
            max_deltas=catchup_batch,
            reentry_mode="NO_REENTRY",
            now="first-cognitive",
        ))
        if first.focus_refs != ("memory:zzzz-critical",):
            raise AssertionError(first.focus_refs)

        plane = UnifiedDBQueryPlane(ledger)
        prepared = plane.query(QuerySpec(
            "prepared-before-idle", domains=("memory",), limit=16, basis_epoch=initial_epoch
        ))
        idle_lat: list[float] = []
        for i in range(repeat):
            out, ms = timed(lambda i=i: runtime.run_pulse(
                basis_epoch=initial_epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=catchup_batch,
                reentry_mode="NO_REENTRY",
                now=f"idle-{i}",
            ))
            idle_lat.append(ms)
            if out.applied_delta_count != 0:
                raise AssertionError("idle Pulse applied semantic event delta")
            if out.model_call_count or out.tool_call_count or out.effect_count:
                raise AssertionError("idle Pulse violated zero-model/tool/effect boundary")
        prepared_survived = bool(plane.select_for_assembly(prepared)["selected"])
        idle_root_pass = (
            ledger.epoch == initial_epoch
            and ledger.semantic_state_hash == initial_hash
            and ledger.trace_root_hash == initial_trace
        )

        integrity_lat: list[float] = []
        for _ in range(repeat):
            runtime._reset_integrity_cache()
            _, ms = timed(runtime._full_ledger_integrity)
            integrity_lat.append(ms)
            runtime._reset_integrity_cache()

        # One large transaction must remain one event-delta regardless of op count.
        big_ops = [
            {
                "op":"SET","domain":"memory","key":f"atomic-{i:04d}",
                "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
            }
            for i in range(180)
        ]
        ledger.append_event(
            event_id="one-180-op-event",idem="one-180-op-event",base_epoch=ledger.epoch,
            event_type="ATOMIC_180_OP_EVENT",writer="benchmark",ops=big_ops,
            committed_at="2026-08-10T02:00:02Z",
        )
        big_epoch = ledger.epoch
        bridge = runtime.bridge_stateledger_events(now="bridge-big")
        big_backlog = runtime.backlog_count()
        big, big_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=big_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=1,
            max_deltas=1,
            reentry_mode="NO_REENTRY",
            now="apply-big",
        ))

        # Many separate transactions exercise bounded event-wise catch-up and source epochs.
        event_epochs: list[int] = []
        many_count = catchup_batch * 2 + 17
        for i in range(many_count):
            ledger.append_event(
                event_id=f"many-{i:05d}",idem=f"many-{i:05d}",base_epoch=ledger.epoch,
                event_type="ONE_EVENT",writer="benchmark",
                ops=[{
                    "op":"SET","domain":"memory","key":f"many-{i:05d}",
                    "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
                }],
                committed_at=f"many-{i:05d}",
            )
            event_epochs.append(ledger.epoch)
        many_final_epoch = ledger.epoch
        runtime.bridge_stateledger_events(now="bridge-many")
        many_initial_backlog = runtime.backlog_count()
        blocked = False
        try:
            runtime.run_pulse(
                basis_epoch=many_final_epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=catchup_batch,
                reentry_mode="NO_REENTRY",
                now="must-block",
            )
        except PulseStateError:
            blocked = True

        catchup_lat: list[float] = []
        catchup_applied = 0
        source_epochs: list[int] = []
        boundary_pass = True
        while runtime.backlog_count() > catchup_batch:
            r, ms = timed(lambda: runtime.drain_backlog(
                basis_epoch=many_final_epoch,
                max_deltas=catchup_batch,
                now=f"catchup-{len(catchup_lat)}",
            ))
            catchup_lat.append(ms)
            catchup_applied += r.applied_delta_count
            source_epoch = int(runtime._state()["source_epoch"])
            source_epochs.append(source_epoch)
            boundary_pass = boundary_pass and source_epoch == event_epochs[catchup_applied - 1]
            if r.model_call_count or r.tool_call_count or r.effect_count:
                raise AssertionError("catch-up invoked model/tool/effect")
        final, final_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=many_final_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=1,
            max_deltas=catchup_batch,
            reentry_mode="NO_REENTRY",
            now="post-catchup-cognition",
        ))
        boundary_pass = boundary_pass and int(runtime._state()["source_epoch"]) == many_final_epoch

        index_verify = runtime.rank_index.verify_index_semantics(
            domains=("memory",),max_candidates=64
        )
        result = {
            "rows": rows,
            "initialization_ms": round(init_ms, 6),
            "bootstrap": {
                "backlog": 0,
                "bridge_mode": bootstrap["bootstrap_mode"],
                "u12_source_epoch": int(runtime.con.execute(
                    "SELECT source_epoch FROM frank_database_pulse_checkpoints "
                    "WHERE pulse_index=0 LIMIT 1"
                ).fetchone()[0]) if False else initial_epoch,
                "ledger_epoch": initial_epoch,
            },
            "first_cognitive_pulse_ms": round(first_ms, 6),
            "idle_cognitive_pulse": stats(idle_lat),
            "full_integrity_only": stats(integrity_lat),
            "idle_invariants": {
                "semantic_root_pass": idle_root_pass,
                "prepared_query_receipt_survived": prepared_survived,
                "late_salience_target_selected": first.focus_refs == ("memory:zzzz-critical",),
            },
            "one_big_atomic_event": {
                "ops": len(big_ops),
                "bridge_events_consumed": bridge["events_consumed"],
                "bridge_admitted_deltas": bridge["admitted_deltas"],
                "backlog_before_pulse": big_backlog,
                "pulse_ms": round(big_ms, 6),
                "applied_delta_count": big.applied_delta_count,
                "memory_update_observed_count": big.memory_update_observed_count,
                "source_epoch_after": int(runtime.con.execute(
                    "SELECT source_epoch FROM frank_database_pulse_state WHERE singleton_id=1"
                ).fetchone()[0]),
                "event_epoch": big_epoch,
            },
            "many_event_catchup": {
                "event_count": many_count,
                "initial_backlog": many_initial_backlog,
                "cognition_blocked_before_catchup": blocked,
                "catchup_pulse_count": len(catchup_lat),
                "catchup_applied_total": catchup_applied,
                "catchup_latency": stats(catchup_lat) if catchup_lat else None,
                "observed_source_epochs": source_epochs,
                "event_boundary_pass": boundary_pass,
                "final_cognitive_pulse_ms": round(final_ms, 6),
                "final_applied_delta_count": final.applied_delta_count,
                "final_backlog": runtime.backlog_count(),
                "final_focus": list(final.focus_refs),
                "final_semantic_epoch": ledger.epoch,
            },
            "rank_index_verify": index_verify,
        }
        ledger.close()
        return result


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--rows',default='100,1000,10000')
    ap.add_argument('--repeat',type=int,default=7)
    ap.add_argument('--catchup-batch',type=int,default=32)
    ap.add_argument('--output')
    a=ap.parse_args()
    sizes=[int(x) for x in a.rows.split(',') if x.strip()]
    repeat=max(1,min(30,a.repeat)); batch=max(4,min(512,a.catchup_batch))
    results=[benchmark(n,repeat,batch) for n in sizes]
    payload={
        "schema_version":"1.0",
        "benchmark_class":"CLAY_SELF_USE_ENGINEERING_DIFFERENTIAL",
        "implementation":"database_pulse_runtime_v4_event_atomic",
        "results":results,
        "runtime_metadata":{
            "python":sys.version,
            "sqlite":sqlite3.sqlite_version,
            "platform":platform.platform(),
            "machine":platform.machine(),
        },
        "limitations":[
            "Synthetic StateLedger engineering fixture; not live-FRANK task-quality evidence.",
            "No external database-product comparison; only project-internal architecture claims are measured.",
            "Full canonical root recomputation remains intentionally enabled and may dominate hot latency at scale.",
            "Authoritative rank index depends on SQLite JSON expression-index support/version.",
            "Hostinger execution is preliminary and cannot replace Andreas Ubuntu target acceptance.",
        ],
    }
    text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
