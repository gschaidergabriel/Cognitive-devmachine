#!/usr/bin/env python3
"""Fail-closed validator for JSPACE_GWT_CAUSAL_DISCRIMINATOR_RECEIPT/v1.

This receipt binds one matched three-arm discriminator:
  baseline vs targeted J-Space/workspace perturbation vs matched non-J-Space control.

A PASS means only that the experiment envelope is structurally and cryptographically
coherent enough to retain as bounded research evidence. A single receipt MUST NOT mint
causal-use, model-quality, Whole-GWT, factual-truth, or whole-product credit.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from typing import Any

SCHEMA = "JSPACE_GWT_CAUSAL_DISCRIMINATOR_RECEIPT/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
MODES = {"LOCAL_LATENT", "COMPILED_EXTERNAL"}
METRICS = {"TASK_SCORE_DELTA", "OUTPUT_KL", "TOP1_FLIP", "WORKSPACE_RECALL_DELTA"}
COST_CLASSES = {"LOCAL", "FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}
LOCAL_KINDS = {
    "baseline": "NONE",
    "target": "JSPACE_TARGET_ABLATION",
    "control": "MATCHED_NON_JSPACE_ABLATION",
}
EXTERNAL_KINDS = {
    "baseline": "NONE",
    "target": "JSPACE_WORKSPACE_PROJECTION_ABLATION",
    "control": "MATCHED_NON_JSPACE_CONTEXT_CONTROL",
}


class ReceiptError(ValueError):
    pass


def _obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if type(value) is not dict:
        raise ReceiptError(f"{key}:OBJECT_REQUIRED")
    return value


def _text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if type(value) is not str or not value:
        raise ReceiptError(f"{key}:TEXT_REQUIRED")
    return value


def _bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        raise ReceiptError(f"{key}:BOOL_REQUIRED")
    return value


def _count(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if type(value) is not int or value < 0:
        raise ReceiptError(f"{key}:NONNEGATIVE_INT_REQUIRED")
    return value


def _finite_number(parent: dict[str, Any], key: str, *, nonnegative: bool = False) -> float:
    value = parent.get(key)
    if type(value) not in {int, float} or type(value) is bool or not math.isfinite(float(value)):
        raise ReceiptError(f"{key}:FINITE_NUMBER_REQUIRED")
    number = float(value)
    if nonnegative and number < 0:
        raise ReceiptError(f"{key}:NONNEGATIVE_REQUIRED")
    return number


def _is_placeholder_hex(value: str) -> bool:
    return value == ("0" * len(value)) or value == ("f" * len(value))


def _hex(parent: dict[str, Any], key: str, pattern: re.Pattern[str], *, nullable: bool = False) -> str | None:
    value = parent.get(key)
    if value is None and nullable:
        return None
    value = _text(parent, key)
    if pattern.fullmatch(value) is None:
        raise ReceiptError(f"{key}:DIGEST_FORMAT")
    if _is_placeholder_hex(value):
        raise ReceiptError(f"{key}:IDENTITY_PLACEHOLDER")
    return value


def _finite_json(value: Any, path: str = "$") -> None:
    t = type(value)
    if value is None or t in {str, bool, int}:
        return
    if t is float:
        if not math.isfinite(value):
            raise ReceiptError(f"NONFINITE_JSON:{path}")
        return
    if t is list:
        for index, item in enumerate(value):
            _finite_json(item, f"{path}[{index}]")
        return
    if t is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ReceiptError(f"NONSTRING_JSON_KEY:{path}")
            _finite_json(item, f"{path}.{key}")
        return
    raise ReceiptError(f"UNSUPPORTED_JSON_TYPE:{path}:{t.__name__}")


def canonical_digest(receipt: dict[str, Any]) -> str:
    material = copy.deepcopy(receipt)
    material.pop("receipt_envelope_digest", None)
    _finite_json(material)
    raw = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_arm(
    arm_name: str,
    arm: dict[str, Any],
    *,
    generation: int,
    input_digest: str,
    decoding_digest: str,
    engine_digest: str,
    expected_kind: str,
    mode: str,
) -> dict[str, Any]:
    _text(arm, "run_id")
    if _count(arm, "entity_generation") != generation:
        raise ReceiptError(f"{arm_name}:GENERATION_MISMATCH")
    if _hex(arm, "input_digest", HEX64) != input_digest:
        raise ReceiptError(f"{arm_name}:INPUT_MISMATCH")
    if _hex(arm, "decoding_config_digest", HEX64) != decoding_digest:
        raise ReceiptError(f"{arm_name}:DECODING_MISMATCH")
    if _hex(arm, "engine_identity_digest", HEX64) != engine_digest:
        raise ReceiptError(f"{arm_name}:ENGINE_IDENTITY_MISMATCH")

    intervention_kind = _text(arm, "intervention_kind")
    if intervention_kind != expected_kind:
        raise ReceiptError(f"{arm_name}:INTERVENTION_KIND_MISMATCH")
    intervention_digest = _hex(arm, "intervention_digest", HEX64, nullable=True)
    if arm_name == "baseline":
        if intervention_digest is not None:
            raise ReceiptError("BASELINE_INTERVENTION_MUST_BE_NULL")
    elif intervention_digest is None:
        raise ReceiptError(f"{arm_name}:INTERVENTION_DIGEST_REQUIRED")

    _hex(arm, "workspace_projection_digest", HEX64)
    result_digest = _hex(arm, "candidate_result_digest", HEX64)
    _hex(arm, "behavior_measurement_digest", HEX64)
    _hex(arm, "telemetry_digest", HEX64)

    if _bool(arm, "executed") is not True:
        raise ReceiptError(f"{arm_name}:EXECUTION_REQUIRED")
    hidden_state_access = _bool(arm, "hidden_state_access")
    provider_hidden_state_claimed = _bool(arm, "provider_hidden_state_claimed")
    if mode == "COMPILED_EXTERNAL":
        if hidden_state_access:
            raise ReceiptError(f"{arm_name}:EXTERNAL_HIDDEN_STATE_ACCESS_FORBIDDEN")
        if provider_hidden_state_claimed:
            raise ReceiptError(f"{arm_name}:EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN")
    elif not hidden_state_access:
        raise ReceiptError(f"{arm_name}:LOCAL_LATENT_REQUIRES_HIDDEN_STATE_ACCESS")

    return {
        "result_digest": result_digest,
        "intervention_digest": intervention_digest,
    }


def validate(receipt: dict[str, Any]) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise ReceiptError("ROOT_OBJECT_REQUIRED")
    _finite_json(receipt)
    if receipt.get("schema") != SCHEMA:
        raise ReceiptError("SCHEMA_MISMATCH")

    source = _obj(receipt, "source")
    runtime = _obj(receipt, "runtime")
    identity = _obj(receipt, "identity")
    experiment = _obj(receipt, "experiment")
    pairing = _obj(receipt, "pairing")
    comparison = _obj(receipt, "comparison")
    execution = _obj(receipt, "execution")

    source_commit = _hex(source, "commit", GIT_OID)
    _hex(source, "tree", GIT_OID)
    if source.get("dirty") is not False:
        raise ReceiptError("SOURCE_DIRTY_OR_UNKNOWN")

    generation = _count(runtime, "entity_generation")
    if generation < 1:
        raise ReceiptError("ENTITY_GENERATION_MUST_BE_POSITIVE")
    _hex(runtime, "runtime_identity_digest", HEX64)
    _hex(runtime, "bundled_manifest_digest", HEX64)
    _hex(runtime, "boot_binding_receipt_digest", HEX64)
    _hex(runtime, "jspace_profile_digest", HEX64)
    _hex(runtime, "lens_artifact_digest", HEX64)
    _hex(runtime, "workspace_calibration_digest", HEX64)

    _hex(identity, "zero_identity_digest", HEX64)
    _hex(identity, "grf_digest", HEX64)
    _hex(identity, "workspace_policy_digest", HEX64)

    mode = _text(experiment, "mode")
    if mode not in MODES:
        raise ReceiptError("MODE_UNSUPPORTED")
    metric = _text(experiment, "metric")
    if metric not in METRICS:
        raise ReceiptError("METRIC_UNSUPPORTED")
    _hex(experiment, "task_digest", HEX64)
    input_digest = _hex(experiment, "input_digest", HEX64)
    decoding_digest = _hex(experiment, "decoding_config_digest", HEX64)
    engine_digest = _hex(experiment, "engine_identity_digest", HEX64)
    _hex(experiment, "inference_packet_digest", HEX64)

    required_pairing = (
        "same_task",
        "same_input",
        "same_decoding_config",
        "same_engine_identity",
        "same_generation",
        "only_intervention_differs",
        "control_capacity_matched",
    )
    for key in required_pairing:
        if _bool(pairing, key) is not True:
            raise ReceiptError(f"PAIRING_REQUIRED:{key}")

    arms = _obj(experiment, "arms")
    expected = LOCAL_KINDS if mode == "LOCAL_LATENT" else EXTERNAL_KINDS
    arm_results: dict[str, dict[str, Any]] = {}
    run_ids: list[str] = []
    for arm_name in ("baseline", "target", "control"):
        arm = _obj(arms, arm_name)
        run_ids.append(_text(arm, "run_id"))
        arm_results[arm_name] = _validate_arm(
            arm_name,
            arm,
            generation=generation,
            input_digest=input_digest,
            decoding_digest=decoding_digest,
            engine_digest=engine_digest,
            expected_kind=expected[arm_name],
            mode=mode,
        )
    if len(set(run_ids)) != 3:
        raise ReceiptError("RUN_ID_REUSE_FORBIDDEN")
    if arm_results["target"]["intervention_digest"] == arm_results["control"]["intervention_digest"]:
        raise ReceiptError("TARGET_CONTROL_INTERVENTION_ALIAS")

    if mode == "LOCAL_LATENT":
        if _bool(experiment, "local_activation_access") is not True:
            raise ReceiptError("LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS")
        if _bool(experiment, "external_hidden_state_claimed"):
            raise ReceiptError("LOCAL_MODE_EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN")
    else:
        if _bool(experiment, "local_activation_access"):
            raise ReceiptError("COMPILED_EXTERNAL_LOCAL_ACTIVATION_CLAIM_FORBIDDEN")
        if _bool(experiment, "external_hidden_state_claimed"):
            raise ReceiptError("COMPILED_EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN")

    target_effect = _finite_number(comparison, "target_effect", nonnegative=True)
    control_effect = _finite_number(comparison, "control_effect", nonnegative=True)
    minimum_margin = _finite_number(comparison, "minimum_margin", nonnegative=True)
    reported_margin = _finite_number(comparison, "target_minus_control_margin")
    computed_margin = target_effect - control_effect
    if abs(reported_margin - computed_margin) > 1e-12:
        raise ReceiptError("COMPARISON_MARGIN_MISMATCH")
    if _bool(comparison, "matched_controls_passed") is not True:
        raise ReceiptError("MATCHED_CONTROLS_REQUIRED")

    # This single-trial receipt is deliberately non-promotional. Even a large observed
    # margin is bounded evidence to be replicated/aggregated elsewhere.
    if _bool(comparison, "causal_use_claimed"):
        raise ReceiptError("SINGLE_DISCRIMINATOR_CANNOT_CLAIM_CAUSAL_USE")
    if _text(comparison, "causal_use_credit") != "ZERO_SINGLE_TRIAL":
        raise ReceiptError("CAUSAL_USE_CREDIT_MUST_REMAIN_ZERO")
    if _text(comparison, "whole_gwt_credit") != "ZERO":
        raise ReceiptError("WHOLE_GWT_CREDIT_MUST_REMAIN_ZERO")
    if _text(comparison, "whole_product_credit") != "ZERO":
        raise ReceiptError("WHOLE_PRODUCT_CREDIT_MUST_REMAIN_ZERO")

    free_only = _bool(execution, "free_only")
    cost_class = _text(execution, "lane_cost_class")
    if cost_class not in COST_CLASSES:
        raise ReceiptError("LANE_COST_CLASS_INVALID")
    if _bool(execution, "lane_admitted") is not True:
        raise ReceiptError("EXECUTED_DISCRIMINATOR_REQUIRES_ADMITTED_LANE")
    secret_lookups = _count(execution, "secret_lookup_count")
    network_touches = _count(execution, "network_touch_count")
    if free_only and cost_class not in {"LOCAL", "FREE"}:
        raise ReceiptError("FREE_ONLY_NONFREE_DISCRIMINATOR_FORBIDDEN")
    if mode == "LOCAL_LATENT" and (secret_lookups or network_touches):
        raise ReceiptError("LOCAL_LATENT_DISCRIMINATOR_MUST_BE_OFFLINE")
    _hex(execution, "policy_authority_digest", HEX64)

    envelope_digest = _hex(receipt, "receipt_envelope_digest", HEX64)
    if envelope_digest != canonical_digest(receipt):
        raise ReceiptError("RECEIPT_ENVELOPE_DIGEST_MISMATCH")

    return {
        "ok": True,
        "schema": SCHEMA,
        "receipt_digest": envelope_digest,
        "source_commit": source_commit,
        "entity_generation": generation,
        "mode": mode,
        "metric": metric,
        "target_minus_control_margin": computed_margin,
        "minimum_margin": minimum_margin,
        "margin_meets_declared_threshold": computed_margin >= minimum_margin,
        "causal_use_credit": "ZERO_SINGLE_TRIAL",
        "whole_gwt_credit": "ZERO",
        "whole_product_credit": "ZERO",
    }


def main() -> int:
    try:
        receipt = json.load(
            sys.stdin,
            parse_constant=lambda value: (_ for _ in ()).throw(ReceiptError(f"NONFINITE_JSON_CONSTANT:{value}")),
        )
        result = validate(receipt)
    except (ReceiptError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
