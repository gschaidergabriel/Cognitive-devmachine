#!/usr/bin/env python3
"""Scientific successor gate for Trigger-1 local hidden-state promotion.

V2 correctly checks runtime identity, controls, holdout separation and the zero-cost
API boundary, but those checks alone cannot detect a circular construction where the
intervention vector is derived from the same LM-head contrast used as the outcome.
At the final normalized hidden state such a vector makes the directional logit effect
algebraically expected even if no model-internal causal feature was identified.

This V3 gate preserves V2 mechanism/runtime evidence but withholds the stricter owner
Trigger-1 goal credit for LOCAL_PYTORCH_ACTIVATION_INTERVENTION unless the candidate
also proves a disjoint hidden-activation basis and at least one downstream transformer
block after the intervention.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate as base

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v3"
REQUIRED_LOCAL_BASIS_CLASS = "DISJOINT_HIDDEN_ACTIVATION_CONTRAST"


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _scientific_identification_failures(candidate: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if candidate.get("runtime_intervention_class") != "LOCAL_PYTORCH_ACTIVATION_INTERVENTION":
        return failures

    intervention = candidate.get("intervention")
    calibration = candidate.get("calibration")
    holdout = candidate.get("holdout")
    identity = candidate.get("source_identity")
    if not isinstance(intervention, dict):
        return ["LOCAL_INTERVENTION_OBJECT_REQUIRED"]
    if not isinstance(calibration, dict):
        calibration = {}
    if not isinstance(holdout, dict):
        holdout = {}
    if not isinstance(identity, dict):
        identity = {}

    if intervention.get("basis_derivation_class") != REQUIRED_LOCAL_BASIS_CLASS:
        failures.append("DISJOINT_HIDDEN_ACTIVATION_BASIS_REQUIRED")
    if intervention.get("readout_target_weights_used") is not False:
        failures.append("LM_HEAD_TARGET_WEIGHT_DERIVATION_FORBIDDEN_FOR_GOAL_CREDIT")
    if intervention.get("direct_readout_algebraically_forced") is not False:
        failures.append("DIRECT_READOUT_ALGEBRAIC_EFFECT_MUST_BE_FALSE")

    depth = intervention.get("post_intervention_transform_depth")
    if not isinstance(depth, int) or depth < 1:
        failures.append("POST_INTERVENTION_TRANSFORM_DEPTH_REQUIRED")

    basis_family = intervention.get("basis_source_family_id")
    if not _nonempty(basis_family):
        failures.append("BASIS_SOURCE_FAMILY_ID_REQUIRED")
    elif basis_family in {calibration.get("family_id"), holdout.get("family_id")}:
        failures.append("BASIS_SOURCE_FAMILY_MUST_BE_DISJOINT")

    basis_seeds = intervention.get("basis_source_seeds")
    if not isinstance(basis_seeds, list) or not basis_seeds:
        failures.append("BASIS_SOURCE_SEEDS_REQUIRED")
        basis_seeds = []
    cal_seeds = calibration.get("seeds") if isinstance(calibration.get("seeds"), list) else []
    hold_seeds = holdout.get("seeds") if isinstance(holdout.get("seeds"), list) else []
    if set(map(str, basis_seeds)) & (set(map(str, cal_seeds)) | set(map(str, hold_seeds))):
        failures.append("BASIS_CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT")

    if identity.get("repo_dirty") is not False:
        failures.append("CLEAN_TRACKED_SOURCE_REQUIRED_FOR_OWNER_GOAL_CREDIT")
    if not _nonempty(identity.get("repo_tree")):
        failures.append("EXACT_REPO_TREE_REQUIRED")
    dirty_sha = identity.get("repo_dirty_state_sha256")
    if not isinstance(dirty_sha, str) or len(dirty_sha) != 64:
        failures.append("DIRTY_STATE_SHA256_REQUIRED")

    return failures


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    verdict = dict(base.adjudicate(candidate))
    scientific_failures = _scientific_identification_failures(candidate)
    scientific_ok = not scientific_failures

    base_goal = bool(verdict.get("owner_trigger1_goal_credit_candidate"))
    if candidate.get("runtime_intervention_class") == "LOCAL_PYTORCH_ACTIVATION_INTERVENTION":
        goal = base_goal and scientific_ok
        verdict["owner_trigger1_goal_credit_candidate"] = goal
        verdict["owner_trigger1_direct_free_api_model_credit_candidate"] = goal
    else:
        goal = base_goal

    verdict["schema"] = VERDICT_SCHEMA
    verdict["scientific_identification_ok"] = scientific_ok
    verdict["scientific_identification_failures"] = sorted(set(scientific_failures))
    verdict["readout_circularity_guard_applied"] = (
        candidate.get("runtime_intervention_class") == "LOCAL_PYTORCH_ACTIVATION_INTERVENTION"
    )
    verdict["evidence_boundary"] = (
        "Mechanism/runtime credit remains governed by V2. For local PyTorch hidden-state owner-goal "
        "promotion, V3 additionally requires a basis derived from disjoint hidden activations, no "
        "LM-head target-weight derivation, at least one downstream transformer block after the "
        "intervention, disjoint basis/calibration/holdout families and clean exact tracked source. "
        "A final-readout vector constructed from the measured LM-head contrast is plumbing evidence only."
    )
    return verdict


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = dict(base.adjudicate_file(path))
        result["schema"] = VERDICT_SCHEMA
        result["scientific_identification_ok"] = False
        result["scientific_identification_failures"] = [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"]
        result["readout_circularity_guard_applied"] = False
        return result
    if not isinstance(candidate, dict):
        result = dict(base.adjudicate_file(path))
        result["schema"] = VERDICT_SCHEMA
        result["scientific_identification_ok"] = False
        result["scientific_identification_failures"] = ["CANDIDATE_OBJECT_REQUIRED"]
        result["readout_circularity_guard_applied"] = False
        return result
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
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
