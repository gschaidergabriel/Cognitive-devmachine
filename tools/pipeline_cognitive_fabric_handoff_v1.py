#!/usr/bin/env python3
"""Deterministic Mini Entity pipeline <-> Unified Cognitive Fabric handoff.

This module is a reusable contract helper, NOT a second runtime/state/effect authority.
It separates:

FETCH -> admit_pre_inference(): validate exact ZERO_WORKSPACE_CAPSULE/v1 and compile
        exact ZERO_INFERENCE_PACKET/v1.
EXECUTE -> external/selected inference engine runs candidate computation.
WRITE_BACK -> validate_post_inference(): validate the post-execution
        UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1, strict Zero capsule/packet/UCF
        ancestry, and exact candidate-result binding before canonical pipeline gate/commit.

No function here writes MiniUnifiedDB or performs an effect.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
IMPL = ROOT / "research_entity" / "global" / "j-space" / "implementations"
if str(IMPL) not in sys.path:
    sys.path.insert(0, str(IMPL))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import zero_inference_packet_v1 as packet_v1  # type: ignore  # noqa: E402
import zero_workspace_capsule_v1 as capsule_v1  # type: ignore  # noqa: E402
import validate_unified_cognitive_fabric_receipt_v1 as ucf_v1  # type: ignore  # noqa: E402
import validate_zero_ucf_capsule_chain_v1 as strict_chain_v1  # type: ignore  # noqa: E402

SCHEMA = "PIPELINE_COGNITIVE_FABRIC_HANDOFF/v1"
ENGINE_CLASS_MAP = {
    "BUNDLED_LOCAL_08B": "local_08b",
    "CLAUDE_CODE": "claude_code",
    "ADAPTIVE_BACKEND": "adaptive_backend",
}


class HandoffError(ValueError):
    pass


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise HandoffError(msg)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _fabric_profile(profile: Mapping[str, Any]) -> tuple[str, str]:
    fabric = profile.get("cognitive_fabric")
    _need(isinstance(fabric, Mapping), "COGNITIVE_FABRIC_PROFILE_REQUIRED")
    target = str(fabric.get("target_engine_class", ""))
    mode = str(fabric.get("jspace_mode", ""))
    _need(target in packet_v1.TARGET_ENGINES, "COGNITIVE_FABRIC_ENGINE_CLASS_INVALID")
    _need(mode in packet_v1.JSPACE_MODES, "COGNITIVE_FABRIC_JSPACE_MODE_INVALID")
    if target == "NO_MODEL_REQUIRED":
        _need(mode == "PLAIN_COMPATIBILITY", "NO_MODEL_REQUIRES_PLAIN_COMPATIBILITY")
    return target, mode


def admit_pre_inference(
    *,
    capsule: Mapping[str, Any],
    profile: Mapping[str, Any],
    system: str,
    user: str,
    entity_generation: int,
    causal_turn_id: str,
) -> dict[str, Any]:
    """Validate the fresh workspace capsule and compile the sole pre-inference packet.

    `system`/`user` are admitted only after exact capsule task/generation/turn binding.
    A workspace abstention never becomes executable inference.
    """
    _need(isinstance(capsule, Mapping), "CAPSULE_REQUIRED")
    c = dict(capsule)
    capsule_v1.validate(c)
    _need(c.get("mode") == "WORKSPACE_BOUND", "WORKSPACE_ABSTAINED")
    _need(c.get("entity_generation") == entity_generation, "CAPSULE_GENERATION_STALE")
    _need(c.get("causal_turn_id") == causal_turn_id, "CAPSULE_CAUSAL_TURN_MISMATCH")
    _need(isinstance(system, str) and isinstance(user, str), "PROMPT_CONTEXT_INVALID")
    _need(c.get("task", {}).get("text") == user, "CAPSULE_TASK_TEXT_MISMATCH")
    _need(
        c.get("task", {}).get("sha256") == hashlib.sha256(user.encode("utf-8")).hexdigest(),
        "CAPSULE_TASK_DIGEST_MISMATCH",
    )

    target, mode = _fabric_profile(profile)
    _need(target != "NO_MODEL_REQUIRED", "NO_MODEL_PACKET_CANNOT_EXECUTE")
    packet = packet_v1.compile_packet(c, target_engine_class=target, jspace_mode=mode)
    packet_v1.validate(packet, c)

    inference = profile.get("inference")
    _need(isinstance(inference, Mapping), "INFERENCE_PROFILE_REQUIRED")
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "PRE_INFERENCE_ADMISSION",
        "entity_generation": entity_generation,
        "causal_turn_id": causal_turn_id,
        "inference": dict(inference),
        "system": system,
        "user": user,
        "zero_workspace_capsule": c,
        "zero_workspace_capsule_digest": c["capsule_digest"],
        "inference_packet": packet,
        "inference_packet_digest": packet["packet_digest"],
        "target_engine_class": target,
        "jspace_mode": mode,
        "cognitive_fabric_receipt_digest": None,
        "runtime_credit": "ZERO_PRE_EXECUTION",
    }


def validate_post_inference(
    *,
    cycle_receipt: Mapping[str, Any],
    admission: Mapping[str, Any],
    generated: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate post-execution UCF evidence and exact generated-candidate binding.

    The receipt must already describe an executed candidate cycle. It may not claim a
    canonical state/effect commit; those remain downstream deterministic pipeline duties.
    """
    _need(isinstance(cycle_receipt, Mapping), "UCF_RUNTIME_RECEIPT_REQUIRED")
    _need(isinstance(admission, Mapping), "ADMISSION_REQUIRED")
    _need(isinstance(generated, Mapping), "GENERATED_RESULT_REQUIRED")
    _need(admission.get("phase") == "PRE_INFERENCE_ADMISSION", "ADMISSION_PHASE_INVALID")
    _need(admission.get("cognitive_fabric_receipt_digest") is None, "PRE_INFERENCE_RECEIPT_FORBIDDEN")

    cycle = json.loads(json.dumps(dict(cycle_receipt)))
    base = ucf_v1.validate(cycle)
    _need(bool(base.get("ok")), "UCF_RUNTIME_RECEIPT_INVALID")

    capsule = admission.get("zero_workspace_capsule")
    packet = admission.get("inference_packet")
    _need(isinstance(capsule, dict) and isinstance(packet, dict), "ADMISSION_ANCESTRY_MISSING")
    strict_errors = strict_chain_v1.validate_zero_bindings(cycle, capsule, packet)
    _need(not strict_errors, "ZERO_UCF_ANCESTRY_INVALID:" + ",".join(strict_errors))

    inference = cycle.get("inference", {})
    authority = cycle.get("authority", {})
    _need(inference.get("executed") is True, "UCF_INFERENCE_NOT_EXECUTED")
    target = str(admission.get("target_engine_class", ""))
    _need(ENGINE_CLASS_MAP.get(target) == inference.get("engine_class"), "ENGINE_CLASS_BINDING_MISMATCH")
    _need(admission.get("jspace_mode") == inference.get("jspace_mode"), "JSPACE_MODE_BINDING_MISMATCH")

    payload = generated.get("payload")
    _need(isinstance(payload, Mapping), "GENERATED_PAYLOAD_NOT_OBJECT")
    candidate_digest = sha256_obj(dict(payload))
    _need(
        inference.get("candidate_result_digest") == candidate_digest,
        "CANDIDATE_RESULT_DIGEST_MISMATCH",
    )
    _need(authority.get("validation_decision") == "ACCEPT", "UCF_CYCLE_NOT_ACCEPTED")
    _need(authority.get("canonical_write_committed") is False, "PREMATURE_CANONICAL_WRITE")
    _need(authority.get("effect_committed") is False, "PREMATURE_EFFECT_COMMIT")

    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "POST_INFERENCE_VALIDATION",
        "entity_generation": admission.get("entity_generation"),
        "causal_turn_id": admission.get("causal_turn_id"),
        "zero_workspace_capsule_digest": admission.get("zero_workspace_capsule_digest"),
        "inference_packet_digest": admission.get("inference_packet_digest"),
        "candidate_result_digest": candidate_digest,
        "cognitive_fabric_receipt_digest": cycle.get("receipt_envelope_digest"),
        "runtime_credit": "BOUNDED_EXECUTED_CYCLE_ONLY",
        "canonical_write_committed": False,
        "effect_committed": False,
    }


__all__ = [
    "SCHEMA",
    "HandoffError",
    "admit_pre_inference",
    "validate_post_inference",
    "sha256_obj",
]
