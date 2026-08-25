#!/usr/bin/env python3
"""Converged deterministic Trigger-2 Hyperposition/GRF reference labelers v3.

Fuses the two parallel v2 semantics required by the current Trigger-2 ledger:
- exact evidence-event replay is idempotent;
- correlation ancestry and (independence_group,payload_key) are distinct identities;
- distinct correlated/repackaged events are retained for provenance but get zero
  independent-evidence credit;
- the full v/K/E+/E-/F/T/A/sigma branch carrier is validated;
- branch birth and explicit-equivalence merge are supported under certificates;
- relation, resolution and discriminator-separation labels are mechanically derived;
- discriminator/salience ordering is ordinal, never probability or truth.

Pure synthetic/curriculum reference logic. It never mints canonical truth, real-effect
rights, J-Space/HCU/runtime credit, accepted dataset tokens, or training credit.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v3"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v3"
EVENT_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EVIDENCE_EVENT/v3"
TEST_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_DISCRIMINATOR/v3"

ALLOWED_K = {"APPLIES", "DOES_NOT_APPLY", "UNKNOWN"}
ALLOWED_SIGMA = {
    "LIVE_UNRESOLVED", "SUPPORTED_UNRESOLVED", "WEAKENED_UNRESOLVED",
    "FALSIFIED", "RESOLVED_PASS",
}
ALLOWED_VISIBILITY = {"VISIBLE", "FILTERED_CONTEXT"}
NONUPDATING_RELATIONS = {"IRRELEVANT", "UNKNOWN_RELATION"}
REQUIRED_BRANCH_FIELDS = {
    "branch_id", "v", "K", "E_plus", "E_minus", "F", "T", "A", "sigma",
    "projection_visibility",
}
REQUIRED_EVENT_FIELDS = {
    "evidence_event_id", "correlation_ancestry_id", "independence_group",
    "payload_key", "provenance", "observed_outcome", "independence_qualified",
    "discriminator",
}


class LabelerError(ValueError):
    pass


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _event_id(e: Dict[str, Any]) -> str:
    return str(e.get("evidence_event_id") or "")


def _ancestry(e: Dict[str, Any]) -> str:
    return str(e.get("correlation_ancestry_id") or "")


def _independence_key(e: Dict[str, Any]) -> Tuple[str, str]:
    return (str(e.get("independence_group") or ""), str(e.get("payload_key") or ""))


def _record(event: Dict[str, Any], relation: str, *, independent_credit: bool, branch_id: str | None = None) -> Dict[str, Any]:
    return {
        "evidence_event_id": _event_id(event),
        "correlation_ancestry_id": _ancestry(event),
        "independence_group": event["independence_group"],
        "payload_key": event["payload_key"],
        "provenance": deepcopy(event["provenance"]),
        "observed_outcome": deepcopy(event["observed_outcome"]),
        "relation": relation,
        "target_branch_id": branch_id,
        "independent_credit": bool(independent_credit),
    }


def _iter_records(state: Dict[str, Any]):
    for branch in state.get("branches", []):
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for e in branch.get(field, []) or []:
                if isinstance(e, dict):
                    yield e
    for field in ("correlated_observations", "nonupdating_observations"):
        for e in state.get(field, []) or []:
            if isinstance(e, dict):
                yield e


def validate_branch(branch: Any) -> None:
    if not isinstance(branch, dict):
        raise LabelerError("BRANCH_OBJECT_REQUIRED")
    missing = REQUIRED_BRANCH_FIELDS - set(branch)
    if missing:
        raise LabelerError("BRANCH_FULL_H_I_FIELDS_REQUIRED:" + ",".join(sorted(missing)))
    if not _nonempty(branch.get("branch_id")) or not _nonempty(branch.get("v")):
        raise LabelerError("BRANCH_ID_OR_V_REQUIRED")
    if branch.get("K") not in ALLOWED_K:
        raise LabelerError("BRANCH_K_INVALID")
    if branch.get("sigma") not in ALLOWED_SIGMA:
        raise LabelerError("BRANCH_SIGMA_INVALID")
    if branch.get("projection_visibility") not in ALLOWED_VISIBILITY:
        raise LabelerError("BRANCH_VISIBILITY_INVALID")
    if not isinstance(branch.get("E_plus"), list) or not isinstance(branch.get("E_minus"), list) or not isinstance(branch.get("F"), list):
        raise LabelerError("BRANCH_EVIDENCE_LISTS_REQUIRED")
    if branch.get("T") is None or branch.get("A") is None:
        raise LabelerError("BRANCH_T_AND_A_REQUIRED")


def validate_state(state: Any) -> None:
    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
        raise LabelerError("STATE_SCHEMA_MISMATCH")
    if state.get("canonical_truth_allowed") is not False:
        raise LabelerError("STATE_CANONICAL_TRUTH_MUST_BE_FALSE")
    if state.get("direct_effect_authority") is not False:
        raise LabelerError("STATE_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if not _nonempty(state.get("query_id")):
        raise LabelerError("STATE_QUERY_ID_REQUIRED")
    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        raise LabelerError("STATE_REQUIRES_AT_LEAST_TWO_BRANCHES")
    seen = set()
    for branch in branches:
        validate_branch(branch)
        bid = branch["branch_id"]
        if bid in seen:
            raise LabelerError("DUPLICATE_BRANCH_ID")
        seen.add(bid)


def validate_test(test: Any, state: Dict[str, Any]) -> None:
    if not isinstance(test, dict) or test.get("schema") != TEST_SCHEMA:
        raise LabelerError("TEST_SCHEMA_MISMATCH")
    if not _nonempty(test.get("test_id")):
        raise LabelerError("TEST_ID_REQUIRED")
    outcomes = test.get("outcomes")
    if not isinstance(outcomes, dict):
        raise LabelerError("TEST_OUTCOMES_REQUIRED")
    branch_ids = {b["branch_id"] for b in state["branches"]}
    unknown = set(outcomes) - branch_ids
    if unknown:
        raise LabelerError("TEST_OUTCOME_UNKNOWN_BRANCH:" + ",".join(sorted(unknown)))
    for field in ("risk_class", "execution_cost_class", "coordination_cost_class"):
        if not isinstance(test.get(field, 0), int) or int(test.get(field, 0)) < 0:
            raise LabelerError("TEST_ORDINAL_COST_INVALID:" + field)


def validate_event(event: Any, state: Dict[str, Any]) -> None:
    if not isinstance(event, dict) or event.get("schema") != EVENT_SCHEMA:
        raise LabelerError("EVENT_SCHEMA_MISMATCH")
    if event.get("canonical_truth_allowed") is not False:
        raise LabelerError("EVENT_CANONICAL_TRUTH_MUST_BE_FALSE")
    if event.get("direct_effect_authority") is not False:
        raise LabelerError("EVENT_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    missing = REQUIRED_EVENT_FIELDS - set(event)
    if missing:
        raise LabelerError("EVENT_FIELDS_MISSING:" + ",".join(sorted(missing)))
    if not all(_nonempty(event.get(k)) for k in ("evidence_event_id", "correlation_ancestry_id", "independence_group", "payload_key")):
        raise LabelerError("EVENT_IDENTITY_FIELDS_INVALID")
    if not isinstance(event.get("independence_qualified"), bool):
        raise LabelerError("EVENT_INDEPENDENCE_QUALIFIED_BOOL_REQUIRED")
    test = event.get("discriminator")
    validate_test(test, state)
    if test.get("test_id") != event.get("discriminator_id", test.get("test_id")):
        raise LabelerError("EVENT_DISCRIMINATOR_ID_MISMATCH")


def derive_relations(state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, str]:
    """Derive branch relations from test outcomes + observed outcome; no caller labels."""
    validate_state(state)
    validate_event(event, state)
    outcomes = event["discriminator"]["outcomes"]
    observed = event["observed_outcome"]
    relations: Dict[str, str] = {}
    for branch in state["branches"]:
        bid = branch["branch_id"]
        if branch["K"] == "DOES_NOT_APPLY":
            relations[bid] = "IRRELEVANT"
            continue
        expected = outcomes.get(bid, "UNKNOWN")
        if observed in (None, "UNKNOWN", "UNOBSERVED") or expected in (None, "UNKNOWN", "UNOBSERVABLE"):
            relations[bid] = "UNKNOWN_RELATION"
        elif expected == observed:
            relations[bid] = "SUPPORTS"
        else:
            relations[bid] = "FALSIFIES"
    return relations


def _identity_status(state: Dict[str, Any], event: Dict[str, Any]) -> str:
    eid = _event_id(event)
    ancestry = _ancestry(event)
    ikey = _independence_key(event)
    records = list(_iter_records(state))
    if any(_event_id(r) == eid for r in records):
        return "EXACT_EVENT_REPLAY"
    if any(_ancestry(r) == ancestry for r in records):
        return "CORRELATED_ANCESTRY_EVENT"
    if any(_independence_key(r) == ikey for r in records):
        return "REPACKAGED_PAYLOAD_EVENT"
    if not event["independence_qualified"]:
        return "NOVEL_BUT_NOT_INDEPENDENCE_QUALIFIED"
    return "NOVEL_INDEPENDENT_EVENT"


def _merge_explicit_equivalents(branches: List[Dict[str, Any]], cert: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    if cert is None:
        return branches
    if not isinstance(cert, dict) or cert.get("equivalent") is not True or not _nonempty(cert.get("certificate_id")):
        raise LabelerError("EQUIVALENCE_CERTIFICATE_INVALID")
    ids = sorted(set(cert.get("branch_ids") or []))
    if len(ids) < 2:
        raise LabelerError("EQUIVALENCE_REQUIRES_AT_LEAST_TWO_BRANCHES")
    by_id = {b["branch_id"]: b for b in branches}
    if any(i not in by_id for i in ids):
        raise LabelerError("EQUIVALENCE_UNKNOWN_BRANCH")
    group = [by_id[i] for i in ids]
    if any(b["sigma"] == "RESOLVED_PASS" for b in group):
        raise LabelerError("RESOLVED_BRANCH_MERGE_FORBIDDEN")
    pivot = deepcopy(group[0])
    for b in group[1:]:
        if b["v"] != pivot["v"] or b["K"] != pivot["K"] or b["T"] != pivot["T"]:
            raise LabelerError("EQUIVALENCE_CONFLICTS_WITH_V_K_T")
    pivot["branch_id"] = cert.get("merge_to_branch_id") or ids[0]
    pivot["merged_from_branch_ids"] = ids
    for field in ("E_plus", "E_minus", "F", "correlated_observations"):
        seen, values = set(), []
        for b in group:
            for e in b.get(field, []) or []:
                eid = _event_id(e)
                if eid and eid not in seen:
                    seen.add(eid)
                    values.append(deepcopy(e))
        pivot[field] = values
    sigmas = {b["sigma"] for b in group}
    if "FALSIFIED" in sigmas:
        pivot["sigma"] = "FALSIFIED"
    elif "WEAKENED_UNRESOLVED" in sigmas:
        pivot["sigma"] = "WEAKENED_UNRESOLVED"
    elif "SUPPORTED_UNRESOLVED" in sigmas:
        pivot["sigma"] = "SUPPORTED_UNRESOLVED"
    else:
        pivot["sigma"] = "LIVE_UNRESOLVED"
    pivot["A"] = {
        "merge_certificate_id": cert["certificate_id"],
        "merged_origins": [deepcopy(b["A"]) for b in group],
    }
    keep = [deepcopy(b) for b in branches if b["branch_id"] not in ids]
    keep.append(pivot)
    if len(keep) < 2:
        raise LabelerError("MERGE_CANNOT_COLLAPSE_HYPERPOSITION_TO_SINGLE_BRANCH")
    return keep


def _apply_branch_birth(branches: List[Dict[str, Any]], event: Dict[str, Any]) -> List[Dict[str, Any]]:
    payload = event.get("new_branch_payload")
    if payload is None:
        return branches
    cert = event.get("branch_birth_certificate")
    if not isinstance(cert, dict) or not _nonempty(cert.get("certificate_id")):
        raise LabelerError("BRANCH_BIRTH_CERTIFICATE_REQUIRED")
    if cert.get("basis_event_id") != event["evidence_event_id"]:
        raise LabelerError("BRANCH_BIRTH_BASIS_EVENT_MISMATCH")
    if cert.get("observed_outcome") != event["observed_outcome"]:
        raise LabelerError("BRANCH_BIRTH_OUTCOME_MISMATCH")
    validate_branch(payload)
    if any(b["branch_id"] == payload["branch_id"] for b in branches):
        raise LabelerError("BRANCH_BIRTH_DUPLICATE_ID")
    out = [deepcopy(b) for b in branches]
    newborn = deepcopy(payload)
    newborn["A"] = {
        "birth_certificate_id": cert["certificate_id"],
        "basis_event_id": event["evidence_event_id"],
        "declared_origin": deepcopy(payload["A"]),
    }
    out.append(newborn)
    return out


def u_state(state: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic update with event/ancestry/payload identity separated."""
    validate_state(state)
    validate_event(event, state)
    relations = derive_relations(state, event)
    identity_status = _identity_status(state, event)
    if identity_status == "EXACT_EVENT_REPLAY":
        return {
            "schema": SCHEMA,
            "state_after": deepcopy(state),
            "derived_relations": relations,
            "identity_status": identity_status,
            "independent_evidence_credit": False,
            "state_changed": False,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
            "training_credit_minted": False,
        }

    independent = identity_status == "NOVEL_INDEPENDENT_EVENT"
    structural_requested = event.get("new_branch_payload") is not None or event.get("equivalence_certificate") is not None
    if structural_requested and not independent:
        raise LabelerError("NONINDEPENDENT_EVENT_CANNOT_MUTATE_BRANCH_TOPOLOGY")

    out = deepcopy(state)
    if not independent:
        out.setdefault("correlated_observations", []).append(
            _record(event, "CORRELATED_OR_NONINDEPENDENT", independent_credit=False)
        )
    else:
        by_id = {b["branch_id"]: b for b in out["branches"]}
        for bid, relation in relations.items():
            branch = by_id[bid]
            record = _record(event, relation, independent_credit=True, branch_id=bid)
            if relation == "SUPPORTS":
                branch["E_plus"].append(record)
                if branch["sigma"] not in {"FALSIFIED", "RESOLVED_PASS"}:
                    branch["sigma"] = "SUPPORTED_UNRESOLVED"
            elif relation == "FALSIFIES":
                branch["F"].append(record)
                if branch["K"] == "APPLIES":
                    branch["sigma"] = "FALSIFIED"
            elif relation in NONUPDATING_RELATIONS:
                out.setdefault("nonupdating_observations", []).append(record)
        out["branches"] = [by_id[b["branch_id"]] for b in state["branches"]]

    out["branches"] = _apply_branch_birth(out["branches"], event)
    out["branches"] = _merge_explicit_equivalents(out["branches"], event.get("equivalence_certificate"))
    validate_state(out)
    return {
        "schema": SCHEMA,
        "state_after": out,
        "derived_relations": relations,
        "identity_status": identity_status,
        "independent_evidence_credit": independent,
        "state_changed": out != state,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "training_credit_minted": False,
    }


