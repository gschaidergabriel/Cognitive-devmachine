#!/usr/bin/env python3
"""Fail-closed manifest validator and capacity planner for Mini Entity HCU grids.

The Hyperposition Computational Unit (HCU) is a set of logical cognition lanes inside
ONE Mini Entity. It is not a swarm of durable agents. Capacity claims are only numeric
when model/runtime memory measurements are bound into the manifest.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

SCHEMA = "mini-entity-hcu-grid-manifest/v1"
STATE_AUTHORITY = "MiniUnifiedDB"
EFFECT_AUTHORITY = "ENTITYOS_MINI_ENTITY_EFFECT_GATE"
MODULE_CLASS = "~0.8B_GENERIC_CLAYCOG"
UNRESOLVED = "UNRESOLVED_UNTIL_MEASURED"


class HCUManifestError(ValueError):
    """Typed fail-closed HCU manifest error."""


@dataclass(frozen=True)
class CapacityPlan:
    logical_lanes: int
    resident_replicas: int
    active_inference_lanes: int
    available_ram_bytes: int


@dataclass(frozen=True)
class ValidatedHCUManifest:
    manifest: dict[str, Any]
    identity_sha256: str


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HCUManifestError(f"{field}:POSITIVE_INTEGER_REQUIRED")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HCUManifestError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HCUManifestError(f"MANIFEST_NOT_CANONICAL_JSON:{exc.__class__.__name__}") from exc


def plan_shared_weight_capacity(*, host_ram_bytes: int, reserved_ram_bytes: int,
                                measured_shared_weight_rss_bytes: int,
                                measured_incremental_lane_rss_bytes: int,
                                cpu_cores: int,
                                measured_cpu_parallel_ceiling: int) -> CapacityPlan:
    host_ram_bytes = _positive_int(host_ram_bytes, "host_ram_bytes")
    reserved_ram_bytes = _nonnegative_int(reserved_ram_bytes, "reserved_ram_bytes")
    measured_shared_weight_rss_bytes = _positive_int(measured_shared_weight_rss_bytes, "measured_shared_weight_rss_bytes")
    measured_incremental_lane_rss_bytes = _positive_int(measured_incremental_lane_rss_bytes, "measured_incremental_lane_rss_bytes")
    cpu_cores = _positive_int(cpu_cores, "cpu_cores")
    measured_cpu_parallel_ceiling = _positive_int(measured_cpu_parallel_ceiling, "measured_cpu_parallel_ceiling")
    available = host_ram_bytes - reserved_ram_bytes - measured_shared_weight_rss_bytes
    if available < measured_incremental_lane_rss_bytes:
        raise HCUManifestError("INSUFFICIENT_RAM_FOR_ONE_LANE_AFTER_RESERVE")
    lanes = available // measured_incremental_lane_rss_bytes
    active = min(lanes, cpu_cores, measured_cpu_parallel_ceiling)
    return CapacityPlan(lanes, 1, active, available)


def validate_manifest(data: Any) -> ValidatedHCUManifest:
    if not isinstance(data, dict):
        raise HCUManifestError("MANIFEST_OBJECT_REQUIRED")
    required = {"schema","grid_id","entity_count","state_authority","effect_authority","module_class","lane_semantics","weight_topology","host_profile","capacity","scheduler","feed_policy","provenance"}
    missing = sorted(required - set(data))
    if missing:
        raise HCUManifestError("MISSING_REQUIRED_FIELDS:" + ",".join(missing))
    unknown = sorted(set(data) - required)
    if unknown:
        raise HCUManifestError("UNKNOWN_FIELDS:" + ",".join(unknown))
    manifest = dict(data)
    if manifest["schema"] != SCHEMA:
        raise HCUManifestError("SCHEMA_UNSUPPORTED")
    if not isinstance(manifest["grid_id"], str) or not manifest["grid_id"].strip():
        raise HCUManifestError("grid_id:NONEMPTY_STRING_REQUIRED")
    if manifest["entity_count"] != 1:
        raise HCUManifestError("ENTITY_COUNT_MUST_EQUAL_ONE")
    if manifest["state_authority"] != STATE_AUTHORITY:
        raise HCUManifestError("STATE_AUTHORITY_MUST_BE_MINIUNIFIEDDB")
    if manifest["effect_authority"] != EFFECT_AUTHORITY:
        raise HCUManifestError("EFFECT_AUTHORITY_MUST_BE_ENTITYOS_MINI_ENTITY_GATE")
    if manifest["module_class"] != MODULE_CLASS:
        raise HCUManifestError("MODULE_CLASS_MUST_BE_GENERIC_APPROX_08B_CLAYCOG")
    if manifest["lane_semantics"] != "LOGICAL_HYPERPOSITION_COGNITION_LANES":
        raise HCUManifestError("LANE_SEMANTICS_UNSUPPORTED")
    if manifest["weight_topology"] not in {"SHARED_IMMUTABLE_CHECKPOINT_PREFERRED","REPLICATED_EXACT_CHECKPOINT_MEASURED_ONLY"}:
        raise HCUManifestError("WEIGHT_TOPOLOGY_UNSUPPORTED")
    host = manifest["host_profile"]
    if not isinstance(host, dict):
        raise HCUManifestError("host_profile:OBJECT_REQUIRED")
    for field in ("cpu_cores","ram_bytes","disk_bytes","bandwidth_bytes"):
        _positive_int(host.get(field), f"host_profile.{field}")
    if host.get("evidence") not in {"OWNER_SPEC_DEPLOYMENT_TARGET_ONLY","EXACT_RUNTIME_MEASURED"}:
        raise HCUManifestError("host_profile.evidence:UNSUPPORTED")
    capacity = manifest["capacity"]
    if not isinstance(capacity, dict) or capacity.get("policy") != "MAX_SAFE_MEASURED":
        raise HCUManifestError("capacity.policy:MUST_BE_MAX_SAFE_MEASURED")
    measured = capacity.get("measurement_bound")
    if not isinstance(measured, bool):
        raise HCUManifestError("capacity.measurement_bound:BOOLEAN_REQUIRED")
    numeric_fields = ("logical_lanes","resident_replicas","active_inference_lanes","measured_shared_weight_rss_bytes","measured_incremental_lane_rss_bytes","measured_cpu_parallel_ceiling")
    if measured:
        for field in numeric_fields:
            _positive_int(capacity.get(field), f"capacity.{field}")
        if capacity["active_inference_lanes"] > host["cpu_cores"]:
            raise HCUManifestError("ACTIVE_INFERENCE_EXCEEDS_CPU_CORES")
        if capacity["active_inference_lanes"] > capacity["logical_lanes"]:
            raise HCUManifestError("ACTIVE_INFERENCE_EXCEEDS_LOGICAL_LANES")
        if capacity["resident_replicas"] > capacity["logical_lanes"]:
            raise HCUManifestError("RESIDENT_REPLICAS_EXCEED_LOGICAL_LANES")
        reserve = _nonnegative_int(capacity.get("reserved_ram_bytes"), "capacity.reserved_ram_bytes")
        if reserve >= host["ram_bytes"]:
            raise HCUManifestError("RAM_RESERVE_MUST_BE_BELOW_HOST_RAM")
    else:
        if capacity.get("reserved_ram_bytes") not in {None, UNRESOLVED}:
            raise HCUManifestError("UNMEASURED_RESERVED_RAM_MUST_BE_UNRESOLVED")
        for field in numeric_fields:
            if capacity.get(field) != UNRESOLVED:
                raise HCUManifestError(f"UNMEASURED_NUMERIC_CAPACITY_FORBIDDEN:{field}")
    expected_scheduler = {"packet_type":"InferencePacket","parallel_candidates_non_authoritative":True,"single_gwt_commit_winner":True,"generation_fence_required":True,"hyperposition_branch_isolation":True}
    scheduler = manifest["scheduler"]
    if not isinstance(scheduler, dict):
        raise HCUManifestError("scheduler:OBJECT_REQUIRED")
    for key, expected in expected_scheduler.items():
        if scheduler.get(key) != expected:
            raise HCUManifestError(f"scheduler.{key}:REQUIRED_VALUE_MISMATCH")
    expected_feed = {"free_llm_token_pool_role":"CANDIDATE_RESEARCH_INPUT_ONLY","model_output_canonical_truth":False,"model_output_direct_effect":False,"together_forbidden":True}
    feed = manifest["feed_policy"]
    if not isinstance(feed, dict):
        raise HCUManifestError("feed_policy:OBJECT_REQUIRED")
    for key, expected in expected_feed.items():
        if feed.get(key) != expected:
            raise HCUManifestError(f"feed_policy.{key}:REQUIRED_VALUE_MISMATCH")
    if not isinstance(manifest["provenance"], dict) or not manifest["provenance"]:
        raise HCUManifestError("provenance:NONEMPTY_OBJECT_REQUIRED")
    return ValidatedHCUManifest(manifest, hashlib.sha256(_canonical_json_bytes(manifest)).hexdigest())
