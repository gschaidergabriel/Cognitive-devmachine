#!/usr/bin/env python3
"""Thin retained-runtime phase bridge into the single canonical UCF admission compositor.

This module intentionally owns no cognition semantics, durable state, turn allocation,
model execution, truth/effect authority, or post-turn UCF finalization.  It only adapts
the canonical Clay ``phase(...)`` envelope to ``pipeline_cognitive_fabric_admission_v1``
and checks that the returned candidate-only admission is still bound to the exact
MiniUnifiedDB generation plus compiled state/packet identities supplied by the phase.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Callable

ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
ORIGIN = "ProfilePipelineRuntime"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_DATA = {"compiled", "prompt", "invocation"}


class RuntimeCognitiveFabricBridgeError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeCognitiveFabricBridgeError(message)


def _mapping(value: Any, message: str) -> Mapping[str, Any]:
    _need(isinstance(value, Mapping), message)
    return value


def _digest(value: Any, name: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def admit_phase(
    db: Any,
    phase_payload: Mapping[str, Any],
    *,
    compositor: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Adapt one canonical runtime phase envelope to the retained admission compositor.

    ``db`` must be the same MiniUnifiedDB connection used to resolve the active cognition
    turn.  The caller is responsible for opening it read-only / without introducing a
    second transaction authority.  ``compositor`` is injectable only for deterministic
    component testing; production defaults to the single repository-owned compositor.
    """
    payload = _mapping(phase_payload, "PHASE_PAYLOAD_OBJECT_REQUIRED")
    profile = _mapping(payload.get("profile"), "PROFILE_OBJECT_REQUIRED")
    previous = _mapping(payload.get("previous"), "PREVIOUS_OBJECT_REQUIRED")
    data = _mapping(payload.get("data"), "DATA_OBJECT_REQUIRED")

    generation = previous.get("generation")
    _need(type(generation) is int and generation >= 0, "PREVIOUS_GENERATION_INVALID")
    _need(_REQUIRED_DATA.issubset(data), "COGNITION_PHASE_DATA_INCOMPLETE")

    compiled = _mapping(data.get("compiled"), "COMPILED_OBJECT_REQUIRED")
    prompt = _mapping(data.get("prompt"), "PROMPT_OBJECT_REQUIRED")
    invocation = _mapping(data.get("invocation"), "INVOCATION_OBJECT_REQUIRED")
    canonical_state_hash = _digest(compiled.get("canonical_state_hash"), "canonical_state_hash")
    packet_hash = _digest(compiled.get("packet_hash"), "packet_hash")

    if compositor is None:
        from pipeline_cognitive_fabric_admission_v1 import (  # local canonical source
            build_pre_inference_admission,
        )

        compositor = build_pre_inference_admission

    admitted = compositor(
        db,
        entity_generation=generation,
        invocation=invocation,
        compiled=compiled,
        prompt=prompt,
        profile=profile,
        origin=ORIGIN,
    )

    _need(type(admitted) is dict and admitted.get("ok") is True, "COGNITIVE_FABRIC_ADMISSION_FAILED")
    _need(admitted.get("schema") == ADMISSION_SCHEMA, "COGNITIVE_FABRIC_ADMISSION_SCHEMA_MISMATCH")
    _need(admitted.get("generation") == generation, "COGNITIVE_FABRIC_ADMISSION_GENERATION_DRIFT")
    _need(
        admitted.get("canonical_state_hash") == canonical_state_hash,
        "COGNITIVE_FABRIC_ADMISSION_CANONICAL_STATE_DRIFT",
    )
    _need(admitted.get("packet_hash") == packet_hash, "COGNITIVE_FABRIC_ADMISSION_PACKET_DRIFT")
    _digest(admitted.get("inference_packet_digest"), "inference_packet_digest")
    _digest(admitted.get("cognitive_fabric_receipt_digest"), "cognitive_fabric_receipt_digest")
    _mapping(admitted.get("inference"), "ADMITTED_INFERENCE_OBJECT_REQUIRED")
    _need(type(admitted.get("system")) is str, "ADMITTED_SYSTEM_TEXT_REQUIRED")
    _need(type(admitted.get("user")) is str, "ADMITTED_USER_TEXT_REQUIRED")

    receipt = _mapping(admitted.get("admission_receipt"), "ADMISSION_RECEIPT_OBJECT_REQUIRED")
    _need(receipt.get("authority") == "CANDIDATE_INFERENCE_ONLY", "ADMISSION_AUTHORITY_ESCALATION")
    _need(receipt.get("real_effect_executed") is False, "PREINFERENCE_EFFECT_EXECUTION_FORBIDDEN")
    _need(
        "ucf_runtime_receipt_digest" not in admitted and "ucf_runtime_receipt_digest" not in receipt,
        "PREINFERENCE_FINAL_UCF_RECEIPT_FORBIDDEN",
    )

    return admitted


__all__ = [
    "ADMISSION_SCHEMA",
    "ORIGIN",
    "RuntimeCognitiveFabricBridgeError",
    "admit_phase",
]
