#!/usr/bin/env python3
"""Trigger-2 deterministic Hyperposition/GRF reference labelers v2.

Corrects v1 evidence identity semantics: exact replay identity is idempotent, while a
distinct evidence event from the same correlation/ancestry family is preserved for audit
but receives no independent-evidence credit. Pure synthetic/curriculum reference logic;
never canonical truth/effect/J-Space/HCU/training authority.

v2 fail-closed hardening:
- branch IDs must be unique/non-empty;
- every observation target must resolve to a current branch;
- one exact evidence-event ID cannot silently change relation or correlation ancestry;
- merge targets cannot collide with surviving branches;
- PASS application must select exactly one existing branch.
"""
from __future__ import annotations
from copy import deepcopy
from itertools import combinations
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v2"
LIVE_SIGMA = {"LIVE_UNRESOLVED", "SUPPORTED_UNRESOLVED", "WEAKENED_UNRESOLVED", "RESOLVED_PASS"}
RELATIONS = {"SUPPORTS", "COUNTERS", "FALSIFIES", "IRRELEVANT", "UNKNOWN_RELATION"}


def _event_id(e: Dict[str, Any]) -> str:
    return str(e.get("evidence_event_id") or e.get("evidence_id") or "")


def _ancestry(e: Dict[str, Any]) -> str:
    return str(e.get("correlation_ancestry_id") or e.get("causal_ancestry_id") or "")


def _validate_branches(branches: List[Dict[str, Any]]) -> None:
    ids = [b.get("branch_id") for b in branches]
    if any(not isinstance(i, str) or not i for i in ids):
        raise ValueError("every branch requires a non-empty string branch_id")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate branch_id in Hyperposition state")


def _validate_observation(observation: Dict[str, Any], branch_ids: set[str]) -> None:
    relation = observation.get("relation")
    if relation not in RELATIONS:
        raise ValueError(f"unknown relation: {relation}")
    targets = set(observation.get("target_branch_ids") or [])
    unknown = targets - branch_ids
    if unknown:
        raise ValueError(f"observation references unknown target branch ids: {sorted(unknown)}")
    if relation in {"SUPPORTS", "COUNTERS", "FALSIFIES"} and not targets:
        raise ValueError(f"{relation} observation requires at least one target branch")
    for field, value in (
        ("evidence_event_id", _event_id(observation)),
        ("correlation_ancestry_id", _ancestry(observation)),
        ("independence_group", observation.get("independence_group")),
        ("provenance", observation.get("provenance")),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field} required")


def _iter_evidence(branch: Dict[str, Any]):
    for field in ("E_plus", "E_minus", "F", "pending_falsifiers", "correlated_observations"):
        for e in branch.get(field, []) or []:
            if isinstance(e, dict):
                yield field, e


def _exact_seen(branch: Dict[str, Any], obs: Dict[str, Any]) -> bool:
    """Exact event replay is idempotent; identity collisions fail closed."""
    oid = _event_id(obs)
    if not oid:
        raise ValueError("evidence_event_id required")
    for _, existing in _iter_evidence(branch):
        if _event_id(existing) != oid:
            continue
        old_relation = str(existing.get("relation", ""))
        new_relation = str(obs.get("relation", ""))
        old_ancestry = _ancestry(existing)
        new_ancestry = _ancestry(obs)
        if old_relation and new_relation and old_relation != new_relation:
            raise ValueError("exact evidence_event_id reused with conflicting relation")
        if old_ancestry and new_ancestry and old_ancestry != new_ancestry:
            raise ValueError("exact evidence_event_id reused with conflicting correlation ancestry")
        return True
    return False


def _ancestry_seen(branch: Dict[str, Any], obs: Dict[str, Any]) -> bool:
    anc = _ancestry(obs)
    if not anc:
        raise ValueError("correlation_ancestry_id required")
    return any(_ancestry(e) == anc for _, e in _iter_evidence(branch))


def _record(obs: Dict[str, Any], *, independent_credit: bool) -> Dict[str, Any]:
    return {
        "evidence_event_id": _event_id(obs),
        "correlation_ancestry_id": _ancestry(obs),
        "independence_group": obs["independence_group"],
        "provenance": obs["provenance"],
        "relation": obs["relation"],
        "independent_credit": bool(independent_credit),
    }


def _attach(branch: Dict[str, Any], field: str, obs: Dict[str, Any], *, independent_credit: bool) -> None:
    branch.setdefault(field, []).append(_record(obs, independent_credit=independent_credit))


