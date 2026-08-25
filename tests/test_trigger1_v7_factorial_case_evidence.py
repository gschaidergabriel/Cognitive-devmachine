from __future__ import annotations

import unittest

from tools import trigger1_semantic_factorial_evidence_gate_v1 as gate
from tools import trigger1_v7_factorial_case_evidence as producer


class Trigger1V7FactorialCaseEvidenceTests(unittest.TestCase):
    def test_plans_are_exact_distinct_three_by_three_factorials(self):
        calibration = producer.build_plan("CALIBRATION")
        holdout = producer.build_plan("HOLDOUT")
        expected = {(target, code) for target in producer.TARGETS for code in producer.CODES}
        self.assertEqual(
            {(row["semantic_target"], row["output_code_identity"]) for row in calibration["cases"]},
            expected,
        )
        self.assertEqual(
            {(row["semantic_target"], row["output_code_identity"]) for row in holdout["cases"]},
            expected,
        )
        self.assertNotEqual(calibration["split_family_id"], holdout["split_family_id"])
        self.assertFalse(calibration["model_executed"])
        self.assertFalse(holdout["runtime_receipts_present"])

    def test_runtime_expansion_has_exact_six_controls_per_case(self):
        plan = producer.build_plan("CALIBRATION")
        rows = producer.expand_runtime_cases(plan, "candidate-1")
        self.assertEqual(len(rows), 9 * len(producer.CONTROLS))
        for case in plan["cases"]:
            observed = {row["control"] for row in rows if row["case_id"] == case["case_id"]}
            self.assertEqual(observed, set(producer.CONTROLS))

    def test_binding_real_receipt_slots_is_accepted_by_v7_evidence_gate(self):
        plan = producer.build_plan("CALIBRATION")
        expanded = producer.expand_runtime_cases(plan, "candidate-1")
        runtime_rows = [
            {
                "case_id": row["case_id"],
                "control": row["control"],
                "runtime_receipt_sha256": producer.canonical_sha({
                    "case_id": row["case_id"], "control": row["control"], "observed": True
                }),
            }
            for row in expanded
        ]
        split = producer.bind_runtime_receipts(plan, runtime_rows)
        derived, failures = gate.derive_split_receipt(split, "CALIBRATION")
        self.assertEqual(failures, [])
        self.assertIsNotNone(derived)
        self.assertEqual(derived["receipt_sha256"], split["semantic_factorial_receipt_sha256"])
        self.assertEqual(derived["runtime_observation_count_bound"], 54)

    def test_missing_control_receipt_fails_closed(self):
        plan = producer.build_plan("CALIBRATION")
        expanded = producer.expand_runtime_cases(plan, "candidate-1")
        runtime_rows = [
            {
                "case_id": row["case_id"],
                "control": row["control"],
                "runtime_receipt_sha256": "a" * 64,
            }
            for row in expanded[:-1]
        ]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_CONTROLS_MISSING"):
            producer.bind_runtime_receipts(plan, runtime_rows)

    def test_legacy_affirmative_only_plan_cannot_be_bound(self):
        plan = producer.build_plan("CALIBRATION")
        plan["cases"] = [row for row in plan["cases"] if row["semantic_target"] == "AFFIRMATIVE"]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "EXACTLY_NINE"):
            producer.expand_runtime_cases(plan, "legacy")

    def test_interaction_binding_matches_gate(self):
        digest = "b" * 64
        analysis = producer.build_interaction_binding(digest, "c" * 64, "d" * 64, "e" * 64)
        derived, failures = gate.derive_interaction_binding(analysis, digest)
        self.assertEqual(failures, [])
        self.assertEqual(derived["binding_sha256"], analysis["analysis_binding_sha256"])


if __name__ == "__main__":
    unittest.main()
