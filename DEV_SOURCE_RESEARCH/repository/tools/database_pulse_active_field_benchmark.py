#!/usr/bin/env python3
from __future__ import annotations

"""Benchmark Pulse Active Field V2 against bounded lexical and wide correctness references.

The wide arm is a correctness reference on the H1 StateLedger query plane, not a general
external database benchmark. Active Field is a derived/rebuildable preprocessor projection.
"""

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa: E402
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane  # noqa: E402
from research_entity.runtime.database_pulse_active_field_v2 import PulseActiveFieldV2, signal_score  # noqa: E402


def q(xs: list[float], p: float) -> float:
    if not xs:
        return 0.0
    ys = sorted(xs)
    return ys[min(len(ys)-1, max(0, math.ceil(p*len(ys))-1))]


def stats(xs: list[float]) -> dict[str, Any]:
    return {
        "n": len(xs),
        "min_ms": round(min(xs), 6) if xs else 0.0,
        "p50_ms": round(statistics.median(xs), 6) if xs else 0.0,
        "p90_ms": round(q(xs, .90), 6),
        "p95_ms": round(q(xs, .95), 6),
        "p99_ms": round(q(xs, .99), 6),
        "max_ms": round(max(xs), 6) if xs else 0.0,
        "mean_ms": round(statistics.mean(xs), 6) if xs else 0.0,
    }


def timed(fn: Callable[[], Any]):
    t0 = time.perf_counter_ns()
    out = fn()
    return out, (time.perf_counter_ns()-t0)/1_000_000.0


def seed(rows: int) -> StateLedger:
    ledger = StateLedger()
    ops = []
    for i in range(rows):
        ops.append({
            "op":"SET", "domain":"memory", "key":f"k{i:06d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN", "status":"CURRENT",
        })
    ops.append({
        "op":"SET", "domain":"memory", "key":"zzzzzz-critical",
        "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
        "epistemic":"KNOWN", "status":"CURRENT",
    })
    ledger.append_event(
        event_id="active-field-benchmark-seed", idem="active-field-benchmark-seed",
        base_epoch=ledger.epoch, event_type="BENCHMARK_SEED", writer="benchmark",
        ops=ops, committed_at="2026-08-10T00:40:00Z",
    )
    return ledger


def focus_from_query(receipt) -> str | None:
    known = [r for r in receipt.rows if r["status"]=="CURRENT" and r["epistemic"]=="KNOWN"]
    ranked = []
    for row in known:
        score, _ = signal_score(row.get("value"))
        ranked.append((score, f"{row['domain']}:{row['key']}", row["semantic_hash"]))
    ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
    return ranked[0][1] if ranked else None


