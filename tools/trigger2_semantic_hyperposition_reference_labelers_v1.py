#!/usr/bin/env python3
"""Deterministic reference labelers for Trigger-2 semantic Hyperposition.

Pure synthetic/curriculum reference logic only. These functions label candidate state
transitions and discriminator/salience ordering. They do NOT mint canonical truth,
real-effect authority, J-Space runtime credit, HCU credit, or training credit.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_REFERENCE_LABELERS/v1"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v1"
OBS_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_OBSERVATION/v1"
DISC_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_DISCRIMINATOR/v1"

ALLOWED_EFFECTS = {"SUPPORT", "WEAKEN", "FALSIFY", "PROVE", "RETAIN"}
ALLOWED_EPISTEMIC = {
    "OBSERVED", "UNKNOWN", "HYPOTHESIS", "COUNTERHYPOTHESIS",
    "PREDICTION", "MEASUREMENT_ERROR", "CONTRADICTION", "SYNTHETIC_PROOF",
}
ALLOWED_VALIDITY = {"LIVE", "FALSIFIED", "PROVEN_WITHIN_SYNTHETIC_WORLD"}


def _fail(code: str, **extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": False,
        "failure": code,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
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
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


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
    seen: set[str] = set()
    for b in branches:
        if not isinstance(b, dict):
            return None, "BRANCH_OBJECT_REQUIRED"
        bid = b.get("branch_id")
        if not isinstance(bid, str) or not bid:
            return None, "BRANCH_ID_REQUIRED"
        if bid in seen:
            return None, "DUPLICATE_BRANCH_ID"
        seen.add(bid)
        if b.get("validity") not in ALLOWED_VALIDITY:
            return None, "BRANCH_VALIDITY_INVALID"
        if not isinstance(b.get("evidence_for"), list) or not isinstance(b.get("evidence_against"), list):
            return None, "BRANCH_EVIDENCE_LISTS_REQUIRED"
    return state, None


def _has_same_ancestry(branch: dict[str, Any], ancestry: str) -> bool:
    for side in ("evidence_for", "evidence_against"):
        for e in branch.get(side, []):
            if isinstance(e, dict) and e.get("provenance_ancestry_id") == ancestry:
                return True
    return False


def U_update(state: Any, observation: Any) -> dict[str, Any]:
    """Deterministically label one branch-set update without deleting branches.

    Duplicate evidence from the same provenance ancestry is retained as provenance but
    marked non-independent and cannot create a second independent update.
    """
    _, err = _validate_state(state)
    if err:
        return _fail(err)
    if not isinstance(observation, dict) or observation.get("schema") != OBS_SCHEMA:
        return _fail("OBSERVATION_SCHEMA_MISMATCH")
    if observation.get("canonical_truth_allowed") is not False:
        return _fail("OBSERVATION_CANONICAL_TRUTH_MUST_BE_FALSE")
    if observation.get("direct_effect_authority") is not False:
        return _fail("OBSERVATION_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    effect = observation.get("effect")
    if effect not in ALLOWED_EFFECTS:
        return _fail("OBSERVATION_EFFECT_INVALID")
    targets = observation.get("target_branch_ids")
    if not isinstance(targets, list) or not targets or not all(isinstance(x, str) and x for x in targets):
        return _fail("OBSERVATION_TARGET_BRANCH_IDS_REQUIRED")
    evidence = observation.get("evidence")
    if not isinstance(evidence, dict):
        return _fail("OBSERVATION_EVIDENCE_OBJECT_REQUIRED")
    required = {"evidence_id", "provenance_ancestry_id", "independence_group", "epistemic_type"}
    if not required.issubset(evidence):
        return _fail("OBSERVATION_EVIDENCE_FIELDS_MISSING")
    if evidence.get("epistemic_type") not in ALLOWED_EPISTEMIC:
        return _fail("OBSERVATION_EPISTEMIC_TYPE_INVALID")

    out = deepcopy(state)
    branch_by_id = {b["branch_id"]: b for b in out["branches"]}
    missing = sorted(set(targets) - set(branch_by_id))
    if missing:
        return _fail("OBSERVATION_TARGET_BRANCH_UNKNOWN", unknown_branch_ids=missing)

    ancestry = str(evidence["provenance_ancestry_id"])
    if not ancestry:
        return _fail("PROVENANCE_ANCESTRY_REQUIRED")

    updates = []
    for bid in targets:
        branch = branch_by_id[bid]
        same_ancestry = _has_same_ancestry(branch, ancestry)
        ev = deepcopy(evidence)
        ev["independent_for_update"] = not same_ancestry
        ev["applied_effect"] = effect
        ev["target_branch_id"] = bid

        if effect in {"SUPPORT", "PROVE"}:
            branch["evidence_for"].append(ev)
        elif effect in {"WEAKEN", "FALSIFY"}:
            branch["evidence_against"].append(ev)
        elif effect == "RETAIN":
            branch.setdefault("retention_events", []).append(ev)

        validity_before = branch["validity"]
        if not same_ancestry:
            if effect == "FALSIFY":
                branch["validity"] = "FALSIFIED"
            elif effect == "PROVE":
                branch["validity"] = "PROVEN_WITHIN_SYNTHETIC_WORLD"
        updates.append({
            "branch_id": bid,
            "effect": effect,
            "independent_for_update": not same_ancestry,
            "validity_before": validity_before,
            "validity_after": branch["validity"],
        })

    out["branches"] = [branch_by_id[b["branch_id"]] for b in state["branches"]]
    out["last_observation_id"] = evidence["evidence_id"]
    return _ok(
        labeler="U_update",
        state_after=out,
        updates=updates,
        branch_count_before=len(state["branches"]),
        branch_count_after=len(out["branches"]),
        automatic_resolution_performed=False,
        duplicate_ancestry_rule="SAME_PROVENANCE_ANCESTRY_IS_NONINDEPENDENT_FOR_UPDATE",
    )


def D_resolve(state: Any, discriminator_outcome: Any | None = None) -> dict[str, Any]:
    """Resolve only from explicit synthetic proof/discriminator evidence.

    Resolution changes a task-local status; it never deletes alternatives or mints world truth.
    """
    _, err = _validate_state(state)
    if err:
        return _fail(err)
    live = [b for b in state["branches"] if b["validity"] != "FALSIFIED"]
    proven = [b for b in live if b["validity"] == "PROVEN_WITHIN_SYNTHETIC_WORLD"]

    if discriminator_outcome is None:
        if len(proven) == 1:
            winner = proven[0]["branch_id"]
            return _ok(
                labeler="D_resolve",
                resolution={"status": "RESOLVED_WITHIN_SYNTHETIC_WORLD", "resolved_branch": winner, "basis": "EXPLICIT_SYNTHETIC_PROOF"},
                retained_branch_ids=[b["branch_id"] for b in state["branches"]],
            )
        return _ok(
            labeler="D_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "NO_UNIQUE_EXPLICIT_PROOF_OR_DISCRIMINATOR"},
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )

    if not isinstance(discriminator_outcome, dict):
        return _fail("DISCRIMINATOR_OUTCOME_OBJECT_REQUIRED")
    if discriminator_outcome.get("schema") != DISC_SCHEMA:
        return _fail("DISCRIMINATOR_SCHEMA_MISMATCH")
    if discriminator_outcome.get("canonical_truth_allowed") is not False:
        return _fail("DISCRIMINATOR_CANONICAL_TRUTH_MUST_BE_FALSE")
    if discriminator_outcome.get("direct_effect_authority") is not False:
        return _fail("DISCRIMINATOR_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    winner = discriminator_outcome.get("winner_branch_id")
    separates = discriminator_outcome.get("separates_live_branch_ids")
    if winner not in {b["branch_id"] for b in live}:
        return _fail("DISCRIMINATOR_WINNER_NOT_LIVE")
    if not isinstance(separates, list):
        return _fail("DISCRIMINATOR_SEPARATION_SET_REQUIRED")
    live_ids = {b["branch_id"] for b in live}
    if set(separates) != live_ids:
        return _ok(
            labeler="D_resolve",
            resolution={"status": "UNRESOLVED", "resolved_branch": None, "basis": "DISCRIMINATOR_DOES_NOT_SEPARATE_ALL_LIVE_ALTERNATIVES"},
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )
    return _ok(
        labeler="D_resolve",
        resolution={"status": "RESOLVED_WITHIN_SYNTHETIC_WORLD", "resolved_branch": winner, "basis": "EXPLICIT_DISCRIMINATOR"},
        retained_branch_ids=[b["branch_id"] for b in state["branches"]],
    )


def U_d_test_order(state: Any, discriminators: Any) -> dict[str, Any]:
    """Deterministic ordinal discriminator ordering; never outputs probabilities.

    Order: admissible first, then more live-branch pairs separated, then lower cost_rank,
    then stable discriminator_id. This is a curriculum/reference ordering, not truth.
    """
    _, err = _validate_state(state)
    if err:
        return _fail(err)
    if not isinstance(discriminators, list) or not discriminators:
        return _fail("DISCRIMINATOR_LIST_REQUIRED")
    live_ids = {b["branch_id"] for b in state["branches"] if b["validity"] != "FALSIFIED"}
    rows = []
    for d in discriminators:
        if not isinstance(d, dict) or d.get("schema") != DISC_SCHEMA:
            return _fail("DISCRIMINATOR_SCHEMA_MISMATCH")
        did = d.get("discriminator_id")
        pairs = d.get("separates_pairs")
        cost = d.get("cost_rank")
        if not isinstance(did, str) or not did:
            return _fail("DISCRIMINATOR_ID_REQUIRED")
        if not isinstance(pairs, list) or not isinstance(cost, int) or cost < 0:
            return _fail("DISCRIMINATOR_ORDER_FIELDS_INVALID")
        covered = set()
        for p in pairs:
            if isinstance(p, list) and len(p) == 2 and all(x in live_ids for x in p) and p[0] != p[1]:
                covered.add(tuple(sorted(p)))
        admissible = (
            d.get("canonical_truth_allowed") is False
            and d.get("direct_effect_authority") is False
            and d.get("admissible") is True
        )
        rows.append({
            "discriminator_id": did,
            "admissible": admissible,
            "separated_live_pairs": len(covered),
            "cost_rank": cost,
            "score_tuple": (0 if admissible else 1, -len(covered), cost, did),
        })
    rows.sort(key=lambda x: x["score_tuple"])
    for i, r in enumerate(rows, 1):
        r["ordinal_rank"] = i
        del r["score_tuple"]
    return _ok(
        labeler="U_d_test_order",
        ordering=rows,
        probability_output=False,
        truth_output=False,
        rule="ADMISSIBLE_THEN_MAX_PAIR_SEPARATION_THEN_MIN_COST_THEN_STABLE_ID",
    )


def f_salience_rank(items: Any) -> dict[str, Any]:
    """Deterministic attention/salience ranking with explicit anti-truth boundary.

    Salience is based only on declared actionability, scope and freshness ranks and is not
    evidence strength, probability, branch truth, or resolution authority.
    """
    if not isinstance(items, list) or not items:
        return _fail("SALIENCE_ITEM_LIST_REQUIRED")
    rows = []
    for item in items:
        if not isinstance(item, dict):
            return _fail("SALIENCE_ITEM_OBJECT_REQUIRED")
        iid = item.get("item_id")
        actionability = item.get("actionability_rank")
        scope = item.get("scope_rank")
        freshness = item.get("freshness_rank")
        if not isinstance(iid, str) or not iid:
            return _fail("SALIENCE_ITEM_ID_REQUIRED")
        if not all(isinstance(x, int) and x >= 0 for x in (actionability, scope, freshness)):
            return _fail("SALIENCE_RANK_FIELDS_INVALID")
        rows.append({
            "item_id": iid,
            "actionability_rank": actionability,
            "scope_rank": scope,
            "freshness_rank": freshness,
            "_key": (actionability, scope, freshness, iid),
        })
    rows.sort(key=lambda x: x["_key"])
    for i, r in enumerate(rows, 1):
        r["salience_rank"] = i
        del r["_key"]
    return _ok(
        labeler="f_salience_rank",
        ranking=rows,
        probability_output=False,
        truth_output=False,
        evidence_strength_output=False,
        rule="LOWER_DECLARED_ACTIONABILITY_SCOPE_FRESHNESS_RANKS_FIRST_STABLE_ID_TIEBREAK",
    )
