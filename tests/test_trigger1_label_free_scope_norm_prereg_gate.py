from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_label_free_scope_norm_prereg_gate as gate

HEX64 = "a" * 64
GIT40 = "b" * 40


def factorial_cells() -> list[dict[str, str]]:
    return [
        {"semantic_target": t, "output_code": c}
        for t in ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
        for c in ("A", "B", "C")
    ]


def valid_plan() -> dict:
    return {
        "schema": gate.SCHEMA,
        "identity": {
            "model_id": "Qwen/Qwen3-0.6B",
            "model_revision": "pinned-revision",
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
            "gguf_sha256": HEX64,
            "llama_cpp_commit": GIT40,
            "native_harness_sha256": HEX64,
        },
        "basis": {
            "model_facing_explicit_semantic_labels": False,
            "uses_evaluation_output_codes": False,
            "uses_holdout_data": False,
            "lexical_family_sha256": ["1" * 64, "2" * 64, "3" * 64],
            "lexical_nuisance_control": {
                "enabled": True,
                "construction_independent_of_semantic_vector": True,
                "definition_sha256": HEX64,
            },
        },
        "calibration": {
            "semantic_targets": ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"],
            "output_codes": ["A", "B", "C"],
            "target_x_code_cells": factorial_cells(),
            "balanced_cell_counts": True,
            "lexical_family_sha256": ["4" * 64, "5" * 64, "6" * 64],
            "seeds": [101, 102, 103],
        },
        "holdout": {
            "semantic_targets": ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"],
            "output_codes": ["A", "B", "C"],
            "target_x_code_cells": factorial_cells(),
            "balanced_cell_counts": True,
            "lexical_family_sha256": ["7" * 64, "8" * 64, "9" * 64],
            "seeds": [201, 202, 203],
            "sealed_until_operating_point_frozen": True,
        },
        "scenario_blocking": {
            "unit": "SCENARIO_FAMILY",
            "every_family_contains_all_semantic_targets": True,
            "matched_content_skeleton_within_family": True,
            "model_facing_target_identity_exposed": False,
            "within_family_centering": True,
            "equal_family_weighting": True,
            "blocked_permutation_within_family": True,
            "output_code_rotation_independent_within_family": True,
            "basis_scenario_family_sha256": ["e" * 64, "f" * 64, "0" * 64],
            "calibration_scenario_family_sha256": ["a" * 64, "b" * 64, "c" * 64],
            "holdout_scenario_family_sha256": ["d" * 64, "1" * 64, "2" * 64],
            "blocked_rank_and_permutation_rule_sha256": HEX64,
        },
        "measurement": {
            "gain_selection_split": "CALIBRATION_ONLY",
            "residual_norm_relative": True,
            "residual_norm_definition": "l2(intervention)/l2(pre_intervention_residual)",
            "residual_norm_fraction_grid": [0.01, 0.02, 0.04, 0.08],
            "operating_point_rule_sha256": HEX64,
            "holdout_can_change_operating_point": False,
            "token_scope_conditions": [
                "PYTORCH_LAST_TOKEN_ONLY",
                "PYTORCH_ALL_PROMPT_TOKENS",
                "NATIVE_LLAMA_CPP_ALL_PROMPT_TOKENS_CVEC",
            ],
            "scope_divergence_classification_rule": "native is strict replication only of matched all-token scope",
        },
        "controls": {
            "names": [
                "BASELINE",
                "+VECTOR",
                "SIGN_FLIP",
                "NULL_VECTOR",
                "ORTHOGONAL_SAME_NORM",
                "PERMUTED_SAME_NORM",
                "LABEL_ONLY_NUISANCE_VECTOR",
            ],
            "same_norm_for_nonzero_geometric_controls": True,
            "same_cases_across_controls": True,
        },
        "coherence": {
            "cross_family_cosine_required": True,
            "permutation_null_required": True,
            "threshold_selected_on": "CALIBRATION_ONLY",
            "per_family_directional_signs_preserved": True,
            "coherence_rule_sha256": HEX64,
        },
        "output_realization": {
            "context_boundary_attestation_required": True,
            "prompt_plus_completion_prefix_check": True,
            "codebook_family_sha256": ["c" * 64, "d" * 64],
            "codebook_family_counterbalance_required": True,
            "generated_or_constrained_behavioral_agreement_required": True,
            "realization_rule_frozen_before_holdout": True,
            "realization_metric_sha256": HEX64,
        },
        "outcomes": {
            "primary_test": "TREATMENT_X_SEMANTIC_TARGET_INTERACTION",
            "sign_flip_must_reverse_interaction": True,
            "fresh_family_consistency_required": True,
            "off_target_task_family": "lexically-disjoint non-semantic control tasks",
            "off_target_drift_threshold": 0.05,
            "metric_definition_sha256": HEX64,
            "multiple_comparison_rule": "preregistered familywise correction",
        },
        "execution": {
            "requires_canonical_atomic_lease": True,
            "mode": "FREE_ONLY",
            "preregistration_mints_runtime_credit": False,
        },
    }


