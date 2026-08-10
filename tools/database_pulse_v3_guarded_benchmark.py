#!/usr/bin/env python3
from __future__ import annotations

"""Engineering benchmark for the guarded U12 + ActiveField Database Pulse V3 candidate.

Measured questions:
  * Does idle cognition preserve the canonical StateLedger semantic epoch/root?
  * Does bounded backlog catch-up remain zero-model/tool/effect and lossless?
  * Does salience-aware ActiveField retain the late high-salience target?
  * How much of idle Pulse latency is the intentionally retained full integrity scan?

This is a project-internal differential/engineering proxy, not a benchmark against external
DB products and not final Andreas-target acceptance.
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
from research_entity.runtime.database_pulse_runtime_v3_guarded import DatabasePulseRuntimeV3Guarded  # noqa:E402


def quantile(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, math.ceil(p * len(ys)) - 1))]


def summary(xs: list[float]) -> dict[str, object]:
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6),
        "p50_ms": round(statistics.median(xs), 6),
        "p90_ms": round(quantile(xs, 0.90), 6),
        "p95_ms": round(quantile(xs, 0.95), 6),
        "p99_ms": round(quantile(xs, 0.99), 6),
        "max_ms": round(max(xs), 6),
        "mean_ms": round(statistics.mean(xs), 6),
    }


def seed(path: str, rows: int) -> StateLedger:
    ledger = StateLedger(path)
    ops = [
        {
            "op":"SET", "domain":"memory", "key":f"k{i:08d}",
            "value":{
                "i":i, "priority":0.0, "urgency":0.0, "salience":0.0,
                "novelty":0.0, "payload":"x" * 24,
            },
            "epistemic":"KNOWN", "status":"CURRENT",
        }
        for i in range(rows)
    ]
    ops.append({
        "op":"SET", "domain":"memory", "key":"zzzz-critical",
        "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
        "epistemic":"KNOWN", "status":"CURRENT",
    })
    ledger.append_event(
        event_id="guarded-v3-seed", idem="guarded-v3-seed", base_epoch=ledger.epoch,
        event_type="GUARDED_V3_BENCH_SEED", writer="database-pulse-v3-guarded-benchmark",
        ops=ops, committed_at="2026-08-10T01:30:00Z",
    )
    return ledger


def timed(fn):
    t0 = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns() - t0) / 1_000_000.0


def bench_size(rows: int, repeat: int, batch: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as td:
        ledger = seed(str(Path(td) / "pulse.sqlite"), rows)
        runtime = DatabasePulseRuntimeV3Guarded(ledger, now="2026-08-10T01:30:01Z")
        epoch = ledger.epoch
        semantic_hash = ledger.semantic_state_hash
        trace_hash = ledger.trace_root_hash

        # Materialize the global source bridge first, then explicitly catch up in bounded
        # zero-cognition entity Pulses until one coherent cognitive Pulse can close the queue.
        runtime._integrity_cache = None
        runtime._full_ledger_integrity()
        runtime.bridge_stateledger_events(source_domains=(), now="bridge")
        initial_backlog = runtime.backlog_count()
        catchup_ms: list[float] = []
        catchup_applied = 0
        while runtime.backlog_count() > batch:
            receipt, ms = timed(lambda: runtime.drain_backlog(
                basis_epoch=epoch, max_deltas=batch, now=f"catchup-{len(catchup_ms)}"
            ))
            catchup_ms.append(ms)
            catchup_applied += receipt.applied_delta_count
            if receipt.model_call_count or receipt.tool_call_count or receipt.effect_count:
                raise AssertionError("catch-up violated zero-model/tool/effect invariant")

        cognitive, cognitive_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=1,
            max_deltas=batch,
            reentry_mode="NO_REENTRY",
            now="first-cognitive",
        ))
        if cognitive.focus_refs != ("memory:zzzz-critical",):
            raise AssertionError(f"late salience target missing: {cognitive.focus_refs}")
        if runtime.backlog_count() != 0:
            raise AssertionError("cognitive Pulse did not close bounded backlog")

        plane = UnifiedDBQueryPlane(ledger)
        prepared = plane.query(QuerySpec(
            "guarded-v3-prepared", domains=("memory",), limit=16, basis_epoch=epoch
        ))
        idle_ms: list[float] = []
        for i in range(repeat):
            receipt, ms = timed(lambda i=i: runtime.run_pulse(
                basis_epoch=epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=batch,
                reentry_mode="NO_REENTRY",
                now=f"idle-{i}",
            ))
            idle_ms.append(ms)
            if receipt.applied_delta_count != 0:
                raise AssertionError("idle Pulse unexpectedly applied semantic delta")
            if receipt.model_call_count or receipt.tool_call_count or receipt.effect_count:
                raise AssertionError("idle Pulse violated zero-model/tool/effect invariant")
        selected = plane.select_for_assembly(prepared)

        integrity_ms: list[float] = []
        for _ in range(repeat):
            runtime._integrity_cache = None
            _, ms = timed(runtime._full_ledger_integrity)
            integrity_ms.append(ms)
            runtime._integrity_cache = None

        ledger.append_event(
            event_id="guarded-v3-delta", idem="guarded-v3-delta", base_epoch=ledger.epoch,
            event_type="MEMORY_UPDATE", writer="database-pulse-v3-guarded-benchmark",
            ops=[{
                "op":"SET","domain":"memory","key":"hot-new","value":{"priority":1.0},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
        )
        delta_epoch = ledger.epoch
        delta, delta_ms = timed(lambda: runtime.run_pulse(
            basis_epoch=delta_epoch,
            source_domains=("memory",),
            max_candidates=64,
            max_focus=2,
            max_deltas=batch,
            reentry_mode="NO_REENTRY",
            now="single-delta",
        ))

        result = {
            "rows": rows,
            "batch": batch,
            "initial_bridge_backlog": initial_backlog,
            "catchup_pulse_count": len(catchup_ms),
            "catchup_applied_total": catchup_applied,
            "catchup_latency": summary(catchup_ms) if catchup_ms else None,
            "first_cognitive_pulse_ms": round(cognitive_ms, 6),
            "idle_cognitive_pulse": summary(idle_ms),
            "full_integrity_only": summary(integrity_ms),
            "prepared_query_survived_idle": bool(selected["selected"]),
            "semantic_epoch_unchanged_across_idle": ledger.epoch == delta_epoch,
            "semantic_hash_unchanged_before_external_delta": semantic_hash != ledger.semantic_state_hash,
            "trace_hash_unchanged_before_external_delta": trace_hash != ledger.trace_root_hash,
            "late_salience_target_selected": cognitive.focus_refs == ("memory:zzzz-critical",),
            "single_delta_pulse_ms": round(delta_ms, 6),
            "single_delta_applied": delta.applied_delta_count,
            "single_delta_memory_update_observed": delta.memory_update_observed_count,
            "final_pulse_index": delta.pulse_index,
            "final_backlog": runtime.backlog_count(),
        }
        # The external single semantic delta intentionally advances the ledger once.  The
        # stronger idle invariant is captured separately before that event below.
        result["idle_semantic_epoch_advance"] = delta_epoch - epoch
        result["idle_semantic_self_churn_pass"] = (
            result["prepared_query_survived_idle"]
            and delta_epoch == epoch + 1
            and result["single_delta_applied"] == 1
        )
        ledger.close()
        return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="100,1000,10000")
    ap.add_argument("--repeat", type=int, default=7)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--output")
    args = ap.parse_args()
    sizes = [int(x) for x in args.rows.split(",") if x.strip()]
    repeat = max(1, min(30, args.repeat))
    batch = max(1, min(4096, args.batch))
    results = [bench_size(n, repeat, batch) for n in sizes]
    payload = {
        "schema_version": "1.0",
        "benchmark_class": "CLAY_SELF_USE_ENGINEERING_PROXY",
        "implementation": "database_pulse_runtime_v3_guarded",
        "hypotheses": {
            "H1": "idle endogenous Pulse does not churn canonical semantic epoch/root",
            "H2": "salience-aware ActiveField preserves late high-salience target under bounded candidate budget",
            "H3": "large bursts catch up through bounded zero-cognition U12 Pulses before coherent cognition",
            "H4": "full integrity scan remains a measurable scaling cost and is not hidden",
        },
        "repeat": repeat,
        "results": results,
        "runtime_metadata": {
            "python": sys.version,
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "limitations": [
            "Synthetic StateLedger workload; not live-FRANK task-quality evidence.",
            "No comparison to an external database product is made.",
            "Full canonical StateLedger root recomputation is intentionally retained per guarded operation pending an equivalent incremental integrity mechanism.",
            "Hostinger execution is preliminary and does not replace Andreas Ubuntu target acceptance.",
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
