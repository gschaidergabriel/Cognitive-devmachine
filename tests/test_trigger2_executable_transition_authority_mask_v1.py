from __future__ import annotations

import copy
import unittest

from tools import trigger2_executable_transition_authority_mask_v1 as mask


class Trigger2ExecutableTransitionAuthorityMaskV1Tests(unittest.TestCase):
    def test_all_current_pilot_rows_mask_deterministic_authority_and_remain_quarantined(self):
        result = mask.audit_all()
        self.assertTrue(result["pass"], result["failures"])
        self.assertGreater(result["row_count"], 0)
        self.assertFalse(result["training_eligible"])
        self.assertEqual(0, result["accepted_dataset_tokens_minted"])
        self.assertEqual(0, result["training_credit_minted"])

    def test_each_model_target_excludes_authority_keys(self):
        for row in mask.rows():
            self.assertEqual([], mask._forbidden_paths(row["model_target"]))
            self.assertFalse(row["training_eligible"])
            envelope = row["model_input"]["bound_oracle_envelope"]
            for key in ("causal_event_id", "admission_id", "generation", "work_id", "process_id", "executor_binding"):
                self.assertIn(key, envelope)

    def test_self_minted_lease_in_model_target_fails(self):
        row = copy.deepcopy(mask.rows()[0])
        row["model_target"]["lease_id"] = "model-invented-lease"
        result = mask.audit_row(row)
        self.assertFalse(result["pass"])
        self.assertIn("FORBIDDEN_AUTHORITY_IN_MODEL_TARGET:lease_id", result["failures"])

    def test_self_minted_nested_admission_id_fails(self):
        row = copy.deepcopy(mask.rows()[0])
        row["model_target"]["result_payload"]["admission_id"] = "model-invented-admission"
        result = mask.audit_row(row)
        self.assertFalse(result["pass"])
        self.assertIn(
            "FORBIDDEN_AUTHORITY_IN_MODEL_TARGET:result_payload.admission_id",
            result["failures"],
        )

    def test_result_and_reentry_digests_are_postwrap_not_model_targets(self):
        for row in mask.rows():
            target = row["model_target"]
            self.assertNotIn("result_digest", target)
            self.assertNotIn("reentry_digest", target)
            postwrap = row["deterministic_postwrap"]
            self.assertTrue(postwrap["wrapper_derives_result_and_reentry_digests"])
            self.assertTrue(postwrap["wrapper_rejects_envelope_override"])

    def test_adapter_does_not_promote_training_or_dataset_credit(self):
        for row in mask.rows():
            self.assertFalse(row["training_eligible"])
            self.assertEqual(0, row["accepted_dataset_tokens_minted"])
            self.assertEqual(0, row["training_credit_minted"])


if __name__ == "__main__":
    unittest.main()
