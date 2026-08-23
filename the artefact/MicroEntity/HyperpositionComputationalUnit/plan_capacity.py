#!/usr/bin/env python3
"""Plan a sparse 0.8B Hyperposition Computational Unit from a host profile.

This is a capacity planner, not runtime evidence.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def plan(profile: dict) -> dict:
    obs = profile["owner_observed_plan"]
    a = profile["planning_assumptions"]
    usable = max(0.0, float(obs["memory_gib"]) - float(a["os_coordinator_reserve_gib"]))
    per_cell = float(a["q4_cell_rss_budget_gib"])
    memory_bound = math.floor(usable / per_cell) if per_cell > 0 else 0
    cores = int(obs["cpu_cores"])
    threads = max(1, int(a["cpu_threads_per_active_decoder"]))
    cpu_active = max(1, cores // threads)
    return {
        "schema": "HCU_CAPACITY_PLAN/v1",
        "status": "PLANNING_ONLY_NOT_RUNTIME_EVIDENCE",
        "memory": {
            "total_gib": obs["memory_gib"],
            "reserve_gib": a["os_coordinator_reserve_gib"],
            "usable_gib": round(usable, 3),
            "assumed_q4_cell_rss_gib": per_cell,
            "memory_bound_resident_cells": memory_bound,
        },
        "cpu": {
            "cores": cores,
            "threads_per_active_decoder": threads,
            "estimated_parallel_decode_slots": cpu_active,
        },
        "candidate_profiles": profile["candidate_profiles"],
        "recommendation": {
            "first_profile": "balanced",
            "reason": "keep RAM headroom while limiting simultaneous decode to the 4-core CPU",
            "promotion_gate": "measure exact RSS and 1/2/4 decoder throughput before deployment promotion",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("profile", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    p = json.loads(args.profile.read_text())
    out = plan(p)
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
