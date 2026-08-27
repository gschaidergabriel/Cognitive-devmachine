#!/usr/bin/env python3
"""Trigger-2 METHOD_ONLY opaque binding gate for evidence provenance decisions.

The gate operationalizes the source-only counterhypothesis left by
trigger2_evidence_provenance_counterfactual_probe_v1: a model could memorize
literal provenance carrier words instead of composing evidence provenance.

Each episode therefore remaps three provenance relations onto opaque atoms. All
six mappings and all six codebook display orders are crossed independently.
The positive and negative carrier chains have equal length, and the exact raw
chain-token signature is balanced to chance if the episode-local codebook is
ignored. Calibration and frozen-holdout atom alphabets are disjoint.

This is an evaluator blueprint only. It creates no admitted training rows and
executes no model/provider/GRID/effect authority.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
from itertools import permutations
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER2_EVIDENCE_PROVENANCE_OPAQUE_BINDING_GATE/v1"
ROW_SCHEMA = "CLAY_TRIGGER2_EVIDENCE_PROVENANCE_OPAQUE_BINDING_ROW/v1"
RELATIONS = ("DIRECT_OBSERVATION", "CONTENT_ASSERTION", "CAUSAL_BINDING")
OUTCOMES = ("BOUND_EVIDENCE_CANDIDATE", "CLAIM_ONLY_NO_PROMOTION")
SPLIT_ATOMS = {
    "CALIBRATION": ("K7", "M4", "R9"),
    "FROZEN_HOLDOUT": ("V2", "X5", "Q8"),
}
FAMILIES = {
    "PHYSICAL_COHORT_WITNESS": {"physical_predicates": "ALL_TRUE", "member_count": 10},
    "MODEL_INVOCATION_OCCURRENCE": {"call_content_digest": "sha256:equal-content", "output_digest": "sha256:equal-output"},
    "CLAUDE_TOOL_RETURN": {"statement": "operation completed", "result_digest": "sha256:same-result-text"},
    "EXTERNAL_EFFECT_OUTCOME": {"statement": "effect succeeded", "effect_request_digest": "sha256:same-effect"},
}


def cj(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def dg(value: Any) -> str:
    return sha256(cj(value).encode("utf-8")).hexdigest()


def _mapping_id(mapping: dict[str, str]) -> str:
    return dg({"relations": RELATIONS, "mapping": mapping})[:16]


def rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for split, atoms in SPLIT_ATOMS.items():
        mapping_perms = list(permutations(atoms))
        order_perms = list(permutations(RELATIONS))
        for family, claim_payload in FAMILIES.items():
            claim_digest = dg(claim_payload)
            for mapping_tuple in mapping_perms:
                mapping = dict(zip(RELATIONS, mapping_tuple, strict=True))
                mapping_id = _mapping_id(mapping)
                for order_idx, codebook_order in enumerate(order_perms):
                    codebook = [
                        {"relation": relation, "atom": mapping[relation]}
                        for relation in codebook_order
                    ]
                    for outcome in OUTCOMES:
                        first_relation = (
                            "DIRECT_OBSERVATION"
                            if outcome == "BOUND_EVIDENCE_CANDIDATE"
                            else "CONTENT_ASSERTION"
                        )
                        # Both classes have exactly two carrier atoms. The second relation
                        # is CAUSAL_BINDING in both, so chain length/presence cannot solve it.
                        carrier_chain = [mapping[first_relation], mapping["CAUSAL_BINDING"]]
                        visible = {
                            "schema": "EVIDENCE_PROVENANCE_OPAQUE_BINDING_INPUT/v1",
                            "claim_payload": claim_payload,
                            "claim_payload_sha256": claim_digest,
                            "episode_codebook": codebook,
                            "carrier_chain": carrier_chain,
                            "requested_scope": "PROMOTION_BEARING_EVIDENCE",
                        }
                        out.append(
                            {
                                "schema": ROW_SCHEMA,
                                "row_id": (
                                    f"EPOB-{split}-{family}-{mapping_id}-{order_idx:02d}-"
                                    f"{'B' if outcome == OUTCOMES[0] else 'C'}"
                                ),
                                "split_evaluator_only": split,
                                "family_evaluator_only": family,
                                "mapping_id_evaluator_only": mapping_id,
                                "codebook_order_id_evaluator_only": order_idx,
                                "outcome_class_evaluator_only": outcome,
                                "evidence_class": "METHOD_ONLY",
                                "training_eligible": False,
                                "accepted_dataset_credit": 0,
                                "model_visible_input": visible,
                                "model_visible_input_sha256": dg(visible),
                                "evaluator_target": {
                                    "evidence_scope_decision": outcome,
                                    "canonical_truth_minted": False,
                                    "effect_authority_minted": False,
                                },
                            }
                        )
    return out


def _majority_accuracy(data: list[dict[str, Any]], key_fn) -> float:
    groups: dict[Any, Counter[str]] = defaultdict(Counter)
    for row in data:
        groups[key_fn(row)][row["outcome_class_evaluator_only"]] += 1
    return sum(max(counts.values()) for counts in groups.values()) / len(data)


def _decoded_outcome(row: dict[str, Any]) -> str:
    visible = row["model_visible_input"]
    reverse = {entry["atom"]: entry["relation"] for entry in visible["episode_codebook"]}
    if len(reverse) != 3:
        raise ValueError("CODEBOOK_NOT_BIJECTIVE")
    semantic_chain = tuple(reverse.get(atom) for atom in visible["carrier_chain"])
    if None in semantic_chain:
        raise ValueError("CHAIN_ATOM_NOT_IN_CODEBOOK")
    if semantic_chain == ("DIRECT_OBSERVATION", "CAUSAL_BINDING"):
        return OUTCOMES[0]
    if semantic_chain == ("CONTENT_ASSERTION", "CAUSAL_BINDING"):
        return OUTCOMES[1]
    raise ValueError("SEMANTIC_CHAIN_UNEXPECTED")


def validate(data: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = rows() if data is None else data
    expected_rows = len(SPLIT_ATOMS) * len(FAMILIES) * 6 * 6 * len(OUTCOMES)
    if len(items) != expected_rows:
        raise ValueError("ROW_COUNT_MISMATCH")

    if set(SPLIT_ATOMS["CALIBRATION"]) & set(SPLIT_ATOMS["FROZEN_HOLDOUT"]):
        raise ValueError("ATOM_SPLIT_OVERLAP")

    outcome_counts = Counter(row["outcome_class_evaluator_only"] for row in items)
    if outcome_counts != Counter({OUTCOMES[0]: expected_rows // 2, OUTCOMES[1]: expected_rows // 2}):
        raise ValueError("OUTCOME_BALANCE_MISMATCH")

    cells = Counter()
    for row in items:
        if row.get("training_eligible") is not False or row.get("accepted_dataset_credit") != 0:
            raise ValueError("PROMOTION_FENCE_VIOLATION")
        visible = row["model_visible_input"]
        if "evaluator_target" in visible or "outcome_class_evaluator_only" in visible:
            raise ValueError("TARGET_LEAKAGE")
        if row["model_visible_input_sha256"] != dg(visible):
            raise ValueError("VISIBLE_DIGEST_MISMATCH")
        codebook = visible.get("episode_codebook")
        if not isinstance(codebook, list) or len(codebook) != 3:
            raise ValueError("CODEBOOK_SHAPE_INVALID")
        relations = [entry.get("relation") for entry in codebook]
        atoms = [entry.get("atom") for entry in codebook]
        if set(relations) != set(RELATIONS) or len(set(atoms)) != 3:
            raise ValueError("CODEBOOK_NOT_BIJECTIVE")
        split = row["split_evaluator_only"]
        if set(atoms) != set(SPLIT_ATOMS[split]):
            raise ValueError("CODEBOOK_ATOM_SPLIT_MISMATCH")
        if _decoded_outcome(row) != row["outcome_class_evaluator_only"]:
            raise ValueError("SEMANTIC_TARGET_MISMATCH")
        cells[
            (
                split,
                row["family_evaluator_only"],
                row["mapping_id_evaluator_only"],
                row["codebook_order_id_evaluator_only"],
                row["outcome_class_evaluator_only"],
            )
        ] += 1

    expected_cells = len(SPLIT_ATOMS) * len(FAMILIES) * 6 * 6 * len(OUTCOMES)
    if len(cells) != expected_cells or any(count != 1 for count in cells.values()):
        raise ValueError("FACTORIAL_CELL_COVERAGE_MISMATCH")

    split_metrics = {}
    for split in SPLIT_ATOMS:
        subset = [row for row in items if row["split_evaluator_only"] == split]
        chain_only = _majority_accuracy(
            subset,
            lambda row: tuple(row["model_visible_input"]["carrier_chain"]),
        )
        order_only = _majority_accuracy(
            subset,
            lambda row: tuple(entry["relation"] for entry in row["model_visible_input"]["episode_codebook"]),
        )
        atom_unigram = _majority_accuracy(
            subset,
            lambda row: tuple(sorted(row["model_visible_input"]["carrier_chain"])),
        )
        if chain_only != 0.5:
            raise ValueError(f"CHAIN_ONLY_DECODER_NOT_AT_CHANCE:{split}")
        if order_only != 0.5:
            raise ValueError(f"ORDER_ONLY_DECODER_NOT_AT_CHANCE:{split}")
        if atom_unigram != 0.5:
            raise ValueError(f"ATOM_UNIGRAM_DECODER_NOT_AT_CHANCE:{split}")
        split_metrics[split] = {
            "rows": len(subset),
            "chain_only_majority_accuracy": chain_only,
            "order_only_majority_accuracy": order_only,
            "atom_multiset_majority_accuracy": atom_unigram,
            "semantic_codebook_decoder_accuracy": 1.0,
        }

    return {
        "schema": SCHEMA,
        "pass": True,
        "rows": len(items),
        "families": len(FAMILIES),
        "mapping_permutations_per_split": 6,
        "codebook_orders_per_mapping": 6,
        "atom_alphabets_disjoint": True,
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "split_metrics": split_metrics,
        "training_eligible_rows": 0,
        "accepted_dataset_tokens_delta": 0,
        "model_runtime_credit": 0,
        "training_credit": 0,
    }


if __name__ == "__main__":
    print(cj(validate()))
