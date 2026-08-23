#!/usr/bin/env python3
"""Conservative planning-only capacity calculator for the Mini Entity HCU.

This tool does not benchmark or admit runtime capability. It computes a safe starting
layout from an explicit host profile and provisional or measured tile footprints.
Runtime promotion requires separate exact execution evidence.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


class CapacityError(ValueError):
    """Raised when a capacity profile is invalid or cannot admit one tile."""


@dataclass(frozen=True)
class HostProfile:
    vcpu: int
    memory_gib: float
    disk_gb: float
    bandwidth_tb: float


@dataclass(frozen=True)
class SafetyProfile:
    ram_utilization_fraction: float
    non_model_reserve_gib: float
    disk_reserve_gb: float
    threads_per_active_tile: int


@dataclass(frozen=True)
class TileFootprint:
    resident_rss_gib: float
    active_context_increment_gib: float
    artifact_size_gb: float


@dataclass(frozen=True)
class CapacityPlan:
    status: str
    usable_ram_gib: float
    usable_disk_gb: float
    max_resident_tiles: int
    max_parallel_active_tiles: int
    max_cold_distinct_artifacts: int
    estimated_resident_ram_gib: float
    estimated_active_increment_gib: float
    estimated_total_ram_gib: float
    cpu_active_limit: int
    notes: tuple[str, ...]


def _positive(name: str, value: float) -> float:
    if value <= 0:
        raise CapacityError(f"{name} must be > 0")
    return value


def _non_negative(name: str, value: float) -> float:
    if value < 0:
        raise CapacityError(f"{name} must be >= 0")
    return value


def _validate(host: HostProfile, safety: SafetyProfile, tile: TileFootprint) -> None:
    if host.vcpu <= 0:
        raise CapacityError("vcpu must be > 0")
    _positive("memory_gib", host.memory_gib)
    _positive("disk_gb", host.disk_gb)
    _non_negative("bandwidth_tb", host.bandwidth_tb)

    if not (0 < safety.ram_utilization_fraction <= 1):
        raise CapacityError("ram_utilization_fraction must be in (0, 1]")
    _non_negative("non_model_reserve_gib", safety.non_model_reserve_gib)
    _non_negative("disk_reserve_gb", safety.disk_reserve_gb)
    if safety.threads_per_active_tile <= 0:
        raise CapacityError("threads_per_active_tile must be > 0")

    _positive("resident_rss_gib", tile.resident_rss_gib)
    _non_negative("active_context_increment_gib", tile.active_context_increment_gib)
    _positive("artifact_size_gb", tile.artifact_size_gb)


def plan_capacity(
    host: HostProfile,
    safety: SafetyProfile,
    tile: TileFootprint,
) -> CapacityPlan:
    """Return the largest conservative resident layout for the supplied profile.

    The planner first derives CPU-bounded active slots. It then searches downward from
    the RAM-only resident maximum until resident weights plus the active-context reserve
    fit in the usable RAM envelope.
    """

    _validate(host, safety, tile)

    usable_ram = host.memory_gib * safety.ram_utilization_fraction - safety.non_model_reserve_gib
    usable_disk = host.disk_gb - safety.disk_reserve_gb

    if usable_ram <= 0:
        raise CapacityError("no RAM remains after utilization and non-model reserve")
    if usable_disk <= 0:
        raise CapacityError("no disk remains after reserve")

    cpu_active_limit = max(1, host.vcpu // safety.threads_per_active_tile)
    ram_only_resident = int(math.floor(usable_ram / tile.resident_rss_gib))

    if ram_only_resident < 1:
        raise CapacityError("profile cannot admit one resident tile")

    resident = 0
    active = 0
    for candidate_resident in range(ram_only_resident, 0, -1):
        candidate_active = min(cpu_active_limit, candidate_resident)
        total = (
            candidate_resident * tile.resident_rss_gib
            + candidate_active * tile.active_context_increment_gib
        )
        if total <= usable_ram + 1e-12:
            resident = candidate_resident
            active = candidate_active
            break

    if resident < 1:
        raise CapacityError("profile cannot admit one tile plus active-context reserve")

    cold = int(math.floor(usable_disk / tile.artifact_size_gb))

    resident_ram = resident * tile.resident_rss_gib
    active_increment = active * tile.active_context_increment_gib
    total_ram = resident_ram + active_increment

    return CapacityPlan(
        status="PLANNING_ESTIMATE_NOT_RUNTIME_MEASURED",
        usable_ram_gib=round(usable_ram, 6),
        usable_disk_gb=round(usable_disk, 6),
        max_resident_tiles=resident,
        max_parallel_active_tiles=active,
        max_cold_distinct_artifacts=cold,
        estimated_resident_ram_gib=round(resident_ram, 6),
        estimated_active_increment_gib=round(active_increment, 6),
        estimated_total_ram_gib=round(total_ram, 6),
        cpu_active_limit=cpu_active_limit,
        notes=(
            "Counts depend on the supplied footprint and are not benchmark results.",
            "Logical tiles may exceed physical decoders when exact read-only base weights are shared.",
            "Measured peak RSS/context overhead must replace provisional footprint values before promotion.",
        ),
    )


def _from_mapping(raw: Mapping[str, Any]) -> tuple[HostProfile, SafetyProfile, TileFootprint]:
    host_raw = raw["host"]
    safety_raw = raw["safety"]
    tile_raw = raw["provisional_tile_footprint"]

    host = HostProfile(
        vcpu=int(host_raw["vcpu"]),
        memory_gib=float(host_raw["memory_gib"]),
        disk_gb=float(host_raw["disk_gb"]),
        bandwidth_tb=float(host_raw.get("bandwidth_tb", 0.0)),
    )
    safety = SafetyProfile(
        ram_utilization_fraction=float(safety_raw["ram_utilization_fraction"]),
        non_model_reserve_gib=float(safety_raw["non_model_reserve_gib"]),
        disk_reserve_gb=float(safety_raw["disk_reserve_gb"]),
        threads_per_active_tile=int(safety_raw["threads_per_active_tile"]),
    )
    tile = TileFootprint(
        resident_rss_gib=float(tile_raw["resident_rss_gib"]),
        active_context_increment_gib=float(tile_raw["active_context_increment_gib"]),
        artifact_size_gb=float(tile_raw["artifact_size_gb"]),
    )
    return host, safety, tile


def plan_from_file(path: Path) -> CapacityPlan:
    raw = json.loads(path.read_text(encoding="utf-8"))
    host, safety, tile = _from_mapping(raw)
    return plan_capacity(host, safety, tile)


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Mini Entity HCU resident/active/cold tile capacity")
    parser.add_argument("profile", type=Path, help="HCU_HOST_PROFILE/v1 JSON path")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()

    plan = plan_from_file(args.profile)
    payload = asdict(plan)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":") if args.compact else None, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
