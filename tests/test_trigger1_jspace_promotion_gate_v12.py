from __future__ import annotations

from copy import deepcopy
import unittest
from unittest import mock

from tools import trigger1_abstract_state_challenge_v1 as challenge_gate
from tools import trigger1_jspace_promotion_gate_v12 as gate

H = "a" * 64


def v11_positive() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11",
        "abstract_native_semantic_jspace_candidate": True,
        "cross_scope_causal_effect_equivalence_candidate": False,
        "strict_micro_mechanistic_identity_candidate": False,
        "v11_failures": [],
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
    }


def runtime_rows(challenge: dict, split: str) -> list[dict]:
    source = challenge["calibration_rows"] if split == "CALIBRATION" else challenge["holdout_rows"]
    rows: list[dict] = []
    for raw in source:
        row = {
            "family_id": raw["family_id"],
            "family_sha256": raw["family_sha256"],
            "semantic_target": raw["semantic_target"],
            "seed": raw["seed"],
            "prompt_sha256": raw["prompt_sha256"],
            "runtime_receipt_sha256": H,
            "control_runtime_receipts": {name: H for name in gate.REQUIRED_CONTROLS},
        }
        if split == "HOLDOUT":
            row["output_code_identity"] = raw["output_code_identity"]
        rows.append(row)
    return rows


def candidate() -> dict:
    challenge = challenge_gate.build_challenge()
    return {
        "abstract_state_challenge": challenge,
        "abstract_state_challenge_runtime_binding": {
            "challenge_sha256": challenge["challenge_sha256"],
            "runtime_intervention_scope": "ALL_PROMPT_TOKENS",
            "model_facing_target_identity_exposed": False,
            "prompt_bytes_revalidated_from_runtime_rows": True,
            "generic_compliance_axis_fails_to_reproduce_target_matrix": True,
            "generic_compliance_control_receipt_sha256": H,
            "binding_receipt_sha256": H,
            "calibration_rows": runtime_rows(challenge, "CALIBRATION"),
            "holdout_rows": runtime_rows(challenge, "HOLDOUT"),
        },
    }


class Trigger1JspacePromotionGateV12Tests(unittest.TestCase):
    def adjudicate(self, value: dict) -> dict:
        with mock.patch.object(gate.v11, "adjudicate", return_value=v11_positive()):
            return gate.adjudicate(value)

    def test_exact_derived_challenge_bytes_can_support_v11_candidate_without_minting_credit(self):
        result = self.adjudicate(candidate())
        self.assertTrue(result["derived_abstract_challenge_design_pass"], result["v12_failures"])
        self.assertTrue(result["exact_abstract_challenge_runtime_binding_pass"])
        self.assertTrue(result["abstract_native_semantic_jspace_candidate"])
        self.assertFalse(result["strict_micro_mechanistic_identity_candidate"])
        self.assertFalse(result["canonical_credit_minted"])
        self.assertFalse(result["jspace_model_runtime_credit"])

    def test_runtime_prompt_hash_drift_blocks_promotion(self):
        value = candidate()
        value["abstract_state_challenge_runtime_binding"]["holdout_rows"][0]["prompt_sha256"] = "b" * 64
        result = self.adjudicate(value)
        self.assertFalse(result["exact_abstract_challenge_runtime_binding_pass"])
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertTrue(any("prompt_sha256" in x for x in result["v12_failures"]))

    def test_missing_control_receipt_blocks_promotion(self):
        value = candidate()
        row = value["abstract_state_challenge_runtime_binding"]["holdout_rows"][0]
        row["control_runtime_receipts"].pop("PERMUTED_SAME_NORM")
        result = self.adjudicate(value)
        self.assertFalse(result["exact_abstract_challenge_runtime_binding_pass"])
        self.assertTrue(any("EXACT_SIX_CONTROL_RECEIPTS_REQUIRED" in x for x in result["v12_failures"]))

    def test_generic_compliance_counterhypothesis_is_mandatory(self):
        value = candidate()
        value["abstract_state_challenge_runtime_binding"]["generic_compliance_axis_fails_to_reproduce_target_matrix"] = False
        result = self.adjudicate(value)
        self.assertFalse(result["exact_abstract_challenge_runtime_binding_pass"])
        self.assertIn("EXECUTED_GENERIC_COMPLIANCE_COUNTERHYPOTHESIS_MUST_FAIL", result["v12_failures"])

    def test_v11_direct_native_scope_remains_all_prompt_tokens_and_does_not_claim_last_token_identity(self):
        value = candidate()
        value["abstract_state_challenge_runtime_binding"]["runtime_intervention_scope"] = "LAST_TOKEN_ONLY"
        result = self.adjudicate(value)
        self.assertFalse(result["exact_abstract_challenge_runtime_binding_pass"])
        self.assertIn("V11_DIRECT_NATIVE_CHALLENGE_SCOPE_MUST_BE_ALL_PROMPT_TOKENS", result["v12_failures"])
        self.assertFalse(result["strict_micro_mechanistic_identity_candidate"])

    def test_v11_failure_cannot_be_rescued_by_challenge_binding(self):
        value = candidate()
        bad = v11_positive()
        bad["abstract_native_semantic_jspace_candidate"] = False
        bad["v11_failures"] = ["UPSTREAM_FAIL"]
        with mock.patch.object(gate.v11, "adjudicate", return_value=bad):
            result = gate.adjudicate(value)
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertIn("UPSTREAM_FAIL", result["v12_failures"])

    def test_forged_challenge_metadata_cannot_hide_model_facing_lexical_shortcut(self):
        value = candidate()
        challenge = value["abstract_state_challenge"]
        row = challenge["calibration_rows"][0]
        row["prompt"] += " approve"
        row["state_surface"] = row["prompt"]
        row["prompt_sha256"] = challenge_gate.text_sha(row["prompt"])
        row["state_surface_sha256"] = challenge_gate.text_sha(row["state_surface"])
        row["state_content_tokens"] = list(challenge_gate.content_tokens(row["state_surface"]))
        challenge.pop("challenge_sha256")
        challenge["challenge_sha256"] = challenge_gate.canonical_sha(challenge)
        value["abstract_state_challenge_runtime_binding"]["challenge_sha256"] = challenge["challenge_sha256"]
        result = self.adjudicate(value)
        self.assertFalse(result["derived_abstract_challenge_design_pass"])
        self.assertFalse(result["abstract_native_semantic_jspace_candidate"])
        self.assertTrue(any("DIRECT_SEMANTIC_SHORTCUT" in x for x in result["v12_failures"]))


if __name__ == "__main__":
    unittest.main()
