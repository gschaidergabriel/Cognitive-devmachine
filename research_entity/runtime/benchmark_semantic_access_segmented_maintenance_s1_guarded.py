#!/usr/bin/env python3
from __future__ import annotations

"""Matched SPM-S1 vs guarded SPM-S1 overhead + corruption-repair benchmark.

Synthetic deterministic engineering scope only. This benchmark does not establish universal
DB superiority or downstream Frank cognitive outcome quality.
"""

import argparse
import json
import math
import os
import random
import statistics
import tempfile
import time
from pathlib import Path

from benchmark_semantic_access_pulse_v12 import make_model
from semantic_access_pulse_v12 import PulsePlan
from semantic_access_segmented_maintenance_s1 import SegmentedPulseMaintenanceS1
from semantic_access_segmented_maintenance_s1_guarded import SegmentedPulseMaintenanceS1Guarded


def p95(xs):
    ys = sorted(xs)
    return ys[min(len(ys)-1, max(0, math.ceil(.95*len(ys))-1))] if ys else 0.0


def stats(xs):
    return {
        "n": len(xs),
        "p50_ms": round(statistics.median(xs), 6),
        "p95_ms": round(p95(xs), 6),
        "min_ms": round(min(xs), 6),
        "max_ms": round(max(xs), 6),
    }


