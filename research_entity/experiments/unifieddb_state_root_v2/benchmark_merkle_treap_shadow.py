#!/usr/bin/env python3
from __future__ import annotations

"""Matched root-maintenance benchmark: current exact root vs Merkle shadow.

This benchmark isolates only authenticated state-root maintenance. It does NOT claim a
whole-transaction speedup, does NOT change StateLedger authority, and does NOT compare
complete DBMS products. The current byte-exact semantic_state_hash remains canonical.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import sqlite3
import statistics
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "research_entity" / "harness" / "reference"))

from state_ledger import StateLedger, cjson, h, rawh  # type: ignore  # noqa: E402
from merkle_treap_shadow import MerkleTreapShadow, ROOT_VERSION  # noqa: E402

SEED = 20260810


def percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    p = (len(values) - 1) * q
    lo = math.floor(p)
    hi = math.ceil(p)
    if lo == hi:
        return values[lo]
    return values[lo] * (hi - p) + values[hi] * (p - lo)


def mkrow(i: int, *, revision: int = 0) -> dict[str, Any]:
    domain = f"domain_{i % 17:02d}"
    key = f"key_{i:08d}"
    value = {
        "i": i,
        "revision": revision,
        "payload": ("x" * 64) + f"-{i % 101:03d}",
    }
    epistemic = "KNOWN" if i % 29 else "CONFLICT"
    status = "CURRENT" if i % 41 else "SUPERSEDED"
    semantic_hash = h(
        {
            "domain": domain,
            "key": key,
            "value": value,
            "epistemic": epistemic,
            "status": status,
        }
    )
    return {
        "domain": domain,
        "key": key,
        "value": value,
        "epistemic": epistemic,
        "status": status,
        "domain_epoch": 1,
        "semantic_hash": semantic_hash,
    }


def load_state(ledger: StateLedger, rows: list[dict[str, Any]]) -> None:
    ledger.conn.execute("DELETE FROM state")
    ledger.conn.execute("DELETE FROM domain_epochs")
    domains = sorted({str(r["domain"]) for r in rows})
    ledger.conn.executemany(
        "INSERT INTO domain_epochs(domain,epoch) VALUES(?,1)",
        ((d,) for d in domains),
    )
    ledger.conn.executemany(
        "INSERT INTO state(domain,k,value_json,epistemic,status,domain_epoch,semantic_hash) VALUES(?,?,?,?,?,?,?)",
        (
            (
                r["domain"],
                r["key"],
                cjson(r["value"]),
                r["epistemic"],
                r["status"],
                r["domain_epoch"],
                r["semantic_hash"],
            )
            for r in rows
        ),
    )
    ledger._set("global_epoch", 1)
    ledger._set("semantic_chain_hash", rawh("benchmark-chain"))
    ledger._set("execution_chain_hash", rawh("benchmark-execution"))
    ledger.conn.commit()


def timing(fn, repeats: int) -> list[float]:
    out: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        fn()
        out.append((time.perf_counter_ns() - t0) / 1_000.0)
    return out


def summarize_us(xs: list[float]) -> dict[str, float]:
    return {
        "p50": statistics.median(xs),
        "p95": percentile(xs, 0.95),
        "p99": percentile(xs, 0.99),
        "mean": statistics.mean(xs),
        "min": min(xs),
        "max": max(xs),
    }


def run_size(n: int, updates: int, repeats: int) -> dict[str, Any]:
    rng = random.Random(SEED + n)
    rows = [mkrow(i) for i in range(n)]
    by_id = {i: rows[i] for i in range(n)}

    with StateLedger(":memory:") as ledger:
        load_state(ledger, rows)
        exact_streaming = ledger._semantic_state_hash_streaming()
        exact_legacy = ledger._roots_legacy()[0]
        exact_equivalent = exact_streaming == exact_legacy
        full_lat = timing(ledger._semantic_state_hash_streaming, repeats)

        t0 = time.perf_counter_ns()
        shadow = MerkleTreapShadow.rebuild(rows)
        build_us = (time.perf_counter_ns() - t0) / 1_000.0

        update_lat: list[float] = []
        depths: list[int] = []
        for revision in range(1, updates + 1):
            i = rng.randrange(n)
            row = mkrow(i, revision=revision)
            by_id[i] = row
            t1 = time.perf_counter_ns()
            receipt = shadow.upsert(row)
            update_lat.append((time.perf_counter_ns() - t1) / 1_000.0)
            depths.append(int(receipt["path_depth"]))

        # Explicit new-key insertion path, since StateLedger SET may create a new key.
        for extra in range(32):
            i = n + extra
            row = mkrow(i, revision=updates + extra + 1)
            by_id[i] = row
            t1 = time.perf_counter_ns()
            receipt = shadow.upsert(row)
            update_lat.append((time.perf_counter_ns() - t1) / 1_000.0)
            depths.append(int(receipt["path_depth"]))

        final_rows = list(by_id.values())
        t2 = time.perf_counter_ns()
        verification = shadow.verify_rebuild(final_rows)
        verify_rebuild_us = (time.perf_counter_ns() - t2) / 1_000.0

        shuffled = final_rows[:]
        rng.shuffle(shuffled)
        order_independent = (
            MerkleTreapShadow.rebuild(shuffled).state_merkle_root
            == shadow.state_merkle_root
        )

        domain_epochs = {d: 1 for d in sorted({r["domain"] for r in final_rows})}
        wrapper = shadow.wrapper_root(
            global_epoch=updates + 1,
            domain_epochs=domain_epochs,
            semantic_chain_hash=rawh("benchmark-chain-after-updates"),
        )

    full = summarize_us(full_lat)
    incremental = summarize_us(update_lat)
    return {
        "rows_initial": n,
        "rows_final": len(final_rows),
        "mutating_updates": updates,
        "new_key_inserts": 32,
        "current_exact_root": {
            "streaming_equals_legacy": exact_equivalent,
            "root": exact_streaming,
            "latency_us": full,
            "complexity_observed": "O(N)_FULL_STATE_SCAN",
        },
        "merkle_shadow": {
            "root_version": ROOT_VERSION,
            "build_us": build_us,
            "incremental_latency_us": incremental,
            "path_depth_mean": statistics.mean(depths),
            "path_depth_max": max(depths),
            "rebuild_verification_us": verify_rebuild_us,
            "rebuild_verified": bool(verification["verified"]),
            "order_independent_rebuild": order_independent,
            "state_merkle_root": shadow.state_merkle_root,
            "wrapper_root": wrapper,
            "node_count": shadow.node_count,
        },
        "hash_maintenance_speedup_p50_x": full["p50"] / incremental["p50"],
        "claim_boundary": (
            "hash-maintenance component only; not total transaction speedup; "
            "Merkle root is non-canonical research shadow"
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="1000,5000,20000,50000")
    ap.add_argument("--updates", type=int, default=500)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--output")
    args = ap.parse_args()
    sizes = [int(x) for x in args.sizes.split(",") if x.strip()]
    results = [run_size(n, max(1, args.updates), max(1, args.repeats)) for n in sizes]
    payload = {
        "schema_version": "1.0",
        "benchmark": "UNIFIEDDB_STATE_ROOT_V2_MERKLE_SHADOW",
        "evidence_class": "EXECUTED_ENGINEERING_COMPONENT_BENCHMARK",
        "seed": SEED,
        "environment": {
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "results": results,
        "promotion_gate": {
            "canonical_hash_changed": False,
            "required_before_any_hash_v2_migration": [
                "event/replay/snapshot compatibility contract",
                "crash/restart rebuild equivalence",
                "target Ubuntu benchmark",
                "proof semantics and corruption falsifiers",
                "rollback to current byte-exact root",
                "explicit owner-authorized versioned migration",
            ],
        },
        "limitations": [
            "Synthetic state rows; not current Clay/Frank production state distribution.",
            "Compares authenticated hash-maintenance components, not complete DB transactions or DBMS products.",
            "Python object-tree memory/layout is a research prototype, not the final storage representation.",
            "The Merkle shadow commits to the same semantic row content but intentionally does not equal the current byte-exact semantic_state_hash value.",
        ],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
