from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_jspace_promotion_gate_v5 as gate

HEX64 = "a" * 64
HEX64_B = "b" * 64


def complete_v5_candidate() -> dict:
    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "vector_derivation": {
            "model_facing_label_free": True,
            "lexically_disjoint_basis_families": True,
            "lexical_nuisance_projection_or_control": True,
            "lexical_nuisance_receipt_sha256": HEX64,
        },
        "controls": {
            "LABEL_ONLY_NUISANCE_VECTOR": {"runtime_receipt_sha256": HEX64},
        },
        "calibration": {
            "family_id": "cal-family",
            "semantic_target_x_output_code_factorial": True,
            "residual_norm_relative_intervention": True,
            "operating_point_selected_on_calibration_only": True,
            "operating_point_receipt_sha256": HEX64,
        },
        "holdout": {
            "family_id": "hold-family",
            "metric_definition_sha256": HEX64,
            "semantic_target_x_output_code_factorial": True,
            "per_family_semantic_target_interaction": True,
            "operating_point_frozen_before_holdout": True,
            "cross_family_direction_coherence_test": True,
            "cross_family_direction_coherence_receipt_sha256": HEX64,
            "off_target_drift_test": True,
            "off_target_drift_within_preregistered_threshold": True,
            "off_target_drift_receipt_sha256": HEX64,
        },
        "intervention": {
            "residual_norm_ratio": 0.05,
            "token_scope": "ALL_PROMPT_TOKENS",
            "scope_classification": "NATIVE_CVEC_ALL_PROMPT_TOKENS",
            "strict_last_token_replication_claimed": False,
        },
        "measurement_protocol": {
            "frozen_before_holdout": True,
            "protocol_sha256": HEX64,
            "preregistered_off_target_drift_threshold": 0.10,
        },
    }


def _row(split: str, family: str, case_index: int, target: str, code: str) -> dict:
    baseline = 0.1 * case_index
    effect = {"AFFIRMATIVE": 1.0, "NEGATIVE": -0.5, "NEUTRAL": 0.0}[target]
    scores = {
        "BASELINE": baseline,
        "+VECTOR": baseline + effect,
        "SIGN_FLIP": baseline - effect,
        "NULL_VECTOR": baseline,
        "ORTHOGONAL_SAME_NORM": baseline + 0.01,
        "PERMUTED_SAME_NORM": baseline - 0.01,
    }
    receipts = {
        control: gate._canonical_sha256({"split": split, "case": case_index, "control": control})
        for control in gate.v4.REQUIRED_CONTROLS
    }
    return {
        "split": split,
        "family_id": family,
        "case_id": f"{split.lower()}-{case_index}",
        "seed": 1000 + case_index,
        "prompt_sha256": gate._canonical_sha256({"split": split, "case": case_index, "prompt": True}),
        "semantic_target": target,
        "output_code_identity": code,
        "control_runtime_receipts": receipts,
        "control_target_scores": scores,
    }


