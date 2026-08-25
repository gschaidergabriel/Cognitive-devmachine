from __future__ import annotations

from copy import deepcopy
import unittest
from unittest import mock

from tools import trigger1_abstract_state_challenge_v1 as abstract_challenge
from tools import trigger1_jspace_promotion_gate_v10 as gate
from tools import trigger1_native_cvec_scope_analyze_v1 as scope_analyzer


D = "a" * 64


def base_v9_positive() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v9",
        "scientifically_independent_vector_candidate": True,
        "owner_trigger1_goal_credit_candidate": True,
        "owner_trigger1_direct_free_api_model_credit_candidate": True,
        "modular_hcu_jspace_control_candidate": True,
        "joint_case_universe_binding_pass": True,
        "v9_failures": [],
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
    }


def scope_analysis() -> dict:
    core = {
        "schema": scope_analyzer.SCHEMA,
        "localized_native_scope_pass": True,
        "immediate_actuator_equivalence_pass": True,
        "pass": True,
        "case_count": 6,
        "cases": [],
        "immediate_cosine_min": 0.9999,
        "immediate_relative_difference_max": 0.001,
        "broadcast_full_causal_identity_claimed": False,
        "downstream_and_behavioral_parity_are_diagnostics_not_assumptions": True,
        "failures": [],
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "evidence_boundary": "synthetic unit fixture",
    }
    core["analysis_sha256"] = scope_analyzer.canonical_sha(core)
    return core


def positive_candidate() -> dict:
    challenge = abstract_challenge.build_challenge()
    return {
        "runtime_intervention_class": gate.NATIVE_CVEC_CLASS,
        "abstract_state_challenge": challenge,
        "native_token_scope_evidence": {
            "analysis": scope_analysis(),
            "scope_probe_runtime_receipt_sha256": D,
            "scope_probe_harness_sha256": D,
            "localized_executor_sha256": D,
            "native_api": "llama_set_adapter_cvec",
            "promotion_token_scope": "LAST_TOKEN_DECODE_ONLY",
            "prefix_prefill_without_cvec": True,
            "final_token_native_cvec_applied": True,
        },
        "abstract_state_runtime_evidence": {
            "token_scope": "LAST_TOKEN_DECODE_ONLY",
            "challenge_sha256": challenge["challenge_sha256"],
            "fresh_holdout_opened_under_admitted_coordination": True,
            "holdout_target_blind_prompt_bytes_attested": True,
            "calibration_holdout_lexical_disjointness_attested": True,
            "six_calibration_families_executed": True,
            "six_fresh_holdout_families_executed": True,
            "semantic_target_x_output_code_counterbalanced": True,
            "target_selective_causal_matrix_pass": True,
            "sign_null_orthogonal_permuted_controls_pass": True,
            "generic_compliance_axis_fails_to_reproduce_target_matrix": True,
            "downstream_nonterminal_transport_pass": True,
            "dual_behavioral_readout_pass": True,
            "representation_transport_behavioral_rank_agree": True,
            "runtime_receipt_sha256": D,
            "target_selective_matrix_receipt_sha256": D,
            "generic_compliance_control_receipt_sha256": D,
            "downstream_transport_receipt_sha256": D,
            "dual_readout_receipt_sha256": D,
        },
    }


