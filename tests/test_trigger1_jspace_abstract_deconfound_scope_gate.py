from __future__ import annotations

import unittest

from tools import trigger1_jspace_abstract_deconfound_scope_gate as gate

H = "a" * 64


def valid_candidate():
    return {
        "abstract_state_deconfound": {
            "basis_model_facing_canonical_labels_absent": True,
            "holdout_model_facing_canonical_labels_absent": True,
            "basis_holdout_lexically_disjoint": True,
            "basis_holdout_scenario_disjoint": True,
            "semantic_synonym_lexicon_disjoint": True,
            "semantic_target_evaluator_metadata_only": True,
            "full_three_by_three_target_x_output_code": True,
            "per_scenario_target_and_code_rotation": True,
            "nuisance_subspace_fit_on_calibration_only": True,
            "semantic_basis_residualized_against_nuisance_subspace": True,
            "residualization_frozen_before_holdout": True,
            "holdout_nuisance_controls_fail_to_reproduce": True,
            "holdout_target_selective_causal_matrix_pass": True,
            "nuisance_axes": sorted(gate.REQUIRED_NUISANCE_AXES),
            "lexical_audit_receipt_sha256": H,
            "nuisance_subspace_receipt_sha256": H,
            "projected_basis_receipt_sha256": H,
            "holdout_nuisance_control_receipt_sha256": H,
            "holdout_causal_matrix_receipt_sha256": H,
            "post_projection_max_abs_nuisance_cosine": 1e-5,
            "retained_semantic_subspace_norm_fraction": 0.61,
            "lexical_audit_frozen_before_holdout": True,
        },
        "direct_native_scope_evidence": {
            "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
            "token_scope": "ALL_PROMPT_TOKENS",
            "legacy_last_token_witness_used_as_causal_identity_premise": False,
            "same_projected_basis_as_preregistered": True,
            "calibration_only_operating_point": True,
            "operating_point_frozen_before_holdout": True,
            "fresh_label_free_counterbalanced_holdout": True,
            "matched_sign_null_orthogonal_permuted_nuisance_controls": True,
            "nonterminal_transport_observed": True,
            "context_valid_dual_readout_agrees": True,
            "class_selective_causal_matrix_pass": True,
            "runtime_receipt_sha256": H,
            "nonterminal_transport_receipt_sha256": H,
            "dual_readout_receipt_sha256": H,
            "causal_matrix_receipt_sha256": H,
        },
        "cross_scope_effect_bridge": {
            "legacy_scope": "LAST_TOKEN_ONLY",
            "native_scope": "ALL_PROMPT_TOKENS",
            "comparison_claim": "CAUSAL_EFFECT_EQUIVALENCE_NOT_MECHANISTIC_IDENTITY",
            "same_case_universe": True,
            "same_layer": True,
            "same_projected_vector_identity": True,
            "same_control_family": True,
            "equivalence_protocol_frozen_before_observation": True,
            "equivalence_test_kind": "PAIRED_TOST_ON_CONTROL_NORMALIZED_EFFECT",
            "paired_tost_pass": True,
            "control_normalized_effect_sign_structure_agrees": True,
            "alpha": 0.05,
            "equivalence_rope_abs_standardized_effect": 0.20,
            "equivalence_protocol_sha256": H,
            "paired_effect_receipt_sha256": H,
            "strict_micro_mechanistic_identity_claimed": False,
        },
    }


