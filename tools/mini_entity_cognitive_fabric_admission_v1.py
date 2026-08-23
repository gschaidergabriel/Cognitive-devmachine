#!/usr/bin/env python3
"""Pre-inference admission ticket for the canonical Mini Entity Cognitive Fabric.

This module deliberately does NOT mint or validate the post-inference
UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.  Its only job is to validate the exact
ZERO_WORKSPACE_CAPSULE/v1 -> ZERO_INFERENCE_PACKET/v1 ancestry needed *before*
inference and to bind the admitted candidate engine/context into a deterministic,
no-effect admission receipt.

MiniUnifiedDB remains canonical durable authority.  The receipt produced here is an
ephemeral/candidate execution fence, never truth, effect, identity or recovery state.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
JSPACE_IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
if str(JSPACE_IMPL) not in sys.path:
    sys.path.insert(0, str(JSPACE_IMPL))

import zero_inference_packet_v1 as packet_v1
import zero_workspace_capsule_v1 as capsule_v1

REQUEST_SCHEMA = "mini-entity-cognitive-fabric-admission-request/v1"
ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
RECEIPT_SCHEMA = "MINI_ENTITY_COGNITIVE_FABRIC_ADMISSION_RECEIPT/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENGINE_CLASS = {
    "CLAUDE_CODE": "claude_code",
    "BUNDLED_LOCAL_08B": "local_08b",
    "ADAPTIVE_BACKEND": "adaptive_backend",
}
PROPOSAL_FIELDS = {
    "zero_workspace_capsule",
    "zero_inference_packet",
    "boot_binding_receipt_digest",
    "inference",
    "system",
    "user",
    "jspace_measurement_refs",
    "gwt_selection_refs",
    "origin_trigger",
}


class AdmissionError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise AdmissionError("NON_CANONICAL_JSON") from exc


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hex64(value: Any, error: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise AdmissionError(error)
    if value in {"0" * 64, "f" * 64}:
        raise AdmissionError(error + ":PLACEHOLDER")
    return value


def _text(value: Any, error: str) -> str:
    if not isinstance(value, str) or not value:
        raise AdmissionError(error)
    return value


def _refs(value: Any, error: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise AdmissionError(error)
    if len(value) != len(set(value)):
        raise AdmissionError(error + ":DUPLICATE")
    return list(value)


def validate_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping) or request.get("schema") != REQUEST_SCHEMA:
        raise AdmissionError("BAD_ADMISSION_REQUEST_SCHEMA")
    generation = request.get("generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise AdmissionError("MISSING_GENERATION")
    canonical_state_hash = _hex64(request.get("canonical_state_hash"), "BAD_CANONICAL_STATE_HASH")
    packet_hash = _hex64(request.get("packet_hash"), "BAD_PACKET_HASH")
    profile_id = _text(request.get("profile_id"), "MISSING_PROFILE_ID")
    profile_hash = _hex64(request.get("profile_hash"), "BAD_PROFILE_HASH")
    task_text = _text(request.get("task_text"), "MISSING_TASK_TEXT")
    system = _text(request.get("system"), "MISSING_SYSTEM_CONTEXT")
    user = _text(request.get("user"), "MISSING_USER_CONTEXT")
    configured_inference = request.get("configured_inference")
    if not isinstance(configured_inference, Mapping) or not configured_inference.get("kind"):
        raise AdmissionError("BAD_CONFIGURED_INFERENCE")
    canonical_json(configured_inference)
    return {
        "schema": REQUEST_SCHEMA,
        "generation": generation,
        "canonical_state_hash": canonical_state_hash,
        "packet_hash": packet_hash,
        "profile_id": profile_id,
        "profile_hash": profile_hash,
        "task_text": task_text,
        "task_sha256": sha256_text(task_text),
        "system": system,
        "system_digest": sha256_text(system),
        "user": user,
        "user_digest": sha256_text(user),
        "configured_inference": dict(configured_inference),
        "configured_inference_digest": sha256_obj(dict(configured_inference)),
    }


def compile_admission(request: Mapping[str, Any], proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a trusted fabric proposal and return the exact candidate admission envelope.

    The proposal may choose/augment candidate inference context, but it cannot choose the
    receipt digest or authority statement.  Those are deterministically generated here.
    """
    req = validate_request(request)
    if not isinstance(proposal, Mapping):
        raise AdmissionError("ADMISSION_PROPOSAL_OBJECT_REQUIRED")
    unknown = set(proposal) - PROPOSAL_FIELDS
    if unknown:
        raise AdmissionError("ADMISSION_PROPOSAL_FIELDS_MISMATCH:" + ",".join(sorted(unknown)))

    capsule = proposal.get("zero_workspace_capsule")
    packet = proposal.get("zero_inference_packet")
    if not isinstance(capsule, dict):
        raise AdmissionError("ZERO_WORKSPACE_CAPSULE_REQUIRED")
    if not isinstance(packet, dict):
        raise AdmissionError("ZERO_INFERENCE_PACKET_REQUIRED")
    try:
        capsule_v1.validate(capsule)
    except Exception as exc:
        raise AdmissionError("ZERO_WORKSPACE_CAPSULE_INVALID:" + str(exc)) from exc
    if capsule.get("mode") != "WORKSPACE_BOUND":
        raise AdmissionError("COGNITIVE_FABRIC_ABSTAINED")
    if capsule.get("entity_generation") != req["generation"]:
        raise AdmissionError("STALE_GENERATION")
    if capsule.get("task_sha256") != req["task_sha256"]:
        raise AdmissionError("PROMPT_CAPSULE_IDENTITY_MISMATCH")
    try:
        packet_v1.validate(packet, capsule)
    except Exception as exc:
        raise AdmissionError("ZERO_INFERENCE_PACKET_INVALID:" + str(exc)) from exc
    if packet.get("entity_generation") != req["generation"]:
        raise AdmissionError("PACKET_GENERATION_MISMATCH")
    target_engine_class = packet.get("target_engine_class")
    if target_engine_class not in ENGINE_CLASS:
        raise AdmissionError("NO_EXECUTABLE_INFERENCE_ROUTE")
    engine_class = ENGINE_CLASS[target_engine_class]
    jspace_mode = _text(packet.get("jspace_mode"), "MISSING_JSPACE_MODE")

    boot_binding_receipt_digest = _hex64(
        proposal.get("boot_binding_receipt_digest"),
        "MISSING_OR_MALFORMED_BOOT_BINDING_RECEIPT_DIGEST",
    )
    inference = proposal.get("inference")
    if not isinstance(inference, Mapping) or not inference.get("kind"):
        raise AdmissionError("UNADMITTED_INFERENCE_ENGINE")
    inference = dict(inference)
    canonical_json(inference)
    system = _text(proposal.get("system"), "MISSING_ADMITTED_SYSTEM_CONTEXT")
    user = _text(proposal.get("user"), "MISSING_ADMITTED_USER_CONTEXT")
    jspace_refs = _refs(proposal.get("jspace_measurement_refs"), "BAD_JSPACE_MEASUREMENT_REFS")
    gwt_refs = _refs(proposal.get("gwt_selection_refs"), "BAD_GWT_SELECTION_REFS")
    if jspace_mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"} and not jspace_refs:
        raise AdmissionError("UNMEASURED_VALUE_PROMOTED_TO_MEASURED")
    if gwt_refs and gwt_refs != list(capsule.get("selected_workspace_slots", [])):
        raise AdmissionError("GWT_SELECTION_CAPSULE_MISMATCH")
    origin_trigger = proposal.get("origin_trigger")
    if origin_trigger is not None and (not isinstance(origin_trigger, str) or not origin_trigger):
        raise AdmissionError("BAD_ORIGIN_TRIGGER")

    inference_packet_digest = _hex64(packet.get("packet_digest"), "BAD_INFERENCE_PACKET_DIGEST")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "generation": req["generation"],
        "canonical_state_hash": req["canonical_state_hash"],
        "source_packet_hash": req["packet_hash"],
        "profile_id": req["profile_id"],
        "profile_hash": req["profile_hash"],
        "source_task_sha256": req["task_sha256"],
        "source_system_digest": req["system_digest"],
        "source_user_digest": req["user_digest"],
        "configured_inference_digest": req["configured_inference_digest"],
        "zero_workspace_capsule_digest": _hex64(capsule.get("capsule_digest"), "BAD_CAPSULE_DIGEST"),
        "zero_identity_digest": _hex64(capsule.get("zero_identity_digest"), "BAD_ZERO_IDENTITY_DIGEST"),
        "grf_digest": _hex64(capsule.get("grf_digest"), "BAD_GRF_DIGEST"),
        "workspace_digest": _hex64(capsule.get("workspace_digest"), "BAD_WORKSPACE_DIGEST"),
        "boot_binding_receipt_digest": boot_binding_receipt_digest,
        "inference_packet_digest": inference_packet_digest,
        "target_engine_class": target_engine_class,
        "engine_class": engine_class,
        "jspace_mode": jspace_mode,
        "jspace_measurement_refs": jspace_refs,
        "gwt_selection_refs": gwt_refs,
        "admitted_inference_digest": sha256_obj(inference),
        "admitted_system_digest": sha256_text(system),
        "admitted_user_digest": sha256_text(user),
        "origin_trigger": origin_trigger or "UNKNOWN",
        "authority": "CANDIDATE_INFERENCE_ONLY",
        "effect_executed": False,
        "canonical_write_committed": False,
    }
    cognitive_fabric_receipt_digest = sha256_obj(receipt)
    return {
        "ok": True,
        "schema": ADMISSION_SCHEMA,
        "generation": req["generation"],
        "canonical_state_hash": req["canonical_state_hash"],
        "packet_hash": req["packet_hash"],
        "inference_packet_digest": inference_packet_digest,
        "cognitive_fabric_receipt_digest": cognitive_fabric_receipt_digest,
        "inference": inference,
        "system": system,
        "user": user,
        "zero_workspace_capsule": capsule,
        "zero_inference_packet": packet,
        "admission_receipt": receipt,
    }


