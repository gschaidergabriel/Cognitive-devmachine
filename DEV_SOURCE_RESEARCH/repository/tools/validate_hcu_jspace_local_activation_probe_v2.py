#!/usr/bin/env python3
"""Fail-closed validator for ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2.

A PASS validates only the bounded raw probe envelope. Intervention-mode PASS does not
promote J-Space causality: the raw probe intentionally lacks exact loader-consumption
attestation and predeclared acceptance thresholds and must remain UNASSESSED_CANDIDATE_ONLY.
"""
from __future__ import annotations

import json
import math
import re
import sys
from typing import Any

SCHEMA = "ENTITYOS_HCU_JSPACE_LOCAL_ACTIVATION_PROBE/v2"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CORE_INTERVENTION_CONDITIONS = {
    "BASELINE_CLEAN",
    "BASELINE_CORRUPTED",
    "INTERVENTION_TARGET",
    "SHAM_CONTROL",
    "OFF_TARGET_CONTROL",
}
TECHNICAL_INTERVENTION_CONDITION = "BASELINE_CLEAN_OFF_TARGET_REFERENCE"


class ProbeReceiptError(ValueError):
    pass


def _obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if type(value) is not dict:
        raise ProbeReceiptError(f"{key}:OBJECT_REQUIRED")
    return value


def _list(parent: dict[str, Any], key: str, *, nonempty: bool = False) -> list[Any]:
    value = parent.get(key)
    if type(value) is not list or (nonempty and not value):
        raise ProbeReceiptError(f"{key}:LIST_REQUIRED")
    return value


def _text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if type(value) is not str or not value:
        raise ProbeReceiptError(f"{key}:TEXT_REQUIRED")
    return value


def _bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        raise ProbeReceiptError(f"{key}:BOOL_REQUIRED")
    return value


def _int(parent: dict[str, Any], key: str, *, minimum: int = 0) -> int:
    value = parent.get(key)
    if type(value) is not int or value < minimum:
        raise ProbeReceiptError(f"{key}:NONNEGATIVE_INT_REQUIRED")
    return value


def _hex(parent: dict[str, Any], key: str, pattern: re.Pattern[str] = HEX64) -> str:
    value = _text(parent, key)
    if pattern.fullmatch(value) is None or value in {"0" * len(value), "f" * len(value)}:
        raise ProbeReceiptError(f"{key}:DIGEST_INVALID")
    return value


def _finite_number(parent: dict[str, Any], key: str) -> float:
    value = parent.get(key)
    if type(value) not in {int, float} or isinstance(value, bool) or not math.isfinite(float(value)):
        raise ProbeReceiptError(f"{key}:FINITE_NUMBER_REQUIRED")
    return float(value)


