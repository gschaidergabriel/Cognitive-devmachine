#!/usr/bin/env python3
"""Trigger-2 OOD topology provenance counterfactual probe.

METHOD_ONLY / evaluator-blueprint artifact.  No rows are training-admitted and
no provider/model/GRID/effect/canonical admission is performed.

The key counterfactual is stronger than the v1 provenance probe: paired rows
have the same visible lexical multiset (including graph node IDs, roles,
relation labels, JSON keys, claim atoms, and presentation metadata) and differ
only in graph connectivity.  A bag-of-visible-tokens decoder therefore has no
pairwise information, while a structural evaluator can still distinguish
whether an observation is causally connected to the claim through a receipt.

DEVELOPMENT and OOD_HOLDOUT use disjoint opaque carrier vocabularies.  This
tests the method-level dataset invariant needed before any model-level OOD
claim is attempted.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER2_EVIDENCE_PROVENANCE_TOPOLOGY_OOD_PROBE/v1"
ROW_SCHEMA = "CLAY_TRIGGER2_EVIDENCE_PROVENANCE_TOPOLOGY_OOD_ROW/v1"
OUTCOMES = ("BOUND_EVIDENCE_CANDIDATE", "CLAIM_ONLY_NO_PROMOTION")
SPLITS = ("DEVELOPMENT", "OOD_HOLDOUT")
FAMILY_COUNT = 4
NUISANCE = (
    ("layout-a", "forward", "carrier-alpha"),
    ("layout-a", "reverse", "carrier-beta"),
    ("layout-b", "forward", "carrier-beta"),
    ("layout-b", "reverse", "carrier-alpha"),
)


def cj(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def dg(value: Any) -> str:
    return sha256(cj(value).encode("utf-8")).hexdigest()


def _opaque_tokens(split: str, family_idx: int, nuisance_idx: int) -> tuple[str, ...]:
    prefix = "dvx" if split == "DEVELOPMENT" else "odz"
    return tuple(
        f"{prefix}_{family_idx:02d}_{nuisance_idx:02d}_{slot:02d}"
        for slot in range(8)
    )


def _ordered(items: list[dict[str, Any]], reverse: bool) -> list[dict[str, Any]]:
    return list(reversed(items)) if reverse else items


def _visible_graph(
    *,
    split: str,
    family_idx: int,
    nuisance_idx: int,
    outcome: str,
    reverse: bool,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    opaque = _opaque_tokens(split, family_idx, nuisance_idx)
    claim_id, receipt_id, observation_id, distractor_id = opaque[3:7]
    nodes = [
        {"id": claim_id, "role": "claim"},
        {"id": receipt_id, "role": "receipt"},
        {"id": observation_id, "role": "observation"},
        {"id": distractor_id, "role": "distractor"},
    ]

    # Both variants are directed 4-cycles. Thus each node ID occurs exactly
    # once as src and once as dst, every role/relation token count is identical,
    # and only connectivity differs.
    if outcome == "BOUND_EVIDENCE_CANDIDATE":
        edge_pairs = (
            (observation_id, receipt_id),
            (receipt_id, claim_id),
            (claim_id, distractor_id),
            (distractor_id, observation_id),
        )
    elif outcome == "CLAIM_ONLY_NO_PROMOTION":
        edge_pairs = (
            (observation_id, distractor_id),
            (distractor_id, claim_id),
            (claim_id, receipt_id),
            (receipt_id, observation_id),
        )
    else:
        raise ValueError("UNKNOWN_OUTCOME")

    edges = [{"src": src, "rel": "link", "dst": dst} for src, dst in edge_pairs]
    visible = {
        "schema": "EVIDENCE_PROVENANCE_TOPOLOGY_INPUT/v1",
        "claim_payload": {
            "opaque_atoms": [opaque[0], opaque[1], opaque[2]],
            "content_sha256": dg([opaque[0], opaque[1], opaque[2]]),
        },
        "evidence_graph": {
            "nodes": _ordered(nodes, reverse),
            "edges": _ordered(edges, reverse),
        },
        "requested_scope": "PROMOTION_BEARING_EVIDENCE",
    }
    return visible, opaque


def _leaf_token_counter(value: Any) -> Counter[str]:
    """Bag of all JSON key/value strings; deliberately ignores graph position."""
    out: Counter[str] = Counter()

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, val in obj.items():
                out[str(key)] += 1
                walk(val)
        elif isinstance(obj, list):
            for val in obj:
                walk(val)
        elif isinstance(obj, str):
            out[obj] += 1
        elif obj is None:
            out["<NULL>"] += 1
        elif isinstance(obj, bool):
            out["<BOOL:" + str(obj).lower() + ">"] += 1
        elif isinstance(obj, (int, float)):
            out["<NUM:" + repr(obj) + ">"] += 1
        else:
            raise TypeError(f"UNSUPPORTED_LEAF:{type(obj).__name__}")

    walk(value)
    return out


def lexical_bag_sha256(visible: dict[str, Any]) -> str:
    bag = sorted(_leaf_token_counter(visible).items())
    return dg(bag)


def semantic_topology_decision(visible: dict[str, Any]) -> str:
    """Reference structural rule; it does not inspect opaque carrier values."""
    graph = visible.get("evidence_graph")
    if not isinstance(graph, dict):
        raise ValueError("GRAPH_REQUIRED")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("GRAPH_SHAPE_INVALID")

    by_role: dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("NODE_INVALID")
        role, node_id = node.get("role"), node.get("id")
        if role in by_role or role not in {"claim", "receipt", "observation", "distractor"}:
            raise ValueError("NODE_ROLE_INVALID")
        if not isinstance(node_id, str):
            raise ValueError("NODE_ID_INVALID")
        by_role[role] = node_id
    if set(by_role) != {"claim", "receipt", "observation", "distractor"}:
        raise ValueError("NODE_ROLE_SET_INVALID")

    links: set[tuple[str, str]] = set()
    for edge in edges:
        if (
            not isinstance(edge, dict)
            or edge.get("rel") != "link"
            or not isinstance(edge.get("src"), str)
            or not isinstance(edge.get("dst"), str)
        ):
            raise ValueError("EDGE_INVALID")
        links.add((edge["src"], edge["dst"]))
    if len(edges) != 4 or len(links) != 4:
        raise ValueError("EDGE_SET_INVALID")

    bound = (
        (by_role["observation"], by_role["receipt"]) in links
        and (by_role["receipt"], by_role["claim"]) in links
    )
    return OUTCOMES[0] if bound else OUTCOMES[1]


def rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for split in SPLITS:
        for family_idx in range(1, FAMILY_COUNT + 1):
            for nuisance_idx, (layout, field_order, carrier_name) in enumerate(NUISANCE, 1):
                reverse = field_order == "reverse"
                pair_key = f"{split}:{family_idx:02d}:{nuisance_idx:02d}"
                for variant_idx, outcome in enumerate(OUTCOMES):
                    visible, opaque = _visible_graph(
                        split=split,
                        family_idx=family_idx,
                        nuisance_idx=nuisance_idx,
                        outcome=outcome,
                        reverse=reverse,
                    )
                    visible["presentation"] = {
                        "layout": layout,
                        "field_order": field_order,
                        "carrier_name": carrier_name,
                    }
                    target = {
                        "evidence_scope_decision": outcome,
                        "canonical_truth_minted": False,
                        "effect_authority_minted": False,
                    }
                    out.append(
                        {
                            "schema": ROW_SCHEMA,
                            "row_id": f"EPTG-{split}-{family_idx:02d}-{nuisance_idx:02d}-{variant_idx}",
                            "split_evaluator_only": split,
                            "family_evaluator_only": f"FAMILY_{family_idx:02d}",
                            "pair_key": pair_key,
                            "training_eligible": False,
                            "accepted_dataset_credit": 0,
                            "model_visible_input": visible,
                            "model_visible_input_sha256": dg(visible),
                            "visible_lexical_bag_sha256": lexical_bag_sha256(visible),
                            "carrier_tokens_evaluator_only": list(opaque),
                            "evaluator_target": target,
                            "outcome_class_evaluator_only": outcome,
                        }
                    )
    return out


def _majority_accuracy(items: list[dict[str, Any]], key_fields: tuple[str, ...]) -> float:
    groups: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    for row in items:
        p = row["model_visible_input"]["presentation"]
        key = tuple(p[field] for field in key_fields)
        groups[key][row["outcome_class_evaluator_only"]] += 1
    correct = sum(max(counts.values()) for counts in groups.values())
    return correct / len(items)


def validate(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data = rows() if items is None else items
    expected_rows = len(SPLITS) * FAMILY_COUNT * len(NUISANCE) * len(OUTCOMES)
    if len(data) != expected_rows:
        raise ValueError("ROW_COUNT_MISMATCH")

    outcomes = Counter(row.get("outcome_class_evaluator_only") for row in data)
    if outcomes != Counter({OUTCOMES[0]: expected_rows // 2, OUTCOMES[1]: expected_rows // 2}):
        raise ValueError("OUTCOME_BALANCE_MISMATCH")

    pair_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    carrier_by_split: dict[str, set[str]] = {split: set() for split in SPLITS}
    semantic_correct = 0

    for row in data:
        if row.get("training_eligible") is not False or row.get("accepted_dataset_credit") != 0:
            raise ValueError("PROMOTION_FENCE_VIOLATION")
        visible = row.get("model_visible_input")
        if not isinstance(visible, dict):
            raise ValueError("VISIBLE_INPUT_INVALID")
        forbidden_visible = {
            "evaluator_target",
            "outcome_class_evaluator_only",
            "split_evaluator_only",
            "family_evaluator_only",
            "training_eligible",
        }
        if forbidden_visible.intersection(visible):
            raise ValueError("TARGET_OR_SPLIT_LEAKAGE")
        if row.get("model_visible_input_sha256") != dg(visible):
            raise ValueError("VISIBLE_DIGEST_MISMATCH")
        if row.get("visible_lexical_bag_sha256") != lexical_bag_sha256(visible):
            raise ValueError("LEXICAL_BAG_DIGEST_MISMATCH")
        outcome = row["outcome_class_evaluator_only"]
        if semantic_topology_decision(visible) == outcome:
            semantic_correct += 1
        pair_groups[row["pair_key"]].append(row)
        split = row.get("split_evaluator_only")
        if split not in carrier_by_split:
            raise ValueError("SPLIT_INVALID")
        tokens = row.get("carrier_tokens_evaluator_only")
        if not isinstance(tokens, list) or any(not isinstance(t, str) for t in tokens):
            raise ValueError("CARRIER_TOKEN_SET_INVALID")
        carrier_by_split[split].update(tokens)

    expected_pairs = expected_rows // 2
    if len(pair_groups) != expected_pairs:
        raise ValueError("PAIR_COUNT_MISMATCH")
    for pair_key, pair in pair_groups.items():
        if len(pair) != 2:
            raise ValueError(f"PAIR_SIZE_MISMATCH:{pair_key}")
        if {row["outcome_class_evaluator_only"] for row in pair} != set(OUTCOMES):
            raise ValueError(f"PAIR_OUTCOME_MISMATCH:{pair_key}")
        if pair[0]["model_visible_input"]["claim_payload"] != pair[1]["model_visible_input"]["claim_payload"]:
            raise ValueError(f"PAIR_CLAIM_CONTENT_MISMATCH:{pair_key}")
        if pair[0]["model_visible_input"]["presentation"] != pair[1]["model_visible_input"]["presentation"]:
            raise ValueError(f"PAIR_PRESENTATION_MISMATCH:{pair_key}")
        if pair[0]["visible_lexical_bag_sha256"] != pair[1]["visible_lexical_bag_sha256"]:
            raise ValueError(f"PAIR_LEXICAL_BAG_NOT_IDENTICAL:{pair_key}")

    if carrier_by_split["DEVELOPMENT"] & carrier_by_split["OOD_HOLDOUT"]:
        raise ValueError("DEV_OOD_CARRIER_VOCAB_OVERLAP")

    nuisance_accuracy = _majority_accuracy(
        data, ("layout", "field_order", "carrier_name")
    )
    if nuisance_accuracy != 0.5:
        raise ValueError("NUISANCE_ONLY_DECODER_NOT_AT_CHANCE")

    semantic_accuracy = semantic_correct / len(data)
    if semantic_accuracy != 1.0:
        raise ValueError("SEMANTIC_TOPOLOGY_REFERENCE_NOT_PERFECT")

    return {
        "schema": SCHEMA,
        "pass": True,
        "rows": len(data),
        "splits": list(SPLITS),
        "families": FAMILY_COUNT,
        "counterfactual_pairs": len(pair_groups),
        "outcome_counts": dict(sorted(outcomes.items())),
        "pairwise_visible_lexical_bag_upper_bound": 0.5,
        "every_counterfactual_pair_has_identical_visible_lexical_bag": True,
        "development_ood_opaque_carrier_vocab_disjoint": True,
        "nuisance_only_majority_accuracy": nuisance_accuracy,
        "semantic_topology_reference_accuracy": semantic_accuracy,
        "target_and_split_hidden_from_model_visible_input": True,
        "training_eligible_rows": 0,
        "accepted_dataset_tokens_delta": 0,
        "model_runtime_credit": 0,
        "training_credit": 0,
    }


if __name__ == "__main__":
    print(cj(validate()))
