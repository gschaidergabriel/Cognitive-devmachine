#!/usr/bin/env python3
from __future__ import annotations

"""Matched semantic-safety contract benchmark: raw SQLite vs Clay typed gate.

Purpose
-------
Falsify an unfair claim that Clay's semantic-safety accuracy comes merely from comparing
against a deliberately naive row store.  The conventional SQLite arm receives the SAME
admission contract as the Clay gate and is allowed to enforce it with indexed SQL.

This is intentionally a gate-level benchmark.  Canonical row/hash construction is shared
preprocessing and excluded from both timed arms because stock SQLite has no built-in
SHA-256.  The question is whether the admission semantics themselves are uniquely
accurate to Clay (counterhypothesis: no), and what execution overhead each representation
has once all receipt fields exist.

No arm mints truth or effect authority.  A PASS means only "context is admissible under
this declared contract".
"""

from dataclasses import dataclass
import argparse
import json
import math
from pathlib import Path
import platform
import random
import sqlite3
import statistics
import time
from typing import Iterable

SEED = 20260810

CLASSES = (
    "SAFE",
    "STATE_EPOCH_STALE",
    "STATE_HASH_STALE",
    "GRAPH_LAG",
    "GRAPH_FUTURE",
    "AMBIGUOUS",
    "UNVERIFIED",
    "TAMPERED_COUNT",
    "TAMPERED_HASH",
)


@dataclass(frozen=True)
class Case:
    case_id: int
    fault_class: str
    current_state_epoch: int
    basis_epoch: int
    current_state_hash: str
    receipt_state_hash: str
    graph_source_epoch: int
    graph_verified: int
    ambiguous_heads: int
    expected_row_count: int
    actual_row_count: int
    expected_rows_hash: str
    actual_rows_hash: str
    expected_admit: int


def _pct(xs: list[float], q: float) -> float:
    ys = sorted(xs)
    p = (len(ys) - 1) * q
    lo = math.floor(p)
    hi = math.ceil(p)
    return ys[lo] if lo == hi else ys[lo] * (hi - p) + ys[hi] * (p - lo)


def _lat(xs: list[float]) -> dict[str, float]:
    return {
        "p50_ns": statistics.median(xs),
        "p95_ns": _pct(xs, 0.95),
        "p99_ns": _pct(xs, 0.99),
        "mean_ns": statistics.mean(xs),
        "min_ns": min(xs),
        "max_ns": max(xs),
    }


def make_case(case_id: int, fault_class: str) -> Case:
    epoch = 1000 + case_id
    state_hash = f"state-{case_id:08d}"
    rows_hash = f"rows-{case_id:08d}"
    values = dict(
        current_state_epoch=epoch,
        basis_epoch=epoch,
        current_state_hash=state_hash,
        receipt_state_hash=state_hash,
        graph_source_epoch=epoch,
        graph_verified=1,
        ambiguous_heads=0,
        expected_row_count=8,
        actual_row_count=8,
        expected_rows_hash=rows_hash,
        actual_rows_hash=rows_hash,
    )
    if fault_class == "STATE_EPOCH_STALE":
        values["basis_epoch"] = epoch - 1
    elif fault_class == "STATE_HASH_STALE":
        values["receipt_state_hash"] = state_hash + "-old"
    elif fault_class == "GRAPH_LAG":
        values["graph_source_epoch"] = epoch - 1
    elif fault_class == "GRAPH_FUTURE":
        values["graph_source_epoch"] = epoch + 1
    elif fault_class == "AMBIGUOUS":
        values["ambiguous_heads"] = 1
    elif fault_class == "UNVERIFIED":
        values["graph_verified"] = 0
    elif fault_class == "TAMPERED_COUNT":
        values["actual_row_count"] = 7
    elif fault_class == "TAMPERED_HASH":
        values["actual_rows_hash"] = rows_hash + "-tampered"
    elif fault_class != "SAFE":
        raise ValueError(fault_class)
    return Case(case_id=case_id, fault_class=fault_class, expected_admit=int(fault_class == "SAFE"), **values)


