#!/usr/bin/env python3
"""Derivation-bound reference labelers for Trigger-2 semantic Hyperposition.

SOURCE / SYNTHETIC CURRICULUM REFERENCE ONLY.

V2 closes the critical v1 circularity blockers by deriving branch update relations and
resolution from an admissible discriminator's per-branch predictions plus one observed
result. Callers cannot supply an update ``effect``, a winner, or a separation set.
Evidence replay/dependence identity is checked across the whole state. The labeler never
mints canonical truth, direct-effect authority, J-Space/HCU/EntityOS runtime credit, or
training credit.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_REFERENCE_LABELERS/v2"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v2"
OBS_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_OBSERVATION/v2"
DISC_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_DISCRIMINATOR/v2"

BRANCH_FIELDS = ("id", "v", "K", "E_plus", "E_minus", "F", "T", "A", "sigma")
EVIDENCE_FIELDS = (
    "evidence_id",
    "causal_event_id",
    "provenance_or_ancestry_id",
    "independence_group",
    "provenance",
    "epistemic_type",
)
ALLOWED_EPISTEMIC = {
    "OBSERVED",
    "UNKNOWN",
    "HYPOTHESIS",
    "COUNTERHYPOTHESIS",
    "PREDICTION",
    "MEASUREMENT_ERROR",
    "CONTRADICTION",
    "SYNTHETIC_PROOF",
}
ALLOWED_CONTEXT = {"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"}
ALLOWED_SIGMA = {
    "LIVE_UNRESOLVED",
    "SUPPORTED_UNRESOLVED",
    "WEAKENED_UNRESOLVED",
    "FALSIFIED",
    "RESOLVED_PASS",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _fail(code: str, **extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": False,
        "failure": code,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


def _ok(**extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": True,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


def _validate_evidence(e: Any) -> str | None:
    if not isinstance(e, dict):
        return "EVIDENCE_OBJECT_REQUIRED"
    for field in EVIDENCE_FIELDS:
        if not _nonempty(e.get(field)):
            return f"EVIDENCE_FIELD_REQUIRED:{field}"
    if e.get("epistemic_type") not in ALLOWED_EPISTEMIC:
        return "EVIDENCE_EPISTEMIC_TYPE_INVALID"
    return None


def _validate_branch(branch: Any) -> str | None:
    if not isinstance(branch, dict):
        return "BRANCH_OBJECT_REQUIRED"
    for field in BRANCH_FIELDS:
        if field not in branch:
            return f"BRANCH_FIELD_REQUIRED:{field}"
    if not _nonempty(branch.get("id")):
        return "BRANCH_ID_REQUIRED"
    if branch.get("K") not in ALLOWED_CONTEXT:
        return "BRANCH_CONTEXT_INVALID"
    if branch.get("sigma") not in ALLOWED_SIGMA:
        return "BRANCH_SIGMA_INVALID"
    for field in ("E_plus", "E_minus", "F"):
        items = branch.get(field)
        if not isinstance(items, list):
            return f"BRANCH_{field}_LIST_REQUIRED"
        for item in items:
            err = _validate_evidence(item)
            if err:
                return f"BRANCH_{field}:{err}"
    return None


def _validate_state(state: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
        return None, "STATE_SCHEMA_MISMATCH"
    if state.get("canonical_truth_allowed") is not False:
        return None, "STATE_CANONICAL_TRUTH_MUST_BE_FALSE"
    if state.get("direct_effect_authority") is not False:
        return None, "STATE_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE"
    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        return None, "STATE_REQUIRES_AT_LEAST_TWO_BRANCHES"
    ids: list[str] = []
    for branch in branches:
        err = _validate_branch(branch)
        if err:
            return None, err
        ids.append(branch["id"])
    if len(ids) != len(set(ids)):
        return None, "DUPLICATE_BRANCH_ID"
    joint = state.get("joint_state")
    if not isinstance(joint, dict):
        return None, "JOINT_STATE_REQUIRED"
    if joint.get("cartesian_completion_allowed") is not False:
        return None, "IMPLICIT_CARTESIAN_COMPLETION_FORBIDDEN"
    if joint.get("representation") not in {"WHOLE_WORLD_BRANCHES", "EXPLICIT_COMPATIBILITY_SETS"}:
        return None, "JOINT_STATE_REPRESENTATION_INVALID"
    return state, None


def _validate_discriminator(d: Any, branch_ids: set[str]) -> str | None:
    if not isinstance(d, dict) or d.get("schema") != DISC_SCHEMA:
        return "DISCRIMINATOR_SCHEMA_MISMATCH"
    if d.get("canonical_truth_allowed") is not False:
        return "DISCRIMINATOR_CANONICAL_TRUTH_MUST_BE_FALSE"
    if d.get("direct_effect_authority") is not False:
        return "DISCRIMINATOR_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE"
    if d.get("admissible") is not True:
        return "DISCRIMINATOR_NOT_ADMISSIBLE"
    if not _nonempty(d.get("discriminator_id")):
        return "DISCRIMINATOR_ID_REQUIRED"
    if not _nonempty(d.get("prediction_derivation_id")):
        return "DISCRIMINATOR_PREDICTION_DERIVATION_ID_REQUIRED"
    if d.get("predictions_derived_from_synthetic_task_world") is not True:
        return "DISCRIMINATOR_PREDICTIONS_NOT_DERIVATION_BOUND"
    predictions = d.get("branch_predictions")
    if not isinstance(predictions, dict):
        return "DISCRIMINATOR_BRANCH_PREDICTIONS_REQUIRED"
    if set(predictions) != branch_ids:
        return "DISCRIMINATOR_MUST_PREDICT_ALL_BRANCHES"
    if any(not _nonempty(value) for value in predictions.values()):
        return "DISCRIMINATOR_PREDICTION_INVALID"
    for forbidden in ("winner_branch_id", "separates_live_branch_ids", "effect", "target_branch_ids"):
        if forbidden in d:
            return f"SELF_ASSERTED_LABEL_FIELD_FORBIDDEN:{forbidden}"
    return None


def _iter_state_evidence(state: dict[str, Any]):
    for branch in state["branches"]:
        for side in ("E_plus", "E_minus", "F"):
            for e in branch.get(side, []):
                yield branch["id"], side, e


def _evidence_identity_guard(state: dict[str, Any], incoming: dict[str, Any]) -> tuple[bool, str | None, list[dict[str, Any]]]:
    """Return (independent, failure, prior_matches).

    Same evidence_id or causal_event_id must keep immutable identity metadata. Same
    ancestry or independence_group makes the evidence correlated/non-independent even
    when it is not a replay.
    """
    matches: list[dict[str, Any]] = []
    independent = True
    immutable = (
        "causal_event_id",
        "provenance_or_ancestry_id",
        "independence_group",
        "provenance",
        "epistemic_type",
    )
    for branch_id, side, prior in _iter_state_evidence(state):
        same_eid = prior.get("evidence_id") == incoming.get("evidence_id")
        same_event = prior.get("causal_event_id") == incoming.get("causal_event_id")
        if same_eid or same_event:
            for field in immutable:
                if prior.get(field) != incoming.get(field):
                    return False, f"EVIDENCE_IDENTITY_REPLAY_CONFLICT:{field}", matches
            matches.append({"branch_id": branch_id, "side": side, "kind": "REPLAY"})
            independent = False
        if prior.get("provenance_or_ancestry_id") == incoming.get("provenance_or_ancestry_id"):
            independent = False
            matches.append({"branch_id": branch_id, "side": side, "kind": "SAME_ANCESTRY"})
        if prior.get("independence_group") == incoming.get("independence_group"):
            independent = False
            matches.append({"branch_id": branch_id, "side": side, "kind": "SAME_INDEPENDENCE_GROUP"})
    return independent, None, matches


def _relation_for_branch(branch: dict[str, Any], observed_result: str, predicted_result: str, exhaustive: bool) -> str:
    if branch["K"] == "DOES_NOT_APPLY":
        return "IRRELEVANT"
    if branch["K"] == "UNKNOWN":
        return "UNKNOWN_RELATION"
    if predicted_result == observed_result:
        return "SUPPORTS"
    return "FALSIFIES" if exhaustive else "COUNTERS"


def U_update(state: Any, observation: Any) -> dict[str, Any]:
    """Derive a branch-local update from prediction x observed-result, never caller effect."""
    validated, err = _validate_state(state)
    if err:
        return _fail(err)
    assert validated is not None
    if not isinstance(observation, dict) or observation.get("schema") != OBS_SCHEMA:
        return _fail("OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("canonical_truth_allowed") is not False:
        return _fail("OBSERVATION_CANONICAL_TRUTH_MUST_BE_FALSE")
    if observation.get("direct_effect_authority") is not False:
        return _fail("OBSERVATION_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    for forbidden in ("effect", "winner_branch_id", "separates_live_branch_ids", "target_branch_ids"):
        if forbidden in observation:
            return _fail(f"SELF_ASSERTED_LABEL_FIELD_FORBIDDEN:{forbidden}")
    observed_result = observation.get("observed_result")
    if not _nonempty(observed_result):
        return _fail("OBSERVED_RESULT_REQUIRED")
    evidence = observation.get("evidence")
    evidence_err = _validate_evidence(evidence)
    if evidence_err:
        return _fail(evidence_err)
    discriminator = observation.get("discriminator")
    branch_ids = {b["id"] for b in state["branches"]}
    disc_err = _validate_discriminator(discriminator, branch_ids)
    if disc_err:
        return _fail(disc_err)

    independent, identity_err, dependence_matches = _evidence_identity_guard(state, evidence)
    if identity_err:
        return _fail(identity_err)

    out = deepcopy(state)
    by_id = {b["id"]: b for b in out["branches"]}
    predictions = discriminator["branch_predictions"]
    exhaustive = discriminator.get("exhaustive_deterministic_partition") is True
    relations: list[dict[str, Any]] = []
    replay = any(m["kind"] == "REPLAY" for m in dependence_matches)

    for bid in sorted(by_id):
        branch = by_id[bid]
        relation = _relation_for_branch(branch, observed_result, predictions[bid], exhaustive)
        relations.append({"branch_id": bid, "derived_relation": relation})
        if replay or relation in {"IRRELEVANT", "UNKNOWN_RELATION"}:
            continue
        ev = deepcopy(evidence)
        ev["derived_relation"] = relation
        ev["discriminator_id"] = discriminator["discriminator_id"]
        ev["observed_result"] = observed_result
        ev["predicted_result"] = predictions[bid]
        ev["independent_for_update"] = independent
        if relation == "SUPPORTS":
            branch["E_plus"].append(ev)
            if independent and branch["sigma"] != "FALSIFIED":
                branch["sigma"] = "SUPPORTED_UNRESOLVED"
        elif relation == "COUNTERS":
            branch["E_minus"].append(ev)
            if independent and branch["sigma"] != "FALSIFIED":
                branch["sigma"] = "WEAKENED_UNRESOLVED"
        elif relation == "FALSIFIES":
            branch["F"].append(ev)
            if independent:
                branch["sigma"] = "FALSIFIED"

    return _ok(
        labeler="U_update",
        state_after=out,
        derived_relations=relations,
        evidence_independent_for_update=independent,
        replay_detected=replay,
        dependence_matches=dependence_matches,
        automatic_resolution_performed=False,
        derivation_rule="BRANCH_PREDICTION_X_OBSERVED_RESULT",
    )


def D_resolve(state: Any, observation: Any | None = None) -> dict[str, Any]:
    """Resolve only when an admissible exhaustive discriminator uniquely matches one live branch."""
    validated, err = _validate_state(state)
    if err:
        return _fail(err)
    assert validated is not None
    retained = [b["id"] for b in state["branches"]]
    live = [b for b in state["branches"] if b["sigma"] != "FALSIFIED" and b["K"] != "DOES_NOT_APPLY"]
    if observation is None:
        return _ok(
            labeler="D_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "NO_DERIVATION_BOUND_DISCRIMINATOR_OBSERVATION"},
            retained_branch_ids=retained,
        )
    if not isinstance(observation, dict) or observation.get("schema") != OBS_SCHEMA:
        return _fail("OBSERVATION_SCHEMA_MISMATCH")
    for forbidden in ("effect", "winner_branch_id", "separates_live_branch_ids", "target_branch_ids"):
        if forbidden in observation:
            return _fail(f"SELF_ASSERTED_LABEL_FIELD_FORBIDDEN:{forbidden}")
    observed_result = observation.get("observed_result")
    if not _nonempty(observed_result):
        return _fail("OBSERVED_RESULT_REQUIRED")
    discriminator = observation.get("discriminator")
    branch_ids = {b["id"] for b in state["branches"]}
    disc_err = _validate_discriminator(discriminator, branch_ids)
    if disc_err:
        return _fail(disc_err)
    if discriminator.get("exhaustive_deterministic_partition") is not True:
        return _ok(
            labeler="D_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "DISCRIMINATOR_NOT_EXHAUSTIVE_DETERMINISTIC"},
            retained_branch_ids=retained,
        )
    predictions = discriminator["branch_predictions"]
    matching = [b["id"] for b in live if predictions[b["id"]] == observed_result]
    if len(matching) != 1:
        return _ok(
            labeler="D_resolve",
            resolution={
                "status": "UNRESOLVED",
                "resolved_branch": None,
                "basis": "OBSERVED_RESULT_DOES_NOT_UNIQUELY_IDENTIFY_ONE_LIVE_BRANCH",
                "matching_live_branch_ids": sorted(matching),
            },
            retained_branch_ids=retained,
        )
    winner = matching[0]
    evidence = observation.get("evidence")
    evidence_err = _validate_evidence(evidence)
    if evidence_err:
        return _fail(evidence_err)
    independent, identity_err, dependence_matches = _evidence_identity_guard(state, evidence)
    if identity_err:
        return _fail(identity_err)
    return _ok(
        labeler="D_resolve",
        resolution={
            "status": "RESOLVED_WITHIN_SYNTHETIC_WORLD",
            "resolved_branch": winner,
            "basis": "DERIVED_EXHAUSTIVE_DISCRIMINATOR_MATCH",
            "discriminator_id": discriminator["discriminator_id"],
            "prediction_derivation_id": discriminator["prediction_derivation_id"],
            "reopen_policy": "REOPEN_ON_PRECONDITION_INVALIDATION",
            "precondition_ids": [evidence["evidence_id"], discriminator["discriminator_id"]],
        },
        retained_branch_ids=retained,
        evidence_independent_for_update=independent,
        dependence_matches=dependence_matches,
    )


def U_d_test_order(state: Any, discriminators: Any) -> dict[str, Any]:
    """Probability-free ordinal discriminator ordering using derived prediction partitions."""
    validated, err = _validate_state(state)
    if err:
        return _fail(err)
    assert validated is not None
    if not isinstance(discriminators, list) or not discriminators:
        return _fail("DISCRIMINATOR_LIST_REQUIRED")
    live_ids = sorted(b["id"] for b in state["branches"] if b["sigma"] != "FALSIFIED" and b["K"] != "DOES_NOT_APPLY")
    branch_ids = {b["id"] for b in state["branches"]}
    rows: list[dict[str, Any]] = []
    for d in discriminators:
        disc_err = _validate_discriminator(d, branch_ids)
        if disc_err:
            return _fail(disc_err)
        predictions = d["branch_predictions"]
        separated = 0
        for a, b in combinations(live_ids, 2):
            if predictions[a] != predictions[b]:
                separated += 1
        groups: dict[str, int] = {}
        for bid in live_ids:
            groups[predictions[bid]] = groups.get(predictions[bid], 0) + 1
        worst = max(groups.values()) if groups else 0
        for field in ("risk_class", "execution_cost_class", "coordination_cost_class"):
            value = d.get(field, 0)
            if not isinstance(value, int) or value < 0:
                return _fail(f"DISCRIMINATOR_{field.upper()}_INVALID")
        rows.append({
            "discriminator_id": d["discriminator_id"],
            "separated_live_pairs": separated,
            "worst_case_remaining_partition": worst,
            "risk_class": d.get("risk_class", 0),
            "execution_cost_class": d.get("execution_cost_class", 0),
            "coordination_cost_class": d.get("coordination_cost_class", 0),
        })
    rows.sort(key=lambda r: (
        -r["separated_live_pairs"],
        r["worst_case_remaining_partition"],
        r["risk_class"],
        r["execution_cost_class"],
        r["coordination_cost_class"],
        r["discriminator_id"],
    ))
    for rank, row in enumerate(rows, 1):
        row["ordinal_rank"] = rank
    return _ok(
        labeler="U_d_test_order",
        ordering=rows,
        probability_output=False,
        truth_output=False,
        rule="MAX_DERIVED_PAIR_SEPARATION_THEN_MIN_WORST_PARTITION_THEN_MIN_ORDINAL_COSTS",
    )


def f_salience_rank(items: Any) -> dict[str, Any]:
    """Attention ordering only; never a truth/probability/evidence-strength label."""
    if not isinstance(items, list) or not items:
        return _fail("SALIENCE_ITEM_LIST_REQUIRED")
    rows: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict) or not _nonempty(item.get("item_id")):
            return _fail("SALIENCE_ITEM_INVALID")
        row = deepcopy(item)
        for field in (
            "authority_boundary_risk",
            "expiry_or_time_urgency",
            "live_discriminator_relevance",
            "current_goal_relevance",
        ):
            value = row.get(field, 0)
            if not isinstance(value, int) or value < 0:
                return _fail(f"SALIENCE_{field.upper()}_INVALID")
        row["novel_independent_evidence"] = bool(row.get("novel_independent_evidence", False))
        rows.append(row)
    rows.sort(key=lambda r: (
        -r.get("authority_boundary_risk", 0),
        -r.get("expiry_or_time_urgency", 0),
        -r.get("live_discriminator_relevance", 0),
        -r.get("current_goal_relevance", 0),
        -int(r["novel_independent_evidence"]),
        r["item_id"],
    ))
    return _ok(
        labeler="f_salience_rank",
        ranking=[{"item_id": r["item_id"], "ordinal_rank": i} for i, r in enumerate(rows, 1)],
        truth_output=False,
        probability_output=False,
        evidence_strength_output=False,
        rule="AUTHORITY_RISK_THEN_URGENCY_THEN_DISCRIMINATOR_RELEVANCE_THEN_GOAL_RELEVANCE_THEN_NOVEL_INDEPENDENT_EVIDENCE",
    )
