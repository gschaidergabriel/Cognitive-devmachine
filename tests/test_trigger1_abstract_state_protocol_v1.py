from __future__ import annotations

import unittest

from tools import trigger1_abstract_state_protocol_v1 as protocol


class AbstractStateProtocolTests(unittest.TestCase):
    def test_frozen_protocol_is_label_free_disjoint_and_counterbalanced(self):
        result = protocol.validate_design()
        self.assertTrue(result["pass"], result["failures"])
        self.assertTrue(result["payload_lexicon_pairwise_disjoint"])
        self.assertTrue(result["canonical_status_words_model_facing_absent"])
        self.assertTrue(result["semantic_x_output_code_counterbalanced"])
        self.assertEqual(result["basis_family_count"], 6)
        self.assertEqual(result["calibration_case_count"], 9)
        self.assertEqual(result["holdout_case_count"], 9)

    def test_no_model_facing_prompt_contains_forbidden_status_or_compliance_token(self):
        prompts = [row["prompt"] for row in protocol.basis_rows()]
        for split in ("CALIBRATION", "HOLDOUT"):
            prompts.extend(row["prompt"] for row in protocol.factorial_case_specs(split))
        for prompt in prompts:
            self.assertEqual(protocol.forbidden_hits(prompt), [], prompt)

    def test_phase_payload_lexicons_are_pairwise_disjoint(self):
        lex = {
            "BASIS": protocol.payload_lexicon([row["prompt"] for row in protocol.basis_rows()]),
            "CALIBRATION": protocol.payload_lexicon([row["prompt"] for row in protocol.factorial_case_specs("CALIBRATION")]),
            "HOLDOUT": protocol.payload_lexicon([row["prompt"] for row in protocol.factorial_case_specs("HOLDOUT")]),
        }
        self.assertFalse(lex["BASIS"] & lex["CALIBRATION"])
        self.assertFalse(lex["BASIS"] & lex["HOLDOUT"])
        self.assertFalse(lex["CALIBRATION"] & lex["HOLDOUT"])

    def test_each_split_is_exact_three_by_three_target_code_factorial(self):
        expected = {(semantic, code) for semantic in protocol.CLASSES for code in protocol.CODES}
        for split in ("CALIBRATION", "HOLDOUT"):
            rows = protocol.factorial_case_specs(split)
            observed = {(row["semantic_target"], row["output_code_identity"]) for row in rows}
            self.assertEqual(observed, expected)
            self.assertEqual(len(rows), 9)

    def test_obvious_semantic_shortcut_is_detected(self):
        self.assertIn("approval", protocol.forbidden_hits("/no_think\napproval"))
        self.assertIn("yes", protocol.forbidden_hits("/no_think\nyes"))
        self.assertIn("neutral", protocol.forbidden_hits("/no_think\nneutral"))


if __name__ == "__main__":
    unittest.main()
