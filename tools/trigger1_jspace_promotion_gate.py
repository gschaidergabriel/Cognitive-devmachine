#!/usr/bin/env python3
"""Fail-closed evidence gate for Trigger-1 direct J-Space/vector-steering claims.

Trigger-1 V2 is goal-bound rather than provider-bound. A local loopback target
must carry executable evidence, not merely an opaque 64-hex receipt claim.
Terminal output-projection shortcuts remain technical positive controls only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v2"
LOCAL_RESULT_SCHEMA = "CLAY_TRIGGER1_LOCAL_QWEN06_ACTIVATION_API_EXPERIMENT/v1"
LOCAL_RESULT_FILENAME = "trigger1_local_activation_api_result.json"
REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
INSTRUMENTED_RUNTIME_CLASSES = {
    "LOCAL_PYTORCH_ACTIVATION_INTERVENTION",
    "LOCAL_LLAMA_CPP_CVEC_APPLIED",
    "PROVIDER_RUNTIME_INTERNAL_VECTOR_INTERVENTION",
    "OTHER_RUNTIME_OBSERVED_INTERNAL_INTERVENTION",
}
OWNER_API_TARGET_CLASS = "ZERO_COST_API_SERVED_MODEL_RUNTIME"
LEGACY_OWNER_API_TARGET_CLASS = "EXACT_ADMITTED_FREE_API_MODEL_RUNTIME"
LOCAL_API_SURFACE = "LOCAL_LOOPBACK_API"
EXTERNAL_API_SURFACE = "FREE_EXTERNAL_API"
TERMINAL_OUTPUT_SITE_MARKERS = (
    "lm_head",
    "output_head",
    "model.model.norm:output",
    "final_norm:output",
    "final_layer_norm:output",
)


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _loopback_url(value: Any) -> bool:
    if not _nonempty(value):
        return False
    try:
        parsed = urlparse(str(value))
    except Exception:
        return False
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"127.0.0.1", "localhost", "::1"}


def _causal_site_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    intervention = candidate.get("intervention")
    if not isinstance(intervention, dict):
        return False, ["INTERVENTION_IDENTITY_REQUIRED"]
    site = intervention.get("activation_site")
    if not _nonempty(site):
        return False, ["ACTIVATION_SITE_REQUIRED"]
    normalized = str(site).strip().lower().replace(" ", "")
    if intervention.get("terminal_output_projection_shortcut") is True or any(
        marker in normalized for marker in TERMINAL_OUTPUT_SITE_MARKERS
    ):
        failures.append("TERMINAL_OUTPUT_PROJECTION_SHORTCUT_NOT_JSPACE_CAUSAL_EVIDENCE")
    return not failures, failures


def _control_receipts(controls: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not isinstance(controls, dict):
        return False, ["CONTROLS_OBJECT_REQUIRED"]
    for name in REQUIRED_CONTROLS:
        row = controls.get(name)
        if not isinstance(row, dict):
            failures.append(f"CONTROL_REQUIRED:{name}")
            continue
        if not _sha256(row.get("runtime_receipt_sha256")):
            failures.append(f"CONTROL_RUNTIME_RECEIPT_REQUIRED:{name}")
        observations = row.get("observations")
        if observations is not None and (
            not isinstance(observations, int) or isinstance(observations, bool) or observations <= 0
        ):
            failures.append(f"CONTROL_OBSERVATIONS_POSITIVE_REQUIRED:{name}")
    return not failures, failures


def _split_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    calibration = candidate.get("calibration")
    holdout = candidate.get("holdout")
    if not isinstance(calibration, dict) or not isinstance(holdout, dict):
        return False, ["CALIBRATION_AND_HOLDOUT_REQUIRED"]
    cal_family = calibration.get("family_id")
    hold_family = holdout.get("family_id")
    if not _nonempty(cal_family) or not _nonempty(hold_family):
        failures.append("SPLIT_FAMILY_IDENTITIES_REQUIRED")
    elif cal_family == hold_family:
        failures.append("CALIBRATION_HOLDOUT_FAMILY_MUST_DIFFER")
    cal_seeds = calibration.get("seeds")
    hold_seeds = holdout.get("seeds")
    if not isinstance(cal_seeds, list) or not cal_seeds:
        failures.append("CALIBRATION_FIXED_SEEDS_REQUIRED")
        cal_seeds = []
    if not isinstance(hold_seeds, list) or not hold_seeds:
        failures.append("HOLDOUT_FIXED_SEEDS_REQUIRED")
        hold_seeds = []
    if set(map(str, cal_seeds)) & set(map(str, hold_seeds)):
        failures.append("CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT")
    if holdout.get("reproducible_directional_effect") is not True:
        failures.append("REPRODUCIBLE_DIRECTIONAL_HOLDOUT_EFFECT_REQUIRED")
    if holdout.get("strongest_counterexample_recorded") is not True:
        failures.append("STRONGEST_COUNTEREXAMPLE_REQUIRED")
    if not _sha256(holdout.get("analysis_receipt_sha256")):
        failures.append("HOLDOUT_ANALYSIS_RECEIPT_REQUIRED")
    return not failures, failures


def _identity_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    identity = candidate.get("source_identity")
    intervention = candidate.get("intervention")
    if not isinstance(identity, dict):
        failures.append("SOURCE_IDENTITY_REQUIRED")
        identity = {}
    if not isinstance(intervention, dict):
        failures.append("INTERVENTION_IDENTITY_REQUIRED")
        intervention = {}
    if not _git_sha(identity.get("repo_head")):
        failures.append("EXACT_REPO_HEAD_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        if not _sha256(identity.get(key)):
            failures.append(f"IDENTITY_SHA256_REQUIRED:{key}")
    if intervention.get("runtime_observed") is not True:
        failures.append("RUNTIME_OBSERVED_INTERVENTION_REQUIRED")
    if not _nonempty(intervention.get("invocation_id")):
        failures.append("INTERVENTION_INVOCATION_ID_REQUIRED")
    if not _nonempty(intervention.get("activation_site")):
        failures.append("ACTIVATION_SITE_REQUIRED")
    for key in (
        "source_packet_sha256",
        "adapter_sha256",
        "local_vector_sha256",
        "applied_vector_sha256",
        "runtime_intervention_receipt_sha256",
    ):
        if not _sha256(intervention.get(key)):
            failures.append(f"INTERVENTION_SHA256_REQUIRED:{key}")
    if intervention.get("gain") is None:
        failures.append("INTERVENTION_GAIN_REQUIRED")
    if intervention.get("layer_start") is None or intervention.get("layer_end") is None:
        failures.append("INTERVENTION_LAYER_RANGE_REQUIRED")
    return not failures, failures


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _local_runtime_result_evidence(
    candidate: dict[str, Any], result: dict[str, Any] | None
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not isinstance(result, dict):
        return False, ["LOCAL_RUNTIME_RESULT_REQUIRED"]
    if result.get("schema") != LOCAL_RESULT_SCHEMA:
        failures.append("LOCAL_RUNTIME_RESULT_SCHEMA_INVALID")
    if result.get("status") != "PASS":
        failures.append("LOCAL_RUNTIME_RESULT_PASS_REQUIRED")
    verdict = result.get("verdict")
    if not isinstance(verdict, dict) or verdict.get("pass") is not True:
        failures.append("LOCAL_RUNTIME_SCIENTIFIC_PASS_REQUIRED")
    if result.get("api_loopback_only") is not True:
        failures.append("LOCAL_RUNTIME_RESULT_LOOPBACK_REQUIRED")
    if result.get("zero_provider_billing") is not True:
        failures.append("LOCAL_RUNTIME_RESULT_ZERO_PROVIDER_BILLING_REQUIRED")
    if result.get("external_provider_credentials_read") is not False:
        failures.append("LOCAL_RUNTIME_RESULT_CREDENTIAL_BLIND_REQUIRED")

    target = candidate.get("target") if isinstance(candidate.get("target"), dict) else {}
    transport = candidate.get("transport") if isinstance(candidate.get("transport"), dict) else {}
    identity = candidate.get("source_identity") if isinstance(candidate.get("source_identity"), dict) else {}
    controls = candidate.get("controls") if isinstance(candidate.get("controls"), dict) else {}
    holdout = candidate.get("holdout") if isinstance(candidate.get("holdout"), dict) else {}

    endpoint = result.get("api_endpoint")
    if endpoint != transport.get("endpoint") or not _loopback_url(endpoint):
        failures.append("LOCAL_RUNTIME_ENDPOINT_BINDING_MISMATCH")
    source = result.get("source")
    if not isinstance(source, dict):
        failures.append("LOCAL_RUNTIME_SOURCE_OBJECT_REQUIRED")
        source = {}
    if source.get("repo_head") != identity.get("repo_head"):
        failures.append("LOCAL_RUNTIME_SOURCE_HEAD_MISMATCH")
    if not _git_sha(source.get("repo_tree")):
        failures.append("LOCAL_RUNTIME_SOURCE_TREE_REQUIRED")
    for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
        if result.get(key) != identity.get(key):
            failures.append(f"LOCAL_RUNTIME_IDENTITY_MISMATCH:{key}")
    expected_route = (
        f"{result.get('model')}@{result.get('model_revision')}"
        if _nonempty(result.get("model")) and _nonempty(result.get("model_revision"))
        else None
    )
    if expected_route != target.get("model_or_route"):
        failures.append("LOCAL_RUNTIME_MODEL_ROUTE_MISMATCH")

    calibration_rows = result.get("calibration_rows")
    holdout_rows = result.get("holdout_rows")
    if not isinstance(calibration_rows, list):
        failures.append("LOCAL_RUNTIME_CALIBRATION_ROWS_REQUIRED")
        calibration_rows = []
    if not isinstance(holdout_rows, list):
        failures.append("LOCAL_RUNTIME_HOLDOUT_ROWS_REQUIRED")
        holdout_rows = []
    api_invocations = len(calibration_rows) + len(holdout_rows)
    if api_invocations <= 0:
        failures.append("LOCAL_RUNTIME_API_INVOCATIONS_REQUIRED")

    holdout_receipts: list[str] = []
    for row in holdout_rows:
        if not isinstance(row, dict):
            failures.append("LOCAL_RUNTIME_HOLDOUT_ROW_OBJECT_REQUIRED")
            continue
        receipt = row.get("runtime_receipt_sha256")
        if not _sha256(receipt):
            failures.append("LOCAL_RUNTIME_HOLDOUT_RECEIPT_REQUIRED")
            continue
        holdout_receipts.append(receipt)

    for control in REQUIRED_CONTROLS:
        receipts = [
            row.get("runtime_receipt_sha256")
            for row in holdout_rows
            if isinstance(row, dict)
            and row.get("control") == control
            and _sha256(row.get("runtime_receipt_sha256"))
        ]
        control_row = controls.get(control)
        if not receipts:
            failures.append(f"LOCAL_RUNTIME_CONTROL_OBSERVATIONS_REQUIRED:{control}")
            continue
        if not isinstance(control_row, dict):
            failures.append(f"LOCAL_RUNTIME_CONTROL_BINDING_REQUIRED:{control}")
            continue
        if control_row.get("runtime_receipt_sha256") != _canonical_sha(receipts):
            failures.append(f"LOCAL_RUNTIME_CONTROL_RECEIPT_MISMATCH:{control}")
        if control_row.get("observations") != len(receipts):
            failures.append(f"LOCAL_RUNTIME_CONTROL_COUNT_MISMATCH:{control}")

    if isinstance(verdict, dict) and holdout_receipts:
        expected_analysis = _canonical_sha({"verdict": verdict, "holdout_receipts": holdout_receipts})
        if holdout.get("analysis_receipt_sha256") != expected_analysis:
            failures.append("LOCAL_RUNTIME_ANALYSIS_RECEIPT_MISMATCH")

    expected_receipt = _canonical_sha(
        {
            "endpoint": endpoint,
            "runtime_build_sha256": result.get("runtime_build_sha256"),
            "checkpoint_sha256": result.get("checkpoint_sha256"),
            "tokenizer_sha256": result.get("tokenizer_sha256"),
            "source": source,
            "api_invocations": api_invocations,
        }
    )
    if target.get("local_runtime_execution_receipt_sha256") != expected_receipt:
        failures.append("LOCAL_RUNTIME_EXECUTION_RECEIPT_MISMATCH")

    recorded_result_sha = result.get("result_sha256")
    if not _sha256(recorded_result_sha):
        failures.append("LOCAL_RUNTIME_RESULT_SHA256_REQUIRED")
    else:
        unsigned_result = dict(result)
        unsigned_result.pop("result_sha256", None)
        if recorded_result_sha != _canonical_sha(unsigned_result):
            failures.append("LOCAL_RUNTIME_RESULT_SHA256_MISMATCH")
    return not failures, failures


def _owner_target_evidence(
    candidate: dict[str, Any], local_runtime_result: dict[str, Any] | None = None
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    target = candidate.get("target")
    transport = candidate.get("transport")
    if not isinstance(target, dict):
        return False, ["OWNER_API_TARGET_EVIDENCE_REQUIRED"]
    if not isinstance(transport, dict):
        transport = {}
    relation = target.get("relation")
    if relation not in {OWNER_API_TARGET_CLASS, LEGACY_OWNER_API_TARGET_CLASS}:
        failures.append("ZERO_COST_API_SERVED_MODEL_RUNTIME_REQUIRED")
    if not _nonempty(target.get("provider")) or not _nonempty(target.get("model_or_route")):
        failures.append("EXACT_PROVIDER_AND_MODEL_ROUTE_REQUIRED")
    surface = target.get("execution_surface")
    if surface is None and relation == LEGACY_OWNER_API_TARGET_CLASS:
        surface = EXTERNAL_API_SURFACE
    if transport.get("api_served") is not True and relation != LEGACY_OWNER_API_TARGET_CLASS:
        failures.append("API_SERVED_RUNTIME_REQUIRED")
    if surface == LOCAL_API_SURFACE:
        if target.get("zero_provider_billing") is not True:
            failures.append("LOCAL_ZERO_PROVIDER_BILLING_REQUIRED")
        if target.get("provider") != "local":
            failures.append("LOCAL_API_PROVIDER_MUST_BE_LOCAL")
        if not _sha256(target.get("local_runtime_execution_receipt_sha256")):
            failures.append("LOCAL_RUNTIME_EXECUTION_RECEIPT_REQUIRED")
        if transport.get("loopback_only") is not True:
            failures.append("LOCAL_API_LOOPBACK_ONLY_REQUIRED")
        if not _loopback_url(transport.get("endpoint")):
            failures.append("LOCAL_API_LOOPBACK_ENDPOINT_REQUIRED")
        _, local_failures = _local_runtime_result_evidence(candidate, local_runtime_result)
        failures.extend(local_failures)
    elif surface == EXTERNAL_API_SURFACE:
        if target.get("typed_free_lane_admitted") is not True:
            failures.append("TYPED_FREE_LANE_ADMISSION_REQUIRED")
        if not _sha256(target.get("free_lane_execution_receipt_sha256")):
            failures.append("FREE_LANE_EXECUTION_RECEIPT_REQUIRED")
    else:
        failures.append("API_EXECUTION_SURFACE_REQUIRED")
    return not failures, failures


def adjudicate(
    candidate: dict[str, Any], *, local_runtime_result: dict[str, Any] | None = None
) -> dict[str, Any]:
    failures: list[str] = []
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        failures.append("CANDIDATE_SCHEMA_INVALID")
    runtime_class = candidate.get("runtime_intervention_class")
    if runtime_class not in INSTRUMENTED_RUNTIME_CLASSES:
        failures.append("INSTRUMENTED_RUNTIME_CLASS_REQUIRED")
    transport = candidate.get("transport")
    if not isinstance(transport, dict):
        failures.append("TRANSPORT_EVIDENCE_REQUIRED")
        transport = {}
    if transport.get("hosted_prompt_only") is not False:
        failures.append("HOSTED_PROMPT_ONLY_CANNOT_PROVE_VECTOR_STEERING")
    identity_ok, identity_failures = _identity_evidence(candidate)
    controls_ok, control_failures = _control_receipts(candidate.get("controls"))
    split_ok, split_failures = _split_evidence(candidate)
    site_ok, site_failures = _causal_site_evidence(candidate)
    failures.extend(identity_failures)
    failures.extend(control_failures)
    failures.extend(split_failures)
    failures.extend(site_failures)
    mechanism_pass = (
        candidate.get("schema") == CANDIDATE_SCHEMA
        and runtime_class in INSTRUMENTED_RUNTIME_CLASSES
        and transport.get("hosted_prompt_only") is False
        and identity_ok
        and controls_ok
        and split_ok
        and site_ok
    )
    owner_target_ok, target_failures = _owner_target_evidence(
        candidate, local_runtime_result=local_runtime_result
    )
    owner_target_pass = mechanism_pass and owner_target_ok
    return {
        "schema": VERDICT_SCHEMA,
        "mechanism_runtime_vector_credit_candidate": bool(mechanism_pass),
        "owner_trigger1_goal_credit_candidate": bool(owner_target_pass),
        "owner_trigger1_direct_free_api_model_credit_candidate": bool(owner_target_pass),
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "failures": sorted(set(failures)),
        "owner_target_failures": sorted(set(target_failures)),
        "evidence_boundary": (
            "PASS means promotion-candidate evidence only. External FREE targets require typed FREE execution evidence. "
            "Local loopback targets additionally require the sibling exact runtime result to hash-bind source tree, "
            "runtime/model/tokenizer, actual API observations, six-control receipts and result digest. The intervention "
            "must be non-terminal with downstream model computation; terminal output shortcuts remain technical positive controls only."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    candidate = _load_json_object(path)
    if candidate is None:
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": ["CANDIDATE_FILE_INVALID"],
            "owner_target_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    local_runtime_result = None
    target = candidate.get("target")
    if isinstance(target, dict) and target.get("execution_surface") == LOCAL_API_SURFACE:
        local_runtime_result = _load_json_object(path.with_name(LOCAL_RESULT_FILENAME))
    verdict = adjudicate(candidate, local_runtime_result=local_runtime_result)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if local_runtime_result is not None:
        result_path = path.with_name(LOCAL_RESULT_FILENAME)
        verdict["local_runtime_result_path"] = str(result_path)
        verdict["local_runtime_result_file_sha256"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    goal = any(item.get("owner_trigger1_goal_credit_candidate") is True for item in verdicts)
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v2",
        "candidate_files_seen": len(paths),
        "mechanism_runtime_vector_credit_candidate": any(
            item.get("mechanism_runtime_vector_credit_candidate") is True for item in verdicts
        ),
        "owner_trigger1_goal_credit_candidate": goal,
        "owner_trigger1_direct_free_api_model_credit_candidate": goal,
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = parser.parse_args()
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
