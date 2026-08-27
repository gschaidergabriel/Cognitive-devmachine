from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_prereg_plan_receipt as receipt
import trigger1_prereg_runtime_binding_gate as gate

BASE_TEST = ROOT / "tests" / "test_trigger1_label_free_scope_norm_prereg_gate.py"
SPEC = importlib.util.spec_from_file_location("trigger1_existing_prereg_tests", BASE_TEST)
assert SPEC is not None and SPEC.loader is not None
base_test = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base_test)


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def valid_plan() -> dict:
    return base_test.valid_plan()


def rows_for_split(split: str, plan: dict) -> list[dict]:
    if split == "CALIBRATION":
        scenarios = plan["scenario_blocking"]["calibration_scenario_family_sha256"]
        lexicals = plan["calibration"]["lexical_family_sha256"]
        seeds = plan["calibration"]["seeds"]
    else:
        scenarios = plan["scenario_blocking"]["holdout_scenario_family_sha256"]
        lexicals = plan["holdout"]["lexical_family_sha256"]
        seeds = plan["holdout"]["seeds"]
    targets = ["AFFIRMATIVE", "NEGATIVE", "NEUTRAL"]
    codes = ["A", "B", "C"]
    rows = []
    for scenario_index, scenario_sha in enumerate(scenarios):
        for target_index, target in enumerate(targets):
            code = codes[(target_index + scenario_index) % 3]
            rows.append(
                {
                    "split": split,
                    "case_id": f"{split}-{scenario_index}-{target_index}",
                    "scenario_family_sha256": scenario_sha,
                    "lexical_family_sha256": lexicals[scenario_index],
                    "seed": seeds[scenario_index],
                    "prompt_sha256": h(f"{split}-{scenario_index}-{target_index}"),
                    "semantic_target": target,
                    "output_code_identity": code,
                }
            )
    return rows


def valid_candidate() -> dict:
    plan = valid_plan()
    bound = receipt.bind(plan)
    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "source_identity": {
            "checkpoint_sha256": plan["identity"]["checkpoint_sha256"],
            "tokenizer_sha256": plan["identity"]["tokenizer_sha256"],
            "gguf_sha256": plan["identity"]["gguf_sha256"],
            "llama_cpp_commit": plan["identity"]["llama_cpp_commit"],
            "native_harness_sha256": plan["identity"]["native_harness_sha256"],
        },
        "intervention": {
            "token_scope": "ALL_PROMPT_TOKENS",
            "residual_norm_ratio": 0.05,
        },
        "holdout": {
            "metric_definition_sha256": plan["outcomes"]["metric_definition_sha256"]
        },
        "semantic_factorial_attestation": {
            "rows": rows_for_split("CALIBRATION", plan) + rows_for_split("HOLDOUT", plan)
        },
        "preregistration_evidence": {
            "plan": plan,
            "receipt": bound,
            "plan_sha256": bound["plan_sha256"],
            "receipt_sha256": bound["receipt_sha256"],
        },
    }


class PreregRuntimeBindingTests(unittest.TestCase):
    def test_plan_receipt_is_deterministic_and_plan_bound(self):
        plan = valid_plan()
        one = receipt.bind(plan)
        two = receipt.bind(copy.deepcopy(plan))
        self.assertTrue(one["pass"])
        self.assertEqual(one["receipt_sha256"], two["receipt_sha256"])
        changed = copy.deepcopy(plan)
        changed["outcomes"]["metric_definition_sha256"] = "4" * 64
        self.assertNotEqual(one["plan_sha256"], receipt.bind(changed)["plan_sha256"])

    def test_valid_runtime_binding_passes(self):
        verdict = gate.validate(valid_candidate())
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertEqual([], verdict["failures"])
        self.assertFalse(verdict["runtime_credit_minted"])

    def test_runtime_identity_mutation_fails(self):
        candidate = valid_candidate()
        candidate["source_identity"]["gguf_sha256"] = "9" * 64
        failures = gate.validate(candidate)["failures"]
        self.assertIn("NATIVE_RUNTIME_PLAN_IDENTITY_MISMATCH:gguf_sha256", failures)

    def test_unplanned_scenario_family_fails(self):
        candidate = valid_candidate()
        candidate["semantic_factorial_attestation"]["rows"][0][
            "scenario_family_sha256"
        ] = "8" * 64
        failures = gate.validate(candidate)["failures"]
        self.assertIn("BOUND_CASE_ROW_0_SCENARIO_FAMILY_NOT_IN_BOUND_PLAN", failures)

    def test_reused_prompt_hash_fails(self):
        candidate = valid_candidate()
        rows = candidate["semantic_factorial_attestation"]["rows"]
        rows[1]["prompt_sha256"] = rows[0]["prompt_sha256"]
        failures = gate.validate(candidate)["failures"]
        self.assertIn(
            "BOUND_CASE_ROW_1_PROMPT_SHA256_REUSED_ACROSS_CASE_UNIVERSE", failures
        )

    def test_plan_mutation_after_receipt_fails(self):
        candidate = valid_candidate()
        candidate["preregistration_evidence"]["plan"]["holdout"]["seeds"][0] = 999
        failures = gate.validate(candidate)["failures"]
        self.assertIn("PREREGISTRATION_RECEIPT_MISMATCH", failures)
        self.assertIn("PREREGISTRATION_PLAN_SHA256_BINDING_MISMATCH", failures)

    def test_each_planned_scenario_must_cover_targets_and_code_rotation(self):
        candidate = valid_candidate()
        rows = candidate["semantic_factorial_attestation"]["rows"]
        rows[0]["semantic_target"] = "NEGATIVE"
        failures = gate.validate(candidate)["failures"]
        self.assertTrue(
            any(
                failure.startswith("CALIBRATION_SCENARIO_MISSING_SEMANTIC_TARGETS")
                for failure in failures
            )
        )


if __name__ == "__main__":
    unittest.main()
