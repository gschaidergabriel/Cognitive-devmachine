#!/usr/bin/env python3
"""Deterministic Trigger-2 reference labelers for synthetic Hyperposition training cases.

Scope:
- deterministic candidate-label generation only;
- no canonical-truth authority;
- no runtime/model/training credit;
- branch order is a nuisance;
- salience is attention ordering only, never truth/probability.

The four exported reference functions correspond to the current Trigger-2 contract:
    U_update
    D_resolve
    U_d_test_order
    f_salience_rank
"""

from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Dict, List, Mapping, Sequence, Tuple

REQUIRED_BRANCH_FIELDS = (
    "branch_id",
    "v_semantic_value",
    "K_context_predicate",
    "E_plus",
    "E_minus",
    "F_falsifier",
    "T_validity_scope",
    "A_origin_provenance",
    "sigma_epistemic_status",
)

RELATIONS = {"SUPPORT", "COUNTER", "FALSIFY", "NONE"}
OUTCOMES = {"PASS", "FAIL", "UNKNOWN"}


class LabelerError(ValueError):
    """Fail-closed input/schema error."""


def _require_branch(branch: Mapping[str, Any]) -> None:
    missing = [k for k in REQUIRED_BRANCH_FIELDS if k not in branch]
    if missing:
        raise LabelerError(f"missing branch fields: {missing}")
    if not isinstance(branch["branch_id"], str) or not branch["branch_id"]:
        raise LabelerError("branch_id must be a non-empty string")
    if not isinstance(branch["E_plus"], list) or not isinstance(branch["E_minus"], list):
        raise LabelerError("E_plus and E_minus must be lists")


def _branch_ids(branch_set: Sequence[Mapping[str, Any]]) -> List[str]:
    ids: List[str] = []
    for branch in branch_set:
        _require_branch(branch)
        ids.append(branch["branch_id"])
    if len(ids) != len(set(ids)):
        raise LabelerError("duplicate branch_id")
    if len(ids) < 2:
        raise LabelerError("Hyperposition reference cases require >=2 branches")
    return ids


def _evidence_record(observation: Mapping[str, Any], relation: str) -> Dict[str, Any]:
    evidence_id = observation.get("evidence_id")
    independence_group = observation.get("independence_group")
    provenance = observation.get("provenance")
    if not isinstance(evidence_id, str) or not evidence_id:
        raise LabelerError("observation.evidence_id must be a non-empty string")
    if not isinstance(independence_group, str) or not independence_group:
        raise LabelerError("observation.independence_group must be a non-empty string")
    if provenance in (None, ""):
        raise LabelerError("observation.provenance is required")
    return {
        "evidence_id": evidence_id,
        "independence_group": independence_group,
        "provenance": provenance,
        "relation": relation,
    }


def _append_unique_evidence(target: List[Dict[str, Any]], record: Dict[str, Any]) -> None:
    """Replay-safe: same evidence_id is not counted twice."""
    if any(item.get("evidence_id") == record["evidence_id"] for item in target):
        return
    target.append(record)


