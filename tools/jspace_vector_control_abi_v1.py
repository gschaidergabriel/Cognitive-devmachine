#!/usr/bin/env python3
"""Canonical full-control packet builder/validator for JSPACE_VECTOR_CONTROL_ABI/v1.

This module deliberately reserves JSPACE_VECTOR_CONTROL_ABI/v1 for a *full causal
control packet*.  It is not a q8 wire codec schema and not a partial derivation
hash preimage.  Existing historical/donor uses remain provenance, but new packets
must satisfy this fail-closed contract.

The builder consumes an already evidence-bearing Trigger-1 direct steering candidate.
It never upgrades runtime/model/canonical credit.  Missing operator, token-position,
off-target metric, or magnitude-envelope evidence blocks packet construction rather
than being inferred from narration or control names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "JSPACE_VECTOR_CONTROL_ABI/v1"
ABI_ROLE = "FULL_CAUSAL_CONTROL_PACKET"
CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
EVIDENCE_SCHEMA = "JSPACE_VECTOR_CONTROL_EXPLICIT_EVIDENCE/v1"
TRUTH_STATUS = "CANDIDATE_MEASUREMENT_ONLY"
CREDIT_SCOPE = "JSPACE_CONTROL_PACKET_ONLY_NO_CANONICAL_OR_MODEL_PROMOTION"

REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
ALLOWED_OPERATORS = {
    "ADD",
    "ABLATE",
    "PROJECT_OUT",
    "PATCH",
    "SWAP",
    "RESCUE",
}


class AbiError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AbiError(code)


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


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _object(value: Any, code: str) -> dict[str, Any]:
    _require(isinstance(value, dict), code)
    return value


def _validate_control_receipts(controls: Any) -> dict[str, str]:
    controls = _object(controls, "CONTROLS_OBJECT_REQUIRED")
    receipts: dict[str, str] = {}
    for name in REQUIRED_CONTROLS:
        row = controls.get(name)
        _require(isinstance(row, dict), f"CONTROL_REQUIRED:{name}")
        receipt = row.get("runtime_receipt_sha256")
        _require(_sha256(receipt), f"CONTROL_RUNTIME_RECEIPT_REQUIRED:{name}")
        receipts[name] = str(receipt)
    return receipts


def _validate_identity(candidate: dict[str, Any]) -> dict[str, Any]:
    identity = _object(candidate.get("source_identity"), "SOURCE_IDENTITY_REQUIRED")
    _require(_git_sha40(identity.get("repo_head")), "EXACT_REPO_HEAD_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        _require(_sha256(identity.get(key)), f"IDENTITY_SHA256_REQUIRED:{key}")
    return identity


def _validate_explicit_evidence(candidate: dict[str, Any], gain: float) -> dict[str, Any]:
    evidence = _object(candidate.get("jspace_vector_control_evidence"), "EXPLICIT_CONTROL_ABI_EVIDENCE_REQUIRED")
    _require(evidence.get("schema") == EVIDENCE_SCHEMA, "EXPLICIT_CONTROL_ABI_EVIDENCE_SCHEMA_INVALID")

    operator = evidence.get("intervention_operator")
    _require(operator in ALLOWED_OPERATORS, "INTERVENTION_OPERATOR_REQUIRED_OR_UNSUPPORTED")
    _require(_nonempty(evidence.get("token_position_policy")), "TOKEN_POSITION_POLICY_REQUIRED")

    target_metric = _object(evidence.get("target_metric_definition"), "TARGET_METRIC_DEFINITION_REQUIRED")
    off_target_metric = _object(evidence.get("off_target_metric_definition"), "OFF_TARGET_METRIC_DEFINITION_REQUIRED")
    _require(bool(target_metric), "TARGET_METRIC_DEFINITION_REQUIRED")
    _require(bool(off_target_metric), "OFF_TARGET_METRIC_DEFINITION_REQUIRED")
    _require(canonical_json(target_metric) != canonical_json(off_target_metric), "TARGET_AND_OFFTARGET_METRICS_MUST_DIFFER")

    envelope = _object(evidence.get("allowed_magnitude_envelope"), "ALLOWED_MAGNITUDE_ENVELOPE_REQUIRED")
    gain_min = envelope.get("gain_min")
    gain_max = envelope.get("gain_max")
    _require(_finite_number(gain_min) and _finite_number(gain_max), "GAIN_ENVELOPE_NUMBERS_REQUIRED")
    gain_min_f = float(gain_min)
    gain_max_f = float(gain_max)
    _require(gain_min_f <= gain_max_f, "GAIN_ENVELOPE_ORDER_INVALID")
    _require(gain_min_f <= gain <= gain_max_f, "APPLIED_GAIN_OUTSIDE_ALLOWED_ENVELOPE")
    _require(_sha256(envelope.get("envelope_receipt_sha256")), "MAGNITUDE_ENVELOPE_RECEIPT_REQUIRED")

    _require(evidence.get("holdout_used_for_derivation") is False, "EXPLICIT_HOLDOUT_DERIVATION_FENCE_REQUIRED")
    _require(_sha256(evidence.get("frozen_calibration_receipt_sha256")), "FROZEN_CALIBRATION_RECEIPT_REQUIRED")
    return evidence


def build_packet(candidate: dict[str, Any]) -> dict[str, Any]:
    """Build one canonical full-control packet from explicit measured evidence."""
    _require(isinstance(candidate, dict), "CANDIDATE_OBJECT_REQUIRED")
    _require(candidate.get("schema") == CANDIDATE_SCHEMA, "CANDIDATE_SCHEMA_INVALID")

    identity = _validate_identity(candidate)
    intervention = _object(candidate.get("intervention"), "INTERVENTION_IDENTITY_REQUIRED")
    _require(intervention.get("runtime_observed") is True, "RUNTIME_OBSERVED_INTERVENTION_REQUIRED")
    for key in (
        "source_packet_sha256",
        "adapter_sha256",
        "local_vector_sha256",
        "applied_vector_sha256",
        "runtime_intervention_receipt_sha256",
    ):
        _require(_sha256(intervention.get(key)), f"INTERVENTION_SHA256_REQUIRED:{key}")
    _require(_nonempty(intervention.get("activation_site")), "ACTIVATION_SITE_REQUIRED")
    _require(_nonempty(intervention.get("invocation_id")), "INTERVENTION_INVOCATION_ID_REQUIRED")
    _require(_finite_number(intervention.get("gain")), "INTERVENTION_GAIN_REQUIRED")
    gain = float(intervention["gain"])

    derivation = _object(candidate.get("vector_derivation"), "VECTOR_DERIVATION_EVIDENCE_REQUIRED")
    _require(_nonempty(derivation.get("method")), "VECTOR_DERIVATION_METHOD_REQUIRED")
    _require(_nonempty(derivation.get("derivation_family_id")), "VECTOR_DERIVATION_FAMILY_ID_REQUIRED")
    _require(_sha256(derivation.get("derivation_receipt_sha256")), "VECTOR_DERIVATION_RECEIPT_REQUIRED")
    _require(derivation.get("uses_holdout_data") is False, "VECTOR_DERIVATION_MUST_NOT_USE_HOLDOUT_DATA")
    _require(derivation.get("uses_evaluation_output_labels") is False, "VECTOR_DERIVATION_MUST_NOT_USE_EVALUATION_OUTPUT_LABELS")

    calibration = _object(candidate.get("calibration"), "CALIBRATION_EVIDENCE_REQUIRED")
    holdout = _object(candidate.get("holdout"), "HOLDOUT_EVIDENCE_REQUIRED")
    _require(_nonempty(calibration.get("family_id")), "CALIBRATION_FAMILY_ID_REQUIRED")
    _require(_nonempty(holdout.get("family_id")), "HOLDOUT_FAMILY_ID_REQUIRED")
    _require(calibration.get("family_id") != holdout.get("family_id"), "CALIBRATION_HOLDOUT_FAMILY_MUST_DIFFER")
    _require(holdout.get("evaluation_independent_of_vector_derivation") is True, "HOLDOUT_EVALUATION_INDEPENDENCE_REQUIRED")
    _require(_sha256(holdout.get("metric_definition_sha256")), "HOLDOUT_METRIC_DEFINITION_RECEIPT_REQUIRED")

    target = _object(candidate.get("target"), "TARGET_RUNTIME_IDENTITY_REQUIRED")
    _require(_nonempty(target.get("provider")), "TARGET_PROVIDER_REQUIRED")
    _require(_nonempty(target.get("model_or_route")), "TARGET_MODEL_OR_ROUTE_REQUIRED")
    _require(_nonempty(target.get("execution_surface")), "TARGET_EXECUTION_SURFACE_REQUIRED")

    control_receipts = _validate_control_receipts(candidate.get("controls"))
    explicit = _validate_explicit_evidence(candidate, gain)

    packet = {
        "schema": SCHEMA,
        "abi_role": ABI_ROLE,
        "truth_status": TRUTH_STATUS,
        "canonical_truth": False,
        "credit_scope": CREDIT_SCOPE,
        "source_candidate": {
            "schema": CANDIDATE_SCHEMA,
            "sha256": digest(candidate),
            "invocation_id": intervention["invocation_id"],
        },
        "source_trace_or_derivation_family_id": derivation["derivation_family_id"],
        "source_model_runtime_identity": {
            "repo_head": identity["repo_head"],
            "runtime_build_sha256": identity["runtime_build_sha256"],
            "checkpoint_sha256": identity["checkpoint_sha256"],
            "tokenizer_sha256": identity["tokenizer_sha256"],
        },
        "target_model_runtime_identity": {
            "provider": target["provider"],
            "model_or_route": target["model_or_route"],
            "execution_surface": target["execution_surface"],
            "runtime_build_sha256": identity["runtime_build_sha256"],
            "checkpoint_sha256": identity["checkpoint_sha256"],
            "tokenizer_sha256": identity["tokenizer_sha256"],
        },
        "target_activation_site": intervention["activation_site"],
        "vector_identity": {
            "source_packet_sha256": intervention["source_packet_sha256"],
            "local_vector_sha256": intervention["local_vector_sha256"],
            "applied_vector_sha256": intervention["applied_vector_sha256"],
            "adapter_sha256": intervention["adapter_sha256"],
        },
        "construction_method": derivation["method"],
        "derivation_evidence": {
            "derivation_family_id": derivation["derivation_family_id"],
            "derivation_receipt_sha256": derivation["derivation_receipt_sha256"],
            "holdout_used_for_derivation": explicit["holdout_used_for_derivation"],
            "frozen_calibration_receipt_sha256": explicit["frozen_calibration_receipt_sha256"],
        },
        "gain_policy": {
            "applied_gain": gain,
            "calibration_family_id": calibration["family_id"],
            "allowed_magnitude_envelope": explicit["allowed_magnitude_envelope"],
        },
        "token_position_policy": explicit["token_position_policy"],
        "intervention_operator": explicit["intervention_operator"],
        "matched_control_family": {
            "required": list(REQUIRED_CONTROLS),
            "runtime_receipts": control_receipts,
        },
        "target_metric_definition": explicit["target_metric_definition"],
        "target_metric_definition_sha256": digest(explicit["target_metric_definition"]),
        "off_target_metric_definition": explicit["off_target_metric_definition"],
        "off_target_metric_definition_sha256": digest(explicit["off_target_metric_definition"]),
        "holdout_identity": {
            "family_id": holdout["family_id"],
            "metric_definition_sha256": holdout["metric_definition_sha256"],
            "evaluation_independent_of_vector_derivation": True,
        },
        "causal_receipt_identity": intervention["runtime_intervention_receipt_sha256"],
        "namespace_semantics": {
            "full_control_packet": True,
            "q8_wire_codec": False,
            "partial_derivation_descriptor": False,
        },
    }
    packet["packet_sha256"] = digest(packet)
    return packet


def validate_packet(packet: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not isinstance(packet, dict):
        return False, ["PACKET_OBJECT_REQUIRED"]
    if packet.get("schema") != SCHEMA:
        failures.append("SCHEMA_INVALID")
    if packet.get("abi_role") != ABI_ROLE:
        failures.append("JSPACE_VECTOR_CONTROL_ABI_ROLE_COLLISION")
    if packet.get("truth_status") != TRUTH_STATUS or packet.get("canonical_truth") is not False:
        failures.append("TRUTH_AUTHORITY_FENCE_INVALID")
    if packet.get("credit_scope") != CREDIT_SCOPE:
        failures.append("CREDIT_SCOPE_INVALID")
    if packet.get("namespace_semantics") != {
        "full_control_packet": True,
        "q8_wire_codec": False,
        "partial_derivation_descriptor": False,
    }:
        failures.append("NAMESPACE_SEMANTICS_INVALID")
    claimed = packet.get("packet_sha256")
    if not _sha256(claimed):
        failures.append("PACKET_SHA256_REQUIRED")
    else:
        material = dict(packet)
        material.pop("packet_sha256", None)
        if claimed != digest(material):
            failures.append("PACKET_SHA256_MISMATCH")
    return not failures, failures


def adjudicate(candidate: Any) -> dict[str, Any]:
    try:
        packet = build_packet(candidate)
        valid, failures = validate_packet(packet)
        if not valid:
            raise AbiError("PACKET_VALIDATION_FAILED:" + ",".join(failures))
        return {
            "schema": "JSPACE_VECTOR_CONTROL_ABI_ADMISSION/v1",
            "status": "PASS",
            "failures": [],
            "packet": packet,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
        }
    except Exception as exc:
        return {
            "schema": "JSPACE_VECTOR_CONTROL_ABI_ADMISSION/v1",
            "status": "BLOCKED",
            "failures": [str(exc)],
            "packet": None,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    except Exception as exc:
        result = {
            "schema": "JSPACE_VECTOR_CONTROL_ABI_ADMISSION/v1",
            "status": "BLOCKED",
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "packet": None,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
        }
    else:
        result = adjudicate(candidate)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
