#!/usr/bin/env python3
from __future__ import annotations
from copy import deepcopy
from itertools import combinations
from typing import Any, Dict, Iterable, List, Tuple

LIVE_SIGMA = {
    "LIVE_UNRESOLVED",
    "SUPPORTED_UNRESOLVED",
    "WEAKENED_UNRESOLVED",
    "RESOLVED_PASS",
}


def _ev_key(e: Dict[str, Any]) -> Tuple[str, str]:
    return str(e.get("evidence_id", "")), str(e.get("causal_ancestry_id", ""))


def _already_seen(branch: Dict[str, Any], obs: Dict[str, Any]) -> bool:
    oid, oanc = _ev_key(obs)
    for field in ("E_plus", "E_minus", "F", "pending_falsifiers"):
        for e in branch.get(field, []) or []:
            eid, eanc = _ev_key(e)
            if oid and eid == oid:
                return True
            if oanc and eanc == oanc:
                return True
    return False


def _attach(branch: Dict[str, Any], field: str, obs: Dict[str, Any]) -> None:
    branch.setdefault(field, []).append({
        "evidence_id": obs["evidence_id"],
        "causal_ancestry_id": obs["causal_ancestry_id"],
        "independence_group": obs["independence_group"],
        "provenance": obs["provenance"],
        "relation": obs["relation"],
    })


def _merge_explicit_equivalents(branches: List[Dict[str, Any]], cert: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    pivot["branch_id"] = merged_id
    pivot["merged_from_branch_ids"] = ids
    for field in ("E_plus", "E_minus", "F", "pending_falsifiers"):
        seen = set()
        out = []
        for b in group:
            for e in b.get(field, []) or []:
                key = _ev_key(e)
                if key not in seen:
                    seen.add(key)
                    out.append(deepcopy(e))
        if out:
            pivot[field] = out
    if any(b.get("sigma") == "FALSIFIED" for b in group):
        pivot["sigma"] = "FALSIFIED"
    elif any(b.get("sigma") == "WEAKENED_UNRESOLVED" for b in group):
        pivot["sigma"] = "WEAKENED_UNRESOLVED"
    elif any(b.get("sigma") == "SUPPORTED_UNRESOLVED" for b in group):
        pivot["sigma"] = "SUPPORTED_UNRESOLVED"
    else:
        pivot["sigma"] = "LIVE_UNRESOLVED"
    pivot["A"] = {
        "merge_certificate": cert.get("certificate_id", "EXPLICIT_EQUIVALENCE"),
        "merged_origins": [deepcopy(b.get("A")) for b in group],
    }
    keep = [b for b in branches if b["branch_id"] not in ids]
    keep.append(pivot)
    return keep


def u_state(state: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic training-reference transition. Does not infer evidence truth from text."""
    out = deepcopy(state)
    branches = out.setdefault("branches", [])
    relation = observation["relation"]
    targets = set(observation.get("target_branch_ids") or [])
    for branch in branches:
        if branch.get("branch_id") not in targets:
            continue
        if branch.get("K") == "DOES_NOT_APPLY":
            branch["projection_visibility"] = "FILTERED_CONTEXT"
        if relation in {"IRRELEVANT", "UNKNOWN_RELATION"}:
            continue
        if _already_seen(branch, observation):
            continue
        if relation == "SUPPORTS":
            _attach(branch, "E_plus", observation)
            if branch.get("sigma") != "FALSIFIED":
                branch["sigma"] = "SUPPORTED_UNRESOLVED"
        elif relation == "COUNTERS":
            _attach(branch, "E_minus", observation)
            if branch.get("sigma") != "FALSIFIED":
                branch["sigma"] = "WEAKENED_UNRESOLVED"
        elif relation == "FALSIFIES":
            if branch.get("K") == "APPLIES":
                _attach(branch, "F", observation)
                branch["sigma"] = "FALSIFIED"
            else:
                _attach(branch, "pending_falsifiers", observation)
        else:
            raise ValueError(f"unknown relation: {relation}")

    payload = observation.get("new_branch_payload")
    if payload is not None:
        if not observation.get("branch_creation_warranted", False):
            raise ValueError("new branch payload requires explicit branch_creation_warranted")
        if any(b.get("branch_id") == payload.get("branch_id") for b in branches):
            raise ValueError("new branch id already exists")
        branches.append(deepcopy(payload))

    out["branches"] = _merge_explicit_equivalents(
        branches, observation.get("equivalence_certificate")
    )
    return out


def d_resolve(state: Dict[str, Any]) -> Dict[str, Any]:
    branches = state.get("branches", [])
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
    sid = resolution["selected_branch_id"]
    for b in out.get("branches", []):
        if b.get("branch_id") == sid:
            b["sigma"] = "RESOLVED_PASS"
    return out


def _live_branch_ids(state: Dict[str, Any]) -> List[str]:
    return sorted(
        b["branch_id"]
        for b in state.get("branches", [])
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
