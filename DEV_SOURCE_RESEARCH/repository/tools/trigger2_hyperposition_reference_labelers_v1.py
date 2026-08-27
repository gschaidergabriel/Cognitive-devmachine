#!/usr/bin/env python3
"""Deterministic Trigger-2 semantic-Hyperposition reference labelers v1.

These functions generate *reference targets* from latent synthetic/task-local state.
They do not infer canonical world truth and are not model/runtime evidence.

Design goals:
- deterministic U update labels;
- deterministic resolve/unresolved labels;
- deterministic pairwise discriminator ordering;
- deterministic salience ordering that cannot be interpreted as truth/probability;
- ancestry-aware evidence deduplication;
- projection is never deletion;
- explicit, fail-closed schemas.
"""
from __future__ import annotations

import copy
import itertools
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v1"
BRANCH_SCHEMA = "XENO_HYPERPOSITION_BRANCH/v1"
OBS_SCHEMA = "XENO_HYPERPOSITION_OBSERVATION/v1"
TEST_SCHEMA = "XENO_HYPERPOSITION_DISCRIMINATOR/v1"

RELATIONS = {"SUPPORT", "COUNTER", "FALSIFY", "NO_EFFECT"}
EPISTEMIC = {"OBSERVED", "HYPOTHESIS", "COUNTERHYPOTHESIS", "UNKNOWN", "PREDICTION"}
VALIDITY = {"LIVE", "FALSIFIED", "OUT_OF_SCOPE"}
DECISION_ROLES = {"NONDECISIVE", "DECISIVE_SUPPORT", "DECISIVE_CONTRADICTION"}


class LabelerError(ValueError):
    pass


def _required(d: dict[str, Any], keys: Iterable[str], where: str) -> None:
    missing = [k for k in keys if k not in d]
    if missing:
        raise LabelerError(f"{where}: missing {missing}")


def _validate_branch(branch: dict[str, Any]) -> None:
    _required(
        branch,
        [
            "branch_id",
            "v_semantic_value",
            "K_context_predicate",
            "E_plus",
            "E_minus",
            "F_falsifier",
            "T_validity_scope",
            "A_origin_provenance",
            "sigma_epistemic_status",
            "projection_visibility",
            "validity",
        ],
        "branch",
    )
    if branch["sigma_epistemic_status"] not in EPISTEMIC:
        raise LabelerError("branch: invalid sigma_epistemic_status")
    if branch["validity"] not in VALIDITY:
        raise LabelerError("branch: invalid validity")
    if not isinstance(branch["E_plus"], list) or not isinstance(branch["E_minus"], list):
        raise LabelerError("branch: E_plus/E_minus must be lists")


def validate_branch_set(branches: list[dict[str, Any]]) -> None:
    if len(branches) < 2:
        raise LabelerError("branch_set: at least two branches required")
    ids: set[str] = set()
    for b in branches:
        _validate_branch(b)
        bid = b["branch_id"]
        if bid in ids:
            raise LabelerError(f"branch_set: duplicate branch_id {bid}")
        ids.add(bid)


def _validate_evidence_item(item: dict[str, Any]) -> None:
    _required(
        item,
        ["evidence_id", "provenance_ancestry_id", "independence_group", "decision_role"],
        "evidence_item",
    )
    if item["decision_role"] not in DECISION_ROLES:
        raise LabelerError("evidence_item: invalid decision_role")


def _evidence_identity(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(item["evidence_id"]),
        str(item["provenance_ancestry_id"]),
        str(item["independence_group"]),
    )


def _append_unique_evidence(dst: list[dict[str, Any]], item: dict[str, Any]) -> None:
    _validate_evidence_item(item)
    identity = _evidence_identity(item)
    if identity not in {_evidence_identity(x) for x in dst}:
        dst.append(copy.deepcopy(item))


