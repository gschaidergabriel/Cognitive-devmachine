#!/usr/bin/env python3
"""Trigger-2 ZECP07 ancestry-aware semantic relation gate.

Companion gate to the current executable-transition semantic acceptance. It adds the
missing matched-pair relation from the correlated-evidence ancestry eval: raw vote
counts and wording may remain identical while only upstream provenance grouping changes.
The change may alter discriminator priority/confidence, but it must never mint truth.

Source/eval only. PASS mints zero dataset, checkpoint, J-Space, runtime or training credit.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from trigger2_cognitive_process_executable_transition_pilot_v2 import rows
from trigger2_cognitive_transition_semantic_relation_gate_v1 import validate_semantic_relation

SCHEMA = "TRIGGER2_ZECP07_ANCESTRY_RELATION_GATE/v1"


def _need(cond: bool, code: str) -> None:
    if not cond:
        raise ValueError(code)


def _group_count(groups: Any, alternative: str) -> int | None:
    if groups is None or groups == "UNKNOWN":
        return None
    _need(isinstance(groups, dict), "ANCESTRY_GROUPS_OBJECT_OR_UNKNOWN_REQUIRED")
    value = groups.get(alternative)
    _need(isinstance(value, list), f"ANCESTRY_GROUP_LIST_REQUIRED:{alternative}")
    _need(all(isinstance(x, str) and x for x in value), f"ANCESTRY_GROUP_ID_INVALID:{alternative}")
    return len(set(value))


def adjudicate_ancestry_relation(case: dict[str, Any]) -> dict[str, Any]:
    votes = case.get("votes")
    _need(isinstance(votes, dict), "VOTES_OBJECT_REQUIRED")
    _need(set(votes) == {"A", "B"}, "VOTE_ALTERNATIVES_MUST_BE_A_B")
    a_votes = votes["A"]
    b_votes = votes["B"]
    _need(isinstance(a_votes, int) and a_votes >= 0, "A_VOTE_COUNT_INVALID")
    _need(isinstance(b_votes, int) and b_votes >= 0, "B_VOTE_COUNT_INVALID")

    causal = case.get("causal_discriminator")
    groups = case.get("upstream_groups")
    a_groups = _group_count(groups, "A")
    b_groups = _group_count(groups, "B")

    if causal is not None:
        return {
            "resolution": "DEFER_TO_CAUSAL_DISCRIMINATOR",
            "provenance_independence": "NOT_DECISIVE_ONCE_CAUSAL_RESULT_EXISTS",
            "next": "ADJUDICATE_CAUSAL_RESULT_THROUGH_DETERMINISTIC_GATE",
            "majority_minted_truth": False,
            "truth_authority": False,
        }

    if a_groups is None or b_groups is None:
        return {
            "resolution": "UNRESOLVED",
            "provenance_independence": "UNKNOWN",
            "next": "RESOLVE_ANCESTRY_OR_RUN_CAUSAL_DISCRIMINATOR",
            "majority_minted_truth": False,
            "truth_authority": False,
        }

    raw_majority = "A" if a_votes > b_votes else "B" if b_votes > a_votes else "TIE"
    effective_majority = "A" if a_groups > b_groups else "B" if b_groups > a_groups else "TIE"
    correlated_a = a_groups < a_votes
    correlated_b = b_groups < b_votes

    if raw_majority != "TIE" and raw_majority != effective_majority:
        next_action = "TRACE_OR_RETRIEVE_INDEPENDENT_EVIDENCE"
    elif correlated_a or correlated_b:
        next_action = "TRACE_OR_RETRIEVE_INDEPENDENT_EVIDENCE"
    else:
        next_action = "RUN_CAUSAL_DISCRIMINATOR"

    if correlated_a and not correlated_b:
        provenance = "KNOWN_CORRELATED_A"
    elif correlated_b and not correlated_a:
        provenance = "KNOWN_CORRELATED_B"
    elif correlated_a and correlated_b:
        provenance = "KNOWN_CORRELATED_BOTH"
    else:
        provenance = "KNOWN_INDEPENDENCE_GROUPS"

    return {
        "resolution": "UNRESOLVED",
        "provenance_independence": provenance,
        "raw_vote_majority": raw_majority,
        "effective_ancestry_group_majority": effective_majority,
        "effective_group_counts": {"A": a_groups, "B": b_groups},
        "next": next_action,
        "majority_minted_truth": False,
        "truth_authority": False,
    }


def validate_expected(case: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    actual = adjudicate_ancestry_relation(case)
    for key, value in expected.items():
        _need(actual.get(key) == value, f"ANCESTRY_EXPECTATION_MISMATCH:{key}")
    _need(actual["resolution"] != "A_IS_TRUE", "CORRELATED_MAJORITY_MINTED_TRUTH")
    _need(actual["resolution"] != "B_IS_TRUE", "CORRELATED_MAJORITY_MINTED_TRUTH")
    _need(actual["majority_minted_truth"] is False, "MAJORITY_TRUTH_FLAG_FORBIDDEN")
    _need(actual["truth_authority"] is False, "ANCESTRY_COUNT_CANNOT_MINT_TRUTH_AUTHORITY")
    return actual


def _base_zecp07_row() -> dict[str, Any]:
    row = next(r for r in rows() if r["process_id_evaluator_only"] == "ZECP07")
    validate_semantic_relation(row)
    return row


def self_test() -> dict[str, Any]:
    cases: dict[str, bool] = {}

    # Anchor this companion relation to the current ZECP07 semantic gate first.
    base = _base_zecp07_row()
    cases["CURRENT_ZECP07_BASE_SEMANTIC_RELATION_PASSES"] = (
        base["process_id_evaluator_only"] == "ZECP07"
    )

    correlated = {
        "votes": {"A": 8, "B": 2},
        "upstream_groups": {"A": ["src-X"], "B": ["src-Y", "src-Z"]},
        "causal_discriminator": None,
    }
    independent = {
        "votes": {"A": 8, "B": 2},
        "upstream_groups": {
            "A": [f"src-A{i}" for i in range(1, 9)],
            "B": ["src-Y", "src-Z"],
        },
        "causal_discriminator": None,
    }
    unknown = {
        "votes": {"A": 8, "B": 2},
        "upstream_groups": "UNKNOWN",
        "causal_discriminator": None,
    }

    c = validate_expected(
        correlated,
        {
            "resolution": "UNRESOLVED",
            "provenance_independence": "KNOWN_CORRELATED_A",
            "next": "TRACE_OR_RETRIEVE_INDEPENDENT_EVIDENCE",
            "majority_minted_truth": False,
        },
    )
    i = validate_expected(
        independent,
        {
            "resolution": "UNRESOLVED",
            "provenance_independence": "KNOWN_INDEPENDENCE_GROUPS",
            "next": "RUN_CAUSAL_DISCRIMINATOR",
            "majority_minted_truth": False,
        },
    )
    u = validate_expected(
        unknown,
        {
            "resolution": "UNRESOLVED",
            "provenance_independence": "UNKNOWN",
            "next": "RESOLVE_ANCESTRY_OR_RUN_CAUSAL_DISCRIMINATOR",
            "majority_minted_truth": False,
        },
    )

    cases["MATCHED_PAIR_RAW_VOTES_IDENTICAL"] = correlated["votes"] == independent["votes"]
    cases["MATCHED_PAIR_ONLY_ANCESTRY_CHANGES_DECISION_FEATURE"] = (
        c["provenance_independence"] != i["provenance_independence"]
        and c["next"] != i["next"]
        and c["resolution"] == i["resolution"] == "UNRESOLVED"
    )
    cases["UNKNOWN_ANCESTRY_PRESERVES_UNKNOWN"] = (
        u["provenance_independence"] == "UNKNOWN"
        and u["resolution"] == "UNRESOLVED"
    )

    # Hard negative: correlated majority cannot be rewritten to truth merely because
    # the raw count is 8:2. The expected relation must fail if a caller demands that.
    try:
        validate_expected(correlated, {"resolution": "A_IS_TRUE"})
        cases["CORRELATED_MAJORITY_TRUTH_SELECTION_REJECTED"] = False
    except ValueError:
        cases["CORRELATED_MAJORITY_TRUTH_SELECTION_REJECTED"] = True

    # Hard negative: even an ancestry-group majority is evidence only, never fact authority.
    try:
        validate_expected(independent, {"truth_authority": True})
        cases["INDEPENDENT_GROUP_COUNT_CANNOT_MINT_TRUTH"] = False
    except ValueError:
        cases["INDEPENDENT_GROUP_COUNT_CANNOT_MINT_TRUTH"] = True

    # Metamorphic control: presentation order of provenance groups must not change result.
    shuffled = copy.deepcopy(correlated)
    shuffled["upstream_groups"] = {
        "A": list(reversed(shuffled["upstream_groups"]["A"])),
        "B": list(reversed(shuffled["upstream_groups"]["B"])),
    }
    cases["ANCESTRY_GROUP_PRESENTATION_ORDER_INVARIANT"] = (
        adjudicate_ancestry_relation(shuffled) == adjudicate_ancestry_relation(correlated)
    )

    return {"pass": all(cases.values()), "cases": cases}


def run() -> dict[str, Any]:
    st = self_test()
    return {
        "schema": SCHEMA,
        "pass": st["pass"],
        "self_test": st,
        "process_scope": ["ZECP07"],
        "relation": "RAW_EVIDENCE_CARDINALITY_NEQ_INDEPENDENT_ANCESTRY_SUPPORT",
        "candidate_eval_only": True,
        "accepted_dataset_tokens": 0,
        "training_eligible_rows": 0,
        "training_credit": 0,
        "jspace_causal_credit": 0,
        "physical_grid10_runtime_credit": 0,
        "whole_hcu_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
    }


def main() -> int:
    result = run()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