def _merge_explicit_equivalents(branches: List[Dict[str, Any]], cert: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    _validate_branches(branches)
    if not cert or not cert.get("equivalent"):
        return branches
    ids = sorted(set(cert.get("branch_ids") or []))
    if len(ids) < 2:
        return branches
    by_id = {b["branch_id"]: b for b in branches}
    if any(i not in by_id for i in ids):
        raise ValueError("equivalence certificate references unknown branch")
    group = [by_id[i] for i in ids]
    pivot = deepcopy(group[0])
    for b in group[1:]:
        if b.get("v") != pivot.get("v") or b.get("K") != pivot.get("K") or b.get("T") != pivot.get("T"):
            raise ValueError("equivalence certificate conflicts with branch semantics/scope")
    merged_id = cert.get("merge_to_branch_id") or ids[0]
    if not isinstance(merged_id, str) or not merged_id:
        raise ValueError("merge_to_branch_id must be a non-empty string")
    keep = [b for b in branches if b["branch_id"] not in ids]
    if any(b["branch_id"] == merged_id for b in keep):
        raise ValueError("merge_to_branch_id collides with an existing non-merged branch")
    pivot["branch_id"] = merged_id
    pivot["merged_from_branch_ids"] = ids
    for field in ("E_plus", "E_minus", "F", "pending_falsifiers", "correlated_observations"):
        seen = set()
        out = []
        for b in group:
            for e in b.get(field, []) or []:
                key = _event_id(e)
                if key and key not in seen:
                    seen.add(key)
                    out.append(deepcopy(e))
        if out:
            pivot[field] = out
    sigmas = {b.get("sigma") for b in group}
    if "FALSIFIED" in sigmas:
        pivot["sigma"] = "FALSIFIED"
    elif "WEAKENED_UNRESOLVED" in sigmas:
        pivot["sigma"] = "WEAKENED_UNRESOLVED"
    elif "SUPPORTED_UNRESOLVED" in sigmas:
        pivot["sigma"] = "SUPPORTED_UNRESOLVED"
    else:
        pivot["sigma"] = "LIVE_UNRESOLVED"
    pivot["A"] = {
        "merge_certificate": cert.get("certificate_id", "EXPLICIT_EQUIVALENCE"),
        "merged_origins": [deepcopy(b.get("A")) for b in group],
    }
    result = keep + [pivot]
    _validate_branches(result)
    return result


def u_state(state: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic state update preserving exact-event vs correlation-ancestry identity."""
    out = deepcopy(state)
    branches = out.setdefault("branches", [])
    if not isinstance(branches, list):
        raise ValueError("state.branches must be a list")
    _validate_branches(branches)
    branch_ids = {b["branch_id"] for b in branches}
    _validate_observation(observation, branch_ids)
    relation = observation["relation"]
    targets = set(observation.get("target_branch_ids") or [])
    for branch in branches:
        if branch.get("branch_id") not in targets:
            continue
        if branch.get("K") == "DOES_NOT_APPLY":
            branch["projection_visibility"] = "FILTERED_CONTEXT"
        if relation in {"IRRELEVANT", "UNKNOWN_RELATION"}:
            continue
        if _exact_seen(branch, observation):
            continue
        correlated = _ancestry_seen(branch, observation)
        independent_credit = not correlated and bool(observation.get("independence_qualified", False))
        if correlated:
            branch.setdefault("correlated_observations", []).append(_record(observation, independent_credit=False))
            continue
        if relation == "SUPPORTS":
            _attach(branch, "E_plus", observation, independent_credit=independent_credit)
            if branch.get("sigma") != "FALSIFIED":
                branch["sigma"] = "SUPPORTED_UNRESOLVED"
        elif relation == "COUNTERS":
            _attach(branch, "E_minus", observation, independent_credit=independent_credit)
            if branch.get("sigma") != "FALSIFIED":
                branch["sigma"] = "WEAKENED_UNRESOLVED"
        elif relation == "FALSIFIES":
            if branch.get("K") == "APPLIES":
                _attach(branch, "F", observation, independent_credit=independent_credit)
                branch["sigma"] = "FALSIFIED"
            else:
                _attach(branch, "pending_falsifiers", observation, independent_credit=independent_credit)

    payload = observation.get("new_branch_payload")
    if payload is not None:
        if not observation.get("branch_creation_warranted", False):
            raise ValueError("new branch payload requires explicit branch_creation_warranted")
        payload_id = payload.get("branch_id")
        if not isinstance(payload_id, str) or not payload_id:
            raise ValueError("new branch payload requires a non-empty string branch_id")
        if any(b.get("branch_id") == payload_id for b in branches):
            raise ValueError("new branch id already exists")
        branches.append(deepcopy(payload))
        _validate_branches(branches)
    out["branches"] = _merge_explicit_equivalents(branches, observation.get("equivalence_certificate"))
    return out


def d_resolve(state: Dict[str, Any]) -> Dict[str, Any]:
    branches = state.get("branches", [])
    if not isinstance(branches, list):
        raise ValueError("state.branches must be a list")
    _validate_branches(branches)
    if any(b.get("K") == "UNKNOWN" and b.get("sigma") != "FALSIFIED" for b in branches):
        return {"resolution": "UNRESOLVED", "selected_branch_id": None}
    applicable = [b for b in branches if b.get("K") == "APPLIES"]
    live = [b for b in applicable if b.get("sigma") != "FALSIFIED"]
    if len(live) != 1:
        return {"resolution": "UNRESOLVED", "selected_branch_id": None}
    selected = live[0]
    competitors = [b for b in applicable if b.get("branch_id") != selected.get("branch_id")]
    if any(b.get("sigma") != "FALSIFIED" for b in competitors):
        return {"resolution": "UNRESOLVED", "selected_branch_id": None}
    return {"resolution": "PASS", "selected_branch_id": selected["branch_id"]}


def apply_resolution(state: Dict[str, Any], resolution: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(state)
    if resolution.get("resolution") != "PASS":
        return out
    branches = out.get("branches", [])
    if not isinstance(branches, list):
        raise ValueError("state.branches must be a list")
    _validate_branches(branches)
    sid = resolution.get("selected_branch_id")
    matches = [b for b in branches if b.get("branch_id") == sid]
    if len(matches) != 1:
        raise ValueError("PASS resolution must select exactly one existing branch")
    matches[0]["sigma"] = "RESOLVED_PASS"
    return out


def _live_branch_ids(state: Dict[str, Any]) -> List[str]:
    branches = state.get("branches", [])
    if not isinstance(branches, list):
        raise ValueError("state.branches must be a list")
    _validate_branches(branches)
    return sorted(
        b["branch_id"] for b in branches
        if b.get("K") != "DOES_NOT_APPLY" and b.get("sigma") != "FALSIFIED"
    )


def _test_key(test: Dict[str, Any], branch_ids: List[str]) -> Tuple[Any, ...]:
    outcomes = test.get("outcomes", {})
    sep = 0
    for a, b in combinations(branch_ids, 2):
        oa, ob = outcomes.get(a, "UNKNOWN"), outcomes.get(b, "UNKNOWN")
        if oa != "UNKNOWN" and ob != "UNKNOWN" and oa != ob:
            sep += 1
    groups: Dict[str, int] = {}
    for bid in branch_ids:
        groups[outcomes.get(bid, "UNKNOWN")] = groups.get(outcomes.get(bid, "UNKNOWN"), 0) + 1
    worst = max(groups.values()) if groups else 0
    return (
        -sep,
        worst,
        int(test.get("risk_class", 0)),
        int(test.get("execution_cost_class", 0)),
        int(test.get("coordination_cost_class", 0)),
        str(test["test_id"]),
    )


def u_test_order(state: Dict[str, Any], tests: Iterable[Dict[str, Any]]) -> List[str]:
    branch_ids = _live_branch_ids(state)
    return [
        t["test_id"]
        for t in sorted((deepcopy(t) for t in tests), key=lambda t: _test_key(t, branch_ids))
    ]


def f_salience_order(items: Iterable[Dict[str, Any]]) -> List[str]:
    def key(x: Dict[str, Any]) -> Tuple[Any, ...]:
        return (
            -int(x.get("authority_boundary_risk", 0)),
            -int(x.get("expiry_or_time_urgency", 0)),
            -int(x.get("live_discriminator_relevance", 0)),
            -int(x.get("current_goal_relevance", 0)),
            -int(bool(x.get("novel_independent_evidence", 0))),
            str(x["item_id"]),
        )
    return [x["item_id"] for x in sorted((deepcopy(i) for i in items), key=key)]