def U_update(branch_set: list[dict[str, Any]], observation: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministically update branch-local evidence/validity.

    `observation.branch_relations` is latent generator metadata and MUST NOT be rendered
    into model-visible training input. It maps every branch id to SUPPORT, COUNTER,
    FALSIFY or NO_EFFECT.
    """
    validate_branch_set(branch_set)
    _required(observation, ["schema", "evidence", "branch_relations"], "observation")
    if observation["schema"] != OBS_SCHEMA:
        raise LabelerError("observation: wrong schema")
    evidence = observation["evidence"]
    _validate_evidence_item(evidence)
    relations = observation["branch_relations"]
    branch_ids = {b["branch_id"] for b in branch_set}
    if set(relations) != branch_ids:
        raise LabelerError("observation: branch_relations must cover exactly the branch set")
    if any(r not in RELATIONS for r in relations.values()):
        raise LabelerError("observation: invalid branch relation")

    out = copy.deepcopy(branch_set)
    for branch in out:
        relation = relations[branch["branch_id"]]
        if relation == "SUPPORT":
            _append_unique_evidence(branch["E_plus"], evidence)
        elif relation == "COUNTER":
            _append_unique_evidence(branch["E_minus"], evidence)
        elif relation == "FALSIFY":
            _append_unique_evidence(branch["E_minus"], evidence)
            branch["validity"] = "FALSIFIED"
        elif relation == "NO_EFFECT":
            pass
    merge_directives = observation.get("merge_directives", [])
    for directive in merge_directives:
        _required(
            directive,
            ["source_branch_ids", "merged_branch_id", "equivalence_rule", "equivalence_certificate_id"],
            "merge_directive",
        )
        src_ids = list(directive["source_branch_ids"])
        if len(src_ids) < 2 or len(set(src_ids)) != len(src_ids):
            raise LabelerError("merge_directive: need >=2 distinct source branches")
        if directive["equivalence_rule"] != "EXACT_SYNTHETIC_EQUIVALENCE":
            raise LabelerError("merge_directive: only exact declared synthetic equivalence is supported")
        by_id = {b["branch_id"]: b for b in out}
        if any(x not in by_id for x in src_ids):
            raise LabelerError("merge_directive: unknown source branch")
        if directive["merged_branch_id"] in by_id:
            raise LabelerError("merge_directive: merged_branch_id already exists")
        src = [by_id[x] for x in src_ids]
        signature = {(b["v_semantic_value"], b["K_context_predicate"], b["T_validity_scope"]) for b in src}
        if len(signature) != 1:
            raise LabelerError("merge_directive: branches are not exactly equivalent on v/K/T")
        merged = copy.deepcopy(src[0])
        merged["branch_id"] = directive["merged_branch_id"]
        merged["A_origin_provenance"] = "MERGE:" + directive["equivalence_certificate_id"]
        merged["merge_certificate_id"] = directive["equivalence_certificate_id"]
        merged["merged_from"] = sorted(src_ids)
        merged["validity"] = "LIVE"
        merged["E_plus"] = []
        merged["E_minus"] = []
        for b in src:
            for item in b["E_plus"]:
                _append_unique_evidence(merged["E_plus"], item)
            for item in b["E_minus"]:
                _append_unique_evidence(merged["E_minus"], item)
            b["validity"] = "OUT_OF_SCOPE"
            b["merged_into"] = directive["merged_branch_id"]
            b["merge_certificate_id"] = directive["equivalence_certificate_id"]
        out.append(merged)
    return out


def _has_decisive_support(branch: dict[str, Any]) -> bool:
    return any(e.get("decision_role") == "DECISIVE_SUPPORT" for e in branch["E_plus"])


def _has_decisive_contradiction(branch: dict[str, Any]) -> bool:
    return any(e.get("decision_role") == "DECISIVE_CONTRADICTION" for e in branch["E_minus"])


def D_resolve(branch_set: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    """Return task-local resolution without majority, salience, recurrence or probability.

    Resolution is permitted only when the context declares an executed admissible
    discriminator/proof event and the post-update state leaves exactly one eligible branch.
    """
    validate_branch_set(branch_set)
    _required(
        context,
        ["context_id", "discriminator_executed", "discriminator_admissible", "resolution_scope"],
        "resolve_context",
    )
    if context["resolution_scope"] != "TASK_LOCAL_SYNTHETIC_OR_ADMITTED_EVIDENCE":
        raise LabelerError("resolve_context: invalid resolution_scope")

    eligible: list[dict[str, Any]] = []
    for b in branch_set:
        if b["validity"] != "LIVE":
            continue
        if _has_decisive_contradiction(b):
            continue
        eligible.append(b)

    if not context["discriminator_executed"] or not context["discriminator_admissible"]:
        return {
            "status": "UNRESOLVED",
            "resolved_branch": None,
            "live_branches": [b["branch_id"] for b in eligible],
            "reason": "NO_ADMISSIBLE_EXECUTED_DISCRIMINATOR",
            "canonical_truth_minted": False,
        }

    if len(eligible) == 1:
        winner = eligible[0]
        if _has_decisive_support(winner) or context.get("all_other_branches_explicitly_falsified", False):
            return {
                "status": "RESOLVED_WITHIN_TASK",
                "resolved_branch": winner["branch_id"],
                "live_branches": [winner["branch_id"]],
                "reason": "UNIQUE_ELIGIBLE_BRANCH_AFTER_ADMISSIBLE_DISCRIMINATOR",
                "canonical_truth_minted": False,
            }

    return {
        "status": "UNRESOLVED",
        "resolved_branch": None,
        "live_branches": [b["branch_id"] for b in eligible],
        "reason": "MULTIPLE_OR_ZERO_ELIGIBLE_BRANCHES",
        "canonical_truth_minted": False,
    }


def _unordered_pair(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted((a, b)))


def U_d_test_order(branch_set: list[dict[str, Any]], tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank discriminators by separation utility, not by truth probability.

    Lexicographic preference:
    1) admissible & observable;
    2) more live branch pairs separated;
    3) more novel independence groups;
    4) lower declared cost;
    5) stable test_id tie-break.
    """
    validate_branch_set(branch_set)
    live_ids = sorted(b["branch_id"] for b in branch_set if b["validity"] == "LIVE")
    live_pairs = {_unordered_pair(a, b) for a, b in itertools.combinations(live_ids, 2)}
    ranked: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for t in tests:
        _required(
            t,
            [
                "schema",
                "test_id",
                "admissible",
                "observable",
                "separates_branch_pairs",
                "novel_independence_groups",
                "cost_units",
            ],
            "discriminator",
        )
        if t["schema"] != TEST_SCHEMA:
            raise LabelerError("discriminator: wrong schema")
        if t["test_id"] in seen_ids:
            raise LabelerError("discriminator: duplicate test_id")
        seen_ids.add(t["test_id"])
        declared_pairs = {_unordered_pair(*p) for p in t["separates_branch_pairs"]}
        if not declared_pairs <= live_pairs:
            raise LabelerError("discriminator: pair outside live branch set")
        if t["cost_units"] < 0:
            raise LabelerError("discriminator: negative cost")
        coverage = len(declared_pairs)
        admissible_observable = int(bool(t["admissible"] and t["observable"]))
        result = copy.deepcopy(t)
        result["pair_coverage"] = coverage
        result["ranking_key_explanation"] = "admissible_observable > pair_coverage > independence_novelty > lower_cost"
        result["truth_probability"] = None
        result["truth_status_changed"] = False
        result["_sort_key"] = (
            -admissible_observable,
            -coverage,
            -int(t["novel_independence_groups"]),
            float(t["cost_units"]),
            str(t["test_id"]),
        )
        ranked.append(result)
    ranked.sort(key=lambda x: x["_sort_key"])
    for i, t in enumerate(ranked, start=1):
        t["rank"] = i
        del t["_sort_key"]
    return ranked


def f_salience_rank(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank attention/reentry priority without changing evidence or truth status.

    Required generator-side factors are bounded integers 0..3:
    decision_relevance, deadline_urgency, reentry_cost. Higher relevance/urgency and
    lower reentry cost rank earlier. No support count, majority, confidence or recurrence
    is accepted as a factor.
    """
    ranked: list[dict[str, Any]] = []
    seen: set[str] = set()
    forbidden = {"support_count", "majority", "confidence", "probability", "recurrence_count", "vote_count"}
    for item in items:
        _required(item, ["item_id", "decision_relevance", "deadline_urgency", "reentry_cost"], "salience_item")
        if item["item_id"] in seen:
            raise LabelerError("salience_item: duplicate item_id")
        seen.add(item["item_id"])
        if forbidden & set(item):
            raise LabelerError("salience_item: truth/probability proxy factor forbidden")
        for k in ("decision_relevance", "deadline_urgency", "reentry_cost"):
            if not isinstance(item[k], int) or not 0 <= item[k] <= 3:
                raise LabelerError(f"salience_item: {k} must be int 0..3")
        out = copy.deepcopy(item)
        out["truth_probability"] = None
        out["truth_status_changed"] = False
        out["_sort_key"] = (
            -item["decision_relevance"],
            -item["deadline_urgency"],
            item["reentry_cost"],
            str(item["item_id"]),
        )
        ranked.append(out)
    ranked.sort(key=lambda x: x["_sort_key"])
    for i, item in enumerate(ranked, start=1):
        item["salience_rank"] = i
        del item["_sort_key"]
    return ranked


def label_transition(
    branch_set: list[dict[str, Any]],
    observation: dict[str, Any],
    resolve_context: dict[str, Any],
) -> dict[str, Any]:
    after = U_update(branch_set, observation)
    resolution = D_resolve(after, resolve_context)
    return {
        "schema": SCHEMA,
        "hyperposition_state_after": after,
        "resolution": resolution,
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
    }