class Trigger1JspacePromotionGateV10Tests(unittest.TestCase):
    def adjudicate(self, candidate: dict) -> dict:
        with mock.patch.object(gate.v9, "adjudicate", return_value=base_v9_positive()):
            return gate.adjudicate(candidate)

    def test_all_three_hard_boundaries_produce_only_noncanonical_candidate(self):
        result = self.adjudicate(positive_candidate())
        self.assertTrue(result["abstract_state_challenge_design_pass"], result["v10_failures"])
        self.assertTrue(result["localized_native_token_scope_pass"])
        self.assertTrue(result["abstract_state_runtime_pass"])
        self.assertTrue(result["abstract_semantic_jspace_control_candidate"])
        self.assertFalse(result["broadcast_causal_equivalence_required_for_localized_promotion"])
        self.assertFalse(result["broadcast_full_causal_identity_claimed"])
        self.assertFalse(result["canonical_credit_minted"])
        self.assertFalse(result["canonical_semantics_promotion"])
        self.assertFalse(result["jspace_model_runtime_credit"])

    def test_lexical_shortcut_in_embedded_challenge_blocks_promotion(self):
        candidate = positive_candidate()
        row = candidate["abstract_state_challenge"]["calibration_rows"][0]
        row["prompt"] += " approve"
        row["state_surface"] = row["prompt"]
        row["prompt_sha256"] = abstract_challenge.text_sha(row["prompt"])
        row["state_surface_sha256"] = abstract_challenge.text_sha(row["state_surface"])
        row["state_content_tokens"] = list(abstract_challenge.content_tokens(row["state_surface"]))
        candidate["abstract_state_challenge"].pop("challenge_sha256")
        candidate["abstract_state_challenge"]["challenge_sha256"] = abstract_challenge.canonical_sha(
            candidate["abstract_state_challenge"]
        )
        candidate["abstract_state_runtime_evidence"]["challenge_sha256"] = candidate[
            "abstract_state_challenge"
        ]["challenge_sha256"]
        result = self.adjudicate(candidate)
        self.assertFalse(result["abstract_state_challenge_design_pass"])
        self.assertFalse(result["abstract_semantic_jspace_control_candidate"])
        self.assertTrue(any("DIRECT_SEMANTIC_SHORTCUT" in x for x in result["v10_failures"]))

    def test_broadcast_scope_cannot_substitute_for_localized_native_scope(self):
        candidate = positive_candidate()
        candidate["native_token_scope_evidence"]["promotion_token_scope"] = "ALL_PROMPT_TOKENS"
        candidate["abstract_state_runtime_evidence"]["token_scope"] = "ALL_PROMPT_TOKENS"
        result = self.adjudicate(candidate)
        self.assertFalse(result["localized_native_token_scope_pass"])
        self.assertFalse(result["abstract_state_runtime_pass"])
        self.assertFalse(result["abstract_semantic_jspace_control_candidate"])
        self.assertIn("PROMOTION_TOKEN_SCOPE_MUST_BE_LAST_TOKEN_DECODE_ONLY", result["v10_failures"])

    def test_scope_analysis_cannot_claim_full_broadcast_causal_identity(self):
        candidate = positive_candidate()
        analysis = candidate["native_token_scope_evidence"]["analysis"]
        analysis["broadcast_full_causal_identity_claimed"] = True
        analysis.pop("analysis_sha256")
        analysis["analysis_sha256"] = scope_analyzer.canonical_sha(analysis)
        result = self.adjudicate(candidate)
        self.assertFalse(result["localized_native_token_scope_pass"])
        self.assertIn("BROADCAST_FULL_CAUSAL_IDENTITY_MUST_NOT_BE_ASSUMED", result["v10_failures"])

    def test_generic_compliance_counterhypothesis_must_be_falsified(self):
        candidate = positive_candidate()
        candidate["abstract_state_runtime_evidence"][
            "generic_compliance_axis_fails_to_reproduce_target_matrix"
        ] = False
        result = self.adjudicate(candidate)
        self.assertFalse(result["abstract_state_runtime_pass"])
        self.assertFalse(result["abstract_semantic_jspace_control_candidate"])
        self.assertIn("GENERIC_COMPLIANCE_COUNTERHYPOTHESIS_MUST_FAIL", result["v10_failures"])

    def test_fresh_holdout_requires_admitted_coordination(self):
        candidate = positive_candidate()
        candidate["abstract_state_runtime_evidence"][
            "fresh_holdout_opened_under_admitted_coordination"
        ] = False
        result = self.adjudicate(candidate)
        self.assertFalse(result["abstract_state_runtime_pass"])
        self.assertIn("FRESH_HOLDOUT_REQUIRES_ADMITTED_COORDINATION", result["v10_failures"])

    def test_runtime_receipts_are_required_even_when_summary_booleans_are_positive(self):
        candidate = positive_candidate()
        candidate["abstract_state_runtime_evidence"]["generic_compliance_control_receipt_sha256"] = None
        result = self.adjudicate(candidate)
        self.assertFalse(result["abstract_state_runtime_pass"])
        self.assertFalse(result["abstract_semantic_jspace_control_candidate"])
        self.assertTrue(any("GENERIC_COMPLIANCE_CONTROL_RECEIPT" in x for x in result["v10_failures"]))

    def test_v9_must_still_be_positive(self):
        candidate = positive_candidate()
        negative = base_v9_positive()
        negative["scientifically_independent_vector_candidate"] = False
        negative["owner_trigger1_goal_credit_candidate"] = False
        negative["modular_hcu_jspace_control_candidate"] = False
        negative["v9_failures"] = ["UPSTREAM_FAIL"]
        with mock.patch.object(gate.v9, "adjudicate", return_value=negative):
            result = gate.adjudicate(candidate)
        self.assertFalse(result["abstract_semantic_jspace_control_candidate"])
        self.assertIn("UPSTREAM_FAIL", result["v10_failures"])


if __name__ == "__main__":
    unittest.main()
