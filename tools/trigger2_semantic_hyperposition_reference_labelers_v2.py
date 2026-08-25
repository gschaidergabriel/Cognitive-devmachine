#!/usr/bin/env python3
"""Derivation-bound Trigger-2 Hyperposition reference labelers v2.

This successor deliberately supports a *narrow* executable synthetic task world rather
than pretending to solve arbitrary semantics. Branch hypotheses contain a deterministic
attribute world. Discriminators are ATTRIBUTE_READ operations. The labeler derives each
branch prediction by executing that task-world relation, then derives SUPPORT/FALSIFY,
resolution and discriminator coverage from the observed result.

Scope: synthetic curriculum labels only. No canonical truth, effect, runtime, model or
training credit is implied.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any, Dict, List, Mapping, Sequence, Tuple

SCHEMA = "TRIGGER2_SEMANTIC_HYPERPOSITION_REFERENCE_LABELERS/v2"
DERIVATION_DOMAIN = "SYNTHETIC_ATTRIBUTE_WORLD/v1"
REQUIRED_BRANCH_FIELDS = (
    "branch_id", "v_semantic_value", "K_context_predicate", "E_plus", "E_minus",
    "F_falsifier", "T_validity_scope", "A_origin_provenance",
    "sigma_epistemic_status", "task_world",
)
LIVE_STATUSES = {"HYPOTHESIS", "OBSERVED", "SUPPORTED", "UNKNOWN"}
TERMINAL_REJECT = {"FALSIFIED"}


class LabelerError(ValueError):
    """Fail-closed malformed or ambiguous synthetic-oracle input."""


def _nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise LabelerError(f"{name} must be a non-empty string")
    return value


def _require_branch(branch: Mapping[str, Any]) -> None:
    missing = [k for k in REQUIRED_BRANCH_FIELDS if k not in branch]
    if missing:
        raise LabelerError(f"missing branch fields: {missing}")
    _nonempty(branch["branch_id"], "branch_id")
    if not isinstance(branch["E_plus"], list) or not isinstance(branch["E_minus"], list):
        raise LabelerError("E_plus/E_minus must be lists")
    world = branch["task_world"]
    if not isinstance(world, Mapping) or world.get("schema") != DERIVATION_DOMAIN:
        raise LabelerError(f"task_world.schema must be {DERIVATION_DOMAIN}")
    attrs = world.get("attributes")
    if not isinstance(attrs, Mapping) or not attrs:
        raise LabelerError("task_world.attributes must be a non-empty mapping")
    for key, value in attrs.items():
        _nonempty(key, "task-world attribute")
        if isinstance(value, (dict, list, set, tuple)) or value is None:
            raise LabelerError("attribute outcomes must be scalar and non-null")


def _branch_ids(branch_set: Sequence[Mapping[str, Any]]) -> List[str]:
    ids: List[str] = []
    for branch in branch_set:
        _require_branch(branch)
        ids.append(branch["branch_id"])
    if len(ids) < 2:
        raise LabelerError("Hyperposition reference cases require >=2 branches")
    if len(ids) != len(set(ids)):
        raise LabelerError("duplicate branch_id")
    return ids


def _require_discriminator(discriminator: Mapping[str, Any]) -> Tuple[str, str]:
    if not isinstance(discriminator, Mapping):
        raise LabelerError("discriminator must be a mapping")
    did = _nonempty(discriminator.get("discriminator_id"), "discriminator_id")
    if discriminator.get("kind") != "ATTRIBUTE_READ":
        raise LabelerError("only ATTRIBUTE_READ discriminators are admitted by v2")
    attribute = _nonempty(discriminator.get("attribute"), "discriminator.attribute")
    forbidden = set(discriminator) - {"discriminator_id", "kind", "attribute"}
    if forbidden:
        raise LabelerError(f"unrecognized discriminator fields: {sorted(forbidden)}")
    return did, attribute


def derive_prediction(branch: Mapping[str, Any], discriminator: Mapping[str, Any]) -> Any:
    """Execute the synthetic task-world relation for one branch."""
    _require_branch(branch)
    _, attribute = _require_discriminator(discriminator)
    attrs = branch["task_world"]["attributes"]
    if attribute not in attrs:
        raise LabelerError(
            f"inadmissible discriminator: attribute {attribute!r} missing from branch {branch['branch_id']}"
        )
    return attrs[attribute]


def discriminator_predictions(
    branch_set: Sequence[Mapping[str, Any]], discriminator: Mapping[str, Any]
) -> Dict[str, Any]:
    _branch_ids(branch_set)
    return {b["branch_id"]: derive_prediction(b, discriminator) for b in branch_set}


def derive_relation(branch: Mapping[str, Any], observation: Mapping[str, Any]) -> str:
    if not isinstance(observation, Mapping):
        raise LabelerError("observation must be a mapping")
    discriminator = observation.get("discriminator")
    observed = observation.get("observed_outcome")
    if observed is None or isinstance(observed, (dict, list, set, tuple)):
        raise LabelerError("observed_outcome must be a non-null scalar")
    expected = derive_prediction(branch, discriminator)
    return "SUPPORT" if expected == observed else "FALSIFY"


def _identity_fields(observation: Mapping[str, Any]) -> Dict[str, Any]:
    did, attribute = _require_discriminator(observation.get("discriminator"))
    return {
        "evidence_id": _nonempty(observation.get("evidence_id"), "evidence_id"),
        "discriminator_id": did,
        "discriminator_kind": "ATTRIBUTE_READ",
        "attribute": attribute,
        "observed_outcome": observation.get("observed_outcome"),
        "independence_group": _nonempty(observation.get("independence_group"), "independence_group"),
        "provenance": _nonempty(observation.get("provenance"), "provenance"),
    }


def _all_evidence(branch_set: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    return [item for b in branch_set for item in list(b["E_plus"]) + list(b["E_minus"])]


def _same_identity(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    keys = (
        "evidence_id", "discriminator_id", "discriminator_kind", "attribute",
        "observed_outcome", "independence_group", "provenance",
    )
    return all(a.get(k) == b.get(k) for k in keys)


def U_update(
    branch_set: Sequence[Mapping[str, Any]], observation: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    """Apply one executable synthetic observation without deleting branches.

    - No caller-supplied effect label exists.
    - same evidence_id with changed identity fails closed;
    - a reused independence_group is idempotent only for the exact same observation;
      otherwise it fails closed instead of double-counting correlated evidence.
    """
    _branch_ids(branch_set)
    identity = _identity_fields(observation)
    # Force discriminator admissibility across *every* current branch before update.
    discriminator_predictions(branch_set, observation["discriminator"])

    prior_all = _all_evidence(branch_set)
    same_id = [x for x in prior_all if x.get("evidence_id") == identity["evidence_id"]]
    if same_id and not all(_same_identity(x, identity) for x in same_id):
        raise LabelerError("evidence_id replay identity conflict")
    same_group = [x for x in prior_all if x.get("independence_group") == identity["independence_group"]]
    if same_group and not all(_same_identity(x, identity) for x in same_group):
        raise LabelerError("independence_group reused for a different observation")

    out = deepcopy(list(branch_set))
    for branch in out:
        relation = derive_relation(branch, observation)
        record = dict(identity, relation=relation, derivation_domain=DERIVATION_DOMAIN)
        existing = [x for x in list(branch["E_plus"]) + list(branch["E_minus"])
                    if x.get("evidence_id") == identity["evidence_id"]]
        if existing:
            expected_same = all(dict(x) == record for x in existing)
            if not expected_same:
                raise LabelerError("branch-local evidence replay conflict")
            continue
        if relation == "SUPPORT":
            branch["E_plus"].append(record)
            if branch.get("sigma_epistemic_status") in {"HYPOTHESIS", "UNKNOWN"}:
                branch["sigma_epistemic_status"] = "SUPPORTED"
        else:
            branch["E_minus"].append(record)
            branch["sigma_epistemic_status"] = "FALSIFIED"
            branch["falsified_by"] = identity["evidence_id"]
    return out


def live_branch_ids(branch_set: Sequence[Mapping[str, Any]]) -> List[str]:
    _branch_ids(branch_set)
    live: List[str] = []
    for branch in branch_set:
        status = branch.get("sigma_epistemic_status")
        if status in TERMINAL_REJECT:
            continue
        if status not in LIVE_STATUSES:
            raise LabelerError(f"unsupported sigma_epistemic_status: {status!r}")
        live.append(branch["branch_id"])
    return live


def D_resolve(branch_set: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Resolve iff prior *derived* updates leave exactly one live branch."""
    live = live_branch_ids(branch_set)
    if len(live) == 1:
        return {
            "resolution_status": "RESOLVED_BY_DERIVED_DISCRIMINATOR",
            "resolved_branch_id": live[0],
            "reason": "ALL_OTHER_BRANCHES_FALSIFIED_BY_EXECUTED_TASK_WORLD_RELATION",
        }
    if not live:
        return {
            "resolution_status": "UNRESOLVED_CONTRADICTION",
            "resolved_branch_id": None,
            "reason": "ALL_BRANCHES_FALSIFIED",
        }
    return {
        "resolution_status": "UNRESOLVED",
        "resolved_branch_id": None,
        "reason": "MULTIPLE_LIVE_BRANCHES",
    }