def U_update(
    branch_set: Sequence[Mapping[str, Any]],
    observation: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    """Deterministically update branch-local evidence without destructive collapse.

    observation.relation_by_branch maps every branch id to one of:
    SUPPORT | COUNTER | FALSIFY | NONE.

    FALSIFY marks a branch as falsified but retains it in the branch set so provenance,
    contradiction, and replay remain inspectable.
    """
    ids = _branch_ids(branch_set)
    rel = observation.get("relation_by_branch")
    if not isinstance(rel, Mapping):
        raise LabelerError("observation.relation_by_branch must be a mapping")
    if set(rel.keys()) != set(ids):
        raise LabelerError("relation_by_branch must cover exactly the current branch ids")
    bad = {value for value in rel.values() if value not in RELATIONS}
    if bad:
        raise LabelerError(f"invalid relation(s): {sorted(bad)}")

    out = deepcopy(list(branch_set))
    for branch in out:
        relation = rel[branch["branch_id"]]
        if relation == "NONE":
            continue
        record = _evidence_record(observation, relation)
        if relation == "SUPPORT":
            _append_unique_evidence(branch["E_plus"], record)
        else:
            _append_unique_evidence(branch["E_minus"], record)
        if relation == "FALSIFY":
            branch["sigma_epistemic_status"] = "FALSIFIED"
            branch["falsified_by"] = record["evidence_id"]
    return out


def D_resolve(
    branch_set: Sequence[Mapping[str, Any]],
    discriminator_outcomes: Mapping[str, str] | None,
) -> Dict[str, Any]:
    """Resolve only from an explicit discriminator outcome.

    Resolution is permitted iff exactly one branch is PASS and every other branch is FAIL.
    UNKNOWN, missing outcomes, majority, salience, recurrence, or support-count asymmetry
    cannot resolve a Hyperposition reference case.
    """
    ids = _branch_ids(branch_set)
    if discriminator_outcomes is None:
        return {
            "resolution_status": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "NO_DISCRIMINATOR_OUTCOME",
        }
    if set(discriminator_outcomes.keys()) != set(ids):
        raise LabelerError("discriminator outcomes must cover exactly the current branch ids")
    bad = {v for v in discriminator_outcomes.values() if v not in OUTCOMES}
    if bad:
        raise LabelerError(f"invalid discriminator outcome(s): {sorted(bad)}")

    passed = [bid for bid in ids if discriminator_outcomes[bid] == "PASS"]
    failed = [bid for bid in ids if discriminator_outcomes[bid] == "FAIL"]
    if len(passed) == 1 and len(failed) == len(ids) - 1:
        return {
            "resolution_status": "RESOLVED_BY_DISCRIMINATOR",
            "resolved_branch_id": passed[0],
            "reason": "ONE_PASS_ALL_OTHERS_FAIL",
        }
    return {
        "resolution_status": "UNRESOLVED",
        "resolved_branch_id": None,
        "reason": "DISCRIMINATOR_NOT_UNIQUE_OR_INCOMPLETE",
    }


def _normalized_pair(pair: Sequence[str]) -> Tuple[str, str]:
    if len(pair) != 2:
        raise LabelerError("distinguishes_pairs entries must contain exactly two branch ids")
    a, b = pair
    if not isinstance(a, str) or not isinstance(b, str) or a == b:
        raise LabelerError("invalid distinguishes_pairs entry")
    return tuple(sorted((a, b)))


def U_d_test_order(
    live_branch_ids: Sequence[str],
    candidates: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Return a deterministic ordinal ranking of discriminators.

    Priority:
    1. greater coverage of currently live branch pairs;
    2. independent evidence source/group preferred;
    3. lower declared nonnegative cost;
    4. candidate_id lexical tie-break.

    This is an ordering target, not a calibrated probability or truth score.
    """
    ids = list(live_branch_ids)
    if len(ids) < 2 or len(ids) != len(set(ids)):
        raise LabelerError("live_branch_ids must contain >=2 unique ids")
    live_pairs = {tuple(sorted(p)) for p in combinations(ids, 2)}
    ranked: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []

    for candidate in candidates:
        cid = candidate.get("candidate_id")
        if not isinstance(cid, str) or not cid:
            raise LabelerError("candidate_id must be a non-empty string")
        raw_pairs = candidate.get("distinguishes_pairs", [])
        if not isinstance(raw_pairs, list):
            raise LabelerError("distinguishes_pairs must be a list")
        covered = {_normalized_pair(p) for p in raw_pairs} & live_pairs
        independent = bool(candidate.get("independent_of_existing", False))
        cost = candidate.get("cost", 0.0)
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
            raise LabelerError("candidate cost must be a nonnegative number")
        key = (-len(covered), -int(independent), float(cost), cid)
        ranked.append(
            (
                key,
                {
                    "candidate_id": cid,
                    "live_pair_coverage": len(covered),
                    "independent_of_existing": independent,
                    "cost": float(cost),
                    "ordering_only": True,
                },
            )
        )

    ranked.sort(key=lambda item: item[0])
    return [dict(item[1], rank=i + 1) for i, item in enumerate(ranked)]


def f_salience_rank(branch_set: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Rank attention salience only; never emit truth, probability, or resolution labels."""
    _branch_ids(branch_set)
    rows: List[Tuple[Tuple[float, str], Dict[str, Any]]] = []
    for branch in branch_set:
        salience = branch.get("salience", 0.0)
        if not isinstance(salience, (int, float)) or isinstance(salience, bool):
            raise LabelerError("branch salience must be numeric when present")
        bid = branch["branch_id"]
        rows.append(
            (
                (-float(salience), bid),
                {
                    "branch_id": bid,
                    "salience": float(salience),
                    "attention_ordering_only": True,
                    "truth_semantics": "NONE",
                },
            )
        )
    rows.sort(key=lambda item: item[0])
    return [dict(item[1], rank=i + 1) for i, item in enumerate(rows)]


__all__ = [
    "LabelerError",
    "U_update",
    "D_resolve",
    "U_d_test_order",
    "f_salience_rank",
]
