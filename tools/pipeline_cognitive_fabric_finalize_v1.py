#!/usr/bin/env python3
"""Post-commit UCF finalization for the canonical Mini Entity pipeline.

This module owns no durable state, model execution, gate decision or effect path. It
accepts bounded runtime-evidence material produced by the admitted inference adapter,
cross-binds it to the exact pre-inference Cognitive Fabric admission, deterministic gate
and observed MiniUnifiedDB commit, then delegates final semantic validation to the single
canonical UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1 validator.

The inference candidate cannot mint terminal authority: authority, committed generation,
candidate-result identity, terminal-result identity and receipt envelope digest are all
materialized only here, after the commit outcome exists.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

SCHEMA = "MINI_ENTITY_COGNITIVE_FABRIC_FINALIZATION/v1"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class CognitiveFabricFinalizationError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveFabricFinalizationError(message)


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
        raise CognitiveFabricFinalizationError("NONCANONICAL_JSON") from exc


def _sha256_obj(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _mapping(value: Any, name: str) -> dict[str, Any]:
    _need(isinstance(value, Mapping), f"{name}:OBJECT_REQUIRED")
    return dict(value)


def _text(value: Any, name: str) -> str:
    _need(type(value) is str and bool(value.strip()), f"{name}:NONEMPTY_TEXT_REQUIRED")
    return value.strip()


def _digest(value: Any, name: str) -> str:
    value = _text(value, name)
    _need(_HEX64.fullmatch(value) is not None, f"{name}:SHA256_REQUIRED")
    _need(value not in {"0" * 64, "f" * 64}, f"{name}:PLACEHOLDER_REJECTED")
    return value


def _same(value: Any, expected: Any, message: str) -> None:
    _need(value == expected, message)


def _default_validator() -> Any:
    import validate_unified_cognitive_fabric_receipt_v1 as validator

    return validator


def finalize_post_commit(
    *,
    admitted: Mapping[str, Any],
    generated: Mapping[str, Any],
    gated: Mapping[str, Any],
    committed: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    validator_module: Any | None = None,
) -> dict[str, Any]:
    """Finalize one already-committed candidate into canonical UCF runtime evidence.

    `generated.ucf_runtime_evidence` is explicitly pre-terminal evidence only. It may carry
    measured source/runtime/workspace/capability/execution-lane material, but it may not
    supply final authority, committed generation, candidate-result identity, terminal
    result identity or the UCF receipt envelope digest.
    """
    a = _mapping(admitted, "admitted")
    g = _mapping(generated, "generated")
    gate = _mapping(gated, "gated")
    commit = _mapping(committed, "committed")
    comp = _mapping(compiled, "compiled")
    pr = _mapping(prompt, "prompt")

    _need(a.get("ok") is True, "ADMISSION_NOT_SUCCESSFUL")
    _same(a.get("schema"), "mini-entity-cognitive-fabric-admission/v1", "ADMISSION_SCHEMA_MISMATCH")
    _need(g.get("ok") is True, "INFERENCE_NOT_SUCCESSFUL")
    _need(gate.get("ok") is True, "GATE_NOT_SUCCESSFUL")
    _need(commit.get("ok") is True, "COMMIT_NOT_SUCCESSFUL")

    admission_digest = _digest(
        a.get("cognitive_fabric_receipt_digest"),
        "cognitive_fabric_admission_receipt_digest",
    )
    packet_digest = _digest(a.get("inference_packet_digest"), "inference_packet_digest")
    _same(
        g.get("cognitive_fabric_admission_receipt_digest"),
        admission_digest,
        "ADMISSION_RECEIPT_IDENTITY_DRIFT",
    )
    _same(g.get("inference_packet_digest"), packet_digest, "INFERENCE_PACKET_IDENTITY_DRIFT")
    _same(a.get("canonical_state_hash"), comp.get("canonical_state_hash"), "CANONICAL_STATE_IDENTITY_DRIFT")
    _same(a.get("packet_hash"), comp.get("packet_hash"), "SOURCE_PACKET_IDENTITY_DRIFT")

    generated_payload = _mapping(g.get("payload"), "generated.payload")
    gated_payload = _mapping(gate.get("payload"), "gated.payload")
    _same(_sha256_obj(gated_payload), _sha256_obj(generated_payload), "GATE_CANDIDATE_IDENTITY_DRIFT")
    candidate_result_digest = _sha256_obj(generated_payload)

    admission_generation = a.get("generation")
    committed_generation = commit.get("generation")
    _need(type(admission_generation) is int and admission_generation >= 0, "ADMISSION_GENERATION_INVALID")
    _need(type(committed_generation) is int and committed_generation >= 0, "COMMIT_GENERATION_INVALID")
    _same(committed_generation, admission_generation + 1, "COMMIT_GENERATION_DRIFT")
    output_id = _text(commit.get("output_id"), "commit.output_id")

    evidence = _mapping(g.get("ucf_runtime_evidence"), "generated.ucf_runtime_evidence")
    for forbidden in ("authority", "receipt_envelope_digest"):
        _need(forbidden not in evidence, "PRETERMINAL_AUTHORITY_FIELD_FORBIDDEN:" + forbidden)
    receipt = copy.deepcopy(evidence)
    _same(receipt.get("schema"), "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1", "UCF_SCHEMA_MISMATCH")

    runtime = _mapping(receipt.get("runtime"), "ucf.runtime")
    runtime["generation"] = committed_generation
    receipt["runtime"] = runtime

    inference = _mapping(receipt.get("inference"), "ucf.inference")
    _same(inference.get("engine_class"), a.get("ucf_engine_class"), "UCF_ENGINE_CLASS_DRIFT")
    _same(inference.get("jspace_mode"), a.get("jspace_mode"), "UCF_JSPACE_MODE_DRIFT")
    _same(inference.get("adapter_version"), a.get("admission_receipt", {}).get("adapter_version"), "UCF_ADAPTER_VERSION_DRIFT")
    inference["inference_packet_digest"] = packet_digest
    inference["candidate_result_digest"] = candidate_result_digest
    inference["executed"] = True
    inference["candidate_only"] = True
    receipt["inference"] = inference

    identity = _mapping(receipt.get("identity"), "ucf.identity")
    _same(identity.get("zero_identity_digest"), a.get("admission_receipt", {}).get("zero_identity_digest"), "UCF_ZERO_IDENTITY_DRIFT")
    _same(identity.get("grf_digest"), a.get("admission_receipt", {}).get("grf_digest"), "UCF_GRF_IDENTITY_DRIFT")

    core = _mapping(receipt.get("bundled_core"), "ucf.bundled_core")
    admission_receipt = _mapping(a.get("admission_receipt"), "admission_receipt")
    _same(core.get("manifest_digest"), admission_receipt.get("bundled_manifest_digest"), "UCF_MANIFEST_IDENTITY_DRIFT")
    _same(core.get("checkpoint_digest"), admission_receipt.get("local_model_digest"), "UCF_MODEL_IDENTITY_DRIFT")
    _same(core.get("tokenizer_digest"), admission_receipt.get("tokenizer_digest"), "UCF_TOKENIZER_IDENTITY_DRIFT")
    _same(core.get("jspace_profile_digest"), admission_receipt.get("jspace_profile_digest"), "UCF_JSPACE_PROFILE_DRIFT")
    _same(core.get("lens_profile_digest"), admission_receipt.get("jacobian_lens_digest"), "UCF_LENS_IDENTITY_DRIFT")
    _same(core.get("workspace_calibration_digest"), admission_receipt.get("workspace_calibration_digest"), "UCF_WORKSPACE_CALIBRATION_DRIFT")

    binding = _mapping(receipt.get("binding"), "ucf.binding")
    _same(binding.get("zero_identity_digest"), admission_receipt.get("zero_identity_digest"), "UCF_ZERO_BINDING_DRIFT")
    _same(binding.get("grf_digest"), admission_receipt.get("grf_digest"), "UCF_GRF_BINDING_DRIFT")
    _same(binding.get("bundled_manifest_digest"), admission_receipt.get("bundled_manifest_digest"), "UCF_MANIFEST_BINDING_DRIFT")
    _same(binding.get("boot_binding_receipt_digest"), admission_receipt.get("boot_binding_digest"), "UCF_BOOT_BINDING_DRIFT")

    workspace = _mapping(receipt.get("workspace"), "ucf.workspace")
    _same(workspace.get("before_digest"), admission_receipt.get("workspace_digest"), "UCF_WORKSPACE_BEFORE_DRIFT")

    receipt["authority"] = {
        "candidate_requested_direct_state_mutation": False,
        "candidate_requested_direct_effect_mutation": False,
        "validation_decision": "ACCEPT",
        "canonical_write_committed": True,
        "effect_committed": False,
    }

    execution = _mapping(receipt.get("execution"), "ucf.execution")
    _need("terminal_result_digest" not in execution, "PRETERMINAL_RESULT_DIGEST_FORBIDDEN")
    terminal_material = {
        "schema": SCHEMA,
        "admission_receipt_digest": admission_digest,
        "inference_packet_digest": packet_digest,
        "candidate_result_digest": candidate_result_digest,
        "canonical_state_hash": _digest(comp.get("canonical_state_hash"), "canonical_state_hash"),
        "packet_hash": _digest(comp.get("packet_hash"), "packet_hash"),
        "output_id": output_id,
        "committed_generation": committed_generation,
        "prompt_digest": _sha256_obj(pr),
    }
    execution["terminal_result_digest"] = _sha256_obj(terminal_material)
    receipt["execution"] = execution

    freshness = _mapping(receipt.get("freshness"), "ucf.freshness")
    _same(freshness.get("stale_generation"), False, "STALE_GENERATION_AT_FINALIZATION")

    validator = validator_module or _default_validator()
    receipt["receipt_envelope_digest"] = validator.canonical_digest(receipt)
    validated = validator.validate(receipt)
    final_digest = _digest(validated.get("receipt_digest"), "ucf_runtime_receipt_digest")

    return {
        "ok": True,
        "schema": SCHEMA,
        "ucf_runtime_receipt_digest": final_digest,
        "terminal_result_digest": execution["terminal_result_digest"],
        "candidate_result_digest": candidate_result_digest,
        "committed_generation": committed_generation,
        "admission_receipt_digest": admission_digest,
        "inference_packet_digest": packet_digest,
        "receipt": receipt,
        "authority": "POST_COMMIT_EVIDENCE_ONLY_NO_WRITE_NO_EFFECT",
    }


__all__ = [
    "SCHEMA",
    "CognitiveFabricFinalizationError",
    "finalize_post_commit",
]
