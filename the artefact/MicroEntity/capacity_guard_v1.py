#!/usr/bin/env python3
"""Fail-closed capacity-claim guard for the Mini Entity HCU KVM4 topology.

The source topology intentionally contains planning targets (for example 16 logical
slots and 2 resident workers). Those numbers are not runtime evidence. This module
prevents a source/planning profile from being promoted into a measured capacity claim
without an exact authorized-isolated measurement receipt.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

TOPOLOGY_SCHEMA = "HCU_TOPOLOGY/v1"
MEASUREMENT_SCHEMA = "HCU_CAPACITY_MEASUREMENT/v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNRESOLVED = "UNRESOLVED_UNTIL_EXACT_ISOLATED_MEASUREMENT"


class HCUCapacityError(ValueError):
    """Typed fail-closed HCU capacity error."""


@dataclass(frozen=True)
class CapacityDecision:
    status: str
    logical_slots: int | str
    resident_workers: int | str
    physical_decode_concurrency: int | str
    identity_sha256: str


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HCUCapacityError(f"NON_CANONICAL_JSON:{exc.__class__.__name__}") from exc


def _pos_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise HCUCapacityError(f"{field}:POSITIVE_INTEGER_REQUIRED")
    return value


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise HCUCapacityError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise HCUCapacityError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def validate_topology(topology: Any) -> dict[str, Any]:
    if not isinstance(topology, dict):
        raise HCUCapacityError("TOPOLOGY_OBJECT_REQUIRED")
    if topology.get("schema_version") != TOPOLOGY_SCHEMA:
        raise HCUCapacityError("TOPOLOGY_SCHEMA_UNSUPPORTED")
    if topology.get("status") != "SOURCE_PROFILE_UNVERIFIED_RUNTIME":
        raise HCUCapacityError("TOPOLOGY_STATUS_MUST_REMAIN_SOURCE_PROFILE_UNVERIFIED_RUNTIME")

    host = topology.get("owner_supplied_host")
    if not isinstance(host, dict):
        raise HCUCapacityError("owner_supplied_host:OBJECT_REQUIRED")
    if _pos_int(host.get("cpu_cores"), "owner_supplied_host.cpu_cores") != 4:
        raise HCUCapacityError("KVM4_CPU_CORE_CONTRACT_MISMATCH")
    if _pos_int(host.get("memory_gib"), "owner_supplied_host.memory_gib") != 16:
        raise HCUCapacityError("KVM4_MEMORY_CONTRACT_MISMATCH")

    cognition = topology.get("cognition")
    if not isinstance(cognition, dict) or cognition.get("model_class") != "~0.8B_GENERIC_CLAYCOG":
        raise HCUCapacityError("COGNITION_MODEL_CLASS_MISMATCH")
    for field in ("target_resident_inference_workers", "default_parallel_decode", "hard_parallel_decode_ceiling"):
        _pos_int(cognition.get(field), f"cognition.{field}")
    if cognition["hard_parallel_decode_ceiling"] > host["cpu_cores"]:
        raise HCUCapacityError("PLANNING_DECODE_CEILING_EXCEEDS_HOST_CPU_CORES")

    grid = topology.get("logical_grid")
    if not isinstance(grid, dict):
        raise HCUCapacityError("logical_grid:OBJECT_REQUIRED")
    target_slots = _pos_int(grid.get("target_slots"), "logical_grid.target_slots")
    adaptive_ceiling = _pos_int(grid.get("adaptive_ceiling"), "logical_grid.adaptive_ceiling")
    if target_slots > adaptive_ceiling:
        raise HCUCapacityError("TARGET_SLOTS_EXCEED_ADAPTIVE_CEILING")
    lanes = grid.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise HCUCapacityError("logical_grid.lanes:NONEMPTY_OBJECT_REQUIRED")
    lane_total = sum(_pos_int(v, f"logical_grid.lanes.{k}") for k, v in lanes.items())
    if lane_total != target_slots:
        raise HCUCapacityError("LOGICAL_LANE_SUM_MUST_EQUAL_TARGET_SLOTS")
    if grid.get("slot_semantics") != "LOGICAL_CONTEXT_ROLE_NOT_DISTINCT_ENTITY_OR_WEIGHT_COPY":
        raise HCUCapacityError("LOGICAL_SLOT_SEMANTICS_MISMATCH")

    persistence = topology.get("persistence")
    if not isinstance(persistence, dict) or persistence.get("authority") != "MiniUnifiedDB":
        raise HCUCapacityError("MINIUNIFIEDDB_MUST_REMAIN_CANONICAL_AUTHORITY")
    if persistence.get("generation_fenced") is not True:
        raise HCUCapacityError("GENERATION_FENCE_REQUIRED")
    effects = topology.get("effects")
    if not isinstance(effects, dict) or effects.get("authority") != "EffectGate" or effects.get("module_direct_effects") is not False:
        raise HCUCapacityError("EFFECTGATE_ONLY_EFFECT_AUTHORITY_REQUIRED")
    feed = topology.get("external_feed")
    if not isinstance(feed, dict) or feed.get("mode") != "FREE_ONLY" or feed.get("paid_fallback") is not False or feed.get("together_execution") != "FORBIDDEN_CURRENT_OWNER_CONTROL":
        raise HCUCapacityError("FREE_ONLY_FEED_POLICY_MISMATCH")

    evidence = topology.get("evidence")
    if not isinstance(evidence, dict):
        raise HCUCapacityError("evidence:OBJECT_REQUIRED")
    for field in ("runtime_fit", "throughput", "safe_slot_ceiling"):
        if evidence.get(field) != "UNVERIFIED":
            raise HCUCapacityError(f"SOURCE_TOPOLOGY_CANNOT_MINT_RUNTIME_CLAIM:{field}")
    return dict(topology)


def unresolved_decision(topology: Any) -> CapacityDecision:
    validated = validate_topology(topology)
    return CapacityDecision(
        status=UNRESOLVED,
        logical_slots=UNRESOLVED,
        resident_workers=UNRESOLVED,
        physical_decode_concurrency=UNRESOLVED,
        identity_sha256=hashlib.sha256(_canonical(validated)).hexdigest(),
    )


def admit_measurement(topology: Any, measurement: Any) -> CapacityDecision:
    validated = validate_topology(topology)
    if not isinstance(measurement, dict) or measurement.get("schema") != MEASUREMENT_SCHEMA:
        raise HCUCapacityError("MEASUREMENT_SCHEMA_UNSUPPORTED")
    required_exact = (
        "source_commit_sha256", "checkpoint_sha256", "tokenizer_sha256",
        "runtime_sha256", "measurement_receipt_sha256"
    )
    for field in required_exact:
        _sha(measurement.get(field), field)
    if measurement.get("execution_surface") != "AUTHORIZED_ISOLATED_SANDBOX":
        raise HCUCapacityError("CAPACITY_MEASUREMENT_SURFACE_NOT_ADMITTED")
    if measurement.get("host_profile_id") != validated.get("profile_id"):
        raise HCUCapacityError("CAPACITY_MEASUREMENT_HOST_PROFILE_MISMATCH")
    if measurement.get("model_class") != validated["cognition"]["model_class"]:
        raise HCUCapacityError("CAPACITY_MEASUREMENT_MODEL_CLASS_MISMATCH")

    shared_rss = _pos_int(measurement.get("shared_weight_rss_bytes"), "shared_weight_rss_bytes")
    incremental = _pos_int(measurement.get("incremental_logical_slot_rss_bytes"), "incremental_logical_slot_rss_bytes")
    reserve = _pos_int(measurement.get("safety_reserve_bytes"), "safety_reserve_bytes")
    host_ram = validated["owner_supplied_host"]["memory_gib"] * 1024**3
    if reserve + shared_rss >= host_ram:
        raise HCUCapacityError("NO_RAM_LEFT_FOR_LOGICAL_SLOT_AFTER_RESERVE")
    computed_slots = (host_ram - reserve - shared_rss) // incremental
    measured_slots = _pos_int(measurement.get("measured_safe_logical_slots"), "measured_safe_logical_slots")
    measured_resident = _pos_int(measurement.get("measured_safe_resident_workers"), "measured_safe_resident_workers")
    measured_decode = _pos_int(measurement.get("measured_safe_physical_decode"), "measured_safe_physical_decode")
    if measured_slots > computed_slots:
        raise HCUCapacityError("MEASURED_LOGICAL_SLOTS_EXCEED_MEMORY_BOUND")
    if measured_decode > validated["owner_supplied_host"]["cpu_cores"]:
        raise HCUCapacityError("MEASURED_DECODE_EXCEEDS_CPU_CORES")
    if measured_decode > measured_resident:
        raise HCUCapacityError("MEASURED_DECODE_EXCEEDS_RESIDENT_WORKERS")
    if measured_resident > measured_slots:
        raise HCUCapacityError("MEASURED_RESIDENT_WORKERS_EXCEED_LOGICAL_SLOTS")

    payload = {"topology": validated, "measurement": measurement}
    return CapacityDecision(
        status="EXACT_ISOLATED_MEASUREMENT_BOUND",
        logical_slots=measured_slots,
        resident_workers=measured_resident,
        physical_decode_concurrency=measured_decode,
        identity_sha256=hashlib.sha256(_canonical(payload)).hexdigest(),
    )
