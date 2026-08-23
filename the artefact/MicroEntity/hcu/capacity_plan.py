#!/usr/bin/env python3
"""Deterministic HCU KVM4 capacity planner.

This is source-level resource planning only. It does not award runtime credit and
must be replaced/adjusted by exact measured RSS, KV/context memory, throughput,
latency, queue depth and swap-pressure receipts from an admitted runtime.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class Hardware:
    cpu_cores: int = 4
    ram_mib: int = 16 * 1024
    disk_gib: int = 200
    bandwidth_tb: int = 16


@dataclass(frozen=True)
class PlanningBudget:
    mini_entity_soft_mib: int = 12 * 1024
    mini_entity_hard_mib: int = 14 * 1024
    estimated_weight_mib: int = 620
    estimated_hot_lane_overhead_mib: int = 640
    estimated_logical_state_mib: int = 64
    target_logical_slots: int = 16
    adaptive_logical_ceiling: int = 24
    target_hot_lanes: int = 2


def plan(hw: Hardware, b: PlanningBudget) -> dict:
    if hw.cpu_cores < 1 or hw.ram_mib < 1024:
        raise ValueError("invalid hardware")
    hard_budget = min(hw.ram_mib, b.mini_entity_hard_mib)
    soft_budget = min(hard_budget, b.mini_entity_soft_mib)
    if soft_budget <= b.estimated_weight_mib + b.estimated_hot_lane_overhead_mib:
        raise ValueError("planning budget cannot admit one local lane")

    shared_weight_lane_mem_cap = max(
        1,
        (soft_budget - b.estimated_weight_mib) // b.estimated_hot_lane_overhead_mib,
    )
    replicated_lane_mem_cap = max(
        1,
        soft_budget // (b.estimated_weight_mib + b.estimated_hot_lane_overhead_mib),
    )
    default_hot = min(b.target_hot_lanes, hw.cpu_cores, shared_weight_lane_mem_cap)
    burst_hot = min(max(default_hot, hw.cpu_cores - 1), hw.cpu_cores, shared_weight_lane_mem_cap)
    hard_decode_ceiling = min(hw.cpu_cores, shared_weight_lane_mem_cap)

    after_default_lanes = (
        soft_budget
        - b.estimated_weight_mib
        - default_hot * b.estimated_hot_lane_overhead_mib
    )
    logical_mem_cap = max(1, after_default_lanes // b.estimated_logical_state_mib)
    logical_target = min(b.target_logical_slots, logical_mem_cap)
    logical_ceiling = min(b.adaptive_logical_ceiling, logical_mem_cap)

    return {
        "schema_version": "HCU_CAPACITY_PLAN/v2",
        "claim_class": "DETERMINISTIC_PLANNING_ONLY_NOT_RUNTIME_CREDIT",
        "hardware": asdict(hw),
        "planning_budget": asdict(b),
        "topology": {
            "logical_slots_target": int(logical_target),
            "logical_slots_adaptive_ceiling": int(logical_ceiling),
            "resident_hot_lanes_target": int(default_hot),
            "planning_burst_hot_lanes": int(burst_hot),
            "hard_parallel_decode_ceiling_from_cpu_and_estimated_memory": int(hard_decode_ceiling),
            "weight_strategy": "SHARED_FILE_PAGE_CACHE_OR_READ_ONLY_MMAP_WHERE_RUNTIME_SUPPORTS_IT",
            "scheduler": "RESOURCE_ADAPTIVE_WEIGHTED_QUEUE_PLUS_GWT_HYPERPOSITION_BARRIERS",
        },
        "planning_caps": {
            "shared_weight_lane_memory_cap_under_soft_budget": int(shared_weight_lane_mem_cap),
            "independent_replica_memory_cap_under_soft_budget": int(replicated_lane_mem_cap),
            "logical_state_memory_cap_after_default_lanes": int(logical_mem_cap),
        },
        "promotion_gate": [
            "exact_checkpoint_and_runtime_identity",
            "measured_worker_rss",
            "measured_context_kv_bytes",
            "p50_p95_decode_latency",
            "token_throughput_under_queue_load",
            "swap_pressure",
            "restart_generation_fencing",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu-cores", type=int, default=4)
    ap.add_argument("--ram-gib", type=int, default=16)
    ap.add_argument("--disk-gib", type=int, default=200)
    ap.add_argument("--bandwidth-tb", type=int, default=16)
    args = ap.parse_args()
    out = plan(
        Hardware(args.cpu_cores, args.ram_gib * 1024, args.disk_gib, args.bandwidth_tb),
        PlanningBudget(),
    )
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