def _rebuild_attestation(candidate: dict, rows: list[dict]) -> dict:
    sorted_rows = sorted(rows, key=lambda row: (row["split"], row["family_id"], row["case_id"]))
    case_universe_sha = gate._canonical_sha256(sorted_rows)
    contingency = {split: {} for split in gate.REQUIRED_SPLITS}
    effects = {split: {} for split in gate.REQUIRED_SPLITS}
    for row in rows:
        cell = f'{row["semantic_target"]}|{row["output_code_identity"]}'
        contingency[row["split"]][cell] = contingency[row["split"]].get(cell, 0) + 1
        effects[row["split"]].setdefault(row["semantic_target"], []).append(
            row["control_target_scores"]["+VECTOR"] - row["control_target_scores"]["BASELINE"]
        )
    family_by_split = {
        "CALIBRATION": candidate["calibration"]["family_id"],
        "HOLDOUT": candidate["holdout"]["family_id"],
    }
    factorial_material = {
        "schema": gate.CASE_ATTESTATION_SCHEMA,
        "case_universe_sha256": case_universe_sha,
        "families": family_by_split,
        "contingency": {
            split: {key: contingency[split][key] for key in sorted(contingency[split])}
            for split in gate.REQUIRED_SPLITS
        },
    }
    factorial_sha = gate._canonical_sha256(factorial_material)
    summary = {}
    for split in gate.REQUIRED_SPLITS:
        means = {
            target: sum(effects[split][target]) / len(effects[split][target])
            for target in sorted(gate.REQUIRED_SEMANTIC_TARGETS)
            if effects[split].get(target)
        }
        if len(means) == len(gate.REQUIRED_SEMANTIC_TARGETS):
            summary[family_by_split[split]] = {
                "split": split,
                "mean_plus_minus_baseline_by_semantic_target": means,
                "interaction_span": max(means.values()) - min(means.values()),
            }
    analysis = {
        "case_universe_sha256": case_universe_sha,
        "factorial_receipt_sha256": factorial_sha,
        "metric_definition_sha256": candidate["holdout"]["metric_definition_sha256"],
        "analysis_implementation_sha256": HEX64,
        "semantic_target_interaction_test": True,
        "per_family_semantic_target_interaction": True,
        "family_interaction_summary": summary,
    }
    analysis["interaction_analysis_receipt_sha256"] = gate._canonical_sha256(analysis)
    return {
        "schema": gate.CASE_ATTESTATION_SCHEMA,
        "rows": rows,
        "case_universe_sha256": case_universe_sha,
        "factorial_receipt_sha256": factorial_sha,
        "interaction_analysis": analysis,
    }


def attach_valid_attestation(candidate: dict) -> dict:
    rows = []
    case_index = 0
    for split, family in (("CALIBRATION", candidate["calibration"]["family_id"]), ("HOLDOUT", candidate["holdout"]["family_id"])):
        for target in sorted(gate.REQUIRED_SEMANTIC_TARGETS):
            for code in sorted(gate.REQUIRED_OUTPUT_CODES):
                case_index += 1
                rows.append(_row(split, family, case_index, target, code))
    candidate["semantic_factorial_attestation"] = _rebuild_attestation(candidate, rows)
    return candidate


