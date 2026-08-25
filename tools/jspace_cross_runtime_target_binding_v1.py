#!/usr/bin/env python3
"""Bind a measured JSPACE_VECTOR_CONTROL_ABI/v1 packet to a distinct native runtime.

The current full-control ABI is source-runtime evidence.  A PyTorch hidden-state PASS must
not become native llama.cpp/cvec evidence by copying source runtime/checkpoint hashes or a
PyTorch activation-site name into a target claim.  This additive, noncanonical bridge makes
that cross-runtime boundary explicit without creating a second vector, truth, or effect
authority.

It intentionally does *not* execute a model and always emits runtime_observed=false.  Native
runtime credit requires a later exact-source execution receipt that consumes this binding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SOURCE_SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
SOURCE_ROLE = "FULL_CAUSAL_CONTROL_PACKET"
TARGET_SPEC_SCHEMA = "JSPACE_NATIVE_CVEC_TARGET_SPEC/v1"
BINDING_SCHEMA = "JSPACE_CROSS_RUNTIME_TARGET_BINDING/v1"
TRUTH_STATUS = "CANDIDATE_MEASUREMENT_ONLY"
CREDIT_SCOPE = "CROSS_RUNTIME_TARGET_BINDING_ONLY_NO_RUNTIME_OR_CANONICAL_PROMOTION"
NATIVE_CVEC_API = "llama_set_adapter_cvec"


class BindingError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise BindingError(code)


def _object(value: Any, code: str) -> dict[str, Any]:
    _require(isinstance(value, dict), code)
    return value


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git_sha40(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validated_source_packet(packet: Any) -> dict[str, Any]:
    packet = _object(packet, "SOURCE_PACKET_OBJECT_REQUIRED")
    _require(packet.get("schema") == SOURCE_SCHEMA, "SOURCE_PACKET_SCHEMA_INVALID")
    _require(packet.get("abi_role") == SOURCE_ROLE, "SOURCE_PACKET_ROLE_INVALID")
    _require(packet.get("canonical_truth") is False, "SOURCE_PACKET_TRUTH_FENCE_REQUIRED")
    _require(packet.get("truth_status") == TRUTH_STATUS, "SOURCE_PACKET_TRUTH_STATUS_INVALID")

    claimed = packet.get("packet_sha256")
    _require(_sha256(claimed), "SOURCE_PACKET_SHA256_REQUIRED")
    material = dict(packet)
    material.pop("packet_sha256", None)
    _require(claimed == digest(material), "SOURCE_PACKET_SHA256_MISMATCH")

    source = _object(packet.get("source_model_runtime_identity"), "SOURCE_RUNTIME_IDENTITY_REQUIRED")
    _require(_git_sha40(source.get("repo_head")), "SOURCE_REPO_HEAD_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        _require(_sha256(source.get(key)), f"SOURCE_RUNTIME_SHA256_REQUIRED:{key}")

    # The pre-existing v1 packet can legitimately describe a same-runtime target.  Before
    # crossing runtimes we require that its target hash triplet still equals the measured
    # source triplet; otherwise two independent target-binding mechanisms would be stacked.
    old_target = _object(packet.get("target_model_runtime_identity"), "SOURCE_PACKET_TARGET_IDENTITY_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        _require(old_target.get(key) == source.get(key), f"SOURCE_PACKET_ALREADY_CROSS_RUNTIME:{key}")

    vector = _object(packet.get("vector_identity"), "SOURCE_VECTOR_IDENTITY_REQUIRED")
    for key in ("source_packet_sha256", "local_vector_sha256", "applied_vector_sha256", "adapter_sha256"):
        _require(_sha256(vector.get(key)), f"SOURCE_VECTOR_SHA256_REQUIRED:{key}")
    _require(_nonempty(packet.get("target_activation_site")), "SOURCE_ACTIVATION_SITE_REQUIRED")
    _require(_nonempty(packet.get("intervention_operator")), "SOURCE_INTERVENTION_OPERATOR_REQUIRED")
    return packet


def _validated_target_spec(spec: Any, source_packet: dict[str, Any]) -> dict[str, Any]:
    spec = _object(spec, "TARGET_SPEC_OBJECT_REQUIRED")
    _require(spec.get("schema") == TARGET_SPEC_SCHEMA, "TARGET_SPEC_SCHEMA_INVALID")

    target = _object(spec.get("target_runtime_identity"), "TARGET_RUNTIME_IDENTITY_REQUIRED")
    for key in ("provider", "model_or_route", "execution_surface", "artifact_format"):
        _require(_nonempty(target.get(key)), f"TARGET_RUNTIME_FIELD_REQUIRED:{key}")
    _require(_git_sha40(target.get("runtime_source_commit")), "TARGET_RUNTIME_SOURCE_COMMIT_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        _require(_sha256(target.get(key)), f"TARGET_RUNTIME_SHA256_REQUIRED:{key}")

    source_runtime = source_packet["source_model_runtime_identity"]
    changed = any(
        target[key] != source_runtime[key]
        for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256")
    )
    _require(changed, "TARGET_RUNTIME_MUST_DIFFER_FROM_SOURCE")

    vector = _object(spec.get("target_vector_binding"), "TARGET_VECTOR_BINDING_REQUIRED")
    _require(vector.get("api_symbol") == NATIVE_CVEC_API, "TARGET_CVEC_API_SYMBOL_INVALID")
    _require(vector.get("source_local_vector_sha256") == source_packet["vector_identity"]["local_vector_sha256"], "SOURCE_LOCAL_VECTOR_IDENTITY_MISMATCH")
    _require(vector.get("source_applied_vector_sha256") == source_packet["vector_identity"]["applied_vector_sha256"], "SOURCE_APPLIED_VECTOR_IDENTITY_MISMATCH")
    _require(vector.get("source_activation_site") == source_packet["target_activation_site"], "SOURCE_ACTIVATION_SITE_MISMATCH")
    for key in ("target_cvec_sha256", "conversion_receipt_sha256", "dimension_receipt_sha256"):
        _require(_sha256(vector.get(key)), f"TARGET_VECTOR_SHA256_REQUIRED:{key}")
    _require(_positive_int(vector.get("source_vector_dimension")), "SOURCE_VECTOR_DIMENSION_REQUIRED")
    _require(_positive_int(vector.get("target_cvec_dimension")), "TARGET_CVEC_DIMENSION_REQUIRED")
    _require(vector.get("source_vector_dimension") == vector.get("target_cvec_dimension"), "CROSS_RUNTIME_VECTOR_DIMENSION_MISMATCH")
    _require(_nonempty(vector.get("conversion_method")), "VECTOR_CONVERSION_METHOD_REQUIRED")

    mapping = _object(vector.get("target_layer_mapping"), "TARGET_LAYER_MAPPING_REQUIRED")
    _require(isinstance(mapping.get("source_layer"), int) and mapping.get("source_layer") >= 0, "SOURCE_LAYER_REQUIRED")
    _require(isinstance(mapping.get("target_layer_start"), int) and mapping.get("target_layer_start") >= 0, "TARGET_LAYER_START_REQUIRED")
    _require(isinstance(mapping.get("target_layer_end"), int) and mapping.get("target_layer_end") >= mapping.get("target_layer_start"), "TARGET_LAYER_END_REQUIRED")
    _require(_nonempty(mapping.get("mapping_semantics")), "TARGET_LAYER_MAPPING_SEMANTICS_REQUIRED")
    _require(_sha256(mapping.get("mapping_receipt_sha256")), "TARGET_LAYER_MAPPING_RECEIPT_REQUIRED")

    _require(spec.get("native_runtime_observed") is False, "PREEXECUTION_BINDING_MUST_NOT_CLAIM_RUNTIME")
    return spec


def build_binding(source_packet: dict[str, Any], target_spec: dict[str, Any]) -> dict[str, Any]:
    packet = _validated_source_packet(source_packet)
    spec = _validated_target_spec(target_spec, packet)
    source_runtime = packet["source_model_runtime_identity"]
    target_runtime = spec["target_runtime_identity"]
    vector = spec["target_vector_binding"]

    binding = {
        "schema": BINDING_SCHEMA,
        "truth_status": TRUTH_STATUS,
        "canonical_truth": False,
        "credit_scope": CREDIT_SCOPE,
        "runtime_observed": False,
        "source_control_packet": {
            "schema": SOURCE_SCHEMA,
            "packet_sha256": packet["packet_sha256"],
        },
        "source_model_runtime_identity": source_runtime,
        "target_model_runtime_identity": target_runtime,
        "runtime_identity_relation": "EXPLICIT_CROSS_RUNTIME_TARGET",
        "source_intervention": {
            "activation_site": packet["target_activation_site"],
            "operator": packet["intervention_operator"],
            "local_vector_sha256": packet["vector_identity"]["local_vector_sha256"],
            "applied_vector_sha256": packet["vector_identity"]["applied_vector_sha256"],
        },
        "target_intervention": {
            "api_symbol": vector["api_symbol"],
            "target_cvec_sha256": vector["target_cvec_sha256"],
            "source_vector_dimension": vector["source_vector_dimension"],
            "target_cvec_dimension": vector["target_cvec_dimension"],
            "conversion_method": vector["conversion_method"],
            "conversion_receipt_sha256": vector["conversion_receipt_sha256"],
            "dimension_receipt_sha256": vector["dimension_receipt_sha256"],
            "target_layer_mapping": vector["target_layer_mapping"],
        },
        "promotion_fences": {
            "source_component_credit_preserved": True,
            "native_cvec_runtime_credit": False,
            "full_hcu_runtime_credit": False,
            "training_credit": False,
            "whole_product_pass": False,
            "requires_exact_runtime_consumption_receipt": True,
        },
    }
    binding["binding_sha256"] = digest(binding)
    return binding


def validate_binding(binding: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not isinstance(binding, dict):
        return False, ["BINDING_OBJECT_REQUIRED"]
    if binding.get("schema") != BINDING_SCHEMA:
        failures.append("BINDING_SCHEMA_INVALID")
    if binding.get("canonical_truth") is not False or binding.get("truth_status") != TRUTH_STATUS:
        failures.append("BINDING_TRUTH_FENCE_INVALID")
    if binding.get("credit_scope") != CREDIT_SCOPE or binding.get("runtime_observed") is not False:
        failures.append("BINDING_CREDIT_SCOPE_INVALID")
    if binding.get("runtime_identity_relation") != "EXPLICIT_CROSS_RUNTIME_TARGET":
        failures.append("BINDING_RUNTIME_RELATION_INVALID")
    claimed = binding.get("binding_sha256")
    if not _sha256(claimed):
        failures.append("BINDING_SHA256_REQUIRED")
    else:
        material = dict(binding)
        material.pop("binding_sha256", None)
        if claimed != digest(material):
            failures.append("BINDING_SHA256_MISMATCH")
    fences = binding.get("promotion_fences")
    if not isinstance(fences, dict) or fences.get("native_cvec_runtime_credit") is not False or fences.get("requires_exact_runtime_consumption_receipt") is not True:
        failures.append("BINDING_PROMOTION_FENCE_INVALID")
    return not failures, failures


def adjudicate(source_packet: Any, target_spec: Any) -> dict[str, Any]:
    try:
        binding = build_binding(source_packet, target_spec)
        valid, failures = validate_binding(binding)
        if not valid:
            raise BindingError("BINDING_VALIDATION_FAILED:" + ",".join(failures))
        return {
            "schema": "JSPACE_CROSS_RUNTIME_TARGET_BINDING_ADMISSION/v1",
            "status": "PASS",
            "failures": [],
            "binding": binding,
            "canonical_credit_minted": False,
            "native_cvec_runtime_credit_minted": False,
            "full_hcu_runtime_credit_minted": False,
            "training_credit_minted": False,
        }
    except Exception as exc:
        return {
            "schema": "JSPACE_CROSS_RUNTIME_TARGET_BINDING_ADMISSION/v1",
            "status": "BLOCKED",
            "failures": [str(exc)],
            "binding": None,
            "canonical_credit_minted": False,
            "native_cvec_runtime_credit_minted": False,
            "full_hcu_runtime_credit_minted": False,
            "training_credit_minted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-packet", required=True, type=Path)
    parser.add_argument("--target-spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        packet = json.loads(args.source_packet.read_text(encoding="utf-8"))
        spec = json.loads(args.target_spec.read_text(encoding="utf-8"))
        result = adjudicate(packet, spec)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": result["status"], "output": str(args.output)}, sort_keys=True))
        return 0 if result["status"] == "PASS" else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": f"{type(exc).__name__}:{str(exc)[:800]}"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
