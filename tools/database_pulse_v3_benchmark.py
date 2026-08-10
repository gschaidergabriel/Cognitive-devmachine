#!/usr/bin/env python3
from __future__ import annotations

"""Differential engineering benchmark for Database Pulse V3.

This benchmark measures narrow architecture claims, not universal database superiority:

H1  V3 preserves unrelated StateLedger QueryReceipts across idle endogenous Pulses.
H2  ActiveField preselection keeps a high-salience late key visible under a bounded budget.
H3  U12 delta acknowledgement remains bounded/atomic while Pulse execution stays zero-model.
H4  The deliberately retained full StateLedger integrity gate is likely O(N); report it
    explicitly rather than mislabeling the whole V3 hot path as O(delta).

Comparator `database_pulse_runtime_v2` is the current semantic-StateLedger active-field Pulse,
so both arms share salience-aware candidate generation.  The main differential is where Pulse
execution state is persisted.
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

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch  # noqa:E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa:E402
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec  # noqa:E402
from research_entity.runtime.database_pulse_runtime_v2 import DatabasePulseRuntimeV2  # noqa:E402
from research_entity.runtime.database_pulse_runtime_v3 import DatabasePulseRuntimeV3  # noqa:E402


def q(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, math.ceil(p * len(ys)) - 1))]


def stats(xs: list[float]) -> dict[str, object]:
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


def seed(path: str, rows: int) -> StateLedger:
    ledger = StateLedger(path)
    ops = []
    for i in range(rows):
        epi = "UNKNOWN" if i % 997 == 0 else ("CONFLICT" if i % 1543 == 0 else "KNOWN")
        ops.append({
            "op":"SET", "domain":"memory", "key":f"k{i:08d}",
            "value":{
                "i":i, "priority":0.0, "urgency":0.0, "salience":0.0,
                "novelty":0.0, "payload":"x" * 24,
            },
            "epistemic":epi, "status":"CURRENT",
        })
    ops.append({
        "op":"SET", "domain":"memory", "key":"zzzz-critical",
        "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
        "epistemic":"KNOWN", "status":"CURRENT",
    })
    ledger.append_event(
        event_id="bench-seed", idem="bench-seed", base_epoch=ledger.epoch,
        event_type="PULSE_V3_BENCH_SEED", writer="database-pulse-v3-benchmark", ops=ops,
        committed_at="2026-08-10T01:10:00Z",
    )
    return ledger


def measure_integrity(runtime: DatabasePulseRuntimeV3, repeat: int) -> dict[str, object]:
    lat = []
    for _ in range(repeat):
        t0 = time.perf_counter_ns()
        runtime._full_ledger_integrity()
        lat.append((time.perf_counter_ns() - t0) / 1_000_000)
    return stats(lat)


def arm_v2(path: str, rows: int, repeat: int) -> dict[str, object]:
    ledger = seed(path, rows)
    runtime = DatabasePulseRuntimeV2(ledger)
    runtime.set_scheduler(
        enabled=True, event_id="scheduler-v2", base_epoch=ledger.epoch,
        actor="bench", reason="bench", committed_at="2026-08-10T01:10:01Z",
    )
    runtime.run_pulse(
        PulseSpec("warm-v2", basis_epoch=ledger.epoch, source_domains=("memory",),
                  max_candidates=64, max_focus=1, reentry_mode="NO_REENTRY"),
        committed_at="2026-08-10T01:10:02Z",
    )
    plane = UnifiedDBQueryPlane(ledger)
    prepared = plane.query(QuerySpec(
        "prepared-v2", domains=("memory",), limit=16, basis_epoch=ledger.epoch
    ))
    before = ledger.epoch
    lat = []
    focus_ok = True
    for i in range(repeat):
        t0 = time.perf_counter_ns()
        out = runtime.run_pulse(
            PulseSpec(f"idle-v2-{i}", basis_epoch=ledger.epoch, source_domains=("memory",),
                      max_candidates=64, max_focus=1, reentry_mode="NO_REENTRY"),
        )
        lat.append((time.perf_counter_ns() - t0) / 1_000_000)
        focus_ok = focus_ok and out.focus_refs == ("memory:zzzz-critical",)
    survives = True
    try:
        plane.select_for_assembly(prepared)
    except StaleEpoch:
        survives = False
    out = {
        "idle_pulse": stats(lat),
        "semantic_epoch_advance_idle": ledger.epoch - before,
        "prepared_query_survives_idle": survives,
        "tail_critical_selected_every_time": focus_ok,
        "final_semantic_epoch": ledger.epoch,
    }
    ledger.close()
    return out


def arm_v3(path: str, rows: int, repeat: int) -> dict[str, object]:
    ledger = seed(path, rows)
    runtime = DatabasePulseRuntimeV3(ledger, now="2026-08-10T01:10:01Z")
    warm = runtime.run_pulse(
        basis_epoch=ledger.epoch, source_domains=("memory",), max_candidates=64,
        max_focus=1, max_deltas=4096, reentry_mode="NO_REENTRY",
        now="2026-08-10T01:10:02Z",
    )
    plane = UnifiedDBQueryPlane(ledger)
    prepared = plane.query(QuerySpec(
        "prepared-v3", domains=("memory",), limit=16, basis_epoch=ledger.epoch
    ))
    before = ledger.epoch
    semantic_hash = ledger.semantic_state_hash
    lat = []
    focus_ok = warm.focus_refs == ("memory:zzzz-critical",)
    for i in range(repeat):
        t0 = time.perf_counter_ns()
        out = runtime.run_pulse(
            basis_epoch=ledger.epoch, source_domains=("memory",), max_candidates=64,
            max_focus=1, max_deltas=32, reentry_mode="NO_REENTRY", now=f"idle-v3-{i}",
        )
        lat.append((time.perf_counter_ns() - t0) / 1_000_000)
        focus_ok = focus_ok and out.focus_refs == ("memory:zzzz-critical",)
        if out.model_call_count or out.tool_call_count or out.effect_count:
            raise AssertionError("zero-model/tool/effect idle invariant violated")
    survives = True
    try:
        plane.select_for_assembly(prepared)
    except StaleEpoch:
        survives = False
    if ledger.semantic_state_hash != semantic_hash:
        raise AssertionError("V3 idle Pulse changed semantic root")

    ledger.append_event(
        event_id="bench-delta", idem="bench-delta", base_epoch=ledger.epoch,
        event_type="BENCH_MEMORY_DELTA", writer="database-pulse-v3-benchmark",
        ops=[{
            "op":"SET", "domain":"memory", "key":"hot-new",
            "value":{"priority":1.0}, "epistemic":"KNOWN", "status":"CURRENT",
        }],
    )
    t0 = time.perf_counter_ns()
    delta = runtime.run_pulse(
        basis_epoch=ledger.epoch, source_domains=("memory",), max_candidates=64,
        max_focus=2, max_deltas=32, reentry_mode="NO_REENTRY", now="delta-v3",
    )
    delta_ms = (time.perf_counter_ns() - t0) / 1_000_000
    out = {
        "idle_pulse": stats(lat),
        "full_integrity_only": measure_integrity(runtime, repeat),
        "semantic_epoch_advance_idle": before - before,
        "prepared_query_survives_idle": survives,
        "tail_critical_selected_every_time": focus_ok,
        "warm_applied_delta_count": warm.applied_delta_count,
        "one_semantic_delta_pulse_ms": round(delta_ms, 6),
        "one_semantic_delta_applied_count": delta.applied_delta_count,
        "one_semantic_delta_memory_update_count": delta.memory_update_observed_count,
        "final_pulse_index": delta.pulse_index,
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
            v2 = arm_v2(str(Path(td) / "v2.sqlite"), rows, repeat)
            v3 = arm_v3(str(Path(td) / "v3.sqlite"), rows, repeat)
        results.append({
            "rows": rows,
            "semantic_active_field_v2": v2,
            "u12_active_field_v3": v3,
            "v3_vs_v2_idle_p50_ratio": round(
                float(v3["idle_pulse"]["p50_ms"]) /
                max(float(v2["idle_pulse"]["p50_ms"]), 1e-12), 6
            ),
            "h1_no_semantic_self_churn": (
                v3["semantic_epoch_advance_idle"] == 0
                and v3["prepared_query_survives_idle"] is True
            ),
            "h2_tail_salience_visible": v3["tail_critical_selected_every_time"],
            "h3_delta_ack_observed": (
                v3["one_semantic_delta_applied_count"] == 1
                and v3["one_semantic_delta_memory_update_count"] == 1
            ),
        })
    payload = {
        "schema_version": "1.0",
        "benchmark_class": "CLAY_SELF_USE_ENGINEERING_DIFFERENTIAL",
        "implementation": "database_pulse_runtime_v3_u12_active_field",
        "repeat": repeat,
        "results": results,
        "limitations": [
            "Reference Python/SQLite research candidates; not final one-module Frank binary.",
            "The comparator is the current semantic active-field Pulse v2, not an external database product.",
            "V3 intentionally retains full canonical StateLedger root recomputation per Pulse; scaling cost is reported rather than optimized away without an equivalent integrity mechanism.",
            "Synthetic memory fixtures do not establish live-FRANK answer quality or phenomenal consciousness.",
            "Hostinger evidence is preliminary and cannot replace Andreas target-system acceptance.",
        ],
        "runtime_metadata": {
            "python": sys.version,
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
