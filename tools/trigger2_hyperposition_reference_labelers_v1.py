#!/usr/bin/env python3
"""Deterministic training-only reference labelers for Trigger-2 semantic Hyperposition.

This module defines executable source-design labelers for synthetic/candidate training rows.
It is NOT canonical GRF authority, does not mint facts, and does not authorize effects.

Operators:
- U_update: branch-local evidence update without silent branch collapse.
- D_resolve: evidence-qualified synthetic-task resolution / explicit UNRESOLVED.
- U_d_test_order: deterministic discriminator ranking (ordering only, no probability).
- f_salience_rank: deterministic attention/salience ordering (never truth/probability).
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_REFERENCE_LABELERS/v1"
BRANCH_REQUIRED = (
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
)
ALLOWED_SIGMA = {
    "OBSERVED",
    "SUPPORTED",
    "HYPOTHESIS",
    "PREDICTION",
    "UNKNOWN",
    "COUNTERHYPOTHESIS",
    "CONTRADICTED",
    "FALSIFIED",
}
NONRESOLVING_EVIDENCE_KINDS = {"RECURRENCE", "MAJORITY", "SALIENCE", "SIMILARITY", "BROADCAST"}
EVIDENCE_POLARITIES = {"SUPPORT", "COUNTER", "FALSIFY", "NO_EFFECT"}


class LabelerError(ValueError):
    pass


def _canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise LabelerError(msg)


def validate_branch(branch: dict[str, Any]) -> None:
    for key in BRANCH_REQUIRED:
        _require(key in branch, f"MISSING_BRANCH_FIELD:{key}")
    _require(isinstance(branch["branch_id"], str) and branch["branch_id"], "INVALID_BRANCH_ID")
    _require(isinstance(branch["E_plus"], list), "E_PLUS_NOT_LIST")
    _require(isinstance(branch["E_minus"], list), "E_MINUS_NOT_LIST")
    _require(branch["sigma_epistemic_status"] in ALLOWED_SIGMA, "INVALID_SIGMA")
    _require(
        branch["projection_visibility"] in {"VISIBLE", "FILTERED_BUT_RETAINED"},
        "INVALID_PROJECTION_VISIBILITY",
    )


def validate_state(state: dict[str, Any]) -> None:
    _require(isinstance(state.get("query_id"), str) and state["query_id"], "INVALID_QUERY_ID")
    branches = state.get("branches")
    _require(isinstance(branches, list) and len(branches) >= 2, "NEED_AT_LEAST_TWO_BRANCHES")
    ids = []
    for branch in branches:
        validate_branch(branch)
        ids.append(branch["branch_id"])
    _require(len(ids) == len(set(ids)), "DUPLICATE_BRANCH_ID")


def _evidence_record(observation: dict[str, Any]) -> dict[str, Any]:
    required = ("evidence_id", "provenance", "independence_group", "evidence_kind", "polarity")
    for key in required:
        _require(key in observation, f"MISSING_OBSERVATION_FIELD:{key}")
    _require(observation["polarity"] in EVIDENCE_POLARITIES, "INVALID_POLARITY")
    return {
        "evidence_id": observation["evidence_id"],
        "provenance": observation["provenance"],
        "independence_group": observation["independence_group"],
        "evidence_kind": observation["evidence_kind"],
        "claim": observation.get("claim", ""),
    }


def U_update(state: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    """Apply one synthetic/candidate observation to named branches.

    Rules intentionally fail closed:
    - branch existence is preserved;
    - duplicate evidence IDs are idempotent;
    - recurrence/majority/salience/similarity/broadcast cannot resolve or falsify;
    - projection filtering is never deletion;
    - no canonical-truth/effect authority is produced.
    """
    validate_state(state)
    out = copy.deepcopy(state)
    target_ids = observation.get("target_branch_ids")
    _require(isinstance(target_ids, list) and target_ids, "MISSING_TARGET_BRANCH_IDS")
    known = {b["branch_id"] for b in out["branches"]}
    _require(set(target_ids) <= known, "UNKNOWN_TARGET_BRANCH")

    record = _evidence_record(observation)
    polarity = observation["polarity"]
    kind = observation["evidence_kind"]

    if kind in NONRESOLVING_EVIDENCE_KINDS:
        _require(polarity in {"NO_EFFECT", "SUPPORT", "COUNTER"}, "NONRESOLVING_KIND_CANNOT_FALSIFY")

    for branch in out["branches"]:
        if branch["branch_id"] not in target_ids:
            continue
        all_ids = {
            e.get("evidence_id")
            for e in branch["E_plus"] + branch["E_minus"]
            if isinstance(e, dict)
        }
        if record["evidence_id"] in all_ids:
            continue
        if polarity == "SUPPORT":
            branch["E_plus"].append(record)
            if branch["sigma_epistemic_status"] in {
                "UNKNOWN",
                "HYPOTHESIS",
                "PREDICTION",
                "COUNTERHYPOTHESIS",
            }:
                branch["sigma_epistemic_status"] = "SUPPORTED"
        elif polarity == "COUNTER":
            branch["E_minus"].append(record)
            if branch["sigma_epistemic_status"] != "FALSIFIED":
                branch["sigma_epistemic_status"] = "CONTRADICTED"
        elif polarity == "FALSIFY":
            _require(kind not in NONRESOLVING_EVIDENCE_KINDS, "INVALID_FALSIFIER_EVIDENCE_KIND")
            branch["E_minus"].append(record)
            branch["sigma_epistemic_status"] = "FALSIFIED"
        elif polarity == "NO_EFFECT":
            branch["E_minus"].append(record)

    out["last_update"] = {
        "operator": "U_update",
        "observation_digest": _sha(observation),
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
    }
    validate_state(out)
    return out


def D_resolve(
    state: dict[str, Any],
    discriminator_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return deterministic synthetic-task resolution without minting canonical truth."""
    validate_state(state)
    live = [b for b in state["branches"] if b["sigma_epistemic_status"] != "FALSIFIED"]
    base = {
        "operator": "D_resolve",
        "state_digest": _sha(state),
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
    }

    if discriminator_result is None:
        return {
            **base,
            "resolution_state": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "NO_DISCRIMINATOR_RESULT",
        }

    if discriminator_result.get("qualified") is not True:
        return {
            **base,
            "resolution_state": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "DISCRIMINATOR_NOT_QUALIFIED",
        }

    if discriminator_result.get("evidence_kind") in NONRESOLVING_EVIDENCE_KINDS:
        return {
            **base,
            "resolution_state": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "NONRESOLVING_SIGNAL",
        }

    selected = discriminator_result.get("selected_branch_id")
    if not isinstance(selected, str) or selected not in {b["branch_id"] for b in state["branches"]}:
        return {
            **base,
            "resolution_state": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "INVALID_SELECTED_BRANCH",
        }

    selected_branch = next(b for b in state["branches"] if b["branch_id"] == selected)
    if selected_branch["sigma_epistemic_status"] == "FALSIFIED":
        return {
            **base,
            "resolution_state": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "SELECTED_BRANCH_FALSIFIED",
        }

    others_live = [b["branch_id"] for b in live if b["branch_id"] != selected]
    if others_live:
        return {
            **base,
            "resolution_state": "UNRESOLVED",
            "resolved_branch_id": None,
            "reason": "COMPETING_LIVE_BRANCHES_REMAIN",
            "live_competitors": others_live,
        }

    return {
        **base,
        "resolution_state": "RESOLVED_SYNTHETIC_TASK",
        "resolved_branch_id": selected,
        "reason": "QUALIFIED_DISCRIMINATOR_AND_ALL_COMPETITORS_FALSIFIED",
    }