def _condition_map(probe: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = _list(probe, "conditions", nonempty=True)
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ProbeReceiptError(f"conditions[{index}]:OBJECT_REQUIRED")
        name = _text(row, "condition")
        if name in result:
            raise ProbeReceiptError(f"CONDITION_DUPLICATE:{name}")
        _hex(row, "model_execution_id_derived_local")
        _hex(row, "jspace_trace_id_derived_local")
        if _bool(row, "derived_ids_are_canonical"):
            raise ProbeReceiptError("DERIVED_LOCAL_IDS_CANNOT_BE_CANONICAL")
        _int(row, "layer")
        _text(row, "activation_site")
        _hex(row, "activation_before_sha256_float32")
        _hex(row, "activation_after_sha256_float32")
        shape = _list(row, "activation_shape", nonempty=True)
        if not all(type(x) is int and x > 0 for x in shape):
            raise ProbeReceiptError("ACTIVATION_SHAPE_INVALID")
        _text(row, "activation_dtype")
        _hex(row, "final_logits_sha256_float32")
        if _text(row, "field_classification") != "OBSERVED_RUNTIME_MEASUREMENT_WITH_DERIVED_LOCAL_IDS":
            raise ProbeReceiptError("CONDITION_FIELD_CLASSIFICATION_INVALID")
        result[name] = row
    return result


def validate(receipt: dict[str, Any]) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise ProbeReceiptError("ROOT_OBJECT_REQUIRED")
    if receipt.get("schema") != SCHEMA:
        raise ProbeReceiptError("SCHEMA_MISMATCH")
    if receipt.get("program") != "ENTITYOS_HCU" or receipt.get("product") != "EntityOS" or receipt.get("architecture") != "HCU":
        raise ProbeReceiptError("PRODUCT_AUTHORITY_MISMATCH")
    if receipt.get("mode") != "FREE_ONLY_LOCAL_OFFLINE":
        raise ProbeReceiptError("EXECUTION_MODE_MISMATCH")
    probe_mode = _text(receipt, "probe_mode")
    if probe_mode not in {"observation", "intervention"}:
        raise ProbeReceiptError("PROBE_MODE_INVALID")
    expected_classification = (
        "LOCAL_MODEL_SPECIFIC_OBSERVATION_CANDIDATE_EVIDENCE_ONLY"
        if probe_mode == "observation"
        else "LOCAL_MODEL_SPECIFIC_CAUSAL_CANDIDATE_EVIDENCE_ONLY"
    )
    if receipt.get("classification") != expected_classification:
        raise ProbeReceiptError("PROBE_CLASSIFICATION_MISMATCH")

    _hex(receipt, "source_git_head", HEX40)
    _hex(receipt, "probe_source_sha256")
    if _int(receipt, "network_attempt_count") != 0:
        raise ProbeReceiptError("OFFLINE_NETWORK_ATTEMPT_OBSERVED")
    if "failure" in receipt:
        raise ProbeReceiptError("FAILED_PROBE_NOT_ADMISSIBLE")

    authority = _obj(receipt, "authority")
    _text(authority, "epoch")
    _hex(authority, "inbox_sha256")
    _hex(authority, "steering_sha256")

    binding = _obj(receipt, "causal_binding")
    for key in ("generation", "causal_event_id", "admission_id", "route_id", "inference_receipt_id"):
        _text(binding, key)

    model_source = _obj(receipt, "model_source_identity")
    _hex(model_source, "tree_sha256")
    files = _list(model_source, "files", nonempty=True)
    for row in files:
        if type(row) is not dict:
            raise ProbeReceiptError("MODEL_SOURCE_FILE_OBJECT_REQUIRED")
        _text(row, "path")
        _int(row, "size")
        _hex(row, "sha256")

    post_load = _obj(receipt, "post_load_identity")
    _hex(post_load, "post_load_parameter_value_sha256_float32_canonical")
    _int(post_load, "parameter_tensors")
    _int(post_load, "parameter_elements")
    if _bool(post_load, "loader_consumption_attestation"):
        raise ProbeReceiptError("RAW_PROBE_CANNOT_SELF_ATTEST_LOADER_CONSUMPTION")
    if post_load.get("field_classification") != "OBSERVED_POST_LOAD_VALUE_IDENTITY_PARTIAL":
        raise ProbeReceiptError("POST_LOAD_IDENTITY_CLASSIFICATION_INVALID")

    credit = _obj(receipt, "credit")
    for key in ("entityos_hcu_whole_runtime", "hcu_full_runtime", "jspace_model_runtime", "training"):
        if _int(credit, key) != 0:
            raise ProbeReceiptError(f"CREDIT_INFLATION_FORBIDDEN:{key}")
    if _bool(credit, "whole_product_pass"):
        raise ProbeReceiptError("WHOLE_PRODUCT_PASS_FORBIDDEN")

    promotion = _obj(receipt, "promotion")
    if promotion.get("status") != "UNASSESSED_CANDIDATE_ONLY":
        raise ProbeReceiptError("RAW_PROBE_PROMOTION_FORBIDDEN")
    _text(promotion, "reason")

    probe = _obj(receipt, "probe")
    layer = _int(probe, "layer")
    _int(probe, "target_position")
    _hex(probe, "clean_token_ids_sha256")
    conditions = _condition_map(probe)
    if not all(row["layer"] == layer for row in conditions.values()):
        raise ProbeReceiptError("CONDITION_LAYER_MISMATCH")

    lease = _obj(receipt, "atomic_experiment_lease")
    if probe_mode == "observation":
        if lease.get("status") != "NOT_REQUIRED_OBSERVATION_ONLY_NO_HIDDEN_STATE_MODIFICATION":
            raise ProbeReceiptError("OBSERVATION_LEASE_STATUS_INVALID")
        if _bool(lease, "unusual_intervention_performed"):
            raise ProbeReceiptError("OBSERVATION_CANNOT_CLAIM_INTERVENTION")
        if set(conditions) != {"OBSERVATION_BASELINE_CLEAN"}:
            raise ProbeReceiptError("OBSERVATION_CONDITION_SET_INVALID")
        row = conditions["OBSERVATION_BASELINE_CLEAN"]
        if row["activation_before_sha256_float32"] != row["activation_after_sha256_float32"]:
            raise ProbeReceiptError("OBSERVATION_MODIFIED_HIDDEN_STATE")
        for metric_key in ("target_logit", "off_target_logit", "target_token_id", "off_target_token_id"):
            if metric_key in row:
                raise ProbeReceiptError("OBSERVATION_INTERVENTION_METRIC_LEAK")
    else:
        if lease.get("lease_file_validated") is not True:
            raise ProbeReceiptError("INTERVENTION_ATOMIC_LEASE_NOT_VALIDATED")
        for key in ("trigger_key", "claim_path", "claim_sha256", "claimant_organ", "experiment_name", "intervention_contract"):
            _text(lease, key)
        required = CORE_INTERVENTION_CONDITIONS | {TECHNICAL_INTERVENTION_CONDITION}
        if set(conditions) != required:
            missing = sorted(required - set(conditions))
            extra = sorted(set(conditions) - required)
            raise ProbeReceiptError(f"INTERVENTION_CONDITION_SET_INVALID:missing={missing}:extra={extra}")
        _int(probe, "off_target_position")
        _hex(probe, "corrupted_token_ids_sha256")
        metrics = _obj(probe, "derived_metrics")
        for key in (
            "target_patch_effect_on_target_logit",
            "sham_effect_on_target_logit",
            "off_target_patch_effect_on_target_logit",
            "target_patch_effect_on_off_target_logit",
        ):
            _finite_number(metrics, key)
        clean = conditions["BASELINE_CLEAN"]
        corrupt = conditions["BASELINE_CORRUPTED"]
        target = conditions["INTERVENTION_TARGET"]
        sham = conditions["SHAM_CONTROL"]
        clean_off = conditions[TECHNICAL_INTERVENTION_CONDITION]
        off = conditions["OFF_TARGET_CONTROL"]
        if clean["activation_before_sha256_float32"] != clean["activation_after_sha256_float32"]:
            raise ProbeReceiptError("CLEAN_BASELINE_MODIFIED")
        if corrupt["activation_before_sha256_float32"] != corrupt["activation_after_sha256_float32"]:
            raise ProbeReceiptError("CORRUPTED_BASELINE_MODIFIED")
        if target["activation_after_sha256_float32"] != clean["activation_before_sha256_float32"]:
            raise ProbeReceiptError("TARGET_PATCH_NOT_BOUND_TO_CLEAN_ACTIVATION")
        if sham["activation_after_sha256_float32"] != corrupt["activation_before_sha256_float32"]:
            raise ProbeReceiptError("SHAM_PATCH_NOT_BOUND_TO_CORRUPTED_ACTIVATION")
        if off["activation_after_sha256_float32"] != clean_off["activation_before_sha256_float32"]:
            raise ProbeReceiptError("OFF_TARGET_PATCH_NOT_BOUND_TO_CLEAN_REFERENCE")

    return {
        "ok": True,
        "schema": SCHEMA,
        "probe_mode": probe_mode,
        "source_git_head": receipt["source_git_head"],
        "promotion": "UNASSESSED_CANDIDATE_ONLY",
        "credit": "ZERO",
    }


def main() -> int:
    try:
        value = json.load(sys.stdin)
        result = validate(value)
    except (json.JSONDecodeError, ProbeReceiptError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
