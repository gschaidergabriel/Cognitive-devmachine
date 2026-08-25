from __future__ import annotations

import hashlib

from tools import trigger1_internal_state_specificity_gate_v2 as gate


def h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def candidate() -> dict:
    commands = {
        target: {
            "command_id_sha256": h("cmd-" + target),
            "semantic_vector_sha256": h("vec-" + target),
            "nuisance_residualized": True,
        }
        for target in gate.TARGETS
    }
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    rows = []
    for family, rotation in enumerate(rotations):
        for target in gate.TARGETS:
            baseline = {
                "runtime_receipt_sha256": h(f"base-runtime-{family}-{target}"),
                "probe_receipt_sha256": h(f"base-probe-{family}-{target}"),
                "output_metric_receipt_sha256": h(f"base-output-{family}-{target}"),
                "internal_scores": {name: 0.0 for name in gate.TARGETS},
                "target_output_score": 0.0,
            }
            applications = {}
            for applied in gate.TARGETS:
                scores = {name: 0.0 for name in gate.TARGETS}
                scores[applied] = 1.0
                applications[applied] = {
                    "command_id_sha256": commands[applied]["command_id_sha256"],
                    "semantic_vector_sha256": commands[applied]["semantic_vector_sha256"],
                    "runtime_receipt_sha256": h(f"runtime-{family}-{target}-{applied}"),
                    "probe_receipt_sha256": h(f"probe-{family}-{target}-{applied}"),
                    "output_metric_receipt_sha256": h(f"output-{family}-{target}-{applied}"),
                    "internal_scores": scores,
                    "target_output_score": 0.8 if applied == target else 0.05,
                    "off_target_internal_drift": 0.02,
                }
            rows.append({
                "case_id": f"family-{family}-{target}",
                "case_identity_sha256": h(f"case-{family}-{target}"),
                "prompt_sha256": h(f"prompt-{family}"),
                "semantic_target": target,
                "output_code_identity": rotation[target],
                "baseline": baseline,
                "applications": applications,
            })
    return {
        "internal_state_specificity_attestation": {
            "schema": gate.SCHEMA,
            "abstract_state_challenge_sha256": h("challenge"),
            "v12_candidate_sha256": h("v12-candidate"),
            "protocol_sha256": h("protocol"),
            "frozen_before_holdout": True,
            "thresholds_selected_on": "CALIBRATION_ONLY",
            "independent_probe": {
                "uses_output_tokens": False,
                "uses_steering_basis_families": False,
                "fit_split": "CALIBRATION_ONLY",
                "steering_layer": 20,
                "probe_layer": 24,
                "probe_definition_sha256": h("probe-definition"),
            },
            "commands": commands,
            "thresholds": {
                "min_internal_match_vs_baseline": 0.5,
                "min_internal_match_vs_best_nonmatching": 0.5,
                "min_behavior_match_vs_best_nonmatching": 0.5,
                "max_nonmatching_behavior_uplift_vs_baseline": 0.1,
                "max_off_target_internal_drift": 0.05,
            },
            "holdout_rows": rows,
        }
    }


def test_valid_matrix_is_reconstructed_and_nonminting():
    result = gate.adjudicate(candidate())
    assert result["internal_state_specificity_candidate"], result["failures"]
    assert result["generic_compliance_rejected_by_same_case_competition"]
    assert not result["canonical_credit_minted"] and not result["jspace_model_runtime_credit"]


def test_generic_compliance_behavior_fails_same_case_competition():
    value = candidate()
    for row in value["internal_state_specificity_attestation"]["holdout_rows"]:
        for app in row["applications"].values():
            app["target_output_score"] = 0.6
    result = gate.adjudicate(value)
    assert not result["internal_state_specificity_candidate"]
    assert any("TARGET_SPECIFIC_INTERNAL_STATE_THRESHOLD_FAILED" in item for item in result["failures"])


def test_behavior_only_without_internal_state_specificity_fails():
    value = candidate()
    for row in value["internal_state_specificity_attestation"]["holdout_rows"]:
        for app in row["applications"].values():
            app["internal_scores"] = {name: 0.2 for name in gate.TARGETS}
    assert not gate.adjudicate(value)["internal_state_specificity_candidate"]


def test_probe_cannot_use_output_tokens():
    value = candidate()
    value["internal_state_specificity_attestation"]["independent_probe"]["uses_output_tokens"] = True
    assert "PROBE_MUST_NOT_USE_OUTPUT_TOKENS" in gate.adjudicate(value)["failures"]


def test_probe_cannot_reuse_steering_basis_families():
    value = candidate()
    value["internal_state_specificity_attestation"]["independent_probe"]["uses_steering_basis_families"] = True
    assert "PROBE_MUST_NOT_USE_STEERING_BASIS_FAMILIES" in gate.adjudicate(value)["failures"]


def test_probe_must_be_downstream():
    value = candidate()
    value["internal_state_specificity_attestation"]["independent_probe"]["probe_layer"] = 20
    assert "INDEPENDENT_DOWNSTREAM_PROBE_LAYER_REQUIRED" in gate.adjudicate(value)["failures"]


def test_target_code_counterbalance_is_reconstructed():
    value = candidate()
    value["internal_state_specificity_attestation"]["holdout_rows"][0]["output_code_identity"] = "C"
    assert "HOLDOUT_TARGET_X_CODE_MUST_BE_EXACT_ONE_EACH" in gate.adjudicate(value)["failures"]


def test_command_and_vector_identity_are_bound_per_application():
    value = candidate()
    app = value["internal_state_specificity_attestation"]["holdout_rows"][0]["applications"]["AFFIRMATIVE"]
    app["semantic_vector_sha256"] = h("wrong")
    result = gate.adjudicate(value)
    assert not result["internal_state_specificity_candidate"]
    assert any("VECTOR_ID_MISMATCH" in item for item in result["failures"])


def test_non_residualized_command_fails():
    value = candidate()
    value["internal_state_specificity_attestation"]["commands"]["NEUTRAL"]["nuisance_residualized"] = False
    assert "NUISANCE_RESIDUALIZATION_REQUIRED:NEUTRAL" in gate.adjudicate(value)["failures"]
