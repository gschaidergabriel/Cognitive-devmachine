from __future__ import annotations

from typing import Any


class GlobalWorkspaceReentryContractError(ValueError):
    pass


def _fail(code: str) -> None:
    raise GlobalWorkspaceReentryContractError(code)


def validate(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema") != "GLOBAL_WORKSPACE_REENTRY_RECEIPT_CONTRACT/v1":
        _fail("SCHEMA_MISMATCH")
    if value.get("receipt_schema") != "GLOBAL_WORKSPACE_REENTRY_RECEIPT/v1":
        _fail("RECEIPT_SCHEMA_MISMATCH")

    authority = value.get("authority") or {}
    expected_bindings = {
        "census_schema": "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1",
        "abi_schema": "COGNITIVE_PROCESS_ABI/v1",
        "workspace_process": "ZECP10",
        "claude_handoff_process": "ZECP13",
        "claude_return_process": "ZECP14",
        "jspace_research_process": "ZECP20",
    }
    for key, expected in expected_bindings.items():
        if authority.get(key) != expected:
            _fail(f"AUTHORITY_BINDING_MISMATCH:{key}")
    if authority.get("free_only") is not True:
        _fail("FREE_ONLY_REQUIRED")

    controls = set(value.get("required_control_binding") or [])
    required_controls = {
        "preregistration_ref", "matched_control_ref", "treatment_execution_ref", "control_execution_ref",
        "comparison_metric", "comparison_direction", "measured_treatment_value", "measured_control_value",
        "measured_delta", "off_target_regression", "control_match_manifest",
    }
    if not required_controls.issubset(controls):
        _fail("MATCHED_CONTROL_BINDING_INCOMPLETE")

    match = set(value.get("control_match_manifest_required") or [])
    if "difference_is_declared_transfer_intervention" not in match:
        _fail("INTERVENTION_DIFFERENCE_NOT_ISOLATED")

    if value.get("allowed_causal_credit") != ["NONE", "OBSERVABLE_WORKSPACE_REENTRY"]:
        _fail("CAUSAL_CREDIT_SCOPE_INFLATED")

    zero_text = "\n".join(value.get("automatic_zero_credit_conditions") or [])
    for required in (
        "matched_control_ref missing",
        "preregistration_ref missing",
        "comparison metric selected after outcome exposure",
        "stale generation or stale workspace epoch",
        "observed_downstream_change is FALSE or UNKNOWN",
        "activation-level or hidden-state access claimed for Claude Code",
    ):
        if required not in zero_text:
            _fail(f"ZERO_CREDIT_GUARD_MISSING:{required}")

    ceiling = value.get("jspace_claim_ceiling") or {}
    if ceiling.get("receipt_maximum") != "OBSERVABLE_WORKSPACE_REENTRY":
        _fail("RECEIPT_JSPACE_CLAIM_INFLATION")
    if ceiling.get("model_specific_causal_jspace") != "REQUIRES_SEPARATE_EXACT_MODEL_RUNTIME_INTERVENTION_RECEIPT":
        _fail("MODEL_SPECIFIC_JSPACE_SEPARATE_RECEIPT_REQUIRED")
    if ceiling.get("claude_hidden_activation_access") != "UNKNOWN_UNLESS_EXACTLY_EXPOSED_AND_OBSERVED":
        _fail("CLAUDE_HIDDEN_ACCESS_CLAIM_CEILING_MISSING")
    if ceiling.get("frozen_v1_negative_evidence") != "MUST_REMAIN_PRESERVED":
        _fail("FROZEN_V1_NEGATIVE_EVIDENCE_MUST_BE_PRESERVED")

    fences = value.get("authority_fences") or {}
    if fences.get("real_effect_path") != "EffectGate+EffectJournal_ONLY":
        _fail("REAL_EFFECT_PATH_MISMATCH")
    if fences.get("capability_self_grant") != "FORBIDDEN":
        _fail("CAPABILITY_SELF_GRANT_MUST_BE_FORBIDDEN")
    if fences.get("model_grid_claude_outputs") != "CANDIDATE_PROJECTION_MEASUREMENT_ONLY":
        _fail("MODEL_OUTPUT_AUTHORITY_INFLATION")
    if fences.get("unknown_outcome") != "UNKNOWN_NOT_FALSE_NOT_SUCCESS":
        _fail("UNKNOWN_OUTCOME_COLLAPSED")

    discriminators = {d.get("id") for d in value.get("acceptance_discriminators") or []}
    expected_discriminators = {
        "GWR-D1-MATCHED-CONTROL-REQUIRED", "GWR-D2-PREDECLARED-METRIC",
        "GWR-D3-STALE-REENTRY", "GWR-D4-CLAUDE-CLAIM-CEILING",
        "GWR-D5-OFF-TARGET-REGRESSION", "GWR-D6-NEGATIVE-EVIDENCE",
    }
    if discriminators != expected_discriminators:
        _fail("DISCRIMINATOR_SET_MISMATCH")

    credit = value.get("credit_boundary") or {}
    for key in (
        "observable_workspace_reentry_runtime_credit", "claude_bridge_runtime_credit",
        "jspace_model_runtime_credit", "whole_hcu_runtime_credit",
        "whole_entityos_runtime_credit", "training_credit",
    ):
        if credit.get(key) != 0:
            _fail(f"RUNTIME_CREDIT_INFLATION:{key}")

    return {
        "ok": True,
        "receipt_schema": value["receipt_schema"],
        "control_binding_count": len(controls),
        "discriminator_count": len(discriminators),
        "maximum_causal_credit": ceiling["receipt_maximum"],
        "next_exact_gate": value.get("next_exact_gate"),
    }
