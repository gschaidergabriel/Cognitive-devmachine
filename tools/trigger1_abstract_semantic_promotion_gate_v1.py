#!/usr/bin/env python3
"""Final hard semantic-abstraction promotion gate for Trigger-1.

Consumes an already adjudicated v8 verdict plus exact abstract/counterbalanced prompt
coverage and the raw three-way scope-equivalence payload. It is intentionally
non-minting: a positive result is a scientific promotion candidate only.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from tools import trigger1_abstract_state_counterbalance_v1 as design
from tools import trigger1_intervention_scope_equivalence_v1 as scope

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_SEMANTIC_PROMOTION_INPUT/v1"
RESULT_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_SEMANTIC_PROMOTION_GATE/v1"


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    v8 = payload.get("v8_verdict")
    if not isinstance(v8, dict):
        raise ValueError("V8_VERDICT_REQUIRED")
    design_receipt = design.validate()
    declared_design = payload.get("abstract_design")
    if not isinstance(declared_design, dict):
        raise ValueError("ABSTRACT_DESIGN_BINDING_REQUIRED")

    expected_prompt_hashes = sorted(row["prompt_sha256"] for row in design.build_rows())
    observed_prompt_hashes = declared_design.get("observed_prompt_sha256")
    if not isinstance(observed_prompt_hashes, list):
        raise ValueError("OBSERVED_PROMPT_HASH_ARRAY_REQUIRED")
    observed_prompt_hashes = sorted(str(x) for x in observed_prompt_hashes)

    design_ok = (
        declared_design.get("design_receipt_sha256") == design_receipt["design_receipt_sha256"]
        and declared_design.get("rows_sha256") == design_receipt["rows_sha256"]
        and observed_prompt_hashes == expected_prompt_hashes
    )

    scope_payload = payload.get("scope_equivalence_payload")
    if not isinstance(scope_payload, dict):
        raise ValueError("SCOPE_EQUIVALENCE_PAYLOAD_REQUIRED")
    scope_result = scope.adjudicate(scope_payload)
    scope_ok = scope_result["classification"] == "SCOPE_INVARIANT_SEMANTIC_RESPONSE_EQUIVALENCE"

    nuisance = payload.get("nuisance_control")
    if not isinstance(nuisance, dict):
        raise ValueError("NUISANCE_CONTROL_REQUIRED")
    nuisance_ok = (
        nuisance.get("semantic_target_selectivity_pass") is True
        and nuisance.get("affect_nuisance_invariance_pass") is True
        and nuisance.get("surface_form_invariance_pass") is True
        and nuisance.get("presentation_position_invariance_pass") is True
    )

    v8_ok = (
        v8.get("scientifically_independent_vector_candidate") is True
        and v8.get("preregistration_runtime_binding_pass") is True
    )

    failures = []
    if not v8_ok:
        failures.append("V8_SCIENTIFIC_AND_PREREG_BINDING_REQUIRED")
    if not design_ok:
        failures.append("EXACT_ABSTRACT_DESIGN_AND_PROMPT_UNIVERSE_BINDING_REQUIRED")
    if not scope_ok:
        failures.append("THREE_WAY_SCOPE_INVARIANT_RESPONSE_EQUIVALENCE_REQUIRED")
    if not nuisance_ok:
        failures.append("COUNTERBALANCED_NUISANCE_INVARIANCE_REQUIRED")

    promoted = not failures
    result = {
        "schema": RESULT_SCHEMA,
        "v8_scientific_prereg_pass": v8_ok,
        "abstract_design_binding_pass": design_ok,
        "scope_invariant_response_equivalence_pass": scope_ok,
        "counterbalanced_nuisance_invariance_pass": nuisance_ok,
        "abstract_semantic_jspace_candidate": promoted,
        "failures": failures,
        "design_receipt_sha256": design_receipt["design_receipt_sha256"],
        "scope_adjudication_receipt_sha256": scope_result["adjudication_receipt_sha256"],
        "causal_identity_claim_allowed": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "Positive status means the v8 causal/prereg chain also survived a lexically-disjoint, "
            "model-label-free, compliance-free, counterbalanced prompt universe; semantic effects "
            "were invariant to affect/surface/position nuisance; and last-token versus broadcast "
            "interventions were response-equivalent at the frozen metric. It does not prove literal "
            "mechanistic identity and mints no canonical/runtime/product/training credit by itself."
        ),
    }
    result["promotion_receipt_sha256"] = canonical_sha(result)
    return result
