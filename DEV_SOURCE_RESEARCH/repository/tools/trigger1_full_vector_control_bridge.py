#!/usr/bin/env python3
"""Fail-closed successor from the retained Trigger-1 direct candidate to full J-Space control ABI.

This stage does not execute a model and does not invent missing scientific facts.  It binds
predeclared intervention semantics to the exact Git blob of the retained intermediate executor,
recomputes calibration/holdout adjudication from raw measured rows, derives an exact frozen-gain
envelope, binds the existing wrong-layer localization measurement as a distinct off-target metric,
and only then asks `jspace_vector_control_abi_v1` to build `JSPACE_VECTOR_CONTROL_ABI/v1`.

Any executor drift, missing measured row, changed calibration selection, absent wrong-layer receipt,
or ABI mismatch blocks.  PASS is source/evidence-shape readiness only; it mints no model-runtime,
training, canonical-truth, HCU-full, or whole-product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import jspace_vector_control_abi_v1 as abi
import trigger1_intermediate_contrastive_protocol as protocol
import trigger1_intermediate_promotion_bridge as bridge

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "research_entity/claycode/TRIGGER1_INTERMEDIATE_FULL_CONTROL_SOURCE_CONTRACT_V1.json"
CONTRACT_SCHEMA = "TRIGGER1_INTERMEDIATE_FULL_CONTROL_SOURCE_CONTRACT/v1"
BRIDGE_SCHEMA = "CLAY_TRIGGER1_JSPACE_FULL_CONTROL_BRIDGE/v1"
EVIDENCE_SCHEMA = "JSPACE_VECTOR_CONTROL_EXPLICIT_EVIDENCE/v1"


class FullControlBridgeError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FullControlBridgeError(code)


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite(value: Any) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), "FINITE_NUMBER_REQUIRED")
    parsed = float(value)
    _require(math.isfinite(parsed), "FINITE_NUMBER_REQUIRED")
    return parsed


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def load_source_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise FullControlBridgeError(f"SOURCE_CONTRACT_INVALID:{type(exc).__name__}") from exc
    _require(isinstance(contract, dict), "SOURCE_CONTRACT_OBJECT_REQUIRED")
    _require(contract.get("schema") == CONTRACT_SCHEMA, "SOURCE_CONTRACT_SCHEMA_INVALID")
    executor_rel = contract.get("executor_path")
    _require(isinstance(executor_rel, str) and executor_rel, "SOURCE_CONTRACT_EXECUTOR_PATH_REQUIRED")
    executor = ROOT / executor_rel
    _require(executor.is_file(), "SOURCE_CONTRACT_EXECUTOR_MISSING")
    expected_blob = contract.get("executor_git_blob_sha1")
    actual_blob = git_blob_sha1(executor)
    _require(isinstance(expected_blob, str) and len(expected_blob) == 40, "SOURCE_CONTRACT_EXECUTOR_BLOB_REQUIRED")
    _require(actual_blob == expected_blob, "EXECUTOR_SOURCE_CONTRACT_BLOB_MISMATCH")
    controlled = contract.get("controlled_intervention")
    _require(isinstance(controlled, dict), "SOURCE_CONTRACT_INTERVENTION_REQUIRED")
    _require(controlled.get("control") == "+VECTOR", "SOURCE_CONTRACT_CONTROL_INVALID")
    _require(controlled.get("intervention_operator") == "ADD", "SOURCE_CONTRACT_OPERATOR_INVALID")
    _require(
        controlled.get("token_position_policy") == "LAST_INPUT_TOKEN_AT_SELECTED_LAYER_OUTPUT",
        "SOURCE_CONTRACT_TOKEN_POSITION_POLICY_INVALID",
    )
    return contract


def _recompute_result(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(result.get("schema") == bridge.INTERMEDIATE_SCHEMA, "INTERMEDIATE_RESULT_SCHEMA_INVALID")
    _require(result.get("status") == "PASS", "INTERMEDIATE_RESULT_PASS_REQUIRED")
    calibration = result.get("calibration_rows")
    holdout = result.get("holdout_rows")
    _require(isinstance(calibration, list) and calibration, "CALIBRATION_ROWS_REQUIRED")
    _require(isinstance(holdout, list) and holdout, "HOLDOUT_ROWS_REQUIRED")
    recomputed_selected = protocol.select_layer_gain(calibration)
    _require(recomputed_selected.get("selected") is True, "CALIBRATION_RECOMPUTE_DID_NOT_SELECT")
    _require(recomputed_selected == result.get("selected"), "CALIBRATION_SELECTION_RECOMPUTE_MISMATCH")
    layer = recomputed_selected.get("layer")
    gain = recomputed_selected.get("gain")
    _require(isinstance(layer, int) and layer >= 0, "SELECTED_LAYER_REQUIRED")
    selected_gain = _finite(gain)
    recomputed_verdict = protocol.adjudicate_holdout(
        holdout,
        selected_layer=layer,
        selected_gain=selected_gain,
    )
    _require(recomputed_verdict == result.get("verdict"), "HOLDOUT_VERDICT_RECOMPUTE_MISMATCH")
    _require(recomputed_verdict.get("pass") is True, "INTERMEDIATE_PROTOCOL_PASS_REQUIRED")
    return recomputed_selected, recomputed_verdict


def _validate_direct_candidate(
    result: dict[str, Any],
    candidate: dict[str, Any],
    selected: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    _require(candidate.get("schema") == bridge.DIRECT_SCHEMA, "DIRECT_CANDIDATE_SCHEMA_INVALID")
    source = result.get("source")
    identity = candidate.get("source_identity")
    _require(isinstance(source, dict) and isinstance(identity, dict), "SOURCE_IDENTITY_REQUIRED")
    _require(identity.get("repo_head") == source.get("repo_head"), "DIRECT_REPO_HEAD_MISMATCH")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        _require(_sha256(result.get(key)), f"RESULT_IDENTITY_SHA_REQUIRED:{key}")
        _require(identity.get(key) == result.get(key), f"DIRECT_IDENTITY_MISMATCH:{key}")

    intervention = candidate.get("intervention")
    _require(isinstance(intervention, dict), "DIRECT_INTERVENTION_REQUIRED")
    _require(intervention.get("runtime_observed") is True, "DIRECT_RUNTIME_INTERVENTION_REQUIRED")
    layer = int(selected["layer"])
    gain = float(selected["gain"])
    controlled = contract["controlled_intervention"]
    expected_site = str(controlled["activation_site_template"]).format(selected_layer=layer)
    _require(intervention.get("activation_site") == expected_site, "DIRECT_ACTIVATION_SITE_CONTRACT_MISMATCH")
    _require(_finite(intervention.get("gain")) == gain, "DIRECT_GAIN_MISMATCH")
    _require(intervention.get("layer_start") == layer and intervention.get("layer_end") == layer, "DIRECT_LAYER_RANGE_MISMATCH")
    for key in (
        "source_packet_sha256",
        "adapter_sha256",
        "local_vector_sha256",
        "applied_vector_sha256",
        "runtime_intervention_receipt_sha256",
    ):
        _require(_sha256(intervention.get(key)), f"DIRECT_INTERVENTION_SHA_REQUIRED:{key}")

    holdout = candidate.get("holdout")
    _require(isinstance(holdout, dict), "DIRECT_HOLDOUT_REQUIRED")
    _require(holdout.get("evaluation_independent_of_vector_derivation") is True, "DIRECT_HOLDOUT_INDEPENDENCE_REQUIRED")
    _require(holdout.get("label_mapping_counterbalanced") is True, "DIRECT_COUNTERBALANCE_REQUIRED")
    _require(
        holdout.get("metric_definition_sha256") == bridge.digest(bridge.METRIC_DEFINITION),
        "DIRECT_TARGET_METRIC_MISMATCH",
    )


def _wrong_layer_measurement(result: dict[str, Any], selected_layer: int) -> dict[str, Any]:
    holdout = result["holdout_rows"]
    plus_rows = [row for row in holdout if row.get("control") == "+VECTOR" and int(row.get("layer", -1)) == selected_layer]
    _require(bool(plus_rows), "PLUS_VECTOR_HOLDOUT_REQUIRED")
    measurements: list[dict[str, Any]] = []
    for row in plus_rows:
        _require(int(row.get("hook_calls", 0)) > 0, "PLUS_VECTOR_RUNTIME_HOOK_REQUIRED")
        _require(_sha256(row.get("runtime_receipt_sha256")), "PLUS_VECTOR_RUNTIME_RECEIPT_REQUIRED")
        _require(row.get("wrong_layer_same_selected_vector") is True, "WRONG_LAYER_SAME_SELECTED_VECTOR_REQUIRED")
        wrong_layer = row.get("wrong_layer")
        _require(isinstance(wrong_layer, int) and not isinstance(wrong_layer, bool), "WRONG_LAYER_REQUIRED")
        _require(wrong_layer != selected_layer, "WRONG_LAYER_MUST_DIFFER")
        _require(row.get("wrong_layer_vector_source_layer") == selected_layer, "WRONG_LAYER_VECTOR_SOURCE_MISMATCH")
        _require(_sha256(row.get("wrong_layer_receipt_sha256")), "WRONG_LAYER_RUNTIME_RECEIPT_REQUIRED")
        _require(_sha256(row.get("lesion_receipt_sha256")), "LESION_RUNTIME_RECEIPT_REQUIRED")
        _require(_sha256(row.get("rescue_receipt_sha256")), "RESCUE_RUNTIME_RECEIPT_REQUIRED")
        wrong_delta = _finite(row.get("wrong_layer_delta"))
        _require(wrong_delta < 0.0, "WRONG_LAYER_LOCALIZATION_EFFECT_NOT_STRICTLY_NEGATIVE")
        _require(_finite(row.get("lesion_delta")) <= 0.0, "LESION_CONTROL_FAILED")
        _require(_finite(row.get("rescue_delta")) > 0.0, "RESCUE_CONTROL_FAILED")
        measurements.append({
            "prompt_sha256": row.get("prompt_sha256"),
            "seed": row.get("seed"),
            "label_map_id": row.get("label_map_id"),
            "selected_layer": selected_layer,
            "wrong_layer": wrong_layer,
            "wrong_layer_delta": wrong_delta,
            "plus_vector_runtime_receipt_sha256": row.get("runtime_receipt_sha256"),
            "wrong_layer_runtime_receipt_sha256": row.get("wrong_layer_receipt_sha256"),
            "lesion_runtime_receipt_sha256": row.get("lesion_receipt_sha256"),
            "rescue_runtime_receipt_sha256": row.get("rescue_receipt_sha256"),
        })
    return {
        "schema": "TRIGGER1_WRONG_LAYER_LOCALIZATION_MEASUREMENT_FAMILY/v1",
        "rows": measurements,
        "family_sha256": digest(measurements),
    }


def build_explicit_evidence(
    result: dict[str, Any],
    direct_candidate: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(isinstance(result, dict) and isinstance(direct_candidate, dict), "JSON_OBJECTS_REQUIRED")
    contract = contract or load_source_contract()
    selected, _verdict = _recompute_result(result)
    _validate_direct_candidate(result, direct_candidate, selected, contract)

    selected_layer = int(selected["layer"])
    selected_gain = float(selected["gain"])
    wrong_layer_family = _wrong_layer_measurement(result, selected_layer)
    calibration_sha = digest(result["calibration_rows"])
    frozen_calibration_material = {
        "schema": "TRIGGER1_FROZEN_CALIBRATION_RECEIPT/v1",
        "calibration_rows_sha256": calibration_sha,
        "selected": selected,
        "repo_head": direct_candidate["source_identity"]["repo_head"],
        "executor_git_blob_sha1": contract["executor_git_blob_sha1"],
    }
    frozen_calibration_receipt_sha = digest(frozen_calibration_material)
    envelope_material = {
        "schema": "TRIGGER1_EXACT_SELECTED_GAIN_ENVELOPE/v1",
        "gain_min": selected_gain,
        "gain_max": selected_gain,
        "calibration_rows_sha256": calibration_sha,
        "selection_sha256": selected.get("selection_sha256"),
        "frozen_calibration_receipt_sha256": frozen_calibration_receipt_sha,
    }
    envelope_receipt_sha = digest(envelope_material)

    target_contract = contract.get("target_metric")
    off_target_contract = contract.get("off_target_metric")
    _require(isinstance(target_contract, dict) and isinstance(off_target_contract, dict), "SOURCE_CONTRACT_METRICS_REQUIRED")
    _require(target_contract.get("schema") == bridge.METRIC_DEFINITION.get("schema"), "TARGET_METRIC_SCHEMA_CONTRACT_MISMATCH")
    _require(target_contract.get("score") == bridge.METRIC_DEFINITION.get("score"), "TARGET_METRIC_SCORE_CONTRACT_MISMATCH")

    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "intervention_operator": contract["controlled_intervention"]["intervention_operator"],
        "token_position_policy": contract["controlled_intervention"]["token_position_policy"],
        "target_metric_definition": bridge.METRIC_DEFINITION,
        "off_target_metric_definition": off_target_contract,
        "allowed_magnitude_envelope": {
            "gain_min": selected_gain,
            "gain_max": selected_gain,
            "envelope_receipt_sha256": envelope_receipt_sha,
        },
        "holdout_used_for_derivation": False,
        "frozen_calibration_receipt_sha256": frozen_calibration_receipt_sha,
        "source_contract_sha256": digest(contract),
        "executor_git_blob_sha1": contract["executor_git_blob_sha1"],
        "wrong_layer_measurement_family_sha256": wrong_layer_family["family_sha256"],
        "provenance_scope": "EXACT_EXECUTOR_SOURCE_POLICY_PLUS_RECOMPUTED_MEASURED_ROWS",
    }
    enriched = dict(direct_candidate)
    enriched["jspace_vector_control_evidence"] = evidence
    admission = abi.adjudicate(enriched)
    _require(admission.get("status") == "PASS", "FULL_CONTROL_ABI_ADMISSION_BLOCKED:" + ",".join(admission.get("failures") or []))
    packet = admission.get("packet")
    _require(isinstance(packet, dict) and packet.get("schema") == abi.SCHEMA, "FULL_CONTROL_PACKET_REQUIRED")
    return enriched, admission


def adjudicate(result: Any, direct_candidate: Any) -> dict[str, Any]:
    try:
        contract = load_source_contract()
        enriched, admission = build_explicit_evidence(result, direct_candidate, contract)
        return {
            "schema": BRIDGE_SCHEMA,
            "status": "PASS",
            "failures": [],
            "source_contract_sha256": digest(contract),
            "executor_git_blob_sha1": contract["executor_git_blob_sha1"],
            "direct_candidate_sha256": digest(direct_candidate),
            "enriched_candidate_sha256": digest(enriched),
            "enriched_candidate": enriched,
            "abi_admission": admission,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
            "whole_product_credit_minted": False,
            "evidence_scope": "FULL_CONTROL_SOURCE_AND_EVIDENCE_SHAPE_READINESS_ONLY",
        }
    except Exception as exc:
        return {
            "schema": BRIDGE_SCHEMA,
            "status": "BLOCKED",
            "failures": [str(exc)],
            "enriched_candidate": None,
            "abi_admission": None,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
            "whole_product_credit_minted": False,
            "evidence_scope": "NONE",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--direct-candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = json.loads(args.result.read_text(encoding="utf-8"))
        direct_candidate = json.loads(args.direct_candidate.read_text(encoding="utf-8"))
    except Exception as exc:
        verdict = {
            "schema": BRIDGE_SCHEMA,
            "status": "BLOCKED",
            "failures": [f"INPUT_JSON_INVALID:{type(exc).__name__}"],
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
            "whole_product_credit_minted": False,
            "evidence_scope": "NONE",
        }
    else:
        verdict = adjudicate(result, direct_candidate)
    args.output.write_text(json.dumps(verdict, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": verdict.get("schema"),
        "status": verdict.get("status"),
        "failures": verdict.get("failures"),
        "output": str(args.output),
    }, sort_keys=True))
    return 0 if verdict.get("status") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