def d_resolve(state: Dict[str, Any]) -> Dict[str, Any]:
    """Mechanically derive resolution from K/sigma only; no caller decision label."""
    validate_state(state)
    branches = state["branches"]
    if any(b["K"] == "UNKNOWN" and b["sigma"] != "FALSIFIED" for b in branches):
        return {"resolution": "UNRESOLVED", "selected_branch_id": None, "basis": "LIVE_UNKNOWN_CONTEXT_BRANCH"}
    applicable = [b for b in branches if b["K"] == "APPLIES"]
    live = [b for b in applicable if b["sigma"] != "FALSIFIED"]
    if len(live) != 1:
        return {"resolution": "UNRESOLVED", "selected_branch_id": None, "basis": "NOT_EXACTLY_ONE_LIVE_APPLICABLE_BRANCH"}
    selected = live[0]
    competitors = [b for b in applicable if b["branch_id"] != selected["branch_id"]]
    if any(b["sigma"] != "FALSIFIED" for b in competitors):
        return {"resolution": "UNRESOLVED", "selected_branch_id": None, "basis": "LIVE_COMPETITOR_REMAINS"}
    return {"resolution": "PASS", "selected_branch_id": selected["branch_id"], "basis": "ALL_APPLICABLE_COMPETITORS_FALSIFIED"}


