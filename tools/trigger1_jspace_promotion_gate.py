#!/usr/bin/env python3
"""Fail-closed evidence gate for Trigger-1 direct J-Space/vector-steering claims.

Trigger-1 V2 is goal-bound rather than provider-bound. The full target may be met by
an exact admitted FREE external API runtime or by an exact zero-provider-billing
loopback API runtime, provided the same internal-vector, identity, matched-control
and disjoint-holdout evidence is present.

Hosted prompt/completion traffic alone can never satisfy a positive verdict. A local
PyTorch activation intervention may establish mechanism-level vector-consumption
evidence without establishing the Trigger-1 scientific goal: goal promotion also
requires explicit evidence that vector construction and evaluation are not the same
readout-aligned algebraic objective.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

CANDIDATE_SCHEMA = "CLAY_TRIGGER1_JSPACE_DIRECT_STEERING_CANDIDATE/v1"
VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v3"
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
LOCAL_PYTORCH_RUNTIME_CLASS = "LOCAL_PYTORCH_ACTIVATION_INTERVENTION"


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
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

    head = identity.get("repo_head")
    if not isinstance(head, str) or len(head) != 40:
        failures.append("EXACT_REPO_HEAD_REQUIRED")
    else:
        try:
            int(head, 16)
        except ValueError:
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


def _scientific_independence_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    """Keep mechanism evidence while rejecting algebraically self-confirming goal claims.

    The current local PyTorch fastpath constructs v from the same lm_head contrast that
    defines its score and injects v at final-norm output immediately before lm_head.
    In that geometry, the expected +v/-v/null/orthogonal score ordering follows from
    the readout algebra itself. Such a run can prove that the hook consumed a vector,
    but it cannot by itself prove a nontrivial J-Space causal direction.

    Other runtime classes keep their existing gate behavior. Local PyTorch candidates
    must positively bind an independent scientific discriminator before goal credit.
    """
    if candidate.get("runtime_intervention_class") != LOCAL_PYTORCH_RUNTIME_CLASS:
        return True, []

    evidence = candidate.get("scientific_independence")
    if not isinstance(evidence, dict):
        return False, ["CAUSAL_INDEPENDENCE_EVIDENCE_REQUIRED_FOR_LOCAL_PYTORCH"]

    failures: list[str] = []
    if evidence.get("vector_construction_evaluation_independent") is not True:
        failures.append("VECTOR_CONSTRUCTION_MUST_BE_INDEPENDENT_OF_EVALUATION_READOUT")
    if evidence.get("holdout_target_independent_of_vector_construction") is not True:
        failures.append("INDEPENDENT_HOLDOUT_TARGET_REQUIRED")
    if evidence.get("readout_algebraically_forces_directional_metric") is not False:
        failures.append("READOUT_ALIGNED_TAUTOLOGY_NOT_EXCLUDED")
    if not _sha256(evidence.get("evidence_receipt_sha256")):
        failures.append("CAUSAL_INDEPENDENCE_RECEIPT_REQUIRED")
    return not failures, failures


def _owner_target_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
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
    elif surface == EXTERNAL_API_SURFACE:
        if target.get("typed_free_lane_admitted") is not True:
            failures.append("TYPED_FREE_LANE_ADMISSION_REQUIRED")
        if not _sha256(target.get("free_lane_execution_receipt_sha256")):
            failures.append("FREE_LANE_EXECUTION_RECEIPT_REQUIRED")
    else:
        failures.append("API_EXECUTION_SURFACE_REQUIRED")

    return not failures, failures


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
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
    failures.extend(identity_failures)
    failures.extend(control_failures)
    failures.extend(split_failures)

    mechanism_pass = (
        candidate.get("schema") == CANDIDATE_SCHEMA
        and runtime_class in INSTRUMENTED_RUNTIME_CLASSES
        and transport.get("hosted_prompt_only") is False
        and identity_ok
        and controls_ok
        and split_ok
    )

    owner_target_ok, target_failures = _owner_target_evidence(candidate)
    scientific_ok, scientific_failures = _scientific_independence_evidence(candidate)
    owner_target_failures = [*target_failures, *scientific_failures]
    owner_target_pass = mechanism_pass and owner_target_ok and scientific_ok

    return {
        "schema": VERDICT_SCHEMA,
        "mechanism_runtime_vector_credit_candidate": bool(mechanism_pass),
        "scientific_independence_pass": bool(scientific_ok),
        "owner_trigger1_goal_credit_candidate": bool(owner_target_pass),
        "owner_trigger1_direct_free_api_model_credit_candidate": bool(owner_target_pass),
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "failures": sorted(set(failures)),
        "scientific_independence_failures": sorted(set(scientific_failures)),
        "owner_target_failures": sorted(set(owner_target_failures)),
        "evidence_boundary": (
            "Mechanism PASS can establish that an instrumented runtime consumed the vector. Trigger-1 goal "
            "PASS additionally requires a non-self-confirming scientific discriminator. For local PyTorch "
            "interventions, a vector derived from the same readout contrast used as the evaluation metric "
            "cannot receive goal credit merely because +vector/sign-flip/null/orthogonal controls behave as "
            "that linear geometry predicts. Canonical, whole-product, J-Space-model and training credit remain false."
        ),
    }


def _invalid_verdict(failure: str) -> dict[str, Any]:
    return {
        "schema": VERDICT_SCHEMA,
        "mechanism_runtime_vector_credit_candidate": False,
        "scientific_independence_pass": False,
        "owner_trigger1_goal_credit_candidate": False,
        "owner_trigger1_direct_free_api_model_credit_candidate": False,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "failures": [failure],
        "scientific_independence_failures": [],
        "owner_target_failures": [],
        "evidence_boundary": "Invalid candidate files fail closed.",
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _invalid_verdict(f"CANDIDATE_FILE_INVALID:{type(exc).__name__}")
    if not isinstance(candidate, dict):
        return _invalid_verdict("CANDIDATE_OBJECT_REQUIRED")
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    goal = any(item.get("owner_trigger1_goal_credit_candidate") is True for item in verdicts)
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v3",
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

    if args.candidate:
        result = adjudicate_file(Path(args.candidate))
    else:
        result = scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
