#!/usr/bin/env python3
"""Successor scientific guard for Trigger-1 semantic-target specificity.

This guard composes the canonical Trigger-1 promotion gate and closes a narrower
scientific-independence gap: counterbalancing output-code labels does not by itself
exclude generic instruction/compliance steering when every evaluation prompt asks
for the same semantic target.

It does not mint canonical credit. It preserves the predecessor mechanism verdict
and may only demote scientific/owner-goal promotion.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate as base

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_SEMANTIC_TARGET_GATE/v1"


def _semantic_target_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    holdout = candidate.get("holdout")
    if not isinstance(holdout, dict):
        return False, ["HOLDOUT_REQUIRED_FOR_SEMANTIC_TARGET_GUARD"]

    if holdout.get("metric_uses_output_tokens") is not True:
        return True, []

    if holdout.get("requested_semantic_target_counterbalanced") is not True:
        return False, ["TOKEN_OUTPUT_METRIC_REQUIRES_COUNTERBALANCED_REQUESTED_SEMANTIC_TARGET"]

    targets = holdout.get("requested_semantic_targets")
    if not isinstance(targets, list) or len(targets) < 2 or not all(isinstance(x, str) and x.strip() for x in targets):
        return False, ["REQUESTED_SEMANTIC_TARGET_LIST_REQUIRED"]

    counts = Counter(x.strip() for x in targets)
    if len(counts) < 2:
        return False, ["REQUESTED_SEMANTIC_TARGET_VARIATION_REQUIRED"]
    if len(set(counts.values())) != 1:
        return False, ["REQUESTED_SEMANTIC_TARGET_COUNTS_MUST_BE_BALANCED"]

    return True, []


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    predecessor = base.adjudicate(candidate)
    semantic_ok, semantic_failures = _semantic_target_evidence(candidate)

    scientific = bool(predecessor.get("scientifically_independent_vector_candidate") is True and semantic_ok)
    owner = bool(predecessor.get("owner_trigger1_goal_credit_candidate") is True and semantic_ok)
    scientific_failures = sorted(set(predecessor.get("scientific_independence_failures", []) + semantic_failures))
    owner_failures = sorted(set(predecessor.get("owner_target_failures", []) + semantic_failures))

    return {
        "schema": VERDICT_SCHEMA,
        "predecessor_schema": predecessor.get("schema"),
        "mechanism_runtime_vector_credit_candidate": bool(predecessor.get("mechanism_runtime_vector_credit_candidate") is True),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "failures": sorted(set(predecessor.get("failures", []) + semantic_failures)),
        "scientific_independence_failures": scientific_failures,
        "owner_target_failures": owner_failures,
        "semantic_target_guard_pass": semantic_ok,
        "evidence_boundary": (
            "Output-label counterbalance alone cannot distinguish semantic steering from generic compliance. "
            "For token-output promotion, requested semantic targets must also vary and be balanced on holdout. "
            "This successor guard may demote predecessor scientific/owner-goal credit but never promotes mechanism, "
            "J-Space model, HCU, training, canonical semantics, or whole-product credit by itself."
        ),
        "predecessor_verdict": predecessor,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    try:
        candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "canonical_credit_minted": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }, sort_keys=True))
        return 0
    if not isinstance(candidate, dict):
        candidate = {}
    print(json.dumps(adjudicate(candidate), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