def run_arm(cls, path, seeds, cluster, versions, recompute, events, query_repeats, paths_per_seed):
    x = cls(path)
    t0 = time.perf_counter_ns()
    x.bootstrap(event_id="boot", source_epoch=1, graph_epoch=1, seeds=seeds, recompute_seed=recompute)
    bootstrap_ms = (time.perf_counter_ns()-t0)/1e6
    source_epoch = 1
    local_ms = []
    modes = []
    reused = []
    for event in range(events):
        c = event % max(cluster.values(), default=0) if max(cluster.values(), default=0) else 0
        impacted = [s for s in seeds if cluster[s] == c]
        for seed in impacted:
            versions[seed] += 1
        source_epoch += 1
        t0 = time.perf_counter_ns()
        receipt = x.apply_pulse(
            PulsePlan(
                f"local-{event}", "VALUE_UPDATE", (f"cluster:{c:03d}",), tuple(impacted),
                True, source_epoch, 1,
            ),
            recompute_seed=recompute,
            recompute_all_seeds=lambda: seeds,
            incremental_fraction_limit=.25,
        )
        local_ms.append((time.perf_counter_ns()-t0)/1e6)
        modes.append(receipt.mode)
        reused.append(receipt.reused_segment_count)
    rng = random.Random(90210)
    query_ms = []
    for _ in range(query_repeats):
        seed = seeds[rng.randrange(len(seeds))]
        t0 = time.perf_counter_ns()
        refs = x.query(seed, paths_per_seed)
        query_ms.append((time.perf_counter_ns()-t0)/1e6)
        if len(refs) != paths_per_seed:
            raise AssertionError("unexpected query cardinality")
    audit = x.audit_current_generation()
    out = {
        "bootstrap_ms": round(bootstrap_ms, 6),
        "local_update_ms": stats(local_ms),
        "query_ms": stats(query_ms),
        "all_local_incremental": all(m == "SEGMENTED_INCREMENTAL_PULSE" for m in modes),
        "median_reused_segments": statistics.median(reused),
        "audit_pass": bool(audit["pass"]),
        "storage": x.storage_counts(),
        "source_epoch": source_epoch,
    }
    return x, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=1200)
    ap.add_argument("--clusters", type=int, default=60)
    ap.add_argument("--paths", type=int, default=20)
    ap.add_argument("--events", type=int, default=6)
    ap.add_argument("--query-repeats", type=int, default=500)
    ap.add_argument("--output")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as td:
        seeds_b, cluster_b, versions_b, recompute_b = make_model(args.seeds, args.clusters, args.paths)
        base, base_out = run_arm(
            SegmentedPulseMaintenanceS1,
            os.path.join(td, "base.sqlite"),
            seeds_b, cluster_b, versions_b, recompute_b,
            args.events, args.query_repeats, args.paths,
        )

        seeds_g, cluster_g, versions_g, recompute_g = make_model(args.seeds, args.clusters, args.paths)
        guard, guard_out = run_arm(
            SegmentedPulseMaintenanceS1Guarded,
            os.path.join(td, "guard.sqlite"),
            seeds_g, cluster_g, versions_g, recompute_g,
            args.events, args.query_repeats, args.paths,
        )

        # Corrupt one CURRENT reverse-dependency row. The persistent SQLite trigger must mark
        # health DIRTY before any later impact-selection pass can rely on that reverse index.
        head = guard.head_basis()
        if head is None:
            raise AssertionError("guarded head missing")
        victim_seed = seeds_g[0]
        segment_id = guard.con.execute(
            "SELECT segment_id FROM access_generation_seed WHERE generation_id=? AND seed_id=?",
            (head[2], victim_seed),
        ).fetchone()[0]
        dependency = guard.con.execute(
            "SELECT dependency_logical_id FROM access_segment_dependency WHERE segment_id=? ORDER BY dependency_logical_id LIMIT 1",
            (segment_id,),
        ).fetchone()[0]
        guard.con.execute(
            "DELETE FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id=?",
            (segment_id, dependency),
        )
        guard.con.commit()
        dirty_before = guard.integrity_state()
        if dirty_before["status"] != "DIRTY":
            raise AssertionError("tripwire failed to mark DIRTY")
        blocked_read = False
        try:
            guard.query(victim_seed, args.paths)
        except Exception:
            blocked_read = True
        if not blocked_read:
            raise AssertionError("DIRTY projection served a model-facing read")

        repair_epoch = int(guard_out["source_epoch"]) + 1
        t0 = time.perf_counter_ns()
        repair = guard.apply_pulse(
            PulsePlan(
                "integrity-repair", "VALUE_UPDATE", (dependency,), (victim_seed,),
                True, repair_epoch, 1,
            ),
            recompute_seed=recompute_g,
            recompute_all_seeds=lambda: seeds_g,
            incremental_fraction_limit=.25,
        )
        repair_ms = (time.perf_counter_ns()-t0)/1e6
        post = guard.guarded_audit()
        if repair.mode != "FULL_FALLBACK" or guard.integrity_state()["status"] != "CLEAN" or not post["pass"]:
            raise AssertionError("integrity repair gate failed")

        base.close()
        guard.close()

        base_q = base_out["query_ms"]["p50_ms"]
        guard_q = guard_out["query_ms"]["p50_ms"]
        base_local = base_out["local_update_ms"]["p50_ms"]
        guard_local = guard_out["local_update_ms"]["p50_ms"]
        out = {
            "schema": "clay.unifieddb.spm_s1.integrity_tripwire.benchmark.v1",
            "truth_class": "LOCAL_OR_RUNNER_SYNTHETIC_ENGINEERING_ONLY",
            "fixture": {
                "seeds": args.seeds,
                "clusters": args.clusters,
                "paths_per_seed": args.paths,
                "local_events_per_arm": args.events,
                "query_repeats_per_arm": args.query_repeats,
            },
            "spm_s1_base": base_out,
            "spm_s1_guarded": guard_out,
            "overhead": {
                "query_p50_ratio_guard_over_base": round(guard_q/base_q, 6) if base_q else None,
                "query_p50_delta_ms": round(guard_q-base_q, 6),
                "local_update_p50_ratio_guard_over_base": round(guard_local/base_local, 6) if base_local else None,
                "local_update_p50_delta_ms": round(guard_local-base_local, 6),
            },
            "tamper_recovery": {
                "dirty_before_repair": dirty_before,
                "dirty_read_blocked": blocked_read,
                "repair_mode": repair.mode,
                "repair_ms": round(repair_ms, 6),
                "post_repair_clean": post["integrity_state"]["status"] == "CLEAN",
                "post_repair_deep_audit_pass": bool(post["pass"]),
            },
            "limitations": [
                "Synthetic clustered topology; real Frank/Clay reverse-dependency fan-out is not yet measured.",
                "SQLite local process benchmark; WAL multi-connection contention is a separate gate.",
                "The guarded hot path adds one integrity-state lookup; this overhead is intentionally measured rather than hidden.",
                "No downstream model/GWT outcome quality is measured here.",
            ],
        }
        text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        print(text, end="")


if __name__ == "__main__":
    main()