def build_cases(per_class: int) -> list[Case]:
    cases: list[Case] = []
    cid = 0
    for cls in CLASSES:
        for _ in range(per_class):
            cases.append(make_case(cid, cls))
            cid += 1
    random.Random(SEED).shuffle(cases)
    return cases


def clay_typed_gate(c: Case) -> int:
    # Mirrors the safety decisions in UnifiedDBQueryPlane.select_for_assembly +
    # UnifiedClayContextAssembler after canonical receipt/hash fields have been computed.
    if c.basis_epoch != c.current_state_epoch:
        return 0
    if c.receipt_state_hash != c.current_state_hash:
        return 0
    if c.ambiguous_heads:
        return 0
    if not c.graph_verified:
        return 0
    if c.graph_source_epoch != c.basis_epoch:
        return 0
    if c.actual_row_count != c.expected_row_count:
        return 0
    if c.actual_rows_hash != c.expected_rows_hash:
        return 0
    return 1


def setup_sqlite(cases: Iterable[Case]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript(
        """
        CREATE TABLE context_candidate(
          case_id INTEGER PRIMARY KEY,
          fault_class TEXT NOT NULL,
          current_state_epoch INTEGER NOT NULL,
          basis_epoch INTEGER NOT NULL,
          current_state_hash TEXT NOT NULL,
          receipt_state_hash TEXT NOT NULL,
          graph_source_epoch INTEGER NOT NULL,
          graph_verified INTEGER NOT NULL,
          ambiguous_heads INTEGER NOT NULL,
          expected_row_count INTEGER NOT NULL,
          actual_row_count INTEGER NOT NULL,
          expected_rows_hash TEXT NOT NULL,
          actual_rows_hash TEXT NOT NULL,
          expected_admit INTEGER NOT NULL
        );
        CREATE INDEX idx_context_candidate_gate
        ON context_candidate(
          case_id,
          current_state_epoch,
          basis_epoch,
          graph_source_epoch,
          graph_verified,
          ambiguous_heads
        );
        """
    )
    con.executemany(
        "INSERT INTO context_candidate VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            (
                c.case_id,
                c.fault_class,
                c.current_state_epoch,
                c.basis_epoch,
                c.current_state_hash,
                c.receipt_state_hash,
                c.graph_source_epoch,
                c.graph_verified,
                c.ambiguous_heads,
                c.expected_row_count,
                c.actual_row_count,
                c.expected_rows_hash,
                c.actual_rows_hash,
                c.expected_admit,
            )
            for c in cases
        ),
    )
    con.commit()
    return con


SQL_ONE = """
SELECT CASE WHEN
  basis_epoch = current_state_epoch
  AND receipt_state_hash = current_state_hash
  AND ambiguous_heads = 0
  AND graph_verified = 1
  AND graph_source_epoch = basis_epoch
  AND actual_row_count = expected_row_count
  AND actual_rows_hash = expected_rows_hash
THEN 1 ELSE 0 END
FROM context_candidate
WHERE case_id = ?
"""

SQL_BATCH = """
SELECT case_id, CASE WHEN
  basis_epoch = current_state_epoch
  AND receipt_state_hash = current_state_hash
  AND ambiguous_heads = 0
  AND graph_verified = 1
  AND graph_source_epoch = basis_epoch
  AND actual_row_count = expected_row_count
  AND actual_rows_hash = expected_rows_hash
THEN 1 ELSE 0 END AS admit
FROM context_candidate
ORDER BY case_id
"""


def confusion(expected: list[int], got: list[int]) -> dict[str, float | int]:
    tp = sum(e == 1 and g == 1 for e, g in zip(expected, got))
    tn = sum(e == 0 and g == 0 for e, g in zip(expected, got))
    fp = sum(e == 0 and g == 1 for e, g in zip(expected, got))
    fn = sum(e == 1 and g == 0 for e, g in zip(expected, got))
    n = len(expected)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": (tp + tn) / n,
        "precision": precision,
        "recall": recall,
        "false_accept_rate_unsafe": fp / max(1, tn + fp),
    }


