#!/usr/bin/env python3
"""Deterministic HCU capacity planner.

Planning only; not runtime evidence.
"""
from __future__ import annotations
import argparse
import json
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Hardware:
    cpu_cores: int = 4
    ram_mib: int = 16 * 1024
    disk_gib: int = 200
    bandwidth_tb: int = 16

@dataclass(frozen=True)
class ModelBudget:
    weight_mib: int = 620
    hot_lane_mib: int = 640
    logical_state_mib: int = 64
    control_plane_mib: int = 1024
    reserve_mib: int = 4096
    operator_logical_cap: int = 32
    logical_modules_per_core: int = 4

def plan(hw: Hardware, b: ModelBudget) -> dict:
    if hw.cpu_cores < 1 or hw.ram_mib <= 0:
        raise ValueError("invalid hardware")
    usable = hw.ram_mib - b.reserve_mib - b.control_plane_mib
    if usable <= b.weight_mib + b.hot_lane_mib:
        raise ValueError("insufficient RAM for one admitted local lane")

    shared_mem_cap = max(1, (usable - b.weight_mib) // b.hot_lane_mib)
    cpu_lane_cap = max(1, hw.cpu_cores - 1)
    recommended_hot = max(1, min(shared_mem_cap, cpu_lane_cap, 2 if hw.cpu_cores <= 4 else cpu_lane_cap))
    burst_hot = max(recommended_hot, min(shared_mem_cap, cpu_lane_cap))
    replica_mem_cap = usable // (b.weight_mib + b.hot_lane_mib)
    recommended_replicas = max(1, min(replica_mem_cap, recommended_hot))
    logical_target = min(b.operator_logical_cap, max(8, hw.cpu_cores * b.logical_modules_per_core))
    remaining_for_state = usable - b.weight_mib - recommended_hot * b.hot_lane_mib
    logical_mem_cap = max(1, remaining_for_state // b.logical_state_mib)
    logical_target = min(logical_target, logical_mem_cap)

    return {
        "schema_version": "hcu-capacity-plan/v1",
        "claim_class": "DETERMINISTIC_PLANNING_ONLY_NOT_RUNTIME_CREDIT",
        "hardware": asdict(hw),
        "budget": asdict(b),
        "topology": {
            "weight_strategy": "ONE_READ_ONLY_SHARED_OR_MMAP_WEIGHT_IMAGE_WHERE_RUNTIME_SUPPORTS_IT",
            "logical_modules": int(logical_target),
            "recommended_hot_inference_lanes": int(recommended_hot),
            "burst_hot_inference_lanes": int(burst_hot),
            "recommended_independent_weight_replicas_if_sharing_unavailable": int(recommended_replicas),
            "scheduler": "WEIGHTED_FAIR_QUEUE_PLUS_GWT_BROADCAST_BARRIERS",
            "module_state": "SEPARATE_TYPED_STATE_PER_LOGICAL_TILE"
        },
        "resource_reasoning": {
            "usable_after_reserve_and_control_mib": int(usable),
            "shared_weight_memory_hot_lane_cap": int(shared_mem_cap),
            "replicated_weight_memory_cap": int(replica_mem_cap),
            "cpu_hot_lane_cap_after_control_reserve": int(cpu_lane_cap),
            "note": "More resident copies are possible by RAM, but on 4 CPU cores they usually reduce throughput. Scale logical tiles first; scale hot lanes only from measured throughput/latency."
        }
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu-cores", type=int, default=4)
    ap.add_argument("--ram-gib", type=int, default=16)
    ap.add_argument("--disk-gib", type=int, default=200)
    ap.add_argument("--bandwidth-tb", type=int, default=16)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()
    out = plan(Hardware(args.cpu_cores, args.ram_gib * 1024, args.disk_gib, args.bandwidth_tb), ModelBudget())
    print(json.dumps(out, indent=2 if args.pretty else None, sort_keys=True))

if __name__ == "__main__":
    main()
