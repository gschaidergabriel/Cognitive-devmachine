#!/usr/bin/env python3
"""Deterministic Trigger-2 semantic-Hyperposition reference labelers (v1).

Scope:
- candidate/source training-data construction only;
- synthetic/method worlds only;
- never grants canonical truth or direct effect authority.

Implements the reference functions required by the current Trigger-2
semantic-Hyperposition contract:
  U_update, D_resolve, U_d_test_order, f_salience_rank.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from typing import Any, Dict, Sequence, Tuple

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v1"
BRANCH_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_BRANCH/v1"
ANTI_COLLAPSE = (
    "NO_MAJORITY_AS_TRUTH",
    "NO_SALIENCE_AS_PROBABILITY",
    "NO_RECURRENCE_AS_EVIDENCE",
    "NO_SILENT_BRANCH_DROP",
    "PROJECTION_IS_NOT_DELETION",
)
RESOLUTION_EVIDENCE_KINDS = {
    "EXACT_SYNTHETIC_PROOF",
    "EXPLICIT_FALSIFIER",
    "TYPED_SYNTHETIC_MEASUREMENT",
}


class LabelerError(ValueError):
    pass


def _required(d: Dict[str, Any], keys: Sequence[str], where: str) -> None:
    missing = [k for k in keys if k not in d]
    if missing:
        raise LabelerError(f"{where}: missing required fields {missing}")


def validate_branch(branch: Dict[str, Any]) -> None:
    _required(
        branch,
        (
            "branch_id", "v_semantic_value", "K_context_predicate", "E_plus",
            "E_minus", "F_falsifier", "T_validity_scope", "A_origin_provenance",
            "sigma_epistemic_status", "projection_visibility", "validity",
        ),
        "branch",
    )
    if branch["validity"] not in {"LIVE", "FALSIFIED"}:
        raise LabelerError("branch.validity must be LIVE or FALSIFIED")
    if not isinstance(branch["E_plus"], list) or not isinstance(branch["E_minus"], list):
        raise LabelerError("E_plus/E_minus must be lists")


def validate_branch_set(branches: Sequence[Dict[str, Any]]) -> None:
    if len(branches) < 2:
        raise LabelerError("Hyperposition requires at least two branches")
    ids = []
    for branch in branches:
        validate_branch(branch)
        ids.append(branch["branch_id"])
    if len(ids) != len(set(ids)):
        raise LabelerError("duplicate branch_id")


def _evidence_key(e: Dict[str, Any]) -> Tuple[str, str, str]:
    _required(e, ("evidence_id", "provenance_ancestry_id", "independence_group"), "evidence")
    return (e["evidence_id"], e["provenance_ancestry_id"], e["independence_group"])


def _seen_evidence_keys(branch: Dict[str, Any]) -> set[Tuple[str, str, str]]:
    return {_evidence_key(e) for e in branch["E_plus"] + branch["E_minus"]}


def _observation_evidence(observation: Dict[str, Any]) -> Dict[str, Any]:
    _required(
        observation,
        ("evidence_id", "provenance_ancestry_id", "independence_group", "evidence_kind"),
        "observation",
    )
    return {
        "evidence_id": observation["evidence_id"],
        "provenance_ancestry_id": observation["provenance_ancestry_id"],
        "independence_group": observation["independence_group"],
        "evidence_kind": observation["evidence_kind"],
        "payload_ref": observation.get("payload_ref", "INLINE_SYNTHETIC"),
    }


def U_update(branches: Sequence[Dict[str, Any]], observation: Dict[str, Any]) -> Dict[str, Any]:
    """Update branch-local evidence without silent collapse; exact replay is idempotent."""
    validate_branch_set(branches)
    _required(observation, ("supports", "contradicts", "falsifies"), "observation")
    ids = {b["branch_id"] for b in branches}
    for field in ("supports", "contradicts", "falsifies"):
        unknown = set(observation[field]) - ids
        if unknown:
            raise LabelerError(f"{field}: unknown branch ids {sorted(unknown)}")

    evidence = _observation_evidence(observation)
    ek = _evidence_key(evidence)
    out = copy.deepcopy(list(branches))
    audit = {
        "schema": SCHEMA, "operation": "U_update", "evidence_key": list(ek),
        "added_support": [], "added_counterevidence": [], "falsified": [],
        "duplicate_ignored": [], "retained": [],
    }

    for branch in out:
        bid = branch["branch_id"]
        seen = _seen_evidence_keys(branch)
        touched = False
        if bid in observation["supports"]:
            touched = True
            if ek in seen:
                audit["duplicate_ignored"].append([bid, "E_plus"])
            else:
                branch["E_plus"].append(copy.deepcopy(evidence))
                seen.add(ek)
                audit["added_support"].append(bid)
        if bid in observation["contradicts"] or bid in observation["falsifies"]:
            touched = True
            if ek in seen:
                audit["duplicate_ignored"].append([bid, "E_minus"])
            else:
                branch["E_minus"].append(copy.deepcopy(evidence))
                seen.add(ek)
                audit["added_counterevidence"].append(bid)
        if bid in observation["falsifies"]:
            branch["validity"] = "FALSIFIED"
            audit["falsified"].append(bid)
        if not touched:
            audit["retained"].append(bid)

    validate_branch_set(out)
    return {"branches": out, "audit": audit}


def D_resolve(branches_after: Sequence[Dict[str, Any]], observation: Dict[str, Any] | None) -> Dict[str, Any]:
    """Resolve task-local synthetic branches only under explicit discriminator evidence."""
    validate_branch_set(branches_after)
    live = [b["branch_id"] for b in branches_after if b["validity"] == "LIVE"]
    falsified = [b["branch_id"] for b in branches_after if b["validity"] == "FALSIFIED"]
    base = {
        "schema": SCHEMA, "operation": "D_resolve", "canonical_truth_allowed": False,
        "direct_effect_authority": False, "live_branches": live,
        "falsified_branches": falsified, "resolved_branch": None,
        "status": "UNRESOLVED", "reason": None,
    }
    if observation is None:
        base["reason"] = "NO_DISCRIMINATING_OBSERVATION"; return base
    if not observation.get("discriminator_id"):
        base["reason"] = "NO_EXPLICIT_DISCRIMINATOR"; return base
    if observation.get("evidence_kind") not in RESOLUTION_EVIDENCE_KINDS:
        base["reason"] = "EVIDENCE_KIND_NOT_RESOLUTION_QUALIFIED"; return base
    if not observation.get("resolution_authorized", False):
        base["reason"] = "RESOLUTION_NOT_AUTHORIZED_BY_SYNTHETIC_TASK_RULE"; return base
    if not observation.get("synthetic_world", False):
        base["reason"] = "NON_SYNTHETIC_WORLD_CANNOT_BE_RESOLVED_BY_THIS_TRAINING_LABELER"; return base
    if len(live) != 1:
        base["reason"] = "MULTIPLE_OR_ZERO_LIVE_BRANCHES_REMAIN"; return base
    if not falsified:
        base["reason"] = "NO_COMPETING_BRANCH_WAS_FALSIFIED"; return base
    base["status"] = "RESOLVED_WITHIN_SYNTHETIC_WORLD"
    base["resolved_branch"] = live[0]
    base["reason"] = "EXPLICIT_DISCRIMINATOR_LEFT_EXACTLY_ONE_LIVE_BRANCH"
    return base


def _live_pairs(branches: Sequence[Dict[str, Any]]) -> set[Tuple[str, str]]:
    live = sorted(b["branch_id"] for b in branches if b["validity"] == "LIVE")
    return {tuple(pair) for pair in itertools.combinations(live, 2)}


def U_d_test_order(branches: Sequence[Dict[str, Any]], candidates: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Ordinal discriminator ranking by live-branch pair coverage, then lower cost."""
    validate_branch_set(branches)
    required_pairs = _live_pairs(branches)
    ranked = []
    for candidate in candidates:
        _required(candidate, ("discriminator_id", "separates_pairs", "cost_rank", "independence_group"), "discriminator")
        pairs = set()
        for pair in candidate["separates_pairs"]:
            if len(pair) != 2:
                raise LabelerError("separates_pairs entries must contain two branch ids")
            pairs.add(tuple(sorted(pair)))
        coverage = len(required_pairs & pairs)
        ranked.append({
            "discriminator_id": candidate["discriminator_id"],
            "coverage_pairs": coverage,
            "covers_all_live_pairs": bool(required_pairs) and required_pairs.issubset(pairs),
            "cost_rank": int(candidate["cost_rank"]),
            "independence_group": candidate["independence_group"],
        })
    ranked.sort(key=lambda x: (-x["coverage_pairs"], x["cost_rank"], x["discriminator_id"]))
    return {
        "schema": SCHEMA, "operation": "U_d_test_order",
        "required_live_pairs": [list(x) for x in sorted(required_pairs)],
        "ranking": ranked, "probability_interpretation_forbidden": True,
    }


