#!/usr/bin/env python3
"""Successor candidate gate for Trigger-2 deterministic synthetic supervision.

v2 preserves v1's evidence boundary while adding one explicit class for synthetic
worlds whose target state is computed by a version/hash-bound deterministic labeler.
This permits positive Hyperposition/GRF training examples without pretending that a
synthetic resolution is real-world causal evidence.

This gate still cannot write the canonical dataset or mint runtime/training credit.
"""
from __future__ import annotations
import re
from typing import Any

SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE_GATE/v2"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_CLASSES = {
    "METHOD_ONLY",
    "SYNTHETIC_HARD_NEGATIVE",
    "SYNTHETIC_DETERMINISTIC_LABEL",
    "SOURCE_OBSERVED",
    "COMPONENT_CAUSAL_MEASURED",
    "CAUSAL_VERIFIED",
}
REALITY_LEVELS = {f"R{i}" for i in range(7)}
JSPACE_TARGET_TYPES = {"JSPACE_VECTOR_EFFECT", "ABSTRACT_STATE_CONTROL", "HIDDEN_STATE_COORDINATE"}


def _sha(x: Any) -> bool:
    return isinstance(x, str) and bool(_SHA256.fullmatch(x.lower()))


def _synthetic_binding_ok(row: dict[str, Any], failures: list[str]) -> bool:
    binding = row.get("synthetic_labeler_binding")
    if not isinstance(binding, dict):
        failures.append("SYNTHETIC_LABELER_BINDING_REQUIRED")
        return False
    for k in ("labeler_id", "labeler_version"):
        if not isinstance(binding.get(k), str) or not binding.get(k):
            failures.append("SYNTHETIC_LABELER_BINDING_MISSING:" + k)
    for k in ("labeler_sha256", "generator_sha256"):
        if not _sha(binding.get(k)):
            failures.append("SYNTHETIC_LABELER_BINDING_SHA256_INVALID:" + k)
    if binding.get("synthetic_world") is not True:
        failures.append("SYNTHETIC_WORLD_TRUE_REQUIRED")
    if binding.get("source_real_world_claim") is not False:
        failures.append("SYNTHETIC_SOURCE_REAL_WORLD_CLAIM_MUST_BE_FALSE")
    if binding.get("resolution_basis") != "MECHANICALLY_GENERATED_TYPED_RELATION":
        failures.append("SYNTHETIC_RESOLUTION_BASIS_INVALID")
    return not any(f.startswith("SYNTHETIC_") for f in failures)


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        row = {}
        failures.append("ROW_OBJECT_REQUIRED")
    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")

    ev = row.get("evidence_class")
    if ev not in EVIDENCE_CLASSES:
        failures.append("EVIDENCE_CLASS_INVALID")
    level = row.get("reality_level")
    if level not in REALITY_LEVELS:
        failures.append("REALITY_LEVEL_INVALID")
    if not isinstance(row.get("family_id"), str) or not row.get("family_id"):
        failures.append("FAMILY_ID_REQUIRED")
    if not isinstance(row.get("provenance_ancestry_id"), str) or not row.get("provenance_ancestry_id"):
        failures.append("PROVENANCE_ANCESTRY_ID_REQUIRED")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("TRAINING_ROW_CANNOT_MINT_CANONICAL_TRUTH")
    if row.get("direct_effect_authority") is not False:
        failures.append("TRAINING_ROW_CANNOT_HAVE_DIRECT_EFFECT_AUTHORITY")

    fact_status = row.get("fact_status")
    if fact_status not in {"UNKNOWN", "MEASURED", "VERIFIED", "NOT_APPLICABLE"}:
        failures.append("FACT_STATUS_INVALID")
    if ev in {"METHOD_ONLY", "SYNTHETIC_HARD_NEGATIVE", "SYNTHETIC_DETERMINISTIC_LABEL"} and fact_status not in {"UNKNOWN", "NOT_APPLICABLE"}:
        failures.append("SYNTHETIC_OR_METHOD_ROW_CANNOT_ASSERT_FACT")
    if level in {"R2", "R3"} and fact_status in {"MEASURED", "VERIFIED"}:
        failures.append("GENERATED_OR_COUNTERREALITY_CANNOT_ASSERT_MEASURED_FACT")

    if ev == "SYNTHETIC_DETERMINISTIC_LABEL":
        _synthetic_binding_ok(row, failures)

    hp = row.get("hyperposition")
    if hp is not None:
        if not isinstance(hp, dict):
            failures.append("HYPERPOSITION_OBJECT_REQUIRED")
        else:
            alts = hp.get("alternatives")
            if not isinstance(alts, list) or len(alts) < 2 or len(set(map(str, alts))) != len(alts):
                failures.append("HYPERPOSITION_ALTERNATIVES_INVALID")
            status = hp.get("resolution_status")
            if status not in {"UNRESOLVED", "RESOLVED_BY_EVIDENCE"}:
                failures.append("HYPERPOSITION_RESOLUTION_STATUS_INVALID")
            if status == "UNRESOLVED" and hp.get("resolved_alternative") is not None:
                failures.append("UNRESOLVED_HYPERPOSITION_CANNOT_HAVE_RESOLVED_ALTERNATIVE")
            if status == "RESOLVED_BY_EVIDENCE":
                if ev in {"COMPONENT_CAUSAL_MEASURED", "CAUSAL_VERIFIED"}:
                    pass
                elif ev == "SYNTHETIC_DETERMINISTIC_LABEL":
                    _synthetic_binding_ok(row, failures)
                else:
                    failures.append("HYPERPOSITION_RESOLUTION_REQUIRES_CAUSAL_OR_DETERMINISTIC_SYNTHETIC_LABEL")
                if hp.get("resolved_alternative") not in (alts or []):
                    failures.append("RESOLVED_ALTERNATIVE_NOT_IN_SET")

    target_type = row.get("target_type")
    if not isinstance(target_type, str) or not target_type:
        failures.append("TARGET_TYPE_REQUIRED")
    if target_type in JSPACE_TARGET_TYPES:
        if ev not in {"COMPONENT_CAUSAL_MEASURED", "CAUSAL_VERIFIED"}:
            failures.append("JSPACE_TARGET_REQUIRES_CAUSAL_EVIDENCE")
        binding = row.get("model_runtime_binding")
        if not isinstance(binding, dict):
            failures.append("JSPACE_MODEL_RUNTIME_BINDING_REQUIRED")
        else:
            for k in ("model_id", "model_revision", "weights_sha256", "runtime_id", "runtime_revision"):
                v = binding.get(k)
                if not isinstance(v, str) or not v:
                    failures.append("JSPACE_BINDING_MISSING:" + k)
            if binding.get("weights_sha256") is not None and not _sha(binding.get("weights_sha256")):
                failures.append("JSPACE_WEIGHTS_SHA256_INVALID")
        receipt = row.get("causal_receipt_sha256")
        if not _sha(receipt):
            failures.append("JSPACE_CAUSAL_RECEIPT_SHA256_REQUIRED")
        if row.get("source_model_family") != row.get("target_model_family"):
            failures.append("CROSS_MODEL_JSPACE_LABEL_TRANSFER_FORBIDDEN")

    split = row.get("split")
    if split not in {"TRAIN", "VALIDATION", "HOLDOUT"}:
        failures.append("SPLIT_INVALID")
    if row.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY":
        failures.append("FAMILY_PROVENANCE_SPLIT_UNIT_REQUIRED")
    if row.get("selected_using_holdout") is not False:
        failures.append("HOLDOUT_SELECTION_FORBIDDEN")

    return {
        "schema": SCHEMA,
        "candidate_admission_pass": not failures,
        "failures": sorted(set(failures)),
        "canonical_dataset_write_performed": False,
        "canonical_truth_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "synthetic_resolution_credit_scope": "training-target structure only; never real-world causal/factual credit",
        "evidence_boundary": "Candidate-row validation only. Canonical dataset admission remains the evidence-qualified Forge/Distillery/TrainingTrace path."
    }