def benchmark(*, rows: int, bounded: int, repeats: int, delta_updates: int):
    if rows + 1 > 4096:
        raise ValueError("rows must remain <=4095 for the wide QueryPlane correctness arm")
    ledger = seed(rows)
    qp = UnifiedDBQueryPlane(ledger)
    target = "memory:zzzzzz-critical"
    try:
        field, build_ms = timed(lambda: PulseActiveFieldV2(ledger))
        rebuild, rebuild_ms = timed(lambda: field.full_rebuild(now="benchmark-rebuild"))
        verification = field.verify_projection()

        bounded_lat = []
        bounded_focus = None
        for i in range(repeats):
            receipt, ms = timed(lambda i=i: qp.query(QuerySpec(
                query_id=f"bounded-{i}", domains=("memory",), statuses=("CURRENT",),
                epistemic=("KNOWN",), limit=bounded, basis_epoch=ledger.epoch,
                purpose="BOUNDED_LEXICAL_REFERENCE",
            )))
            bounded_lat.append(ms)
            bounded_focus = focus_from_query(receipt)

        wide_lat = []
        wide_focus = None
        for i in range(repeats):
            receipt, ms = timed(lambda i=i: qp.query(QuerySpec(
                query_id=f"wide-{i}", domains=("memory",), statuses=("CURRENT",),
                epistemic=("KNOWN",), limit=rows+1, basis_epoch=ledger.epoch,
                purpose="WIDE_CORRECTNESS_REFERENCE",
            )))
            wide_lat.append(ms)
            wide_focus = focus_from_query(receipt)

        active_lat = []
        active_focus = None
        for i in range(repeats):
            selection, ms = timed(lambda i=i: field.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=bounded, max_focus=1, reentry_mode="NO_REENTRY",
                now=f"select-{i}",
            ))
            active_lat.append(ms)
            active_focus = selection.focus_refs[0] if selection.focus_refs else None

        delta_refresh_lat = []
        touched_counts = []
        for i in range(delta_updates):
            key = f"k{i % rows:06d}"
            ledger.append_event(
                event_id=f"delta-{i}", idem=f"delta-{i}", base_epoch=ledger.epoch,
                event_type="BENCHMARK_DELTA", writer="benchmark",
                ops=[{
                    "op":"SET", "domain":"memory", "key":key,
                    "value":{"fact":i,"priority":0.25 if i % 2 else 0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
                    "epistemic":"KNOWN", "status":"CURRENT",
                }], committed_at=f"2026-08-10T00:41:{i%60:02d}Z",
            )
            result, ms = timed(lambda i=i: field.refresh(now=f"delta-refresh-{i}"))
            delta_refresh_lat.append(ms)
            touched_counts.append(int(result.get("touched_refs", -1)))

        final_selection = field.select(
            source_domains=("memory",), basis_epoch=ledger.epoch,
            max_candidates=bounded, max_focus=1, reentry_mode="NO_REENTRY", now="final",
        )
        final_verify = field.verify_projection()
        active_stats = stats(active_lat)
        wide_stats = stats(wide_lat)
        speedup = (
            wide_stats["p50_ms"] / active_stats["p50_ms"]
            if active_stats["p50_ms"] > 0 else None
        )
        return {
            "schema_version":"1.0",
            "benchmark_class":"PULSE_ACTIVE_FIELD_ENGINEERING_PROXY",
            "fixture":{"state_rows":rows+1,"low_rows":rows,"candidate_budget":bounded,"repeats":repeats,"delta_updates":delta_updates},
            "correctness":{
                "expected_focus":target,
                "bounded_lexical_focus":bounded_focus,
                "wide_reference_focus":wide_focus,
                "active_field_focus":active_focus,
                "final_active_field_focus":final_selection.focus_refs[0] if final_selection.focus_refs else None,
                "bounded_lexical_correct":bounded_focus==target,
                "wide_reference_correct":wide_focus==target,
                "active_field_correct":active_focus==target,
                "projection_verify_initial":verification,
                "projection_verify_final":final_verify,
                "all_delta_refreshes_touched_one_ref":all(x==1 for x in touched_counts),
            },
            "latency":{
                "active_field_object_init_ms":round(build_ms,6),
                "cold_full_rebuild_ms":round(rebuild_ms,6),
                "bounded_lexical_query_only":stats(bounded_lat),
                "wide_query_plus_decode_only":stats(wide_lat),
                "active_field_refresh_plus_select":active_stats,
                "delta_refresh_only":stats(delta_refresh_lat),
                "wide_to_active_median_ratio":round(speedup,4) if speedup is not None else None,
            },
            "rebuild_receipt":rebuild,
            "authority_boundary":"projection ranking is context-only and never semantic truth/effect authority",
            "limitations":[
                "Synthetic H1 StateLedger fixture; no live-FRANK downstream task quality measured.",
                "Wide reference query latency excludes Python salience-ranking time, so the comparison is conservative against Active Field.",
                "StateLedger event-write cost is excluded from delta_refresh_only; this isolates projection-maintenance cost.",
                "This benchmark does not claim superiority over general database systems.",
            ],
        }
    finally:
        ledger.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=3000)
    ap.add_argument("--bounded", type=int, default=64)
    ap.add_argument("--repeats", type=int, default=200)
    ap.add_argument("--delta-updates", type=int, default=100)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = benchmark(
        rows=max(100, min(4095, args.rows)),
        bounded=max(8, min(512, args.bounded)),
        repeats=max(10, args.repeats),
        delta_updates=max(1, args.delta_updates),
    )
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")
    print(text,end="")


if __name__ == "__main__":
    main()
