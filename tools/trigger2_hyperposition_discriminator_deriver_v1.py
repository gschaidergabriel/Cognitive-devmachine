#!/usr/bin/env python3
"""Deterministic upstream derivation for Trigger-2 Hyperposition discriminator labels.

Purpose
-------
Close the causal-label gap where branch_relations, decisive roles, pair separation, and
all-other-branches-falsified could otherwise begin as caller/generator assertions.

This source operates only on explicit synthetic task-world outcomes. Given an exact
categorical discriminator specification and its observed synthetic outcome, it derives:
- relation per branch;
- branch-local evidence role;
- separated branch pairs;
- surviving/matching branch set;
- whether all nonmatching branches are mechanically falsified;
- a source-data-bound derivation receipt.

It deliberately does NOT mint canonical world truth, effect authority, model/J-Space/HCU
runtime evidence, accepted dataset tokens, or training credit.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_DISCRIMINATOR_DERIVER/v1"
SPEC_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_SPEC/v1"
OBS_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_OBSERVATION/v1"
RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_DERIVATION_RECEIPT/v1"
UNKNOWN_PREDICTION = "__UNKNOWN__"


class DerivationError(ValueError):
    pass


def _canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha(obj: Any) -> str:
    return hashlib.sha256(_canon(obj)).hexdigest()


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def _validate_spec(spec: Any) -> tuple[list[str], list[str], dict[str, str]]:
    if not isinstance(spec, dict) or spec.get("schema") != SPEC_SCHEMA:
        raise DerivationError("SPEC_SCHEMA_MISMATCH")
    if spec.get("canonical_truth_allowed") is not False:
        raise DerivationError("SPEC_CANONICAL_TRUTH_MUST_BE_FALSE")
    if spec.get("direct_effect_authority") is not False:
        raise DerivationError("SPEC_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if spec.get("semantics") != "EXACT_CATEGORICAL_MUTUALLY_EXCLUSIVE_EXHAUSTIVE":
        raise DerivationError("ONLY_EXACT_CATEGORICAL_DISCRIMINATORS_SUPPORTED")
    if not _nonempty(spec.get("test_id")):
        raise DerivationError("TEST_ID_REQUIRED")

    branch_ids = spec.get("live_branch_ids")
    if not isinstance(branch_ids, list) or len(branch_ids) < 2 or not all(_nonempty(x) for x in branch_ids):
        raise DerivationError("LIVE_BRANCH_IDS_INVALID")
    if len(set(branch_ids)) != len(branch_ids):
        raise DerivationError("DUPLICATE_LIVE_BRANCH_ID")

    domain = spec.get("outcome_domain")
    if not isinstance(domain, list) or len(domain) < 2 or not all(_nonempty(x) for x in domain):
        raise DerivationError("OUTCOME_DOMAIN_INVALID")
    if UNKNOWN_PREDICTION in domain:
        raise DerivationError("UNKNOWN_SENTINEL_FORBIDDEN_IN_OUTCOME_DOMAIN")
    if len(set(domain)) != len(domain):
        raise DerivationError("DUPLICATE_OUTCOME_DOMAIN_VALUE")

    predictions = spec.get("predicted_outcome_by_branch")
    if not isinstance(predictions, dict) or set(predictions) != set(branch_ids):
        raise DerivationError("PREDICTION_MAP_MUST_COVER_EXACT_LIVE_BRANCH_SET")
    for bid, outcome in predictions.items():
        if outcome != UNKNOWN_PREDICTION and outcome not in domain:
            raise DerivationError(f"PREDICTION_OUTSIDE_DOMAIN:{bid}")

    forbidden = {
        "branch_relations",
        "decision_role",
        "decision_role_by_branch",
        "separates_branch_pairs",
        "all_other_branches_explicitly_falsified",
        "resolved_branch",
    }
    if forbidden & set(spec):
        raise DerivationError("DERIVED_FIELDS_MUST_NOT_BE_CALLER_SUPPLIED")
    return list(branch_ids), list(domain), dict(predictions)


def _validate_observation(obs: Any, spec: dict[str, Any], domain: list[str]) -> str:
    if not isinstance(obs, dict) or obs.get("schema") != OBS_SCHEMA:
        raise DerivationError("OBS_SCHEMA_MISMATCH")
    if obs.get("canonical_truth_allowed") is not False:
        raise DerivationError("OBS_CANONICAL_TRUTH_MUST_BE_FALSE")
    if obs.get("direct_effect_authority") is not False:
        raise DerivationError("OBS_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if obs.get("test_id") != spec.get("test_id"):
        raise DerivationError("OBS_TEST_ID_MISMATCH")
    outcome = obs.get("observed_outcome")
    if outcome not in domain:
        raise DerivationError("OBSERVED_OUTCOME_OUTSIDE_DOMAIN")
    forbidden = {
        "branch_relations",
        "decision_role",
        "decision_role_by_branch",
        "separates_branch_pairs",
        "all_other_branches_explicitly_falsified",
        "resolved_branch",
    }
    if forbidden & set(obs):
        raise DerivationError("DERIVED_FIELDS_MUST_NOT_BE_OBSERVATION_SUPPLIED")
    return str(outcome)


def derive(spec: Any, observation: Any) -> dict[str, Any]:
    branch_ids, domain, predictions = _validate_spec(spec)
    observed = _validate_observation(observation, spec, domain)

    matching = sorted(bid for bid in branch_ids if predictions[bid] == observed)
    unknown = sorted(bid for bid in branch_ids if predictions[bid] == UNKNOWN_PREDICTION)
    mismatching = sorted(
        bid for bid in branch_ids
        if predictions[bid] not in {observed, UNKNOWN_PREDICTION}
    )

    relations: dict[str, str] = {}
    roles: dict[str, str] = {}
    unique_match = len(matching) == 1
    for bid in branch_ids:
        pred = predictions[bid]
        if pred == UNKNOWN_PREDICTION:
            relations[bid] = "NO_EFFECT"
            roles[bid] = "NONDECISIVE"
        elif pred == observed:
            relations[bid] = "SUPPORT"
            roles[bid] = "DECISIVE_SUPPORT" if unique_match and not unknown else "NONDECISIVE"
        else:
            relations[bid] = "FALSIFY"
            roles[bid] = "DECISIVE_CONTRADICTION"

    separated_pairs = sorted(
        [list(_pair(a, b)) for a, b in itertools.combinations(branch_ids, 2)
         if predictions[a] != UNKNOWN_PREDICTION
         and predictions[b] != UNKNOWN_PREDICTION
         and predictions[a] != predictions[b]]
    )

    all_other_falsified = bool(unique_match and not unknown and len(mismatching) == len(branch_ids) - 1)
    resolution = {
        "status": "RESOLVED_WITHIN_SYNTHETIC_WORLD" if all_other_falsified else "UNRESOLVED",
        "resolved_branch": matching[0] if all_other_falsified else None,
        "basis": "UNIQUE_EXACT_OUTCOME_MATCH" if all_other_falsified else "MULTIPLE_OR_UNKNOWN_MATCHING_ALTERNATIVES",
    }

    semantic_material = {
        "spec": spec,
        "observation": observation,
        "derived": {
            "branch_relations": relations,
            "decision_role_by_branch": roles,
            "separates_branch_pairs": separated_pairs,
            "matching_branch_ids": matching,
            "unknown_prediction_branch_ids": unknown,
            "mismatching_branch_ids": mismatching,
            "all_other_branches_explicitly_falsified": all_other_falsified,
            "resolution": resolution,
        },
    }
    receipt_id = _sha(semantic_material)

    return {
        "schema": SCHEMA,
        "pass": True,
        "branch_relations": relations,
        "decision_role_by_branch": roles,
        "separates_branch_pairs": separated_pairs,
        "matching_branch_ids": matching,
        "unknown_prediction_branch_ids": unknown,
        "mismatching_branch_ids": mismatching,
        "all_other_branches_explicitly_falsified": all_other_falsified,
        "resolution": resolution,
        "legacy_shared_evidence_decision_role": "NONDECISIVE",
        "legacy_note": "Current v1 shared-evidence object cannot faithfully encode per-branch decisive roles. Keep shared role NONDECISIVE and use mechanically derived FALSIFY validity plus derived all-other-falsified for compatibility until a branch-local evidence-role successor is wired.",
        "derivation_receipt": {
            "schema": RECEIPT_SCHEMA,
            "receipt_id": receipt_id,
            "spec_sha256": _sha(spec),
            "observation_sha256": _sha(observation),
            "derived_sha256": _sha(semantic_material["derived"]),
            "test_id": spec["test_id"],
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "runtime_credit_minted": False,
            "jspace_model_runtime_credit_minted": False,
            "training_credit_minted": False,
        },
    }


def to_legacy_v1_inputs(spec: Any, observation: Any, evidence_identity: dict[str, Any]) -> dict[str, Any]:
    """Produce fail-closed v1-compatible labeler inputs from the derivation receipt.

    The compatibility evidence decision_role remains NONDECISIVE because the v1 evidence
    object has one shared role while the derivation has branch-local decisive roles.
    Falsification itself remains encoded by mechanically derived branch_relations.
    """
    result = derive(spec, observation)
    required = {"evidence_id", "provenance_ancestry_id", "independence_group"}
    if not isinstance(evidence_identity, dict) or not required.issubset(evidence_identity):
        raise DerivationError("EVIDENCE_IDENTITY_INCOMPLETE")
    evidence = {
        "evidence_id": str(evidence_identity["evidence_id"]),
        "provenance_ancestry_id": str(evidence_identity["provenance_ancestry_id"]),
        "independence_group": str(evidence_identity["independence_group"]),
        "decision_role": "NONDECISIVE",
        "derivation_receipt_id": result["derivation_receipt"]["receipt_id"],
    }
    return {
        "observation": {
            "schema": "XENO_HYPERPOSITION_OBSERVATION/v1",
            "evidence": evidence,
            "branch_relations": result["branch_relations"],
        },
        "resolve_context": {
            "context_id": str(spec["test_id"]),
            "discriminator_executed": True,
            "discriminator_admissible": True,
            "resolution_scope": "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE",
            "all_other_branches_explicitly_falsified": result["all_other_branches_explicitly_falsified"],
            "derivation_receipt_id": result["derivation_receipt"]["receipt_id"],
        },
        "branch_local_decision_roles_evaluator_only": result["decision_role_by_branch"],
        "derived_separates_branch_pairs_evaluator_only": result["separates_branch_pairs"],
        "derivation_receipt": result["derivation_receipt"],
        "canonical_truth_minted": False,
        "training_credit_minted": False,
    }
