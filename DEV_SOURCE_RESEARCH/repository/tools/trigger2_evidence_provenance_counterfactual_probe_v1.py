#!/usr/bin/env python3
"""Trigger-2 source-only evidence-provenance counterfactual probe.

This probe is a METHOD_ONLY / evaluator-blueprint artifact. It does not generate
training-admitted rows and does not execute providers, models, GRID, effects, or
canonical admission. It targets one failure mode exposed by Trigger-2 V66:
identical claim content must not receive the same evidentiary scope when one
carrier is bound to an observed/minted authority event and the other is only a
caller/model assertion.

The model-visible projection contains the provenance facts needed for the
cognitive decision, while target/evaluator fields stay outside that projection.
Nuisance layout/order/carrier labels are exactly counterbalanced across outcomes.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER2_EVIDENCE_PROVENANCE_COUNTERFACTUAL_PROBE/v1"
ROW_SCHEMA = "CLAY_TRIGGER2_EVIDENCE_PROVENANCE_COUNTERFACTUAL_ROW/v1"
OUTCOMES = ("BOUND_EVIDENCE_CANDIDATE", "CLAIM_ONLY_NO_PROMOTION")


def cj(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def dg(value: Any) -> str:
    return sha256(cj(value).encode("utf-8")).hexdigest()


FAMILIES = (
    {
        "family": "PHYSICAL_COHORT_WITNESS",
        "process_id": "ZECP09",
        "claim": {"physical_predicates": "ALL_TRUE", "member_count": 10},
        "bound": {
            "producer_surface": "controller-observation",
            "mint_event": "barrier-observation-event",
            "bindings": ["node", "pid", "read_receipt", "snapshot", "barrier"],
        },
        "claim_only": {
            "producer_surface": "caller-payload",
            "mint_event": None,
            "bindings": ["node", "pid", "read_receipt", "snapshot", "barrier"],
        },
        "missing": "physical_observation_provenance",
    },
    {
        "family": "MODEL_INVOCATION_OCCURRENCE",
        "process_id": "ZECP09",
        "claim": {"call_content_digest": "sha256:equal-content", "output_digest": "sha256:equal-output"},
        "bound": {
            "producer_surface": "controller-executor",
            "mint_event": "precall-launch-plus-postcall-observation",
            "bindings": ["launch_descriptor", "executor_observation", "node_admission", "generation"],
        },
        "claim_only": {
            "producer_surface": "content-envelope",
            "mint_event": None,
            "bindings": ["call_content", "output_content"],
        },
        "missing": "invocation_occurrence_provenance",
    },
    {
        "family": "CLAUDE_TOOL_RETURN",
        "process_id": "ZECP14",
        "claim": {"statement": "operation completed", "result_digest": "sha256:same-result-text"},
        "bound": {
            "producer_surface": "bridge-tool-return",
            "mint_event": "tool-result-receipt",
            "bindings": ["bridge_request", "tool_call", "tool_result", "return_event"],
        },
        "claim_only": {
            "producer_surface": "assistant-text-return",
            "mint_event": None,
            "bindings": ["bridge_request", "assistant_text"],
        },
        "missing": "tool_result_receipt",
    },
    {
        "family": "EXTERNAL_EFFECT_OUTCOME",
        "process_id": "ZECP18",
        "claim": {"statement": "effect succeeded", "effect_request_digest": "sha256:same-effect"},
        "bound": {
            "producer_surface": "effect-journal",
            "mint_event": "verified-effect-outcome",
            "bindings": ["effect_request", "journal_entry", "verified_outcome"],
        },
        "claim_only": {
            "producer_surface": "transport-session",
            "mint_event": None,
            "bindings": ["effect_request", "transport_timeout", "assistant_guess"],
        },
        "missing": "verified_external_outcome",
    },
)

NUISANCE = (
    ("layout-a", "forward", "carrier-alpha"),
    ("layout-a", "reverse", "carrier-beta"),
    ("layout-b", "forward", "carrier-beta"),
    ("layout-b", "reverse", "carrier-alpha"),
)


def rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for family in FAMILIES:
        claim_digest = dg(family["claim"])
        for idx, (layout, order, carrier_name) in enumerate(NUISANCE, 1):
            # Flip which nuisance row receives which outcome so every nuisance value is
            # exactly balanced across outcomes within the full probe.
            bound_first = idx % 2 == 1
            variants = (
                ("BOUND", family["bound"], "BOUND_EVIDENCE_CANDIDATE", []),
                ("CLAIM", family["claim_only"], "CLAIM_ONLY_NO_PROMOTION", [family["missing"]]),
            )
            if not bound_first:
                variants = tuple(reversed(variants))
            for ordinal, (kind, provenance, outcome, unknowns) in enumerate(variants):
                row_id = f"EPCF-{family['family']}-{idx:02d}-{ordinal}"
                visible = {
                    "schema": "EVIDENCE_PROVENANCE_DECISION_INPUT/v1",
                    "process_id": family["process_id"],
                    "claim_payload": deepcopy(family["claim"]),
                    "claim_payload_sha256": claim_digest,
                    "provenance": deepcopy(provenance),
                    "presentation": {
                        "layout": layout,
                        "field_order": order,
                        "carrier_name": carrier_name,
                    },
                    "requested_scope": "PROMOTION_BEARING_EVIDENCE",
                }
                target = {
                    "evidence_scope_decision": outcome,
                    "unknowns": unknowns,
                    "canonical_truth_minted": False,
                    "effect_authority_minted": False,
                }
                out.append(
                    {
                        "schema": ROW_SCHEMA,
                        "row_id": row_id,
                        "family": family["family"],
                        "pair_key": f"{family['family']}:{idx:02d}",
                        "evidence_class": "METHOD_ONLY",
                        "training_eligible": False,
                        "accepted_dataset_credit": 0,
                        "model_visible_input": visible,
                        "model_visible_input_sha256": dg(visible),
                        "evaluator_target": target,
                        "outcome_class_evaluator_only": outcome,
                        "variant_kind_evaluator_only": kind,
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
    if len(data) != 32:
        raise ValueError("ROW_COUNT_MISMATCH")

    outcomes = Counter(row["outcome_class_evaluator_only"] for row in data)
    if outcomes != Counter({OUTCOMES[0]: 16, OUTCOMES[1]: 16}):
        raise ValueError("OUTCOME_BALANCE_MISMATCH")

    pair_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in data:
        if row.get("training_eligible") is not False or row.get("accepted_dataset_credit") != 0:
            raise ValueError("PROMOTION_FENCE_VIOLATION")
        if "evaluator_target" in row["model_visible_input"] or "outcome_class_evaluator_only" in row["model_visible_input"]:
            raise ValueError("TARGET_LEAKAGE")
        if row["model_visible_input_sha256"] != dg(row["model_visible_input"]):
            raise ValueError("VISIBLE_DIGEST_MISMATCH")
        pair_groups[row["pair_key"]].append(row)

    if len(pair_groups) != 16:
        raise ValueError("PAIR_COUNT_MISMATCH")
    for pair_key, pair in pair_groups.items():
        if len(pair) != 2:
            raise ValueError(f"PAIR_SIZE_MISMATCH:{pair_key}")
        if {row["outcome_class_evaluator_only"] for row in pair} != set(OUTCOMES):
            raise ValueError(f"PAIR_OUTCOME_MISMATCH:{pair_key}")
        claim_digests = {row["model_visible_input"]["claim_payload_sha256"] for row in pair}
        if len(claim_digests) != 1:
            raise ValueError(f"PAIR_CLAIM_CONTENT_MISMATCH:{pair_key}")
        presentations = {cj(row["model_visible_input"]["presentation"]) for row in pair}
        if len(presentations) != 1:
            raise ValueError(f"PAIR_PRESENTATION_MISMATCH:{pair_key}")

    nuisance_accuracy = _majority_accuracy(data, ("layout", "field_order", "carrier_name"))
    if nuisance_accuracy != 0.5:
        raise ValueError("NUISANCE_ONLY_DECODER_NOT_AT_CHANCE")

    return {
        "schema": SCHEMA,
        "pass": True,
        "rows": len(data),
        "families": len(FAMILIES),
        "counterfactual_pairs": len(pair_groups),
        "outcome_counts": dict(sorted(outcomes.items())),
        "nuisance_only_majority_accuracy": nuisance_accuracy,
        "claim_content_equal_within_every_pair": True,
        "target_hidden_from_model_visible_input": True,
        "training_eligible_rows": 0,
        "accepted_dataset_tokens_delta": 0,
        "runtime_credit": 0,
        "training_credit": 0,
    }


if __name__ == "__main__":
    print(cj(validate()))
