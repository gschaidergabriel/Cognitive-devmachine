#!/usr/bin/env python3
"""Deterministic Trigger-2 semantic-Hyperposition reference labelers v2.

Successor to v1. Pure synthetic/curriculum labeling only. It does not mint
canonical truth, real-effect authority, J-Space/HCU/runtime or training credit.

v2 closes two important source-design gaps:
1) evidence independence is keyed by (independence_group, payload_key), not by
   provenance ancestry alone, so repackaging the same evidence under a new
   ancestry cannot become new support;
2) the labeler validates the full branch carrier needed by the current
   Hyperposition ontology, instead of relying on a separate gate for v/K/E/F/T/A/sigma.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_REFERENCE_LABELERS/v2"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v2"
OBS_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_OBSERVATION/v2"
DISC_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_DISCRIMINATOR/v2"

ALLOWED_EFFECTS = {"SUPPORT", "WEAKEN", "FALSIFY", "PROVE", "RETAIN"}
ALLOWED_EPISTEMIC = {
    "OBSERVED", "UNKNOWN", "HYPOTHESIS", "COUNTERHYPOTHESIS",
    "PREDICTION", "MEASUREMENT_ERROR", "CONTRADICTION", "SYNTHETIC_PROOF",
}
ALLOWED_VALIDITY = {"LIVE", "FALSIFIED", "PROVEN_WITHIN_SYNTHETIC_WORLD"}
ALLOWED_VISIBILITY = {"VISIBLE", "PROJECTED_OUT"}
REQUIRED_BRANCH_FIELDS = {
    "branch_id", "value", "context_predicate", "evidence_for",
    "evidence_against", "falsifier", "validity", "provenance",
    "epistemic_status", "visibility",
}
REQUIRED_EVIDENCE_FIELDS = {
    "evidence_id", "provenance_ancestry_id", "independence_group",
    "payload_key", "epistemic_type",
}


def _fail(code: str, **extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": False,
        "failure": code,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
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
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


def _nonempty(x: Any) -> bool:
    return isinstance(x, str) and bool(x.strip())


def _validate_evidence(ev: Any) -> str | None:
    if not isinstance(ev, dict):
        return "EVIDENCE_OBJECT_REQUIRED"
    if not REQUIRED_EVIDENCE_FIELDS.issubset(ev):
        return "EVIDENCE_FIELDS_MISSING"
    if not all(_nonempty(ev.get(k)) for k in ("evidence_id", "provenance_ancestry_id", "independence_group", "payload_key")):
        return "EVIDENCE_IDENTITY_FIELDS_INVALID"
    if ev.get("epistemic_type") not in ALLOWED_EPISTEMIC:
        return "EVIDENCE_EPISTEMIC_TYPE_INVALID"
    return None


def _validate_state(state: Any) -> str | None:
    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
        return "STATE_SCHEMA_MISMATCH"
    if state.get("canonical_truth_allowed") is not False:
        return "STATE_CANONICAL_TRUTH_MUST_BE_FALSE"
    if state.get("direct_effect_authority") is not False:
        return "STATE_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE"
    if not _nonempty(state.get("query_id")):
        return "STATE_QUERY_ID_REQUIRED"
    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        return "STATE_REQUIRES_AT_LEAST_TWO_BRANCHES"
    seen: set[str] = set()
    for b in branches:
        if not isinstance(b, dict):
            return "BRANCH_OBJECT_REQUIRED"
        if not REQUIRED_BRANCH_FIELDS.issubset(b):
            return "BRANCH_FULL_H_I_FIELDS_REQUIRED"
        bid = b.get("branch_id")
        if not _nonempty(bid):
            return "BRANCH_ID_REQUIRED"
        if bid in seen:
            return "DUPLICATE_BRANCH_ID"
        seen.add(bid)
        if not _nonempty(b.get("value")) or not _nonempty(b.get("context_predicate")):
            return "BRANCH_VALUE_OR_CONTEXT_INVALID"
        if b.get("validity") not in ALLOWED_VALIDITY:
            return "BRANCH_VALIDITY_INVALID"
        if b.get("visibility") not in ALLOWED_VISIBILITY:
            return "BRANCH_VISIBILITY_INVALID"
        if not _nonempty(b.get("provenance")):
            return "BRANCH_PROVENANCE_REQUIRED"
        if b.get("epistemic_status") not in ALLOWED_EPISTEMIC:
            return "BRANCH_EPISTEMIC_STATUS_INVALID"
        if b.get("falsifier") is None:
            return "BRANCH_FALSIFIER_EXPLICIT_VALUE_REQUIRED"
        for side in ("evidence_for", "evidence_against"):
            if not isinstance(b.get(side), list):
                return "BRANCH_EVIDENCE_LISTS_REQUIRED"
            for ev in b[side]:
                err = _validate_evidence(ev)
                if err:
                    return err
    return None


def _independence_key(ev: dict[str, Any]) -> tuple[str, str]:
    return (str(ev["independence_group"]), str(ev["payload_key"]))


def _seen_independence_keys(state: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for b in state["branches"]:
        for side in ("evidence_for", "evidence_against"):
            for ev in b.get(side, []):
                if isinstance(ev, dict) and REQUIRED_EVIDENCE_FIELDS.issubset(ev):
                    keys.add(_independence_key(ev))
    return keys


def U_update(state: Any, observation: Any) -> dict[str, Any]:
    """Update branch-local evidence without branch deletion or automatic resolution."""
    err = _validate_state(state)
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
    if not isinstance(targets, list) or not targets or not all(_nonempty(x) for x in targets):
        return _fail("OBSERVATION_TARGET_BRANCH_IDS_REQUIRED")
    evidence = observation.get("evidence")
    ev_err = _validate_evidence(evidence)
    if ev_err:
        return _fail(ev_err)

    out = deepcopy(state)
    by_id = {b["branch_id"]: b for b in out["branches"]}
    missing = sorted(set(targets) - set(by_id))
    if missing:
        return _fail("OBSERVATION_TARGET_BRANCH_UNKNOWN", unknown_branch_ids=missing)

    key = _independence_key(evidence)
    novel_independent_evidence = key not in _seen_independence_keys(state)
    updates: list[dict[str, Any]] = []

    if not novel_independent_evidence:
        out.setdefault("duplicate_evidence_receipts", []).append({
            "evidence_id": evidence["evidence_id"],
            "provenance_ancestry_id": evidence["provenance_ancestry_id"],
            "independence_group": evidence["independence_group"],
            "payload_key": evidence["payload_key"],
            "rule": "REPACKAGING_DOES_NOT_CREATE_INDEPENDENT_EVIDENCE",
        })

    for bid in targets:
        b = by_id[bid]
        before = b["validity"]
        ev = deepcopy(evidence)
        ev["independent_for_update"] = novel_independent_evidence
        ev["applied_effect"] = effect
        ev["target_branch_id"] = bid

        if novel_independent_evidence:
            if effect in {"SUPPORT", "PROVE"}:
                b["evidence_for"].append(ev)
            elif effect in {"WEAKEN", "FALSIFY"}:
                b["evidence_against"].append(ev)
            elif effect == "RETAIN":
                b.setdefault("retention_events", []).append(ev)

            if effect == "FALSIFY":
                b["validity"] = "FALSIFIED"
            elif effect == "PROVE":
                b["validity"] = "PROVEN_WITHIN_SYNTHETIC_WORLD"

        updates.append({
            "branch_id": bid,
            "effect": effect,
            "independent_for_update": novel_independent_evidence,
            "validity_before": before,
            "validity_after": b["validity"],
        })

    out["branches"] = [by_id[b["branch_id"]] for b in state["branches"]]
    out["last_observation_id"] = evidence["evidence_id"]
    return _ok(
        labeler="U_update",
        state_after=out,
        updates=updates,
        branch_count_before=len(state["branches"]),
        branch_count_after=len(out["branches"]),
        automatic_resolution_performed=False,
        independence_key=["independence_group", "payload_key"],
        novel_independent_evidence=novel_independent_evidence,
        rule="PRESERVE_BRANCH_SET_AND_DEDUP_REPACKAGED_EVIDENCE",
    )


def D_resolve(state: Any, discriminator_outcome: Any | None = None) -> dict[str, Any]:
    """Resolve only from explicit synthetic proof or an adequate discriminator."""
    err = _validate_state(state)
    if err:
        return _fail(err)
    live = [b for b in state["branches"] if b["validity"] != "FALSIFIED"]
    proven = [b for b in live if b["validity"] == "PROVEN_WITHIN_SYNTHETIC_WORLD"]

    if discriminator_outcome is None:
        if len(proven) == 1:
            return _ok(
                labeler="D_resolve",
                resolution={
                    "status": "RESOLVED_WITHIN_SYNTHETIC_WORLD",
                    "resolved_branch": proven[0]["branch_id"],
                    "basis": "UNIQUE_EXPLICIT_SYNTHETIC_PROOF",
                },
                retained_branch_ids=[b["branch_id"] for b in state["branches"]],
            )
        return _ok(
            labeler="D_resolve",
            resolution={
                "status": "UNRESOLVED",
                "resolved_branch": None,
                "basis": "NO_UNIQUE_EXPLICIT_PROOF_OR_ADEQUATE_DISCRIMINATOR",
            },
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )

    if not isinstance(discriminator_outcome, dict) or discriminator_outcome.get("schema") != DISC_SCHEMA:
        return _fail("DISCRIMINATOR_SCHEMA_MISMATCH")
    if discriminator_outcome.get("canonical_truth_allowed") is not False:
        return _fail("DISCRIMINATOR_CANONICAL_TRUTH_MUST_BE_FALSE")
    if discriminator_outcome.get("direct_effect_authority") is not False:
        return _fail("DISCRIMINATOR_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    winner = discriminator_outcome.get("winner_branch_id")
    live_ids = {b["branch_id"] for b in live}
    if winner not in live_ids:
        return _fail("DISCRIMINATOR_WINNER_NOT_LIVE")
    separates = discriminator_outcome.get("separates_live_branch_ids")
    if not isinstance(separates, list) or set(separates) != live_ids:
        return _ok(
            labeler="D_resolve",
            resolution={
                "status": "UNRESOLVED",
                "resolved_branch": None,
                "basis": "DISCRIMINATOR_DOES_NOT_SEPARATE_ALL_LIVE_ALTERNATIVES",
            },
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )
    if discriminator_outcome.get("evidence_qualified") is not True:
        return _ok(
            labeler="D_resolve",
            resolution={
                "status": "UNRESOLVED",
                "resolved_branch": None,
                "basis": "DISCRIMINATOR_NOT_EVIDENCE_QUALIFIED",
            },
            retained_branch_ids=[b["branch_id"] for b in state["branches"]],
        )
    return _ok(
        labeler="D_resolve",
        resolution={
            "status": "RESOLVED_WITHIN_SYNTHETIC_WORLD",
            "resolved_branch": winner,
            "basis": "EXPLICIT_ADEQUATE_DISCRIMINATOR",
        },
        retained_branch_ids=[b["branch_id"] for b in state["branches"]],
    )


def U_d_test_order(state: Any, discriminators: Any) -> dict[str, Any]:
    """Ordinal test ordering; emits no probability, expected-IG or mixed-unit score."""
    err = _validate_state(state)
    if err:
        return _fail(err)
    if not isinstance(discriminators, list) or not discriminators:
        return _fail("DISCRIMINATOR_LIST_REQUIRED")

    live_ids = {b["branch_id"] for b in state["branches"] if b["validity"] != "FALSIFIED"}
    required_pairs = set(combinations(sorted(live_ids), 2))
    rows: list[dict[str, Any]] = []
    for d in discriminators:
        if not isinstance(d, dict) or d.get("schema") != DISC_SCHEMA:
            return _fail("DISCRIMINATOR_SCHEMA_MISMATCH")
        did = d.get("discriminator_id")
        pairs = d.get("separates_pairs")
        ranks = (d.get("risk_rank"), d.get("cost_rank"), d.get("coordination_rank"))
        if not _nonempty(did) or not isinstance(pairs, list):
            return _fail("DISCRIMINATOR_ORDER_FIELDS_INVALID")
        if not all(isinstance(x, int) and x >= 0 for x in ranks):
            return _fail("DISCRIMINATOR_ORDINAL_RANKS_INVALID")
        covered = set()
        for p in pairs:
            if isinstance(p, list) and len(p) == 2 and p[0] != p[1] and set(p).issubset(live_ids):
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
            "separates_all_live_pairs": covered == required_pairs,
            "risk_rank": ranks[0],
            "cost_rank": ranks[1],
            "coordination_rank": ranks[2],
            "_key": (0 if admissible else 1, -len(covered), ranks[0], ranks[1], ranks[2], did),
        })
    rows.sort(key=lambda x: x["_key"])
    for i, row in enumerate(rows, 1):
        row["ordinal_rank"] = i
        del row["_key"]
    return _ok(
        labeler="U_d_test_order",
        ordering=rows,
        probability_output=False,
        expected_information_gain_output=False,
        truth_output=False,
        rule="ADMISSIBLE_THEN_MAX_BRANCH_PAIR_SEPARATION_THEN_MIN_RISK_COST_COORDINATION_RANKS",
    )


def f_salience_rank(items: Any) -> dict[str, Any]:
    """Attention salience ordering only; never truth, probability or evidence strength."""
    if not isinstance(items, list) or not items:
        return _fail("SALIENCE_ITEM_LIST_REQUIRED")
    rows = []
    for item in items:
        if not isinstance(item, dict):
            return _fail("SALIENCE_ITEM_OBJECT_REQUIRED")
        iid = item.get("item_id")
        ranks = (item.get("actionability_rank"), item.get("scope_rank"), item.get("freshness_rank"))
        if not _nonempty(iid):
            return _fail("SALIENCE_ITEM_ID_REQUIRED")
        if not all(isinstance(x, int) and x >= 0 for x in ranks):
            return _fail("SALIENCE_RANK_FIELDS_INVALID")
        rows.append({
            "item_id": iid,
            "actionability_rank": ranks[0],
            "scope_rank": ranks[1],
            "freshness_rank": ranks[2],
            "_key": (*ranks, iid),
        })
    rows.sort(key=lambda x: x["_key"])
    for i, row in enumerate(rows, 1):
        row["salience_rank"] = i
        del row["_key"]
    return _ok(
        labeler="f_salience_rank",
        ranking=rows,
        probability_output=False,
        truth_output=False,
        evidence_strength_output=False,
        resolution_authority_output=False,
        rule="ATTENTION_ORDER_ONLY_NEVER_BRANCH_TRUTH",
    )


def epistemic_guard(source_type: Any, requested_target_type: Any, *, evidence_qualified_observation: bool = False) -> dict[str, Any]:
    """Fail closed on core GRF type confusions used by the E curriculum."""
    if source_type not in ALLOWED_EPISTEMIC or requested_target_type not in ALLOWED_EPISTEMIC:
        return _fail("EPISTEMIC_TYPE_INVALID")
    forbidden = {
        ("UNKNOWN", "OBSERVED"),
        ("MEASUREMENT_ERROR", "OBSERVED"),
        ("PREDICTION", "OBSERVED"),
        ("CONTRADICTION", "OBSERVED"),
    }
    if (source_type, requested_target_type) in forbidden and not evidence_qualified_observation:
        return _ok(
            labeler="epistemic_guard",
            transition_allowed=False,
            reason="EVIDENCE_QUALIFIED_OBSERVATION_REQUIRED",
            source_type=source_type,
            requested_target_type=requested_target_type,
        )
    if source_type in {"HYPOTHESIS", "COUNTERHYPOTHESIS"} and requested_target_type == "OBSERVED" and not evidence_qualified_observation:
        return _ok(
            labeler="epistemic_guard",
            transition_allowed=False,
            reason="HYPOTHESIS_CANNOT_SELF_PROMOTE_TO_OBSERVED",
            source_type=source_type,
            requested_target_type=requested_target_type,
        )
    return _ok(
        labeler="epistemic_guard",
        transition_allowed=True,
        source_type=source_type,
        requested_target_type=requested_target_type,
        note="UNKNOWN remains distinct from ZERO/ABSENT, which are not epistemic types in this schema.",
    )