def validate_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, Mapping) or envelope.get("schema") != ADMISSION_SCHEMA:
        raise AdmissionError("BAD_ADMISSION_SCHEMA")
    receipt = envelope.get("admission_receipt")
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise AdmissionError("BAD_ADMISSION_RECEIPT_SCHEMA")
    expected_receipt = sha256_obj(receipt)
    if envelope.get("cognitive_fabric_receipt_digest") != expected_receipt:
        raise AdmissionError("FABRIC_ADMISSION_RECEIPT_DIGEST_MISMATCH")
    if envelope.get("inference_packet_digest") != receipt.get("inference_packet_digest"):
        raise AdmissionError("INFERENCE_PACKET_DIGEST_BINDING_MISMATCH")
    if sha256_obj(envelope.get("inference")) != receipt.get("admitted_inference_digest"):
        raise AdmissionError("ADMITTED_INFERENCE_DIGEST_MISMATCH")
    if sha256_text(_text(envelope.get("system"), "MISSING_ADMITTED_SYSTEM_CONTEXT")) != receipt.get("admitted_system_digest"):
        raise AdmissionError("ADMITTED_SYSTEM_DIGEST_MISMATCH")
    if sha256_text(_text(envelope.get("user"), "MISSING_ADMITTED_USER_CONTEXT")) != receipt.get("admitted_user_digest"):
        raise AdmissionError("ADMITTED_USER_DIGEST_MISMATCH")
    if envelope.get("generation") != receipt.get("generation"):
        raise AdmissionError("ADMISSION_GENERATION_BINDING_MISMATCH")
    if envelope.get("canonical_state_hash") != receipt.get("canonical_state_hash"):
        raise AdmissionError("ADMISSION_CANONICAL_HASH_BINDING_MISMATCH")
    if envelope.get("packet_hash") != receipt.get("source_packet_hash"):
        raise AdmissionError("ADMISSION_SOURCE_PACKET_HASH_BINDING_MISMATCH")
    return dict(envelope)


__all__ = [
    "REQUEST_SCHEMA",
    "ADMISSION_SCHEMA",
    "RECEIPT_SCHEMA",
    "AdmissionError",
    "canonical_json",
    "sha256_obj",
    "sha256_text",
    "validate_request",
    "compile_admission",
    "validate_envelope",
]
