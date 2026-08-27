from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest
from unittest import mock

from tools import trigger1_jspace_promotion_gate_v9 as gate
from tools import trigger1_v7_factorial_case_evidence as producer


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def specs(split: str) -> list[dict]:
    split = split.upper()
    content = {
        "AFFIRMATIVE": "Every mandatory requirement is satisfied and all approvals are present.",
        "NEGATIVE": "A mandatory requirement is violated and the request cannot proceed.",
        "NEUTRAL": "Required evidence is incomplete and the decision remains pending.",
    }
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
    for scenario in range(3):
        for target_index, target in enumerate(producer.TARGETS):
            prompt = (
                f"/no_think\nCase {split.lower()}-{scenario}-{target_index}. "
                f"{content[target]} Action codes: {codebooks[scenario]}. Return one code."
            )
            rows.append(
                {
                    "schema": producer.CASE_SPEC_SCHEMA,
                    "case_id": f"{split.lower()}-s{scenario}-t{target_index}",
                    "seed": (7100 if split == "CALIBRATION" else 8100) + scenario,
                    "semantic_target": target,
                    "output_code_identity": rotations[scenario][target],
                    "prompt": prompt,
                    "prompt_sha256": h(prompt),
                    "scenario_family_sha256": h(f"{split}:scenario:{scenario}"),
                    "lexical_family_sha256": h(f"{split}:lexical:{scenario}"),
                    "codebook_family_sha256": h(f"{split}:codebook:{scenario}"),
                    "model_facing_target_identity_exposed": False,
                    "model_facing_explicit_semantic_labels": False,
                }
            )
    return rows


def runtime_rows(plan: dict) -> list[dict]:
    expanded = producer.expand_runtime_cases(plan, "candidate-v9")
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


def candidate() -> dict:
    cal_plan = producer.build_plan("CALIBRATION", specs("CALIBRATION"))
    hold_plan = producer.build_plan("HOLDOUT", specs("HOLDOUT"))
    calibration = producer.bind_runtime_receipts(cal_plan, runtime_rows(cal_plan))
    holdout = producer.bind_runtime_receipts(hold_plan, runtime_rows(hold_plan))
    return {
        "calibration": calibration,
        "holdout": holdout,
        "semantic_factorial_attestation": {
            "rows": calibration["preregistration_case_rows"] + holdout["preregistration_case_rows"]
        },
    }


def v8_positive_stub() -> dict:
    return {
        "schema": "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v8",
        "scientifically_independent_vector_candidate": True,
        "owner_trigger1_goal_credit_candidate": True,
        "owner_trigger1_direct_free_api_model_credit_candidate": True,
        "modular_hcu_jspace_control_candidate": True,
        "preregistration_runtime_binding_pass": True,
        "v8_failures": [],
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
    }


class Trigger1V9JointUniverseTests(unittest.TestCase):
    def test_identical_factorial_and_prereg_universe_passes(self):
        result = gate.bind_joint_case_universe(candidate())
        self.assertTrue(result["pass"], result["failures"])
        self.assertEqual(result["joint_case_count"], 18)
        self.assertEqual(result["failures"], [])

    def test_different_prompt_hash_in_prereg_universe_fails(self):
        value = candidate()
        value["semantic_factorial_attestation"]["rows"][0]["prompt_sha256"] = "f" * 64
        result = gate.bind_joint_case_universe(value)
        self.assertFalse(result["pass"])
        self.assertTrue(any("prompt_sha256" in failure for failure in result["failures"]))

    def test_different_control_receipt_map_fails(self):
        value = candidate()
        row = value["semantic_factorial_attestation"]["rows"][0]
        row["control_runtime_receipts"] = dict(row["control_runtime_receipts"])
        row["control_runtime_receipts"][producer.CONTROLS[0]] = "f" * 64
        result = gate.bind_joint_case_universe(value)
        self.assertFalse(result["pass"])
        self.assertTrue(any("CONTROL_RUNTIME_RECEIPTS_MISMATCH" in failure for failure in result["failures"]))

    def test_extra_independently_valid_prereg_case_fails_joint_set(self):
        value = candidate()
        extra = deepcopy(value["semantic_factorial_attestation"]["rows"][0])
        extra["case_id"] = "extra-valid-looking-case"
        extra["prompt_sha256"] = h("extra-valid-looking-prompt")
        value["semantic_factorial_attestation"]["rows"].append(extra)
        result = gate.bind_joint_case_universe(value)
        self.assertFalse(result["pass"])
        self.assertIn("JOINT_CASES_MISSING_FROM_FACTORIAL_EVIDENCE", result["failures"])

    def test_v8_positive_is_rejected_when_joint_universe_drifts(self):
        value = candidate()
        value["semantic_factorial_attestation"]["rows"][0]["semantic_target"] = "NEGATIVE"
        with mock.patch.object(gate.v8, "adjudicate", return_value=v8_positive_stub()):
            result = gate.adjudicate(value)
        self.assertFalse(result["joint_case_universe_binding_pass"])
        self.assertFalse(result["owner_trigger1_goal_credit_candidate"])
        self.assertFalse(result["modular_hcu_jspace_control_candidate"])
        self.assertFalse(result["scientifically_independent_vector_candidate"])

    def test_v8_positive_survives_only_same_joint_universe(self):
        value = candidate()
        with mock.patch.object(gate.v8, "adjudicate", return_value=v8_positive_stub()):
            result = gate.adjudicate(value)
        self.assertTrue(result["joint_case_universe_binding_pass"])
        self.assertTrue(result["owner_trigger1_goal_credit_candidate"])
        self.assertTrue(result["modular_hcu_jspace_control_candidate"])
        self.assertTrue(result["scientifically_independent_vector_candidate"])
        self.assertFalse(result["canonical_credit_minted"])
        self.assertFalse(result["jspace_model_runtime_credit"])


if __name__ == "__main__":
    unittest.main()
