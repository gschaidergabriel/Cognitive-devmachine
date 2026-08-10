#!/usr/bin/env python3
from __future__ import annotations

"""Matched engineering benchmark for the U12 + authoritative-rank-index Pulse V4.

Narrow claims under test:
H1: fresh V4 snapshot bootstrap has zero historical U12 delta backlog;
H2: idle endogenous Pulses do not advance canonical StateLedger semantic epoch/root;
H3: bounded rank selection preserves the high-salience late key;
H4: one new semantic event is bridged/acknowledged exactly once in the next coherent Pulse;
H5: large post-boot bursts require bounded zero-cognition catch-up before cognition;
H6: full canonical StateLedger integrity recomputation remains a visible scaling cost.

Not a benchmark against external database products and not final live-FRANK/Andreas acceptance.
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
from research_entity.runtime.database_pulse_runtime_v4 import DatabasePulseRuntimeV4  # noqa:E402


def q(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    return ys[min(len(ys)-1, max(0, math.ceil(p*len(ys))-1))]


def stats(xs: list[float]) -> dict[str, float | int]:
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6),
        "p50_ms": round(statistics.median(xs), 6),
        "p90_ms": round(q(xs, .90), 6),
        "p95_ms": round(q(xs, .95), 6),
        "p99_ms": round(q(xs, .99), 6),
        "max_ms": round(max(xs), 6),
        "mean_ms": round(statistics.mean(xs), 6),
    }


def timed(fn):
    t0 = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns()-t0)/1_000_000.0


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
        event_id="seed",idem="seed",base_epoch=0,event_type="V4_BENCH_SEED",writer="benchmark",
        ops=ops,committed_at="2026-08-10T01:50:00Z",
    )
    return ledger


def benchmark(rows: int, repeat: int, catchup_batch: int) -> dict:
    with tempfile.TemporaryDirectory() as td:
        ledger = seed(str(Path(td)/"v4.sqlite"), rows)
        runtime, init_ms = timed(
            lambda: DatabasePulseRuntimeV4(ledger, now="2026-08-10T01:50:01Z")
        )
        bootstrap_backlog = runtime.backlog_count()
        bootstrap_state = runtime._state()
        bootstrap_meta = runtime._bridge_meta()
        semantic_epoch = ledger.epoch
        semantic_hash = ledger.semantic_state_hash
        trace_hash = ledger.trace_root_hash

        first, first_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=semantic_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=1,
            max_deltas=catchup_batch,
            reentry_mode="NO_REENTRY",
            now="first",
        ))
        if first.focus_refs != ("memory:zzzz-critical",):
            raise AssertionError(first.focus_refs)

        plane = UnifiedDBQueryPlane(ledger)
        prepared = plane.query(QuerySpec(
            "prepared", domains=("memory",), limit=16, basis_epoch=ledger.epoch
        ))
        idle_lat = []
        for i in range(repeat):
            out, ms = timed(lambda i=i: runtime.run_pulse(
                basis_epoch=semantic_epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=catchup_batch,
                reentry_mode="NO_REENTRY",
                now=f"idle-{i}",
            ))
            idle_lat.append(ms)
            if out.applied_delta_count != 0:
                raise AssertionError("idle Pulse applied semantic delta")
            if out.model_call_count or out.tool_call_count or out.effect_count:
                raise AssertionError("idle zero-model/tool/effect invariant failed")
        prepared_selected = plane.select_for_assembly(prepared)
        idle_epoch = ledger.epoch
        idle_hash = ledger.semantic_state_hash
        idle_trace = ledger.trace_root_hash

        integrity_lat = []
        for _ in range(repeat):
            runtime._reset_integrity_cache()
            _, ms = timed(runtime._full_ledger_integrity)
            integrity_lat.append(ms)
            runtime._reset_integrity_cache()

        ledger.append_event(
            event_id="delta",idem="delta",base_epoch=ledger.epoch,event_type="MEMORY_UPDATE",
            writer="benchmark",
            ops=[{
                "op":"SET","domain":"memory","key":"hot-new","value":{"priority":1.0},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
            committed_at="2026-08-10T01:50:02Z",
        )
        delta_epoch = ledger.epoch
        delta, delta_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=delta_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=2,
            max_deltas=catchup_batch,
            reentry_mode="NO_REENTRY",
            now="delta-pulse",
        ))

        # Post-boot burst exercises coherence gate and bounded zero-cognition catch-up.
        burst_ops = [
            {
                "op":"SET","domain":"memory","key":f"burst-{i:05d}",
                "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
            }
            for i in range(catchup_batch*2 + 17)
        ]
        ledger.append_event(
            event_id="burst",idem="burst",base_epoch=ledger.epoch,event_type="BURST",
            writer="benchmark",ops=burst_ops,committed_at="2026-08-10T01:50:03Z",
        )
        burst_epoch = ledger.epoch
        blocked = False
        try:
            runtime.run_pulse(
                basis_epoch=burst_epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=catchup_batch,
                reentry_mode="NO_REENTRY",
                now="should-block",
            )
        except Exception:
            blocked = True
        catchup_lat = []
        catchup_applied = 0
        while runtime.backlog_count() > catchup_batch:
            r, ms = timed(lambda: runtime.drain_backlog(
                basis_epoch=burst_epoch,max_deltas=catchup_batch,now=f"catchup-{len(catchup_lat)}"
            ))
            catchup_lat.append(ms)
            catchup_applied += r.applied_delta_count
            if r.model_call_count or r.tool_call_count or r.effect_count:
                raise AssertionError("catchup performed model/tool/effect call")
        final, final_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=burst_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=1,
            max_deltas=catchup_batch,
            reentry_mode="NO_REENTRY",
            now="post-catchup",
        ))

        result = {
            "rows": rows,
            "initialization_ms": round(init_ms,6),
            "bootstrap": {
                "backlog": bootstrap_backlog,
                "u12_source_epoch": int(bootstrap_state["source_epoch"]),
                "ledger_epoch": semantic_epoch,
                "bridge_mode": bootstrap_meta["bootstrap_mode"],
                "bridge_last_event_seq": int(bootstrap_meta["last_event_seq"]),
            },
            "first_cognitive_pulse_ms": round(first_ms,6),
            "idle_cognitive_pulse": stats(idle_lat),
            "full_integrity_only": stats(integrity_lat),
            "idle_invariants": {
                "semantic_epoch_advance": idle_epoch-semantic_epoch,
                "semantic_hash_unchanged": idle_hash==semantic_hash,
                "trace_hash_unchanged": idle_trace==trace_hash,
                "prepared_query_receipt_survived": bool(prepared_selected["selected"]),
                "late_salience_target_selected": first.focus_refs == ("memory:zzzz-critical",),
            },
            "single_delta": {
                "pulse_ms": round(delta_ms,6),
                "applied_delta_count": delta.applied_delta_count,
                "memory_update_observed_count": delta.memory_update_observed_count,
                "semantic_epoch_after_external_write": delta_epoch,
                "backlog_after": delta.backlog_after,
            },
            "burst_catchup": {
                "burst_delta_count": len(burst_ops),
                "cognition_blocked_before_catchup": blocked,
                "catchup_pulses": len(catchup_lat),
                "catchup_applied_total": catchup_applied,
                "catchup_latency": stats(catchup_lat) if catchup_lat else None,
                "final_cognitive_pulse_ms": round(final_ms,6),
                "final_backlog": runtime.backlog_count(),
                "final_focus": list(final.focus_refs),
                "semantic_epoch_after_catchup": ledger.epoch,
            },
            "rank_index_verify": runtime.rank_index.verify_index_semantics(
                domains=("memory",),max_candidates=64
            ),
        }
        ledger.close()
        return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rows',default='100,1000,10000')
    ap.add_argument('--repeat',type=int,default=7)
    ap.add_argument('--catchup-batch',type=int,default=512)
    ap.add_argument('--output')
    a=ap.parse_args()
    rows=[int(x) for x in a.rows.split(',') if x.strip()]
    repeat=max(1,min(30,a.repeat)); batch=max(8,min(4096,a.catchup_batch))
    results=[benchmark(n,repeat,batch) for n in rows]
    payload={
        "schema_version":"1.0",
        "benchmark_class":"CLAY_SELF_USE_ENGINEERING_DIFFERENTIAL",
        "implementation":"database_pulse_runtime_v4_u12_authoritative_rank_index",
        "results":results,
        "runtime_metadata":{
            "python":sys.version,
            "sqlite":sqlite3.sqlite_version,
            "platform":platform.platform(),
            "machine":platform.machine(),
        },
        "limitations":[
            "Synthetic StateLedger workload, not live-FRANK task accuracy.",
            "No external database product comparison; claims are internal architecture differentials only.",
            "Full canonical root recomputation remains intentionally enabled and may dominate latency at scale.",
            "SQLite JSON expression-index capability/version and write amplification require target-hardware validation.",
            "Hostinger execution is preliminary and cannot replace Andreas Ubuntu target acceptance.",
        ],
    }
    text=json.dumps(payload,ensure_ascii=False,indent=2)+'\n'
    if a.output:
        p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
    print(text,end='')

if __name__=='__main__': main()