def run(per_class: int, repeats: int) -> dict:
    cases = build_cases(per_class)
    by_id = {c.case_id: c for c in cases}
    expected = [by_id[i].expected_admit for i in sorted(by_id)]
    con = setup_sqlite(cases)

    # Correctness, full set.
    clay_got = [clay_typed_gate(by_id[i]) for i in sorted(by_id)]
    sql_rows = con.execute(SQL_BATCH).fetchall()
    sql_got = [int(r[1]) for r in sql_rows]
    dumb_got = [1] * len(expected)

    # Warm per-case latency. IDs are shuffled to avoid one easy contiguous pattern.
    order = list(by_id)
    random.Random(SEED + 1).shuffle(order)
    clay_lat: list[float] = []
    sql_lat: list[float] = []
    for _ in range(repeats):
        for case_id in order:
            c = by_id[case_id]
            t0 = time.perf_counter_ns()
            clay_typed_gate(c)
            clay_lat.append(float(time.perf_counter_ns() - t0))
            t0 = time.perf_counter_ns()
            con.execute(SQL_ONE, (case_id,)).fetchone()[0]
            sql_lat.append(float(time.perf_counter_ns() - t0))

    # Batch throughput highlights a DB's natural strength and avoids pretending that
    # Python->SQLite call overhead is intrinsic to SQL semantics.
    batch_clay: list[float] = []
    batch_sql: list[float] = []
    for _ in range(max(5, repeats * 5)):
        t0 = time.perf_counter_ns()
        [clay_typed_gate(by_id[i]) for i in sorted(by_id)]
        batch_clay.append(float(time.perf_counter_ns() - t0))
        t0 = time.perf_counter_ns()
        con.execute(SQL_BATCH).fetchall()
        batch_sql.append(float(time.perf_counter_ns() - t0))

    plan = [str(r) for r in con.execute("EXPLAIN QUERY PLAN " + SQL_ONE, (0,)).fetchall()]
    con.close()
    return {
        "schema_version": "1.0",
        "benchmark": "MATCHED_SQLITE_VS_CLAY_SEMANTIC_SAFETY_CONTRACT",
        "evidence_class": "EXECUTED_MATCHED_CONTRACT_ENGINEERING_BENCHMARK",
        "dataset": {
            "seed": SEED,
            "fault_classes": list(CLASSES),
            "cases_per_class": per_class,
            "cases": len(cases),
            "safe_cases": sum(expected),
            "unsafe_cases": len(expected) - sum(expected),
        },
        "correctness": {
            "naive_admit_all": confusion(expected, dumb_got),
            "raw_sqlite_matched_contract": confusion(expected, sql_got),
            "clay_typed_gate": confusion(expected, clay_got),
            "sqlite_equals_clay_decisions": sql_got == clay_got,
        },
        "latency": {
            "single_case_warm": {
                "raw_sqlite_matched_contract": _lat(sql_lat),
                "clay_typed_gate": _lat(clay_lat),
            },
            "full_batch": {
                "raw_sqlite_matched_contract": _lat(batch_sql),
                "clay_typed_gate": _lat(batch_clay),
                "cases_per_batch": len(cases),
            },
        },
        "sqlite_query_plan": plan,
        "interpretation_guard": [
            "If raw SQLite matches Clay correctness, Clay has no unique accuracy claim for this gate once the same semantics are implemented.",
            "Clay's remaining candidate value is typed semantic authority, provenance/receipt composition, replay/fail-closed integration and compilation of those contracts into efficient mechanisms.",
            "Hash construction is shared preprocessing here; this benchmark does not compare cryptographic hashing engines.",
            "This is not a whole-DBMS benchmark and not evidence of universal superiority for either arm.",
        ],
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=1000)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = run(max(1, args.per_class), max(1, args.repeats))
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