class GateTest(unittest.TestCase):
    def test_valid_candidate_passes_without_minting_identity_or_credit(self):
        r = gate.adjudicate(valid_candidate())
        self.assertTrue(r["abstract_native_semantic_jspace_candidate"])
        self.assertTrue(r["cross_scope_causal_effect_equivalence_candidate"])
        self.assertFalse(r["strict_micro_mechanistic_identity_candidate"])
        self.assertFalse(r["canonical_credit_minted"])
        self.assertFalse(r["jspace_model_runtime_credit"])

    def test_lexical_overlap_fails_deconfound(self):
        c = valid_candidate()
        c["abstract_state_deconfound"]["semantic_synonym_lexicon_disjoint"] = False
        r = gate.adjudicate(c)
        self.assertFalse(r["abstract_state_deconfound_pass"])
        self.assertIn("SEMANTIC_SYNONYM_LEXICON_DISJOINTNESS_REQUIRED", r["deconfound_failures"])

    def test_missing_compliance_nuisance_axis_fails(self):
        c = valid_candidate()
        c["abstract_state_deconfound"]["nuisance_axes"] = [
            x for x in c["abstract_state_deconfound"]["nuisance_axes"]
            if x != "GENERIC_INSTRUCTION_COMPLIANCE"
        ]
        r = gate.adjudicate(c)
        self.assertFalse(r["abstract_state_deconfound_pass"])
        self.assertIn("EXACT_REQUIRED_NUISANCE_AXIS_SET_REQUIRED", r["deconfound_failures"])

    def test_projection_must_actually_remove_nuisance(self):
        c = valid_candidate()
        c["abstract_state_deconfound"]["post_projection_max_abs_nuisance_cosine"] = 0.2
        r = gate.adjudicate(c)
        self.assertFalse(r["abstract_state_deconfound_pass"])
        self.assertIn("POST_PROJECTION_NUISANCE_ORTHOGONALITY_REQUIRED", r["deconfound_failures"])

    def test_native_claim_cannot_reuse_last_token_as_identity_premise(self):
        c = valid_candidate()
        c["direct_native_scope_evidence"]["legacy_last_token_witness_used_as_causal_identity_premise"] = True
        r = gate.adjudicate(c)
        self.assertFalse(r["direct_native_scope_evidence_pass"])
        self.assertIn("LEGACY_LAST_TOKEN_WITNESS_CANNOT_BE_NATIVE_CAUSAL_IDENTITY_PREMISE", r["direct_native_scope_failures"])

    def test_native_scope_must_be_all_prompt_tokens(self):
        c = valid_candidate()
        c["direct_native_scope_evidence"]["token_scope"] = "LAST_TOKEN_ONLY"
        r = gate.adjudicate(c)
        self.assertFalse(r["direct_native_scope_evidence_pass"])
        self.assertIn("DIRECT_NATIVE_ALL_PROMPT_TOKENS_SCOPE_REQUIRED", r["direct_native_scope_failures"])

    def test_scope_bridge_can_only_claim_effect_equivalence(self):
        c = valid_candidate()
        c["cross_scope_effect_bridge"]["strict_micro_mechanistic_identity_claimed"] = True
        r = gate.adjudicate(c)
        self.assertFalse(r["cross_scope_causal_effect_equivalence_candidate"])
        self.assertFalse(r["strict_micro_mechanistic_identity_candidate"])
        self.assertIn("MICRO_MECHANISTIC_IDENTITY_CLAIM_FORBIDDEN_FROM_SCOPE_BRIDGE", r["scope_bridge_failures"])

    def test_weak_posthoc_equivalence_boundary_fails(self):
        c = valid_candidate()
        c["cross_scope_effect_bridge"]["equivalence_rope_abs_standardized_effect"] = 0.8
        c["cross_scope_effect_bridge"]["equivalence_protocol_frozen_before_observation"] = False
        r = gate.adjudicate(c)
        self.assertFalse(r["cross_scope_causal_effect_equivalence_candidate"])
        self.assertIn("BRIDGE_EQUIVALENCE_ROPE_TOO_WEAK_OR_INVALID", r["scope_bridge_failures"])
        self.assertIn("BRIDGE_PROTOCOL_MUST_BE_FROZEN_BEFORE_OBSERVATION", r["scope_bridge_failures"])


if __name__ == "__main__":
    unittest.main()
