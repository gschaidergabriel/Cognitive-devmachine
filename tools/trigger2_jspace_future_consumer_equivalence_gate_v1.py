#!/usr/bin/env python3
"""Fail-closed source gate for Trigger-2 future-consumer-equivalence method rows.

This gate is deliberately NONPROMOTING. It validates the small METHOD_ONLY /
SYNTHETIC_HARD_NEGATIVE seed that teaches J-Space evidence boundaries. Passing
this gate cannot create positive J-Space labels, canonical dataset admission,
runtime evidence, or training credit.
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "CLAY_TRIGGER2_FUTURE_CONSUMER_EQUIVALENCE_GATE/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
TARGET_TYPE = "JSPACE_CAUSAL_METHOD_GUARD"
EXPECTED_FAMILIES = {
    "FCE_SAME_OUTPUT_DIFFERENT_FUTURES_F01": "SYNTHETIC_HARD_NEGATIVE",
    "FCE_DIFFERENT_SURFACE_SAME_FUTURE_F01": "METHOD_ONLY",
    "FCE_STEERING_SUCCESS_NO_MEDIATION_F01": "SYNTHETIC_HARD_NEGATIVE",
    "FCE_MEAN_SUCCESS_WORST_FAMILY_FAIL_F01": "SYNTHETIC_HARD_NEGATIVE",
    "FCE_GLOBAL_VECTOR_CONTEXT_FLIP_F01": "SYNTHETIC_HARD_NEGATIVE",
    "FCE_HOLDOUT_CONSUMER_POSTHOC_F01": "SYNTHETIC_HARD_NEGATIVE",
    "FCE_VARIABLE_BINDING_HEURISTIC_F01": "SYNTHETIC_HARD_NEGATIVE",
    "FCE_HYPERPOSITION_INTERFACE_ALTS_F01": "METHOD_ONLY",
}
_COMMITISH = re.compile(r"\b[0-9a-fA-F]{40,64}\b")
CAUSAL_PROMOTION_FIELDS = {
    "model_runtime_binding",
    "causal_receipt_sha256",
    "jspace_vector",
    "hidden_state_coordinate",
    "resolved_jspace_interface",
}


def _result(failures: list[str]) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": failures,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "positive_jspace_causal_credit_minted": 0,
        "runtime_credit_minted": 0,
        "training_credit_minted": 0,
        "evidence_boundary": "Source-method candidate validation only.",
    }


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    fam = row.get("family_id")
    if fam not in EXPECTED_FAMILIES:
        failures.append("FAMILY_NOT_IN_FROZEN_FCE_SEED")
    elif row.get("evidence_class") != EXPECTED_FAMILIES[fam]:
        failures.append("FAMILY_EVIDENCE_CLASS_MISMATCH")

    if row.get("reality_level") not in {"R2", "R3"}:
        failures.append("FCE_METHOD_REALITY_LEVEL_MUST_BE_R2_OR_R3")
    if row.get("fact_status") not in {"UNKNOWN", "NOT_APPLICABLE"}:
        failures.append("FCE_METHOD_ROW_CANNOT_ASSERT_MEASURED_FACT")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("CANONICAL_TRUTH_MUST_BE_FALSE")
    if row.get("direct_effect_authority") is not False:
        failures.append("DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if row.get("target_type") != TARGET_TYPE:
        failures.append("TARGET_TYPE_MUST_REMAIN_METHOD_GUARD")
    if row.get("split") != "TRAIN":
        failures.append("SOURCE_SEED_SPLIT_MUST_REMAIN_TRAIN")
    if row.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY":
        failures.append("FAMILY_PROVENANCE_SPLIT_UNIT_REQUIRED")
    if row.get("selected_using_holdout") is not False:
        failures.append("HOLDOUT_SELECTION_FORBIDDEN")
    if row.get("training_admission_scope") != "CANDIDATE_SOURCE_ONLY":
        failures.append("TRAINING_SCOPE_MUST_BE_CANDIDATE_SOURCE_ONLY")
    if row.get("positive_jspace_label") is not False:
        failures.append("POSITIVE_JSPACE_LABEL_FORBIDDEN")
    if row.get("accepted_dataset_tokens_minted") != 0:
        failures.append("ACCEPTED_DATASET_TOKENS_MUST_BE_ZERO")
    if row.get("training_credit_minted") != 0:
        failures.append("TRAINING_CREDIT_MUST_BE_ZERO")

    ancestry = row.get("provenance_ancestry_id")
    if not isinstance(ancestry, str) or not ancestry:
        failures.append("PROVENANCE_ANCESTRY_ID_REQUIRED")
    for key in ("prompt", "target"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            failures.append(key.upper() + "_REQUIRED")
        elif _COMMITISH.search(value):
            failures.append(key.upper() + "_MUST_NOT_MEMORIZE_TRANSIENT_COMMIT_IDENTITY")

    leaked = sorted(CAUSAL_PROMOTION_FIELDS & set(row))
    if leaked:
        failures.append("NONPROMOTING_METHOD_ROW_CONTAINS_CAUSAL_PROMOTION_FIELDS:" + ",".join(leaked))

    return _result(failures)


def adjudicate_seed(rows: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(rows, list):
        return _result(["SEED_LIST_REQUIRED"])
    if len(rows) != len(EXPECTED_FAMILIES):
        failures.append("SEED_ROW_COUNT_MISMATCH")

    seen_families: list[str] = []
    seen_ancestries: list[str] = []
    row_failures: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        result = adjudicate(row)
        if not result["pass"]:
            row_failures.append({"index": idx, "failures": result["failures"]})
        if isinstance(row, dict):
            seen_families.append(str(row.get("family_id")))
            seen_ancestries.append(str(row.get("provenance_ancestry_id")))

    if set(seen_families) != set(EXPECTED_FAMILIES):
        failures.append("FROZEN_FAMILY_SET_MISMATCH")
    if len(seen_families) != len(set(seen_families)):
        failures.append("DUPLICATE_FAMILY_ID")
    if len(seen_ancestries) != len(set(seen_ancestries)):
        failures.append("DUPLICATE_PROVENANCE_ANCESTRY")
    if row_failures:
        failures.append("ONE_OR_MORE_ROWS_FAIL")

    out = _result(failures)
    out["row_failures"] = row_failures
    out["families_observed"] = sorted(set(seen_families))
    out["source_seed_rows"] = len(rows)
    return out
