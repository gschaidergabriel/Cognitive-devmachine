#!/usr/bin/env python3
"""Derive Trigger-2 Hyperposition relations from a formal synthetic task world.

This is the missing upstream root-label primitive identified by the post-convergence
causal-label audit. It does NOT accept caller-supplied SUPPORTS/COUNTERS/FALSIFIES,
target-branch IDs, decision roles or winners. Instead it computes those fields from
explicit ground facts, deterministic Horn-style rules, branch claims and the observation.

The receipt is synthetic/curriculum evidence only. It cannot mint canonical truth,
real-effect authority, J-Space/HCU/runtime credit, accepted dataset tokens or training credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_TASKWORLD_RELATION_DERIVER/v1"
WORLD_SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_TASK_WORLD/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER2_SYNTHETIC_TASKWORLD_DERIVATION_RECEIPT/v1"
ALLOWED_RELATIONS = {"SUPPORTS", "COUNTERS", "FALSIFIES", "IRRELEVANT"}
_LITERAL_RE = re.compile(
    r"^!?[A-Za-z][A-Za-z0-9_]*(?:\([A-Za-z0-9_.:-]+(?:,[A-Za-z0-9_.:-]+)*\))?$"
)


class DerivationError(ValueError):
    pass


def _canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(x: Any) -> str:
    return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()


def _literal(x: Any) -> str:
    if not isinstance(x, str) or not _LITERAL_RE.fullmatch(x):
        raise DerivationError(f"INVALID_LITERAL:{x!r}")
    return x


def negate(literal: str) -> str:
    _literal(literal)
    return literal[1:] if literal.startswith("!") else "!" + literal


def _validate_world(world: dict[str, Any]) -> None:
    if not isinstance(world, dict) or world.get("schema") != WORLD_SCHEMA:
        raise DerivationError("WORLD_SCHEMA_MISMATCH")
    if world.get("canonical_truth_allowed") is not False:
        raise DerivationError("WORLD_CANONICAL_TRUTH_MUST_BE_FALSE")
    if world.get("direct_effect_authority") is not False:
        raise DerivationError("WORLD_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if not isinstance(world.get("world_id"), str) or not world["world_id"]:
        raise DerivationError("WORLD_ID_REQUIRED")

    facts = world.get("base_facts", [])
    if not isinstance(facts, list):
        raise DerivationError("BASE_FACTS_LIST_REQUIRED")
    for fact in facts:
        _literal(fact)

    rules = world.get("rules", [])
    if not isinstance(rules, list):
        raise DerivationError("RULES_LIST_REQUIRED")
    rule_ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise DerivationError("RULE_OBJECT_REQUIRED")
        rid = rule.get("rule_id")
        if not isinstance(rid, str) or not rid or rid in rule_ids:
            raise DerivationError("RULE_ID_INVALID_OR_DUPLICATE")
        rule_ids.add(rid)
        antecedents = rule.get("if_all")
        if not isinstance(antecedents, list) or not antecedents:
            raise DerivationError("RULE_ANTECEDENTS_REQUIRED")
        for antecedent in antecedents:
            _literal(antecedent)
        _literal(rule.get("then"))

    branches = world.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        raise DerivationError("AT_LEAST_TWO_BRANCHES_REQUIRED")
    branch_ids: set[str] = set()
    for branch in branches:
        if not isinstance(branch, dict):
            raise DerivationError("BRANCH_OBJECT_REQUIRED")
        bid = branch.get("branch_id")
        if not isinstance(bid, str) or not bid or bid in branch_ids:
            raise DerivationError("BRANCH_ID_INVALID_OR_DUPLICATE")
        branch_ids.add(bid)
        _literal(branch.get("claim_literal"))

    observation = world.get("observation")
    if not isinstance(observation, dict):
        raise DerivationError("OBSERVATION_REQUIRED")

    # These fields are the labels this module exists to derive. Accepting them from the
    # generator would recreate the circular-label blocker.
    forbidden = {
        "relation",
        "branch_relations",
        "target_branch_ids",
        "decision_role",
        "winner_branch_id",
        "selected_branch_id",
    }
    injected = sorted(forbidden.intersection(observation))
    if injected:
        raise DerivationError("CALLER_DECISIVE_LABEL_FORBIDDEN:" + ",".join(injected))

    for key in (
        "evidence_event_id",
        "correlation_ancestry_id",
        "independence_group",
        "provenance",
    ):
        if not isinstance(observation.get(key), str) or not observation[key]:
            raise DerivationError("OBSERVATION_IDENTITY_REQUIRED:" + key)

    add_facts = observation.get("add_facts")
    if not isinstance(add_facts, list) or not add_facts:
        raise DerivationError("OBSERVATION_ADD_FACTS_REQUIRED")
    for fact in add_facts:
        _literal(fact)
    if observation.get("independence_qualified") not in {True, False}:
        raise DerivationError("INDEPENDENCE_QUALIFIED_BOOL_REQUIRED")


def forward_closure(facts: list[str], rules: list[dict[str, Any]]) -> list[str]:
    """Compute deterministic closure over finite ground Horn-style rules."""
    known = {_literal(x) for x in facts}
    changed = True
    while changed:
        changed = False
        for rule in rules:
            antecedents = {_literal(x) for x in rule["if_all"]}
            consequent = _literal(rule["then"])
            if antecedents.issubset(known) and consequent not in known:
                known.add(consequent)
                changed = True
    return sorted(known)


def _relation_for_claim(
    claim: str,
    before: set[str],
    after: set[str],
    observation_closure: set[str],
) -> str:
    """Derive one branch relation without collapsing explicit contradiction."""
    opposite = negate(claim)
    support_witness = claim in observation_closure or claim in (after - before)
    counter_witness = opposite in observation_closure or opposite in (after - before)

    # If the formal world entails both sides after the observation, contradiction remains
    # an object. It weakens the branch; it is not silently upgraded to falsification.
    if claim in after and opposite in after and (support_witness or counter_witness):
        return "COUNTERS"
    if counter_witness and opposite in after and claim not in after:
        return "FALSIFIES"
    if support_witness and claim in after and opposite not in after:
        return "SUPPORTS"
    return "IRRELEVANT"


def derive(world: dict[str, Any]) -> dict[str, Any]:
    """Create the immutable semantic-derivation receipt and labeler-ready observations."""
    _validate_world(world)
    rules = world["rules"]
    before_list = forward_closure(list(world.get("base_facts", [])), rules)
    before = set(before_list)
    observation = world["observation"]
    observation_closure_list = forward_closure(list(observation["add_facts"]), rules)
    observation_closure = set(observation_closure_list)
    after_list = forward_closure(
        list(world.get("base_facts", [])) + list(observation["add_facts"]), rules
    )
    after = set(after_list)

    relation_by_branch: dict[str, str] = {}
    truth_after: dict[str, str] = {}
    for branch in world["branches"]:
        claim = branch["claim_literal"]
        opposite = negate(claim)
        relation_by_branch[branch["branch_id"]] = _relation_for_claim(
            claim, before, after, observation_closure
        )
        has_positive = claim in after
        has_negative = opposite in after
        truth_after[branch["branch_id"]] = (
            "BOTH"
            if has_positive and has_negative
            else "TRUE_ONLY"
            if has_positive
            else "FALSE_ONLY"
            if has_negative
            else "UNKNOWN"
        )

    true_only = [bid for bid, status in truth_after.items() if status == "TRUE_ONLY"]
    false_only = [bid for bid, status in truth_after.items() if status == "FALSE_ONLY"]
    if len(true_only) == 1 and len(false_only) == len(truth_after) - 1:
        decision_role = "DECISIVE_SUPPORT"
        selected_branch_id: str | None = true_only[0]
    elif len(false_only) == len(truth_after):
        decision_role = "DECISIVE_CONTRADICTION"
        selected_branch_id = None
    else:
        decision_role = "NONDECISIVE"
        selected_branch_id = None

    grouped: dict[str, list[str]] = {relation: [] for relation in ALLOWED_RELATIONS}
    for bid, relation in relation_by_branch.items():
        grouped[relation].append(bid)

    core = {
        "schema": RECEIPT_SCHEMA,
        "deriver_schema": SCHEMA,
        "world_id": world["world_id"],
        "world_digest": _sha({k: v for k, v in world.items() if k != "observation"}),
        "observation_digest": _sha(observation),
        "rules_digest": _sha(rules),
        "before_closure": before_list,
        "before_closure_digest": _sha(before_list),
        "observation_closure": observation_closure_list,
        "observation_closure_digest": _sha(observation_closure_list),
        "after_closure": after_list,
        "after_closure_digest": _sha(after_list),
        "relation_by_branch": dict(sorted(relation_by_branch.items())),
        "truth_after_by_branch": dict(sorted(truth_after.items())),
        "decision_role": decision_role,
        "selected_branch_id": selected_branch_id,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "synthetic_task_only": True,
    }
    receipt_digest = _sha(core)

    # Current labeler-v2 consumes one relation for one target set, so one formal evidence
    # event is deterministically factored into relation-homogeneous packets. The shared
    # event/ancestry identity proves that the packets came from one causal observation.
    derived_observations = []
    for relation in ("SUPPORTS", "COUNTERS", "FALSIFIES", "IRRELEVANT"):
        targets = sorted(grouped[relation])
        if not targets:
            continue
        derived_observations.append(
            {
                "evidence_event_id": observation["evidence_event_id"],
                "correlation_ancestry_id": observation["correlation_ancestry_id"],
                "independence_group": observation["independence_group"],
                "provenance": observation["provenance"],
                "independence_qualified": observation["independence_qualified"],
                "relation": relation,
                "target_branch_ids": targets,
                "decision_role_derived": decision_role,
                "derivation_receipt_sha256": receipt_digest,
                "canonical_truth_allowed": False,
                "direct_effect_authority": False,
            }
        )

    return {
        **core,
        "receipt_sha256": receipt_digest,
        "derived_observations": derived_observations,
    }


def verify_receipt(receipt: dict[str, Any]) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        return False
    expected = _sha(
        {
            k: v
            for k, v in receipt.items()
            if k not in {"receipt_sha256", "derived_observations"}
        }
    )
    if receipt.get("receipt_sha256") != expected:
        return False
    return all(
        isinstance(packet, dict)
        and packet.get("derivation_receipt_sha256") == expected
        and packet.get("relation") in ALLOWED_RELATIONS
        and packet.get("canonical_truth_allowed") is False
        and packet.get("direct_effect_authority") is False
        for packet in receipt.get("derived_observations", [])
    )


def apply_to_labeler_v2(
    state: dict[str, Any], receipt: dict[str, Any], labeler_module: Any
) -> dict[str, Any]:
    """Apply only hash-verified derived packets to the current event/ancestry labeler v2."""
    if not verify_receipt(receipt):
        raise DerivationError("RECEIPT_DIGEST_INVALID")
    out = json.loads(json.dumps(state))
    for observation in receipt["derived_observations"]:
        packet = {
            key: value
            for key, value in observation.items()
            if key
            not in {
                "decision_role_derived",
                "derivation_receipt_sha256",
                "canonical_truth_allowed",
                "direct_effect_authority",
            }
        }
        out = labeler_module.u_state(out, packet)
    return out
