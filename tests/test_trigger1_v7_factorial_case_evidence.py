from __future__ import annotations

from copy import deepcopy
import unittest

from tools import trigger1_semantic_factorial_evidence_gate_v1 as gate
from tools import trigger1_v7_factorial_case_evidence as producer


def runtime_rows_for(plan: dict, candidate_key: str = "candidate-1") -> list[dict]:
    expanded = producer.expand_runtime_cases(plan, candidate_key)
    return [
        {
            **row,
            "runtime_receipt_sha256": producer.canonical_sha({
                "case_identity_sha256": row["case_identity_sha256"],
                "control": row["control"],
                "observed": True,
            }),
        }
        for row in expanded
    ]


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
        for plan in (calibration, holdout):
            for case in plan["cases"]:
                self.assertEqual(case["case_identity_sha256"], producer._case_identity(case))

    def test_runtime_expansion_has_exact_six_controls_per_case_and_exact_identity(self):
        plan = producer.build_plan("CALIBRATION")
        rows = producer.expand_runtime_cases(plan, "candidate-1")
        self.assertEqual(len(rows), 9 * len(producer.CONTROLS))
        for case in plan["cases"]:
            observed = [row for row in rows if row["case_id"] == case["case_id"]]
            self.assertEqual({row["control"] for row in observed}, set(producer.CONTROLS))
            for row in observed:
                self.assertEqual(row["case_identity_sha256"], case["case_identity_sha256"])
                for field in producer.CASE_IDENTITY_FIELDS:
                    self.assertEqual(row[field], case[field])

    def test_binding_exact_runtime_identity_is_accepted_by_v7_evidence_gate(self):
        plan = producer.build_plan("CALIBRATION")
        split = producer.bind_runtime_receipts(plan, runtime_rows_for(plan))
        derived, failures = gate.derive_split_receipt(split, "CALIBRATION")
        self.assertEqual(failures, [])
        self.assertIsNotNone(derived)
        self.assertEqual(derived["receipt_sha256"], split["semantic_factorial_receipt_sha256"])
        self.assertEqual(derived["runtime_observation_count_bound"], 54)
        self.assertTrue(split["runtime_case_identity_binding"])

    def test_missing_control_receipt_fails_closed(self):
        plan = producer.build_plan("CALIBRATION")
        runtime_rows = runtime_rows_for(plan)[:-1]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_CONTROLS_MISSING"):
            producer.bind_runtime_receipts(plan, runtime_rows)

    def test_legacy_affirmative_only_plan_cannot_be_bound(self):
        plan = producer.build_plan("CALIBRATION")
        plan["cases"] = [row for row in plan["cases"] if row["semantic_target"] == "AFFIRMATIVE"]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "EXACTLY_NINE"):
            producer.expand_runtime_cases(plan, "legacy")

    def test_runtime_row_with_wrong_prompt_hash_fails_even_when_case_id_matches(self):
        plan = producer.build_plan("CALIBRATION")
        rows = runtime_rows_for(plan)
        rows[0] = deepcopy(rows[0])
        rows[0]["prompt_sha256"] = "f" * 64
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_ROW_CASE_FIELD_MISMATCH"):
            producer.bind_runtime_receipts(plan, rows)

    def test_runtime_row_with_recomputed_wrong_case_identity_fails(self):
        plan = producer.build_plan("CALIBRATION")
        rows = runtime_rows_for(plan)
        rows[0] = deepcopy(rows[0])
        rows[0]["semantic_target"] = "NEGATIVE" if rows[0]["semantic_target"] != "NEGATIVE" else "NEUTRAL"
        rows[0]["case_identity_sha256"] = producer._case_identity(rows[0])
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_ROW_CASE_IDENTITY_MISMATCH"):
            producer.bind_runtime_receipts(plan, rows)

    def test_plan_case_identity_mutation_fails_before_runtime_binding(self):
        plan = producer.build_plan("CALIBRATION")
        plan["cases"][0]["seed"] += 1
        with self.assertRaisesRegex(producer.EvidenceBuildError, "PLAN_CASE_IDENTITY_MISMATCH"):
            producer.expand_runtime_cases(plan, "candidate-1")

    def test_interaction_binding_matches_gate(self):
        digest = "b" * 64
        analysis = producer.build_interaction_binding(digest, "c" * 64, "d" * 64, "e" * 64)
        derived, failures = gate.derive_interaction_binding(analysis, digest)
        self.assertEqual(failures, [])
        self.assertEqual(derived["binding_sha256"], analysis["analysis_binding_sha256"])


if __name__ == "__main__":
    unittest.main()
