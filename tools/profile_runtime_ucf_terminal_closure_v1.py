#!/usr/bin/env python3
"""Post-commit ancestry closure for the retained ProfilePipelineRuntime UCF path.

This module deliberately does NOT mint UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.
It verifies the terminal ancestry that is already observable after deterministic gate
and MiniUnifiedDB commit, then reports explicit evidence debt for fields the retained
runtime cannot yet establish truthfully. MiniUnifiedDB remains the only durable state
authority and EffectGate remains the only real-effect authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "PROFILE_RUNTIME_UCF_TERMINAL_CLOSURE/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ProfileRuntimeUCFTerminalClosureError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileRuntimeUCFTerminalClosureError(message)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ProfileRuntimeUCFTerminalClosureError("NONCANONICAL_JSON") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _identity(value: Any, error: str) -> str:
    _need(type(value) is str and _HEX64.fullmatch(value) is not None, error)
    _need(value not in {"0" * 64, "f" * 64}, error + ":PLACEHOLDER")
    return value


def terminal_result_digest(
    *,
    output_id: str,
    generation: int,
    inference_packet_digest: str,
    cognitive_fabric_admission_receipt_digest: str,
) -> str:
    _need(type(output_id) is str and bool(output_id), "OUTPUT_ID_REQUIRED")
    _need(type(generation) is int and generation >= 0, "COMMITTED_GENERATION_INVALID")
    packet_digest = _identity(inference_packet_digest, "INFERENCE_PACKET_DIGEST_INVALID")
    admission_digest = _identity(
        cognitive_fabric_admission_receipt_digest,
        "ADMISSION_RECEIPT_DIGEST_INVALID",
    )
    return _digest(
        {
            "output_id": output_id,
            "generation": generation,
            "inference_packet_digest": packet_digest,
            "cognitive_fabric_admission_receipt_digest": admission_digest,
            "canonical_write_committed": True,
            "effect_committed": False,
        }
    )


def evaluate_terminal_closure(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate post-commit ancestry without pretending final UCF evidence already exists."""
    _need(isinstance(payload, Mapping), "PAYLOAD_OBJECT_REQUIRED")
    data = payload.get("data")
    _need(isinstance(data, Mapping), "DATA_OBJECT_REQUIRED")

    admitted = data.get("admitted")
    generated = data.get("generated")
    gated = data.get("gated")
    committed = data.get("committed")
    compiled = data.get("compiled")
    prompt = data.get("prompt")
    for name, value in (
        ("admitted", admitted),
        ("generated", generated),
        ("gated", gated),
        ("committed", committed),
        ("compiled", compiled),
        ("prompt", prompt),
    ):
        _need(isinstance(value, Mapping), name.upper() + "_OBJECT_REQUIRED")

    _need(admitted.get("ok") is True, "ADMISSION_NOT_SUCCESSFUL")
    _need(generated.get("ok") is True, "INFERENCE_NOT_SUCCESSFUL")
    _need(gated.get("ok") is True, "GATE_NOT_SUCCESSFUL")
    _need(committed.get("ok") is True, "COMMIT_NOT_SUCCESSFUL")

    admission_generation = admitted.get("generation")
    _need(
        type(admission_generation) is int and admission_generation >= 0,
        "ADMISSION_GENERATION_INVALID",
    )
    committed_generation = committed.get("generation")
    _need(
        type(committed_generation) is int
        and committed_generation == admission_generation + 1,
        "COMMIT_GENERATION_DRIFT",
    )

    packet_digest = _identity(
        admitted.get("inference_packet_digest"),
        "INFERENCE_PACKET_DIGEST_INVALID",
    )
    admission_digest = _identity(
        admitted.get("cognitive_fabric_receipt_digest"),
        "ADMISSION_RECEIPT_DIGEST_INVALID",
    )
    _need(
        generated.get("inference_packet_digest") == packet_digest,
        "GENERATED_PACKET_IDENTITY_DRIFT",
    )
    _need(
        generated.get("cognitive_fabric_admission_receipt_digest") == admission_digest,
        "GENERATED_ADMISSION_IDENTITY_DRIFT",
    )
    _need(
        gated.get("inference_packet_digest") == packet_digest,
        "GATED_PACKET_IDENTITY_DRIFT",
    )
    _need(
        gated.get("cognitive_fabric_admission_receipt_digest") == admission_digest,
        "GATED_ADMISSION_IDENTITY_DRIFT",
    )
    _need(
        committed.get("inference_packet_digest") == packet_digest,
        "COMMITTED_PACKET_IDENTITY_DRIFT",
    )
    _need(
        committed.get("cognitive_fabric_admission_receipt_digest") == admission_digest,
        "COMMITTED_ADMISSION_IDENTITY_DRIFT",
    )

    _need(
        admitted.get("canonical_state_hash") == compiled.get("canonical_state_hash"),
        "CANONICAL_STATE_IDENTITY_DRIFT",
    )
    _need(
        admitted.get("packet_hash") == compiled.get("packet_hash"),
        "SOURCE_PACKET_IDENTITY_DRIFT",
    )

    generated_payload = generated.get("payload")
    _need(isinstance(generated_payload, Mapping), "GENERATED_PAYLOAD_OBJECT_REQUIRED")
    candidate_result_digest = _identity(
        generated.get("candidate_result_digest"),
        "CANDIDATE_RESULT_DIGEST_INVALID",
    )
    _need(
        candidate_result_digest == _digest(dict(generated_payload)),
        "CANDIDATE_RESULT_IDENTITY_DRIFT",
    )
    _need(gated.get("payload") == generated_payload, "GATED_PAYLOAD_IDENTITY_DRIFT")
    _need(gated.get("validation_decision") == "ACCEPT", "GATE_DECISION_NOT_ACCEPT")
    _need(
        committed.get("canonical_write_committed") is True,
        "CANONICAL_WRITE_NOT_COMMITTED",
    )
    _need(committed.get("effect_committed") is False, "UNEXPECTED_EFFECT_COMMIT")

    output_id = committed.get("output_id")
    _need(type(output_id) is str and bool(output_id), "OUTPUT_ID_REQUIRED")
    expected_terminal_digest = terminal_result_digest(
        output_id=output_id,
        generation=committed_generation,
        inference_packet_digest=packet_digest,
        cognitive_fabric_admission_receipt_digest=admission_digest,
    )
    _need(
        committed.get("terminal_result_digest") == expected_terminal_digest,
        "TERMINAL_RESULT_IDENTITY_DRIFT",
    )

    closure_material = {
        "admission_generation": admission_generation,
        "committed_generation": committed_generation,
        "canonical_state_hash": compiled.get("canonical_state_hash"),
        "packet_hash": compiled.get("packet_hash"),
        "inference_packet_digest": packet_digest,
        "cognitive_fabric_admission_receipt_digest": admission_digest,
        "candidate_result_digest": candidate_result_digest,
        "validation_decision": gated.get("validation_decision"),
        "output_id": output_id,
        "terminal_result_digest": expected_terminal_digest,
        "canonical_write_committed": True,
        "effect_committed": False,
        "prompt_digest": _digest(dict(prompt)),
    }
    return {
        "ok": False,
        "schema": SCHEMA,
        "error_kind": "PipelineFault",
        "error": "UCF_FINAL_RUNTIME_RECEIPT_EVIDENCE_INCOMPLETE",
        "terminal_ancestry_digest": _digest(closure_material),
        "candidate_result_digest": candidate_result_digest,
        "terminal_result_digest": expected_terminal_digest,
        "missing_runtime_receipt_evidence": [
            "exact_source_commit_tree_dirty_identity",
            "runtime_and_entityos_version_identity",
            "complete_workspace_gwt_jspace_observation_evidence",
            "complete_inference_adapter_capability_evidence",
            "execution_lane_policy_and_touch_evidence",
        ],
        "authority": "EVIDENCE_DEBT_ONLY_NO_UCF_RUNTIME_RECEIPT",
    }


__all__ = [
    "SCHEMA",
    "ProfileRuntimeUCFTerminalClosureError",
    "terminal_result_digest",
    "evaluate_terminal_closure",
]