class PreregGateTests(unittest.TestCase):
    def test_valid_plan_passes(self):
        verdict = gate.validate(valid_plan())
        self.assertTrue(verdict["pass"])
        self.assertEqual([], verdict["failures"])
        self.assertFalse(verdict["runtime_credit_minted"])

    def test_all_affirmative_target_design_fails_even_when_codes_vary(self):
        plan = valid_plan()
        plan["holdout"]["semantic_targets"] = ["AFFIRMATIVE"]
        plan["holdout"]["target_x_code_cells"] = [
            {"semantic_target": "AFFIRMATIVE", "output_code": c} for c in ("A", "B", "C")
        ]
        failures = gate.validate(plan)["failures"]
        self.assertIn("HOLDOUT_SEMANTIC_TARGET_SET_REQUIRED", failures)
        self.assertIn("HOLDOUT_FULL_TARGET_X_CODE_FACTORIAL_REQUIRED", failures)

    def test_explicit_semantic_pole_labels_in_basis_fail(self):
        plan = valid_plan()
        plan["basis"]["model_facing_explicit_semantic_labels"] = True
        self.assertIn("MODEL_FACING_BASIS_MUST_BE_LABEL_FREE", gate.validate(plan)["failures"])

    def test_unmatched_scenario_families_fail_even_when_targets_are_label_free(self):
        plan = valid_plan()
        plan["scenario_blocking"]["every_family_contains_all_semantic_targets"] = False
        plan["scenario_blocking"]["matched_content_skeleton_within_family"] = False
        failures = gate.validate(plan)["failures"]
        self.assertIn("EVERY_SCENARIO_FAMILY_MUST_CONTAIN_ALL_SEMANTIC_TARGETS", failures)
        self.assertIn("MATCHED_CONTENT_SKELETON_WITHIN_SCENARIO_REQUIRED", failures)

    def test_unblocked_permutation_and_family_leak_fail(self):
        plan = valid_plan()
        plan["scenario_blocking"]["blocked_permutation_within_family"] = False
        plan["scenario_blocking"]["holdout_scenario_family_sha256"][0] = plan["scenario_blocking"]["calibration_scenario_family_sha256"][0]
        failures = gate.validate(plan)["failures"]
        self.assertIn("BLOCKED_PERMUTATION_WITHIN_SCENARIO_REQUIRED", failures)
        self.assertIn("BASIS_CALIBRATION_HOLDOUT_SCENARIO_FAMILIES_MUST_BE_DISJOINT", failures)

    def test_raw_gain_without_residual_norm_calibration_fails(self):
        plan = valid_plan()
        plan["measurement"]["residual_norm_relative"] = False
        self.assertIn("RESIDUAL_NORM_RELATIVE_INTERVENTION_REQUIRED", gate.validate(plan)["failures"])

    def test_holdout_cannot_tune_operating_point(self):
        plan = valid_plan()
        plan["measurement"]["holdout_can_change_operating_point"] = True
        self.assertIn("HOLDOUT_MUST_NOT_CHANGE_OPERATING_POINT", gate.validate(plan)["failures"])

    def test_native_only_scope_is_not_strict_replication_design(self):
        plan = valid_plan()
        plan["measurement"]["token_scope_conditions"] = ["NATIVE_LLAMA_CPP_ALL_PROMPT_TOKENS_CVEC"]
        self.assertIn("ALL_SCOPE_MATCH_CONDITIONS_REQUIRED", gate.validate(plan)["failures"])

    def test_lexical_family_leak_fails(self):
        plan = valid_plan()
        plan["holdout"]["lexical_family_sha256"][0] = plan["calibration"]["lexical_family_sha256"][0]
        self.assertIn("CALIBRATION_HOLDOUT_LEXICAL_FAMILIES_MUST_BE_DISJOINT", gate.validate(plan)["failures"])

    def test_nuisance_control_is_mandatory(self):
        plan = valid_plan()
        plan["controls"]["names"].remove("LABEL_ONLY_NUISANCE_VECTOR")
        self.assertIn("SEVEN_MATCHED_CONTROLS_REQUIRED", gate.validate(plan)["failures"])

    def test_coherence_must_use_permutation_null(self):
        plan = valid_plan()
        plan["coherence"]["permutation_null_required"] = False
        self.assertIn("COHERENCE_PERMUTATION_NULL_REQUIRED", gate.validate(plan)["failures"])

    def test_single_global_token_triplet_without_context_boundary_attestation_fails(self):
        plan = valid_plan()
        plan["output_realization"]["context_boundary_attestation_required"] = False
        plan["output_realization"]["prompt_plus_completion_prefix_check"] = False
        failures = gate.validate(plan)["failures"]
        self.assertIn("CONTEXT_BOUNDARY_ATTESTATION_REQUIRED", failures)
        self.assertIn("PROMPT_PLUS_COMPLETION_PREFIX_CHECK_REQUIRED", failures)

    def test_single_codebook_family_without_behavioral_agreement_fails(self):
        plan = valid_plan()
        plan["output_realization"]["codebook_family_sha256"] = ["c" * 64]
        plan["output_realization"]["generated_or_constrained_behavioral_agreement_required"] = False
        failures = gate.validate(plan)["failures"]
        self.assertIn("AT_LEAST_TWO_DISTINCT_CODEBOOK_FAMILIES_REQUIRED", failures)
        self.assertIn("BEHAVIORAL_OUTPUT_AGREEMENT_REQUIRED", failures)

    def test_execution_requires_atomic_lease(self):
        plan = valid_plan()
        plan["execution"]["requires_canonical_atomic_lease"] = False
        self.assertIn("CANONICAL_ATOMIC_LEASE_MUST_BE_REQUIRED_BEFORE_EXECUTION", gate.validate(plan)["failures"])


if __name__ == "__main__":
    unittest.main()