def apply_resolution(state: Dict[str, Any], resolution: Dict[str, Any] | None = None) -> Dict[str, Any]:
    validate_state(state)
    derived = d_resolve(state)
    if resolution is not None and resolution != derived:
        raise LabelerError("CALLER_ASSERTED_RESOLUTION_DOES_NOT_MATCH_DERIVATION")
    out = deepcopy(state)
    if derived["resolution"] == "PASS":
        for branch in out["branches"]:
            if branch["branch_id"] == derived["selected_branch_id"]:
                branch["sigma"] = "RESOLVED_PASS"
    return out


def _live_branch_ids(state: Dict[str, Any]) -> List[str]:
    validate_state(state)
    return sorted(
        b["branch_id"] for b in state["branches"]
        if b["K"] != "DOES_NOT_APPLY" and b["sigma"] != "FALSIFIED"
    )


def derive_test_separation(state: Dict[str, Any], test: Dict[str, Any]) -> Dict[str, Any]:
    """Derive pair separation from declared counterfactual outcomes, not caller pairs."""
    validate_state(state)
    validate_test(test, state)
    live = _live_branch_ids(state)
    outcomes = test["outcomes"]
    pairs = []
    for a, b in combinations(live, 2):
        oa, ob = outcomes.get(a, "UNKNOWN"), outcomes.get(b, "UNKNOWN")
        if oa not in (None, "UNKNOWN", "UNOBSERVABLE") and ob not in (None, "UNKNOWN", "UNOBSERVABLE") and oa != ob:
            pairs.append([a, b])
    partitions: Dict[str, int] = {}
    for bid in live:
        key = str(outcomes.get(bid, "UNKNOWN"))
        partitions[key] = partitions.get(key, 0) + 1
    return {
        "test_id": test["test_id"],
        "live_branch_ids": live,
        "separates_pairs": pairs,
        "separated_pair_count": len(pairs),
        "worst_partition_size": max(partitions.values()) if partitions else 0,
    }