def f_salience_rank(candidates: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Rank attention salience separately from truth/evidence."""
    ranked = []
    for candidate in candidates:
        _required(candidate, ("item_id", "context_match", "task_relevance_rank", "novelty"), "salience item")
        ranked.append({
            "item_id": candidate["item_id"],
            "context_match": bool(candidate["context_match"]),
            "task_relevance_rank": int(candidate["task_relevance_rank"]),
            "novelty": bool(candidate["novelty"]),
        })
    ranked.sort(key=lambda x: (-int(x["context_match"]), x["task_relevance_rank"], -int(x["novelty"]), x["item_id"]))
    return {
        "schema": SCHEMA, "operation": "f_salience_rank", "ranking": ranked,
        "salience_is_probability": False, "salience_is_truth": False,
    }


def _branch(bid: str, value: str) -> Dict[str, Any]:
    return {
        "schema": BRANCH_SCHEMA, "branch_id": bid, "v_semantic_value": value,
        "K_context_predicate": "ctx=synthetic_case", "E_plus": [], "E_minus": [],
        "F_falsifier": f"falsify:{bid}", "T_validity_scope": "synthetic_case_only",
        "A_origin_provenance": "trigger2-labeler-selftest", "sigma_epistemic_status": "HYPOTHESIS",
        "projection_visibility": "VISIBLE", "validity": "LIVE",
    }


def selftest() -> Dict[str, Any]:
    branches = [_branch("b0", "TRUE"), _branch("b1", "FALSE"), _branch("b2", "UNKNOWN")]
    nondisc = {
        "evidence_id": "e1", "provenance_ancestry_id": "p1", "independence_group": "g1",
        "evidence_kind": "NONDISCRIMINATING_OBSERVATION", "supports": ["b0"],
        "contradicts": ["b1"], "falsifies": [], "discriminator_id": None,
        "resolution_authorized": False, "synthetic_world": True,
    }
    s1 = U_update(branches, nondisc)
    assert D_resolve(s1["branches"], nondisc)["status"] == "UNRESOLVED"
    assert len([b for b in s1["branches"] if b["validity"] == "LIVE"]) == 3
    s1_replay = U_update(s1["branches"], nondisc)
    assert s1_replay["audit"]["added_support"] == []
    assert s1_replay["audit"]["added_counterevidence"] == []
    assert len(s1_replay["audit"]["duplicate_ignored"]) == 2
    disc = {
        "evidence_id": "e2", "provenance_ancestry_id": "p2", "independence_group": "g2",
        "evidence_kind": "EXACT_SYNTHETIC_PROOF", "supports": ["b0"], "contradicts": [],
        "falsifies": ["b1", "b2"], "discriminator_id": "d_exact",
        "resolution_authorized": True, "synthetic_world": True,
    }
    s2 = U_update(s1["branches"], disc)
    r2 = D_resolve(s2["branches"], disc)
    assert r2["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD" and r2["resolved_branch"] == "b0"
    majority = dict(disc)
    majority.update({"evidence_id": "e3", "evidence_kind": "RECURRENCE_OR_MAJORITY", "discriminator_id": None, "resolution_authorized": False})
    assert D_resolve(s2["branches"], majority)["status"] == "UNRESOLVED"
    order = U_d_test_order(branches, [
        {"discriminator_id": "d_partial", "separates_pairs": [["b0","b1"]], "cost_rank": 1, "independence_group": "test-a"},
        {"discriminator_id": "d_full", "separates_pairs": [["b0","b1"],["b0","b2"],["b1","b2"]], "cost_rank": 2, "independence_group": "test-b"},
    ])
    assert order["ranking"][0]["discriminator_id"] == "d_full"
    salience = f_salience_rank([
        {"item_id": "i0", "context_match": True, "task_relevance_rank": 1, "novelty": False},
        {"item_id": "i1", "context_match": False, "task_relevance_rank": 0, "novelty": True},
    ])
    assert salience["salience_is_truth"] is False and salience["salience_is_probability"] is False
    return {
        "pass": True, "schema": SCHEMA, "tests": 6, "anti_collapse": list(ANTI_COLLAPSE),
        "scope": "DETERMINISTIC_SOURCE_SELFTEST_ONLY", "training_credit": 0, "runtime_credit": 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); args = ap.parse_args()
    print(json.dumps(selftest() if args.selftest else {"schema": SCHEMA, "status": "REFERENCE_LABELER_LIBRARY"}, sort_keys=True))


if __name__ == "__main__":
    main()