def U_d_test_order(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank discriminators structurally; score is an ordering aid, never probability."""
    ranked = []
    for d in candidates:
        for key in (
            "discriminator_id",
            "separation_count",
            "independence_score",
            "cost",
            "risk",
            "coordination_cost",
        ):
            _require(key in d, f"MISSING_DISCRIMINATOR_FIELD:{key}")
        denom = 1.0 + float(d["cost"]) + float(d["risk"]) + float(d["coordination_cost"])
        score = (float(d["separation_count"]) * float(d["independence_score"])) / denom
        ranked.append({**copy.deepcopy(d), "ordering_score": score, "score_is_probability": False})
    ranked.sort(key=lambda d: (-d["ordering_score"], str(d["discriminator_id"])))
    return ranked


def f_salience_rank(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank attention priority while explicitly denying truth/probability semantics."""
    ranked = []
    for item in items:
        for key in ("item_id", "decision_relevance", "retrieval_cost", "staleness_penalty"):
            _require(key in item, f"MISSING_SALIENCE_FIELD:{key}")
        score = (
            float(item["decision_relevance"])
            - float(item["retrieval_cost"])
            - float(item["staleness_penalty"])
        )
        ranked.append(
            {
                **copy.deepcopy(item),
                "salience_score": score,
                "salience_is_probability": False,
                "salience_is_truth": False,
            }
        )
    ranked.sort(key=lambda x: (-x["salience_score"], str(x["item_id"])))
    return ranked


def label_episode(episode: dict[str, Any]) -> dict[str, Any]:
    """Produce a complete deterministic training reference label for one episode."""
    before = episode["hyperposition_state_before"]
    observation = episode["event_or_observation"]
    after = U_update(before, observation)
    resolution = D_resolve(after, episode.get("discriminator_result"))
    discriminators = U_d_test_order(episode.get("discriminator_candidates", []))
    salience = f_salience_rank(episode.get("salience_items", []))
    return {
        "schema": SCHEMA,
        "hyperposition_state_before": before,
        "event_or_observation": observation,
        "hyperposition_state_after": after,
        "resolution": resolution,
        "discriminator_order": discriminators,
        "salience_order": salience,
        "semantic_class_or_action": episode.get("semantic_class_or_action", "ABSTAIN"),
        "runtime_codebook_or_opcode": episode.get("runtime_codebook_or_opcode"),
        "canonical_truth_minted": False,
        "direct_effect_authority": False,
        "training_only_reference": True,
    }
