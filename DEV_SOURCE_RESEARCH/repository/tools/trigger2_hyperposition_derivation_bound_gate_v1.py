#!/usr/bin/env python3
"""Fail-closed pre-admission gate for derivation-bound Trigger-2 Hyperposition rows.

This gate recomputes the complete synthetic relation->transition chain from formal task-world
inputs and verifies the actual local deriver/labeler bytes. A regex-valid invented digest or
caller-supplied branch relation cannot satisfy it.

SOURCE/CANDIDATE GATE ONLY. Passing does not admit canonical dataset rows or mint training,
runtime, J-Space, HCU, EntityOS, truth, or effect credit.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tools import trigger2_hyperposition_causal_label_chain_v1 as chain

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_DERIVATION_BOUND_GATE/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
DERIVER_FILENAME = "trigger2_hyperposition_causal_label_chain_v1.py"
LABELER_FILENAME = "trigger2_hyperposition_reference_labelers_v1.py"
DERIVER_REPO_PATH = "tools/" + DERIVER_FILENAME
LABELER_REPO_PATH = "tools/" + LABELER_FILENAME


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_source_binding() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    deriver = here / DERIVER_FILENAME
    labeler = here / LABELER_FILENAME
    return {
        "deriver_path": DERIVER_REPO_PATH,
        "deriver_sha256": _sha256(deriver),
        "labeler_path": LABELER_REPO_PATH,
        "labeler_sha256": _sha256(labeler),
        "deriver_schema": chain.SCHEMA,
        "labeler_schema": chain.lab.SCHEMA,
    }


def _result(failures: list[str], recomputed: Any = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "canonical_dataset_admission": False,
        "training_credit_minted": 0,
        "accepted_dataset_tokens_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "failures": sorted(set(failures)),
        "recomputed_chain": recomputed,
    }


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if row.get("training_eligible") is not False:
        failures.append("TRAINING_ELIGIBLE_MUST_REMAIN_FALSE_AT_PRE_ADMISSION_GATE")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("CANONICAL_TRUTH_ALLOWED_MUST_BE_FALSE")
    if row.get("direct_effect_authority") is not False:
        failures.append("DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if row.get("model_visible_fields") != ["prompt"]:
        failures.append("ONLY_PROMPT_MAY_BE_MODEL_VISIBLE")
    if not isinstance(row.get("prompt"), str) or not row.get("prompt"):
        failures.append("PROMPT_REQUIRED")

    binding = row.get("source_binding")
    actual = current_source_binding()
    if not isinstance(binding, dict):
        failures.append("SOURCE_BINDING_REQUIRED")
    elif binding != actual:
        failures.append("SOURCE_BINDING_MISMATCH_ACTUAL_LOCAL_BYTES")

    world = row.get("formal_task_world_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    before = row.get("hyperposition_state_before_evaluator_only")
    claimed = row.get("causal_label_chain_target_evaluator_only")
    if world is None:
        failures.append("FORMAL_TASK_WORLD_REQUIRED")
    if event is None:
        failures.append("SYNTHETIC_TEST_EVENT_REQUIRED")
    if before is None:
        failures.append("HYPERPOSITION_STATE_BEFORE_REQUIRED")
    if claimed is None:
        failures.append("CAUSAL_LABEL_CHAIN_TARGET_REQUIRED")

    recomputed = None
    if not any(x.endswith("_REQUIRED") for x in failures):
        try:
            recomputed = chain.derive_label_chain(before, world, event)
        except Exception as exc:
            failures.append("CAUSAL_CHAIN_RECOMPUTE_REJECTED:" + type(exc).__name__)
        else:
            if claimed != recomputed:
                failures.append("CLAIMED_TARGET_DOES_NOT_MATCH_RECOMPUTED_CAUSAL_CHAIN")
            receipt = recomputed.get("relation_derivation_receipt", {})
            if receipt.get("canonical_truth_minted") is not False:
                failures.append("DERIVATION_RECEIPT_TRUTH_LEAK")
            if receipt.get("direct_effect_authority") is not False:
                failures.append("DERIVATION_RECEIPT_EFFECT_AUTHORITY_LEAK")
            target = recomputed.get("reference_target", {})
            if target.get("canonical_truth_minted") is not False:
                failures.append("REFERENCE_TARGET_TRUTH_LEAK")
            if target.get("direct_effect_authority") is not False:
                failures.append("REFERENCE_TARGET_EFFECT_AUTHORITY_LEAK")

    return _result(failures, recomputed)
