#!/usr/bin/env python3
from __future__ import annotations

"""Bounded proxy benchmark for Pulse final-state effectivization.

This measures one concrete cost already present in SPM-S1: publishing a complete seed->segment
map for each coherent generation. It is not a FRANK outcome benchmark and cannot promote S2.
"""

import argparse
import hashlib
import json
import platform
import random
import resource
import sqlite3
import statistics
import sys
import time

from semantic_pulse_effectivizer_s2 import PulseDeltaEvent, effectivize_pulse_batch


def build_workload(seed_count: int, logical_count: int, event_count: int, rng_seed: int):
    rng = random.Random(rng_seed)
    hot = max(8, logical_count // 8)
    logical_to_seeds: dict[str, tuple[int, ...]] = {}
    seed_to_logicals: list[set[str]] = [set() for _ in range(seed_count)]
    for idx in range(logical_count):
        logical = f"L{idx:04d}"
        if idx < hot:
            pool = range(max(64, seed_count // 6))
        else:
            pool = range(seed_count)
        impacts = tuple(sorted(rng.sample(list(pool), min(24, len(pool)))))
        logical_to_seeds[logical] = impacts
        for seed in impacts:
            seed_to_logicals[seed].add(logical)

    values = {logical: 0 for logical in logical_to_seeds}
    events: list[PulseDeltaEvent] = []
    for i in range(event_count):
        if rng.random() < 0.82:
            logical = f"L{rng.randrange(hot):04d}"
        else:
            logical = f"L{rng.randrange(logical_count):04d}"
        before = values[logical]
        if before > 0 and rng.random() < 0.18:
            after = before - 1
        else:
            after = before + 1
        values[logical] = after
        events.append(
            PulseDeltaEvent(
                event_id=f"E{i:06d}",
                change_class="VALUE_UPDATE",
                from_source_epoch=1 + i,
                to_source_epoch=2 + i,
                from_graph_epoch=1,
                to_graph_epoch=1,
                changed_logical_id=logical,
                before_fingerprint=str(before),
                after_fingerprint=str(after),
                impact_seed_ids=tuple(f"S{s:06d}" for s in logical_to_seeds[logical]),
            )
        )
    return events, logical_to_seeds, seed_to_logicals


def segment_token(seed: int, values: dict[str, int], seed_to_logicals: list[set[str]]) -> int:
    material = "|".join(f"{logical}:{values[logical]}" for logical in sorted(seed_to_logicals[seed]))
    return int(hashlib.sha256(material.encode()).hexdigest()[:15], 16)


def run_once(events, seed_count, seed_to_logicals, *, batch_size: int):
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA journal_mode=MEMORY")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("CREATE TABLE generation_seed(gen INTEGER, seed INTEGER, segment INTEGER, PRIMARY KEY(gen,seed))")
    logical_values = {logical: 0 for deps in seed_to_logicals for logical in deps}
    mapping = [segment_token(seed, logical_values, seed_to_logicals) for seed in range(seed_count)]
    generation_count = 0
    map_rows = 0
    recomputed_seeds = 0
    started = time.perf_counter()

    for start in range(0, len(events), batch_size):
        batch = events[start:start + batch_size]
        for event in batch:
            logical_values[event.changed_logical_id] = int(event.after_fingerprint)
        if batch_size == 1:
            effective_seed_ids = batch[0].impact_seed_ids
        else:
            effect = effectivize_pulse_batch(f"B{start:06d}", batch)
            effective_seed_ids = effect.impact_seed_ids
        for seed_id in effective_seed_ids:
            seed = int(seed_id[1:])
            mapping[seed] = segment_token(seed, logical_values, seed_to_logicals)
        recomputed_seeds += len(set(effective_seed_ids))
        generation_count += 1
        con.executemany(
            "INSERT INTO generation_seed VALUES(?,?,?)",
            ((generation_count, seed, mapping[seed]) for seed in range(seed_count)),
        )
        map_rows += seed_count
    con.commit()
    elapsed = time.perf_counter() - started
    final_hash = hashlib.sha256(json.dumps(mapping, separators=(",", ":")).encode()).hexdigest()
    con.close()
    return {
        "seconds": elapsed,
        "generations": generation_count,
        "generation_map_rows": map_rows,
        "recomputed_seeds": recomputed_seeds,
        "final_state_hash": final_hash,
    }


def q(xs, p):
    ys = sorted(xs)
    if len(ys) == 1:
        return ys[0]
    pos = (len(ys) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(ys) - 1)
    frac = pos - lo
    return ys[lo] * (1 - frac) + ys[hi] * frac


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5000)
    ap.add_argument("--logicals", type=int, default=200)
    ap.add_argument("--events", type=int, default=200)
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--rng-seed", type=int, default=7)
    args = ap.parse_args()
    if min(args.seeds, args.logicals, args.events, args.batch_size, args.reps) <= 0:
        raise SystemExit("all numeric arguments must be positive")

    events, _, seed_to_logicals = build_workload(args.seeds, args.logicals, args.events, args.rng_seed)
    sequential = [run_once(events, args.seeds, seed_to_logicals, batch_size=1) for _ in range(args.reps)]
    batched = [run_once(events, args.seeds, seed_to_logicals, batch_size=args.batch_size) for _ in range(args.reps)]
    if len({r["final_state_hash"] for r in sequential + batched}) != 1:
        raise AssertionError("final-state equivalence falsified")

    seq_times = [r["seconds"] for r in sequential]
    bat_times = [r["seconds"] for r in batched]
    result = {
        "schema_version": "1.0",
        "benchmark": "UNIFIEDDB_PULSE_EFFECTIVIZER_S2_GENERATION_MAP_PROXY",
        "evidence_class": "BOUNDED_SYNTHETIC_MECHANISM_PROXY_NOT_FRANK_SUPERIORITY_EVIDENCE",
        "fixture": vars(args),
        "sequential": {
            "p50_seconds": statistics.median(seq_times),
            "p95_seconds": q(seq_times, 0.95),
            **{k: sequential[0][k] for k in ("generations", "generation_map_rows", "recomputed_seeds")},
        },
        "effectivized": {
            "p50_seconds": statistics.median(bat_times),
            "p95_seconds": q(bat_times, 0.95),
            **{k: batched[0][k] for k in ("generations", "generation_map_rows", "recomputed_seeds")},
        },
        "ratios": {
            "p50_speedup": statistics.median(seq_times) / statistics.median(bat_times),
            "generation_map_row_reduction": 1.0 - batched[0]["generation_map_rows"] / sequential[0]["generation_map_rows"],
            "recompute_reduction": 1.0 - batched[0]["recomputed_seeds"] / sequential[0]["recomputed_seeds"],
        },
        "final_state_hash": sequential[0]["final_state_hash"],
        "platform": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": sys.version.split()[0],
            "sqlite": sqlite3.sqlite_version,
            "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "authority": "PERFORMANCE_PREPROCESSOR_RESEARCH_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY",
        "limitations": [
            "Synthetic read-free final-state projection workload only.",
            "Measures complete generation-map publication plus deterministic seed recomputation proxy, not full SPM-S1 SQLite schema behavior.",
            "Intermediate-observation semantics are deliberately excluded and force sequential publication.",
            "Real Frank Pulse distributions, crash/recovery, concurrency, downstream outcome quality and Andreas target hardware remain unmeasured.",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