def u_test_order(state: Dict[str, Any], tests: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordinal discriminator ordering; no probability, IG scalar, or truth output."""
    rows = []
    for test in tests:
        derived = derive_test_separation(state, test)
        rows.append({
            **derived,
            "risk_class": int(test.get("risk_class", 0)),
            "execution_cost_class": int(test.get("execution_cost_class", 0)),
            "coordination_cost_class": int(test.get("coordination_cost_class", 0)),
        })
    rows.sort(key=lambda r: (
        -r["separated_pair_count"], r["worst_partition_size"], r["risk_class"],
        r["execution_cost_class"], r["coordination_cost_class"], r["test_id"],
    ))
    for i, row in enumerate(rows, 1):
        row["ordinal_rank"] = i
        row["probability_output"] = False
        row["truth_output"] = False
    return rows


def f_salience_order(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attention ordering only; explicitly distinct from truth/evidence probability."""
    rows = []
    for item in items:
        if not isinstance(item, dict) or not _nonempty(item.get("item_id")):
            raise LabelerError("SALIENCE_ITEM_INVALID")
        for field in ("authority_boundary_risk", "expiry_or_time_urgency", "live_discriminator_relevance", "current_goal_relevance"):
            if not isinstance(item.get(field, 0), int) or int(item.get(field, 0)) < 0:
                raise LabelerError("SALIENCE_ORDINAL_FIELD_INVALID:" + field)
        rows.append(deepcopy(item))
    rows.sort(key=lambda x: (
        -int(x.get("authority_boundary_risk", 0)),
        -int(x.get("expiry_or_time_urgency", 0)),
        -int(x.get("live_discriminator_relevance", 0)),
        -int(x.get("current_goal_relevance", 0)),
        -int(bool(x.get("novel_independent_evidence", False))),
        str(x["item_id"]),
    ))
    out = []
    for i, row in enumerate(rows, 1):
        out.append({
            "item_id": row["item_id"],
            "ordinal_rank": i,
            "probability_output": False,
            "truth_output": False,
            "evidence_strength_output": False,
        })
    return out


def canonical_semantics(state: Dict[str, Any]) -> Dict[str, Any]:
    """Order-insensitive projection used by branch-permutation regression tests."""
    validate_state(state)
    out = deepcopy(state)
    out["branches"] = sorted(out["branches"], key=lambda b: b["branch_id"])
    for field in ("correlated_observations", "nonupdating_observations"):
        if field in out:
            out[field] = sorted(out[field], key=lambda e: (_event_id(e), str(e.get("target_branch_id") or "")))
    return out
