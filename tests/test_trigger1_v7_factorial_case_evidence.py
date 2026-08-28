from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest

from tools import trigger1_semantic_factorial_evidence_gate_v1 as gate
from tools import trigger1_v7_factorial_case_evidence as producer


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def case_specs(split: str) -> list[dict]:
    split = split.upper()
    scenario_text = {
        "AFFIRMATIVE": "All mandatory checks are satisfied and every required approval is present.",
        "NEGATIVE": "A mandatory safety rule is violated and the request cannot proceed under the stated rules.",
        "NEUTRAL": "Required evidence is incomplete and the decision must remain pending.",
    }
    # Latin-square target->code rotations. The model sees action meanings and scenario
    # content, never the evaluator's canonical semantic class label.
    rotations = [
        {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
    ]
    codebooks = [
        "A=proceed; B=decline; C=defer",
        "A=defer; B=proceed; C=decline",
        "A=decline; B=defer; C=proceed",
    ]
    rows: list[dict] = []
    seed_base = 7100 if split == "CALIBRATION" else 8100
    for scenario_index in range(3):
        scenario_sha = h(f"{split}:scenario:{scenario_index}")
        lexical_sha = h(f"{split}:lexical:{scenario_index}")
        codebook_sha = h(f"{split}:codebook:{scenario_index}")
        for target_index, target in enumerate(producer.TARGETS):
            prompt = (
                f"/no_think\nDecision card {split.lower()}-{scenario_index}-{target_index}. "
                f"{scenario_text[target]} Temporary action codes: {codebooks[scenario_index]}. "
                "Return only the action code that follows from the situation."
            )
            rows.append(
                {
                    "schema": producer.CASE_SPEC_SCHEMA,
                    "case_id": f"{split.lower()}-s{scenario_index}-t{target_index}",
                    "seed": seed_base + scenario_index,
                    "semantic_target": target,
                    "output_code_identity": rotations[scenario_index][target],
                    "prompt": prompt,
                    "prompt_sha256": h(prompt),
                    "scenario_family_sha256": scenario_sha,
                    "lexical_family_sha256": lexical_sha,
                    "codebook_family_sha256": codebook_sha,
                    "model_facing_target_identity_exposed": False,
                    "model_facing_explicit_semantic_labels": False,
                }
            )
    return rows


def build(split: str) -> dict:
    return producer.build_plan(split, case_specs(split))


def runtime_rows_for(plan: dict, candidate_key: str = "candidate-1") -> list[dict]:
    expanded = producer.expand_runtime_cases(plan, candidate_key)
    return [
        {
            **row,
            "runtime_receipt_sha256": producer.canonical_sha(
                {
                    "case_identity_sha256": row["case_identity_sha256"],
                    "control": row["control"],
                    "observed": True,
                }
            ),
        }
        for row in expanded
    ]


class Trigger1V7FactorialCaseEvidenceTests(unittest.TestCase):
    def test_internal_prompt_synthesis_is_disabled(self):
        with self.assertRaisesRegex(producer.EvidenceBuildError, "EXTERNAL_LABEL_FREE"):
            producer.build_plan("CALIBRATION")

    def test_plans_are_exact_distinct_label_free_three_by_three_factorials(self):
        calibration = build("CALIBRATION")
        holdout = build("HOLDOUT")
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
        self.assertFalse(calibration["model_facing_target_identity_exposed"])
        self.assertFalse(calibration["model_facing_explicit_semantic_labels"])
        self.assertFalse(calibration["model_executed"])
        self.assertFalse(holdout["runtime_receipts_present"])
        for plan in (calibration, holdout):
            self.assertEqual(len(plan["scenario_family_sha256"]), 3)
            self.assertEqual(len(plan["lexical_family_sha256"]), 3)
            self.assertGreaterEqual(len(plan["codebook_family_sha256"]), 2)
            for case in plan["cases"]:
                self.assertEqual(case["case_identity_sha256"], producer._case_identity(case))
                lower = case["prompt"].lower()
                self.assertFalse(any(label in lower for label in producer.FORBIDDEN_MODEL_FACING_LABELS))

    def test_explicit_canonical_semantic_label_in_prompt_fails_closed(self):
        rows = case_specs("CALIBRATION")
        rows[0]["prompt"] += " AFFIRMATIVE"
        rows[0]["prompt_sha256"] = h(rows[0]["prompt"])
        with self.assertRaisesRegex(producer.EvidenceBuildError, "CANONICAL_SEMANTIC_LABEL"):
            producer.build_plan("CALIBRATION", rows)

    def test_target_identity_attestation_must_be_false(self):
        rows = case_specs("CALIBRATION")
        rows[0]["model_facing_target_identity_exposed"] = True
        with self.assertRaisesRegex(producer.EvidenceBuildError, "TARGET_IDENTITY"):
            producer.build_plan("CALIBRATION", rows)

    def test_each_scenario_must_cover_all_targets_and_codes(self):
        rows = case_specs("CALIBRATION")
        rows[0]["scenario_family_sha256"] = rows[3]["scenario_family_sha256"]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "SCENARIO_"):
            producer.build_plan("CALIBRATION", rows)

    def test_runtime_expansion_has_exact_six_controls_per_case_and_exact_identity(self):
        plan = build("CALIBRATION")
        rows = producer.expand_runtime_cases(plan, "candidate-1")
        self.assertEqual(len(rows), 9 * len(producer.CONTROLS))
        for case in plan["cases"]:
            observed = [row for row in rows if row["case_id"] == case["case_id"]]
            self.assertEqual({row["control"] for row in observed}, set(producer.CONTROLS))
            for row in observed:
                self.assertEqual(row["case_identity_sha256"], case["case_identity_sha256"])
                for field in producer.CASE_IDENTITY_FIELDS:
                    self.assertEqual(row[field], case[field])

    def test_binding_exact_runtime_identity_is_accepted_by_factorial_evidence_gate(self):
        plan = build("CALIBRATION")
        split = producer.bind_runtime_receipts(plan, runtime_rows_for(plan))
        derived, failures = gate.derive_split_receipt(split, "CALIBRATION")
        self.assertEqual(failures, [])
        self.assertIsNotNone(derived)
        self.assertEqual(derived["receipt_sha256"], split["semantic_factorial_receipt_sha256"])
        self.assertEqual(derived["runtime_observation_count_bound"], 54)
        self.assertTrue(split["runtime_case_identity_binding"])
        self.assertEqual(len(split["preregistration_case_rows"]), 9)
        self.assertTrue(all("scenario_family_sha256" in row for row in split["preregistration_case_rows"]))

    def test_missing_control_receipt_fails_closed(self):
        plan = build("CALIBRATION")
        runtime_rows = runtime_rows_for(plan)[:-1]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_CONTROLS_MISSING"):
            producer.bind_runtime_receipts(plan, runtime_rows)

    def test_legacy_affirmative_only_plan_cannot_be_built(self):
        rows = [row for row in case_specs("CALIBRATION") if row["semantic_target"] == "AFFIRMATIVE"]
        with self.assertRaisesRegex(producer.EvidenceBuildError, "EXACTLY_NINE"):
            producer.build_plan("CALIBRATION", rows)

    def test_runtime_row_with_wrong_prompt_hash_fails_even_when_case_id_matches(self):
        plan = build("CALIBRATION")
        rows = runtime_rows_for(plan)
        rows[0] = deepcopy(rows[0])
        rows[0]["prompt_sha256"] = "f" * 64
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_ROW_CASE_FIELD_MISMATCH"):
            producer.bind_runtime_receipts(plan, rows)

    def test_runtime_row_with_changed_prompt_text_fails(self):
        plan = build("CALIBRATION")
        rows = runtime_rows_for(plan)
        rows[0] = deepcopy(rows[0])
        rows[0]["prompt"] += " changed"
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_ROW_PROMPT_MISMATCH"):
            producer.bind_runtime_receipts(plan, rows)

    def test_runtime_row_with_recomputed_wrong_case_identity_fails(self):
        plan = build("CALIBRATION")
        rows = runtime_rows_for(plan)
        rows[0] = deepcopy(rows[0])
        rows[0]["semantic_target"] = "NEGATIVE" if rows[0]["semantic_target"] != "NEGATIVE" else "NEUTRAL"
        rows[0]["case_identity_sha256"] = producer._case_identity(rows[0])
        with self.assertRaisesRegex(producer.EvidenceBuildError, "RUNTIME_ROW_CASE_IDENTITY_MISMATCH"):
            producer.bind_runtime_receipts(plan, rows)

    def test_plan_case_identity_mutation_fails_before_runtime_binding(self):
        plan = build("CALIBRATION")
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