def discriminator_pair_coverage(
    branch_set: Sequence[Mapping[str, Any]], discriminator: Mapping[str, Any]
) -> int:
    """Derive live-pair separation by executing the discriminator on each branch."""
    live = set(live_branch_ids(branch_set))
    predictions = discriminator_predictions(branch_set, discriminator)
    ids = [b["branch_id"] for b in branch_set if b["branch_id"] in live]
    return sum(1 for a, b in combinations(ids, 2) if predictions[a] != predictions[b])


def U_d_test_order(
    branch_set: Sequence[Mapping[str, Any]], candidates: Sequence[Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """Ordinal ranking: derived coverage, independent group, cost, stable id.

    Candidate objects contain an executable discriminator; callers cannot assert pair coverage.
    """
    _branch_ids(branch_set)
    ranked: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []
    seen = set()
    for candidate in candidates:
        cid = _nonempty(candidate.get("candidate_id"), "candidate_id")
        if cid in seen:
            raise LabelerError("duplicate candidate_id")
        seen.add(cid)
        discriminator = candidate.get("discriminator")
        did, _ = _require_discriminator(discriminator)
        cost = candidate.get("cost", 0.0)
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
            raise LabelerError("candidate cost must be nonnegative numeric")
        independent = bool(candidate.get("independent_of_existing", False))
        coverage = discriminator_pair_coverage(branch_set, discriminator)
        key = (-coverage, -int(independent), float(cost), cid)
        ranked.append((key, {
            "candidate_id": cid,
            "discriminator_id": did,
            "live_pair_coverage": coverage,
            "independent_of_existing": independent,
            "cost": float(cost),
            "ordering_only": True,
            "coverage_derived": True,
        }))
    ranked.sort(key=lambda x: x[0])
    return [dict(row, rank=i + 1) for i, (_, row) in enumerate(ranked)]


def f_salience_rank(branch_set: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Attention ordering only. Salience can never emit truth/probability/resolution."""
    _branch_ids(branch_set)
    rows: List[Tuple[Tuple[float, str], Dict[str, Any]]] = []
    for branch in branch_set:
        salience = branch.get("salience", 0.0)
        if not isinstance(salience, (int, float)) or isinstance(salience, bool):
            raise LabelerError("salience must be numeric")
        rows.append(((-float(salience), branch["branch_id"]), {
            "branch_id": branch["branch_id"],
            "salience": float(salience),
            "attention_ordering_only": True,
            "truth_semantics": "NONE",
        }))
    rows.sort(key=lambda x: x[0])
    return [dict(row, rank=i + 1) for i, (_, row) in enumerate(rows)]


__all__ = [
    "SCHEMA", "DERIVATION_DOMAIN", "LabelerError", "derive_prediction",
    "discriminator_predictions", "derive_relation", "U_update", "D_resolve",
    "live_branch_ids", "discriminator_pair_coverage", "U_d_test_order", "f_salience_rank",
]
