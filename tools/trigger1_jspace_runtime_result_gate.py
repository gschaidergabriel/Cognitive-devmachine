#!/usr/bin/env python3
"""Bind a Trigger-1 local J-Space promotion candidate to its measured runtime result.

The base promotion gate validates the candidate contract. This successor gate adds an
independent, deterministic reconstruction of the local runtime-execution receipt and
of the control/intervention digests from the persisted runtime result. A syntactically
valid 64-hex receipt claim is therefore insufficient: the candidate must match the
measured result byte-for-semantics at the identities that matter for promotion.

This gate is intentionally local-runtime-specific. It does not grant canonical,
whole-EntityOS/HCU, J-Space model-runtime, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate as base_gate

SCHEMA = "CLAY_TRIGGER1_JSPACE_RUNTIME_RESULT_BINDING_GATE/v1"
LOCAL_RESULT_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v1"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _runtime_receipt_material(result: dict[str, Any]) -> dict[str, Any]:
    calibration_rows = _list(result.get("calibration_rows"))
    holdout_rows = _list(result.get("holdout_rows"))
    return {
        "endpoint": result.get("api_endpoint"),
        "runtime_build_sha256": result.get("runtime_build_sha256"),
        "checkpoint_sha256": result.get("checkpoint_sha256"),
        "tokenizer_sha256": result.get("tokenizer_sha256"),
        "source": result.get("source"),
        "api_invocations": len(calibration_rows) + len(holdout_rows),
    }


def _control_receipts_from_result(result: dict[str, Any]) -> dict[str, str]:
    rows = [row for row in _list(result.get("holdout_rows")) if isinstance(row, dict)]
    out: dict[str, str] = {}
    for control in base_gate.REQUIRED_CONTROLS:
        receipts = [row.get("runtime_receipt_sha256") for row in rows if row.get("control") == control]
        out[control] = canonical_sha(receipts)
    return out


def bind(candidate: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    base = base_gate.adjudicate(candidate)

    if result.get("schema") != LOCAL_RESULT_SCHEMA:
        failures.append("LOCAL_RUNTIME_RESULT_SCHEMA_INVALID")
    if result.get("status") != "PASS":
        failures.append("LOCAL_RUNTIME_RESULT_PASS_REQUIRED")
    if result.get("api_loopback_only") is not True:
        failures.append("RESULT_LOOPBACK_ONLY_REQUIRED")
    if result.get("zero_provider_billing") is not True:
        failures.append("RESULT_ZERO_PROVIDER_BILLING_REQUIRED")
    if result.get("external_provider_credentials_read") is not False:
        failures.append("RESULT_ZERO_EXTERNAL_PROVIDER_CREDENTIAL_READ_REQUIRED")

    source = _dict(result.get("source"))
    identity = _dict(candidate.get("source_identity"))
    target = _dict(candidate.get("target"))
    transport = _dict(candidate.get("transport"))
    intervention = _dict(candidate.get("intervention"))
    controls = _dict(candidate.get("controls"))
    calibration = _dict(candidate.get("calibration"))
    holdout = _dict(candidate.get("holdout"))

    if target.get("execution_surface") != base_gate.LOCAL_API_SURFACE:
        failures.append("LOCAL_RUNTIME_RESULT_BINDING_GATE_LOCAL_ONLY")
    if identity.get("repo_head") != source.get("repo_head"):
        failures.append("RESULT_REPO_HEAD_MISMATCH")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        if identity.get(key) != result.get(key):
            failures.append(f"RESULT_IDENTITY_MISMATCH:{key}")

    endpoint = result.get("api_endpoint")
    if transport.get("endpoint") != endpoint:
        failures.append("RESULT_LOOPBACK_ENDPOINT_MISMATCH")
    expected_model_route = f"{result.get('model')}@{result.get('model_revision')}"
    if target.get("provider") != "local" or target.get("model_or_route") != expected_model_route:
        failures.append("RESULT_LOCAL_MODEL_ROUTE_MISMATCH")

    expected_receipt_sha = canonical_sha(_runtime_receipt_material(result))
    if target.get("local_runtime_execution_receipt_sha256") != expected_receipt_sha:
        failures.append("LOCAL_RUNTIME_EXECUTION_RECEIPT_DIGEST_MISMATCH")

    rows = [row for row in _list(result.get("holdout_rows")) if isinstance(row, dict)]
    expected_control_receipts = _control_receipts_from_result(result)
    for control in base_gate.REQUIRED_CONTROLS:
        row = _dict(controls.get(control))
        if row.get("runtime_receipt_sha256") != expected_control_receipts[control]:
            failures.append(f"CONTROL_RESULT_RECEIPT_MISMATCH:{control}")
        observed_count = sum(1 for item in rows if item.get("control") == control)
        if row.get("observations") is not None and row.get("observations") != observed_count:
            failures.append(f"CONTROL_RESULT_OBSERVATION_COUNT_MISMATCH:{control}")

    holdout_receipts = [row.get("runtime_receipt_sha256") for row in rows]
    plus_rows = [row for row in rows if row.get("control") == "+VECTOR"]
    plus_receipts = [row.get("runtime_receipt_sha256") for row in plus_rows]
    if intervention.get("invocation_id") != canonical_sha(holdout_receipts):
        failures.append("INTERVENTION_INVOCATION_RESULT_MISMATCH")
    if intervention.get("runtime_intervention_receipt_sha256") != canonical_sha(plus_receipts):
        failures.append("INTERVENTION_RECEIPT_RESULT_MISMATCH")
    if plus_rows and intervention.get("applied_vector_sha256") != plus_rows[0].get("applied_vector_sha256"):
        failures.append("APPLIED_VECTOR_RESULT_MISMATCH")
    if intervention.get("gain") != result.get("selected_gain"):
        failures.append("INTERVENTION_GAIN_RESULT_MISMATCH")
    if calibration.get("selected_gain") is not None and calibration.get("selected_gain") != result.get("selected_gain"):
        failures.append("CALIBRATION_GAIN_RESULT_MISMATCH")

    verdict = _dict(result.get("verdict"))
    expected_analysis_sha = canonical_sha({"verdict": verdict, "holdout_receipts": holdout_receipts})
    if holdout.get("analysis_receipt_sha256") != expected_analysis_sha:
        failures.append("HOLDOUT_ANALYSIS_RESULT_MISMATCH")
    if holdout.get("reproducible_directional_effect") is not bool(verdict.get("pass")):
        failures.append("HOLDOUT_VERDICT_RESULT_MISMATCH")

    if candidate.get("intervention", {}).get("source_packet_sha256") != result.get("source_packet_sha256"):
        failures.append("SOURCE_PACKET_RESULT_MISMATCH")
    if candidate.get("intervention", {}).get("adapter_sha256") != result.get("adapter_sha256"):
        failures.append("ADAPTER_RESULT_MISMATCH")
    if candidate.get("intervention", {}).get("local_vector_sha256") != result.get("local_vector_sha256"):
        failures.append("LOCAL_VECTOR_RESULT_MISMATCH")

    binding_pass = not failures
    base_goal = base.get("owner_trigger1_goal_credit_candidate") is True
    promoted_candidate = bool(base_goal and binding_pass)
    return {
        "schema": SCHEMA,
        "base_promotion_gate": base,
        "runtime_result_binding_pass": binding_pass,
        "mechanism_runtime_vector_credit_candidate": bool(
            base.get("mechanism_runtime_vector_credit_candidate") is True and binding_pass
        ),
        "owner_trigger1_goal_credit_candidate": promoted_candidate,
        "owner_trigger1_direct_free_api_model_credit_candidate": promoted_candidate,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "failures": sorted(set(failures)),
        "reconstructed_local_runtime_execution_receipt_sha256": expected_receipt_sha,
        "evidence_boundary": (
            "PASS remains a promotion-candidate result only. It proves that the local candidate contract is "
            "deterministically bound to the persisted runtime result identities, invocation/control receipts, "
            "loopback surface and zero-provider-billing assertions."
        ),
    }


def bind_files(candidate_path: Path, result_path: Path) -> dict[str, Any]:
    try:
        candidate_raw = candidate_path.read_bytes()
        result_raw = result_path.read_bytes()
        candidate = json.loads(candidate_raw)
        result = json.loads(result_raw)
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": SCHEMA,
            "runtime_result_binding_pass": False,
            "mechanism_runtime_vector_credit_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [f"INPUT_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict) or not isinstance(result, dict):
        return {
            "schema": SCHEMA,
            "runtime_result_binding_pass": False,
            "mechanism_runtime_vector_credit_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": ["INPUT_OBJECTS_REQUIRED"],
        }
    verdict = bind(candidate, result)
    verdict["candidate_path"] = str(candidate_path)
    verdict["runtime_result_path"] = str(result_path)
    verdict["candidate_sha256"] = _sha256_bytes(candidate_raw)
    verdict["runtime_result_file_sha256"] = _sha256_bytes(result_raw)
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    verdict = bind_files(Path(args.candidate), Path(args.result))
    print(json.dumps(verdict, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
