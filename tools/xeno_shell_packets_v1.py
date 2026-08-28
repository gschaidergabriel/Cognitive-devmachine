"""COGNITIVE_WORK_PACKET/v1 and COGNITIVE_RESULT_PACKET/v1 -- Xeno Shell Master Spec v1 SS5-6.

Schema + validation + hash-binding only. No model invocation, no S0/S1 authority --
those live in xeno_shell_s0s1s2_transitions_v1.py and grid10_fabric.py respectively.
Every field the spec lists for each packet is present and required; nothing extra is
silently accepted (fail closed on unknown/missing fields, per spec SS19).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

WORK_PACKET_SCHEMA = "COGNITIVE_WORK_PACKET/v1"
RESULT_PACKET_SCHEMA = "COGNITIVE_RESULT_PACKET/v1"

WORK_PACKET_REQUIRED_FIELDS = (
    "causal_event_id",
    "admission_id",
    "generation",
    "work_id",
    "process_id",
    "parent_work_id",
    "workspace_epoch",
    "db_snapshot_refs",
    "input_evidence_refs",
    "epistemic_classes",
    "capability_scope_ref",
    "resource_budget",
    "runtime_grid_facts",
    "route_policy_ref",
    "completion_contract",
)

RESULT_PACKET_ALLOWED_CLASSES = frozenset({
    "CANDIDATE",
    "PROJECTION",
    "MEASUREMENT",
    "DETERMINISTIC_CONTROL_RESULT",
    "EFFECT_RECEIPT",
})

# Spec SS6: DETERMINISTIC_CONTROL_RESULT only from actual deterministic components;
# EFFECT_RECEIPT only from ZECP17. A model/Claude producer may never mint either.
RESTRICTED_RESULT_CLASSES = frozenset({"DETERMINISTIC_CONTROL_RESULT", "EFFECT_RECEIPT"})
MODEL_LIKE_PRODUCERS = frozenset({"MODEL", "CLAUDE_CODE"})


class PacketError(ValueError):
    pass


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(obj: Any) -> str:
    return hashlib.sha256(_canonical_json(obj).encode("utf-8")).hexdigest()


def build_work_packet(**fields: Any) -> dict[str, Any]:
    missing = [f for f in WORK_PACKET_REQUIRED_FIELDS if f not in fields]
    if missing:
        raise PacketError(f"WORK_PACKET_MISSING_FIELDS:{missing}")
    extra = [f for f in fields if f not in WORK_PACKET_REQUIRED_FIELDS]
    if extra:
        raise PacketError(f"WORK_PACKET_UNKNOWN_FIELDS:{extra}")
    body = {k: fields[k] for k in WORK_PACKET_REQUIRED_FIELDS}
    packet = {"schema": WORK_PACKET_SCHEMA, "body": body}
    packet["packet_digest_sha256"] = digest(body)
    return packet


def validate_work_packet(packet: dict[str, Any]) -> None:
    if packet.get("schema") != WORK_PACKET_SCHEMA:
        raise PacketError("WORK_PACKET_SCHEMA_MISMATCH")
    body = packet.get("body")
    if not isinstance(body, dict):
        raise PacketError("WORK_PACKET_BODY_MISSING")
    missing = [f for f in WORK_PACKET_REQUIRED_FIELDS if f not in body]
    if missing:
        raise PacketError(f"WORK_PACKET_MISSING_FIELDS:{missing}")
    if packet.get("packet_digest_sha256") != digest(body):
        raise PacketError("WORK_PACKET_DIGEST_MISMATCH")


def build_result_packet(
    *,
    result_class: str,
    producer: str,
    source_work_digest: str,
    payload: Any,
    unresolved_alternatives: list[Any] | None = None,
) -> dict[str, Any]:
    if result_class not in RESULT_PACKET_ALLOWED_CLASSES:
        raise PacketError(f"RESULT_PACKET_UNKNOWN_CLASS:{result_class}")
    # Spec SS6 hard rule, enforced structurally (not just documented): a model or
    # Claude-Code producer cannot mint DETERMINISTIC_CONTROL_RESULT or EFFECT_RECEIPT.
    if result_class in RESTRICTED_RESULT_CLASSES and producer.upper() in MODEL_LIKE_PRODUCERS:
        raise PacketError(
            f"RESULT_CLASS_PRODUCER_FORBIDDEN:{result_class}_FROM_{producer}"
        )
    body = {
        "result_class": result_class,
        "producer": producer,
        "source_work_digest_sha256": source_work_digest,
        "payload": payload,
        "unresolved_alternatives": unresolved_alternatives or [],
    }
    packet = {"schema": RESULT_PACKET_SCHEMA, "body": body}
    packet["packet_digest_sha256"] = digest(body)
    return packet


def validate_result_packet(packet: dict[str, Any]) -> None:
    if packet.get("schema") != RESULT_PACKET_SCHEMA:
        raise PacketError("RESULT_PACKET_SCHEMA_MISMATCH")
    body = packet.get("body")
    if not isinstance(body, dict):
        raise PacketError("RESULT_PACKET_BODY_MISSING")
    if body.get("result_class") not in RESULT_PACKET_ALLOWED_CLASSES:
        raise PacketError("RESULT_PACKET_UNKNOWN_CLASS")
    if packet.get("packet_digest_sha256") != digest(body):
        raise PacketError("RESULT_PACKET_DIGEST_MISMATCH")