class Trigger1JSpacePromotionGateV5Tests(unittest.TestCase):
    def test_complete_successor_metrology_passes_extra_guard(self):
        ok, failures = gate._extra_specificity_evidence(complete_v5_candidate())
        self.assertTrue(ok)
        self.assertEqual([], failures)

    def test_affirmative_only_style_candidate_cannot_satisfy_v5_by_omission(self):
        candidate = complete_v5_candidate()
        for key in (
            "model_facing_label_free",
            "lexically_disjoint_basis_families",
            "lexical_nuisance_projection_or_control",
        ):
            candidate["vector_derivation"].pop(key)
        candidate["calibration"].pop("semantic_target_x_output_code_factorial")
        candidate["holdout"].pop("semantic_target_x_output_code_factorial")

        ok, failures = gate._extra_specificity_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("MODEL_FACING_LABEL_FREE_BASIS_REQUIRED", failures)
        self.assertIn("LEXICALLY_DISJOINT_BASIS_FAMILIES_REQUIRED", failures)
        self.assertIn("LEXICAL_NUISANCE_PROJECTION_OR_CONTROL_REQUIRED", failures)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_REQUIRED", failures)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_REQUIRED", failures)

    def test_native_cvec_scope_cannot_be_mislabeled_last_token_replication(self):
        candidate = complete_v5_candidate()
        candidate["intervention"]["token_scope"] = "LAST_TOKEN_ONLY"
        candidate["intervention"]["strict_last_token_replication_claimed"] = True

        ok, failures = gate._extra_specificity_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("NATIVE_CVEC_REQUIRES_ALL_PROMPT_TOKENS_SCOPE_CLASSIFICATION", failures)

    def test_raw_gain_without_norm_calibration_and_frozen_operating_point_fails(self):
        candidate = complete_v5_candidate()
        candidate["calibration"]["residual_norm_relative_intervention"] = False
        candidate["calibration"]["operating_point_selected_on_calibration_only"] = False
        candidate["holdout"]["operating_point_frozen_before_holdout"] = False
        candidate["intervention"]["residual_norm_ratio"] = None

        ok, failures = gate._extra_specificity_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("CALIBRATION_RESIDUAL_NORM_RELATIVE_INTERVENTION_REQUIRED", failures)
        self.assertIn("OPERATING_POINT_MUST_BE_SELECTED_ON_CALIBRATION_ONLY", failures)
        self.assertIn("OPERATING_POINT_MUST_BE_FROZEN_BEFORE_HOLDOUT", failures)
        self.assertIn("POSITIVE_RESIDUAL_NORM_RATIO_REQUIRED", failures)

    def test_v5_never_promotes_if_v4_scientific_gate_is_false(self):
        candidate = attach_valid_attestation(complete_v5_candidate())
        base = {
            "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v4",
            "mechanism_runtime_vector_credit_candidate": True,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [],
            "scientific_independence_failures": ["EXAMPLE_V4_FAILURE"],
            "owner_target_failures": ["EXAMPLE_V4_FAILURE"],
        }
        with patch.object(gate.v4, "adjudicate", return_value=base):
            verdict = gate.adjudicate(candidate)

        self.assertTrue(verdict["v5_specificity_controls_pass"])
        self.assertTrue(verdict["case_bound_semantic_factorial_evidence_pass"])
        self.assertFalse(verdict["scientifically_independent_vector_candidate"])
        self.assertFalse(verdict["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(verdict["canonical_credit_minted"])
        self.assertFalse(verdict["jspace_model_runtime_credit"])
        self.assertFalse(verdict["training_credit"])

    def test_case_bound_valid_3x3_factorial_and_interaction_binding_passes(self):
        candidate = attach_valid_attestation(complete_v5_candidate())
        ok, failures = gate._case_bound_semantic_factorial_evidence(candidate)
        self.assertTrue(ok)
        self.assertEqual([], failures)

    def test_lying_summary_affirmative_only_rows_fail_even_with_recomputed_hashes(self):
        candidate = attach_valid_attestation(complete_v5_candidate())
        rows = deepcopy(candidate["semantic_factorial_attestation"]["rows"])
        for row in rows:
            row["semantic_target"] = "AFFIRMATIVE"
        candidate["semantic_factorial_attestation"] = _rebuild_attestation(candidate, rows)

        ok, failures = gate._case_bound_semantic_factorial_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("CALIBRATION_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_INCOMPLETE", failures)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_INCOMPLETE", failures)

    def test_missing_one_target_x_code_cell_fails_even_with_self_consistent_receipts(self):
        candidate = attach_valid_attestation(complete_v5_candidate())
        rows = [
            row for row in candidate["semantic_factorial_attestation"]["rows"]
            if not (
                row["split"] == "HOLDOUT"
                and row["semantic_target"] == "NEGATIVE"
                and row["output_code_identity"] == "B"
            )
        ]
        candidate["semantic_factorial_attestation"] = _rebuild_attestation(candidate, rows)

        ok, failures = gate._case_bound_semantic_factorial_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_INCOMPLETE", failures)

    def test_interaction_analysis_bound_to_different_case_universe_fails(self):
        candidate = attach_valid_attestation(complete_v5_candidate())
        analysis = candidate["semantic_factorial_attestation"]["interaction_analysis"]
        analysis["case_universe_sha256"] = HEX64_B
        analysis_core = {k: v for k, v in analysis.items() if k != "interaction_analysis_receipt_sha256"}
        analysis["interaction_analysis_receipt_sha256"] = gate._canonical_sha256(analysis_core)

        ok, failures = gate._case_bound_semantic_factorial_evidence(candidate)

        self.assertFalse(ok)
        self.assertIn("INTERACTION_ANALYSIS_CASE_UNIVERSE_MISMATCH", failures)

    def test_missing_control_receipt_in_one_factorial_cell_fails(self):
        candidate = attach_valid_attestation(complete_v5_candidate())
        rows = deepcopy(candidate["semantic_factorial_attestation"]["rows"])
        rows[0]["control_runtime_receipts"].pop("SIGN_FLIP")
        candidate["semantic_factorial_attestation"] = _rebuild_attestation(candidate, rows)

        ok, failures = gate._case_bound_semantic_factorial_evidence(candidate)

        self.assertFalse(ok)
        self.assertTrue(any("CONTROL_RUNTIME_RECEIPT_REQUIRED:SIGN_FLIP" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
